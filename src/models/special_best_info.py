from dataclasses import dataclass
from typing import Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

@dataclass
class SpecialBestInfo:
    id: int
    name: Optional[str]
    description: Optional[str]


def get_by_name(cnn: MySQLConnection, name: str) -> Optional[SpecialBestInfo]:
    sql = """
SELECT id, sbi_name, sbi_description
FROM special_best_info
WHERE sbi_name = %s
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (name,))
    rec = cursor.fetchone()

    if rec is None:
        return None

    return SpecialBestInfo(
        id=rec[0],
        name=rec[1],
        description=rec[2]
    )
