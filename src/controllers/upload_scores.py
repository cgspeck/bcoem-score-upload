from dataclasses import dataclass
from typing import Any, Generator, List, Optional, Union
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    g,
    render_template,
    request,
    url_for,
)
from flask_wtf import FlaskForm  # type: ignore
from flask_wtf.file import (
    FileAllowed,
    FileField,  # type: ignore
    FileRequired,
    FileSize,
)
from wtforms import BooleanField, RadioField  # type: ignore
from wtforms.validators import DataRequired  # type: ignore
from mysql.connector import MySQLConnection

from src.controllers.helpers import (
    backup_and_clear_scores,
    db_config_for_env_shortname,
    get_db_connection,
)
from src.csv_validate import (
    REQUIRED_HEADERS,
    validate_headers,
    is_csv,
    try_decode_stream,
)
from src.datadefs import ScoreEntry
from src.email import EmailReason, send_audit_email
from src.models.brewers import get_brewer_dict
from src.models.judging_scores import check_create_westgate_fields
from src.models.special_best_data import set_special_best_winner
from src.place_getter import determine_place_getters
from src.score_process import load_entries_from_csv, prepare_entries, save_entries
from src.utils import must_be_authorized, save_upload


MESSAGES_HEADER = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <!-- Required meta tags -->
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link 
            rel="stylesheet"
            href="{bootstrap_css}"
        >
        <title>Score Upload System - Upload processing results</title>
    </head>
<body>
    <div class="container">
        <h1>Message Log</h1>
"""

MESSAGES_FOOTER = """
    <p><a href="{homepage_path}" >Back to home</a></p>
    </div>
    <script src="{bootstrap_js}"></script> 
