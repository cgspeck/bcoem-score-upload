import csv
from io import StringIO
import io
from typing import Optional, TextIO

REQUIRED_HEADERS = ["Entry Number", "Category", "Sub-category", "Total Score"]


def try_decode_stream(b: bytes) -> Optional[StringIO]:
    t_io = None
    try:
        t_io = io.StringIO(b.decode())
    except UnicodeDecodeError:
        pass

    return t_io


def has_required_headers(data: TextIO) -> bool:
    dr = csv.DictReader(data)
    data.seek(0)
    ok = True

    if dr.fieldnames is None:
        return False

    for h in REQUIRED_HEADERS:
        if h not in dr.fieldnames:
            ok = False

    return ok


def is_csv(data: TextIO) -> bool:
    dialect = None
    try:
        dialect = csv.Sniffer().sniff(data.read(1024))
    except Exception as e:
        print(e)
    finally:
        data.seek(0)

    return dialect is not None
