from flask import Blueprint, render_template
from wtforms.validators import DataRequired
from wtforms import BooleanField, RadioField
from flask_wtf import FlaskForm
from flask import current_app
from src.controllers.helpers import get_db_connection
from src.db import execute_backup_query, execute_clear_query
from src.utils import must_be_authorized, save_backup
from src.web_utils import message_log


clear_scores = Blueprint("clear_scores", __name__, template_folder="templates")


class ClearScoreForm(FlaskForm):
    environment = RadioField(
        "Environment",
        validators=[DataRequired()],
    )
    confirm = BooleanField("Confirm", validators=[DataRequired()])


@clear_scores.before_request
@must_be_authorized
def before_request():
    """Protect all of the admin endpoints."""
    pass


@clear_scores.route("/", methods=["GET", "POST"])
def show_form():
    form = ClearScoreForm()
    form.environment.choices = current_app.config["BCOME_ENV_CHOICES"]

    if form.validate_on_submit():
        messages = []
        cnn = get_db_connection(form.environment.data, messages)
        backup_res = execute_backup_query(cnn)
        backup_path = save_backup(backup_res)
        messages.append(f"Written backup to: {backup_path}")
        execute_clear_query(cnn)
        messages.append(f"Cleared out all scores")
        return message_log(messages)

    return render_template(f"clear_scores_form.html", form=form)
