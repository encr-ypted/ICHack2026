"""
CoachOS Highlight Engine - ML-Driven Event Analysis
Uses trained models to identify True Highlights based on execution difficulty and match context.
"""
import math
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from ultils.match_loader import get_match_events, get_match_lineups

# --- CONFIGURATION ---
MATCH_ID = 3869151
YOUTUBE_VIDEO_ID = "vkyCLzUvv7c"
MODELS_DIR = Path(__file__).parent / "models"

# Video Offsets (synced to YouTube timestamps)
PERIOD_OFFSETS = {
    1: 595, 2: 3963, 3: 7339, 4: 8443, 5: 9500
}

# StatsBomb pitch dimensions and goal coordinates
PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0
GOAL_CENTER = (120.0, 40.0)

# --- MODEL LOADING ---
def load_models():
    """Load ML models from disk. Returns dict of models or None if not found."""
    models = {}
    model_files = {
        "pass": "coachos_pass_model.joblib",
        "shot": "coachos_shot_model.joblib",
        "win": "coachos_win_model.joblib"
    }
    
    for model_type, filename in model_files.items():
        model_path = MODELS_DIR / filename
        if model_path.exists():
            models[model_type] = joblib.load(model_path)
        else:
            print(f"Warning: {filename} not found at {model_path}")
            models[model_type] = None
    
    return models

# Initialize models at module level
ML_MODELS = load_models()

# --- EXPECTED THREAT (xT) GRID ---
# Standard Karun Singh 12x8 grid, transposed for StatsBomb coordinates
XT_GRID = np.array([
    [0.006, 0.007, 0.008, 0.009, 0.011, 0.012, 0.013, 0.014],
    [0.007, 0.008, 0.009, 0.010, 0.012, 0.014, 0.015, 0.016],
    [0.008, 0.009, 0.011, 0.013, 0.015, 0.018, 0.021, 0.024],
    [0.009, 0.010, 0.012, 0.014, 0.018, 0.022, 0.024, 0.028],
    [0.010, 0.011, 0.014, 0.017, 0.023, 0.029, 0.035, 0.039],
    [0.011, 0.013, 0.016, 0.021, 0.031, 0.040, 0.046, 0.057],
    [0.012, 0.014, 0.017, 0.024, 0.036, 0.048, 0.061, 0.076],
    [0.013, 0.015, 0.019, 0.026, 0.039, 0.052, 0.073, 0.098],
    [0.014, 0.016, 0.021, 0.028, 0.044, 0.060, 0.086, 0.124],
    [0.014, 0.017, 0.024, 0.032, 0.052, 0.075, 0.108, 0.169],
    [0.015, 0.019, 0.027, 0.037, 0.062, 0.092, 0.146, 0.245],
    [0.015, 0.021, 0.030, 0.045, 0.068, 0.110, 0.170, 0.283]
]).T

# --- DATA LOADING ---
def load_match_data(match_id: int = 3869151, match_title: str = "argentina_v_france"):
    """Load match events and lineups from cache or StatsBomb API."""
    events = get_match_events(match_id, match_title)
    lineups = get_match_lineups(match_id, match_title)
    return events, lineups


# --- xT GRID UTILITIES ---
def get_grid_cell(x: float, y: float) -> tuple[int, int]:
    """
    Maps pitch coordinates to 12x8 grid cell.
    StatsBomb pitch: x=0-120 (length), y=0-80 (width)
    """
    col = min(int(x / 10), 11)
    row = min(int(y / 10), 7)
    return col, row


def calculate_xt_delta(start_loc: list, end_loc: list) -> float:
    """Calculate expected threat added by moving the ball."""
    if not start_loc or not end_loc:
        return 0.0
    s_col, s_row = get_grid_cell(start_loc[0], start_loc[1])
    e_col, e_row = get_grid_cell(end_loc[0], end_loc[1])
    return float(XT_GRID[e_row][e_col] - XT_GRID[s_row][s_col])


