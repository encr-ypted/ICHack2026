"""
CoachOS Highlight Engine - ML-Driven Event Analysis
Uses trained models to identify True Highlights based on execution difficulty and match context.
"""
import math
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import unquote

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ultils.match_loader import get_match_events, get_match_lineups

# Check if statsbombpy is available for fetching new data
try:
    from statsbombpy import sb
    HAS_STATSBOMB = True
except ImportError:
    HAS_STATSBOMB = False

# --- CONFIGURATION ---
MATCH_ID = 3869151
MODELS_DIR = Path(__file__).parent / "models"

# ============================================
# COMPETITION CONFIGURATION
# ============================================
# StatsBomb Open Data - Available Competitions
COMPETITIONS = {
    "wc2022": {
        "id": "wc2022",
        "name": "FIFA World Cup 2022",
        "short_name": "WC 2022",
        "competition_id": 43,
        "season_id": 106,
        "country": "International",
        "year": 2022
    },
    "euro2024": {
        "id": "euro2024",
        "name": "UEFA Euro 2024",
        "short_name": "Euro 2024",
        "competition_id": 55,
        "season_id": 282,
        "country": "Europe",
        "year": 2024
    },
    "euro2020": {
        "id": "euro2020",
        "name": "UEFA Euro 2020",
        "short_name": "Euro 2020",
        "competition_id": 55,
        "season_id": 43,
        "country": "Europe",
        "year": 2021
    },
    "wc2018": {
        "id": "wc2018",
        "name": "FIFA World Cup 2018",
        "short_name": "WC 2018",
        "competition_id": 43,
        "season_id": 3,
        "country": "International",
        "year": 2018
    },
    "copa2024": {
        "id": "copa2024",
        "name": "Copa America 2024",
        "short_name": "Copa 2024",
        "competition_id": 223,
        "season_id": 282,
        "country": "South America",
        "year": 2024
    },
}

# Default competition
DEFAULT_COMPETITION = "wc2022"

