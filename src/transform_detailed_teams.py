import pandas as pd
from urllib.parse import unquote


def make_team_chip_usage_dataframe(team, user_guid):
    chip_fields = {
        1: ("islimitlesstaken", "limitlesstakengd"),
        2: ("iswildcardtaken", "wildcardtakengd"),
        3: ("isfinalfixtaken", "finalfixtakengd"),
        4: ("isautopilottaken", "autopilottakengd"),
        5: ("isnonigativetaken", "nonigativetakengd"),
        6: ("isextradrstaken", "extradrstakengd"),
    }

    records = []

    for chip_id, (taken_field, race_field) in chip_fields.items():
        if team[taken_field] == chip_id:
            records.append({
                "season": 2026,
                "user_guid": user_guid,
                "team_no": team["teamno"],
                "team_name": unquote(team["teamname"]),
                "chip_id": chip_id,
                "race_used": team[race_field],
            })

    return pd.DataFrame(records)