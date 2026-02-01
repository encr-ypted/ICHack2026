from statsbombpy import sb
import pandas as pd
from ultils.match_loader import get_match_events
from ultils.match_loader import get_match_lineups

MATCH_ID = 3869685
video_offset_seconds = 0

def get_player_data(player_name):
  events = sb.events(match_id=MATCH_ID)

  print(events)


get_match_events(3869151, "argentina_v_france")
get_match_lineups(3869151, "argentina_v_france")

