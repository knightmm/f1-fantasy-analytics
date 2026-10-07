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

def make_detailed_team_assets_dataframe(team, user_guid, race_number):
    records = []

    for player in team["playerid"]:
        records.append({
            "season": 2026,
            "race_number": race_number,
            "user_guid": user_guid,
            "team_no": team["teamno"],
            "asset_id": player["id"],
            "is_captain": player["iscaptain"],
            "is_mg_captain": player["ismgcaptain"],
            "player_position": player["playerpostion"],
            "is_final": player["isfinal"],
        })

    return pd.DataFrame(records)