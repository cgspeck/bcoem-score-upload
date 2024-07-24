from dataclasses import dataclass
from typing import List, Optional, Set
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

from src.datadefs import CountbackStatusRec


def check_create_westgate_fields(cnn: MySQLConnection, messages: list[str]) -> bool:
    wg_fields = [
        "wg_aroma",
        "wg_appearance",
        "wg_flavour",
        "wg_body",
        "wg_overall",
        "wg_score_spread",
        "wg_countback",
    ]
    sql = """
DESCRIBE judging_scores;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    existing_fields = []
    for r in cursor.fetchall():
        existing_fields.append(r[0])

    for f in wg_fields:
        if f not in existing_fields:
            messages.append(f"Creating {f} column...")
            sql = f"ALTER TABLE judging_scores ADD {f} FLOAT NULL"

            if f == "wg_countback":
                sql = f"ALTER TABLE judging_scores ADD {f} VARCHAR(255) NULL"

            cursor.execute(sql)
            cursor.fetchall()
            warnings = cursor.fetchwarnings()
            if warnings is None:
                continue

            for w in warnings:
                messages.append(f"{w[0]}: {w[1]}: {w[2]}")

    messages.append("Database state ok")
    return True


@dataclass
class JudgingScore:
    id: int  # db ID
    brewer_id: int # 'bid'
    score_table: int  # 'scoreTable'
    entry_id: int  # 'eid'
    total_score: float  # this is called 'scoreEntry' in BCOE&M
    aroma: float  # this is wg_aroma
    appearance: float  # this is wg_appearance
    flavour: float  # this is wg_flavour
    body: float  # this is wg_body
    overall: float  # this is wg_overall
    score_spread: float  # this is wg_score_spread
    countback_status: Optional[
        Set[CountbackStatusRec]
    ]  # stored as 'ENUM vs 123, ENUM vs 456'
    score_type: int = 1  # 'scoreType'
    score_place: Optional[int] = None  # stored as NULLABLE VarChar[3]

def load_all(cnn: MySQLConnection) -> List[JudgingScore]:
    sql = """
SELECT id, eid, bid, scoreTable, scoreEntry, scorePlace, scoreType, wg_aroma, wg_appearance, wg_flavour, wg_body, wg_overall, wg_score_spread, wg_countback
FROM judging_scores
ORDER BY scoreEntry DESC, cast(scorePlace as unsigned) ASC
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for (
        id,
        eid,
        bid,
        scoreTable,
        scoreEntry,
        scorePlace,
        scoreType,
        wg_aroma,
        wg_appearance,
        wg_flavour,
        wg_body,
        wg_overall,
        wg_score_spread,
        wg_countback,
    ) in cursor:
        score_place = None
        if scorePlace is not None:
            score_place = int(scorePlace)

        countback_status = None

        if wg_countback is not None:
            countback_status = set()
            for c in wg_countback.split(","):
                countback_status.add(CountbackStatusRec.from_db_str(c.strip()))

        memo.append(JudgingScore(
            id=id,
            brewer_id=bid,
            score_table=scoreTable,
            entry_id=eid,
            total_score=scoreEntry,
            aroma=wg_aroma,
            appearance=wg_appearance,
            flavour=wg_flavour,
            body=wg_body,
            overall=wg_overall,
            score_spread=wg_score_spread,
            score_place=score_place,
            countback_status=countback_status,
            score_type=scoreType
        ))

    return memo
