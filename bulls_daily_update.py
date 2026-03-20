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

# Try multiple seasons
seasons = ['2025-26', '2025']

bulls_basic = {}
bulls_advanced = {}
calculated = {}
today_game = None
next_game = None
injuries = []
all_games_today = []

# 1. TEAM STATS - Try multiple seasons
stats_found = False
for season in seasons:
    if stats_found:
        break
    print(f"\nTrying season: {season}")
    try:
        time.sleep(1.5)  # Avoid rate limit

        basic = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Base',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]

        time.sleep(1.5)

        adv = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Advanced',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]

        print(f"Basic columns: {basic.columns.tolist()}")
        print(f"Advanced columns: {adv.columns.tolist()}")

        team_data = pd.merge(
            basic[['TEAM_ID', 'PTS', 'REB', 'AST', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA']],
            adv[['TEAM_ID', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'TS_PCT', 'PACE', 'PIE']],
            on='TEAM_ID',
            how='left'
        )

        bulls_row = team_data[team_data['TEAM_ID'] == bulls_id]
        print(f"Bulls rows found: {len(bulls_row)}")

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
                "pace": float(bulls['PACE']),
                "pie": float(bulls.get('PIE', 0.0))
            }

            # Calculated
            poss = (bulls['FGA'] + 0.44 * bulls['FTA'] + bulls['TOV'] - bulls.get('OREB', 0))
            poss = max(1, poss)

            calculated = {
                "offensive_rating": (bulls['PTS'] / poss) * 100,
                "defensive_rating": bulls['DEF_RATING'],
                "net_rating": bulls['NET_RATING'],
                "pace": bulls['PACE'],
                "efg_pct": (bulls['FGM'] + 0.5 * bulls['FG3M']) / bulls['FGA'] if bulls['FGA'] > 0 else 0,
                "ts_pct_calc": bulls['PTS'] / (2 * (bulls['FGA'] + 0.44 * bulls['FTA'])) if (bulls['FGA'] + bulls['FTA'] > 0) else 0,
                "tov_pct": bulls['TOV'] / poss if poss > 0 else 0,
                "orb_pct": bulls.get('OREB', 0) / (bulls.get('OREB', 0) + bulls.get('OPP_DREB', 0)) if (bulls.get('OREB', 0) + bulls.get('OPP_DREB', 0) > 0) else 0
            }

            stats_found = True
            print(f"Stats pulled successfully for season {season}")
        else:
            print(f"No Bulls row for season {season}")
    except Exception as e:
        print(f"Stats error for {season}: {e}")

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