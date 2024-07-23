from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursor


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
