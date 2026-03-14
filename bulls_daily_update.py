import pandas as pd
import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import leaguedashteamstats, leaguegamefinder
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import teams
from datetime import datetime
import json

print("=== Bulls Daily Team Efficiency Update ===")
print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

bulls_id = 1610612741
current_season = '2025-26'

# Initialize variables
bulls_basic = {}
bulls_advanced = {}
calculated = {}
today_game = None
next_game = None
injuries = []

# 1. Basic & Advanced Stats
try:
    basic = leaguedashteamstats.LeagueDashTeamStats(
        season=current_season,
        measure_type_detailed_defense='Base',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    adv = leaguedashteamstats.LeagueDashTeamStats(
        season=current_season,
        measure_type_detailed_defense='Advanced',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]

    team_data = pd.merge(
        basic[['TEAM_ID', 'TEAM_NAME', 'PTS', 'REB', 'AST', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA']],
        adv[['TEAM_ID', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'TS_PCT', 'PACE', 'PIE']],
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
            "pace": float(bulls['PACE']),
            "pie": float(bulls.get('PIE', 0.0))
        }

        print("\nBulls Basic Stats:")
        for k, v in bulls_basic.items():
            print(f"{k.upper()}: {v:.1f}")

        print("\nBulls Advanced Stats (API):")
        for k, v in bulls_advanced.items():
            print(f"{k.replace('_', ' ').title()}: {v:.2f}")

        # Calculated Advanced Metrics
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

        print("\nCalculated Advanced Metrics:")
        for k, v in calculated.items():
            print(f"{k.replace('_', ' ').title()}: {v:.3f}")
    else:
        print("No Bulls data found")
except Exception as e:
    print(f"Stats error: {e}")

# 2. Today's Game Check
try:
    sb = scoreboard.ScoreBoard()
    games = sb.get_dict()['scoreboard']['games']

    print(f"\nGames today ({datetime.now().strftime('%Y-%m-%d')}): {len(games)}")
    for g in games:
        home = g['homeTeam']['teamName']
        away = g['awayTeam']['teamName']
        status = g['gameStatusText']
        print(f"{away} @ {home} - {status}")

        if bulls_id == g['homeTeam']['teamId'] or bulls_id == g['awayTeam']['teamId']:
            today_game = {
                "opponent": away if bulls_id == g['homeTeam']['teamId'] else home,
                "home": bulls_id == g['homeTeam']['teamId'],
                "status": status
            }
            print("  *** BULLS GAME TODAY! ***")
            break

    if today_game:
        print(f"Bulls play today vs {today_game['opponent']} ({'Home' if today_game['home'] else 'Away'}) - {today_game['status']}")
    else:
        print("No Bulls game today.")
except Exception as e:
    print(f"Today's game error: {e}")

# 3. Next Game if No Today
if not today_game:
    try:
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
                "is_home": is_home
            }
            print(f"\nNext game: {next_game['date']} vs {next_game['opponent']} ({'Home' if is_home else 'Away'})")
        else:
            print("\nNo upcoming games (season may be over or playoffs)")
    except Exception as e:
        print(f"Next game error: {e}")

# 4. Injury Report (CBS Sports scrape)
try:
    url = "https://www.cbssports.com/nba/teams/chi/chicago-bulls/injuries"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    injuries = []
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')[1:]  # skip header
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                player = cols[0].text.strip()
                position = cols[1].text.strip()
                injury = cols[2].text.strip()
                status = cols[3].text.strip()
                injuries.append({
                    "player": player,
                    "position": position,
                    "injury": injury,
                    "status": status
                })

    if injuries:
        print("\nBulls Injury Report (latest):")
        for inj in injuries:
            print(f"{inj['player']} ({inj['position']}): {inj['injury']} - {inj['status']}")
    else:
        print("\nNo injuries found or page structure changed")
except Exception as e:
    print(f"Injury scrape error: {e}")
    injuries = []

# 5. Save JSON with injuries included
data = {
    "date": datetime.now().strftime('%Y-%m-%d'),
    "bulls_basic": bulls_basic,
    "bulls_advanced": bulls_advanced,
    "calculated": calculated,
    "game_today": today_game,
    "next_game": next_game,
    "injuries": injuries  # Now saved here!
}

with open('bulls_team_efficiency.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_team_efficiency.json (with injuries)")
print("Script finished.")