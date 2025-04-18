from dataclasses import dataclass
from typing import Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from src.datadefs import ScoreEntry
from src.models import special_best_info

@dataclass
class SpecialBestData:
    id: int
    sid: int  # special best info id
    bid: int  # brewer id
    eid: int  # entry id
    sbd_place: int  # only ever 1


def set_special_best_winner(
    cnn: MySQLConnection, se: ScoreEntry, name: str, messages: list[str]
) -> bool:
    sbi = special_best_info.get_by_name(cnn, name)

    if sbi is None:
        messages.append(f"Error: could not find special_best_info record for {name}")
        return False

    sql = """
DELETE FROM special_best_data
WHERE sid = %s;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (sbi.id,))
    cursor.fetchone()

    sql = """
INSERT INTO special_best_data (sid, bid, eid, sbd_place)
VALUES (%s, %s, %s, %s)
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (sbi.id, se.brewer_id, se.entry_id, 1))
    cursor.fetchone()
    messages.append(
        f"Set '{name}' to '{se.brewer.first_name} {se.brewer.last_name}' for entry {se.entry_id}"
    )
    return True

def get_by_sbi_name(cnn: MySQLConnection, name: str) -> Optional[SpecialBestData]:
    sbi = special_best_info.get_by_name(cnn, name)

    if sbi is None:
        return None

    sql = """
SELECT id, sid, bid, eid, sbd_place
FROM special_best_data
WHERE sid = %s;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (sbi.id,))
    rec = cursor.fetchone()

    return SpecialBestData(id=rec[0], sid=rec[1], bid=rec[2], eid=rec[3], sbd_place=rec[4])
