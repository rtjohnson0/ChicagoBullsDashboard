import pandas as pd
import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import leaguedashteamstats, leaguegamefinder
from datetime import datetime
import json
import time

print("=== Bulls Daily Stats Update ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

bulls_id = 1610612741
current_season = '2025-26'

bulls_basic = {}
bulls_advanced = {}
next_game = {"date": None, "opponent": None, "is_home": None, "time": "TBD"}
injuries = []

# 1. Basic & Advanced Team Stats
try:
    print("\nFetching Bulls season stats...")
    time.sleep(1.5)

    basic = leaguedashteamstats.LeagueDashTeamStats(
        season=current_season,
        measure_type_detailed_defense='Base',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    time.sleep(1.5)

    adv = leaguedashteamstats.LeagueDashTeamStats(
        season=current_season,
        measure_type_detailed_defense='Advanced',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    bulls_row = basic[basic['TEAM_ID'] == bulls_id]
    if not bulls_row.empty:
        b = bulls_row.iloc[0]
        bulls_basic = {
            "pts": float(b['PTS']),
            "reb": float(b['REB']),
            "ast": float(b['AST']),
            "tov": float(b['TOV']),
            "fgm": float(b['FGM']),
            "fga": float(b['FGA']),
            "fg3m": float(b['FG3M']),
            "fg3a": float(b['FG3A']),
            "ftm": float(b['FTM']),
            "fta": float(b['FTA'])
        }

        a = adv[adv['TEAM_ID'] == bulls_id]
        if not a.empty:
            a = a.iloc[0]
            bulls_advanced = {
                "off_rating": float(a['OFF_RATING']),
                "def_rating": float(a['DEF_RATING']),
                "net_rating": float(a['NET_RATING']),
                "ts_pct": float(a['TS_PCT']),
                "pace": float(a['PACE'])
            }

        print("\nBulls Season Stats:")
        for k, v in bulls_basic.items():
            print(f"{k.upper()}: {v:.1f}")
        for k, v in bulls_advanced.items():
            print(f"{k.replace('_', ' ').title()}: {v:.2f}")
    else:
        print("No Bulls data found")
except Exception as e:
    print(f"Stats error: {e}")

# 2. Next Game
try:
    print("\nFetching next game...")
    games = leaguegamefinder.LeagueGameFinder(team_id_nullable=bulls_id, season_nullable=current_season).get_data_frames()[0]
    games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])
    upcoming = games[games['GAME_DATE'] > datetime.now()].sort_values('GAME_DATE')
    if not upcoming.empty:
        next_g = upcoming.iloc[0]
        next_opp_abbr = next_g['MATCHUP'].split(' @ ')[-1] if '@' in next_g['MATCHUP'] else next_g['MATCHUP'].split(' vs. ')[-1]
        is_home = '@' not in next_g['MATCHUP']

        next_game = {
            "date": next_g['GAME_DATE'].strftime('%Y-%m-%d'),
            "opponent": next_opp_abbr,
            "is_home": is_home,
            "time": "TBD"
        }
        print(f"Next game: {next_game['date']} vs {next_game['opponent']} ({'Home' if is_home else 'Away'})")
except Exception as e:
    print(f"Next game error: {e}")

# 3. Injury Report
try:
    print("\nScraping Bulls injury report...")
    url = "https://www.cbssports.com/nba/teams/CHI/chicago-bulls/injuries/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.select_one("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
                injuries.append({
                    "player": cols[0].text.strip(),
                    "position": cols[1].text.strip(),
                    "injury": cols[2].text.strip(),
                    "status": cols[3].text.strip()
                })

    if injuries:
        print("\nBulls Injury Report:")
        for inj in injuries:
            print(f"{inj['player']} ({inj['position']}): {inj['injury']} - {inj['status']}")
except Exception as e:
    print(f"Injury scrape error: {e}")
    injuries = []

# 4. Prepare data for JSON (this is what the frontend will read)
data = {
    "date": datetime.now().strftime('%Y-%m-%d'),
    "bulls_season_stats": {
        "ppg": bulls_basic.get("pts", None),
        "rpg": bulls_basic.get("reb", None),
        "apg": bulls_basic.get("ast", None),
        "tovpg": bulls_basic.get("tov", None),
        "fgm": bulls_basic.get("fgm", None),
        "fga": bulls_basic.get("fga", None),
        "fg3m": bulls_basic.get("fg3m", None),
        "fg3a": bulls_basic.get("fg3a", None),
        "ftm": bulls_basic.get("ftm", None),
        "fta": bulls_basic.get("fta", None),
        "off_rating": bulls_advanced.get("off_rating", None),
        "def_rating": bulls_advanced.get("def_rating", None),
        "net_rating": bulls_advanced.get("net_rating", None),
        "ts_pct": bulls_advanced.get("ts_pct", None),
        "pace": bulls_advanced.get("pace", None)
    },
    "next_game": next_game,
    "injuries": injuries
}

# Save to file
with open('bulls_daily.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_daily.json")
print("JSON content preview:")
print(json.dumps(data, indent=2))  # ← This prints the full JSON to terminal so you can verify
print("Script finished.")