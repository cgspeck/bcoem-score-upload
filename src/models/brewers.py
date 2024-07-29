from dataclasses import dataclass
from typing import Dict, List, Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


@dataclass
class Brewer:
    id: int
    uid: int
    last_name: str
    first_name: str
    club: Optional[str]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __lt__(s, o):
        if not isinstance(o, s.__class__):
            return False

        return s.last_name < o.last_name

    def __gt__(s, o):
        return not s < o


def get_brewers(cnn: MySQLConnection) -> List[Brewer]:
    sql = """
SELECT id, uid, brewerFirstName, brewerLastName, brewerClubs
FROM `brewer`
ORDER BY id ASC;
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for id, uid, brewerFirstName, brewerLastName, brewerClubs in cursor:
        memo.append(
            Brewer(
                id=id,
                uid=uid,
                last_name=brewerLastName,
                first_name=brewerFirstName,
                club=brewerClubs,
            )
        )

    return memo


def get_brewer_dict(cnn: MySQLConnection) -> Dict[int, Brewer]:
    memo = {}
    brewers = get_brewers(cnn)

    for brewer in brewers:
        memo[brewer.id] = brewer

    return memo


def get_brewer_uid_dict(cnn: MySQLConnection) -> Dict[int, Brewer]:
    memo = {}
    brewers = get_brewers(cnn)

    for brewer in brewers:
        memo[brewer.uid] = brewer

    return memo
