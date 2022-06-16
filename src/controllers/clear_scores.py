from typing import Optional
from flask import Blueprint, current_app, g, render_template
from flask_wtf import FlaskForm  # type: ignore
from wtforms import BooleanField, RadioField  # type: ignore
from wtforms.validators import DataRequired  # type: ignore
from mysql.connector import MySQLConnection  # type: ignore

from src.controllers.helpers import (backup_and_clear_scores,
                                     db_config_for_env_shortname,
                                     get_db_connection, message_log)
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
        env_short_name = form.environment.data
        env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]

        messages = []
        db_config = db_config_for_env_shortname(env_short_name, messages)
        cnn: Optional[MySQLConnection] = None

        try:
            cnn = get_db_connection(db_config)
        except Exception as e:
            messages.append(f"Error connecting to database: {e}")
            return message_log(messages)

        messages.append("Connected to DB.")
        backup_and_clear_scores(cnn, env_short_name, messages)

        send_audit_email(
            reason=EmailReason.ClearTable,
            env_full_name=env_full_name,
            user_name=user_name,
            user_email=user_email
        )
        return message_log(messages)

    return render_template(f"clear_scores_form.html", form=form)
