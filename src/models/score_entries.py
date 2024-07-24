from typing import List
from mysql.connector import MySQLConnection

from src.datadefs import ScoreEntry
from src.models import brew_entries, brewers, judging_scores, judging_tables

def load_all(cnn: MySQLConnection) -> List[ScoreEntry]:
    judging_score_recs = judging_scores.load_all(cnn)

    judging_table_dict = judging_tables.get_judging_table_dict(cnn)
    brewer_dict = brewers.get_brewer_dict(cnn)
    brew_entries_dict = brew_entries.get_brew_entries_dict(cnn)
    memo: List[ScoreEntry] = []

    for js_rec in judging_score_recs:
        brew_entry = brew_entries_dict[js_rec.entry_id]
        judging_table = judging_table_dict[js_rec.score_table]

        memo.append(
            ScoreEntry(
                entry_id=js_rec.entry_id,
                category=brew_entry.category,
                sub_category=brew_entry.subcategory,
                total_score=js_rec.total_score,
                aroma=js_rec.aroma,
                appearance=js_rec.appearance,
                flavour=js_rec.flavour,
                body=js_rec.body,
                overall=js_rec.overall,
                score_spread=js_rec.score_spread,
                brewer_id=js_rec.brewer_id,
                style_id=None,  # allocated to judging tables
                score_table=js_rec.score_table,
                score_type=js_rec.score_type,
                # calculated score place as an int
                # maps to 'scorePlace, varchar3 in database
                score_place=js_rec.score_place,
                # used to store & display countback status
                countback_status=js_rec.countback_status or set(),
                # Only used for displaying reports
                brewer=brewer_dict[js_rec.brewer_id],
                brew_entry=brew_entry,
                judging_table=judging_table
            )
        )

    return memo
