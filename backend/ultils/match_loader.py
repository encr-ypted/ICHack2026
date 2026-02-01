from statsbombpy import sb
import json
import os

DATA_DIR = "./data"
MATCH_ID = 3869151


def get_match_events(match_id, match_title):
    file_path = os.path.join(DATA_DIR, f"match_{match_title}_events_{match_id}.json")

    # 1. Check if we already have it saved
    if os.path.exists(file_path):
        print(f"Loading match {match_id} from local cache...")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. If not, fetch it from StatsBomb
    print(f"Fetching match {match_id} from StatsBomb (this might take a bit)...")
    events = sb.events(match_id=match_id, fmt="dict")

    # 3. Save it for next time
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

    return events


def get_match_lineups(match_id, match_title):
    file_path = os.path.join(DATA_DIR, f"match_{match_title}_lineups_{match_id}.json")

    # 1. Check local cache
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 2. Fetch from StatsBomb
    # statsbombpy returns a dict where keys are Team Names
    print(f"Fetching lineups for match {match_id}...")
    lineups = sb.lineups(match_id=match_id)

    # 3. Save to cache
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        # Note: sb.lineups returns dataframes in a dict,
        # so we convert them to records (JSON friendly)
        json_ready_lineups = {team: df.to_dict(orient='records') for team, df in lineups.items()}
        json.dump(json_ready_lineups, f, ensure_ascii=False, indent=4)

    return json_ready_lineups