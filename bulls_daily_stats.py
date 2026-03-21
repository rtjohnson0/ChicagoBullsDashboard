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
current_season = '2025-26'  # Moved here so it's global

bulls_basic = {}
bulls_advanced = {}
next_game = {"date": None, "opponent": None, "is_home": None, "time": "TBD"}
injuries = []

# Try current season first, fallback if empty
seasons_to_try = [current_season, '2025']

stats_found = False

for season in seasons_to_try:
    if stats_found:
        break

    print(f"\nTrying season: {season}")

    try:
        time.sleep(1.5)

        basic = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Base',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]

        print(f"Basic stats rows: {len(basic)}")
        if 'TEAM_ID' in basic.columns:
            print("TEAM_ID column exists in basic")

        time.sleep(1.5)

        adv = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Advanced',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]

        print(f"Advanced stats rows: {len(adv)}")

        if len(basic) > 0 and len(adv) > 0:
            team_data = pd.merge(
                basic[['TEAM_ID', 'PTS', 'REB', 'AST', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA']],
                adv[['TEAM_ID', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'TS_PCT', 'PACE']],
                on='TEAM_ID',
                how='left'
            )

            bulls_row = team_data[team_data['TEAM_ID'] == bulls_id]
            print(f"Bulls rows found for {season}: {len(bulls_row)}")

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

                bulls_advanced = {
                    "off_rating": float(b.get('OFF_RATING', None)),
                    "def_rating": float(b.get('DEF_RATING', None)),
                    "net_rating": float(b.get('NET_RATING', None)),
                    "ts_pct": float(b.get('TS_PCT', None)),
                    "pace": float(b.get('PACE', None))
                }

                print("\nBulls Season Stats:")
                for k, v in bulls_basic.items():
                    print(f"{k.upper()}: {v:.1f}")
                for k, v in bulls_advanced.items():
                    print(f"{k.replace('_', ' ').title()}: {v}")

                stats_found = True
            else:
                print(f"No Bulls row found for season {season}")
        else:
            print(f"No data returned for season {season}")
    except Exception as e:
        print(f"Stats error for {season}: {e}")

# Next Game (fixed: current_season is now defined)
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
    else:
        print("\nNo upcoming games found")
except Exception as e:
    print(f"Next game error: {e}")

# Injury Report
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

    if injuries:
        print("\nBulls Injury Report:")
        for inj in injuries:
            print(f"{inj['player']} ({inj['position']}): {inj['injury']} - {inj['status']}")
except Exception as e:
    print(f"Injury scrape error: {e}")
    injuries = []

# Save to JSON
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
    "injuries": injuries
}

with open('bulls_daily.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_daily.json")
print("JSON content preview:")
print(json.dumps(data, indent=2))
print("Script finished.")