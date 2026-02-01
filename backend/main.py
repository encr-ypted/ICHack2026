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
        "pass": "pass_model.joblib",
        "shot": "shot_model.joblib",
        "win": "win_model.joblib"
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


# --- HIGHLIGHT/LOWLIGHT SCORING ENGINE ---
# Thresholds for categorizing moments
HIGHLIGHT_THRESHOLD = 0.1   # Minimum score for a positive highlight
LOWLIGHT_THRESHOLD = -0.1   # Maximum score for a negative lowlight (area for improvement)

def calculate_highlight_score(event: dict, game_state: dict) -> tuple[float, str, float, float]:
    """
    Calculate ML-driven highlight score for an event.
    
    Positive scores indicate good performance (highlights).
    Negative scores indicate areas for improvement (lowlights).
    
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
        dribble_outcome = event.get("dribble", {}).get("outcome", {}).get("name", "")
        if dribble_outcome == "Complete":
            value_added = 0.3
            description = "Successful Dribble"
        elif dribble_outcome == "Incomplete":
            # Failed dribble - negative impact (lost possession)
            value_added = -0.25
            description = "Failed Dribble (Dispossessed)"
            
    elif event_type == "Interception":
        value_added = 0.25
        description = "Defensive Interception"
        
    elif event_type == "Ball Recovery":
        value_added = 0.15
        description = "Ball Recovery"
        
    elif event_type == "Dispossessed":
        # Lost the ball under pressure
        value_added = -0.2
        description = "Dispossessed"
        
    elif event_type == "Miscontrol":
        # Failed to control the ball
        value_added = -0.15
        description = "Miscontrol"
        
    elif event_type == "Foul Committed":
        # Committed a foul
        card = event.get("foul_committed", {}).get("card", {}).get("name", "")
        if card == "Red Card":
            value_added = -1.0
            description = "RED CARD - Sent Off"
        elif card == "Second Yellow":
            value_added = -0.8
            description = "Second Yellow - Sent Off"
        elif card == "Yellow Card":
            value_added = -0.3
            description = "Yellow Card"
        else:
            value_added = -0.1
            description = "Foul Committed"
    
    # Final Highlight Score: (Value Added + xT) * Clutch Factor
    # Clutch factor amplifies both positive AND negative scores in crucial moments
    clutch_factor = 1.0 + abs(win_prob_delta)
    highlight_score = (value_added + xt_delta) * clutch_factor
    
    return highlight_score, description, xt_delta, value_added


def _score_pass(event: dict, xt_delta: float) -> tuple[float, str]:
    """
    Score a pass event using ML model.
    
    Positive scoring: Difficult passes completed (low P_success, but succeeded)
    Negative scoring: Easy passes failed (high P_success, but failed)
    
    Thresholds:
        - P_success > 0.8: "Easy" pass - failure is penalized
        - P_success < 0.5: "Difficult" pass - success is rewarded
    """
    pass_data = event.get("pass", {})
    
    # Check for special pass types first (always positive)
    if pass_data.get("goal_assist"):
        return 1.0, "Goal Assist"
    if pass_data.get("shot_assist"):
        return 0.6, "Key Pass (Chance Created)"
    
    # Use ML model for pass success probability
    p_success = predict_pass_success(event)
    
    # In StatsBomb, missing 'outcome' means pass was successful
    pass_completed = "outcome" not in pass_data
    
    if p_success is not None:
        if pass_completed:
            # POSITIVE: Value Added = difficulty overcome (1 - P_success)
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
        else:
            # NEGATIVE: Failed pass - penalize based on how easy it should have been
            # Higher P_success = easier pass = more negative impact when failed
            if p_success > 0.8:
                # Easy pass missed - significant negative impact
                value_added = -(p_success - 0.5)  # Range: -0.3 to -0.5
                description = "Easy Pass Missed (Turnover)"
            elif p_success > 0.6:
                # Moderate difficulty pass missed
                value_added = -(p_success - 0.4)  # Range: -0.2 to -0.4
                description = "Pass Failed (Turnover)"
            else:
                # Difficult pass missed - less penalty
                value_added = -0.1
                description = "Ambitious Pass Failed"
            
            return value_added, description
    
    # Fallback: use xT-based scoring (no ML model available)
    if pass_completed:
        if xt_delta > 0.05:
            return 0.3, "Progressive Pass"
        return 0.0, "Regular Pass"
    else:
        # Failed pass without ML - use xT loss
        if xt_delta < -0.05:
            return -0.3, "Pass Failed (Lost Territory)"
        return -0.1, "Pass Failed"


def _score_shot(event: dict, game_state: dict) -> tuple[float, str, float]:
    """
    Score a shot event using ML model.
    
    Positive scoring: Goals from difficult positions (low xG converted)
    Negative scoring: Big chances missed (high xG not converted)
    
    Thresholds:
        - xG > 0.4: "Big Chance" - missing is heavily penalized
        - xG > 0.25: "Good Chance" - missing is moderately penalized
        - xG < 0.1: "Difficult Shot" - scoring is heavily rewarded
    """
    shot_data = event.get("shot", {})
    outcome = shot_data.get("outcome", {}).get("name", "")
    
    # Get xG from model
    xg = predict_xg(event)
    
    # Fallback to StatsBomb xG if model unavailable
    if xg is None:
        xg = shot_data.get("statsbomb_xg", 0.1)
    
    win_prob_delta = 0.0
    
    if outcome == "Goal":
        # POSITIVE: Value Added = beating the odds (1 - xG)
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
    
    # Not a goal - evaluate based on chance quality
    if xg > 0.4:
        # BIG CHANCE MISSED - significant negative impact
        # The higher the xG, the more negative (should have scored)
        value_added = -(xg - 0.1)  # Range: -0.3 to -0.9 for high xG
        
        if outcome == "Saved":
            description = "Big Chance Missed (Saved)"
            value_added *= 0.7  # Less penalty - at least on target
        elif outcome == "Post":
            description = "Big Chance Missed (Hit Post)"
            value_added *= 0.8  # Slightly less penalty
        elif outcome in ["Off T", "Wayward"]:
            description = "Big Chance Missed (Off Target)"
        elif outcome == "Blocked":
            description = "Big Chance Blocked"
            value_added *= 0.6  # Less penalty - defender intervened
        else:
            description = "Big Chance Missed"
            
    elif xg > 0.25:
        # GOOD CHANCE MISSED - moderate negative impact
        value_added = -(xg - 0.15)  # Range: -0.1 to -0.25
        
        if outcome == "Saved":
            description = "Chance Missed (Saved)"
            value_added *= 0.5  # On target gets credit
        elif outcome in ["Off T", "Wayward"]:
            description = "Chance Missed (Off Target)"
        else:
            description = f"Chance Missed ({outcome})"
            
    else:
        # LOW xG SHOT - minor positive/neutral (taking the shot is fine)
        if outcome == "Saved":
            value_added = xg * 0.5  # Credit for testing keeper
            description = "Shot on Target"
        elif outcome == "Post":
            value_added = xg * 0.4
            description = "Shot Hit Post"
        elif outcome in ["Blocked"]:
            value_added = xg * 0.2
            description = "Shot Blocked"
        else:
            value_added = 0.0  # Neutral - difficult shot missed
            description = f"Shot Off Target"
    
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
) -> tuple[dict, list, list]:
    """
    Analyze player events and return stats with top highlights AND areas for improvement.
    
    Args:
        match_events: Dictionary of match events from StatsBomb
        player_name: Name of player to analyze
        home_team: Home team name for win probability calculations
        top_n: Number of top moments to return for each category
    
    Returns:
        tuple: (player_stats, top_highlights, areas_for_improvement)
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
        return {"error": f"Player '{player_name}' not found"}, [], []
    
    print(f"Analyzing {len(player_events)} events for {player_name}...")
    
    # Process all events to track game state
    player_event_ids = {e.get("id") for e in player_events}
    all_moments = []
    total_highlight_score = 0.0
    total_value_added = 0.0
    positive_contributions = 0
    negative_contributions = 0
    
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
        
        # Track positive vs negative contributions
        if highlight_score > 0:
            positive_contributions += 1
        elif highlight_score < 0:
            negative_contributions += 1
        
        # Store moment if it meets either threshold (highlight or lowlight)
        moment_data = {
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
        }
        
        # Include if above highlight threshold OR below lowlight threshold
        if highlight_score > HIGHLIGHT_THRESHOLD or highlight_score < LOWLIGHT_THRESHOLD:
            all_moments.append(moment_data)
    
    # Separate into highlights (positive) and lowlights (negative)
    highlights = [m for m in all_moments if m["highlight_score"] > HIGHLIGHT_THRESHOLD]
    lowlights = [m for m in all_moments if m["highlight_score"] < LOWLIGHT_THRESHOLD]
    
    # Sort highlights: highest positive first
    top_highlights = sorted(
        highlights, 
        key=lambda x: x["highlight_score"], 
        reverse=True
    )[:top_n]
    
    # Sort lowlights: most negative first (worst mistakes)
    areas_for_improvement = sorted(
        lowlights, 
        key=lambda x: x["highlight_score"]  # Ascending - most negative first
    )[:top_n]
    
    # Calculate player statistics
    pass_events = [e for e in player_events if e["type"]["name"] == "Pass"]
    complete_passes = [p for p in pass_events if "outcome" not in p.get("pass", {})]
    shot_events = [e for e in player_events if e["type"]["name"] == "Shot"]
    goals = [s for s in shot_events if s.get("shot", {}).get("outcome", {}).get("name") == "Goal"]
    
    stats = {
        "name": player_name,
        "total_highlight_score": round(total_highlight_score, 2),
        "total_value_added": round(total_value_added, 2),
        "total_actions": len(player_events),
        "positive_contributions": positive_contributions,
        "negative_contributions": negative_contributions,
        "highlights_count": len(highlights),
        "lowlights_count": len(lowlights),
        "pass_accuracy": (
            f"{int(len(complete_passes) / len(pass_events) * 100)}%" 
            if pass_events else "N/A"
        ),
        "shots": len(shot_events),
        "goals": len(goals),
        "ml_models_active": {
            "pass_model": ML_MODELS.get("pass") is not None,
            "shot_model": ML_MODELS.get("shot") is not None,
            "win_model": ML_MODELS.get("win") is not None
        }
    }
    
    return stats, top_highlights, areas_for_improvement


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
        
        if highlight_score > HIGHLIGHT_THRESHOLD:
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


