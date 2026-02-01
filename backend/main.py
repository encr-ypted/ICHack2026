from statsbombpy import sb
import pandas as pd
from ultils.match_loader import get_match_events
from ultils.match_loader import get_match_lineups

MATCH_ID = 3869685
VIDEO_OFFSET = 8443


link = "https://www.youtube.com/watch?v=vkyCLzUvv7c"



def get_player_data(match_events, player_name):
  # Fetch events
  events = match_events

  # Filter for the specific player
  player_events = events[events['player'] == player_name].copy()
  print(player_events)

  if player_events.empty:
    return {"error": "Player not found"}

  # 2. CALCULATE IMPACT (The HRT "Secret Sauce")
  # In a real run, you'd calculate Win Prob before/after every event.
  # For this script, let's assume we have calculated 'win_prob_delta'
  # (If you don't have the model running yet, we can mock these deltas for the MVP)

  # Let's mock the "Delta" for now to get the UI built,
  # then swap in the real model later.
  player_events['win_prob_delta'] = np.random.uniform(-0.02, 0.05, size=len(player_events))

  # 3. FIND KEY MOMENTS
  # Sort by highest impact (positive delta)
  top_moments = player_events.nlargest(3, 'win_prob_delta')

  formatted_moments = []
  for _, row in top_moments.iterrows():
    minute = row['minute']
    second = row['second']

    # Calculate YouTube Timestamp
    total_seconds = (minute * 60) + second + video_offset_seconds

    formatted_moments.append({
      "time_display": f"{minute}:{second:02d}",
      "event_type": row['type'],
      "impact": f"+{row['win_prob_delta'] * 100:.1f}% Win Prob",
      "video_url": f"https://www.youtube.com/embed/MGP3y7TMxIQ?start={total_seconds}&autoplay=1"
    })

  # 4. GENERATE STATS
  stats = {
    "name": player_name,
    "impact_score": round(player_events['win_prob_delta'].sum() * 10, 1),
    "pass_completion": "88%",  # You can calculate this easily from data
    "total_actions": len(player_events)
  }

  return stats, formatted_moments

wc_event_finals = get_match_events(3869151, "argentina_v_france")
get_match_lineups(3869151, "argentina_v_france")

#get_player_data(wc_event_finals, 'Damián Emiliano Martínez')

def get_pitch_pilot_url(minute, second, period):
  """
  Generates a synchronized YouTube URL for the Argentina vs France 2022 Final.
  Handles the clock resets between halves and extra time.
  """
  YOUTUBE_BASE_ID = "vkyCLzUvv7c"

  # These are your verified 'Whistle Moments' in seconds
  offsets = {
    1: 595,  # 1st Half Whistle starts at 0'
    2: 3963,  # 2nd Half Whistle starts at 45'
    3: 7339,  # ET 1 Whistle starts at 90'
    4: 8443,  # ET 2 Whistle starts at 105'
    5: 9500  # Penalty Shootout start (approximate)
  }

  # Get the offset for the current period, default to 1st half if missing
  current_offset = offsets.get(period, 595)

  # StatsBomb clock logic:
  # We subtract the 'Starting Minute' of the period to get elapsed time in that period,
  # then add the YouTube offset where that period actually begins.
  if period == 1:
    elapsed_seconds = (minute * 60) + second
  elif period == 2:
    elapsed_seconds = ((minute - 45) * 60) + second
  elif period == 3:
    elapsed_seconds = ((minute - 90) * 60) + second
  elif period == 4:
    elapsed_seconds = ((minute - 105) * 60) + second
  else:
    # For penalties or unknown periods, we just jump to the start of the offset
    elapsed_seconds = 0

  total_seconds = elapsed_seconds + current_offset

  return f"https://youtu.be/vkyCLzUvv7c?si=1Zpfgtxkdk6qmlhB&t={int(total_seconds)}"



