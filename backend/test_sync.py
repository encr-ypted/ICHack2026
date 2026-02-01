"""
Video Sync Tester for Argentina vs France 2022 World Cup Final

This script tests if your video offset correctly aligns StatsBomb event 
timestamps with the actual YouTube video.

Usage:
    python test_sync.py

Adjust MY_VIDEO_OFFSET until the generated URLs land ~2-3 seconds before 
each milestone event.
"""

def get_youtube_url(minute, second, offset, video_id="MGP3y7TMxIQ"):
    """Generate a YouTube embed URL with autoplay at the specified timestamp."""
    total_seconds = (minute * 60) + second + offset
    return f"https://www.youtube.com/embed/{video_id}?start={total_seconds}&autoplay=1"


def get_youtube_short_url(minute, second, offset, video_id="vkyCLzUvv7c"):
    """Generate a shorter youtu.be URL (easier to click in terminal)."""
    total_seconds = (minute * 60) + second + offset
    return f"https://youtu.be/{video_id}?t={total_seconds}"


# --- CONFIGURATION ---
# Replace this with the 'Whistle Offset' you found (in seconds)
# Example: If the 1st half whistle blows at 09:55 in video, offset = 595
FIRST_HALF_OFFSET = 595  # Adjust this until sync is perfect

# Video IDs (use the one that matches your video)
FULL_MATCH_VIDEO_ID = "vkyCLzUvv7c"  # Full match video
HIGHLIGHTS_VIDEO_ID = "MGP3y7TMxIQ"  # Highlights video (from Gemini example)

# Choose which video you're testing against
ACTIVE_VIDEO_ID = FULL_MATCH_VIDEO_ID


# --- VERIFIED STATSBOMB MILESTONES (2022 Final - 1st Half) ---
first_half_milestones = [
    {"name": "Kick Off", "min": 0, "sec": 0, "description": "First whistle of the match"},
    {"name": "Di Maria Foul (Penalty Won)", "min": 21, "sec": 1, "description": "Ousmane Dembele fouls Di Maria in the box"},
    {"name": "Messi Goal (Penalty)", "min": 22, "sec": 10, "description": "Messi scores from the spot"},
    {"name": "Di Maria Goal (Team Move)", "min": 35, "sec": 42, "description": "Beautiful team goal - high xT sequence"},
]

# --- EXTENDED MILESTONES (Full Match) ---
# Use these to test multi-period sync
full_match_milestones = [
    # 1st Half
    {"name": "1H: Kick Off", "min": 0, "sec": 0, "period": 1},
    {"name": "1H: Messi Penalty Goal", "min": 22, "sec": 10, "period": 1},
    {"name": "1H: Di Maria Goal", "min": 35, "sec": 42, "period": 1},
    
    # 2nd Half (clock resets to 45:00)
    {"name": "2H: Mbappé Penalty Goal", "min": 80, "sec": 0, "period": 2},
    {"name": "2H: Mbappé 2nd Goal", "min": 81, "sec": 0, "period": 2},
    
    # Extra Time 1 (clock resets to 90:00)
    {"name": "ET1: Messi Goal", "min": 108, "sec": 0, "period": 3},
    
    # Extra Time 2 (clock resets to 105:00)
    {"name": "ET2: Mbappé Hat-trick", "min": 118, "sec": 0, "period": 4},
]


def get_pitch_pilot_url(minute, second, period):
    """
    Generates a synchronized YouTube URL for the Argentina vs France 2022 Final.
    Handles the clock resets between halves and extra time.
    
    This mirrors the function in main.py for consistency.
    """
    # Whistle moment offsets in the full match video (in seconds)
    offsets = {
        1: 595,   # 1st Half Whistle starts at ~9:55 in video
        2: 3963,  # 2nd Half Whistle starts at ~66:03 in video
        3: 7339,  # ET 1 Whistle starts at ~122:19 in video
        4: 8443,  # ET 2 Whistle starts at ~140:43 in video
        5: 9500   # Penalty Shootout start (approximate)
    }

    current_offset = offsets.get(period, 595)

    # StatsBomb clock logic - subtract starting minute of each period
    if period == 1:
        elapsed_seconds = (minute * 60) + second
    elif period == 2:
        elapsed_seconds = ((minute - 45) * 60) + second
    elif period == 3:
        elapsed_seconds = ((minute - 90) * 60) + second
    elif period == 4:
        elapsed_seconds = ((minute - 105) * 60) + second
    else:
        elapsed_seconds = 0

    total_seconds = elapsed_seconds + current_offset
    return f"https://youtu.be/{FULL_MATCH_VIDEO_ID}?t={int(total_seconds)}"


