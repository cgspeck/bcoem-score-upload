from typing import Any, Dict

import simplejson as json
from pytest_snapshot.plugin import Snapshot


def pdump(v: Any) -> str:
    return json.dumps(v, indent=2, sort_keys=True)


def json_assert(
    snapshot: Snapshot,
    compare_json: str,
    snapshot_name: str,
):

    compare_object = json.loads(compare_json)
    return dict_assert(snapshot, compare_object, snapshot_name)


def dict_assert(
    snapshot: Snapshot,
    compare_object: Dict[str, Any],
    snapshot_name: str,
):
    _compare_object = pdump(compare_object)
    snapshot.assert_match(_compare_object, snapshot_name)
