from flask import Blueprint, render_template
from flask_wtf.file import FileField, FileRequired, FileAllowed, FileSize
from wtforms.validators import DataRequired
from wtforms import BooleanField, RadioField
from flask_wtf import FlaskForm
from flask import current_app
from src.csv_validate import (
    REQUIRED_HEADERS,
    has_required_headers,
    is_csv,
    try_decode_stream,
)

from src.utils import must_be_authorized, save_upload


upload_scores = Blueprint("upload_scores", __name__, template_folder="templates")


class UploadScoreForm(FlaskForm):
    environment = RadioField(
        "Environment",
        validators=[DataRequired()],
    )
    clear_existing = BooleanField(
        "Clear existing scores before run?",
        default=True,
    )
    csv_file = FileField(
        "CSV file",
        validators=[
            FileRequired(),
            FileSize(max_size=3 * 1048576),  # 3mb
            FileAllowed(["csv"]),
        ],
    )
    confirm = BooleanField("Confirm", validators=[DataRequired()])


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

        save_upload(t_io)

        return "success!"

    return render_template(f"upload_scores_form.html", form=form)
