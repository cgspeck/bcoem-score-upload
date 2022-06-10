from flask import Blueprint, render_template
from wtforms.validators import DataRequired
from wtforms import BooleanField, RadioField
from flask_wtf import FlaskForm
from flask import current_app
from src.db import create_connection, execute_backup_query, execute_clear_query, extract_db_config
from src.utils import determine_config, must_be_authorized, save_backup
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
        env_short_name = form.environment.data
        env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]
        messages.append(f"Selected {env_full_name}")
        config_file = determine_config(env_short_name)
        messages.append(f"Loading config from {config_file}")
        db_config = extract_db_config(config_file)
        messages.append(f"Extracted DB config.")
        cnn = create_connection(db_config)
        messages.append(f"Connected to DB.")
        backup_res = execute_backup_query(cnn)
        backup_path = save_backup(backup_res)
        messages.append(f"Written backup to: {backup_path}")
        execute_clear_query(cnn)
        messages.append(f"Cleared out all scores")
        return message_log(messages)

    return render_template(f"clear_scores_form.html", form=form)
