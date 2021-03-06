from dataclasses import dataclass
import datetime
from pathlib import Path
from flask import Blueprint, render_template, send_from_directory

from src.utils import must_be_authorized

@dataclass
class FileListEntry:
    name: str
    size: int
    created_date: datetime.datetime

def construct_blueprint(name: str, dir: Path, display_name:str):
    bp = Blueprint(name, __name__, template_folder="templates")


    @bp.before_request
    @must_be_authorized
    def before_request():
        """Protect all of the admin endpoints."""
        pass


    @bp.route("/")
    def show():
        memo = []
        for p in dir.iterdir():
            st_info = p.stat()
            memo.append(FileListEntry(
                name=p.name,
                size=st_info.st_size,
                created_date=datetime.datetime.fromtimestamp(
                    st_info.st_ctime, 
                    tz=datetime.timezone.utc)
                
            ))

        memo.sort(key=lambda x: x.name, reverse=True)

        return render_template(
            "dir_listing.html",
            dl_view_name=f"{name}.download",
            display_name=display_name,
            entries=memo
        )
    
    @bp.route("/<path:filename>")
    def download(filename):
        return send_from_directory(dir, filename, as_attachment=True)
    
    return(bp)
