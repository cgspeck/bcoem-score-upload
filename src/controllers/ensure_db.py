from typing import Any, Generator, List, Optional, Union
from flask import Blueprint, Response, current_app, request, url_for
from mysql.connector import MySQLConnection

from src.controllers.helpers import db_config_for_env_shortname, get_db_connection
from src.models.judging_scores import check_create_westgate_fields
from src.utils import must_be_authorized


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
ensure_db = Blueprint("ensure_db", __name__, template_folder="templates")


def display_message(message: str) -> str:
    return f"<p>{message}</p>"


@ensure_db.before_request
@must_be_authorized
def before_request() -> None:
    """Protect all of the admin endpoints."""
    pass

@ensure_db.route("/", methods=["GET"])
def show() -> Union[str, Response]:
    homepage_path = url_for("homepage.show")
    env_short_name = request.args.get("comp_env")
    bootstrap_css = url_for("static", filename="css/bootstrap.min.css")
    bootstrap_js = url_for("static", filename="js/bootstrap.min.js")
    messages: List[str] = [MESSAGES_HEADER.format(bootstrap_css=bootstrap_css)]
    db_config = db_config_for_env_shortname(env_short_name, messages)

    def stream_process_csv() -> Generator[str, Any, None]:
        for m in messages:
            yield (display_message(m))
        messages.clear()

        yield (display_message(f"Connecting to {env_short_name} database"))

        cnn: Optional[MySQLConnection] = None

        try:
            cnn = get_db_connection(db_config)
        except Exception as e:
            yield (display_message(f"Error connecting to database: {e}"))
            yield (
                display_message(
                    MESSAGES_FOOTER.format(
                        homepage_path=homepage_path, bootstrap_js=bootstrap_js
                    )
                )
            )
            return

        yield (display_message("Connected to DB."))
        yield (display_message(f"Starting data validation..."))
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

        for m in messages:
            yield (display_message(m))

    return current_app.response_class(stream_process_csv(), mimetype="text/html")