# --- FEATURE ENGINEERING (The Transformer) ---
def extract_features(event: dict, model_type: str) -> Optional[pd.DataFrame]:
    """
    Converts a StatsBomb JSON event into a DataFrame row with model-specific features.
    
    Args:
        event: StatsBomb event dictionary
        model_type: One of 'pass', 'shot', or 'win'
    
    Returns:
        DataFrame with features or None if extraction fails
    """
    try:
        if model_type == "pass":
            return _extract_pass_features(event)
        elif model_type == "shot":
            return _extract_shot_features(event)
        elif model_type == "win":
            return _extract_win_features(event)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    except (KeyError, TypeError):
        return None


def _extract_pass_features(event: dict) -> Optional[pd.DataFrame]:
    """Extract features for pass success prediction."""
    if "pass" not in event or "location" not in event:
        return None
    
    start_x, start_y = event["location"]
    pass_data = event["pass"]
    
    if "end_location" not in pass_data:
        return None
    
    end_x, end_y = pass_data["end_location"]
    
    # Calculate pass geometry
    dx = end_x - start_x
    dy = end_y - start_y
    pass_length = math.sqrt(dx**2 + dy**2)
    pass_angle = math.atan2(dy, dx)  # Radians
    
    # Pressure indicator (1 if under pressure, 0 otherwise)
    under_pressure = 1 if event.get("under_pressure", False) else 0
    
    features = {
        "start_x": start_x,
        "start_y": start_y,
        "end_x": end_x,
        "end_y": end_y,
        "pass_length": pass_length,
        "pass_angle": pass_angle,
        "under_pressure": under_pressure
    }
    
    return pd.DataFrame([features])


def _extract_shot_features(event: dict) -> Optional[pd.DataFrame]:
    """Extract features for xG (shot quality) prediction."""
    if "shot" not in event or "location" not in event:
        return None
    
    shot_x, shot_y = event["location"]
    
    # Distance to goal center (120, 40)
    dx = GOAL_CENTER[0] - shot_x
    dy = GOAL_CENTER[1] - shot_y
    dist_to_goal = math.sqrt(dx**2 + dy**2)
    
    # Angle to goal (radians) - angle between shot direction and goal line
    shot_angle = math.atan2(abs(dy), dx)
    
    under_pressure = 1 if event.get("under_pressure", False) else 0
    
    features = {
        "shot_x": shot_x,
        "shot_y": shot_y,
        "dist_to_goal": dist_to_goal,
        "shot_angle": shot_angle,
        "under_pressure": under_pressure
    }
    
    return pd.DataFrame([features])


def _extract_win_features(event: dict, score_diff_home: int = 0, xg_diff_home: float = 0.0) -> pd.DataFrame:
    """Extract features for win probability prediction."""
    minute = event.get("minute", 0)
    time_remaining = max(0, 90 - minute)
    
    features = {
        "time_remaining": time_remaining,
        "score_diff_home": score_diff_home,
        "xg_diff_home": xg_diff_home
    }
    
    return pd.DataFrame([features])


# --- ML INFERENCE ENGINE ---
def predict_pass_success(event: dict) -> Optional[float]:
    """Predict probability of pass success using ML model."""
    if ML_MODELS.get("pass") is None:
        return None
    
    features = extract_features(event, "pass")
    if features is None:
        return None
    
    try:
        prob = ML_MODELS["pass"].predict_proba(features)[0][1]
        return float(prob)
    except Exception:
        return None


def predict_xg(event: dict) -> Optional[float]:
    """Predict expected goals (xG) for a shot using ML model."""
    if ML_MODELS.get("shot") is None:
        return None
    
    features = extract_features(event, "shot")
    if features is None:
        return None
    
    try:
        xg = ML_MODELS["shot"].predict_proba(features)[0][1]
        return float(xg)
    except Exception:
        return None


def predict_win_probability(minute: int, score_diff_home: int, xg_diff_home: float) -> Optional[float]:
    """Predict win probability given game state."""
    if ML_MODELS.get("win") is None:
        return None
    
    time_remaining = max(0, 90 - minute)
    features = pd.DataFrame([{
        "time_remaining": time_remaining,
        "score_diff_home": score_diff_home,
        "xg_diff_home": xg_diff_home
    }])
    
    try:
        prob = ML_MODELS["win"].predict_proba(features)[0][1]
        return float(prob)
    except Exception:
        return None


