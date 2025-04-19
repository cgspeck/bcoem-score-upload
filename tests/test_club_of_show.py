from src.controllers.report_generator import ClubOfShowCandidate


def test_ordering_simple():
    club1 = ClubOfShowCandidate(
        "club 1",
        entry_count=0,
        member_average_score=0,
        firsts_count=10,
        seconds_count=5,
        thirds_count=1,
    )
    club2 = ClubOfShowCandidate(
        "club 2",
        entry_count=0,
        member_average_score=0,
        firsts_count=0,
        seconds_count=10,
        thirds_count=1,
    )
    club3 = ClubOfShowCandidate(
        "club 3",
        entry_count=0,
        member_average_score=0,
        firsts_count=0,
        seconds_count=0,
        thirds_count=10,
    )
    actual = sorted([club3, club2, club1], reverse=True)
    assert (actual) == [club1, club2, club3]


def test_ordering_tie_break_rule_1():
    # tie break rule one prioritizes clubs with highest average score
    club1 = ClubOfShowCandidate(
        "club 1",
        entry_count=0,
        member_average_score=48,
        firsts_count=0,
        seconds_count=0,
        thirds_count=0,
    )
    club2 = ClubOfShowCandidate(
        "club 2",
        entry_count=0,
        member_average_score=35,
        firsts_count=0,
        seconds_count=0,
        thirds_count=0,
    )
    club3 = ClubOfShowCandidate(
        "club 3",
        entry_count=0,
        member_average_score=20,
        firsts_count=0,
        seconds_count=0,
        thirds_count=0,
    )
    actual = sorted([club3, club2, club1], reverse=True)
    assert (actual) == [club1, club2, club3]


def test_ordering_tie_break_rule_2():
    # tie break rule one prioritizes clubs with lowest entry count
    club1 = ClubOfShowCandidate(
        "club 1",
        entry_count=10,
        member_average_score=0,
        firsts_count=0,
        seconds_count=0,
        thirds_count=0,
    )
    club2 = ClubOfShowCandidate(
        "club 2",
        entry_count=20,
        member_average_score=0,
        firsts_count=0,
        seconds_count=0,
        thirds_count=0,
    )
    club3 = ClubOfShowCandidate(
        "club 3",
        entry_count=30,
        member_average_score=0,
        firsts_count=0,
        seconds_count=0,
        thirds_count=0,
    )
    actual = sorted([club3, club2, club1], reverse=True)
    assert (actual) == [club1, club2, club3]
