import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import leaguedashteamstats
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.library.http import NBAStatsHTTP
from datetime import datetime
import json

NBAStatsHTTP.headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Referer': 'https://stats.nba.com'
}

print("=== Bulls Daily Team Efficiency Update ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

bulls_id = 1610612741
current_season = '2025-26'  # safer season until API updates

bulls_basic = {}
bulls_advanced = {}
calculated = {}
today_game = None
next_game = None
injuries = []

# ===============================
# 1. TEAM STATS (Robust version)
# ===============================

try:
    print("\nFetching team stats...")

    basic = leaguedashteamstats.LeagueDashTeamStats(
        season=current_season,
        measure_type_detailed_defense='Base',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    time.sleep(1)

    adv = leaguedashteamstats.LeagueDashTeamStats(
        season=current_season,
        measure_type_detailed_defense='Advanced',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    # Print columns to verify names
    print("Basic columns:", basic.columns.tolist())
    print("Advanced columns:", adv.columns.tolist())

    # Only keep columns that exist (prevents KeyError)
    basic_cols = [c for c in ['TEAM_ID','PTS','REB','AST','TOV','FGM','FGA','FG3M','FG3A','FTM','FTA'] if c in basic.columns]
    adv_cols = [c for c in ['TEAM_ID','OFF_RATING','DEF_RATING','NET_RATING','TS_PCT','PACE'] if c in adv.columns]

    team_data = pd.merge(basic[basic_cols], adv[adv_cols], on='TEAM_ID', how='inner')

    bulls_row = team_data[team_data['TEAM_ID'] == bulls_id]

    if not bulls_row.empty:

        bulls = bulls_row.iloc[0]

        # Basic stats
        bulls_basic = {col.lower(): float(bulls[col]) for col in basic_cols if col != 'TEAM_ID'}

        # Advanced stats
        bulls_advanced = {col.lower(): float(bulls[col]) for col in adv_cols if col != 'TEAM_ID'}

        # Possessions estimate
        poss = bulls.get('FGA',0) + 0.44 * bulls.get('FTA',0) + bulls.get('TOV',0)
        poss = max(poss,1)

        calculated = {
            "efg_pct": (bulls.get('FGM',0) + 0.5 * bulls.get('FG3M',0)) / bulls.get('FGA',1),
            "ts_pct_calc": bulls.get('PTS',0) / (2 * (bulls.get('FGA',0) + 0.44 * bulls.get('FTA',0))),
            "tov_pct": bulls.get('TOV',0) / poss
        }

        # Win probability estimate
        off = bulls.get('OFF_RATING', 0)
        deff = bulls.get('DEF_RATING', 0)
        if off > 0 and deff > 0:
            win_prob = (off**14) / ((off**14) + (deff**14))
            calculated["expected_win_pct"] = round(win_prob*100,1)
        else:
            calculated["expected_win_pct"] = None

        print("Bulls stats pulled successfully")

    else:
        print("No Bulls data returned from NBA API")

except Exception as e:
    print(f"Stats error: {e}")
# ===============================
# 2. LIVE SCOREBOARD
# ===============================

try:

    print("\nChecking live scoreboard...")

    sb = scoreboard.ScoreBoard()
    games = sb.get_dict()['scoreboard']['games']

    all_games_today = []
    bulls_game = None

    for g in games:

        game_info = {
            "away_team": g['awayTeam']['teamName'],
            "home_team": g['homeTeam']['teamName'],
            "status": g['gameStatusText'],
            "score": f"{g['awayTeam']['score']} - {g['homeTeam']['score']}"
        }

        all_games_today.append(game_info)

        if bulls_id == g['homeTeam']['teamId'] or bulls_id == g['awayTeam']['teamId']:

            today_game = {
                "opponent": g['awayTeam']['teamName'] if bulls_id == g['homeTeam']['teamId'] else g['homeTeam']['teamName'],
                "home": bulls_id == g['homeTeam']['teamId'],
                "status": g['gameStatusText']
            }

            bulls_game = game_info

    print(f"{len(all_games_today)} NBA games today")

except Exception as e:
    print(f"Scoreboard error: {e}")
    all_games_today = []

# ===============================
# 3. INJURY REPORT
# ===============================

try:

    print("\nScraping Bulls injury report...")

    url = "https://www.cbssports.com/nba/teams/CHI/chicago-bulls/injuries/"
    headers = {"User-Agent":"Mozilla/5.0"}

    response = requests.get(url,headers=headers)

    soup = BeautifulSoup(response.text,"html.parser")

    table = soup.select_one("table")

    injuries = []

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

    print(f"{len(injuries)} injuries found")

except Exception as e:

    print(f"Injury scrape error: {e}")
    injuries = []

# ===============================
# 4. SAVE JSON
# ===============================

data = {

    "date": datetime.now().strftime("%Y-%m-%d"),

    "bulls_basic": bulls_basic,

    "bulls_advanced": bulls_advanced,

    "calculated": calculated,

    "game_today": today_game,

    "next_game": next_game,

    "injuries": injuries,

    "all_games_today": all_games_today
}

with open("bulls_team_efficiency.json","w") as f:

    json.dump(data,f,indent=2)

print("\nSaved: bulls_team_efficiency.json")
print("Script finished")