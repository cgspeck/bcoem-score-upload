
from dataclasses import dataclass
import json
from typing import Dict, List, Optional
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor

@dataclass
class Entry:
    entry_number: int
    style: str
    required_info: Optional[str]
    abv: Optional[float]
    pouring_speed: Optional[str]
    pouring_notes: Optional[str]
    rouse_yeast: Optional[str]
    possible_allergens: Optional[str]
    # Category e.g. 10 for porter, is string in BCOEM
    brewstyle_group_int: int
    # Style e.g. 1 for english porter, is string in BCOEM
    brewstyle_num_int: int

@dataclass
class JudgingTable:
    category: str
    style_ids: List[int]
    entries: List[Entry]

@dataclass
class StyleRec:
    brewstyle_group: str
    brewstyle_num: str

def _get_judging_tables(cnn: MySQLConnection) -> List[JudgingTable]:
    sql = """
SELECT id, tableName, tableStyles, tableNumber
FROM judging_tables
ORDER BY tableNumber ASC;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []
    
    for (_id, tableName, tableStyles, _tableNumber)  in cursor:
        style_ids = [int(s_id.strip()) for s_id in tableStyles.split(",")]
        memo.append(JudgingTable(tableName, style_ids, []))
    
    return memo

def _load_style_records(cnn: MySQLConnection, style_ids: List[int], s_recs: Dict[int, StyleRec]):
    for style_id in style_ids:
        if style_id in s_recs:
            continue
        
        # brewStyleGroup = two digit string, aligns to brewing.brewCategorySort
        # brewStyleNum = two digit string, aligns to brewing.brewSubCategory
        sql = """
SELECT id, brewStyleGroup, brewStyleNum
FROM `styles`
WHERE id = %s;
"""
        cursor: MySQLCursor = cnn.cursor()
        cursor.execute(sql, (style_id,))
        _, brewstyle_group, brewstyle_num = cursor.fetchone()
        s_recs[style_id] = StyleRec(brewstyle_group, brewstyle_num)


def _get_judging_entries_for_style(cnn: MySQLConnection, brew_category_sort: str, brew_subcategory: str, s_rec: StyleRec) -> List[Entry]:
    sql = """
SELECT id, brewStyle, brewCategorySort, brewSubCategory, brewInfo, brewABV, brewPouring, brewPossAllergens, brewPaid, brewReceived
FROM brewing
WHERE brewCategorySort = %s
AND brewSubCategory = %s
AND brewPaid = 1
AND brewReceived = 1
ORDER BY id ASC;
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql, (brew_category_sort, brew_subcategory))
    memo = []
    
    for (id, brewStyle, _brewCategorySort, _brewSubCategory, brewInfo, brewABV, brewPouring, brewPossAllergens, _brewPaid, _brewReceived)  in cursor:
        # brewPouring is an optional compound field, with each of the following also optional
        # .pouring is pouring speed
        # .pouring_rouse is rouse yeast
        # {"pouring":"Normal","pouring_rouse":"No","pouring_notes":"Bottle conditioned. Don't rouse yeast"}
        pouring_notes = None
        pouring_speed = None
        rouse_yeast = None
        
        if brewPouring is not None and len(brewPouring.strip()) > 0:
            brew_pouring_dict = json.loads(brewPouring)
            pouring_notes = brew_pouring_dict.get('pouring_notes', None)
            pouring_speed = brew_pouring_dict.get('pouring', None)
            rouse_yeast = brew_pouring_dict.get('pouring_rouse', None)

        brewstyle_num_int=999
        if s_rec.brewstyle_num.isdigit():
            brewstyle_num_int = int(s_rec.brewstyle_num)
        brewstyle_group_int=999
        if s_rec.brewstyle_group.isdigit():
            brewstyle_group_int = int(s_rec.brewstyle_group)


        entry = Entry(
            entry_number=id,
            style=brewStyle,
            abv=brewABV,
            possible_allergens=brewPossAllergens,
            required_info=brewInfo,
            pouring_notes=pouring_notes,
            pouring_speed=pouring_speed,
            rouse_yeast=rouse_yeast,
            brewstyle_num_int=brewstyle_num_int,
            brewstyle_group_int=brewstyle_group_int
        )
        memo.append(entry)
    return memo

def _get_judging_entries(cnn: MySQLConnection, table: JudgingTable, s_recs: Dict[int, StyleRec]) -> List[JudgingTable]:
    memo: List[Entry] = []
    for style_id in table.style_ids:
        s_rec = s_recs[style_id]
        memo.extend(_get_judging_entries_for_style(cnn, s_rec.brewstyle_group, s_rec.brewstyle_num, s_rec))
    
    memo.sort(key=lambda e: e.entry_number)
    return memo

def get_data(cnn: MySQLConnection) -> List[JudgingTable]:
    tables = _get_judging_tables(cnn)
    style_id_brewstyle_group_num_map: Dict[int, StyleRec] = {}

    for table in tables:
        _load_style_records(cnn, table.style_ids, style_id_brewstyle_group_num_map)
        table.entries = _get_judging_entries(cnn, table, style_id_brewstyle_group_num_map)

    return tables
