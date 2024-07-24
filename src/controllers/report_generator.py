from copy import deepcopy
from dataclasses import dataclass
from typing import List, Optional, Set
from flask import Blueprint, current_app, render_template, request

from src import constants
from src.controllers.helpers import (
    db_config_for_env_shortname,
    get_db_connection,
    message_log,
)
from src.datadefs import CountbackStatus, ResultsDisplayInfo, ScoreEntry
from src.models import score_entries
from src.models import special_best_data
from src.utils import must_be_authorized
from mysql.connector import MySQLConnection

report_generator = Blueprint("report_generator", __name__, template_folder="templates")


@report_generator.before_request
@must_be_authorized
def before_request() -> None:
    """Protect all of the admin endpoints."""
    pass


@dataclass
class CategoryNameCodeCombo:
    category_name: str
    category_code: str


CATEGORIES_COMBOS = [
    CategoryNameCodeCombo("Porter", "8"),
    CategoryNameCodeCombo("Stout", "9"),
    CategoryNameCodeCombo("Strong Stout", "10"),
    CategoryNameCodeCombo("Specialty", "21"),
]


@report_generator.route("")
def show() -> str:
    env_short_name = request.args.get("comp_env")
    presentation_mode = request.args.get("presentation_mode", False)

    env_full_name = [
        x[1] for x in current_app.config["BCOME_ENV_CHOICES"] if x[0] == env_short_name
    ][0]

    messages: List[str] = []
    db_config = db_config_for_env_shortname(env_short_name, messages)
    cnn: Optional[MySQLConnection] = None

    try:
        cnn = get_db_connection(db_config)
    except Exception as e:
        messages.append(f"Error connecting to database: {e}")
        return message_log(messages)

    entries: list[ScoreEntry] = score_entries.load_all(cnn)

    best_novice = []
    sbd_novice = special_best_data.get_by_sbi_name(cnn, constants.BEST_NOVICE)

    if sbd_novice is not None:
        best_novice = [e for e in entries if e.entry_id == sbd_novice.eid]

    brewer_of_show = []
    sbd_brewer_of_show = special_best_data.get_by_sbi_name(
        cnn, constants.BREWER_OF_SHOW
    )

    if sbd_brewer_of_show is not None:
        brewer_of_show = [e for e in entries if e.entry_id == sbd_brewer_of_show.eid]

    placegetter_display_infos: List[ResultsDisplayInfo] = [
        ResultsDisplayInfo(
            category_heading=constants.BREWER_OF_SHOW,
            category_blurb="Brewer of Show will be awarded to the highest scoring beer in the competition.",
            show_entry_count=False,
            show_place_column=False,
            show_countback=presentation_mode,
            show_entry_id=False,
            show_judging_table=False,
            entries=brewer_of_show,
        ),
        ResultsDisplayInfo(
            category_heading=constants.BEST_NOVICE,
            category_blurb="The Best Novice Trophy is awarded to the highest score by a Victorian brewer who has not placed in a VicBrew accredited competition.",
            show_entry_count=False,
            show_place_column=False,
            show_countback=False,
            show_entry_id=False,
            show_judging_table=False,
            entries=best_novice,
        ),
    ]

    all_results_display_infos: List[ResultsDisplayInfo] = []

    for cc in CATEGORIES_COMBOS:
        placegetter_entries = sorted(
            [
                deepcopy(x)
                for x in entries
                if x.category == cc.category_code and x.score_place is not None
            ],
            reverse=True,
        )

        placegetter_entry_ids = [p.entry_id for p in placegetter_entries]

        for placegetter in placegetter_entries:
            if placegetter.countback_status is None:
                continue

            kept_countback_status: Set[CountbackStatus] = set()
            for cbs in placegetter.countback_status:
                if cbs.conflict_entry_id in placegetter_entry_ids:
                    kept_countback_status.add(cbs)
            placegetter.countback_status = kept_countback_status

        placegetter_display_infos.append(
            ResultsDisplayInfo(
                category_heading=cc.category_name,
                category_blurb=None,
                show_entry_count=False,
                show_place_column=True,
                show_countback=presentation_mode,
                show_entry_id=True,
                show_judging_table=False,
                entries=placegetter_entries,
            )
        )

        all_results_display_infos.append(
            ResultsDisplayInfo(
                category_heading=cc.category_name,
                category_blurb=None,
                show_entry_count=True,
                show_place_column=False,
                show_countback=presentation_mode,
                show_entry_id=presentation_mode,
                show_judging_table=False,
                entries=sorted(
                    [e for e in entries if e.category == cc.category_code], reverse=True
                ),
            )
        )

    return render_template(
        f"report_generator.html",
        env_full_name=env_full_name,
        placegetter_display_infos=placegetter_display_infos,
        all_results_display_infos=all_results_display_infos,
        presentation_mode=presentation_mode,
    )
