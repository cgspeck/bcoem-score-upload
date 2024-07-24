from dataclasses import dataclass
from typing import Dict, List
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


@dataclass
class BrewEntry:
    id: int
    name: str
    style: str  # e.g. Sweet Stout [BJCP 16A]
    category: str  # e.g. 9
    subcategory: str  # e.g. 01


def get_brew_entries(cnn: MySQLConnection) -> List[BrewEntry]:
    sql = """
SELECT `id`, `brewName`, `brewStyle`, `brewCategory`, `brewSubCategory`
FROM `brewing`
ORDER BY id ASC;
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for id, brewName, brewStyle, brewCategory, brewSubCategory in cursor:
        memo.append(
            BrewEntry(
                id=id,
                name=brewName,
                style=brewStyle,
                category=brewCategory,
                subcategory=brewSubCategory,
            )
        )

    return memo


def get_brew_entries_dict(cnn: MySQLConnection) -> Dict[int, BrewEntry]:
    memo = {}
    brew_entries = get_brew_entries(cnn)

    for brew in brew_entries:
        memo[brew.id] = brew

    return memo
