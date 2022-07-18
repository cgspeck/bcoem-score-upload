from pathlib import Path
from flask import Blueprint, current_app, render_template
from flask_wtf import FlaskForm  # type: ignore
from wtforms import RadioField  # type: ignore
from wtforms.validators import DataRequired
from src.controllers.helpers import message_log  # type: ignore

from src.utils import determine_root, must_be_authorized

pad_upload_filenames = Blueprint("pad_upload_filenames", __name__, template_folder="templates")


class PadUploadFilenamesForm(FlaskForm):
    environment = RadioField(
        "Environment",
        validators=[DataRequired()],   
    )



@pad_upload_filenames.before_request
@must_be_authorized
def before_request():
    """Protect all of the admin endpoints."""
    pass


@pad_upload_filenames.route("/", methods=["GET", "POST"])
def show_form():
    form = PadUploadFilenamesForm()
    form.environment.choices = current_app.config["BCOME_ENV_CHOICES"]

    if form.validate_on_submit():
        env_short_name = form.environment.data
        env_full_name = [x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name][0]

        messages = [f"Padding out files for {env_full_name} environment"]
        user_docs = Path(determine_root(env_short_name), "user_docs").resolve()
        initalize_errors = False
        
        if not user_docs.exists():
            messages.append(f"Path '{user_docs}' does not exist!")
            initalize_errors = True
            
        if not user_docs.is_dir:
            messages.append(f"Path '{user_docs}' is not a folder!")
            initalize_errors = True
        
        if initalize_errors:
            return message_log(messages)
            
        messages.append(f"Iterating over {user_docs}")
        
        for child in user_docs.iterdir():
            messages.append(f"Inspecting {child}")
            if not child.is_file():
                messages.append("Skipping, not a file")
                continue
            
            if not child.suffix.lower() == ".pdf":
                messages.append("Skipping, not a pdf")
                continue
            
            stem = child.stem
            if len(stem) == 6:
                messages.append("Skipping, already 6 characters long")
                continue
                
            parsed = None
            
            try:
                parsed = int(stem)
            except Exception as e:
                messages.append(f"Skipping, error parsing stem: {e}")
                continue
        
            if parsed <= 0:
                messages.append(f"Skipping, parsed result less then or equal to 0: {parsed}")
                continue
            
            dest = Path(user_docs, f"{parsed:06}.pdf").resolve()
            
            if dest.exists():
                messages.append(f"Skipping, {dest} already exists")
                continue
        
            messages.append(f"Moving to {dest}")
            child.rename(dest)
        
        messages.append("Complete")

        return message_log(messages)

    return render_template(f"pad_upload_filenames.html", form=form)
