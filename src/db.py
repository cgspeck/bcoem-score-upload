from typing import Dict, Union

import mysql.connector  # type: ignore
from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor
from src.csv_validate import REQUIRED_HEADERS

from src.datadefs import DBConfig, PHPKEY_DBCONFIG_MAP


BACKUP_SQL = """
SELECT
    j.eid 'Entry Number',
    b.brewCategory 'Category',
    b.brewSubCategory  'Sub-category',
    j.scoreEntry 'Total Score'
FROM judging_scores j
INNER JOIN brewing b
ON b.id = j.eid 
ORDER BY eid;
"""

CLEAR_SQL = """
DELETE FROM judging_scores;
"""


def extract_db_config(fp: str) -> DBConfig:
    memo: Dict[str, Union[None, str, int]] = {
        v: None for v in PHPKEY_DBCONFIG_MAP.values()
    }

    with open(fp, "rt") as fh:
        for line in fh.readlines():
            parts = line.split("=")

            if len(parts) != 2:
                continue

            potential_php_key = parts[0].strip()

            if potential_php_key in PHPKEY_DBCONFIG_MAP.keys():
                config_key = PHPKEY_DBCONFIG_MAP[potential_php_key]
                value: Union[str, int] = parts[1]

                if type(value) == str:
                    value = value.strip()
                    value = value.strip(";")
                    value = value.strip("'")
                    value = value.strip('"')
                    if value == "ini_get('mysqli.default_port')":
                        value = "3306"

                if config_key == "port":
                    value = int(value)

                memo[config_key] = value

    missing = []

    for k, v in memo.items():
        if v is None:
            missing.append(k)

    if len(missing) > 0:
        raise ValueError(f"Missing config for {missing} in {fp}")

    return DBConfig(**memo)  # type: ignore


def create_connection(db_config: DBConfig) -> MySQLConnection:
    return mysql.connector.connect(**db_config.to_dict())


def execute_backup_query(cnn: MySQLConnection) -> list[str]:
    """Returns a CSV (in list of str form) of data required to restore scores table with header row

    Args:
        cnn (MySQLConnection): MySQL Connection Object

    Returns:
        list[str]: CSV with headers of fields "Entry Number", "Category", "Sub-category", "Total Score"
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(BACKUP_SQL)
    memo: list[str] = [",".join(REQUIRED_HEADERS)]

    for row in cursor.fetchall():
        memo.append(",".join([str(r) for r in row]))

    return memo


def execute_clear_query(cnn: MySQLConnection) -> None:
    """Clears all scores from the DB

    Args:
        cnn (MySQLConnection): MySQL Connection Object
    """
    cursor: MySQLCursor = cnn.cursor()
    cursor.execute(CLEAR_SQL)