# Match data organized by competition
# World Cup 2022 matches - Full tournament data
COMPETITION_MATCHES = {
    "wc2022": [
    # === ARGENTINA ===
    {"match_id": 3857300, "match_title": "argentina_v_saudi_arabia", "label": "Argentina 1-2 Saudi Arabia", "stage": "Group Stage", "date": "2022-11-22", "teams": ["Argentina", "Saudi Arabia"]},
    {"match_id": 3857289, "match_title": "argentina_v_mexico", "label": "Argentina 2-0 Mexico", "stage": "Group Stage", "date": "2022-11-26", "teams": ["Argentina", "Mexico"]},
    {"match_id": 3857264, "match_title": "poland_v_argentina", "label": "Poland 0-2 Argentina", "stage": "Group Stage", "date": "2022-11-30", "teams": ["Poland", "Argentina"]},
    {"match_id": 3869151, "match_title": "argentina_v_france", "label": "Argentina 2-1 Australia (R16)", "stage": "Round of 16", "date": "2022-12-03", "teams": ["Argentina", "Australia"]},
    {"match_id": 3869321, "match_title": "netherlands_v_argentina", "label": "Netherlands 2-2 Argentina (QF)", "stage": "Quarter-finals", "date": "2022-12-09", "teams": ["Netherlands", "Argentina"]},
    {"match_id": 3869519, "match_title": "argentina_v_croatia", "label": "Argentina 3-0 Croatia (SF)", "stage": "Semi-finals", "date": "2022-12-13", "teams": ["Argentina", "Croatia"]},
    {"match_id": 3869685, "match_title": "argentina_v_france_final", "label": "Argentina 3-3 France (Final)", "stage": "Final", "date": "2022-12-18", "teams": ["Argentina", "France"]},
    # === FRANCE ===
    {"match_id": 3857279, "match_title": "france_v_australia", "label": "France 4-1 Australia", "stage": "Group Stage", "date": "2022-11-22", "teams": ["France", "Australia"]},
    {"match_id": 3857266, "match_title": "france_v_denmark", "label": "France 2-1 Denmark", "stage": "Group Stage", "date": "2022-11-26", "teams": ["France", "Denmark"]},
    {"match_id": 3857275, "match_title": "tunisia_v_france", "label": "Tunisia 1-0 France", "stage": "Group Stage", "date": "2022-11-30", "teams": ["Tunisia", "France"]},
    {"match_id": 3869152, "match_title": "france_v_poland", "label": "France 3-1 Poland (R16)", "stage": "Round of 16", "date": "2022-12-04", "teams": ["France", "Poland"]},
    {"match_id": 3869354, "match_title": "england_v_france", "label": "England 1-2 France (QF)", "stage": "Quarter-finals", "date": "2022-12-10", "teams": ["England", "France"]},
    {"match_id": 3869552, "match_title": "france_v_morocco", "label": "France 2-0 Morocco (SF)", "stage": "Semi-finals", "date": "2022-12-14", "teams": ["France", "Morocco"]},
    # === BRAZIL ===
    {"match_id": 3857258, "match_title": "brazil_v_serbia", "label": "Brazil 2-0 Serbia", "stage": "Group Stage", "date": "2022-11-24", "teams": ["Brazil", "Serbia"]},
    {"match_id": 3857269, "match_title": "brazil_v_switzerland", "label": "Brazil 1-0 Switzerland", "stage": "Group Stage", "date": "2022-11-28", "teams": ["Brazil", "Switzerland"]},
    {"match_id": 3857280, "match_title": "cameroon_v_brazil", "label": "Cameroon 1-0 Brazil", "stage": "Group Stage", "date": "2022-12-02", "teams": ["Cameroon", "Brazil"]},
    {"match_id": 3869253, "match_title": "brazil_v_south_korea", "label": "Brazil 4-1 South Korea (R16)", "stage": "Round of 16", "date": "2022-12-05", "teams": ["Brazil", "South Korea"]},
    {"match_id": 3869420, "match_title": "croatia_v_brazil", "label": "Croatia 1-1 Brazil (QF)", "stage": "Quarter-finals", "date": "2022-12-09", "teams": ["Croatia", "Brazil"]},
    # === ENGLAND ===
    {"match_id": 3857271, "match_title": "england_v_iran", "label": "England 6-2 Iran", "stage": "Group Stage", "date": "2022-11-21", "teams": ["England", "Iran"]},
    {"match_id": 3857272, "match_title": "england_v_usa", "label": "England 0-0 USA", "stage": "Group Stage", "date": "2022-11-25", "teams": ["England", "United States"]},
    {"match_id": 3857261, "match_title": "wales_v_england", "label": "Wales 0-3 England", "stage": "Group Stage", "date": "2022-11-29", "teams": ["Wales", "England"]},
    {"match_id": 3869118, "match_title": "england_v_senegal", "label": "England 3-0 Senegal (R16)", "stage": "Round of 16", "date": "2022-12-04", "teams": ["England", "Senegal"]},
    # === SPAIN ===
    {"match_id": 3857291, "match_title": "spain_v_costa_rica", "label": "Spain 7-0 Costa Rica", "stage": "Group Stage", "date": "2022-11-23", "teams": ["Spain", "Costa Rica"]},
    {"match_id": 3857263, "match_title": "spain_v_germany", "label": "Spain 1-1 Germany", "stage": "Group Stage", "date": "2022-11-27", "teams": ["Spain", "Germany"]},
    {"match_id": 3869220, "match_title": "morocco_v_spain", "label": "Morocco 0-0 Spain (R16)", "stage": "Round of 16", "date": "2022-12-06", "teams": ["Morocco", "Spain"]},
    # === GERMANY ===
    {"match_id": 3857284, "match_title": "germany_v_japan", "label": "Germany 1-2 Japan", "stage": "Group Stage", "date": "2022-11-23", "teams": ["Germany", "Japan"]},
    {"match_id": 3857292, "match_title": "costa_rica_v_germany", "label": "Costa Rica 2-4 Germany", "stage": "Group Stage", "date": "2022-12-01", "teams": ["Costa Rica", "Germany"]},
    # === PORTUGAL ===
    {"match_id": 3857298, "match_title": "portugal_v_ghana", "label": "Portugal 3-2 Ghana", "stage": "Group Stage", "date": "2022-11-24", "teams": ["Portugal", "Ghana"]},
    {"match_id": 3857270, "match_title": "portugal_v_uruguay", "label": "Portugal 2-0 Uruguay", "stage": "Group Stage", "date": "2022-11-28", "teams": ["Portugal", "Uruguay"]},
    {"match_id": 3857262, "match_title": "south_korea_v_portugal", "label": "South Korea 2-1 Portugal", "stage": "Group Stage", "date": "2022-12-02", "teams": ["South Korea", "Portugal"]},
    {"match_id": 3869254, "match_title": "portugal_v_switzerland", "label": "Portugal 6-1 Switzerland (R16)", "stage": "Round of 16", "date": "2022-12-06", "teams": ["Portugal", "Switzerland"]},
    {"match_id": 3869486, "match_title": "morocco_v_portugal", "label": "Morocco 1-0 Portugal (QF)", "stage": "Quarter-finals", "date": "2022-12-10", "teams": ["Morocco", "Portugal"]},
    # === MOROCCO ===
    {"match_id": 3857277, "match_title": "morocco_v_croatia", "label": "Morocco 0-0 Croatia", "stage": "Group Stage", "date": "2022-11-23", "teams": ["Morocco", "Croatia"]},
    {"match_id": 3857283, "match_title": "belgium_v_morocco", "label": "Belgium 0-2 Morocco", "stage": "Group Stage", "date": "2022-11-27", "teams": ["Belgium", "Morocco"]},
    {"match_id": 3857276, "match_title": "canada_v_morocco", "label": "Canada 1-2 Morocco", "stage": "Group Stage", "date": "2022-12-01", "teams": ["Canada", "Morocco"]},
    {"match_id": 3869684, "match_title": "croatia_v_morocco", "label": "Croatia 2-1 Morocco (3rd)", "stage": "3rd Place", "date": "2022-12-17", "teams": ["Croatia", "Morocco"]},
    # === NETHERLANDS ===
    {"match_id": 3857285, "match_title": "senegal_v_netherlands", "label": "Senegal 0-2 Netherlands", "stage": "Group Stage", "date": "2022-11-21", "teams": ["Senegal", "Netherlands"]},
    {"match_id": 3857274, "match_title": "netherlands_v_ecuador", "label": "Netherlands 1-1 Ecuador", "stage": "Group Stage", "date": "2022-11-25", "teams": ["Netherlands", "Ecuador"]},
    {"match_id": 3857294, "match_title": "netherlands_v_qatar", "label": "Netherlands 2-0 Qatar", "stage": "Group Stage", "date": "2022-11-29", "teams": ["Netherlands", "Qatar"]},
    {"match_id": 3869117, "match_title": "netherlands_v_usa", "label": "Netherlands 3-1 USA (R16)", "stage": "Round of 16", "date": "2022-12-03", "teams": ["Netherlands", "United States"]},
    # === CROATIA ===
    {"match_id": 3857296, "match_title": "croatia_v_belgium", "label": "Croatia 0-0 Belgium", "stage": "Group Stage", "date": "2022-12-01", "teams": ["Croatia", "Belgium"]},
    {"match_id": 3857281, "match_title": "croatia_v_canada", "label": "Croatia 4-1 Canada", "stage": "Group Stage", "date": "2022-11-27", "teams": ["Croatia", "Canada"]},
    {"match_id": 3869219, "match_title": "japan_v_croatia", "label": "Japan 1-1 Croatia (R16)", "stage": "Round of 16", "date": "2022-12-05", "teams": ["Japan", "Croatia"]},
    # === JAPAN ===
    {"match_id": 3857295, "match_title": "japan_v_costa_rica", "label": "Japan 0-1 Costa Rica", "stage": "Group Stage", "date": "2022-11-27", "teams": ["Japan", "Costa Rica"]},
    {"match_id": 3857255, "match_title": "japan_v_spain", "label": "Japan 2-1 Spain", "stage": "Group Stage", "date": "2022-12-01", "teams": ["Japan", "Spain"]},
    ],
    
    # UEFA Euro 2024 - Key matches (more can be fetched dynamically)
    "euro2024": [
        # === SPAIN (Winner) ===
        {"match_id": 3942453, "match_title": "spain_v_croatia", "label": "Spain 3-0 Croatia", "stage": "Group Stage", "date": "2024-06-15", "teams": ["Spain", "Croatia"]},
        {"match_id": 3942459, "match_title": "spain_v_italy", "label": "Spain 1-0 Italy", "stage": "Group Stage", "date": "2024-06-20", "teams": ["Spain", "Italy"]},
        {"match_id": 3942549, "match_title": "spain_v_germany", "label": "Spain 2-1 Germany (QF)", "stage": "Quarter-finals", "date": "2024-07-05", "teams": ["Spain", "Germany"]},
        {"match_id": 3942553, "match_title": "spain_v_france", "label": "Spain 2-1 France (SF)", "stage": "Semi-finals", "date": "2024-07-09", "teams": ["Spain", "France"]},
        {"match_id": 3942555, "match_title": "spain_v_england", "label": "Spain 2-1 England (Final)", "stage": "Final", "date": "2024-07-14", "teams": ["Spain", "England"]},
        # === ENGLAND ===
        {"match_id": 3942454, "match_title": "england_v_serbia", "label": "England 1-0 Serbia", "stage": "Group Stage", "date": "2024-06-16", "teams": ["England", "Serbia"]},
        {"match_id": 3942461, "match_title": "denmark_v_england", "label": "Denmark 1-1 England", "stage": "Group Stage", "date": "2024-06-20", "teams": ["Denmark", "England"]},
        {"match_id": 3942545, "match_title": "england_v_switzerland", "label": "England 1-1 Switzerland (QF)", "stage": "Quarter-finals", "date": "2024-07-06", "teams": ["England", "Switzerland"]},
        {"match_id": 3942551, "match_title": "netherlands_v_england", "label": "Netherlands 1-2 England (SF)", "stage": "Semi-finals", "date": "2024-07-10", "teams": ["Netherlands", "England"]},
        # === FRANCE ===
        {"match_id": 3942456, "match_title": "austria_v_france", "label": "Austria 0-1 France", "stage": "Group Stage", "date": "2024-06-17", "teams": ["Austria", "France"]},
        {"match_id": 3942463, "match_title": "netherlands_v_france", "label": "Netherlands 0-0 France", "stage": "Group Stage", "date": "2024-06-21", "teams": ["Netherlands", "France"]},
        {"match_id": 3942541, "match_title": "france_v_belgium", "label": "France 1-0 Belgium (R16)", "stage": "Round of 16", "date": "2024-07-01", "teams": ["France", "Belgium"]},
        {"match_id": 3942547, "match_title": "portugal_v_france", "label": "Portugal 0-0 France (QF)", "stage": "Quarter-finals", "date": "2024-07-05", "teams": ["Portugal", "France"]},
        # === GERMANY (Host) ===
        {"match_id": 3942451, "match_title": "germany_v_scotland", "label": "Germany 5-1 Scotland", "stage": "Group Stage", "date": "2024-06-14", "teams": ["Germany", "Scotland"]},
        {"match_id": 3942457, "match_title": "germany_v_hungary", "label": "Germany 2-0 Hungary", "stage": "Group Stage", "date": "2024-06-19", "teams": ["Germany", "Hungary"]},
        {"match_id": 3942539, "match_title": "germany_v_denmark", "label": "Germany 2-0 Denmark (R16)", "stage": "Round of 16", "date": "2024-06-29", "teams": ["Germany", "Denmark"]},
        # === PORTUGAL ===
        {"match_id": 3942455, "match_title": "portugal_v_czechia", "label": "Portugal 2-1 Czechia", "stage": "Group Stage", "date": "2024-06-18", "teams": ["Portugal", "Czechia"]},
        {"match_id": 3942462, "match_title": "turkey_v_portugal", "label": "Turkey 0-3 Portugal", "stage": "Group Stage", "date": "2024-06-22", "teams": ["Turkey", "Portugal"]},
        {"match_id": 3942543, "match_title": "portugal_v_slovenia", "label": "Portugal 0-0 Slovenia (R16)", "stage": "Round of 16", "date": "2024-07-01", "teams": ["Portugal", "Slovenia"]},
        # === NETHERLANDS ===
        {"match_id": 3942452, "match_title": "poland_v_netherlands", "label": "Poland 1-2 Netherlands", "stage": "Group Stage", "date": "2024-06-16", "teams": ["Poland", "Netherlands"]},
        {"match_id": 3942537, "match_title": "romania_v_netherlands", "label": "Romania 0-3 Netherlands (R16)", "stage": "Round of 16", "date": "2024-07-02", "teams": ["Romania", "Netherlands"]},
        {"match_id": 3942550, "match_title": "netherlands_v_turkey", "label": "Netherlands 2-1 Turkey (QF)", "stage": "Quarter-finals", "date": "2024-07-06", "teams": ["Netherlands", "Turkey"]},
        # === ITALY ===
        {"match_id": 3942458, "match_title": "italy_v_albania", "label": "Italy 2-1 Albania", "stage": "Group Stage", "date": "2024-06-15", "teams": ["Italy", "Albania"]},
        {"match_id": 3942535, "match_title": "switzerland_v_italy", "label": "Switzerland 2-0 Italy (R16)", "stage": "Round of 16", "date": "2024-06-29", "teams": ["Switzerland", "Italy"]},
    ],
    
    # UEFA Euro 2020 - Key matches
    "euro2020": [
        # === ITALY (Winner) ===
        {"match_id": 3788741, "match_title": "turkey_v_italy", "label": "Turkey 0-3 Italy", "stage": "Group Stage", "date": "2021-06-11", "teams": ["Turkey", "Italy"]},
        {"match_id": 3788747, "match_title": "italy_v_switzerland", "label": "Italy 3-0 Switzerland", "stage": "Group Stage", "date": "2021-06-16", "teams": ["Italy", "Switzerland"]},
        {"match_id": 3788771, "match_title": "italy_v_austria", "label": "Italy 2-1 Austria (R16)", "stage": "Round of 16", "date": "2021-06-26", "teams": ["Italy", "Austria"]},
        {"match_id": 3788779, "match_title": "belgium_v_italy", "label": "Belgium 1-2 Italy (QF)", "stage": "Quarter-finals", "date": "2021-07-02", "teams": ["Belgium", "Italy"]},
        {"match_id": 3788785, "match_title": "italy_v_spain", "label": "Italy 1-1 Spain (SF)", "stage": "Semi-finals", "date": "2021-07-06", "teams": ["Italy", "Spain"]},
        {"match_id": 3788789, "match_title": "italy_v_england", "label": "Italy 1-1 England (Final)", "stage": "Final", "date": "2021-07-11", "teams": ["Italy", "England"]},
        # === ENGLAND ===
        {"match_id": 3788742, "match_title": "england_v_croatia", "label": "England 1-0 Croatia", "stage": "Group Stage", "date": "2021-06-13", "teams": ["England", "Croatia"]},
        {"match_id": 3788748, "match_title": "england_v_scotland", "label": "England 0-0 Scotland", "stage": "Group Stage", "date": "2021-06-18", "teams": ["England", "Scotland"]},
        {"match_id": 3788773, "match_title": "england_v_germany", "label": "England 2-0 Germany (R16)", "stage": "Round of 16", "date": "2021-06-29", "teams": ["England", "Germany"]},
        {"match_id": 3788781, "match_title": "ukraine_v_england", "label": "Ukraine 0-4 England (QF)", "stage": "Quarter-finals", "date": "2021-07-03", "teams": ["Ukraine", "England"]},
        {"match_id": 3788787, "match_title": "england_v_denmark", "label": "England 2-1 Denmark (SF)", "stage": "Semi-finals", "date": "2021-07-07", "teams": ["England", "Denmark"]},
        # === SPAIN ===
        {"match_id": 3788745, "match_title": "spain_v_sweden", "label": "Spain 0-0 Sweden", "stage": "Group Stage", "date": "2021-06-14", "teams": ["Spain", "Sweden"]},
        {"match_id": 3788769, "match_title": "croatia_v_spain", "label": "Croatia 3-5 Spain (R16)", "stage": "Round of 16", "date": "2021-06-28", "teams": ["Croatia", "Spain"]},
        {"match_id": 3788783, "match_title": "switzerland_v_spain", "label": "Switzerland 1-1 Spain (QF)", "stage": "Quarter-finals", "date": "2021-07-02", "teams": ["Switzerland", "Spain"]},
        # === FRANCE ===
        {"match_id": 3788746, "match_title": "france_v_germany", "label": "France 1-0 Germany", "stage": "Group Stage", "date": "2021-06-15", "teams": ["France", "Germany"]},
        {"match_id": 3788751, "match_title": "hungary_v_france", "label": "Hungary 1-1 France", "stage": "Group Stage", "date": "2021-06-19", "teams": ["Hungary", "France"]},
        {"match_id": 3788775, "match_title": "france_v_switzerland", "label": "France 3-3 Switzerland (R16)", "stage": "Round of 16", "date": "2021-06-28", "teams": ["France", "Switzerland"]},
        # === GERMANY ===
        {"match_id": 3788749, "match_title": "portugal_v_germany", "label": "Portugal 2-4 Germany", "stage": "Group Stage", "date": "2021-06-19", "teams": ["Portugal", "Germany"]},
        # === PORTUGAL ===
        {"match_id": 3788744, "match_title": "hungary_v_portugal", "label": "Hungary 0-3 Portugal", "stage": "Group Stage", "date": "2021-06-15", "teams": ["Hungary", "Portugal"]},
        {"match_id": 3788777, "match_title": "belgium_v_portugal", "label": "Belgium 1-0 Portugal (R16)", "stage": "Round of 16", "date": "2021-06-27", "teams": ["Belgium", "Portugal"]},
    ],
    
    # FIFA World Cup 2018 - Key matches
    "wc2018": [
        # === FRANCE (Winner) ===
        {"match_id": 7581, "match_title": "france_v_australia_2018", "label": "France 2-1 Australia", "stage": "Group Stage", "date": "2018-06-16", "teams": ["France", "Australia"]},
        {"match_id": 7545, "match_title": "france_v_peru", "label": "France 1-0 Peru", "stage": "Group Stage", "date": "2018-06-21", "teams": ["France", "Peru"]},
        {"match_id": 8650, "match_title": "france_v_argentina_2018", "label": "France 4-3 Argentina (R16)", "stage": "Round of 16", "date": "2018-06-30", "teams": ["France", "Argentina"]},
        {"match_id": 8656, "match_title": "uruguay_v_france", "label": "Uruguay 0-2 France (QF)", "stage": "Quarter-finals", "date": "2018-07-06", "teams": ["Uruguay", "France"]},
        {"match_id": 8652, "match_title": "france_v_belgium", "label": "France 1-0 Belgium (SF)", "stage": "Semi-finals", "date": "2018-07-10", "teams": ["France", "Belgium"]},
        {"match_id": 8658, "match_title": "france_v_croatia_2018", "label": "France 4-2 Croatia (Final)", "stage": "Final", "date": "2018-07-15", "teams": ["France", "Croatia"]},
        # === CROATIA ===
        {"match_id": 7569, "match_title": "croatia_v_nigeria", "label": "Croatia 2-0 Nigeria", "stage": "Group Stage", "date": "2018-06-16", "teams": ["Croatia", "Nigeria"]},
        {"match_id": 7549, "match_title": "argentina_v_croatia", "label": "Argentina 0-3 Croatia", "stage": "Group Stage", "date": "2018-06-21", "teams": ["Argentina", "Croatia"]},
        {"match_id": 8655, "match_title": "croatia_v_denmark", "label": "Croatia 1-1 Denmark (R16)", "stage": "Round of 16", "date": "2018-07-01", "teams": ["Croatia", "Denmark"]},
        {"match_id": 8653, "match_title": "russia_v_croatia", "label": "Russia 2-2 Croatia (QF)", "stage": "Quarter-finals", "date": "2018-07-07", "teams": ["Russia", "Croatia"]},
        {"match_id": 8657, "match_title": "croatia_v_england_2018", "label": "Croatia 2-1 England (SF)", "stage": "Semi-finals", "date": "2018-07-11", "teams": ["Croatia", "England"]},
        # === BELGIUM ===
        {"match_id": 7579, "match_title": "belgium_v_panama", "label": "Belgium 3-0 Panama", "stage": "Group Stage", "date": "2018-06-18", "teams": ["Belgium", "Panama"]},
        {"match_id": 7547, "match_title": "belgium_v_tunisia", "label": "Belgium 5-2 Tunisia", "stage": "Group Stage", "date": "2018-06-23", "teams": ["Belgium", "Tunisia"]},
        {"match_id": 8649, "match_title": "belgium_v_japan", "label": "Belgium 3-2 Japan (R16)", "stage": "Round of 16", "date": "2018-07-02", "teams": ["Belgium", "Japan"]},
        {"match_id": 8654, "match_title": "brazil_v_belgium", "label": "Brazil 1-2 Belgium (QF)", "stage": "Quarter-finals", "date": "2018-07-06", "teams": ["Brazil", "Belgium"]},
        # === ENGLAND ===
        {"match_id": 7577, "match_title": "tunisia_v_england", "label": "Tunisia 1-2 England", "stage": "Group Stage", "date": "2018-06-18", "teams": ["Tunisia", "England"]},
        {"match_id": 7543, "match_title": "england_v_panama", "label": "England 6-1 Panama", "stage": "Group Stage", "date": "2018-06-24", "teams": ["England", "Panama"]},
        {"match_id": 8648, "match_title": "colombia_v_england", "label": "Colombia 1-1 England (R16)", "stage": "Round of 16", "date": "2018-07-03", "teams": ["Colombia", "England"]},
        {"match_id": 8651, "match_title": "sweden_v_england", "label": "Sweden 0-2 England (QF)", "stage": "Quarter-finals", "date": "2018-07-07", "teams": ["Sweden", "England"]},
        # === BRAZIL ===
        {"match_id": 7575, "match_title": "brazil_v_switzerland", "label": "Brazil 1-1 Switzerland", "stage": "Group Stage", "date": "2018-06-17", "teams": ["Brazil", "Switzerland"]},
        {"match_id": 7541, "match_title": "brazil_v_costa_rica", "label": "Brazil 2-0 Costa Rica", "stage": "Group Stage", "date": "2018-06-22", "teams": ["Brazil", "Costa Rica"]},
        {"match_id": 8646, "match_title": "brazil_v_mexico", "label": "Brazil 2-0 Mexico (R16)", "stage": "Round of 16", "date": "2018-07-02", "teams": ["Brazil", "Mexico"]},
        # === ARGENTINA ===
        {"match_id": 7567, "match_title": "argentina_v_iceland", "label": "Argentina 1-1 Iceland", "stage": "Group Stage", "date": "2018-06-16", "teams": ["Argentina", "Iceland"]},
        {"match_id": 7529, "match_title": "nigeria_v_argentina", "label": "Nigeria 1-2 Argentina", "stage": "Group Stage", "date": "2018-06-26", "teams": ["Nigeria", "Argentina"]},
        # === GERMANY ===
        {"match_id": 7573, "match_title": "germany_v_mexico_2018", "label": "Germany 0-1 Mexico", "stage": "Group Stage", "date": "2018-06-17", "teams": ["Germany", "Mexico"]},
        {"match_id": 7539, "match_title": "germany_v_sweden", "label": "Germany 2-1 Sweden", "stage": "Group Stage", "date": "2018-06-23", "teams": ["Germany", "Sweden"]},
        {"match_id": 7527, "match_title": "south_korea_v_germany", "label": "South Korea 2-0 Germany", "stage": "Group Stage", "date": "2018-06-27", "teams": ["South Korea", "Germany"]},
        # === SPAIN ===
        {"match_id": 7565, "match_title": "portugal_v_spain_2018", "label": "Portugal 3-3 Spain", "stage": "Group Stage", "date": "2018-06-15", "teams": ["Portugal", "Spain"]},
        {"match_id": 8644, "match_title": "spain_v_russia", "label": "Spain 1-1 Russia (R16)", "stage": "Round of 16", "date": "2018-07-01", "teams": ["Spain", "Russia"]},
    ],
    
    # Copa America 2024 - Key matches
    "copa2024": [
        # === ARGENTINA (Winner) ===
        {"match_id": 3943043, "match_title": "argentina_v_canada_copa", "label": "Argentina 2-0 Canada", "stage": "Group Stage", "date": "2024-06-20", "teams": ["Argentina", "Canada"]},
        {"match_id": 3943049, "match_title": "chile_v_argentina", "label": "Chile 0-1 Argentina", "stage": "Group Stage", "date": "2024-06-25", "teams": ["Chile", "Argentina"]},
        {"match_id": 3943077, "match_title": "argentina_v_ecuador_copa", "label": "Argentina 1-1 Ecuador (QF)", "stage": "Quarter-finals", "date": "2024-07-04", "teams": ["Argentina", "Ecuador"]},
        {"match_id": 3943081, "match_title": "argentina_v_canada_sf", "label": "Argentina 2-0 Canada (SF)", "stage": "Semi-finals", "date": "2024-07-09", "teams": ["Argentina", "Canada"]},
        {"match_id": 3943085, "match_title": "argentina_v_colombia_final", "label": "Argentina 1-0 Colombia (Final)", "stage": "Final", "date": "2024-07-14", "teams": ["Argentina", "Colombia"]},
        # === COLOMBIA ===
        {"match_id": 3943045, "match_title": "colombia_v_paraguay", "label": "Colombia 2-1 Paraguay", "stage": "Group Stage", "date": "2024-06-24", "teams": ["Colombia", "Paraguay"]},
        {"match_id": 3943051, "match_title": "colombia_v_costa_rica", "label": "Colombia 3-0 Costa Rica", "stage": "Group Stage", "date": "2024-06-28", "teams": ["Colombia", "Costa Rica"]},
        {"match_id": 3943079, "match_title": "colombia_v_panama", "label": "Colombia 5-0 Panama (QF)", "stage": "Quarter-finals", "date": "2024-07-06", "teams": ["Colombia", "Panama"]},
        {"match_id": 3943083, "match_title": "uruguay_v_colombia", "label": "Uruguay 0-1 Colombia (SF)", "stage": "Semi-finals", "date": "2024-07-10", "teams": ["Uruguay", "Colombia"]},
        # === URUGUAY ===
        {"match_id": 3943047, "match_title": "uruguay_v_panama", "label": "Uruguay 3-1 Panama", "stage": "Group Stage", "date": "2024-06-23", "teams": ["Uruguay", "Panama"]},
        {"match_id": 3943053, "match_title": "uruguay_v_usa", "label": "Uruguay 1-0 USA", "stage": "Group Stage", "date": "2024-07-01", "teams": ["Uruguay", "United States"]},
        {"match_id": 3943075, "match_title": "uruguay_v_brazil_copa", "label": "Uruguay 0-0 Brazil (QF)", "stage": "Quarter-finals", "date": "2024-07-06", "teams": ["Uruguay", "Brazil"]},
        # === BRAZIL ===
        {"match_id": 3943044, "match_title": "brazil_v_costa_rica_copa", "label": "Brazil 0-0 Costa Rica", "stage": "Group Stage", "date": "2024-06-24", "teams": ["Brazil", "Costa Rica"]},
        {"match_id": 3943050, "match_title": "brazil_v_paraguay_copa", "label": "Brazil 4-1 Paraguay", "stage": "Group Stage", "date": "2024-06-28", "teams": ["Brazil", "Paraguay"]},
    ],
}

