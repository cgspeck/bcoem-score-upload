from typing import Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from src.datadefs import ScoreEntry


def _get_sbi_id(
    cnn: MySQLConnection, sbi_name: str, messages: list[str]
) -> Optional[int]:
    sql = """
SELECT id, sbi_name
FROM special_best_info
WHERE sbi_name = %s
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (sbi_name,))
    rec = cursor.fetchone()

    if rec is None:
        messages.append(f"Could not find special_best_info.sid for '{sbi_name}'")

    return rec[0]


def set_special_best_winner(
    cnn: MySQLConnection, se: ScoreEntry, sbi_name: str, messages: list[str]
) -> bool:
    sbi_id = _get_sbi_id(cnn, sbi_name, messages)

    if sbi_id is None:
        return False

    sql = """
DELETE FROM special_best_data
WHERE sid = %s;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (sbi_id,))
    cursor.fetchone()

    sql = """
INSERT INTO special_best_data (sid, bid, eid, sbd_place)
VALUES (%s, %s, %s, %s)
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (sbi_id, se.brewer_id, se.entry_id, 1))
    cursor.fetchone()
    messages.append(
        f"Set '{sbi_name}' to '{se.brewer.first_name} {se.brewer.first_name}' for entry {se.entry_id}"
    )
    return True