def calculate_win_prob_delta(
    event: dict,
    score_before: int,
    score_after: int,
    xg_before: float,
    xg_after: float
) -> float:
    """
    Calculate win probability delta for major events.
    Compares game state before and after the event.
    """
    minute = event.get("minute", 0)
    
    prob_before = predict_win_probability(minute, score_before, xg_before)
    prob_after = predict_win_probability(minute, score_after, xg_after)
    
    if prob_before is None or prob_after is None:
        return 0.0
    
    return prob_after - prob_before


# --- HIGHLIGHT SCORING ENGINE ---
def calculate_highlight_score(event: dict, game_state: dict) -> tuple[float, str, float, float]:
    """
    Calculate ML-driven highlight score for an event.
    
    Returns:
        tuple: (highlight_score, description, xT_delta, value_added)
    """
    event_type = event.get("type", {}).get("name", "")
    description = "Regular Play"
    value_added = 0.0
    xt_delta = 0.0
    win_prob_delta = 0.0
    
    # Calculate xT for ball progression events
    if "location" in event and "pass" in event and "end_location" in event.get("pass", {}):
        xt_delta = calculate_xt_delta(event["location"], event["pass"]["end_location"])
    elif "location" in event and "carry" in event and "end_location" in event.get("carry", {}):
        xt_delta = calculate_xt_delta(event["location"], event["carry"]["end_location"])
    
    if event_type == "Pass":
        value_added, description = _score_pass(event, xt_delta)
        
    elif event_type == "Shot":
        value_added, description, win_prob_delta = _score_shot(event, game_state)
        
    elif event_type == "Dribble":
        if event.get("dribble", {}).get("outcome", {}).get("name") == "Complete":
            value_added = 0.3
            description = "Successful Dribble"
            
    elif event_type == "Interception":
        value_added = 0.25
        description = "Defensive Interception"
        
    elif event_type == "Ball Recovery":
        value_added = 0.15
        description = "Ball Recovery"
    
    # Final Highlight Score: (Value Added + xT) * Clutch Factor
    clutch_factor = 1.0 + abs(win_prob_delta)
    highlight_score = (value_added + xt_delta) * clutch_factor
    
    return highlight_score, description, xt_delta, value_added


def _score_pass(event: dict, xt_delta: float) -> tuple[float, str]:
    """Score a pass event using ML model."""
    pass_data = event.get("pass", {})
    
    # Check for special pass types first
    if pass_data.get("goal_assist"):
        return 1.0, "Goal Assist"
    if pass_data.get("shot_assist"):
        return 0.6, "Key Pass (Chance Created)"
    
    # Use ML model for pass success probability
    p_success = predict_pass_success(event)
    
    # In StatsBomb, missing 'outcome' means pass was successful
    pass_completed = "outcome" not in pass_data
    
    if p_success is not None and pass_completed:
        # Value Added = difficulty overcome (1 - P_success)
        value_added = 1.0 - p_success
        
        if value_added > 0.7:
            description = "Exceptional Pass (High Difficulty)"
        elif value_added > 0.5:
            description = "Impressive Pass"
        elif xt_delta > 0.05:
            description = "Line-Breaking Pass"
        else:
            description = "Completed Pass"
        
        return value_added, description
    
    # Fallback: use xT-based scoring
    if xt_delta > 0.05:
        return 0.3, "Progressive Pass"
    
    return 0.0, "Regular Pass"


def _score_shot(event: dict, game_state: dict) -> tuple[float, str, float]:
    """Score a shot event using ML model."""
    shot_data = event.get("shot", {})
    outcome = shot_data.get("outcome", {}).get("name", "")
    
    # Get xG from model
    xg = predict_xg(event)
    
    # Fallback to StatsBomb xG if model unavailable
    if xg is None:
        xg = shot_data.get("statsbomb_xg", 0.1)
    
    win_prob_delta = 0.0
    
    if outcome == "Goal":
        # Value Added = beating the odds (1 - xG)
        value_added = 1.0 - xg
        description = "GOAL SCORED"
        
        # Calculate win probability swing for goals
        score_before = game_state.get("score_diff", 0)
        score_after = score_before + 1
        xg_before = game_state.get("xg_diff", 0.0)
        xg_after = xg_before + xg
        
        win_prob_delta = calculate_win_prob_delta(
            event, score_before, score_after, xg_before, xg_after
        )
        
        return value_added, description, win_prob_delta
        
    elif outcome == "Saved":
        value_added = xg * 0.5  # Credit for testing the keeper
        description = "Shot on Target"
        
    elif outcome in ["Blocked", "Off T", "Wayward", "Post"]:
        value_added = xg * 0.2
        description = f"Shot ({outcome})"
        
    else:
        value_added = xg * 0.1
        description = "Shot Attempt"
    
    return value_added, description, win_prob_delta


