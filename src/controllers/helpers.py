from flask import current_app
from mysql.connector import MySQLConnection

from src.db import create_connection, execute_backup_query, execute_clear_query, extract_db_config
from src.utils import determine_config, save_backup


def backup_and_clear_scores(cnn: MySQLConnection, messages: list[str]):
    backup_path = do_backup(cnn)
    messages.append(f"Written backup to: {backup_path}")
    execute_clear_query(cnn)
    messages.append(f"Cleared out all scores")


def do_backup(cnn: MySQLConnection):
    backup_res = execute_backup_query(cnn)
    backup_path = save_backup(backup_res)
    return backup_path

def get_db_connection(db_config, messages: list[str]):
    messages.append(f"Extracted DB config.")
    cnn = create_connection(db_config)
    messages.append(f"Connected to DB.")
    return cnn

def db_config_for_env_shortname(env_short_name, messages):
    env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]
    messages.append(f"Selected {env_full_name}")
    config_file = determine_config(env_short_name)
    messages.append(f"Loading config from {config_file}")
    db_config = extract_db_config(config_file)
    return db_config
