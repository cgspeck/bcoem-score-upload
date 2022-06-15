from flask import Blueprint, g, render_template
from wtforms.validators import DataRequired
from wtforms import BooleanField, RadioField
from flask_wtf import FlaskForm
from flask import current_app
from src.controllers.helpers import backup_and_clear_scores, db_config_for_env_shortname, get_db_connection, message_log
from src.email import EmailReason, send_audit_email
from src.utils import must_be_authorized


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
        user_name = g.user_name
        user_email = g.user_email
        env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == form.environment.data][0]

        messages = []
        db_config = db_config_for_env_shortname(form.environment.data, messages)
        cnn = get_db_connection(db_config, messages)
        backup_and_clear_scores(cnn, messages)

        send_audit_email(
            reason=EmailReason.ClearTable,
            env_full_name=env_full_name,
            user_name=user_name,
            user_email=user_email
        )
        return message_log(messages)

    return render_template(f"clear_scores_form.html", form=form)