# --- VIDEO SYNC UTILITIES ---
def get_pitch_pilot_url(minute: int, second: int, period: int) -> str:
    """
    Generate YouTube URL with timestamp synced to match time.
    Handles different period offsets for full match replays.
    """
    current_offset = PERIOD_OFFSETS.get(period, 595)
    
    if period == 1:
        elapsed = (minute * 60) + second
    elif period == 2:
        elapsed = ((minute - 45) * 60) + second
    elif period == 3:
        elapsed = ((minute - 90) * 60) + second
    elif period == 4:
        elapsed = ((minute - 105) * 60) + second
    else:
        elapsed = 0
    
    total_seconds = elapsed + current_offset
    return f"https://youtu.be/{YOUTUBE_VIDEO_ID}?si=OnqNuuoaeIR1kVXI&t={int(total_seconds)}"


# --- GAME STATE TRACKER ---
class GameStateTracker:
    """Tracks running game state for win probability calculations."""
    
    def __init__(self, home_team: str):
        self.home_team = home_team
        self.home_score = 0
        self.away_score = 0
        self.home_xg = 0.0
        self.away_xg = 0.0
    
    @property
    def score_diff(self) -> int:
        return self.home_score - self.away_score
    
    @property
    def xg_diff(self) -> float:
        return self.home_xg - self.away_xg
    
    def update(self, event: dict):
        """Update game state based on event."""
        team = event.get("team", {}).get("name", "")
        event_type = event.get("type", {}).get("name", "")
        
        if event_type == "Shot":
            shot_data = event.get("shot", {})
            xg = shot_data.get("statsbomb_xg", 0.0)
            is_goal = shot_data.get("outcome", {}).get("name") == "Goal"
            
            if team == self.home_team:
                self.home_xg += xg
                if is_goal:
                    self.home_score += 1
            else:
                self.away_xg += xg
                if is_goal:
                    self.away_score += 1
    
    def get_state(self) -> dict:
        return {
            "score_diff": self.score_diff,
            "xg_diff": self.xg_diff,
            "home_score": self.home_score,
            "away_score": self.away_score
        }


