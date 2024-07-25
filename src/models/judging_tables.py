from dataclasses import dataclass
from typing import Dict, List
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


@dataclass
class JudgingTable:
    id: int  # db ID
    name: str
    number: int

def load_all(cnn: MySQLConnection) -> List[JudgingTable]:
    sql = """
SELECT id, tableName, tableNumber
FROM judging_tables
ORDER BY tableNumber ASC
"""
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(sql)
    memo = []

    for id, tableName, tableNumber in cursor:
        name = tableName.strip().lower().replace("table", "").title()
        memo.append(JudgingTable(id=id, name=name, number=tableNumber))

    return memo


def get_judging_table_dict(cnn: MySQLConnection) -> Dict[int, JudgingTable]:
    memo = {}
    brew_entries = load_all(cnn)

    for brew in brew_entries:
        memo[brew.id] = brew

    return memo
