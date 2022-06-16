from typing import Optional
from flask import Blueprint, current_app, g, render_template, request, url_for
from flask_wtf import FlaskForm  # type: ignore
from flask_wtf.file import (FileAllowed, FileField,  # type: ignore
                            FileRequired, FileSize)
from wtforms import BooleanField, RadioField  # type: ignore
from wtforms.validators import DataRequired  # type: ignore
from mysql.connector import MySQLConnection  # type: ignore

from src.controllers.helpers import (backup_and_clear_scores,
                                     db_config_for_env_shortname,
                                     get_db_connection)
from src.csv_validate import (REQUIRED_HEADERS, has_required_headers, is_csv,
                              try_decode_stream)
from src.datadefs import ScoreEntry
from src.email import EmailReason, send_audit_email
from src.score_process import (load_entries_from_csv, prepare_entries,
                               save_entries)
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
upload_scores = Blueprint("upload_scores", __name__, template_folder="templates")

def display_message(message: str):
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
        validators=[DataRequired()]
    )


@upload_scores.before_request
@must_be_authorized
def before_request():
    """Protect all of the admin endpoints."""
    pass


@upload_scores.route("/", methods=["GET", "POST"])
def show_form():
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

        if t_io and not has_required_headers(t_io):
            form.csv_file.errors.append(f"Missing required headers: {REQUIRED_HEADERS}")
            ok = False

        if not ok:
            return render_template(f"upload_scores_form.html", form=form)

        homepage_path = url_for('home_page.show')
        user_name = g.user_name
        user_email = g.user_email
        bootstrap_css = url_for('static', filename='css/bootstrap.min.css')
        bootstrap_js = url_for('static', filename='js/bootstrap.min.js')

        messages: list[str] = [MESSAGES_HEADER.format(bootstrap_css=bootstrap_css)]
        env_short_name = form.environment.data
        env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]
        db_config = db_config_for_env_shortname(env_short_name, messages)
        remote_addr = request.remote_addr

        def stream_process_csv():
            for m in messages:
                yield(display_message(m))
            messages.clear()

            filename = save_upload(t_io, user_name, user_email, env_short_name, remote_addr)
            yield(display_message(f"Saved upload to {filename}"))

            entries: list[ScoreEntry] = []

            try:
                entries = load_entries_from_csv(t_io)
            except Exception as e:
                yield(f"Error loading CSV: {e}")
                yield(MESSAGES_FOOTER.format(homepage_path=homepage_path, bootstrap_js=bootstrap_js))
                return

            yield(display_message(f"Loaded entries from CSV"))

            cnn: Optional[MySQLConnection] = None

            try:
                cnn = get_db_connection(db_config)
            except Exception as e:
                yield(f"Error connecting to database: {e}")
                yield(MESSAGES_FOOTER.format(homepage_path=homepage_path, bootstrap_js=bootstrap_js))
                return

            yield(display_message("Connected to DB."))
            yield(display_message(f"Starting data validation..."))

            data_valid = prepare_entries(cnn, entries, messages)
            for m in messages:
                yield(display_message(m))
            messages.clear()

            if not data_valid:
                yield(MESSAGES_FOOTER.format(homepage_path=homepage_path, bootstrap_js=bootstrap_js))
                return

            yield(display_message("Data validation succeeded"))
            yield(display_message("Starting backup..."))
            backup_and_clear_scores(cnn, env_short_name, messages)
            for m in messages:
                yield(display_message(m))
            messages.clear()
            yield(display_message(f"Saving scores to database, please standby..."))
            save_entries(cnn, entries)
            messages.append(f"{len(entries)} scores saved to the database!")
            messages.append("-" * 20)
            messages.append("IMPORTANT!")
            messages.append("You *MUST* go back to BCOE&M and do the following:")
            messages.append("")
            messages.append("1. set place-getters for each table")
            messages.append("2. publish results")
            messages.append("")
            messages.append("**Admin score reports will not work until place-getters are set**")
            messages.append("-" * 20)
            messages.append("")
            messages.append("You may now close this tab")
            messages.append(MESSAGES_FOOTER.format(homepage_path=homepage_path, bootstrap_js=bootstrap_js))

            send_audit_email(
                reason=EmailReason.UploadScores,
                env_full_name=env_full_name,
                user_name=user_name,
                user_email=user_email
            )

            for m in messages:
                yield(display_message(m))

        return current_app.response_class(stream_process_csv(), mimetype='text/html')

    return render_template(f"upload_scores_form.html", form=form)