# --- MAIN PLAYER ANALYSIS FUNCTION ---
def get_player_data(
    match_events: dict,
    player_name: str,
    home_team: str = "Argentina",
    top_n: int = 5
) -> tuple[dict, list]:
    """
    Analyze player events and return stats with top ML-scored highlights.
    
    Args:
        match_events: Dictionary of match events from StatsBomb
        player_name: Name of player to analyze
        home_team: Home team name for win probability calculations
        top_n: Number of top moments to return
    
    Returns:
        tuple: (player_stats, top_moments)
    """
    # Flatten events dict to list and sort by timestamp
    events_list = list(match_events.values())
    events_list.sort(key=lambda e: (e.get("minute", 0), e.get("second", 0)))
    
    # Initialize game state tracker
    game_state = GameStateTracker(home_team)
    
    # Filter for player events
    player_events = [
        e for e in events_list 
        if e.get("player", {}).get("name") == player_name
    ]
    
    if not player_events:
        return {"error": f"Player '{player_name}' not found"}, []
    
    print(f"Analyzing {len(player_events)} events for {player_name}...")
    
    # Process all events to track game state
    player_event_ids = {e.get("id") for e in player_events}
    processed_moments = []
    total_highlight_score = 0.0
    total_value_added = 0.0
    
    for event in events_list:
        # Update game state for all events
        game_state.update(event)
        
        # Only score player's events
        if event.get("id") not in player_event_ids:
            continue
        
        # Calculate ML-driven highlight score
        highlight_score, description, xt_delta, value_added = calculate_highlight_score(
            event, game_state.get_state()
        )
        
        total_highlight_score += highlight_score
        total_value_added += value_added
        
        # Filter for interesting moments (positive highlight score)
        if highlight_score > 0.05:
            processed_moments.append({
                "time_display": f"{event['minute']}:{event['second']:02d}",
                "event_type": event["type"]["name"],
                "description": description,
                "highlight_score": round(highlight_score, 3),
                "value_added": round(value_added, 3),
                "xt_delta": round(xt_delta, 4),
                "video_url": get_pitch_pilot_url(
                    event["minute"], 
                    event["second"], 
                    event["period"]
                ),
                "period": event["period"],
                "minute": event["minute"]
            })
    
    # Sort by Highlight Score (highest first) and take top N
    top_moments = sorted(
        processed_moments, 
        key=lambda x: x["highlight_score"], 
        reverse=True
    )[:top_n]
    
    # Calculate player statistics
    pass_events = [e for e in player_events if e["type"]["name"] == "Pass"]
    complete_passes = [p for p in pass_events if "outcome" not in p.get("pass", {})]
    
    stats = {
        "name": player_name,
        "total_highlight_score": round(total_highlight_score, 2),
        "total_value_added": round(total_value_added, 2),
        "total_actions": len(player_events),
        "moments_analyzed": len(processed_moments),
        "pass_accuracy": (
            f"{int(len(complete_passes) / len(pass_events) * 100)}%" 
            if pass_events else "N/A"
        ),
        "ml_models_active": {
            "pass_model": ML_MODELS.get("pass") is not None,
            "shot_model": ML_MODELS.get("shot") is not None,
            "win_model": ML_MODELS.get("win") is not None
        }
    }
    
    return stats, top_moments


def get_match_highlights(
    match_events: dict,
    home_team: str = "Argentina",
    top_n: int = 10
) -> list:
    """
    Get top highlights from entire match (all players).
    Useful for match summary views.
    """
    events_list = list(match_events.values())
    events_list.sort(key=lambda e: (e.get("minute", 0), e.get("second", 0)))
    
    game_state = GameStateTracker(home_team)
    all_moments = []
    
    for event in events_list:
        game_state.update(event)
        
        player_name = event.get("player", {}).get("name")
        if not player_name:
            continue
        
        highlight_score, description, xt_delta, value_added = calculate_highlight_score(
            event, game_state.get_state()
        )
        
        if highlight_score > 0.1:
            all_moments.append({
                "player": player_name,
                "team": event.get("team", {}).get("name", ""),
                "time_display": f"{event['minute']}:{event['second']:02d}",
                "event_type": event["type"]["name"],
                "description": description,
                "highlight_score": round(highlight_score, 3),
                "video_url": get_pitch_pilot_url(
                    event["minute"],
                    event["second"],
                    event["period"]
                )
            })
    
    return sorted(all_moments, key=lambda x: x["highlight_score"], reverse=True)[:top_n]


# --- EXECUTION ---
if __name__ == "__main__":
    # Load match data
    wc_final_events, _ = load_match_data()
    
    # Analyze individual player
    print("=" * 60)
    print("PLAYER ANALYSIS: Lionel Messi")
    print("=" * 60)
    
    stats, moments = get_player_data(wc_final_events, "Lionel Andrés Messi Cuccittini")
    
    print(f"\nPlayer Stats: {stats}")
    print(f"\nTop {len(moments)} Highlights:")
    for i, m in enumerate(moments, 1):
        print(f"  {i}. [{m['time_display']}] {m['description']}")
        print(f"     Score: {m['highlight_score']:.3f} | Value Added: {m['value_added']:.3f} | xT: {m['xt_delta']:.4f}")
        print(f"     Watch: {m['video_url']}")
    
    # Get match-wide highlights
    print("\n" + "=" * 60)
    print("MATCH HIGHLIGHTS")
    print("=" * 60)
    
    match_highlights = get_match_highlights(wc_final_events)
    for i, m in enumerate(match_highlights, 1):
        print(f"  {i}. [{m['time_display']}] {m['player']} - {m['description']} (Score: {m['highlight_score']:.3f})")