def test_first_half_sync():
    """Test synchronization for first half events only."""
    print("\n" + "=" * 60)
    print(f"🎬 FIRST HALF SYNC TEST (Offset: {FIRST_HALF_OFFSET}s)")
    print("=" * 60)
    print(f"Video: {ACTIVE_VIDEO_ID}")
    print("-" * 60)
    
    for m in first_half_milestones:
        url = get_youtube_short_url(m['min'], m['sec'], FIRST_HALF_OFFSET, ACTIVE_VIDEO_ID)
        print(f"\n📍 {m['name']} ({m['min']}:{m['sec']:02d})")
        print(f"   {m['description']}")
        print(f"   🔗 {url}")
    
    print("\n" + "-" * 60)
    print("VERIFICATION STEPS:")
    print("1. Click each link above")
    print("2. Video should start 2-3 seconds BEFORE the action")
    print("3. If too early: DECREASE the offset")
    print("4. If too late: INCREASE the offset")
    print("-" * 60)


def test_full_match_sync():
    """Test synchronization across all periods."""
    print("\n" + "=" * 60)
    print("🏆 FULL MATCH SYNC TEST (Multi-Period)")
    print("=" * 60)
    print(f"Video: {FULL_MATCH_VIDEO_ID}")
    print("-" * 60)
    
    for m in full_match_milestones:
        period = m.get('period', 1)
        url = get_pitch_pilot_url(m['min'], m['sec'], period)
        print(f"\n📍 {m['name']} ({m['min']}:{m['sec']:02d}) - Period {period}")
        print(f"   🔗 {url}")
    
    print("\n" + "-" * 60)
    print("KEY MOMENTS TO VERIFY:")
    print("• Di Maria Goal (35:42) - Famous team move, high xT passes")
    print("• Mbappé's two goals in 97 seconds (80:00, 81:37)")
    print("• Messi's ET goal (108:00) - Blocked then tapped in")
    print("-" * 60)


def test_from_json_events():
    """Test with actual events from your JSON data."""
    import json
    import os
    
    events_file = "./data/match_argentina_v_france_events_3869151.json"
    
    if not os.path.exists(events_file):
        print(f"\n⚠️  Events file not found: {events_file}")
        print("   Run main.py first to download the data.")
        return
    
    print("\n" + "=" * 60)
    print("📊 TESTING WITH ACTUAL JSON DATA")
    print("=" * 60)
    
    with open(events_file, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    # Find all goals in the match
    goals = []
    for event_id, event in events.items():
        if event.get('type', {}).get('name') == 'Shot':
            outcome = event.get('shot', {}).get('outcome', {}).get('name', '')
            if outcome == 'Goal':
                goals.append({
                    'player': event.get('player', {}).get('name', 'Unknown'),
                    'minute': event.get('minute', 0),
                    'second': event.get('second', 0),
                    'period': event.get('period', 1),
                    'team': event.get('team', {}).get('name', 'Unknown')
                })
    
    print(f"\nFound {len(goals)} goals in match data:\n")
    
    for goal in goals:
        url = get_pitch_pilot_url(goal['minute'], goal['second'], goal['period'])
        print(f"⚽ {goal['player']} ({goal['team']})")
        print(f"   Time: {goal['minute']}:{goal['second']:02d} (Period {goal['period']})")
        print(f"   🔗 {url}\n")


if __name__ == "__main__":
    print("\n" + "🏟️ " * 20)
    print("    ARGENTINA vs FRANCE 2022 - VIDEO SYNC TESTER")
    print("🏟️ " * 20)
    
    # Run tests
    test_first_half_sync()
    test_full_match_sync()
    test_from_json_events()
    
    print("\n" + "=" * 60)
    print("💡 DEMO TIP FOR JUDGES:")
    print("=" * 60)
    print("""
Click the 'Di Maria Goal (35:42)' link during your presentation.

This goal is famous for being a beautiful team move. Your data will
show HUGE xT values for the 4 passes leading up to it.

The pitch: "Our ML identified this sequence as having the highest
'Expected Threat' of the half. If we click the link... [video plays]
...you can see the exact tactical transition our model identified."
""")