# Backwards compatibility - default to World Cup 2022
WORLD_CUP_MATCHES = COMPETITION_MATCHES["wc2022"]

# Get unique teams for a competition
def get_teams_for_competition(comp_id: str) -> list:
    matches = COMPETITION_MATCHES.get(comp_id, [])
    return sorted(set(team for m in matches for team in m.get("teams", [])))

# Get unique teams across all competitions (for backwards compatibility)
ALL_TEAMS = sorted(set(team for matches in COMPETITION_MATCHES.values() for m in matches for team in m.get("teams", [])))

# FIFA+ Base URL (manual scrubbing required - no timestamp parameters supported)
FIFA_PLUS_BASE_URL = "https://www.fifa.com/fifaplus/en/watch/7CPdFjceNZkadrQkHj85l4"

# Period Offsets: Translate StatsBomb match time to real elapsed match time
# These offsets account for the actual video timeline (stoppage time, delays, etc.)
# Period 1: First half starts at 0:00, Period 2: Second half starts after halftime, etc.
PERIOD_OFFSETS = {
    1: 0,      # First half: minute 0-45
    2: 2700,   # Second half: 45 min offset (45*60)
    3: 5400,   # ET first half: 90 min offset (90*60)
    4: 6300,   # ET second half: 105 min offset (105*60)
    5: 7200    # Penalties: 120 min offset (120*60)
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


def compute_advanced_analytics(player_events: list, team_name: str, home_team: str = "Argentina") -> dict:
    """
    Compute advanced metrics from player events.
    - Progressive passes: pass advances ball ≥15m toward opponent goal
    - Passes into final third: end_location x ≥ 80 (attacking right)
    - Passes into box: end_location in penalty area
    - Total xT: sum of xT delta from all passes/carries
    - Actions under pressure: count and success rate
    - Through balls: pass type indicates through ball
    - Key passes: through balls + passes into box
    """
    # StatsBomb: home team attacks toward x=120, away team toward x=0
    is_attacking_right = (team_name == home_team)

    def is_progressive_pass(event: dict) -> bool:
        loc = event.get("location")
        end = event.get("pass", {}).get("end_location")
        if not loc or not end:
            return False
        dx = end[0] - loc[0]
        return dx >= 15 if is_attacking_right else dx <= -15

    def is_pass_into_final_third(event: dict) -> bool:
        end = event.get("pass", {}).get("end_location")
        if not end:
            return False
        return end[0] >= 80 if is_attacking_right else end[0] <= 40

    def is_pass_into_box(event: dict) -> bool:
        end = event.get("pass", {}).get("end_location")
        if not end:
            return False
        if is_attacking_right:
            return end[0] >= 102 and 18 <= end[1] <= 62
        return end[0] <= 18 and 18 <= end[1] <= 62

    def is_through_ball(event: dict) -> bool:
        pt = event.get("pass", {}).get("type", {})
        name = (pt.get("name") or "") if isinstance(pt, dict) else str(pt)
        return "through" in name.lower()

    total_xt = 0.0
    progressive_passes = 0
    progressive_complete = 0
    passes_into_final_third = 0
    passes_into_box = 0
    through_balls = 0
    key_passes = 0
    actions_under_pressure = 0
    pressure_success = 0

    for event in player_events:
        loc = event.get("location")
        event_type = event.get("type", {}).get("name", "")
        under_pressure = event.get("under_pressure", False)

        if under_pressure:
            actions_under_pressure += 1
            success = False
            if event_type == "Pass":
                success = "outcome" not in event.get("pass", {})
            elif event_type == "Carry":
                success = "outcome" not in event.get("carry", {})
            elif event_type == "Dribble":
                outcome = event.get("dribble", {}).get("outcome", {}).get("name", "")
                success = outcome == "Complete"
            else:
                success = True
            if success:
                pressure_success += 1

        if event_type == "Pass" and loc:
            pass_data = event.get("pass", {})
            end_loc = pass_data.get("end_location")
            if end_loc:
                total_xt += calculate_xt_delta(loc, end_loc)
            complete = "outcome" not in pass_data
            if is_progressive_pass(event):
                progressive_passes += 1
                if complete:
                    progressive_complete += 1
            if is_pass_into_final_third(event):
                passes_into_final_third += 1
            if is_pass_into_box(event):
                passes_into_box += 1
            if is_through_ball(event):
                through_balls += 1
            if is_through_ball(event) or is_pass_into_box(event):
                key_passes += 1

        if event_type == "Carry" and loc:
            end_loc = event.get("carry", {}).get("end_location")
            if end_loc:
                total_xt += calculate_xt_delta(loc, end_loc)
                dx = end_loc[0] - loc[0]
                if (is_attacking_right and dx >= 15) or (not is_attacking_right and dx <= -15):
                    progressive_passes += 1
                    progressive_complete += 1

    pressure_pct = round(pressure_success / actions_under_pressure * 100) if actions_under_pressure > 0 else None
    prog_acc = round(progressive_complete / progressive_passes * 100) if progressive_passes > 0 else None

    return {
        "total_xt": round(total_xt, 3),
        "progressive_passes": progressive_passes,
        "progressive_pass_accuracy": f"{prog_acc}%" if prog_acc is not None else "N/A",
        "passes_into_final_third": passes_into_final_third,
        "passes_into_box": passes_into_box,
        "through_balls": through_balls,
        "key_passes": key_passes,
        "actions_under_pressure": actions_under_pressure,
        "pressure_success_pct": f"{pressure_pct}%" if pressure_pct is not None else "N/A",
    }


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
def get_pitch_pilot_url(minute: int, second: int, period: int) -> dict:
    """
    Calculate the display timestamp for FIFA+ manual video scrubbing.
    
    FIFA+ does not support URL timestamp parameters, so we return:
    - base_url: The FIFA+ match video URL
    - display_time_str: Human-readable timestamp (e.g., "35:42") for manual navigation
    
    Args:
        minute: StatsBomb event minute
        second: StatsBomb event second
        period: Match period (1=first half, 2=second half, 3=ET1, 4=ET2, 5=penalties)
    
    Returns:
        dict: {"base_url": str, "display_time_str": str}
    """
    # Calculate elapsed seconds within the current period
    if period == 1:
        period_elapsed = (minute * 60) + second
    elif period == 2:
        period_elapsed = ((minute - 45) * 60) + second
    elif period == 3:
        period_elapsed = ((minute - 90) * 60) + second
    elif period == 4:
        period_elapsed = ((minute - 105) * 60) + second
    else:
        period_elapsed = 0
    
    # Add period offset to get total elapsed match seconds
    period_offset = PERIOD_OFFSETS.get(period, 0)
    elapsed_match_seconds = period_elapsed + period_offset
    
    # Format as MM:SS display string
    display_minutes = elapsed_match_seconds // 60
    display_seconds = elapsed_match_seconds % 60
    display_time_str = f"{display_minutes}:{display_seconds:02d}"
    
    return {
        "base_url": FIFA_PLUS_BASE_URL,
        "display_time_str": display_time_str
    }


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


# --- PLAYER EVENT MATCHING ---
def _filter_player_events(events_list: list, player_id: Optional[int], player_name: str) -> list:
    """Filter events for a player. Handles ID/name matching with type coercion and fallbacks."""
    def event_player_matches(e, pid, pname):
        player = e.get("player") or {}
        if not player:
            return False
        eid = player.get("id")
        ename = (player.get("name") or "").strip()
        if pid is not None and eid is not None:
            try:
                if int(eid) == int(pid):
                    return True
            except (TypeError, ValueError):
                pass
        if pname and ename:
            if ename == pname or ename.lower() == pname.lower():
                return True
            if pname.lower() in ename.lower() or ename.lower() in pname.lower():
                return True
        return False

    if player_id is not None:
        result = [e for e in events_list if event_player_matches(e, player_id, player_name)]
        if not result and player_name:
            result = [e for e in events_list if event_player_matches(e, None, player_name)]
        return result
    return [e for e in events_list if event_player_matches(e, None, player_name)]


# --- MAIN PLAYER ANALYSIS FUNCTION ---
def get_player_data(
    match_events: dict,
    player_name: str,
    home_team: str = "Argentina",
    top_n: int = 5,
    player_id: Optional[int] = None
) -> tuple[dict, list, list]:
    """
    Analyze player events and return stats with top highlights AND areas for improvement.
    
    Args:
        match_events: Dictionary of match events from StatsBomb
        player_name: Name of player to analyze
        home_team: Home team name for win probability calculations
        top_n: Number of top moments to return for each category
        player_id: Optional player ID for reliable matching (preferred over name)
    
    Returns:
        tuple: (player_stats, top_highlights, areas_for_improvement)
    """
    # Flatten events dict to list and sort by timestamp
    events_list = list(match_events.values())
    events_list.sort(key=lambda e: (e.get("minute", 0), e.get("second", 0)))
    
    # Initialize game state tracker
    game_state = GameStateTracker(home_team)
    
    player_events = _filter_player_events(events_list, player_id, player_name)
    
    if not player_events:
        # Player in squad but did not play (no events)
        empty_stats = {
            "name": player_name,
            "total_highlight_score": 0.0,
            "total_value_added": 0.0,
            "total_actions": 0,
            "positive_contributions": 0,
            "negative_contributions": 0,
            "highlights_count": 0,
            "lowlights_count": 0,
            "pass_accuracy": "N/A",
            "shots": 0,
            "goals": 0,
            "total_xt": 0.0,
            "progressive_passes": 0,
            "progressive_pass_accuracy": "N/A",
            "passes_into_final_third": 0,
            "passes_into_box": 0,
            "through_balls": 0,
            "key_passes": 0,
            "actions_under_pressure": 0,
            "pressure_success_pct": "N/A",
        }
        return {"error": f"Player '{player_name}' not found", "player_did_not_play": True, **empty_stats}, [], []
    
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
        video_info = get_pitch_pilot_url(
            event["minute"], 
            event["second"], 
            event["period"]
        )
        mn, sc = int(event.get("minute", 0)), int(event.get("second", 0))
        moment_data = {
            "time_display": f"{mn}:{sc:02d}",
            "event_type": event["type"]["name"],
            "description": description,
            "highlight_score": round(highlight_score, 3),
            "value_added": round(value_added, 3),
            "xt_delta": round(xt_delta, 4),
            "video_url": video_info["base_url"],
            "video_time": video_info["display_time_str"],
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
    player_team = player_events[0].get("team", {}).get("name", home_team) if player_events else home_team

    # Advanced analytics
    advanced = compute_advanced_analytics(player_events, player_team, home_team)

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
        },
        **advanced,
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
            video_info = get_pitch_pilot_url(
                event["minute"],
                event["second"],
                event["period"]
            )
            all_moments.append({
                "player": player_name,
                "team": event.get("team", {}).get("name", ""),
                "time_display": f"{event['minute']}:{event['second']:02d}",
                "event_type": event["type"]["name"],
                "description": description,
                "highlight_score": round(highlight_score, 3),
                "video_url": video_info["base_url"],
                "video_time": video_info["display_time_str"]
            })
    
    return sorted(all_moments, key=lambda x: x["highlight_score"], reverse=True)[:top_n]


def get_match_summary(
    match_events: dict,
    lineups: dict,
    match_label: str,
    home_team: Optional[str] = None,
    top_players_n: int = 5,
    improvement_players_n: int = 5,
) -> dict:
    """
    Generate full match summary: best players, players needing improvement, team summary, team improvements.
    """
    if home_team is None and lineups:
        home_team = next(iter(lineups.keys()), "Argentina")

    events_list = list(match_events.values())
    # Get unique players who have events
    player_ids_seen = set()
    players_with_events = []
    for e in events_list:
        p = e.get("player")
        if not p:
            continue
        pid = p.get("id")
        pname = (p.get("name") or "").strip()
        if not pname or pid in player_ids_seen:
            continue
        player_ids_seen.add(pid)
        players_with_events.append((pid, pname))

    # Analyze each player
    all_player_stats = []
    all_lowlights_by_player = []
    all_highlights_by_player = []

    for pid, pname in players_with_events:
        stats, highlights, lowlights = get_player_data(
            match_events, pname, home_team=home_team or "Argentina", top_n=3, player_id=pid
        )
        if "error" in stats:
            continue
        team = next(
            (t for t, plist in lineups.items()
             for p in plist if p.get("player_id") == pid or p.get("player_name") == pname),
            ""
        )
        all_player_stats.append({
            "player_name": stats["name"],
            "player_id": pid,
            "team": team,
            "stats": stats,
            "top_highlights": highlights,
            "areas_for_improvement": lowlights,
        })
        for l in lowlights:
            all_lowlights_by_player.append({"player": pname, "description": l.get("description", ""), "event_type": l.get("event_type", "")})
        for h in highlights:
            all_highlights_by_player.append({"player": pname, "description": h.get("description", "")})

    # Sort by net impact: best first, then worst
    all_player_stats.sort(key=lambda x: x["stats"]["total_highlight_score"], reverse=True)
    best_players = all_player_stats[:top_players_n]
    # Players needing improvement: lowest net score first, then most negative contributions
    improvement_candidates = sorted(
        all_player_stats,
        key=lambda x: (x["stats"]["total_highlight_score"], -x["stats"]["negative_contributions"])
    )[:improvement_players_n]

    # Build match summary text
    total_events = len([e for e in events_list if e.get("player")])
    total_goals = len([e for e in events_list
                       if e.get("type", {}).get("name") == "Shot"
                       and e.get("shot", {}).get("outcome", {}).get("name") == "Goal"])
    teams = list(lineups.keys()) if lineups else []
    match_summary_text = (
        f"{match_label} featured {len(players_with_events)} players with {total_events} recorded actions. "
    )
    if best_players:
        top_names = ", ".join(s["stats"]["name"].split()[-1] for s in best_players[:3])
        match_summary_text += (
            f"Standout performers included {top_names}. "
        )
    if improvement_candidates and improvement_candidates[0]["stats"]["total_highlight_score"] < 0:
        imp_names = ", ".join(s["stats"]["name"].split()[-1] for s in improvement_candidates[:3])
        match_summary_text += (
            f"Players who could improve: {imp_names}. "
        )
    match_summary_text += (
        f"Total goals in the match: {total_goals}. "
    )

    # Team-wide improvements (from aggregate lowlight themes)
    event_types_in_lowlights = {}
    for item in all_lowlights_by_player:
        et = item.get("event_type") or "Other"
        event_types_in_lowlights[et] = event_types_in_lowlights.get(et, 0) + 1
    common_issues = sorted(event_types_in_lowlights.items(), key=lambda x: -x[1])[:5]
    team_improvements = []
    type_to_advice = {
        "Pass": "Improve pass selection and weight under pressure",
        "Dribble": "Work on ball retention in 1v1 situations",
        "Dispossessed": "Enhance body positioning and shielding",
        "Bad Touch": "Focus on first-touch control in tight spaces",
        "Shot": "Improve shot selection and composure in front of goal",
        "Foul Committed": "Reduce unnecessary fouls through better positioning",
        "Block": "Anticipate blocking angles earlier",
    }
    for et, _ in common_issues:
        advice = type_to_advice.get(et)
        if advice:
            team_improvements.append(advice)
    if not team_improvements and all_lowlights_by_player:
        team_improvements.append("Reduce turnovers and improve decision-making under pressure")
    if not team_improvements:
        team_improvements.append("Maintain current standards and focus on consistency")

    return {
        "match_title": match_label,
        "match_summary": match_summary_text,
        "best_players": [
            {
                "player_name": p["player_name"],
                "player_id": p["player_id"],
                "team": p["team"],
                "net_impact": p["stats"]["total_highlight_score"],
                "goals": p["stats"]["goals"],
                "highlights_count": p["stats"]["highlights_count"],
            }
            for p in best_players
        ],
        "players_needing_improvement": [
            {
                "player_name": p["player_name"],
                "player_id": p["player_id"],
                "team": p["team"],
                "net_impact": p["stats"]["total_highlight_score"],
                "lowlights_count": p["stats"]["lowlights_count"],
                "top_issue": p["areas_for_improvement"][0]["description"] if p["areas_for_improvement"] else "General consistency",
            }
            for p in improvement_candidates
        ],
        "team_improvements": team_improvements,
        "total_goals": total_goals,
        "players_analyzed": len(all_player_stats),
    }


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
- **Video:** {best_highlight['video_url']} (scrub to {best_highlight['video_time']})
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
- **Video:** {worst_lowlight['video_url']} (scrub to {worst_lowlight['video_time']})
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


def generate_player_summary(
    player_name: str,
    stats: dict,
    top_highlights: list,
    areas_for_improvement: list
) -> dict:
    """
    Generate player summary with structured lists: what_went_well, what_to_work_on, even_better_if.
    Returns dict with 'summary_text' and structured lists for frontend display.
    """
    short_name = stats.get("name", player_name)
    if " " in short_name:
        short_name = short_name.split()[-1]

    total = stats.get("total_actions", 0)
    net = stats.get("total_highlight_score", 0)
    pos = stats.get("positive_contributions", 0)
    neg = stats.get("negative_contributions", 0)
    goals = stats.get("goals", 0)
    shots = stats.get("shots", 0)
    pass_acc = stats.get("pass_accuracy", "N/A")
    n_high = stats.get("highlights_count", 0)
    n_low = stats.get("lowlights_count", 0)

    what_went_well = []
    what_to_work_on = []
    even_better_if = []

    if total == 0:
        return {
            "summary_text": (
                f"{short_name} was named in the squad but did not feature in this match. "
                "No on-pitch data is available for analysis."
            ),
            "what_went_well": [],
            "what_to_work_on": [],
            "even_better_if": [],
        }

    # What went well - from highlights and positive stats
    if goals > 0:
        what_went_well.append(f"Scored {goals} goal{'s' if goals > 1 else ''}")
    if pass_acc and pass_acc != "N/A":
        pct = int(pass_acc.replace("%", "")) if "%" in str(pass_acc) else 0
        if pct >= 85:
            what_went_well.append(f"Strong pass accuracy ({pass_acc})")
        elif pct >= 75:
            what_went_well.append(f"Solid passing ({pass_acc})")
    if pos > neg and total >= 10:
        what_went_well.append(f"More positive than negative actions ({pos} vs {neg})")
    if net > 0.5:
        what_went_well.append("Positive net impact on the match")
    total_xt = stats.get("total_xt", 0) or 0
    if total_xt > 0.05:
        what_went_well.append(f"Generated {total_xt:.2f} xT through ball progression")
    prog = stats.get("progressive_passes", 0) or 0
    if prog >= 5:
        what_went_well.append(f"{prog} progressive passes advancing the ball")
    key_p = stats.get("key_passes", 0) or 0
    if key_p >= 2:
        what_went_well.append(f"{key_p} key passes creating danger")
    pressure_pct = stats.get("pressure_success_pct", "N/A")
    if pressure_pct != "N/A" and pressure_pct:
        pct_val = int(str(pressure_pct).replace("%", "")) if "%" in str(pressure_pct) else 0
        if pct_val >= 75 and (stats.get("actions_under_pressure") or 0) >= 3:
            what_went_well.append(f"Composed under pressure ({pressure_pct})")
    for i, h in enumerate(top_highlights[:3]):
        what_went_well.append(h.get("description", f"Key contribution at {h.get('time_display', '')}"))
    if not what_went_well:
        what_went_well.append(f"Completed {total} actions in the match")

    # What to work on - from lowlights
    for i, l in enumerate(areas_for_improvement[:4]):
        desc = l.get("description", "")
        if desc and desc not in what_to_work_on:
            what_to_work_on.append(desc)
    if neg > pos and total >= 10 and not what_to_work_on:
        what_to_work_on.append("Reduce negative contributions and improve decision-making under pressure")
    if pass_acc and pass_acc != "N/A":
        pct = int(pass_acc.replace("%", "")) if "%" in str(pass_acc) else 0
        if pct < 70 and "passing" not in " ".join(what_to_work_on).lower():
            what_to_work_on.append(f"Improve pass accuracy (current: {pass_acc})")
    prog_acc = stats.get("progressive_pass_accuracy", "N/A")
    if prog_acc != "N/A" and "%" in str(prog_acc):
        pa = int(str(prog_acc).replace("%", ""))
        if pa < 70 and (stats.get("progressive_passes") or 0) >= 3:
            what_to_work_on.append("Improve accuracy of progressive passes")
    if (stats.get("actions_under_pressure") or 0) >= 5:
        pp = stats.get("pressure_success_pct", "N/A")
        if pp != "N/A":
            pv = int(str(pp).replace("%", "")) if "%" in str(pp) else 100
            if pv < 60:
                what_to_work_on.append("Improve decision-making when under pressure")
    if not what_to_work_on:
        what_to_work_on.append("Maintain consistency and build on strengths")

    # Even better if - growth suggestions
    if goals == 0 and shots > 0:
        even_better_if.append("Convert more chances — work on finishing in training")
    if net > 0.3 and n_high >= 2:
        even_better_if.append("Keep producing standout moments at key times")
    if neg > 0:
        even_better_if.append("Cut out avoidable turnovers in dangerous areas")
    if n_low > 2:
        even_better_if.append("Improve composure when under pressure")
    if not even_better_if:
        even_better_if.append("Continue developing and stay consistent")

    # Summary text
    parts = []
    if net > 0.5:
        parts.append(f"{short_name} had a positive impact overall")
    elif net < -0.5:
        parts.append(f"{short_name} struggled to influence the game positively")
    else:
        parts.append(f"{short_name} had a mixed performance")
    parts.append(f"with {total} total actions ({pos} positive, {neg} negative).")
    if goals > 0:
        parts.append(f"Scored {goals} goal{'s' if goals > 1 else ''} from {shots} shot{'s' if shots != 1 else ''}.")
    if pass_acc != "N/A":
        parts.append(f"Pass accuracy: {pass_acc}.")
    summary_text = " ".join(parts)

    return {
        "summary_text": summary_text,
        "what_went_well": what_went_well[:6],
        "what_to_work_on": what_to_work_on[:5],
        "even_better_if": even_better_if[:4],
    }


def generate_player_summary_text(
    player_name: str,
    stats: dict,
    top_highlights: list,
    areas_for_improvement: list
) -> str:
    """Legacy: return just the summary text. Use generate_player_summary for structured data."""
    return generate_player_summary(player_name, stats, top_highlights, areas_for_improvement)["summary_text"]


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
                "video_url": h["video_url"],
                "video_time": h["video_time"]
            }
            for h in top_highlights
        ],
        "areas_for_improvement": [
            {
                "time": l["time_display"],
                "description": l["description"],
                "score": l["highlight_score"],
                "video_url": l["video_url"],
                "video_time": l["video_time"]
            }
            for l in areas_for_improvement
        ],
        "claude_prompt": generate_claude_prompt(
            player_name, stats, top_highlights, areas_for_improvement
        )
    }


