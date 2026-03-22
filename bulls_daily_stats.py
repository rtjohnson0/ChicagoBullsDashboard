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
# 3. Injury Report - Proper column parsing + cleaned names + correct status
try:
    print("\nScraping Bulls injury report from CBS...")
    url = "https://www.cbssports.com/nba/teams/CHI/chicago-bulls/injuries/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.select_one("table.injuries-table") or soup.select_one("table")
    injuries = []

    if table:
        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
                # Player name cell - clean duplication
                player_cell = cols[0]
                player_text = player_cell.get_text(strip=True)

                # Remove duplicated name pattern (e.g. "J. SmithJalen Smith" → "Jalen Smith")
                import re
                # Split on lowercase-uppercase transition or use regex to take full name
                cleaned_player = re.sub(r'([A-Z][a-z]\.)\s*([A-Z][a-z]+)', r'\2', player_text)  # e.g. "J. SmithJalen Smith" → "Jalen Smith"
                cleaned_player = re.sub(r'([A-Z][a-z]+)([A-Z][a-z]+)', r'\1 \2', cleaned_player)  # add space if missing
                player = cleaned_player.strip() or player_text.strip()

                # Position
                position = cols[1].get_text(strip=True)

                # Injury / Date (usually col 2)
                injury_date = cols[2].get_text(strip=True)

                # Status - this is usually col 3 or 4 (Questionable, Out, etc.)
                # CBS often has Status in col 3 or 4 - check length and content
                status_col = cols[3] if len(cols) > 3 else cols[2]
                status = status_col.get_text(strip=True)

                # If status looks like date or injury type, swap with previous column
                if any(word in status.lower() for word in ['thu', 'fri', 'sat', 'sun', 'mon', 'calf', 'knee', 'ankle']):
                    # Likely swapped columns - try col 2 as status
                    status = cols[2].get_text(strip=True)
                    injury_date = cols[3].get_text(strip=True) if len(cols) > 3 else injury_date

                # Clean status to standard terms
                status_lower = status.lower()
                if 'out' in status_lower or 'out indefinitely' in status_lower:
                    status_clean = 'Out'
                elif 'questionable' in status_lower or 'doubtful' in status_lower:
                    status_clean = 'Questionable'
                elif 'probable' in status_lower or 'day-to-day' in status_lower:
                    status_clean = 'Probable / Day-to-Day'
                else:
                    status_clean = status or 'Unknown'

                injuries.append({
                    "player": player,
                    "position": position,
                    "injury": injury_date,
                    "status": status_clean
                })

    if injuries:
        print("\nBulls Injury Report (cleaned & fixed):")
        for inj in injuries:
            print(f"{inj['player']} ({inj['position']}): {inj['injury']} - {inj['status']}")
    else:
        print("No injuries found or page structure changed - CBS may have updated layout")
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
    "injuries": injuries  # now with clean player + full status
}

with open('bulls_daily.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved: bulls_daily.json")
print("Script finished.")