# --- CLAUDE PROMPT GENERATION ---
def generate_claude_prompt(
    player_name: str,
    stats: dict,
    top_highlights: list,
    areas_for_improvement: list
) -> str:
    """
    Generate a structured prompt for Claude to provide player feedback.
    
    The prompt requests:
    1. A positive observation from the best highlight
    2. Constructive criticism based on the worst lowlight
    3. A specific training drill to address the lowlight
    4. An encouraging closing statement
    
    Args:
        player_name: Name of the player
        stats: Player statistics dictionary
        top_highlights: List of top positive moments
        areas_for_improvement: List of negative moments (lowlights)
    
    Returns:
        Formatted prompt string for Claude
    """
    # Build highlight section
    if top_highlights:
        best_highlight = top_highlights[0]
        highlight_section = f"""
## Best Highlight:
- **Time:** {best_highlight['time_display']}
- **Event:** {best_highlight['description']}
- **Impact Score:** {best_highlight['highlight_score']:.3f}
- **Value Added:** {best_highlight['value_added']:.3f}
- **Video:** {best_highlight['video_url']}
"""
    else:
        highlight_section = """
## Best Highlight:
No significant highlights recorded in this match.
"""
    
    # Build lowlight section
    if areas_for_improvement:
        worst_lowlight = areas_for_improvement[0]
        lowlight_section = f"""
## Key Area for Improvement:
- **Time:** {worst_lowlight['time_display']}
- **Event:** {worst_lowlight['description']}
- **Impact Score:** {worst_lowlight['highlight_score']:.3f}
- **Value Lost:** {abs(worst_lowlight['value_added']):.3f}
- **Video:** {worst_lowlight['video_url']}
"""
    else:
        lowlight_section = """
## Key Area for Improvement:
No significant areas for improvement identified - excellent performance!
"""
    
    # Build the full prompt
    prompt = f"""You are an elite football performance analyst providing personalized feedback to a player after analyzing their match performance using advanced ML models.

# Player Analysis: {player_name}

## Match Statistics:
- **Total Actions:** {stats.get('total_actions', 0)}
- **Positive Contributions:** {stats.get('positive_contributions', 0)}
- **Negative Contributions:** {stats.get('negative_contributions', 0)}
- **Pass Accuracy:** {stats.get('pass_accuracy', 'N/A')}
- **Shots:** {stats.get('shots', 0)}
- **Goals:** {stats.get('goals', 0)}
- **Net Impact Score:** {stats.get('total_highlight_score', 0):.2f}
{highlight_section}
{lowlight_section}

---

Please provide feedback in the following structure:

### 1. Positive Observation
Analyze the best highlight moment. Explain what made this action technically impressive and tactically smart. Be specific about body positioning, decision-making speed, or execution quality.

### 2. Constructive Criticism
Analyze the area for improvement. Explain the technical or tactical reason this moment had negative impact. Consider:
- Was it a positioning issue?
- Was it decision-making under pressure?
- Was it technical execution (first touch, weight of pass, shot technique)?
- Was it awareness of surrounding players?

Be honest but supportive - frame it as a growth opportunity.

### 3. Training Drill Recommendation
Recommend ONE specific training drill that would directly address the weakness identified. Include:
- **Drill Name:** A clear, descriptive name
- **Setup:** How to set up the drill
- **Execution:** Step-by-step instructions
- **Focus Points:** What to concentrate on during the drill
- **Progression:** How to increase difficulty over time

### 4. Closing Encouragement
Provide an encouraging closing statement that:
- Acknowledges the player's strengths
- Frames the improvement area as achievable
- Motivates continued development

Keep the tone professional, supportive, and actionable. Use football terminology appropriately.
"""
    
    return prompt


