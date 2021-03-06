from flask import current_app, render_template
from mysql.connector import MySQLConnection  # type: ignore
from src.db import (create_connection, execute_backup_query,
                    execute_clear_query, extract_db_config)
from src.utils import determine_config, save_backup


def backup_and_clear_scores(cnn: MySQLConnection,  env_short_name: str, messages: list[str]):
    backup_path = do_backup(cnn, env_short_name)
    messages.append(f"Written backup to: {backup_path}")
    execute_clear_query(cnn)
    messages.append(f"Cleared out all scores")


def do_backup(cnn: MySQLConnection, env_short_name: str):
    backup_res = execute_backup_query(cnn)
    backup_path = save_backup(backup_res, env_short_name)
    return backup_path

def get_db_connection(db_config):
    return create_connection(db_config)

def db_config_for_env_shortname(env_short_name, messages):
    env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]
    messages.append(f"Selected {env_full_name}")
    config_file = determine_config(env_short_name)
    messages.append(f"Loading config from {config_file}")
    db_config = extract_db_config(config_file)
    return db_config

def message_log(messages: list[str]):
    return render_template("message_log.html", messages=messages)
