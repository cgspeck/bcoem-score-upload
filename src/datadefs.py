from dataclasses import asdict, dataclass
from typing import Optional, Union
from unicodedata import category

from attr import field


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

    def to_dict(self) -> dict[str, Union[str, int]]:
        return asdict(self)


def make_cat_subcat_key(category: str, sub_category: str) -> str:
    _category = category
    _sub_category = sub_category
    
    if _category.isdecimal():
        _category = f"{int(_category)}"

    if _sub_category.isdecimal():
        _sub_category = f"{int(_sub_category)}"

    return f"{_category}-{_sub_category}"

@dataclass
class ScoreEntry:
    entry_id: int # 'eid'
    category: str  # there are entries like "C1", "B1" on other style guides
    sub_category: str  # alphanumeric styles exist
    total_score: float  # this is called 'scoreEntry' in BCOE&M
    
    brewer_id: Optional[int] = None # 'bid'
    style_id: Optional[int] = None # allocated to judging tables
    score_table: Optional[int] = None # 'scoreTable'
    
    style_key: str = field(init=False)

    score_type: str = "1" # 'scoreType'
    
    def __post_init__(self):
        self.style_key = make_cat_subcat_key(self.category, self.sub_category)
