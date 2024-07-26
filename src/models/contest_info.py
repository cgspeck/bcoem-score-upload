from dataclasses import dataclass
from typing import Dict, List
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


@dataclass
class ContestInfo:
    id: int
    name: str


def get_contest_info(cnn: MySQLConnection) -> ContestInfo:
    sql = """
SELECT id, contestName
FROM contest_info
ORDER BY id ASC
LIMIT 1;
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    rec = cursor.fetchone()

    return ContestInfo(id=rec[0], name=rec[1])