# --- PITCH VISUALIZATION DATA EXTRACTION ---
def extract_pitch_viz_data(event: dict) -> Optional[dict]:
    """
    Extract pitch visualization data from a StatsBomb event.
    Returns coordinates and metadata for drawing on a pitch map.
    """
    event_type = event.get("type", {}).get("name", "")
    location = event.get("location")
    
    if not location:
        return None
    
    player_name = event.get("player", {}).get("name", "Unknown")
    # Get short name (last name + first initial)
    name_parts = player_name.split()
    short_name = f"{name_parts[-1][:10]}" if name_parts else "Unknown"
    
    team_name = event.get("team", {}).get("name", "")
    team_color = "#3b82f6" if team_name == "Argentina" else "#ef4444"  # Blue for Argentina, Red for France
    
    viz_data = {
        "player_name": short_name,
        "team_color": team_color,
    }
    
    if event_type == "Pass":
        pass_data = event.get("pass", {})
        end_location = pass_data.get("end_location")
        if end_location:
            # In StatsBomb, missing 'outcome' means pass was successful
            outcome = "incomplete" if "outcome" in pass_data else "complete"
            viz_data.update({
                "action_type": "pass",
                "start_coords": [round(location[0], 1), round(location[1], 1)],
                "end_coords": [round(end_location[0], 1), round(end_location[1], 1)],
                "outcome": outcome,
            })
            return viz_data
    
    elif event_type == "Carry":
        carry_data = event.get("carry", {})
        end_location = carry_data.get("end_location")
        if end_location:
            viz_data.update({
                "action_type": "carry",
                "start_coords": [round(location[0], 1), round(location[1], 1)],
                "end_coords": [round(end_location[0], 1), round(end_location[1], 1)],
                "outcome": "complete",
            })
            return viz_data
    
    elif event_type == "Dribble":
        dribble_outcome = event.get("dribble", {}).get("outcome", {}).get("name", "")
        outcome = "complete" if dribble_outcome == "Complete" else "incomplete"
        viz_data.update({
            "action_type": "dribble",
            "coords": [round(location[0], 1), round(location[1], 1)],
            "outcome": outcome,
        })
        return viz_data
    
    elif event_type == "Shot":
        shot_data = event.get("shot", {})
        shot_outcome = shot_data.get("outcome", {}).get("name", "")
        
        if shot_outcome == "Goal":
            outcome = "goal"
        elif shot_outcome == "Saved":
            outcome = "saved"
        elif shot_outcome == "Blocked":
            outcome = "blocked"
        else:
            outcome = "missed"
        
        viz_data.update({
            "action_type": "shot",
            "coords": [round(location[0], 1), round(location[1], 1)],
            "outcome": outcome,
        })
        return viz_data
    
    elif event_type in ["Interception", "Tackle", "Block", "Clearance", "Ball Recovery"]:
        key = event_type.lower().replace(" ", "_")
        sub = event.get(key, {}) or {}
        outcome_name = (sub.get("outcome") or {}).get("name", "") if isinstance(sub.get("outcome"), dict) else ""
        outcome = "won" if outcome_name != "Lost" else "lost"
        viz_data.update({
            "action_type": "defense",
            "coords": [round(location[0], 1), round(location[1], 1)],
            "outcome": outcome,
        })
        return viz_data

    # Fallback: any event with location (Dispossessed, Bad Touch, Ball Receipt, etc.)
    viz_data.update({
        "action_type": "other",
        "coords": [round(location[0], 1), round(location[1], 1)],
        "outcome": "complete",
    })
    return viz_data


