import csv
from typing import Dict, TextIO
from mysql.connector import MySQLConnection  # type: ignore
from mysql.connector.cursor import MySQLCursor  # type: ignore

from src.datadefs import ScoreEntry, make_cat_subcat_key
from src.utils import format_error_message


def get_brewer_ids(cnn: MySQLConnection, entries: list[ScoreEntry]):
    '''
    Retrieves brewer IDs for a list of entries and
    sets them in place
    '''
    
    entry_id_brewer_id_map: Dict[int, int] = {}
    sql = """
SELECT id, brewBrewerID
FROM brewing
ORDER BY id ASC;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    
    for (id, brewBrewerID)  in cursor:
        # 'brewBrewerId' is varchar for some reason, even though it's an int everywhere else
        entry_id_brewer_id_map[id] = int(brewBrewerID)

    for entry in entries:
        entry.brewer_id = entry_id_brewer_id_map.get(entry.entry_id)


def get_judging_tables(cnn: MySQLConnection, entries: list[ScoreEntry]):
    '''
    Retrieves judging table ids / 'score_table' for list of score entries and
    sets them in place
    '''
    style_id_score_table_map: Dict[int, int] = {}
    sql = """
SELECT id, tableStyles
FROM judging_tables
ORDER BY id ASC;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    
    for (id, tableStyles)  in cursor:
        for style in tableStyles.split(","):
            style_id_score_table_map[int(style)] = id

    for entry in entries:
        if entry.style_id is None:
            continue

        entry.score_table = style_id_score_table_map.get(entry.style_id, None)

def get_prefs_style_set(cnn: MySQLConnection) -> str:
    sql = "SELECT prefsStyleSet FROM preferences LIMIT 1;"
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    return cursor.fetchone()[0]

def get_style_ids(cnn: MySQLConnection, entries: list[ScoreEntry], messages: list[str]):
    '''
    Retrieves style ids for list of score entries and
    sets them in place
    '''
    prefs_style_set = get_prefs_style_set(cnn)
    messages.append(f"Using '{prefs_style_set}' style set")

    style_key_style_id_map: Dict[str, int] = {}    
    sql = """
SELECT id, brewStyleGroup, brewStyleNum
FROM styles
WHERE brewStyleVersion = %s
AND brewStyleActive = 'Y'
ORDER BY id ASC;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (prefs_style_set, ))
    
    for (id, brewStyleGroup, brewStyleNum)  in cursor:
        style_key_style_id_map[make_cat_subcat_key(brewStyleGroup, brewStyleNum)] = id
    
    for entry in entries:
        entry.style_id = style_key_style_id_map.get(entry.style_key, None)

def prepare_entries(cnn: MySQLConnection, entries: list[ScoreEntry], messages: list[str]) -> bool:
    ok = True
    messages.append("Getting brewer IDs")
    get_brewer_ids(cnn, entries)

    missing_entry_ids = [entry.entry_id for entry in entries if entry.brewer_id is None]
    if len(missing_entry_ids) > 0:
        ok = False
        format_error_message(f"Cannot find brewer ID for the following entries: {missing_entry_ids}", messages)
    else:
        messages.append(f"Retrieved brewer ids")

    get_style_ids(cnn, entries, messages)

    missing_style_ids = [entry.entry_id for entry in entries if entry.style_id is None]
    if len(missing_style_ids) > 0:
        ok = False
        format_error_message(f"Cannot find style IDs for the following entries: {missing_style_ids}", messages)
    else:
        messages.append(f"Retrieved style ids")
    
    get_judging_tables(cnn, entries)
    
    missing_judging_table_ids = [entry.entry_id for entry in entries if entry.style_id is None]
    if len(missing_judging_table_ids) > 0:
        ok = False
        format_error_message(f"Cannot find judging table IDs for the following entries: {missing_judging_table_ids}", messages)
    else:
        messages.append(f"Retrieved judging table ids")

    return ok

def load_entries_from_csv(data: TextIO) -> list[ScoreEntry]:
    memo = []
    data.seek(0)
    dr = csv.DictReader(data)
    # ["Entry Number", "Category", "Sub-category", "Total Score"]
    for r in dr:
        entry_id = r["Entry Number"]
        
        if len(entry_id.strip()) == 0:
            continue

        memo.append(ScoreEntry(
            entry_id=int(entry_id),
            category=r["Category"],
            sub_category=r["Sub-category"],
            total_score=float(r["Total Score"]),
        ))
    
    memo.sort(key=lambda x: x.entry_id)

    return memo

def save_entries(cnn: MySQLConnection, entries: list[ScoreEntry]) -> bool:
    ok = True
    sql = """
INSERT INTO judging_scores (eid, bid, scoreTable, scoreEntry, scoreType)
VALUES (%s, %s, %s, %s, %s)
"""
    cursor: MySQLCursor = cnn.cursor()

    for entry in entries:
        data = (entry.entry_id, entry.brewer_id, entry.score_table, entry.total_score, entry.score_type)
        cursor.execute(sql, data)

    cnn.commit()
    return ok
