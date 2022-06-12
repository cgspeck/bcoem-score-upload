from flask import current_app
from src.db import create_connection, extract_db_config

from src.utils import determine_config


def get_db_connection(env_short_name, messages):
    env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]
    messages.append(f"Selected {env_full_name}")
    config_file = determine_config(env_short_name)
    messages.append(f"Loading config from {config_file}")
    db_config = extract_db_config(config_file)
    messages.append(f"Extracted DB config.")
    cnn = create_connection(db_config)
    messages.append(f"Connected to DB.")
    return cnn