def get_player_analysis_with_viz(
    match_events: dict,
    player_name: str,
    home_team: str = "Argentina",
    top_n: int = 5,
    player_id: Optional[int] = None
) -> dict:
    """
    Get player analysis with pitch visualization data included.
    Returns a complete response for the frontend.
    Handles "player did not play" by returning a friendly structure instead of error.
    """
    stats, highlights, lowlights = get_player_data(
        match_events, player_name, home_team, top_n, player_id
    )
    
    if "error" in stats:
        if stats.get("player_did_not_play"):
            summ = generate_player_summary(player_name, stats, [], [])
            return {
                "player_name": player_name,
                "player_did_not_play": True,
                "stats": {k: v for k, v in stats.items() if k not in ("error", "player_did_not_play")},
                "top_highlights": [],
                "areas_for_improvement": [],
                "all_positions": [],
                "player_summary": summ["summary_text"],
                "what_went_well": [],
                "what_to_work_on": [],
                "even_better_if": [],
            }
        return {"error": stats["error"]}
    
    # Get player events for pitch viz (same matching as get_player_data)
    events_list = list(match_events.values())
    player_events = _filter_player_events(events_list, player_id, player_name)
    
    # Add pitch_viz_data to highlights
    for highlight in highlights:
        for event in player_events:
            mn, sc = int(event.get("minute", 0)), int(event.get("second", 0))
            event_time = f"{mn}:{sc:02d}"
            if event_time == highlight["time_display"]:
                viz_data = extract_pitch_viz_data(event)
                if viz_data:
                    highlight["pitch_viz_data"] = viz_data
                break
    
    # Add pitch_viz_data to lowlights
    for lowlight in lowlights:
        for event in player_events:
            mn, sc = int(event.get("minute", 0)), int(event.get("second", 0))
            event_time = f"{mn}:{sc:02d}"
            if event_time == lowlight["time_display"]:
                viz_data = extract_pitch_viz_data(event)
                if viz_data:
                    lowlight["pitch_viz_data"] = viz_data
                break
    
    # Generate all action positions for heat map
    all_positions = []
    for event in player_events:
        location = event.get("location")
        if location:
            all_positions.append({
                "x": round(location[0], 1),
                "y": round(location[1], 1),
                "type": event.get("type", {}).get("name", ""),
            })
    
    summ = generate_player_summary(stats["name"], stats, highlights, lowlights)
    return {
        "player_name": stats["name"],
        "stats": stats,
        "top_highlights": highlights,
        "areas_for_improvement": lowlights,
        "all_positions": all_positions,  # For heat map
        "player_summary": summ["summary_text"],
        "what_went_well": summ["what_went_well"],
        "what_to_work_on": summ["what_to_work_on"],
        "even_better_if": summ["even_better_if"],
    }


# --- FASTAPI APPLICATION ---
app = FastAPI(
    title="CoachOS API",
    description="ML-Driven Player Performance Analysis",
    version="1.0.0"
)

# CORS middleware for frontend - allow common dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:24678",
        "http://127.0.0.1:24678",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Cache match data by match_id
_match_cache: Dict[int, tuple] = {}
_match_summary_cache: Dict[int, dict] = {}


def _get_match_config(match_id: int) -> Optional[dict]:
    """Get match config from WORLD_CUP_MATCHES by match_id."""
    for m in WORLD_CUP_MATCHES:
        if m["match_id"] == match_id:
            return m
    return None


def get_cached_match_data(match_id: Optional[int] = None):
    """Get cached match data for the given match_id. Defaults to first World Cup match."""
    if match_id is None:
        match_id = WORLD_CUP_MATCHES[0]["match_id"]
    config = _get_match_config(match_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    if match_id not in _match_cache:
        _match_cache[match_id] = load_match_data(config["match_id"], config["match_title"])
    return _match_cache[match_id][0], _match_cache[match_id][1], config


# --- API RESPONSE MODELS ---
class PlayerInfo(BaseModel):
    player_id: int
    player_name: str
    player_nickname: Optional[str] = None
    jersey_number: int
    team: str
    position: Optional[str] = None


class PlayersResponse(BaseModel):
    match_id: int
    match_title: str
    teams: List[str]
    players: List[PlayerInfo]


# --- API ENDPOINTS ---
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "CoachOS API",
        "version": "1.0.0",
        "matches_available": len(WORLD_CUP_MATCHES)
    }


# Position ID to pitch coordinates mapping (StatsBomb position IDs)
# Coordinates are for team attacking left-to-right (x: 0-120, y: 0-80)
POSITION_COORDS = {
    1: (6, 40),      # Goalkeeper
    2: (25, 8),      # Right Back
    3: (18, 24),     # Right Center Back
    4: (18, 40),     # Center Back
    5: (18, 56),     # Left Center Back
    6: (25, 72),     # Left Back
    7: (35, 8),      # Right Wing Back
    8: (35, 72),     # Left Wing Back
    9: (40, 24),     # Right Defensive Midfield
    10: (40, 40),    # Center Defensive Midfield
    11: (40, 56),    # Left Defensive Midfield
    12: (55, 16),    # Right Midfield
    13: (55, 32),    # Right Center Midfield
    14: (55, 40),    # Center Midfield
    15: (55, 48),    # Left Center Midfield
    16: (55, 64),    # Left Midfield
    17: (70, 12),    # Right Wing
    18: (70, 28),    # Right Attacking Midfield
    19: (70, 40),    # Center Attacking Midfield
    20: (70, 52),    # Left Attacking Midfield
    21: (70, 68),    # Left Wing
    22: (85, 28),    # Right Center Forward
    23: (85, 40),    # Center Forward / Striker
    24: (85, 52),    # Left Center Forward
    25: (90, 40),    # Secondary Striker
}


def get_formation_positions(events: dict, team_name: str) -> list:
    """
    Extract starting formation positions for a team from Starting XI event.
    Returns list of {player_name, short_name, jersey_number, position_name, x, y}.
    """
    # Find Starting XI event for the team
    for event in events.values():
        if event.get("type", {}).get("name") == "Starting XI" and event.get("team", {}).get("name") == team_name:
            tactics = event.get("tactics", {})
            lineup = tactics.get("lineup", [])
            formation_str = str(tactics.get("formation", ""))
            
            positions = []
            for player_data in lineup:
                player = player_data.get("player", {})
                position = player_data.get("position", {})
                position_id = position.get("id", 23)  # Default to striker
                position_name = position.get("name", "Unknown")
                
                # Get coordinates from mapping
                coords = POSITION_COORDS.get(position_id, (60, 40))
                
                # Get short name (last name or first 10 chars)
                full_name = player.get("name", "Unknown")
                parts = full_name.split()
                short_name = parts[-1] if len(parts) > 1 else full_name[:10]
                
                positions.append({
                    "player_id": player.get("id"),
                    "player_name": full_name,
                    "short_name": short_name,
                    "jersey_number": player_data.get("jersey_number", 0),
                    "position_id": position_id,
                    "position_name": position_name,
                    "x": coords[0],
                    "y": coords[1],
                })
            
            return positions
    
    return []


