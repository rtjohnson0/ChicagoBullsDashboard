from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime
import json
import time

print("=== NBA Live Scoreboard Update ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

all_games_today = []

# 2. LIVE SCOREBOARD - All Games Today (with REAL SCORES)
try:
    print("\nFetching live NBA scoreboard...")
    sb = scoreboard.ScoreBoard()
    games = sb.get_dict()['scoreboard']['games']

    all_games_today = []

    print(f"\nToday's NBA Games ({datetime.now().strftime('%Y-%m-%d')}): {len(games)} total")
    print("-" * 80)

    for g in games:
        away_name = g['awayTeam']['teamName']
        home_name = g['homeTeam']['teamName']
        away_score = g['awayTeam']['score'] if g['awayTeam']['score'] is not None else 0
        home_score = g['homeTeam']['score'] if g['homeTeam']['score'] is not None else 0
        status_text = g['gameStatusText']
        quarter = g.get('period', 0)
        clock = g.get('gameClock', 'N/A')
        is_live = g['gameStatus'] in [2, 3]  # 2 = live, 3 = halftime
        is_completed = g['gameStatus'] == 4  # 4 = final

        game_info = {
            "away_team": away_name,
            "home_team": home_name,
            "away_score": away_score,
            "home_score": home_score,
            "score": f"{away_score} - {home_score}" if away_score > 0 else "N/A",
            "status": status_text,
            "quarter": quarter,
            "time_remaining": clock,
            "is_live": is_live,
            "is_completed": is_completed
        }
        all_games_today.append(game_info)

        # Print each game clearly
        score_str = f"{away_score} - {home_score}" if away_score > 0 else "N/A"
        tag = " LIVE " if is_live else " FINAL " if is_completed else ""
        print(f"{away_name} @ {home_name}  |  {score_str}  |  Q{quarter}  {clock}  |  {status_text}{tag}")

    print("-" * 80)

except Exception as e:
    print(f"Scoreboard error: {e}")

# Save
data = {
    "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
    "all_games_today": all_games_today
}

with open('nba_today_games.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: nba_today_games.json")
print("JSON preview:")
print(json.dumps(data, indent=2))
print("Script finished.")