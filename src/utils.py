from datetime import datetime
from io import StringIO
from pathlib import Path
import time
from typing import Optional
from flask import abort, g, redirect, url_for, current_app
import flask
from flask_dance.contrib.google import google
from functools import wraps

import oauthlib

from src import topt

BACKUP_PATH = Path("data/backups").resolve()
UPLOAD_PATH = Path("data/uploads").resolve()

SECONDS_PER_DAY = 86400
DEFAULT_RETENTION_DAYS = 3 * 365


def cleanup(dir: Path, retain_days: int) -> None:
    threshold = time.time() - (retain_days * SECONDS_PER_DAY)
    for p in dir.iterdir():
        if p.is_file() and p.stat().st_ctime < threshold:
            p.unlink()


def determine_config(env: str) -> str:
    if env == "test":
        return current_app.config["BCOME_TEST_CONF"]

    if env == "prod":
        return current_app.config["BCOME_PROD_CONF"]

    raise ValueError(f"Unknown env: '{env}'")


def determine_root(env: str) -> Path:
    conf_path = determine_config(env)
    return Path(conf_path, "../../").resolve().absolute()


def ensure_paths_exist() -> None:
    BACKUP_PATH.mkdir(parents=True, exist_ok=True)
    UPLOAD_PATH.mkdir(parents=True, exist_ok=True)


def format_error_message(msg: str, messages: list[str]) -> None:
    messages.append("")
    messages.append("ERROR!!!")
    messages.append("-" * 20)
    messages.append(msg)
    messages.append("-" * 20)


def must_have_valid_compenv(f):  # type: ignore
    @wraps(f)
    def decorated(*args, **kwargs):  # type: ignore
        request = flask.request
        comp_env = request.args.get("comp_env")
        if comp_env is None or len(comp_env.strip()) == 0:
            abort(400, "No comp_env param")

        env_short_choices = [x[0] for x in current_app.config["BCOME_ENV_CHOICES"]]

        if comp_env not in env_short_choices:
            abort(400, "Unrecognised environment")

        return f(*args, **kwargs)

    return decorated


def topt_or_authorized(f):  # type: ignore
    @wraps(f)
    def decorated(*args, **kwargs):  # type: ignore
        data = flask.request
        token = data.args.get("token", None)

        if token is not None and current_app.config["TOPT_ENABLED"]:
            token_valid = topt.validate(
                token,
                current_app.config["TOPT_SECRET"],
                current_app.config["TOPT_VALID_MINUTES"],
            )

            if token_valid:
                g.user_email = "topt-user@westgatebrewers.org"
                g.user_name = "TOPT User"
                return f(*args, **kwargs)

            abort(401, "Link timed out, regenerate from admin section in BCOE&M")

        # FIXME: dedupe code here and in must_be_authorized below which is a straight copy-paste
        if current_app.config["BYPASS_OAUTH"]:
            g.user_email = "dev@example.com"
            g.user_name = "Developer User"
            return f(*args, **kwargs)

        if not google.authorized:
            return redirect(url_for("google.login"))

        try:
            resp = google.get("/oauth2/v1/userinfo")
        except oauthlib.oauth2.rfc6749.errors.TokenExpiredError:
            return redirect(url_for("google.login"))

        assert resp.ok, resp.text

        email = resp.json()["email"].lower()
        user_name = resp.json()["name"]
        authorized = email in current_app.config["AUTHORIZED_USERS"]
        if not authorized:
            current_app.logger.error(
                "access attempt", extra={"user_email": email, "user_name": user_name}
            )
            abort(401)

        g.user_email = email
        g.user_name = user_name
        return f(*args, **kwargs)

    return decorated


def must_be_authorized(f):  # type: ignore
    @wraps(f)
    def decorated(*args, **kwargs):  # type: ignore
        if current_app.config["BYPASS_OAUTH"]:
            g.user_email = "dev@example.com"
            g.user_name = "Developer User"
            return f(*args, **kwargs)

        if not google.authorized:
            return redirect(url_for("google.login"))

        try:
            resp = google.get("/oauth2/v1/userinfo")
        except oauthlib.oauth2.rfc6749.errors.TokenExpiredError:
            return redirect(url_for("google.login"))

        assert resp.ok, resp.text

        email = resp.json()["email"].lower()
        user_name = resp.json()["name"]
        authorized = email in current_app.config["AUTHORIZED_USERS"]
        if not authorized:
            current_app.logger.error(
                "access attempt", extra={"user_email": email, "user_name": user_name}
            )
            abort(401)

        g.user_email = email
        g.user_name = user_name
        return f(*args, **kwargs)

    return decorated


def save_backup(
    data: list[str], env_short_name: str, retain_days: int = DEFAULT_RETENTION_DAYS
) -> Path:
    base_filename = f"{time.time()}.{env_short_name}"
    data_path = Path(BACKUP_PATH, f"{base_filename}.csv")
    data_path.write_text("\n".join(data))
    cleanup(BACKUP_PATH, retain_days)
    return data_path


def save_upload(
    data: StringIO,
    user_name: str,
    user_email: str,
    env_short_name: str,
    remote_addr: Optional[str] = None,
    retain_days: int = DEFAULT_RETENTION_DAYS,
) -> str:
    """
    Saves upload an metadata about uploader.
    Returns filename.
    """
    base_filename = f"{time.time()}.{env_short_name}"
    data_path = Path(UPLOAD_PATH, f"{base_filename}.csv")
    meta_path = Path(UPLOAD_PATH, f"{base_filename}.meta.txt")
    data_path.write_text(data.read())
    data.seek(0)

    meta_payload = f"""
Date: {datetime.now()}
User Name: {user_name}
User Email: {user_email}
Remote Address: {remote_addr}
"""
    meta_path.write_text(meta_payload)
    cleanup(UPLOAD_PATH, retain_days)
    return data_path.name
