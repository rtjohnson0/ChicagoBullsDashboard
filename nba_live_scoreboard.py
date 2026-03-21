from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime
import json
import time

print("=== NBA Live Scoreboard Update ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

all_games_today = []

try:
    print("\nFetching live NBA scoreboard...")
    time.sleep(1)  # light delay

    sb = scoreboard.ScoreBoard()
    games = sb.get_dict()['scoreboard']['games']

    for g in games:
        game_info = {
            "away_team": g['awayTeam']['teamName'],
            "home_team": g['homeTeam']['teamName'],
            "away_score": g['awayTeam']['score'] if g['awayTeam']['score'] is not None else 0,
            "home_score": g['homeTeam']['score'] if g['homeTeam']['score'] is not None else 0,
            "status": g['gameStatusText'],
            "quarter": g.get('period', 0),
            "time_remaining": g.get('gameClock', 'N/A'),
            "is_live": g['gameStatus'] in [2, 3],  # 2 = live, 3 = halftime
            "is_completed": g['gameStatus'] == 4
        }
        all_games_today.append(game_info)

    print(f"{len(all_games_today)} games today")
except Exception as e:
    print(f"Scoreboard error: {e}")

data = {
    "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
    "all_games_today": all_games_today
}

with open('nba_today_games.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: nba_today_games.json")
print("Script finished.")