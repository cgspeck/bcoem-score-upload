from flask import Blueprint, render_template

from src.utils import must_be_authorized


homepage = Blueprint("home_page", __name__, template_folder="templates")


@homepage.before_request
@must_be_authorized
def before_request():
    """Protect all of the admin endpoints."""
    pass


@homepage.route("/")
def show():
    return render_template(f"home.html")
