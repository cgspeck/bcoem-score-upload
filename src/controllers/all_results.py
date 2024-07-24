from typing import List, Optional
from flask import Blueprint, current_app, render_template, request

from src.controllers.helpers import db_config_for_env_shortname, get_db_connection, message_log
# from src.models.pullsheets import get_data
from src.datadefs import ResultsDisplayInfo, ScoreEntry
from src.models import score_entries
from src.utils import must_be_authorized
from mysql.connector import MySQLConnection

all_results = Blueprint("all_results", __name__, template_folder="templates")

@all_results.before_request
@must_be_authorized
def before_request() -> None:
    """Protect all of the admin endpoints."""
    pass


@all_results.route("")
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

    entries: list[ScoreEntry] = score_entries.load_all(cnn)
    results_display_info = ResultsDisplayInfo(
        category_heading="Full Results List",
        category_blurb=None,
        show_entry_count=True,
        show_place_column=True,
        show_countback=True,
        show_entry_id=True,
        show_judging_table=True,
        entries=entries,
    )

    return render_template(
        f"all_results.html",
        env_full_name=env_full_name,
        results_display_info=results_display_info,
    )
