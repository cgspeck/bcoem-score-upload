from dataclasses import dataclass
from typing import List
from src.datadefs import CountbackStatus, ScoreEntry


@dataclass
class PlaceGetterResult:
    success: bool
    place_getters: List[ScoreEntry]


def determine_place_getters(
    candidates: List[ScoreEntry], required_places: int
) -> PlaceGetterResult:
    success = True
    place_getters: List[ScoreEntry] = []

    candidates.sort(reverse=True)

    for i, cur_candidate in enumerate(candidates):
        if len(place_getters) >= required_places:
            break

        next_candidate = None
        if len(candidates) > i + 1:
            next_candidate = candidates[i + 1]

        if next_candidate is None:
            cur_candidate.score_place = i + 1
            place_getters.append(cur_candidate)
            continue

        if len(cur_candidate.countback_status) == 0:
            cur_candidate.score_place = i + 1
            place_getters.append(cur_candidate)
            continue

        interesting_conflicts = [
            x
            for x in cur_candidate.countback_status
            if x.status == CountbackStatus.RECALL_JUDGES
        ]

        if len(interesting_conflicts) == 0:
            cur_candidate.score_place = i + 1
            place_getters.append(cur_candidate)
            continue

        next_candidate_id = next_candidate.entry_id
        conflict = any(
            [x.conflict_entry_id == next_candidate_id for x in interesting_conflicts]
        )

        if conflict:
            success = False
            cur_candidate.score_place = i + 1
            place_getters.append(cur_candidate)

    return PlaceGetterResult(success, place_getters)