@app.get("/api/formation")
async def get_formation(match_id: int = None, team: str = None):
    """Get starting formation positions for a team in a match."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        
        teams = list(lineups.keys()) if lineups else []
        if not team and teams:
            team = teams[0]
        
        formation = get_formation_positions(events, team)
        
        # Get formation number from Starting XI
        formation_num = None
        for event in events.values():
            if event.get("type", {}).get("name") == "Starting XI" and event.get("team", {}).get("name") == team:
                formation_num = event.get("tactics", {}).get("formation")
                break
        
        return {
            "match_id": config["match_id"],
            "team": team,
            "formation": formation_num,
            "players": formation,
            "teams": teams,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/team/stats")
async def get_team_stats(match_id: int = None, team: str = None):
    """Get aggregated team statistics from a match."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        
        teams = list(lineups.keys()) if lineups else []
        if not team and teams:
            team = teams[0]
        
        events_list = list(events.values())
        team_events = [e for e in events_list if e.get("team", {}).get("name") == team]
        
        # Basic counts
        passes = [e for e in team_events if e.get("type", {}).get("name") == "Pass"]
        complete_passes = [p for p in passes if "outcome" not in p.get("pass", {})]
        shots = [e for e in team_events if e.get("type", {}).get("name") == "Shot"]
        goals = [s for s in shots if s.get("shot", {}).get("outcome", {}).get("name") == "Goal"]
        
        # Advanced: xT, progressive passes, etc.
        total_xt = 0.0
        progressive_passes = 0
        passes_into_box = 0
        key_passes = 0
        
        for event in team_events:
            loc = event.get("location")
            event_type = event.get("type", {}).get("name", "")
            
            if event_type == "Pass" and loc:
                pass_data = event.get("pass", {})
                end_loc = pass_data.get("end_location")
                if end_loc:
                    total_xt += calculate_xt_delta(loc, end_loc)
                    dx = end_loc[0] - loc[0]
                    if dx >= 15:
                        progressive_passes += 1
                    if end_loc[0] >= 102 and 18 <= end_loc[1] <= 62:
                        passes_into_box += 1
                        key_passes += 1
                    pt = pass_data.get("type", {})
                    if isinstance(pt, dict) and "through" in (pt.get("name") or "").lower():
                        key_passes += 1
            
            if event_type == "Carry" and loc:
                end_loc = event.get("carry", {}).get("end_location")
                if end_loc:
                    total_xt += calculate_xt_delta(loc, end_loc)
        
        # Defensive stats
        tackles = len([e for e in team_events if e.get("type", {}).get("name") == "Duel" and e.get("duel", {}).get("type", {}).get("name") == "Tackle"])
        interceptions = len([e for e in team_events if e.get("type", {}).get("name") == "Interception"])
        clearances = len([e for e in team_events if e.get("type", {}).get("name") == "Clearance"])
        blocks = len([e for e in team_events if e.get("type", {}).get("name") == "Block"])
        
        # Possession (approximate: count team events vs total)
        total_events = len([e for e in events_list if e.get("type", {}).get("name") in ["Pass", "Carry", "Dribble", "Shot"]])
        team_possession_events = len([e for e in team_events if e.get("type", {}).get("name") in ["Pass", "Carry", "Dribble", "Shot"]])
        possession_pct = round(team_possession_events / total_events * 100) if total_events > 0 else 50
        
        pass_accuracy = round(len(complete_passes) / len(passes) * 100) if passes else 0
        
        return {
            "match_id": config["match_id"],
            "team": team,
            "teams": teams,
            "stats": {
                "total_passes": len(passes),
                "complete_passes": len(complete_passes),
                "pass_accuracy": f"{pass_accuracy}%",
                "shots": len(shots),
                "shots_on_target": len([s for s in shots if s.get("shot", {}).get("outcome", {}).get("name") in ["Goal", "Saved"]]),
                "goals": len(goals),
                "total_xt": round(total_xt, 2),
                "progressive_passes": progressive_passes,
                "passes_into_box": passes_into_box,
                "key_passes": key_passes,
                "tackles": tackles,
                "interceptions": interceptions,
                "clearances": clearances,
                "blocks": blocks,
                "possession_pct": f"{possession_pct}%",
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/matches")
async def get_matches(include_uncached: bool = False):
    """Get list of available World Cup 2022 matches. By default only returns cached matches."""
    from ultils.match_loader import DATA_DIR
    
    matches = []
    for m in WORLD_CUP_MATCHES:
        match_id = m["match_id"]
        match_title = m["match_title"]
        
        # Check if cached
        events_file = os.path.join(DATA_DIR, f"match_{match_title}_events_{match_id}.json")
        lineups_file = os.path.join(DATA_DIR, f"match_{match_title}_lineups_{match_id}.json")
        is_cached = os.path.exists(events_file) and os.path.exists(lineups_file)
        
        # Skip uncached matches unless explicitly requested
        if not include_uncached and not is_cached:
            continue
        
        matches.append({
            "match_id": m["match_id"], 
            "label": m["label"], 
            "stage": m["stage"],
            "date": m.get("date"),
            "teams": m.get("teams", []),
            "is_cached": is_cached
        })
    
    return {"matches": matches}


# ============================================
# DATA MANAGEMENT ENDPOINTS
# ============================================

@app.get("/api/data/competitions")
async def get_competitions():
    """Get list of available competitions."""
    return {
        "competitions": [
            {
                "id": comp["id"],
                "name": comp["name"],
                "short_name": comp["short_name"],
                "year": comp["year"],
                "country": comp["country"],
                "match_count": len(COMPETITION_MATCHES.get(comp["id"], []))
            }
            for comp in COMPETITIONS.values()
        ],
        "default": DEFAULT_COMPETITION
    }


@app.get("/api/data/teams")
async def get_teams(competition: str = None):
    """Get list of teams available in a competition."""
    if competition and competition in COMPETITION_MATCHES:
        teams = get_teams_for_competition(competition)
    else:
        teams = ALL_TEAMS
    return {"teams": teams, "competition": competition}


@app.get("/api/data/status")
async def get_data_status(competition: str = None, team: str = None):
    """Get status of cached match data for a competition."""
    from ultils.match_loader import DATA_DIR
    
    # Default to wc2022 if no competition specified
    comp_id = competition if competition and competition in COMPETITION_MATCHES else DEFAULT_COMPETITION
    matches = COMPETITION_MATCHES.get(comp_id, [])
    comp_info = COMPETITIONS.get(comp_id, {})
    
    statuses = []
    for m in matches:
        # Filter by team if specified
        if team and team not in m.get("teams", []):
            continue
            
        match_id = m["match_id"]
        match_title = m["match_title"]
        
        events_file = os.path.join(DATA_DIR, f"match_{match_title}_events_{match_id}.json")
        lineups_file = os.path.join(DATA_DIR, f"match_{match_title}_lineups_{match_id}.json")
        
        has_events = os.path.exists(events_file)
        has_lineups = os.path.exists(lineups_file)
        
        # Get file sizes if they exist
        events_size = os.path.getsize(events_file) if has_events else 0
        lineups_size = os.path.getsize(lineups_file) if has_lineups else 0
        
        statuses.append({
            "match_id": match_id,
            "match_title": match_title,
            "label": m["label"],
            "stage": m["stage"],
            "date": m.get("date"),
            "teams": m.get("teams", []),
            "has_events": has_events,
            "has_lineups": has_lineups,
            "is_complete": has_events and has_lineups,
            "events_size_kb": round(events_size / 1024, 1),
            "lineups_size_kb": round(lineups_size / 1024, 1),
            "total_size_kb": round((events_size + lineups_size) / 1024, 1)
        })
    
    total_cached = sum(1 for s in statuses if s["is_complete"])
    
    return {
        "competition": comp_id,
        "competition_name": comp_info.get("name", ""),
        "total_matches": len(statuses),
        "cached_matches": total_cached,
        "missing_matches": len(statuses) - total_cached,
        "statsbomb_available": HAS_STATSBOMB,
        "all_teams": get_teams_for_competition(comp_id),
        "matches": statuses
    }


@app.post("/api/data/fetch/{match_id}")
async def fetch_match_data(match_id: int, competition: str = None):
    """Fetch match data from StatsBomb and cache it locally."""
    if not HAS_STATSBOMB:
        raise HTTPException(
            status_code=503, 
            detail="statsbombpy not installed. Install with: pip install statsbombpy"
        )
    
    # Find match config across all competitions or specific one
    match_config = None
    if competition and competition in COMPETITION_MATCHES:
        match_config = next((m for m in COMPETITION_MATCHES[competition] if m["match_id"] == match_id), None)
    else:
        # Search all competitions
        for matches in COMPETITION_MATCHES.values():
            match_config = next((m for m in matches if m["match_id"] == match_id), None)
            if match_config:
                break
    
    if not match_config:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not in configured matches")
    
    try:
        from ultils.match_loader import get_match_events, get_match_lineups
        
        # This will fetch from StatsBomb if not cached
        events = get_match_events(match_id, match_config["match_title"])
        lineups = get_match_lineups(match_id, match_config["match_title"])
        
        # Clear any cached data for this match
        if match_id in _match_cache:
            del _match_cache[match_id]
        if match_id in _match_summary_cache:
            del _match_summary_cache[match_id]
        
        event_count = len(events) if isinstance(events, list) else len(events.get("events", []))
        team_count = len(lineups) if isinstance(lineups, dict) else 0
        
        return {
            "success": True,
            "match_id": match_id,
            "label": match_config["label"],
            "events_loaded": event_count,
            "teams_loaded": list(lineups.keys()) if isinstance(lineups, dict) else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/data/delete/{match_id}")
async def delete_match_data(match_id: int, competition: str = None):
    """Delete cached match data."""
    from ultils.match_loader import DATA_DIR
    
    # Find match config across all competitions
    match_config = None
    if competition and competition in COMPETITION_MATCHES:
        match_config = next((m for m in COMPETITION_MATCHES[competition] if m["match_id"] == match_id), None)
    else:
        for matches in COMPETITION_MATCHES.values():
            match_config = next((m for m in matches if m["match_id"] == match_id), None)
            if match_config:
                break
    
    if not match_config:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not in configured matches")
    
    match_title = match_config["match_title"]
    events_file = os.path.join(DATA_DIR, f"match_{match_title}_events_{match_id}.json")
    lineups_file = os.path.join(DATA_DIR, f"match_{match_title}_lineups_{match_id}.json")
    
    deleted_files = []
    
    try:
        if os.path.exists(events_file):
            os.remove(events_file)
            deleted_files.append("events")
        
        if os.path.exists(lineups_file):
            os.remove(lineups_file)
            deleted_files.append("lineups")
        
        # Clear cache
        if match_id in _match_cache:
            del _match_cache[match_id]
        if match_id in _match_summary_cache:
            del _match_summary_cache[match_id]
        
        return {
            "success": True,
            "match_id": match_id,
            "label": match_config["label"],
            "deleted": deleted_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/data/fetch-all")
async def fetch_all_match_data():
    """Fetch all missing match data from StatsBomb."""
    if not HAS_STATSBOMB:
        raise HTTPException(
            status_code=503, 
            detail="statsbombpy not installed. Install with: pip install statsbombpy"
        )
    
    from ultils.match_loader import DATA_DIR, get_match_events, get_match_lineups
    
    results = []
    for m in WORLD_CUP_MATCHES:
        match_id = m["match_id"]
        match_title = m["match_title"]
        
        events_file = os.path.join(DATA_DIR, f"match_{match_title}_events_{match_id}.json")
        lineups_file = os.path.join(DATA_DIR, f"match_{match_title}_lineups_{match_id}.json")
        
        # Skip if already cached
        if os.path.exists(events_file) and os.path.exists(lineups_file):
            results.append({"match_id": match_id, "label": m["label"], "status": "already_cached"})
            continue
        
        try:
            get_match_events(match_id, match_title)
            get_match_lineups(match_id, match_title)
            results.append({"match_id": match_id, "label": m["label"], "status": "fetched"})
        except Exception as e:
            results.append({"match_id": match_id, "label": m["label"], "status": "error", "error": str(e)})
    
    return {
        "success": True,
        "results": results,
        "fetched": sum(1 for r in results if r["status"] == "fetched"),
        "already_cached": sum(1 for r in results if r["status"] == "already_cached"),
        "errors": sum(1 for r in results if r["status"] == "error")
    }


@app.get("/api/players", response_model=PlayersResponse)
async def get_players(match_id: int = None):
    """Get list of all players from the match."""
    try:
        _, lineups, config = get_cached_match_data(match_id)
        
        players = []
        teams = list(lineups.keys())
        
        for team_name, team_players in lineups.items():
            for player in team_players:
                # Get primary position
                positions = player.get("positions", [])
                primary_position = positions[0].get("position") if positions else None
                
                # Handle nan values from pandas (convert to None)
                nickname = player.get("player_nickname")
                if nickname is not None and (isinstance(nickname, float) or str(nickname) == "nan"):
                    nickname = None
                
                players.append(PlayerInfo(
                    player_id=player["player_id"],
                    player_name=player["player_name"],
                    player_nickname=nickname,
                    jersey_number=player["jersey_number"],
                    team=team_name,
                    position=primary_position,
                ))
        
        # Sort by team, then jersey number
        players.sort(key=lambda p: (p.team, p.jersey_number))
        
        return PlayersResponse(
            match_id=config["match_id"],
            match_title=config["label"],
            teams=teams,
            players=players,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_player_from_lineups(lineups: dict, player_name: str = None, player_id: int = None) -> tuple[Optional[int], Optional[str]]:
    """
    Resolve player_id and canonical player_name from lineups.
    Handles encoding/format mismatches via exact match, nickname match, and partial match.
    Returns (player_id, player_name) or (None, None) if not found.
    """
    def norm(s):
        return (str(s or "").strip().lower())

    partial_matches = []
    for team_name, team_players in lineups.items():
        for p in team_players:
            pid = p.get("player_id")
            pname = str(p.get("player_name") or "").strip()
            pnick = p.get("player_nickname")
            if pnick is None or isinstance(pnick, float):
                pnick = ""
            pnick = str(pnick).strip()

            if player_id is not None:
                try:
                    if int(pid) == int(player_id):
                        return (int(pid), pname or str(pid))
                except (TypeError, ValueError):
                    pass

            if player_name:
                inp = norm(player_name)
                if not inp:
                    continue
                if norm(pname) == inp or norm(pnick) == inp:
                    return (pid, pname)
                if inp in norm(pname) or inp in norm(pnick):
                    partial_matches.append((pid, pname))

    if partial_matches:
        return min(partial_matches, key=lambda x: len(x[1]))
    return (None, None)


@app.get("/api/player/{player_name}/analysis")
async def get_player_analysis(player_name: str, top_n: int = 5, match_id: int = None):
    """
    Get detailed player analysis with highlights, lowlights, and pitch viz data.
    
    Args:
        player_name: Full player name or nickname (e.g., "Lionel Messi" or "Lionel Andrés Messi Cuccittini")
        top_n: Number of top moments to return (default 5)
    """
    try:
        events, lineups, _ = get_cached_match_data(match_id)

        # Decode URL-encoded characters
        player_name = unquote(player_name)

        # Resolve player_id from lineups (handles encoding/name variants)
        player_id, canonical_name = _resolve_player_from_lineups(lineups, player_name=player_name)

        if player_id is None or canonical_name is None:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found in match roster")

        result = get_player_analysis_with_viz(
            events,
            canonical_name,
            home_team="Argentina",
            top_n=top_n,
            player_id=player_id,
        )

        if "error" in result and not result.get("player_did_not_play"):
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/player/id/{player_id:int}/analysis")
async def get_player_analysis_by_id(player_id: int, top_n: int = 5, match_id: int = None):
    """
    Get player analysis by player_id (most reliable - use when name matching fails).
    """
    try:
        events, lineups, _ = get_cached_match_data(match_id)
        _, canonical_name = _resolve_player_from_lineups(lineups, player_id=player_id)

        if canonical_name is None:
            raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found in match roster")

        result = get_player_analysis_with_viz(
            events, canonical_name, home_team="Argentina", top_n=top_n, player_id=player_id
        )
        if "error" in result and not result.get("player_did_not_play"):
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/highlights")
async def get_match_highlights_endpoint(top_n: int = 10, match_id: int = None):
    """Get top highlights from the entire match."""
    try:
        events, _, config = get_cached_match_data(match_id)
        highlights = get_match_highlights(events, home_team="Argentina", top_n=top_n)
        
        # Add pitch_viz_data to each highlight
        events_list = list(events.values())
        for highlight in highlights:
            player_name = highlight.get("player")
            time_display = highlight.get("time_display")
            
            for event in events_list:
                if (event.get("player", {}).get("name") == player_name and
                    f"{event['minute']}:{event['second']:02d}" == time_display):
                    viz_data = extract_pitch_viz_data(event)
                    if viz_data:
                        highlight["pitch_viz_data"] = viz_data
                    break
        
        return {
            "match_title": config["label"],
            "highlights": highlights,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


_match_summary_cache: Dict[int, dict] = {}


@app.get("/api/match/summary")
async def get_match_summary_endpoint(match_id: int = None):
    """Get full match summary: best players, players needing improvement, team summary, team improvements."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        mid = config["match_id"]
        if mid not in _match_summary_cache:
            home_team = next(iter(lineups.keys()), "Argentina") if lineups else "Argentina"
            _match_summary_cache[mid] = get_match_summary(
                events, lineups, config["label"],
                home_team=home_team,
                top_players_n=5,
                improvement_players_n=5,
            )
        return _match_summary_cache[mid]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ADVANCED ANALYTICS ENDPOINTS
# ============================================

@app.get("/api/player/compare")
async def compare_players(player1_id: int, player2_id: int, match_id: int = None):
    """Compare two players side by side."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        
        # Resolve player names
        _, name1 = _resolve_player_from_lineups(lineups, player_id=player1_id)
        _, name2 = _resolve_player_from_lineups(lineups, player_id=player2_id)
        
        if not name1 or not name2:
            raise HTTPException(status_code=404, detail="One or both players not found")
        
        # Get stats for both players
        stats1, highlights1, lowlights1 = get_player_data(events, name1, player_id=player1_id)
        stats2, highlights2, lowlights2 = get_player_data(events, name2, player_id=player2_id)
        
        # Get positions for heat maps
        events_list = list(events.values())
        positions1 = []
        positions2 = []
        
        for event in events_list:
            loc = event.get("location")
            if not loc:
                continue
            pid = event.get("player", {}).get("id")
            etype = event.get("type", {}).get("name", "")
            if pid == player1_id:
                positions1.append({"x": round(loc[0], 1), "y": round(loc[1], 1), "type": etype})
            elif pid == player2_id:
                positions2.append({"x": round(loc[0], 1), "y": round(loc[1], 1), "type": etype})
        
        return {
            "match_id": config["match_id"],
            "player1": {
                "player_id": player1_id,
                "name": name1,
                "stats": stats1 if "error" not in stats1 else {},
                "positions": positions1,
                "highlights_count": len(highlights1),
                "lowlights_count": len(lowlights1),
            },
            "player2": {
                "player_id": player2_id,
                "name": name2,
                "stats": stats2 if "error" not in stats2 else {},
                "positions": positions2,
                "highlights_count": len(highlights2),
                "lowlights_count": len(lowlights2),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/momentum")
async def get_match_momentum(match_id: int = None, interval_minutes: int = 5):
    """Get momentum tracker showing team dominance over time intervals."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        teams = list(lineups.keys()) if lineups else ["Team A", "Team B"]
        
        events_list = sorted(events.values(), key=lambda e: (e.get("period", 1), e.get("minute", 0), e.get("second", 0)))
        
        # Track momentum in intervals
        momentum_data = []
        current_interval_start = 0
        
        # Process up to 120 minutes (including extra time)
        for interval_start in range(0, 125, interval_minutes):
            interval_end = interval_start + interval_minutes
            
            team_stats = {team: {"passes": 0, "shots": 0, "possession_events": 0, "xT": 0.0, "pressure_events": 0} for team in teams}
            
            for event in events_list:
                minute = event.get("minute", 0)
                if minute < interval_start or minute >= interval_end:
                    continue
                
                team = event.get("team", {}).get("name")
                if team not in team_stats:
                    continue
                
                etype = event.get("type", {}).get("name", "")
                loc = event.get("location")
                
                if etype == "Pass":
                    team_stats[team]["passes"] += 1
                    team_stats[team]["possession_events"] += 1
                    if loc:
                        end_loc = event.get("pass", {}).get("end_location")
                        if end_loc:
                            team_stats[team]["xT"] += calculate_xt_delta(loc, end_loc)
                elif etype == "Shot":
                    team_stats[team]["shots"] += 1
                elif etype == "Carry":
                    team_stats[team]["possession_events"] += 1
                elif etype == "Pressure":
                    team_stats[team]["pressure_events"] += 1
            
            # Calculate dominance score for each team
            total_possession = sum(ts["possession_events"] for ts in team_stats.values()) or 1
            
            interval_data = {
                "interval_start": interval_start,
                "interval_end": interval_end,
                "teams": {}
            }
            
            for team, ts in team_stats.items():
                possession_pct = round(ts["possession_events"] / total_possession * 100)
                dominance = ts["passes"] * 0.3 + ts["shots"] * 2 + ts["xT"] * 10 + ts["pressure_events"] * 0.5
                interval_data["teams"][team] = {
                    "possession_pct": possession_pct,
                    "passes": ts["passes"],
                    "shots": ts["shots"],
                    "xT": round(ts["xT"], 3),
                    "pressure_events": ts["pressure_events"],
                    "dominance_score": round(dominance, 2),
                }
            
            momentum_data.append(interval_data)
        
        return {
            "match_id": config["match_id"],
            "match_title": config["label"],
            "teams": teams,
            "interval_minutes": interval_minutes,
            "momentum": momentum_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/score-impact")
async def get_score_impact(match_id: int = None):
    """Analyze team/player performance when leading, trailing, or drawing."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        teams = list(lineups.keys()) if lineups else []
        
        events_list = sorted(events.values(), key=lambda e: (e.get("period", 1), e.get("minute", 0), e.get("second", 0)))
        
        # Track score through match
        score = {team: 0 for team in teams}
        
        # Stats by game state
        stats_by_state = {
            "leading": {team: {"passes": 0, "shots": 0, "goals": 0, "xT": 0.0, "complete_passes": 0} for team in teams},
            "trailing": {team: {"passes": 0, "shots": 0, "goals": 0, "xT": 0.0, "complete_passes": 0} for team in teams},
            "drawing": {team: {"passes": 0, "shots": 0, "goals": 0, "xT": 0.0, "complete_passes": 0} for team in teams},
        }
        
        goal_times = []
        
        for event in events_list:
            team = event.get("team", {}).get("name")
            etype = event.get("type", {}).get("name", "")
            
            # Check for goals to update score
            if etype == "Shot" and event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                if team in score:
                    score[team] += 1
                    goal_times.append({
                        "minute": event.get("minute", 0),
                        "team": team,
                        "score": dict(score),
                    })
            
            if team not in teams:
                continue
            
            # Determine game state for this team
            other_team = [t for t in teams if t != team]
            if other_team:
                other = other_team[0]
                if score[team] > score[other]:
                    state = "leading"
                elif score[team] < score[other]:
                    state = "trailing"
                else:
                    state = "drawing"
            else:
                state = "drawing"
            
            loc = event.get("location")
            
            if etype == "Pass":
                stats_by_state[state][team]["passes"] += 1
                if "outcome" not in event.get("pass", {}):
                    stats_by_state[state][team]["complete_passes"] += 1
                if loc:
                    end_loc = event.get("pass", {}).get("end_location")
                    if end_loc:
                        stats_by_state[state][team]["xT"] += calculate_xt_delta(loc, end_loc)
            elif etype == "Shot":
                stats_by_state[state][team]["shots"] += 1
                if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                    stats_by_state[state][team]["goals"] += 1
        
        # Calculate pass accuracy for each state
        result = {"leading": {}, "trailing": {}, "drawing": {}}
        for state, team_stats in stats_by_state.items():
            for team, ts in team_stats.items():
                acc = round(ts["complete_passes"] / ts["passes"] * 100) if ts["passes"] > 0 else 0
                result[state][team] = {
                    "passes": ts["passes"],
                    "pass_accuracy": f"{acc}%",
                    "shots": ts["shots"],
                    "goals": ts["goals"],
                    "xT": round(ts["xT"], 3),
                }
        
        return {
            "match_id": config["match_id"],
            "match_title": config["label"],
            "teams": teams,
            "final_score": score,
            "goal_times": goal_times,
            "stats_by_state": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/substitutions")
async def get_substitution_impact(match_id: int = None):
    """Analyze impact of substitutions on team performance."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        teams = list(lineups.keys()) if lineups else []
        
        events_list = sorted(events.values(), key=lambda e: (e.get("period", 1), e.get("minute", 0), e.get("second", 0)))
        
        # Find substitution events
        substitutions = []
        for event in events_list:
            if event.get("type", {}).get("name") == "Substitution":
                sub_data = event.get("substitution", {})
                substitutions.append({
                    "minute": event.get("minute", 0),
                    "team": event.get("team", {}).get("name", ""),
                    "player_off": event.get("player", {}).get("name", ""),
                    "player_off_id": event.get("player", {}).get("id"),
                    "player_on": sub_data.get("replacement", {}).get("name", ""),
                    "player_on_id": sub_data.get("replacement", {}).get("id"),
                })
        
        # Analyze impact: compare 10 minutes before and after each substitution
        sub_impacts = []
        for sub in substitutions:
            sub_minute = sub["minute"]
            player_on_id = sub["player_on_id"]
            player_off_id = sub["player_off_id"]
            team = sub["team"]
            
            # Team stats before sub (10 mins)
            before = {"passes": 0, "shots": 0, "xT": 0.0}
            after = {"passes": 0, "shots": 0, "xT": 0.0}
            
            # Player on stats after sub
            player_on_stats = {"passes": 0, "shots": 0, "goals": 0, "xT": 0.0}
            
            for event in events_list:
                evt_team = event.get("team", {}).get("name")
                minute = event.get("minute", 0)
                etype = event.get("type", {}).get("name", "")
                pid = event.get("player", {}).get("id")
                loc = event.get("location")
                
                # Before substitution (same team)
                if evt_team == team and sub_minute - 10 <= minute < sub_minute:
                    if etype == "Pass":
                        before["passes"] += 1
                        if loc:
                            end_loc = event.get("pass", {}).get("end_location")
                            if end_loc:
                                before["xT"] += calculate_xt_delta(loc, end_loc)
                    elif etype == "Shot":
                        before["shots"] += 1
                
                # After substitution (same team)
                if evt_team == team and sub_minute <= minute < sub_minute + 10:
                    if etype == "Pass":
                        after["passes"] += 1
                        if loc:
                            end_loc = event.get("pass", {}).get("end_location")
                            if end_loc:
                                after["xT"] += calculate_xt_delta(loc, end_loc)
                    elif etype == "Shot":
                        after["shots"] += 1
                
                # Player on specific stats
                if pid == player_on_id and minute >= sub_minute:
                    if etype == "Pass":
                        player_on_stats["passes"] += 1
                        if loc:
                            end_loc = event.get("pass", {}).get("end_location")
                            if end_loc:
                                player_on_stats["xT"] += calculate_xt_delta(loc, end_loc)
                    elif etype == "Shot":
                        player_on_stats["shots"] += 1
                        if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                            player_on_stats["goals"] += 1
            
            sub_impacts.append({
                **sub,
                "team_before_10min": {
                    "passes": before["passes"],
                    "shots": before["shots"],
                    "xT": round(before["xT"], 3),
                },
                "team_after_10min": {
                    "passes": after["passes"],
                    "shots": after["shots"],
                    "xT": round(after["xT"], 3),
                },
                "player_on_contribution": {
                    "passes": player_on_stats["passes"],
                    "shots": player_on_stats["shots"],
                    "goals": player_on_stats["goals"],
                    "xT": round(player_on_stats["xT"], 3),
                },
                "impact_delta": {
                    "passes": after["passes"] - before["passes"],
                    "shots": after["shots"] - before["shots"],
                    "xT": round(after["xT"] - before["xT"], 3),
                },
            })
        
        return {
            "match_id": config["match_id"],
            "match_title": config["label"],
            "substitutions": sub_impacts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/set-pieces")
async def get_set_piece_analysis(match_id: int = None):
    """Analyze set piece effectiveness: corners, free kicks, throw-ins, penalties."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        teams = list(lineups.keys()) if lineups else []
        
        events_list = sorted(events.values(), key=lambda e: (e.get("period", 1), e.get("minute", 0), e.get("second", 0)))
        
        # Categorize by play pattern
        set_piece_stats = {team: {
            "corners": {"total": 0, "shots": 0, "goals": 0},
            "free_kicks": {"total": 0, "shots": 0, "goals": 0, "direct_shots": 0},
            "throw_ins": {"total": 0, "retained": 0},
            "penalties": {"taken": 0, "scored": 0},
        } for team in teams}
        
        # Track possession sequences
        current_play_pattern = None
        current_possession_team = None
        
        for event in events_list:
            team = event.get("team", {}).get("name")
            etype = event.get("type", {}).get("name", "")
            play_pattern = event.get("play_pattern", {}).get("name", "Regular Play")
            
            if team not in set_piece_stats:
                continue
            
            # Count set piece initiations
            if play_pattern == "From Corner" and etype == "Pass":
                if current_play_pattern != "From Corner" or current_possession_team != team:
                    set_piece_stats[team]["corners"]["total"] += 1
            elif play_pattern == "From Free Kick" and etype in ["Pass", "Shot"]:
                if current_play_pattern != "From Free Kick" or current_possession_team != team:
                    set_piece_stats[team]["free_kicks"]["total"] += 1
                    if etype == "Shot":
                        set_piece_stats[team]["free_kicks"]["direct_shots"] += 1
            elif play_pattern == "From Throw In" and etype == "Pass":
                if current_play_pattern != "From Throw In" or current_possession_team != team:
                    set_piece_stats[team]["throw_ins"]["total"] += 1
            
            # Count outcomes during set pieces
            if play_pattern == "From Corner":
                if etype == "Shot":
                    set_piece_stats[team]["corners"]["shots"] += 1
                    if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                        set_piece_stats[team]["corners"]["goals"] += 1
            elif play_pattern == "From Free Kick":
                if etype == "Shot":
                    set_piece_stats[team]["free_kicks"]["shots"] += 1
                    if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                        set_piece_stats[team]["free_kicks"]["goals"] += 1
            
            # Penalties
            if play_pattern == "From Penalty" and etype == "Shot":
                set_piece_stats[team]["penalties"]["taken"] += 1
                if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                    set_piece_stats[team]["penalties"]["scored"] += 1
            
            current_play_pattern = play_pattern
            current_possession_team = team
        
        return {
            "match_id": config["match_id"],
            "match_title": config["label"],
            "teams": teams,
            "set_pieces": set_piece_stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/passing-network")
async def get_passing_network(match_id: int = None, team: str = None, min_passes: int = 2):
    """Get passing network showing connections between players."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        teams = list(lineups.keys()) if lineups else []
        
        if not team and teams:
            team = teams[0]
        
        events_list = list(events.values())
        
        # Build passing connections
        pass_connections = {}  # (from_id, to_id) -> count
        player_pass_counts = {}  # player_id -> {passes, received, x_sum, y_sum}
        player_names = {}  # player_id -> name
        
        for event in events_list:
            if event.get("type", {}).get("name") != "Pass":
                continue
            if event.get("team", {}).get("name") != team:
                continue
            
            passer_id = event.get("player", {}).get("id")
            passer_name = event.get("player", {}).get("name", "Unknown")
            recipient_id = event.get("pass", {}).get("recipient", {}).get("id")
            loc = event.get("location")
            
            if not passer_id or not recipient_id:
                continue
            
            player_names[passer_id] = passer_name
            recipient_name = event.get("pass", {}).get("recipient", {}).get("name", "Unknown")
            player_names[recipient_id] = recipient_name
            
            # Count connection
            key = (passer_id, recipient_id)
            pass_connections[key] = pass_connections.get(key, 0) + 1
            
            # Track positions and counts
            if passer_id not in player_pass_counts:
                player_pass_counts[passer_id] = {"passes": 0, "received": 0, "x_sum": 0, "y_sum": 0, "count": 0}
            player_pass_counts[passer_id]["passes"] += 1
            if loc:
                player_pass_counts[passer_id]["x_sum"] += loc[0]
                player_pass_counts[passer_id]["y_sum"] += loc[1]
                player_pass_counts[passer_id]["count"] += 1
            
            if recipient_id not in player_pass_counts:
                player_pass_counts[recipient_id] = {"passes": 0, "received": 0, "x_sum": 0, "y_sum": 0, "count": 0}
            player_pass_counts[recipient_id]["received"] += 1
        
        # Build nodes (players)
        nodes = []
        for pid, stats in player_pass_counts.items():
            avg_x = stats["x_sum"] / stats["count"] if stats["count"] > 0 else 60
            avg_y = stats["y_sum"] / stats["count"] if stats["count"] > 0 else 40
            name = player_names.get(pid, "Unknown")
            short_name = name.split()[-1] if " " in name else name
            nodes.append({
                "id": pid,
                "name": name,
                "short_name": short_name,
                "passes": stats["passes"],
                "received": stats["received"],
                "avg_x": round(avg_x, 1),
                "avg_y": round(avg_y, 1),
            })
        
        # Build edges (connections with min_passes threshold)
        edges = []
        max_passes = max(pass_connections.values()) if pass_connections else 1
        for (from_id, to_id), count in pass_connections.items():
            if count >= min_passes:
                edges.append({
                    "from": from_id,
                    "to": to_id,
                    "passes": count,
                    "weight": round(count / max_passes, 2),  # Normalized weight
                })
        
        return {
            "match_id": config["match_id"],
            "match_title": config["label"],
            "team": team,
            "teams": teams,
            "nodes": nodes,
            "edges": edges,
            "total_passes": sum(n["passes"] for n in nodes) // 2,  # Divide by 2 to avoid double count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/pressing")
async def get_pressing_analysis(match_id: int = None):
    """Analyze pressing intensity and effectiveness by team."""
    try:
        events, lineups, config = get_cached_match_data(match_id)
        teams = list(lineups.keys()) if lineups else []
        
        events_list = sorted(events.values(), key=lambda e: (e.get("period", 1), e.get("minute", 0), e.get("second", 0)))
        
        pressing_stats = {team: {
            "total_pressures": 0,
            "successful_pressures": 0,  # Followed by turnover
            "high_pressures": 0,  # In opponent's third (x > 80 for team attacking right)
            "mid_pressures": 0,
            "low_pressures": 0,
            "pressure_locations": [],  # For visualization
            "pressure_by_interval": {},  # 15-min intervals
        } for team in teams}
        
        # Track pressure events and their outcomes
        for i, event in enumerate(events_list):
            if event.get("type", {}).get("name") != "Pressure":
                continue
            
            team = event.get("team", {}).get("name")
            if team not in pressing_stats:
                continue
            
            loc = event.get("location")
            minute = event.get("minute", 0)
            
            pressing_stats[team]["total_pressures"] += 1
            
            if loc:
                pressing_stats[team]["pressure_locations"].append({
                    "x": round(loc[0], 1),
                    "y": round(loc[1], 1),
                    "minute": minute,
                })
                
                # Categorize by zone (assuming team attacks toward x=120)
                if loc[0] > 80:
                    pressing_stats[team]["high_pressures"] += 1
                elif loc[0] > 40:
                    pressing_stats[team]["mid_pressures"] += 1
                else:
                    pressing_stats[team]["low_pressures"] += 1
            
            # Check if pressure was successful (next event is turnover for pressing team)
            if i + 1 < len(events_list):
                next_event = events_list[i + 1]
                next_team = next_event.get("team", {}).get("name")
                next_type = next_event.get("type", {}).get("name", "")
                if next_team == team and next_type in ["Ball Recovery", "Interception"]:
                    pressing_stats[team]["successful_pressures"] += 1
            
            # Track by interval
            interval = (minute // 15) * 15
            interval_key = f"{interval}-{interval + 15}"
            if interval_key not in pressing_stats[team]["pressure_by_interval"]:
                pressing_stats[team]["pressure_by_interval"][interval_key] = 0
            pressing_stats[team]["pressure_by_interval"][interval_key] += 1
        
        # Calculate success rates
        result = {}
        for team, stats in pressing_stats.items():
            success_rate = round(stats["successful_pressures"] / stats["total_pressures"] * 100) if stats["total_pressures"] > 0 else 0
            result[team] = {
                "total_pressures": stats["total_pressures"],
                "successful_pressures": stats["successful_pressures"],
                "success_rate": f"{success_rate}%",
                "high_pressures": stats["high_pressures"],
                "mid_pressures": stats["mid_pressures"],
                "low_pressures": stats["low_pressures"],
                "pressure_locations": stats["pressure_locations"][:100],  # Limit for performance
                "pressure_by_interval": stats["pressure_by_interval"],
            }
        
        return {
            "match_id": config["match_id"],
            "match_title": config["label"],
            "teams": teams,
            "pressing": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            print(f"      Watch at {m['video_time']}: {m['video_url']}")
    else:
        print("   No significant highlights recorded.")
    
    print(f"\n[-] TOP {len(lowlights)} AREAS FOR IMPROVEMENT:")
    if lowlights:
        for i, m in enumerate(lowlights, 1):
            print(f"   {i}. [{m['time_display']}] {m['description']}")
            print(f"      Score: {m['highlight_score']:.3f} | Value: {m['value_added']:.3f} | xT: {m['xt_delta']:+.4f}")
            print(f"      Watch at {m['video_time']}: {m['video_url']}")
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
        print(f"      Watch at {m['video_time']}: {m['video_url']}")
    
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
