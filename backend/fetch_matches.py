"""
Utility script to fetch missing Argentina World Cup 2022 match data from StatsBomb.
Run this script to download all missing match data.

Usage: python fetch_matches.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from statsbombpy import sb
    HAS_STATSBOMB = True
except ImportError:
    HAS_STATSBOMB = False
    print("statsbombpy not installed. Install it with: pip install statsbombpy")
    sys.exit(1)

from ultils.match_loader import get_match_events, get_match_lineups

# All Argentina World Cup 2022 matches
ARGENTINA_MATCHES = [
    {"match_id": 3857300, "match_title": "argentina_v_saudi_arabia", "label": "Argentina vs Saudi Arabia"},
    {"match_id": 3857289, "match_title": "argentina_v_mexico", "label": "Argentina vs Mexico"},
    {"match_id": 3857264, "match_title": "poland_v_argentina", "label": "Poland vs Argentina"},
    {"match_id": 3869151, "match_title": "argentina_v_france", "label": "Argentina vs Australia (R16)"},
    {"match_id": 3869321, "match_title": "netherlands_v_argentina", "label": "Netherlands vs Argentina (QF)"},
    {"match_id": 3869519, "match_title": "argentina_v_croatia", "label": "Argentina vs Croatia (SF)"},
    {"match_id": 3869685, "match_title": "argentina_v_france_final", "label": "Argentina vs France (Final)"},
]


def main():
    print("=" * 60)
    print("Fetching Argentina World Cup 2022 Match Data")
    print("=" * 60)
    
    for match in ARGENTINA_MATCHES:
        match_id = match["match_id"]
        match_title = match["match_title"]
        label = match["label"]
        
        print(f"\nProcessing: {label} (ID: {match_id})")
        
        try:
            # This will either load from cache or fetch from StatsBomb
            events = get_match_events(match_id, match_title)
            print(f"  Events: {len(events) if isinstance(events, list) else 'loaded'}")
            
            lineups = get_match_lineups(match_id, match_title)
            teams = list(lineups.keys()) if isinstance(lineups, dict) else []
            print(f"  Lineups: {teams}")
            
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Done! All available match data has been cached.")
    print("=" * 60)


if __name__ == "__main__":
    main()