def generate_coach_summary(
    player_name: str,
    stats: dict,
    top_highlights: list,
    areas_for_improvement: list
) -> dict:
    """
    Generate a structured summary for coach dashboard display.
    
    Returns a dictionary ready for JSON serialization.
    """
    return {
        "player_name": player_name,
        "summary": {
            "total_actions": stats.get("total_actions", 0),
            "net_impact": stats.get("total_highlight_score", 0),
            "positive_ratio": (
                stats.get("positive_contributions", 0) / 
                max(stats.get("total_actions", 1), 1)
            ),
            "pass_accuracy": stats.get("pass_accuracy", "N/A"),
            "goals": stats.get("goals", 0),
            "shots": stats.get("shots", 0)
        },
        "top_highlights": [
            {
                "time": h["time_display"],
                "description": h["description"],
                "score": h["highlight_score"],
                "video_url": h["video_url"]
            }
            for h in top_highlights
        ],
        "areas_for_improvement": [
            {
                "time": l["time_display"],
                "description": l["description"],
                "score": l["highlight_score"],
                "video_url": l["video_url"]
            }
            for l in areas_for_improvement
        ],
        "claude_prompt": generate_claude_prompt(
            player_name, stats, top_highlights, areas_for_improvement
        )
    }


# --- EXECUTION ---
if __name__ == "__main__":
    # Load match data
    wc_final_events, _ = load_match_data()
    
    # Analyze individual player
    print("=" * 70)
    print("PLAYER ANALYSIS: Lionel Messi")
    print("=" * 70)
    
    stats, highlights, lowlights = get_player_data(
        wc_final_events, 
        "Lionel Andrés Messi Cuccittini"
    )
    
    print(f"\n[STATS] PLAYER STATISTICS:")
    print(f"   Name: {stats['name']}")
    print(f"   Total Actions: {stats['total_actions']}")
    print(f"   Positive Contributions: {stats['positive_contributions']}")
    print(f"   Negative Contributions: {stats['negative_contributions']}")
    print(f"   Pass Accuracy: {stats['pass_accuracy']}")
    print(f"   Shots: {stats['shots']} | Goals: {stats['goals']}")
    print(f"   Net Impact Score: {stats['total_highlight_score']:.2f}")
    print(f"   ML Models Active: {stats['ml_models_active']}")
    
    print(f"\n[+] TOP {len(highlights)} HIGHLIGHTS:")
    if highlights:
        for i, m in enumerate(highlights, 1):
            print(f"   {i}. [{m['time_display']}] {m['description']}")
            print(f"      Score: +{m['highlight_score']:.3f} | Value: +{m['value_added']:.3f} | xT: {m['xt_delta']:+.4f}")
            print(f"      Watch: {m['video_url']}")
    else:
        print("   No significant highlights recorded.")
    
    print(f"\n[-] TOP {len(lowlights)} AREAS FOR IMPROVEMENT:")
    if lowlights:
        for i, m in enumerate(lowlights, 1):
            print(f"   {i}. [{m['time_display']}] {m['description']}")
            print(f"      Score: {m['highlight_score']:.3f} | Value: {m['value_added']:.3f} | xT: {m['xt_delta']:+.4f}")
            print(f"      Watch: {m['video_url']}")
    else:
        print("   No significant areas for improvement - excellent performance!")
    
    # Generate Claude prompt
    print("\n" + "=" * 70)
    print("CLAUDE PROMPT (For AI Feedback Generation)")
    print("=" * 70)
    claude_prompt = generate_claude_prompt(stats['name'], stats, highlights, lowlights)
    print(claude_prompt[:1500] + "..." if len(claude_prompt) > 1500 else claude_prompt)
    
    # Get match-wide highlights
    print("\n" + "=" * 70)
    print("MATCH-WIDE TOP HIGHLIGHTS")
    print("=" * 70)
    
    match_highlights = get_match_highlights(wc_final_events)
    for i, m in enumerate(match_highlights, 1):
        print(f"   {i}. [{m['time_display']}] {m['player']}")
        print(f"      {m['description']} (Score: {m['highlight_score']:.3f})")
    
    # Test with another player who might have more lowlights
    print("\n" + "=" * 70)
    print("PLAYER ANALYSIS: Test Player with Potential Lowlights")
    print("=" * 70)
    
    # Try a defender or midfielder who might have turnovers
    stats2, highlights2, lowlights2 = get_player_data(
        wc_final_events,
        "Rodrigo Javier De Paul"  # Midfielder - likely has both highlights and turnovers
    )
    
    if "error" not in stats2:
        print(f"\n[STATS] {stats2['name']}:")
        print(f"   Positive: {stats2['positive_contributions']} | Negative: {stats2['negative_contributions']}")
        print(f"   Highlights: {len(highlights2)} | Lowlights: {len(lowlights2)}")
        
        if lowlights2:
            print(f"\n   Worst moment: [{lowlights2[0]['time_display']}] {lowlights2[0]['description']} ({lowlights2[0]['highlight_score']:.3f})")
    else:
        print(f"   {stats2}")
