import pandas as pd
import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import leaguedashteamstats, leaguegamefinder
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import teams
from datetime import datetime
import json
import time

print("=== Bulls Daily Team Efficiency Update ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

bulls_id = 1610612741
current_season = '2025-26'  # Try '2025' if empty

# Initialize variables
bulls_basic = {}
bulls_advanced = {}
calculated = {}
today_game = None
next_game = None
injuries = []
all_games_today = []

# 1. TEAM STATS
try:
    print("\nFetching team stats...")
    time.sleep(1)  # small delay to avoid rate limit

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

    # Safe column selection
    basic_cols = ['TEAM_ID', 'PTS', 'REB', 'AST', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA']
    basic_cols = [c for c in basic_cols if c in basic.columns]

    adv_cols = ['TEAM_ID', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'TS_PCT', 'PACE', 'PIE']
    adv_cols = [c for c in adv_cols if c in adv.columns]

    team_data = pd.merge(
        basic[basic_cols],
        adv[adv_cols],
        on='TEAM_ID',
        how='left'
    )

    bulls_row = team_data[team_data['TEAM_ID'] == bulls_id]
    if not bulls_row.empty:
        bulls = bulls_row.iloc[0]

        bulls_basic = {col.lower(): float(bulls[col]) for col in basic_cols if col != 'TEAM_ID'}
        bulls_advanced = {col.lower(): float(bulls[col]) for col in adv_cols if col != 'TEAM_ID'}

        # Possessions estimate
        poss = (bulls.get('FGA', 0) + 0.44 * bulls.get('FTA', 0) + bulls.get('TOV', 0) - bulls.get('OREB', 0))
        poss = max(poss, 1)

        calculated = {
            "efg_pct": (bulls.get('FGM', 0) + 0.5 * bulls.get('FG3M', 0)) / bulls.get('FGA', 1),
            "ts_pct_calc": bulls.get('PTS', 0) / (2 * (bulls.get('FGA', 0) + 0.44 * bulls.get('FTA', 0))) if (bulls.get('FGA', 0) + bulls.get('FTA', 0) > 0) else 0,
            "tov_pct": bulls.get('TOV', 0) / poss,
            "orb_pct": bulls.get('OREB', 0) / (bulls.get('OREB', 0) + bulls.get('OPP_DREB', 0)) if (bulls.get('OREB', 0) + bulls.get('OPP_DREB', 0) > 0) else 0
        }

        print("Bulls stats pulled successfully")
    else:
        print("No Bulls data returned from NBA API")
except Exception as e:
    print(f"Stats error: {e}")

# 2. LIVE SCOREBOARD (All Games Today)
try:
    print("\nChecking live scoreboard...")
    sb = scoreboard.ScoreBoard()
    games = sb.get_dict()['scoreboard']['games']

    for g in games:
        game_info = {
            "away_team": g['awayTeam']['teamName'],
            "home_team": g['homeTeam']['teamName'],
            "status": g['gameStatusText'],
            "score": f"{g['awayTeam']['score']} - {g['homeTeam']['score']}" if g['awayTeam']['score'] > 0 else "N/A",
            "is_live": g['gameStatus'] in [2, 3]  # 2 = live, 3 = halftime, etc.
        }
        all_games_today.append(game_info)

        if bulls_id == g['homeTeam']['teamId'] or bulls_id == g['awayTeam']['teamId']:
            today_game = game_info

    print(f"{len(all_games_today)} NBA games today")
except Exception as e:
    print(f"Scoreboard error: {e}")

# 3. INJURY REPORT
try:
    print("\nScraping Bulls injury report...")
    url = "https://www.cbssports.com/nba/teams/CHI/chicago-bulls/injuries/"
    headers = {"User-Agent": "Mozilla/5.0"}
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

    print(f"{len(injuries)} injuries found")
except Exception as e:
    print(f"Injury scrape error: {e}")
    injuries = []

# 4. SAVE JSON
data = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "bulls_basic": bulls_basic,
    "bulls_advanced": bulls_advanced,
    "calculated": calculated,
    "game_today": today_game,
    "all_games_today": all_games_today,
    "injuries": injuries
}

with open("bulls_team_efficiency.json", "w") as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_team_efficiency.json")
print("Script finished.")