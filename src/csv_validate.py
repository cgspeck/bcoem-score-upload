from copy import deepcopy
import csv
from dataclasses import dataclass, field
from io import StringIO
import io
from typing import Optional, TextIO

REQUIRED_HEADERS = ["Entry Number", "Category", "Sub-category", "Total Score"]


@dataclass
class HeaderValidateResponse:
    ok: bool = True
    missing: list[str] = field(default_factory=list)


def try_decode_stream(b: bytes) -> Optional[StringIO]:
    t_io = None
    try:
        t_io = io.StringIO(b.decode())
    except UnicodeDecodeError:
        pass

    return t_io


def validate_headers(data: TextIO) -> HeaderValidateResponse:
    dr = csv.DictReader(data)
    data.seek(0)
    required_headers = deepcopy(REQUIRED_HEADERS)

    if dr.fieldnames is None:
        return HeaderValidateResponse(ok=False, missing=required_headers)

    [required_headers.remove(x) for x in dr.fieldnames if x in required_headers]

    return HeaderValidateResponse(
        ok=len(required_headers) == 0, missing=required_headers
    )


def is_csv(data: TextIO) -> bool:
    dialect = None
    try:
        dialect = csv.Sniffer().sniff(data.read(1024))
    except Exception as e:
        pass
    finally:
        data.seek(0)

    return dialect is not None
