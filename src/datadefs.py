from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set, Union
from urllib.parse import quote

from src.models.brew_entries import BrewEntry
from src.models.brewers import Brewer
from src.models.judging_tables import JudgingTable


PHPKEY_DBCONFIG_MAP = {
    "$username": "user",
    "$password": "password",
    "$hostname": "host",
    "$database": "database",
    "$database_port": "port",
}


@dataclass
class DBConfig:
    user: str
    password: str
    host: str
    database: str
    port: int
    collation: str = "utf8mb4_unicode_ci"

    def to_dict(self) -> dict[str, Union[str, int]]:
        return asdict(self)

    def to_uri(self) -> str:
        return f"mysql+mysqldb://{quote(self.user)}:{quote(self.password)}@{self.host}:{self.port}/{self.database}?collation={quote(self.collation)}"


def make_cat_subcat_key(category: str, sub_category: str) -> str:
    _category = category
    _sub_category = sub_category

    if _category.isdecimal():
        _category = f"{int(_category)}"

    if _sub_category.isdecimal():
        _sub_category = f"{int(_sub_category)}"

    return f"{_category}-{_sub_category}"


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class CountbackStatus(AutoName):
    OVERALL_IMPRESSION = auto()
    FLAVOUR = auto()
    SMALLEST_SCORE_SPREAD = auto()
    RECALL_JUDGES = auto()


@dataclass(frozen=True)
class CountbackStatusRec:
    status: CountbackStatus
    conflict_entry_id: int

    def __str__(self) -> str:
        return f"{self.status.value} vs {self.conflict_entry_id}"

    def to_db_str(self) -> str:
        return self.__str__()

    def to_report_str(self) -> str:
        e_val = f"{self.status.value}"
        return f"{e_val.replace('_', ' ').title()} vs {self.conflict_entry_id}"

    @classmethod
    def from_db_str(kls, s: str) -> CountbackStatusRec:
        tokens = s.split(" vs ")
        enum_str = tokens[0]
        enum_val = CountbackStatus(enum_str)
        conflict_id = int(tokens[1])
        return kls(enum_val, conflict_id)

    def __repr__(self) -> str:
        return f"CountbackStatusRec(status='{self.status.value}' conflict_entry_id={self.conflict_entry_id})"


@dataclass
class ResultsDisplayInfo:
    category_heading: str
    category_blurb: Optional[str]
    show_entry_count: bool
    show_place_column: bool
    show_countback: bool
    show_entry_id: bool
    show_judging_table: bool
    entries: List[ScoreEntry]

@dataclass(order=False)
class ScoreEntry:
    entry_id: int  # 'eid'
    category: str  # there are entries like "C1", "B1" on other style guides
    sub_category: str  # alphanumeric styles exist
    total_score: float  # this is called 'scoreEntry' in BCOE&M
    aroma: float  # this is wg_aroma
    appearance: float  # this is wg_appearance
    flavour: float  # this is wg_flavour
    body: float  # this is wg_body
    overall: float  # this is wg_overall
    score_spread: float  # this is wg_score_spread

    brewer_id: Optional[int] = None  # 'bid'
    style_id: Optional[int] = None  # allocated to judging tables
    score_table: Optional[int] = None  # 'scoreTable'

    style_key: str = field(init=False)

    score_type: int = 1  # 'scoreType'

    # calculated score place as an int
    # maps to 'scorePlace, varchar3 in database
    score_place: Optional[int] = None
    # used to store & display countback status
    countback_status: Set[CountbackStatusRec] = field(default_factory=set)

    # Only used for displaying reports
    brewer: Optional[Brewer] = None
    brew_entry: Optional[BrewEntry] = None
    judging_table: Optional[JudgingTable] = None

    def countback_status_db_repr(self):
        if len(self.countback_status) == 0:
            return None

        return ", ".join([x.to_db_str() for x in self.countback_status])

    def __post_init__(self) -> None:
        self.style_key = make_cat_subcat_key(self.category, self.sub_category)

    def __lt__(s, o):
        if not isinstance(o, s.__class__):
            return False

        if s.total_score != o.total_score:
            return s.total_score < o.total_score

        if s.overall != o.overall:
            s.countback_status.add(
                CountbackStatusRec(CountbackStatus.OVERALL_IMPRESSION, o.entry_id)
            )
            o.countback_status.add(
                CountbackStatusRec(CountbackStatus.OVERALL_IMPRESSION, s.entry_id)
            )
            return s.overall < o.overall

        if s.flavour != o.flavour:
            s.countback_status.add(
                CountbackStatusRec(CountbackStatus.FLAVOUR, o.entry_id)
            )
            o.countback_status.add(
                CountbackStatusRec(CountbackStatus.FLAVOUR, s.entry_id)
            )
            return s.flavour < o.flavour

        if s.score_spread != o.score_spread:
            s.countback_status.add(
                CountbackStatusRec(CountbackStatus.SMALLEST_SCORE_SPREAD, o.entry_id)
            )
            o.countback_status.add(
                CountbackStatusRec(CountbackStatus.SMALLEST_SCORE_SPREAD, s.entry_id)
            )
            return s.score_spread < o.score_spread

        s.countback_status.add(
            CountbackStatusRec(CountbackStatus.RECALL_JUDGES, o.entry_id)
        )
        o.countback_status.add(
            CountbackStatusRec(CountbackStatus.RECALL_JUDGES, s.entry_id)
        )
        return False

    def __gt__(s, o):
        return not s < o
