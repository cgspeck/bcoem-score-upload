import os
from flask import Flask, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersekrit")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(scope=["profile", "email"])
app.register_blueprint(google_bp, url_prefix="/login")
app.config["AUTHORIZED_USERS"] = [e.lower() for e in os.environ.get('AUTHORIZED_USERS', '').split(',')]

@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v1/userinfo")
    assert resp.ok, resp.text
    
    email = resp.json()["email"].lower()
    authorized = email in app.config["AUTHORIZED_USERS"]
    
    return "You are {email} on Google, and you are {authorized_msg} authorized.".format(
        authorized_msg="" if authorized else "not",
        email=resp.json()["email"]
    )

application = app