</body>
</html>
"""


@dataclass
class DeterminePlaceGetterReq:
    required_places: int
    category: Optional[str]
    category_name: str


upload_scores = Blueprint("upload_scores", __name__, template_folder="templates")


def display_message(message: str) -> str:
    return f"<p>{message}</p>"


class UploadScoreForm(FlaskForm):
    environment = RadioField(
        "Environment",
        validators=[DataRequired()],
    )
    csv_file = FileField(
        "CSV file",
        validators=[
            FileRequired(),
            FileSize(max_size=3 * 1048576),  # 3mb
            FileAllowed(["csv"]),
        ],
    )
    confirm = BooleanField(
        "Confirm",
        description="All existing scores will be cleared and you will have to login to BCOE&M to manually set place-getters.",
        validators=[DataRequired()],
    )


@upload_scores.before_request
@must_be_authorized
def before_request() -> None:
    """Protect all of the admin endpoints."""
    pass


@upload_scores.route("/", methods=["GET", "POST"])
def show_form() -> Union[str, Response]:
    form = UploadScoreForm()
    form.environment.choices = current_app.config["BCOME_ENV_CHOICES"]

    if form.validate_on_submit():
        ok = True
        d = form.csv_file.data
        t_io = try_decode_stream(d.stream.read())

        if t_io is None:
            form.csv_file.errors.append("Binary files not supported!")
            ok = False

        if t_io and not is_csv(t_io):
            form.csv_file.errors.append("Does not appear to be a CSV")
            ok = False

        if not ok:
            return render_template(f"upload_scores_form.html", form=form)

        vhr = validate_headers(t_io)
        if not vhr.ok:
            form.csv_file.errors.append(f"Missing required headers: {vhr.missing}")
            return render_template(f"upload_scores_form.html", form=form)

        homepage_path = url_for("homepage.show")

        user_name = g.user_name
        user_email = g.user_email
        bootstrap_css = url_for("static", filename="css/bootstrap.min.css")
        bootstrap_js = url_for("static", filename="js/bootstrap.min.js")

        messages: List[str] = [MESSAGES_HEADER.format(bootstrap_css=bootstrap_css)]
        env_short_name = form.environment.data
        all_res_link = url_for("all_results.show", comp_env=env_short_name)
        env_full_name = [
            x[1]
            for x in current_app.config["BCOME_ENV_CHOICES"]
            if x[0] == env_short_name
        ][0]
        db_config = db_config_for_env_shortname(env_short_name, messages)
        remote_addr = request.remote_addr

        def stream_process_csv() -> Generator[str, Any, None]:
            for m in messages:
                yield (display_message(m))
            messages.clear()

            if t_io is None:
                abort(500, "Expected a stream")

            filename = save_upload(
                t_io, user_name, user_email, env_short_name, remote_addr
            )
            yield (display_message(f"Saved upload to {filename}"))

            entries: List[ScoreEntry] = []

            try:
                entries = load_entries_from_csv(t_io)
            except Exception as e:
                yield (f"Error loading CSV: {e}")
                yield (
                    MESSAGES_FOOTER.format(
                        homepage_path=homepage_path, bootstrap_js=bootstrap_js
                    )
                )
                return

            yield (display_message(f"Loaded entries from CSV"))

            cnn: Optional[MySQLConnection] = None

            try:
                cnn = get_db_connection(db_config)
            except Exception as e:
                yield (f"Error connecting to database: {e}")
                yield (
                    MESSAGES_FOOTER.format(
                        homepage_path=homepage_path, bootstrap_js=bootstrap_js
                    )
                )
                return

            yield (display_message("Connected to DB."))
            yield (display_message(f"Starting data validation..."))

            data_valid = prepare_entries(cnn, entries, messages)
            for m in messages:
                yield (display_message(m))
            messages.clear()

            if not data_valid:
                yield (
                    MESSAGES_FOOTER.format(
                        homepage_path=homepage_path, bootstrap_js=bootstrap_js
                    )
                )
                return

            yield (display_message("Data validation succeeded"))
            yield (display_message("Starting backup..."))
            backup_and_clear_scores(cnn, env_short_name, messages)
            for m in messages:
                yield (display_message(m))
            messages.clear()

            yield (display_message("Checking database state..."))

            db_ok = check_create_westgate_fields(cnn, messages)
            for m in messages:
                yield (display_message(m))
            messages.clear()

            if not db_ok:
                yield (
                    MESSAGES_FOOTER.format(
                        homepage_path=homepage_path, bootstrap_js=bootstrap_js
                    )
                )
                return

            yield (display_message(f"Sorting entries and determining place getters..."))
            yield (display_message(f"{len(entries)} entries"))
            entries.sort(reverse=True)

            yield (display_message("Loading brewer list..."))
            brewer_dict = get_brewer_dict(cnn)

            for e in entries:
                brewer = brewer_dict[e.brewer_id]
                e.brewer = brewer

            dpgrs: List[DeterminePlaceGetterReq] = [
                DeterminePlaceGetterReq(
                    category=None,
                    category_name="Brewer of Show",
                    required_places=1,
                ),
                DeterminePlaceGetterReq(
                    category="8",
                    category_name="Porter",
                    required_places=3,
                ),
                DeterminePlaceGetterReq(
                    category="9",
                    category_name="Stout",
                    required_places=3,
                ),
                DeterminePlaceGetterReq(
                    category="10",
                    category_name="Strong Stout",
                    required_places=3,
                ),
                DeterminePlaceGetterReq(
                    category="21",
                    category_name="Specialty",
                    required_places=3,
                ),
            ]

            for dpgr in dpgrs:
                if dpgr.category is None:
                    dpgr_res = determine_place_getters(
                        entries,
                        dpgr.required_places,
                    )
                else:
                    dpgr_res = determine_place_getters(
                        [x for x in entries if x.category == dpgr.category],
                        dpgr.required_places,
                    )

                if dpgr_res.success:
                    messages.append(f"Set places for {dpgr.category_name}")
                    if dpgr.category_name == "Brewer of Show":
                        set_special_best_winner(
                            cnn, dpgr_res.place_getters[0], "Brewer of Show", messages
                        )
                else:
                    messages.append(
                        f"Unable to set places for {dpgr.category_name}, unable to resolve count-back, must recall the judges"
                    )

            for m in messages:
                yield (display_message(m))
            messages.clear()

            yield (display_message(f"Saving scores to database, please standby..."))
            save_entries(cnn, entries)
            messages.append(f"{len(entries)} scores saved to the database!")
            messages.append(f"<a href={all_res_link}>View all results here!</a>")
            messages.append("-" * 20)
            messages.append("IMPORTANT!")
            messages.append("You *MUST* go back to BCOE&M and do the following:")
            messages.append("")
            messages.append("1. manually resolve any place-setters mentioned above")
            messages.append(
                "2. identify and set the best novice (using the all results link above + notnovice spreadsheet), use judging number with leading zeros to set: https://comps.westgatebrewers.org/index.php?section=admin&go=special_best_data"
            )
            messages.append("3. publish results")
            messages.append("")
            messages.append(
                "**Admin score reports will not work until place-getters are set**"
            )
            messages.append("-" * 20)
            messages.append("")
            messages.append("You may now close this tab")
            messages.append(
                MESSAGES_FOOTER.format(
                    homepage_path=homepage_path, bootstrap_js=bootstrap_js
                )
            )

            send_audit_email(
                reason=EmailReason.UploadScores,
                env_full_name=env_full_name,
                user_name=user_name,
                user_email=user_email,
            )

            for m in messages:
                yield (display_message(m))

        return current_app.response_class(stream_process_csv(), mimetype="text/html")

    return render_template(f"upload_scores_form.html", form=form)
