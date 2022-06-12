import os
from pprint import pprint
from flask import Flask, abort, g, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint
from functools import wraps
from src.controllers.clear_scores import clear_scores
from src.controllers.homepage import homepage
from src.controllers.upload_scores import upload_scores
from src.controllers import dir_listing

from src.logging import setup_logger
from src.utils import BACKUP_PATH, ensure_paths_exist

setup_logger()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
app.config["BCOME_TEST_CONF"] = os.environ.get("BCOME_TEST_CONF")
app.config["BCOME_PROD_CONF"] = os.environ.get("BCOME_PROD_CONF")
bcome_env_choices = []

if app.config["BCOME_TEST_CONF"] is not None:
    bcome_env_choices.append(("test", "Test Environment"))
    
if app.config["BCOME_PROD_CONF"] is not None:
    bcome_env_choices.append(("prod", "Production Environment"))

app.config["BCOME_ENV_CHOICES"] = bcome_env_choices
app.config["BCOME_ENVS_EXIST"] = (
    app.config["BCOME_TEST_CONF"] is not None
    or app.config["BCOME_PROD_CONF"] is not None
)
google_bp = make_google_blueprint(
    scope=["profile", "email"], redirect_url=os.environ.get("APPLICATION_ROOT", None)
)
app.register_blueprint(google_bp, url_prefix="/login")
app.config["AUTHORIZED_USERS"] = [
    e.lower() for e in os.environ.get("AUTHORIZED_USERS", "").split(",")
]


app.register_blueprint(homepage)

if app.config["BCOME_ENVS_EXIST"]:
    app.register_blueprint(clear_scores, url_prefix="/clear-scores")
    app.register_blueprint(upload_scores, url_prefix="/upload-scores")

app.register_blueprint(dir_listing.construct_blueprint(
    dir=BACKUP_PATH,
    display_name="Backup",
    name="backup"
), url_prefix="/backups")

if app.debug:
    pprint(app.url_map)

ensure_paths_exist()
