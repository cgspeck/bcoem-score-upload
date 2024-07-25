from dataclasses import dataclass
from typing import Dict, List, Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


@dataclass
class Brewer:
    id: int
    last_name: str
    first_name: str
    club: Optional[str]


def get_brewers(cnn: MySQLConnection) -> List[Brewer]:
    sql = """
SELECT id, brewerFirstName, brewerLastName, brewerClubs
FROM `brewer`
ORDER BY id ASC;
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for id, brewerFirstName, brewerLastName, brewerClubs in cursor:
        memo.append(
            Brewer(
                id=id,
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
