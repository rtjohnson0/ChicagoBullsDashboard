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
# 1. TEAM STATS
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

    team_data = pd.merge(
        basic[['TEAM_ID','PTS','REB','AST','TOV','FGM','FGA','FG3M','FG3A','FTM','FTA']],
        adv[['TEAM_ID','OFF_RATING','DEF_RATING','NET_RATING','TS_PCT','PACE']],
        on='TEAM_ID'
    )

    bulls_row = team_data[team_data['TEAM_ID'] == bulls_id]

    if not bulls_row.empty:

        bulls = bulls_row.iloc[0]

        bulls_basic = {
            "pts": float(bulls['PTS']),
            "reb": float(bulls['REB']),
            "ast": float(bulls['AST']),
            "tov": float(bulls['TOV']),
            "fgm": float(bulls['FGM']),
            "fga": float(bulls['FGA']),
            "fg3m": float(bulls['FG3M']),
            "fg3a": float(bulls['FG3A']),
            "ftm": float(bulls['FTM']),
            "fta": float(bulls['FTA'])
        }

        bulls_advanced = {
            "off_rating": float(bulls['OFF_RATING']),
            "def_rating": float(bulls['DEF_RATING']),
            "net_rating": float(bulls['NET_RATING']),
            "ts_pct": float(bulls['TS_PCT']),
            "pace": float(bulls['PACE'])
        }

        # Possessions estimate
        poss = bulls['FGA'] + 0.44 * bulls['FTA'] + bulls['TOV']
        poss = max(poss,1)

        calculated = {
            "efg_pct": (bulls['FGM'] + 0.5 * bulls['FG3M']) / bulls['FGA'] if bulls['FGA'] > 0 else 0,
            "ts_pct_calc": bulls['PTS'] / (2 * (bulls['FGA'] + 0.44 * bulls['FTA'])) if bulls['FGA'] > 0 else 0,
            "tov_pct": bulls['TOV'] / poss
        }

        print("Basic shape:", basic.shape)
        print("Advanced shape:", adv.shape)
        print(basic.head())

        # Win probability estimate (analytics formula)
        off = bulls['OFF_RATING']
        deff = bulls['DEF_RATING']

        win_prob = (off**14) / ((off**14) + (deff**14))
        win_prob = round(win_prob * 100,1)

        calculated["expected_win_pct"] = win_prob

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