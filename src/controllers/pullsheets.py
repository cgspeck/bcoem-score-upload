from typing import List, Optional
from flask import Blueprint, current_app, render_template, request

from src.controllers.helpers import db_config_for_env_shortname, get_db_connection, message_log
from src.models.pullsheets import get_data
from src.utils import must_have_valid_compenv, topt_or_authorized
from mysql.connector import MySQLConnection

pullsheets = Blueprint("pullsheets", __name__, template_folder="templates")

@pullsheets.before_request
@topt_or_authorized
@must_have_valid_compenv
def before_request() -> None:
    """Protect all of the admin endpoints."""
    pass


@pullsheets.route("")
def show() -> str:
    env_short_name = request.args.get('comp_env')
    env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]

    messages: List[str] = []
    db_config = db_config_for_env_shortname(env_short_name, messages)
    cnn: Optional[MySQLConnection] = None

    try:
        cnn = get_db_connection(db_config)
    except Exception as e:
        messages.append(f"Error connecting to database: {e}")
        return message_log(messages)

    tables = get_data(cnn)
    return render_template(f"pullsheets.html", env_full_name=env_full_name, tables=tables)
