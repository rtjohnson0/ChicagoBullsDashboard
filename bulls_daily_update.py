import pandas as pd
import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import commonteamroster, leaguedashplayerstats, scoreboard, leaguegamefinder
from nba_api.stats.static import teams
from datetime import datetime
import json
import time

print("=== Bulls Daily Team Efficiency Update - Current Roster Only ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

bulls_id = 1610612741
current_season = '2025-26'

# Initialize variables
bulls_stats = {}
calculated = {}
today_game = None
next_game = None
injuries = []
all_games_today = []

# 1. Get CURRENT ACTIVE ROSTER (excludes traded players)
try:
    print("\nFetching current Bulls roster...")
    roster = commonteamroster.CommonTeamRoster(team_id=bulls_id, season=current_season)
    roster_df = roster.get_data_frames()[0]  # Main roster table

    current_players = roster_df['Player'].tolist()
    print(f"Current active Bulls players ({len(current_players)}): {', '.join(current_players[:8])}...")

except Exception as e:
    print(f"Roster error: {e}")
    current_players = []

# 2. Season Averages - Only for current roster
try:
    print("\nFetching season averages for current roster...")
    player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=current_season,
        team_id_nullable=bulls_id,
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    # Filter to only current active players
    current_stats = player_stats[player_stats['PLAYER_NAME'].isin(current_players)]

    if not current_stats.empty:
        # Team totals (sum PPG, RPG, etc.)
        bulls_stats = {
            "ppg": float(current_stats['PTS'].sum() / len(current_stats)),
            "rpg": float(current_stats['REB'].sum() / len(current_stats)),
            "apg": float(current_stats['AST'].sum() / len(current_stats)),
            "tovpg": float(current_stats['TOV'].sum() / len(current_stats)),
            "fg_pct": float(current_stats['FG_PCT'].mean()),
            "fg3_pct": float(current_stats['FG3_PCT'].mean()),
            "ft_pct": float(current_stats['FT_PCT'].mean()),
            "stlpg": float(current_stats['STL'].sum() / len(current_stats)),
            "blkpg": float(current_stats['BLK'].sum() / len(current_stats)),
            "player_count": len(current_stats)
        }

        print("\nBulls Current Roster Season Stats:")
        for k, v in bulls_stats.items():
            print(f"{k.upper()}: {v:.2f}")

        # Calculated
        poss = bulls_stats["ppg"] / (bulls_stats["fg_pct"] or 1)  # rough estimate
        calculated = {
            "efg_pct": bulls_stats["fg_pct"] + 0.5 * bulls_stats["fg3_pct"] if bulls_stats["fg3_pct"] else 0,
            "ts_pct": bulls_stats["ppg"] / (2 * (bulls_stats["ppg"] / bulls_stats["fg_pct"] + 0.44 * bulls_stats["ft_pct"])) if bulls_stats["fg_pct"] else 0,
            "tov_pct": bulls_stats["tovpg"] / poss if poss > 0 else 0
        }

        print("\nCalculated Metrics:")
        for k, v in calculated.items():
            print(f"{k.upper()}: {v:.3f}")
    else:
        print("No stats for current roster")
except Exception as e:
    print(f"Player stats error: {e}")

# 3. LIVE SCOREBOARD (All Games Today)
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
            "is_live": g['gameStatus'] in [2, 3]
        }
        all_games_today.append(game_info)

        if bulls_id == g['homeTeam']['teamId'] or bulls_id == g['awayTeam']['teamId']:
            today_game = game_info

    print(f"{len(all_games_today)} NBA games today")
except Exception as e:
    print(f"Scoreboard error: {e}")

# 4. INJURY REPORT (CBS scrape)
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

# 5. SAVE JSON
data = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "bulls_stats": bulls_stats,
    "calculated": calculated,
    "game_today": today_game,
    "all_games_today": all_games_today,
    "injuries": injuries
}

with open("bulls_team_efficiency.json", "w") as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_team_efficiency.json (current roster only)")
print("Script finished.")