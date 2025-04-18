from copy import deepcopy
from dataclasses import dataclass, field
import sys
from typing import Dict, List, Optional, Set
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
from src.models import staff
from src.models.contest_info import ContestInfo, get_contest_info
from src.models.sponsors import Sponsor, get_sponsors
from src.models.staff import StaffSummary
from src.utils import must_have_valid_compenv, topt_or_authorized
from mysql.connector import MySQLConnection

report_generator = Blueprint("report_generator", __name__, template_folder="templates")


@report_generator.before_request
@topt_or_authorized
@must_have_valid_compenv
def before_request() -> None:
    """Protect all of the admin endpoints."""
    pass


@dataclass
class CategoryNameCodeCombo:
    category_name: str
    category_code: str


@dataclass(order=False)
class ClubOfShowCandidate:
    name: str
    firsts_count: int = 0
    seconds_count: int = 0
    thirds_count: int = 0
    scores: list[float] = field(default_factory=list)
    average_score: float = 0
    entry_count: int = 0

    def score(self) -> int:
        return self.firsts_count * 3 + self.seconds_count * 2 + self.thirds_count * 1

    def __lt__(s, o):
        if not isinstance(o, s.__class__):
            return False

        self_score = s.score()
        other_score = o.score()

        if not self_score == other_score:
            return self_score < other_score

        self_average_score = s.average_score
        other_average_score = o.average_score

        if not self_average_score == other_average_score:
            return self_average_score < other_average_score

        self_entry_count = s.entry_count
        other_entry_count = o.entry_count

        return self_entry_count > other_entry_count

    def __gt__(s, o):
        return not s < o


CATEGORIES_COMBOS = [
    CategoryNameCodeCombo("Porter", "8"),
    CategoryNameCodeCombo("Stout", "9"),
    CategoryNameCodeCombo("Strong Stout", "10"),
    CategoryNameCodeCombo("Specialty", "21"),
]


@report_generator.route("")
def show() -> str:
    env_short_name = request.args.get("comp_env")
    presentation_mode = request.args.get("presentation_mode", "False") == "True"

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

    contest_info: Optional[ContestInfo] = None
    staff_summary: Optional[StaffSummary] = None
    sponsors: Optional[List[Sponsor]] = None

    if not presentation_mode:
        contest_info = get_contest_info(cnn)
        staff_summary = staff.get_summary(cnn)
        sponsors = get_sponsors(cnn)

    entries: list[ScoreEntry] = score_entries.load_all(cnn)

    for ent in entries:
        if ent.brewer.club is None:
            continue

        stripped_club = ent.brewer.club.strip()
        if len(stripped_club) == 0:
            ent.brewer.club = None

        if stripped_club.lower() == "none":
            ent.brewer.club = None

    entries_belonging_to_a_club = [
        e for e in entries if e.score_place is not None and e.brewer.club is not None
    ]
    club_of_show_dict: Dict[str, ClubOfShowCandidate] = dict()

    for club_of_show_entry in entries_belonging_to_a_club:
        club_name = club_of_show_entry.brewer.club

        if club_name not in club_of_show_dict:
            club_of_show_dict[club_name] = ClubOfShowCandidate(name=club_name)

        match club_of_show_entry.score_place:
            case 1:
                club_of_show_dict[club_name].firsts_count += 1
            case 2:
                club_of_show_dict[club_name].seconds_count += 1
            case 3:
                club_of_show_dict[club_name].thirds_count += 1

    entries_belonging_to_a_club = [e for e in entries if e.brewer.club is not None]
    for entry_belonging_to_a_club in entries_belonging_to_a_club:
        club_of_show_dict[club_name].entry_count += 1
        club_of_show_dict[club_name].scores.append(
            entry_belonging_to_a_club.total_score
        )

    for x in club_of_show_dict.values():
        if len(x.scores) == 0:
            continue

        x.average_score = sum(x.scores) / len(x.scores)

    club_of_show_list = [x for x in club_of_show_dict.values() if x.score() > 0]
    club_of_show_list.sort(reverse=True)

    print(
        f"club_of_show_list: {club_of_show_list}",
        file=sys.stderr,
    )

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
                show_entry_id=presentation_mode,
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
        club_of_show_list=club_of_show_list,
        placegetter_display_infos=placegetter_display_infos,
        all_results_display_infos=all_results_display_infos,
        presentation_mode=presentation_mode,
        staff_summary=staff_summary,
        contest_info=contest_info,
        sponsors=sponsors,
    )
