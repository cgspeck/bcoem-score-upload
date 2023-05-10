from typing import Any, Dict

import simplejson as json
from pytest_snapshot.plugin import Snapshot  # type: ignore


def pdump(v: Any) -> str:
    return json.dumps(v, indent=2, sort_keys=True)


def json_assert(
    snapshot: Snapshot,
    compare_json: str,
    snapshot_name: str,
) -> None:

    compare_object = json.loads(compare_json)
    dict_assert(snapshot, compare_object, snapshot_name)


def dict_assert(
    snapshot: Snapshot,
    compare_object: Dict[str, Any],
    snapshot_name: str,
) -> None:
    _compare_object = pdump(compare_object)
    snapshot.assert_match(_compare_object, snapshot_name)
