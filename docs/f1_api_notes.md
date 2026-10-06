# F1 Fantasy API Notes

Unofficial notes on the official F1 Fantasy endpoints used by this project. The API has no public documentation; these URL patterns and parameter meanings are based on observed requests.

Base URL: `https://fantasy.formula1.com`

## Public asset data

```text
/feeds/drivers/{race_number}_en.json
```

Returns driver and constructor IDs, names, prices, selection percentages, and overall, race and session points. Records are under `Data.Value`.

Used to track asset prices and performance by race, and to enrich league team selections by joining on asset ID.

## Public league standings

```text
Overall: /feeds/leaderboard/privateleague/list_1_{league_id}_0_{page}.json
By race: /feeds/leaderboard/privateleague/list_2_{league_id}_{race_number}_{page}.json
```

- `league_id`: numeric league ID, distinct from the invite code.
- `race_number`: Fantasy game-day index, mapped through the project's race reference.
- `page`: page number, starting at `1`. The current collector requests page `1`.

Both feeds have been accessed without authentication. Rows are under `Value.leaderboard` and include:

| Field | Meaning |
| --- | --- |
| `user_guid` | Full user identifier |
| `team_no` | Fantasy team number |
| `cur_rank` | League rank |
| `cur_points` | Overall or race points, depending on the feed |
| `user_team` | Selected asset IDs |
| `team_name`, `user_name` | Display names |

## Opponent historical team

Requires authentication.

```text
/services/user/opponentteam/opponentgamedayplayerteamget/1/{user_guid}/{team_no}/{race_number}/1
```

Use `user_guid` and `team_no` from the public standings. Copy `user_guid` in full, including its numeric suffix.

```python
url = (
    "https://fantasy.formula1.com/services/user/opponentteam/"
    f"opponentgamedayplayerteamget/1/{user_guid}/{team_no}/{race_number}/1"
)
```

Returns team composition, captain flags, team value, remaining balance, substitutions, chip information, race/overall points, and race/overall ranks.

Team records are under `Data.Value.userTeam`; selected assets are in `playerid`.


## Opponent game-day summary

```text
/services/user/opponentteam/opponentgamedayget/1/{user_guid}/{team_no}
```

Provides points for all available races in `Data.Value.mdDetails`, the number of Fantasy teams (`teamCount`), and season-level chip usage, including the races in which chips were used. There is no race parameter in this URL.

## Data scope

The historical team endpoint combines race details with season-level information:

| Scope | Fields |
| --- | --- |
| Requested race | Selected assets, captain and race points |
| Season/current | Chip usage and current overall points |
| Additional team details | Value, balance, substitutions and ranks |

Keep race details and season/current values separate when transforming the response. Match each chip’s usage-race field (`…takengd`) to the requested race to identify the chip used that week.

The game-day summary returns scores across all available races and season chip usage. Fetch it once per team per run, alongside historical team requests for each required race.

## Other observed endpoints

| Purpose | Path |
| --- | --- |
| Own team | `/services/user/gameplay/{user_guid}/getteam/1/1/{race_number}/1` |
| User's leagues | `/services/user/league/{user_guid}/leaguelandingv1` |
| League metadata | `/services/user/league/getleagueinfo/{league_code}` |
| Asset statistics | `/feeds/popup/playerstats_{asset_id}.json` |

## Authentication

Authenticated requests use an active F1 Fantasy session, with `F1_COOKIE` and `F1_USER_AGENT` loaded from `.env`. Session values are excluded from version control.

The working collector detects HTTP 401 responses and stops with an explanatory authentication error.

## Collection flow

Public standings → `user_guid` + `team_no` → authenticated opponent data → raw JSON → Python transformation and validation → SQLite → FastAPI / Streamlit.

Web requests may include `?buster=...` for cache busting; the public collectors work without it.
