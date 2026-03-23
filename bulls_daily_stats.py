import pandas as pd
import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import leaguedashteamstats, leaguegamefinder, leaguegamelog
from nba_api.stats.static import teams  # ← THIS WAS MISSING – now imported
from datetime import datetime, timedelta
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
win_probability = None
win_explanation = ""

# 1. Bulls Stats
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
            "pts": float(b.get('PTS', 0)),
            "reb": float(b.get('REB', 0)),
            "ast": float(b.get('AST', 0)),
            "tov": float(b.get('TOV', 0)),
            "fgm": float(b.get('FGM', 0)),
            "fga": float(b.get('FGA', 0)),
            "fg3m": float(b.get('FG3M', 0)),
            "fg3a": float(b.get('FG3A', 0)),
            "ftm": float(b.get('FTM', 0)),
            "fta": float(b.get('FTA', 0))
        }

        a = adv[adv['TEAM_ID'] == bulls_id]
        if not a.empty:
            a = a.iloc[0]
            bulls_advanced = {
                "off_rating": float(a.get('OFF_RATING', None)),
                "def_rating": float(a.get('DEF_RATING', None)),
                "net_rating": float(a.get('NET_RATING', None)),
                "ts_pct": float(a.get('TS_PCT', None)),
                "pace": float(a.get('PACE', None))
            }

            print("\nBulls Season Stats:")
            for k, v in bulls_basic.items():
                print(f"{k.upper()}: {v:.1f}")
            for k, v in bulls_advanced.items():
                print(f"{k.replace('_', ' ').title()}: {v:.2f}")
    else:
        print("No Bulls row found in stats")
except Exception as e:
    print(f"Stats error: {e}")

# 2. Next Game + Win Probability
try:
    print("\nFetching next game and win probability...")
    games = leaguegamefinder.LeagueGameFinder(team_id_nullable=bulls_id, season_nullable=current_season).get_data_frames()[0]
    games['GAME_DATE'] = pd.to_datetime(games['GAME_DATE'])
    upcoming = games[games['GAME_DATE'] > datetime.now() - timedelta(days=1)].sort_values('GAME_DATE')

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

        # Get opponent net rating
        opp_team = teams.find_team_by_abbreviation(next_opp_abbr)
        opp_net = 0
        if opp_team:
            opp_row = adv[adv['TEAM_ID'] == opp_team['id']]
            if not opp_row.empty:
                opp_net = float(opp_row.iloc[0]['NET_RATING'])

        # Last 5 games win % for form
        last5_bulls = leaguegamelog.LeagueGameLog(team_id_nullable=bulls_id, season_nullable=current_season, last_n_games_nullable=5).get_data_frames()[0]
        last5_opp = leaguegamelog.LeagueGameLog(team_id_nullable=opp_team['id'], season_nullable=current_season, last_n_games_nullable=5).get_data_frames()[0] if opp_team else pd.DataFrame()

        bulls_recent_win_pct = (last5_bulls['WL'].str.count('W').sum() / max(1, len(last5_bulls))) * 100 if not last5_bulls.empty else 50
        opp_recent_win_pct = (last5_opp['WL'].str.count('W').sum() / max(1, len(last5_opp))) * 100 if not last5_opp.empty else 50

        # Win probability formula
        rating_diff = (bulls_advanced.get('net_rating', 0) - opp_net) * 1.8
        home_adv = 5 if is_home else -3
        form_diff = (bulls_recent_win_pct - opp_recent_win_pct) * 0.4
        win_probability = max(5, min(95, 50 + rating_diff + home_adv + form_diff))
        win_explanation = f"Net rating diff ({rating_diff:.1f}) + home adv ({home_adv}) + recent form ({form_diff:.1f})"

        print(f"Next game: {next_game['date']} vs {next_opp_abbr} ({'Home' if is_home else 'Away'})")
        print(f"Win Probability: {win_probability:.1f}%")
        print(f"Explanation: {win_explanation}")
    else:
        print("No upcoming games found – win probability set to N/A")
except Exception as e:
    print(f"Next game / win prob error: {e}")

# Injury Report (your current version – cleaned player name)
try:
    print("\nScraping Bulls injury report...")
    url = "https://www.cbssports.com/nba/teams/CHI/chicago-bulls/injuries/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.select_one("table")
    injuries = []
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
                player_text = cols[0].get_text(strip=True)
                # Clean duplicated name (take the last part as full name)
                player = player_text.split()[-1] if len(player_text.split()) > 1 else player_text
                injuries.append({
                    "player": player,
                    "position": cols[1].get_text(strip=True),
                    "injury": cols[2].get_text(strip=True),
                    "status": cols[3].get_text(strip=True)
                })
except Exception as e:
    print(f"Injury scrape error: {e}")
    injuries = []

# Save JSON
data = {
    "date": datetime.now().strftime('%Y-%m-%d'),
    "bulls_season_stats": {
        "ppg": bulls_basic.get("pts"),
        "rpg": bulls_basic.get("reb"),
        "apg": bulls_basic.get("ast"),
        "tovpg": bulls_basic.get("tov"),
        "fgm": bulls_basic.get("fgm"),
        "fga": bulls_basic.get("fga"),
        "fg3m": bulls_basic.get("fg3m"),
        "fg3a": bulls_basic.get("fg3a"),
        "ftm": bulls_basic.get("ftm"),
        "fta": bulls_basic.get("fta"),
        "off_rating": bulls_advanced.get("off_rating"),
        "def_rating": bulls_advanced.get("def_rating"),
        "net_rating": bulls_advanced.get("net_rating"),
        "ts_pct": bulls_advanced.get("ts_pct"),
        "pace": bulls_advanced.get("pace")
    },
    "next_game": next_game,
    "win_probability": round(win_probability, 1) if win_probability is not None else None,
    "win_explanation": win_explanation,
    "injuries": injuries
}

with open('bulls_daily.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_daily.json")
print("Script finished.")