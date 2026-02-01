<script setup lang="ts">
import { cn } from "~/utils/cn";
import { computed, ref, onMounted, watch } from "vue";
import PitchMap from "~/components/PitchMap.vue";
import AdvancedAnalytics from "~/components/AdvancedAnalytics.vue";
import PlayerComparison from "~/components/PlayerComparison.vue";

const emit = defineEmits<{
  navigate: [screen: "landing" | "coach" | "player"];
}>();

const { isDarkMode, toggleTheme } = useTheme();

// ============================================
// API CONFIGURATION
// ============================================
const API_BASE = "http://localhost:8000";

// ============================================
// TYPE DEFINITIONS
// ============================================
interface PitchVizData {
  action_type: "pass" | "carry" | "dribble" | "shot" | "defense";
  player_name: string;
  start_coords?: [number, number];
  end_coords?: [number, number];
  coords?: [number, number];
  outcome: "goal" | "complete" | "incomplete" | "saved" | "blocked" | "missed" | "won" | "lost";
  team_color?: string;
}

interface PlayerPosition {
  x: number;
  y: number;
  type: string;
}

interface Moment {
  time_display: string;
  event_type: string;
  description: string;
  highlight_score: number;
  value_added: number;
  xt_delta: number;
  video_url: string;
  video_time: string;
  period: number;
  minute: number;
  pitch_viz_data?: PitchVizData;
}

interface PlayerStats {
  name: string;
  total_highlight_score: number;
  total_value_added: number;
  total_actions: number;
  positive_contributions: number;
  negative_contributions: number;
  highlights_count: number;
  lowlights_count: number;
  pass_accuracy: string;
  shots: number;
  goals: number;
  total_xt?: number;
  progressive_passes?: number;
  progressive_pass_accuracy?: string;
  passes_into_final_third?: number;
  passes_into_box?: number;
  through_balls?: number;
  key_passes?: number;
  actions_under_pressure?: number;
  pressure_success_pct?: string;
}

interface PlayerInfo {
  player_id: number;
  player_name: string;
  player_nickname: string | null;
  jersey_number: number;
  team: string;
  position: string | null;
}

interface PlayerAnalysis {
  player_name: string;
  stats: PlayerStats;
  top_highlights: Moment[];
  areas_for_improvement: Moment[];
  all_positions: PlayerPosition[];
  player_summary?: string;
  player_did_not_play?: boolean;
  what_went_well?: string[];
  what_to_work_on?: string[];
  even_better_if?: string[];
}

interface MatchSummary {
  match_title: string;
  match_summary: string;
  best_players: { player_name: string; team: string; net_impact: number; goals: number; highlights_count: number }[];
  players_needing_improvement: { player_name: string; team: string; net_impact: number; lowlights_count: number; top_issue: string }[];
  team_improvements: string[];
  total_goals: number;
  players_analyzed: number;
}

interface TeamStats {
  total_passes: number;
  complete_passes: number;
  pass_accuracy: string;
  shots: number;
  shots_on_target: number;
  goals: number;
  total_xt: number;
  progressive_passes: number;
  passes_into_box: number;
  key_passes: number;
  tackles: number;
  interceptions: number;
  clearances: number;
  blocks: number;
  possession_pct: string;
}

interface FormationPlayer {
  player_id: number;
  player_name: string;
  short_name: string;
  jersey_number: number;
  position_name: string;
  x: number;
  y: number;
}

// ============================================
// STATE
// ============================================
// Matches from API
interface MatchOption {
  match_id: number;
  label: string;
  stage: string;
}
const matches = ref<MatchOption[]>([]);
const selectedMatchId = ref<number | null>(null);
const isLoadingMatches = ref(false);

// Players list from API
const players = ref<PlayerInfo[]>([]);
const selectedPlayerName = ref<string>("");
const selectedTeam = ref<string>("Argentina");
const isLoadingPlayers = ref(false);
const isLoadingAnalysis = ref(false);
const analysisError = ref<string | null>(null);

// Player analysis data
const playerAnalysis = ref<PlayerAnalysis | null>(null);

// Active action for pitch visualization
const activeHighlightVizData = ref<PitchVizData | null>(null);

// All positions for heat map
const allPositions = ref<PlayerPosition[]>([]);

// Match summary (whole-team view)
const matchSummary = ref<MatchSummary | null>(null);
const isLoadingMatchSummary = ref(false);

// Team stats
const teamStats = ref<TeamStats | null>(null);
const isLoadingTeamStats = ref(false);

// Formation
const formation = ref<FormationPlayer[]>([]);
const formationNumber = ref<number | null>(null);

// Pitch view mode: 'formation' or 'heatmap'
const pitchViewMode = ref<'formation' | 'heatmap'>('formation');

// Computed: filtered players by team
const filteredPlayers = computed(() => {
  return players.value.filter(p => p.team === selectedTeam.value);
});

// Computed: available teams
const teams = computed(() => {
  const teamSet = new Set(players.value.map(p => p.team));
  return Array.from(teamSet);
});

// Computed: current player display name
const currentPlayerDisplay = computed(() => {
  const player = players.value.find(p => p.player_name === selectedPlayerName.value);
  if (player) {
    return player.player_nickname || player.player_name.split(" ").slice(-1)[0];
  }
  return "Select Player";
});

// Computed: performance breakdown metrics derived from backend stats
const performanceBreakdown = computed(() => {
  const stats = playerAnalysis.value?.stats;
  if (!stats) return null;

  const total = stats.total_actions || 1;
  const hasPassData = stats.pass_accuracy && stats.pass_accuracy !== "N/A";
  const passPct = hasPassData ? parseInt(stats.pass_accuracy, 10) || 0 : null;

  return {
    positiveImpact: Math.min(10, ((stats.positive_contributions || 0) / total) * 10),
    ballRetention: Math.max(0, 10 - ((stats.negative_contributions || 0) / total) * 10),
    passReliability: passPct !== null ? passPct / 10 : null,
    highlightDensity: Math.min(10, ((stats.highlights_count || 0) / total) * 25),
    netValue: Math.min(10, Math.max(0, ((stats.total_value_added || 0) + 2) / 0.7)),
  };
});

// Computed: moments (highlights + lowlights combined and sorted)
const criticalMoments = computed(() => {
  if (!playerAnalysis.value) return [];
  
  const highlights = (playerAnalysis.value.top_highlights || []).map(h => ({
    ...h,
    impact: "positive" as const,
    xTGained: h.value_added,
  }));
  
  const lowlights = (playerAnalysis.value.areas_for_improvement || []).map(l => ({
    ...l,
    impact: "negative" as const,
    xTLost: l.value_added,
  }));
  
  // Combine and sort by minute
  return [...highlights, ...lowlights].sort((a, b) => b.minute - a.minute);
});

// ============================================
// API FUNCTIONS
// ============================================
async function fetchMatches() {
  isLoadingMatches.value = true;
  try {
    const response = await fetch(`${API_BASE}/api/matches`);
    if (!response.ok) throw new Error("Failed to fetch matches");
    const data = await response.json();
    matches.value = data.matches;
    if (data.matches?.length > 0 && !selectedMatchId.value) {
      selectedMatchId.value = data.matches[0].match_id;
    }
  } catch (error) {
    console.error("Error fetching matches:", error);
    analysisError.value = "Failed to connect to backend.";
  } finally {
    isLoadingMatches.value = false;
  }
}

async function fetchPlayers() {
  if (selectedMatchId.value == null) return;
  isLoadingPlayers.value = true;
  analysisError.value = null;
  try {
    const response = await fetch(`${API_BASE}/api/players?match_id=${selectedMatchId.value}`);
    if (!response.ok) throw new Error("Failed to fetch players");
    
    const data = await response.json();
    players.value = data.players;
    
    // Auto-select first player from first team
    const firstTeam = data.teams?.[0];
    const firstPlayer = data.players?.find((p: PlayerInfo) => p.team === firstTeam);
    if (firstPlayer) {
      selectedPlayerName.value = firstPlayer.player_name;
      selectedTeam.value = firstTeam;
    }
  } catch (error) {
    console.error("Error fetching players:", error);
    analysisError.value = "Failed to fetch players for this match.";
  } finally {
    isLoadingPlayers.value = false;
  }
}

async function fetchPlayerAnalysis(playerName: string, playerId?: number) {
  if (!playerName) return;
  
  isLoadingAnalysis.value = true;
  analysisError.value = null;
  
  try {
    const matchParam = selectedMatchId.value != null ? `&match_id=${selectedMatchId.value}` : "";
    // Prefer player_id endpoint (avoids encoding/name matching issues)
    const url = playerId != null
      ? `${API_BASE}/api/player/id/${playerId}/analysis?top_n=5${matchParam}`
      : `${API_BASE}/api/player/${encodeURIComponent(playerName)}/analysis?top_n=5${matchParam}`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to fetch analysis");
    }
    
    const data: PlayerAnalysis = await response.json();
    playerAnalysis.value = data;
    allPositions.value = data.all_positions || [];
    
    // Set first highlight/lowlight as active on map, or clear if none
    const firstMoment = data.top_highlights?.[0] || data.areas_for_improvement?.[0];
    if (firstMoment) {
      let viz = firstMoment.pitch_viz_data || makeFallbackVizData(firstMoment);
      // Ensure outcome is lowercase for consistent comparison
      if (viz && viz.outcome) {
        viz = { ...viz, outcome: viz.outcome.toLowerCase() as any };
      }
      activeHighlightVizData.value = viz;
    } else {
      activeHighlightVizData.value = null;
    }
  } catch (error: any) {
    console.error("Error fetching player analysis:", error);
    analysisError.value = error.message;
    playerAnalysis.value = null;
  } finally {
    isLoadingAnalysis.value = false;
  }
}

// Show action on the pitch map
// Create fallback pitch_viz_data when API doesn't provide it (from allPositions or moment index)
function makeFallbackVizData(moment: Moment & { impact?: string }): PitchVizData {
  const positions = allPositions.value;
  const idx = (moment.minute || 0) % Math.max(1, positions.length);
  const pos = positions[idx] || { x: 60, y: 40, type: "Pass" };
  // Use impact if available (from criticalMoments), otherwise use highlight_score
  const isPositive = moment.impact === "positive" || (moment.highlight_score > 0);
  return {
    action_type: "other",
    player_name: moment.event_type || "Action",
    coords: [pos.x, pos.y],
    outcome: isPositive ? "complete" : "incomplete",
    team_color: isPositive ? "#22c55e" : "#ef4444",
  };
}

const showOnMap = (moment: Moment & { impact?: string }) => {
  let viz = moment.pitch_viz_data || makeFallbackVizData(moment);
  // Ensure outcome is always lowercase for consistent comparison
  if (viz && viz.outcome) {
    viz = { ...viz, outcome: viz.outcome.toLowerCase() as any };
  }
  activeHighlightVizData.value = viz;
};

// Watch for player selection changes
watch(selectedPlayerName, (newName) => {
  if (newName) {
    const player = players.value.find((p) => p.player_name === newName);
    fetchPlayerAnalysis(newName, player?.player_id);
  }
});

// Watch for team changes - auto-select first player
watch(selectedTeam, (newTeam) => {
  const firstPlayer = players.value.find(p => p.team === newTeam);
  if (firstPlayer) {
    selectedPlayerName.value = firstPlayer.player_name;
  }
});

// Watch for match changes - refetch players and match summary
watch(selectedMatchId, (newId) => {
  if (newId) {
    fetchPlayers();
    fetchMatchSummary();
    fetchTeamStats();
    fetchFormation();
  }
});

// Refetch team-specific data when team changes
watch(selectedTeam, () => {
  if (selectedMatchId.value) {
    fetchTeamStats();
    fetchFormation();
  }
});

async function fetchMatchSummary() {
  if (selectedMatchId.value == null) return;
  isLoadingMatchSummary.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/match/summary?match_id=${selectedMatchId.value}`);
    if (res.ok) {
      matchSummary.value = await res.json();
    } else {
      matchSummary.value = null;
    }
  } catch {
    matchSummary.value = null;
  } finally {
    isLoadingMatchSummary.value = false;
  }
}

async function fetchTeamStats() {
  if (selectedMatchId.value == null) return;
  isLoadingTeamStats.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/team/stats?match_id=${selectedMatchId.value}&team=${encodeURIComponent(selectedTeam.value)}`);
    if (res.ok) {
      const data = await res.json();
      teamStats.value = data.stats;
    } else {
      teamStats.value = null;
    }
  } catch {
    teamStats.value = null;
  } finally {
    isLoadingTeamStats.value = false;
  }
}

async function fetchFormation() {
  if (selectedMatchId.value == null) return;
  try {
    const res = await fetch(`${API_BASE}/api/formation?match_id=${selectedMatchId.value}&team=${encodeURIComponent(selectedTeam.value)}`);
    if (res.ok) {
      const data = await res.json();
      formation.value = data.players || [];
      formationNumber.value = data.formation;
    } else {
      formation.value = [];
      formationNumber.value = null;
    }
  } catch {
    formation.value = [];
    formationNumber.value = null;
  }
}

// ============================================
// LIFECYCLE
// ============================================
onMounted(() => {
  fetchMatches();
});



</script>

<template>
  <div
    :class="
      cn(
        'min-h-screen',
        isDarkMode ? 'bg-[#0a0b14] text-white' : 'bg-white text-gray-900'
      )
    "
  >
    <!-- Top Bar -->
    <div
      :class="
        cn(
          'border-b backdrop-blur-sm sticky top-0 z-50',
          isDarkMode
            ? 'border-white/10 bg-[#0a0b14]/95'
            : 'border-gray-200 bg-white/95'
        )
      "
    >
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <UiButton
              variant="ghost"
              size="sm"
              @click="emit('navigate', 'landing')"
              :class="
                isDarkMode
                  ? 'text-white/70 hover:text-white'
                  : 'text-gray-600 hover:text-gray-900'
              "
            >
              <Icon name="lucide:arrow-left" class="w-4 h-4 mr-2" />
              Back
            </UiButton>

            <div
              :class="
                cn('h-6 w-px', isDarkMode ? 'bg-white/10' : 'bg-gray-200')
              "
            ></div>

            <div class="flex items-center gap-3">
              <Icon name="lucide:target" class="w-5 h-5 text-emerald-400" />
              <div>
                <h1 class="font-semibold">PlayerMode</h1>
                <p
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  Personal Analytics Review
                </p>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <button
              @click="toggleTheme"
              :class="
                cn(
                  'p-2 rounded-lg transition-colors',
                  isDarkMode ? 'hover:bg-white/10' : 'hover:bg-gray-100'
                )
              "
              aria-label="Toggle theme"
            >
              <Icon v-if="isDarkMode" name="lucide:sun" class="w-5 h-5" />
              <Icon v-else name="lucide:moon" class="w-5 h-5" />
            </button>

            <div class="flex items-center gap-2">
              <span
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')
                "
                >Match:</span
              >
              <select
                v-model="selectedMatchId"
                :disabled="isLoadingMatches"
                :class="
                  cn(
                    'border rounded-lg px-3 py-2 text-sm min-w-[220px]',
                    isDarkMode
                      ? 'bg-[#12141f] border-white/10 text-white'
                      : 'bg-white border-gray-300 text-gray-900',
                    isLoadingMatches ? 'opacity-50 cursor-wait' : ''
                  )
                "
              >
                <option v-if="isLoadingMatches" :value="null">Loading matches...</option>
                <option
                  v-for="m in matches"
                  :key="m.match_id"
                  :value="m.match_id"
                >
                  {{ m.label }}
                </option>
              </select>
            </div>

            <div class="flex items-center gap-2">
              <span
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')
                "
                >Team:</span
              >
              <select
                v-model="selectedTeam"
                :class="
                  cn(
                    'border rounded-lg px-3 py-2 text-sm',
                    isDarkMode
                      ? 'bg-[#12141f] border-white/10 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  )
                "
              >
                <option v-for="team in teams" :key="team" :value="team">{{ team }}</option>
              </select>
            </div>

            <div class="flex items-center gap-2">
              <span
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')
                "
                >Player:</span
              >
              <select
                v-model="selectedPlayerName"
                :disabled="isLoadingPlayers"
                :class="
                  cn(
                    'border rounded-lg px-3 py-2 text-sm min-w-[200px]',
                    isDarkMode
                      ? 'bg-[#12141f] border-white/10 text-white'
                      : 'bg-white border-gray-300 text-gray-900',
                    isLoadingPlayers ? 'opacity-50 cursor-wait' : ''
                  )
                "
              >
                <option v-if="isLoadingPlayers" value="">Loading...</option>
                <option 
                  v-for="player in filteredPlayers" 
                  :key="player.player_id" 
                  :value="player.player_name"
                >
                  #{{ player.jersey_number }} {{ player.player_nickname || player.player_name.split(' ').slice(-1)[0] }}
                </option>
              </select>
            </div>

            <!-- Match loaded indicator -->
            <div
              v-if="selectedMatchId && matches.length > 0"
              :class="
                cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg border',
                  isDarkMode
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-emerald-50 border-emerald-200'
                )
              "
            >
              <Icon
                name="lucide:trophy"
                class="w-4 h-4 text-emerald-400"
              />
              <span
                :class="
                  cn(
                    'text-sm',
                    isDarkMode ? 'text-emerald-300' : 'text-emerald-700'
                  )
                "
              >
                {{ matches.find(m => m.match_id === selectedMatchId)?.label || 'Match selected' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-12 gap-6 p-6">
      <!-- Left Column - Player Truth Report -->
      <div class="col-span-4 space-y-6">
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-purple-500/30'
                : 'bg-white border-purple-300'
            )
          "
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <div
                :class="cn(
                  'w-10 h-10 rounded-full flex items-center justify-center',
                  selectedTeam === 'Argentina' ? 'bg-blue-500/20' : 'bg-red-500/20'
                )"
              >
                <span class="text-xl font-bold">{{ currentPlayerDisplay.substring(0, 2).toUpperCase() }}</span>
              </div>
              <div>
                <div class="font-semibold">{{ currentPlayerDisplay }}</div>
                <div
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  {{ selectedTeam }} · #{{ filteredPlayers.find(p => p.player_name === selectedPlayerName)?.jersey_number || '?' }}
                </div>
              </div>
            </div>
            <UiBadge
              v-if="isLoadingAnalysis"
              variant="outline"
              :class="
                cn(
                  'text-xs',
                  isDarkMode
                    ? 'border-blue-500/30 text-blue-400'
                    : 'border-blue-300 text-blue-600'
                )
              "
            >
              <Icon name="lucide:loader-2" class="w-3 h-3 mr-1 animate-spin" />
              Loading...
            </UiBadge>
            <UiBadge
              v-else
              variant="outline"
              :class="
                cn(
                  'text-xs',
                  isDarkMode
                    ? 'border-emerald-500/30 text-emerald-400'
                    : 'border-emerald-300 text-emerald-600'
                )
              "
            >
              <Icon name="lucide:sparkles" class="w-3 h-3 mr-1" />
              ML Analyzed
            </UiBadge>
          </div>

          <div
            :class="
              cn(
                'rounded-lg p-4 mb-4 border',
                isDarkMode
                  ? 'bg-[#0a0b14] border-purple-500/20'
                  : 'bg-purple-50 border-purple-200'
              )
            "
          >
            <h4
              :class="
                cn(
                  'font-semibold mb-3',
                  isDarkMode ? 'text-purple-400' : 'text-purple-600'
                )
              "
            >
              The Player Truth Report
            </h4>
            <div v-if="!playerAnalysis" :class="cn('text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')">
              Select a player to see their match summary.
            </div>
            <div v-else class="space-y-4">
              <p
                :class="
                  cn(
                    'text-sm leading-relaxed',
                    isDarkMode ? 'text-white/80' : 'text-gray-700'
                  )
                "
              >
                {{ playerAnalysis.player_summary || 'No summary available.' }}
              </p>
              <div v-if="!playerAnalysis.player_did_not_play && (playerAnalysis.what_went_well?.length || playerAnalysis.what_to_work_on?.length || playerAnalysis.even_better_if?.length)">
                <div v-if="playerAnalysis.what_went_well?.length" class="mb-3">
                  <div class="flex items-center gap-2 mb-1.5">
                    <Icon name="lucide:check-circle-2" class="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span :class="cn('text-xs font-semibold', isDarkMode ? 'text-emerald-400' : 'text-emerald-600')">What went well</span>
                  </div>
                  <ul class="list-disc list-inside text-sm space-y-1" :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">
                    <li v-for="(item, i) in playerAnalysis.what_went_well" :key="i">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="playerAnalysis.what_to_work_on?.length" class="mb-3">
                  <div class="flex items-center gap-2 mb-1.5">
                    <Icon name="lucide:alert-circle" class="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span :class="cn('text-xs font-semibold', isDarkMode ? 'text-amber-400' : 'text-amber-600')">What to work on</span>
                  </div>
                  <ul class="list-disc list-inside text-sm space-y-1" :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">
                    <li v-for="(item, i) in playerAnalysis.what_to_work_on" :key="i">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="playerAnalysis.even_better_if?.length">
                  <div class="flex items-center gap-2 mb-1.5">
                    <Icon name="lucide:sparkles" class="w-4 h-4 text-cyan-400 flex-shrink-0" />
                    <span :class="cn('text-xs font-semibold', isDarkMode ? 'text-cyan-400' : 'text-cyan-600')">Even better if</span>
                  </div>
                  <ul class="list-disc list-inside text-sm space-y-1" :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">
                    <li v-for="(item, i) in playerAnalysis.even_better_if" :key="i">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2 text-xs text-white/50 mb-4">
            <Icon name="lucide:bar-chart-2" class="w-3 h-3" />
            <span>Data-driven analysis from match events</span>
          </div>
        </UiCard>

        <!-- Key Metrics -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-white/10'
                : 'bg-white border-gray-200'
            )
          "
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold">Key Metrics</h3>
            <UiBadge
              variant="outline"
              :class="
                cn(
                  'text-xs',
                  isDarkMode
                    ? 'border-emerald-500/30 text-emerald-400'
                    : 'border-emerald-200 text-emerald-600'
                )
              "
            >
              Live Data
            </UiBadge>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- Net Impact Score -->
            <div
              :class="
                cn(
                  'rounded-lg p-4',
                  (playerAnalysis?.stats?.total_highlight_score ?? 0) >= 0
                    ? isDarkMode ? 'bg-[#0a0b14]' : 'bg-emerald-50'
                    : isDarkMode ? 'bg-[#0a0b14]' : 'bg-amber-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-2xl font-bold mb-1',
                    (playerAnalysis?.stats?.total_highlight_score ?? 0) >= 0
                      ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                      : isDarkMode ? 'text-amber-400' : 'text-amber-600'
                  )
                "
              >
                {{ playerAnalysis?.stats?.total_highlight_score?.toFixed(1) ?? '—' }}
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Net Impact Score
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  :name="(playerAnalysis?.stats?.total_highlight_score ?? 0) >= 0 ? 'lucide:trending-up' : 'lucide:trending-down'"
                  :class="(playerAnalysis?.stats?.total_highlight_score ?? 0) >= 0 ? 'w-3 h-3 text-emerald-400' : 'w-3 h-3 text-amber-400'"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      (playerAnalysis?.stats?.total_highlight_score ?? 0) >= 0
                        ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                        : isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                >
                  {{ (playerAnalysis?.stats?.total_highlight_score ?? 0) >= 0 ? 'Positive' : 'Negative' }}
                </span>
              </div>
            </div>

            <!-- Total Actions -->
            <div
              :class="
                cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-blue-50')
              "
            >
              <div
                :class="
                  cn(
                    'text-2xl font-bold mb-1',
                    isDarkMode ? 'text-blue-400' : 'text-blue-600'
                  )
                "
              >
                {{ playerAnalysis?.stats?.total_actions ?? '—' }}
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Total Actions
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:activity"
                  class="w-3 h-3 text-blue-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-blue-400' : 'text-blue-600'
                    )
                  "
                >
                  +{{ playerAnalysis?.stats?.positive_contributions ?? 0 }} / -{{ playerAnalysis?.stats?.negative_contributions ?? 0 }}
                </span>
              </div>
            </div>

            <!-- Goals/Shots -->
            <div
              :class="
                cn(
                  'rounded-lg p-4',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-purple-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-2xl font-bold mb-1',
                    isDarkMode ? 'text-purple-400' : 'text-purple-600'
                  )
                "
              >
                {{ playerAnalysis?.stats?.goals ?? 0 }}
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Goals
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:target"
                  class="w-3 h-3 text-purple-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-purple-400' : 'text-purple-600'
                    )
                  "
                >
                  {{ playerAnalysis?.stats?.shots ?? 0 }} shots
                </span>
              </div>
            </div>

            <!-- Pass Accuracy -->
            <div
              :class="
                cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50')
              "
            >
              <div
                :class="
                  cn(
                    'text-2xl font-bold mb-1',
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  )
                "
              >
                {{ playerAnalysis?.stats?.pass_accuracy ?? '—' }}
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Pass Accuracy
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:arrow-right-circle"
                  class="w-3 h-3 text-gray-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  ML-analyzed
                </span>
              </div>
            </div>

            <!-- Highlights Count -->
            <div
              :class="
                cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-emerald-50')
              "
            >
              <div
                :class="
                  cn(
                    'text-2xl font-bold mb-1',
                    isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                  )
                "
              >
                {{ playerAnalysis?.stats?.highlights_count ?? '—' }}
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Key Highlights
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon name="lucide:star" class="w-3 h-3 text-emerald-400" />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    )
                  "
                >
                  Positive moments
                </span>
              </div>
            </div>

            <!-- Lowlights Count -->
            <div
              :class="
                cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-amber-50')
              "
            >
              <div
                :class="
                  cn(
                    'text-2xl font-bold mb-1',
                    isDarkMode ? 'text-amber-400' : 'text-amber-600'
                  )
                "
              >
                {{ playerAnalysis?.stats?.lowlights_count ?? '—' }}
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Areas to Improve
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon name="lucide:alert-triangle" class="w-3 h-3 text-amber-400" />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                >
                  Focus points
                </span>
              </div>
            </div>

            <!-- Advanced: Total xT -->
            <div v-if="playerAnalysis?.stats?.total_xt != null" :class="cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-slate-50')">
              <div :class="cn('text-2xl font-bold mb-1', (playerAnalysis?.stats?.total_xt ?? 0) >= 0 ? (isDarkMode ? 'text-emerald-400' : 'text-emerald-600') : (isDarkMode ? 'text-amber-400' : 'text-amber-600'))">
                {{ (playerAnalysis?.stats?.total_xt ?? 0) >= 0 ? '+' : '' }}{{ playerAnalysis?.stats?.total_xt?.toFixed(2) ?? '—' }}
              </div>
              <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Total xT</div>
              <div class="flex items-center gap-1 mt-2">
                <Icon name="lucide:zap" class="w-3 h-3 text-slate-400" />
                <span :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-600')">Expected Threat</span>
              </div>
            </div>

            <!-- Advanced: Progressive Passes -->
            <div v-if="playerAnalysis?.stats?.progressive_passes != null" :class="cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-indigo-50')">
              <div :class="cn('text-2xl font-bold mb-1', isDarkMode ? 'text-indigo-400' : 'text-indigo-600')">
                {{ playerAnalysis?.stats?.progressive_passes ?? 0 }}
              </div>
              <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Progressive Passes</div>
              <div class="flex items-center gap-1 mt-2">
                <Icon name="lucide:move-forward" class="w-3 h-3 text-indigo-400" />
                <span :class="cn('text-xs', isDarkMode ? 'text-indigo-400' : 'text-indigo-600')">{{ playerAnalysis?.stats?.progressive_pass_accuracy ?? 'N/A' }}</span>
              </div>
            </div>

            <!-- Advanced: Key Passes -->
            <div v-if="playerAnalysis?.stats?.key_passes != null" :class="cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-orange-50')">
              <div :class="cn('text-2xl font-bold mb-1', isDarkMode ? 'text-orange-400' : 'text-orange-600')">
                {{ playerAnalysis?.stats?.key_passes ?? 0 }}
              </div>
              <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Key Passes</div>
              <div class="flex items-center gap-1 mt-2">
                <Icon name="lucide:key" class="w-3 h-3 text-orange-400" />
                <span :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-600')">{{ playerAnalysis?.stats?.passes_into_box ?? 0 }} into box</span>
              </div>
            </div>

            <!-- Advanced: Under Pressure -->
            <div v-if="playerAnalysis?.stats?.actions_under_pressure != null" :class="cn('rounded-lg p-4', isDarkMode ? 'bg-[#0a0b14]' : 'bg-rose-50')">
              <div :class="cn('text-2xl font-bold mb-1', isDarkMode ? 'text-rose-400' : 'text-rose-600')">
                {{ playerAnalysis?.stats?.actions_under_pressure ?? 0 }}
              </div>
              <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Under Pressure</div>
              <div class="flex items-center gap-1 mt-2">
                <Icon name="lucide:gauge" class="w-3 h-3 text-rose-400" />
                <span :class="cn('text-xs', isDarkMode ? 'text-rose-400' : 'text-rose-600')">{{ playerAnalysis?.stats?.pressure_success_pct ?? 'N/A' }} success</span>
              </div>
            </div>
          </div>
        </UiCard>

        <!-- Performance Breakdown -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-white/10'
                : 'bg-white border-gray-200'
            )
          "
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold">Performance Breakdown</h3>
            <UiBadge
              variant="outline"
              :class="
                cn(
                  'text-xs',
                  isDarkMode
                    ? 'border-emerald-500/30 text-emerald-400'
                    : 'border-emerald-200 text-emerald-600'
                )
              "
            >
              From Backend
            </UiBadge>
          </div>

          <div v-if="!performanceBreakdown" class="space-y-4">
            <div
              v-for="i in 5"
              :key="i"
              :class="cn('animate-pulse', isDarkMode ? 'bg-white/5' : 'bg-gray-100')"
              class="h-12 rounded-lg"
            ></div>
            <p
              :class="
                cn('text-xs text-center', isDarkMode ? 'text-white/40' : 'text-gray-400')
              "
            >
              Select a player to see breakdown
            </p>
          </div>

          <div v-else-if="playerAnalysis?.player_did_not_play" :class="cn('p-4 rounded-lg border text-center', isDarkMode ? 'bg-[#0a0b14] border-white/10' : 'bg-gray-50 border-gray-200')">
            <Icon name="lucide:user-x" class="w-8 h-8 mx-auto mb-2 text-amber-400" />
            <p :class="cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')">
              No performance data available — player did not feature in this match.
            </p>
          </div>

          <div v-else class="space-y-4">
            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Positive Impact Rate</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      performanceBreakdown.positiveImpact >= 5
                        ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                        : isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                  >{{ performanceBreakdown.positiveImpact.toFixed(1) }}/10</span
                >
              </div>
              <div
                :class="
                  cn(
                    'h-2 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div
                  class="h-full bg-emerald-500 transition-all"
                  :style="{ width: `${Math.min(100, performanceBreakdown.positiveImpact * 10)}%` }"
                ></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Ball Retention</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      performanceBreakdown.ballRetention >= 7
                        ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                        : performanceBreakdown.ballRetention >= 5
                        ? isDarkMode ? 'text-amber-400' : 'text-amber-600'
                        : isDarkMode ? 'text-red-400' : 'text-red-600'
                    )
                  "
                  >{{ performanceBreakdown.ballRetention.toFixed(1) }}/10</span
                >
              </div>
              <div
                :class="
                  cn(
                    'h-2 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div
                  class="h-full bg-emerald-500 transition-all"
                  :style="{ width: `${Math.min(100, performanceBreakdown.ballRetention * 10)}%` }"
                ></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Pass Reliability</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      performanceBreakdown.passReliability !== null && performanceBreakdown.passReliability >= 8
                        ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                        : performanceBreakdown.passReliability !== null && performanceBreakdown.passReliability >= 6
                        ? isDarkMode ? 'text-amber-400' : 'text-amber-600'
                        : isDarkMode ? 'text-white' : 'text-gray-900'
                    )
                  "
                  >{{ performanceBreakdown.passReliability !== null ? `${performanceBreakdown.passReliability.toFixed(1)}/10` : 'N/A' }}</span
                >
              </div>
              <div
                :class="
                  cn(
                    'h-2 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div
                  class="h-full bg-blue-500 transition-all"
                  :style="{ width: performanceBreakdown.passReliability !== null ? `${Math.min(100, performanceBreakdown.passReliability * 10)}%` : '0%' }"
                ></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Highlight Density</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      performanceBreakdown.highlightDensity >= 5
                        ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                        : isDarkMode ? 'text-white' : 'text-gray-900'
                    )
                  "
                  >{{ performanceBreakdown.highlightDensity.toFixed(1) }}/10</span
                >
              </div>
              <div
                :class="
                  cn(
                    'h-2 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div
                  class="h-full bg-purple-500 transition-all"
                  :style="{ width: `${Math.min(100, performanceBreakdown.highlightDensity * 10)}%` }"
                ></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Net Value Added</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      performanceBreakdown.netValue >= 5
                        ? isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                        : performanceBreakdown.netValue >= 3
                        ? isDarkMode ? 'text-amber-400' : 'text-amber-600'
                        : isDarkMode ? 'text-white' : 'text-gray-900'
                    )
                  "
                  >{{ performanceBreakdown.netValue.toFixed(1) }}/10</span
                >
              </div>
              <div
                :class="
                  cn(
                    'h-2 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div
                  class="h-full bg-cyan-500 transition-all"
                  :style="{ width: `${Math.min(100, performanceBreakdown.netValue * 10)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </UiCard>
      </div>

      <!-- Centre Column - Pitch Visualization & Highlights -->
      <div class="col-span-5 space-y-6">
        <!-- Visual Play Analysis - Pitch Map -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-cyan-500/30'
                : 'bg-white border-cyan-300'
            )
          "
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <Icon name="lucide:map" class="w-5 h-5 text-cyan-400" />
              <div>
                <h3 class="font-semibold">Visual Play Analysis</h3>
                <p
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  {{ activeHighlightVizData ? 'Showing selected moment' : (pitchViewMode === 'formation' ? 'Starting formation' : 'All player positions') }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <UiButton
                v-if="activeHighlightVizData"
                variant="ghost"
                size="sm"
                @click="activeHighlightVizData = null"
                :class="cn('text-xs', isDarkMode ? 'text-white/70 hover:text-white' : 'text-gray-600 hover:text-gray-900')"
              >
                <Icon name="lucide:x" class="w-3 h-3 mr-1" />
                Clear
              </UiButton>
              <!-- View mode toggle buttons -->
              <div v-if="!activeHighlightVizData" class="flex items-center gap-1">
                <UiButton
                  variant="ghost"
                  size="sm"
                  @click="pitchViewMode = 'formation'"
                  :class="cn('text-xs px-2', pitchViewMode === 'formation' ? (isDarkMode ? 'bg-white/10 text-white' : 'bg-gray-200 text-gray-900') : (isDarkMode ? 'text-white/50 hover:text-white' : 'text-gray-500 hover:text-gray-900'))"
                >
                  <Icon name="lucide:users" class="w-3 h-3 mr-1" />
                  Formation
                </UiButton>
                <UiButton
                  variant="ghost"
                  size="sm"
                  @click="pitchViewMode = 'heatmap'"
                  :class="cn('text-xs px-2', pitchViewMode === 'heatmap' ? (isDarkMode ? 'bg-white/10 text-white' : 'bg-gray-200 text-gray-900') : (isDarkMode ? 'text-white/50 hover:text-white' : 'text-gray-500 hover:text-gray-900'))"
                >
                  <Icon name="lucide:flame" class="w-3 h-3 mr-1" />
                  Heat Map
                </UiButton>
              </div>
              <UiBadge
                variant="outline"
                :class="
                  cn(
                    'text-xs',
                    isDarkMode
                      ? 'border-cyan-500/30 text-cyan-400'
                      : 'border-cyan-300 text-cyan-600'
                  )
                "
              >
                <Icon name="lucide:crosshair" class="w-3 h-3 mr-1" />
                StatsBomb Data
              </UiBadge>
            </div>
          </div>
          
          <!-- Pitch Map Component -->
          <PitchMap 
            :activeAction="activeHighlightVizData" 
            :allPositions="allPositions"
            :formation="formation"
            :isDarkMode="isDarkMode" 
            :showHeatMap="pitchViewMode === 'heatmap' || !!activeHighlightVizData"
            :showFormation="pitchViewMode === 'formation' && !activeHighlightVizData"
            :teamColor="selectedTeam === 'Argentina' ? '#75aadb' : '#f59e0b'"
          />
        </UiCard>

        <div>
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="font-semibold text-lg">
                Critical Moments
              </h3>
              <p
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                5 most critical moments identified
              </p>
            </div>
            <div class="flex items-center gap-2">
              <UiBadge
                v-if="playerAnalysis?.player_did_not_play"
                variant="outline"
                :class="
                  cn(
                    'text-xs',
                    isDarkMode
                      ? 'border-amber-500/30 text-amber-400'
                      : 'border-amber-300 text-amber-600'
                  )
                "
              >
                <Icon name="lucide:user-x" class="w-3 h-3 mr-1" />
                Did Not Play
              </UiBadge>
              <UiBadge variant="outline" class="border-emerald-500/30 text-emerald-400">
                <Icon name="lucide:target" class="w-3 h-3 mr-1" />
                ML Analyzed
              </UiBadge>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="isLoadingAnalysis" class="space-y-3">
            <div v-for="i in 3" :key="i" :class="cn('p-4 rounded-xl border animate-pulse', isDarkMode ? 'bg-[#12141f] border-white/10' : 'bg-gray-50 border-gray-200')">
              <div class="flex items-center gap-3 mb-3">
                <div :class="cn('w-8 h-8 rounded-full', isDarkMode ? 'bg-white/10' : 'bg-gray-200')"></div>
                <div class="flex-1">
                  <div :class="cn('h-4 rounded w-3/4 mb-2', isDarkMode ? 'bg-white/10' : 'bg-gray-200')"></div>
                  <div :class="cn('h-3 rounded w-1/4', isDarkMode ? 'bg-white/10' : 'bg-gray-200')"></div>
                </div>
              </div>
              <div :class="cn('h-3 rounded w-full mb-2', isDarkMode ? 'bg-white/10' : 'bg-gray-200')"></div>
              <div :class="cn('h-3 rounded w-2/3', isDarkMode ? 'bg-white/10' : 'bg-gray-200')"></div>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="analysisError" :class="cn('p-6 rounded-xl border text-center', isDarkMode ? 'bg-red-500/10 border-red-500/30' : 'bg-red-50 border-red-200')">
            <Icon name="lucide:alert-triangle" class="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p :class="cn('text-sm', isDarkMode ? 'text-red-300' : 'text-red-600')">{{ analysisError }}</p>
            <p :class="cn('text-xs mt-2', isDarkMode ? 'text-white/50' : 'text-gray-500')">
              Make sure the backend is running: <code class="font-mono">uvicorn main:app --reload</code>
            </p>
          </div>

          <!-- Empty State -->
          <div v-else-if="criticalMoments.length === 0" :class="cn('p-6 rounded-xl border text-center', isDarkMode ? 'bg-[#12141f] border-white/10' : 'bg-gray-50 border-gray-200')">
            <Icon 
              :name="playerAnalysis?.player_did_not_play ? 'lucide:user-x' : 'lucide:inbox'" 
              class="w-8 h-8 mx-auto mb-2" 
              :class="playerAnalysis?.player_did_not_play ? 'text-amber-400' : 'text-gray-400'"
            />
            <p :class="cn('text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')">
              {{ playerAnalysis?.player_did_not_play 
                ? 'This player was in the squad but did not feature in this match.' 
                : 'No critical moments found for this player.' }}
            </p>
          </div>

          <!-- Moments List -->
          <div v-else class="space-y-3">
            <UiCard
              v-for="(moment, index) in criticalMoments"
              :key="`${moment.time_display}-${index}`"
              @click="showOnMap(moment)"
              :class="
                cn(
                  'p-4 transition-all hover:scale-[1.01] cursor-pointer',
                  moment.impact === 'negative'
                    ? isDarkMode
                      ? 'bg-[#12141f] border-amber-500/30 hover:border-amber-500/50'
                      : 'bg-white border-amber-300 hover:border-amber-400'
                    : isDarkMode
                    ? 'bg-[#12141f] border-emerald-500/30 hover:border-emerald-500/50'
                    : 'bg-white border-emerald-300 hover:border-emerald-400',
                  activeHighlightVizData === moment.pitch_viz_data
                    ? 'ring-2 ring-cyan-400/50'
                    : ''
                )
              "
            >
              <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-3">
                  <div
                    v-if="moment.impact === 'negative'"
                    class="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0"
                  >
                    <Icon
                      name="lucide:alert-circle"
                      class="w-4 h-4 text-amber-400"
                    />
                  </div>
                  <div
                    v-else
                    class="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0"
                  >
                    <Icon
                      name="lucide:check-circle-2"
                      class="w-4 h-4 text-emerald-400"
                    />
                  </div>
                  <div>
                    <div class="font-semibold text-sm">{{ moment.event_type }}</div>
                    <div
                      :class="
                        cn(
                          'text-xs',
                          isDarkMode ? 'text-white/50' : 'text-gray-500'
                        )
                      "
                    >
                      {{ moment.time_display }}
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <UiBadge
                    variant="outline"
                    :class="
                      cn(
                        'text-xs',
                        moment.impact === 'negative'
                          ? 'border-amber-500/30 text-amber-400'
                          : 'border-emerald-500/30 text-emerald-400'
                      )
                    "
                  >
                    {{ moment.highlight_score >= 0 ? '+' : '' }}{{ moment.highlight_score?.toFixed(2) }}
                  </UiBadge>
                  <Icon 
                    name="lucide:crosshair" 
                    :class="cn(
                      'w-4 h-4',
                      activeHighlightVizData === moment.pitch_viz_data
                        ? 'text-cyan-400'
                        : isDarkMode ? 'text-white/30' : 'text-gray-300'
                    )"
                  />
                </div>
              </div>

              <p
                :class="
                  cn(
                    'text-sm leading-relaxed mb-3',
                    isDarkMode ? 'text-white/70' : 'text-gray-600'
                  )
                "
              >
                {{ moment.description }}
              </p>

              <!-- FIFA+ Video Link -->
              <div class="flex gap-2">
                <a
                  v-if="moment.video_url && moment.video_time"
                  :href="moment.video_url"
                  target="_blank"
                  @click.stop
                  :class="
                    cn(
                      'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
                      isDarkMode
                        ? 'bg-white/5 hover:bg-white/10 text-white/70 border border-white/10'
                        : 'bg-gray-50 hover:bg-gray-100 text-gray-600 border border-gray-200'
                    )
                  "
                >
                  <Icon name="lucide:external-link" class="w-3 h-3" />
                  Watch at {{ moment.video_time }}
                </a>
                <button
                  @click.stop="showOnMap(moment)"
                  :class="
                    cn(
                      'flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
                      isDarkMode
                        ? 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30'
                        : 'bg-cyan-50 hover:bg-cyan-100 text-cyan-700 border border-cyan-200'
                    )
                  "
                >
                  <Icon name="lucide:map" class="w-3 h-3" />
                  Show on Pitch
                </button>
              </div>
            </UiCard>
          </div>
        </div>

        <!-- Voice Playback -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-blue-500/30'
                : 'bg-white border-blue-300'
            )
          "
        >
          <div class="flex items-center gap-2 mb-4">
            <Icon name="lucide:volume-2" class="w-5 h-5 text-blue-400" />
            <h3 class="font-semibold">Audio Mentoring</h3>
          </div>

          <div
            :class="
              cn(
                'rounded-lg p-4 mb-3',
                isDarkMode ? 'bg-[#0a0b14]' : 'bg-blue-50'
              )
            "
          >
            <div class="flex items-center gap-3 mb-3">
              <UiButton
                size="sm"
                class="bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30"
              >
                <Icon name="lucide:play" class="w-3 h-3" />
              </UiButton>
              <div class="flex-1 flex gap-0.5 items-end h-8">
                <div
                  v-for="(height, i) in audioWaveHeights"
                  :key="i"
                  class="flex-1 bg-blue-400/50 rounded-full"
                  :style="{ height: `${height}%` }"
                ></div>
              </div>
            </div>
            <div
              :class="
                cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
              "
            >
              Mentoring Voice via ElevenLabs
            </div>
          </div>

          <p
            :class="
              cn(
                'text-sm italic',
                isDarkMode ? 'text-white/60' : 'text-gray-600'
              )
            "
          >
            "Marcus, you were elite in transition today, but let's work on your
            composure in the box..."
          </p>
        </UiCard>
      </div>

      <!-- Right Column - Training Drills -->
      <div class="col-span-3 space-y-6">
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-emerald-500/30'
                : 'bg-white border-emerald-300'
            )
          "
        >
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <Icon name="lucide:trophy" class="w-5 h-5 text-emerald-400" />
              <div>
                <h3 class="font-semibold">Match Summary</h3>
                <p
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  {{ matchSummary?.match_title || 'Whole-team analysis' }}
                </p>
              </div>
            </div>
            <UiBadge
              variant="outline"
              :class="
                cn(
                  'text-xs',
                  isDarkMode
                    ? 'border-emerald-500/30 text-emerald-400'
                    : 'border-emerald-300 text-emerald-600'
                )
              "
            >
              Data-driven
            </UiBadge>
          </div>

          <div v-if="isLoadingMatchSummary" class="space-y-3">
            <div v-for="i in 4" :key="i" :class="cn('h-12 rounded-lg animate-pulse', isDarkMode ? 'bg-white/5' : 'bg-gray-100')"></div>
          </div>

          <div v-else-if="matchSummary" class="space-y-4">
            <p :class="cn('text-sm leading-relaxed', isDarkMode ? 'text-white/80' : 'text-gray-700')">
              {{ matchSummary.match_summary }}
            </p>

            <div v-if="matchSummary.best_players?.length">
              <div class="flex items-center gap-2 mb-2">
                <Icon name="lucide:trending-up" class="w-4 h-4 text-emerald-400" />
                <span :class="cn('text-xs font-semibold', isDarkMode ? 'text-emerald-400' : 'text-emerald-600')">Best performers</span>
              </div>
              <ul class="space-y-1.5 text-sm" :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">
                <li v-for="(p, i) in matchSummary.best_players" :key="i" class="flex justify-between items-center">
                  <span>{{ p.player_name.split(' ').pop() }}</span>
                  <span :class="cn('text-xs', isDarkMode ? 'text-emerald-400' : 'text-emerald-600')">+{{ p.net_impact?.toFixed(1) }} · {{ p.highlights_count }} highlights</span>
                </li>
              </ul>
            </div>

            <div v-if="matchSummary.players_needing_improvement?.length">
              <div class="flex items-center gap-2 mb-2">
                <Icon name="lucide:alert-triangle" class="w-4 h-4 text-amber-400" />
                <span :class="cn('text-xs font-semibold', isDarkMode ? 'text-amber-400' : 'text-amber-600')">Need improvement</span>
              </div>
              <ul class="space-y-1.5 text-sm" :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">
                <li v-for="(p, i) in matchSummary.players_needing_improvement" :key="i" class="flex justify-between items-center">
                  <span>{{ p.player_name.split(' ').pop() }}</span>
                  <span :class="cn('text-xs', isDarkMode ? 'text-amber-400' : 'text-amber-600')">{{ p.net_impact?.toFixed(1) }} · {{ p.lowlights_count }} lowlights</span>
                </li>
              </ul>
            </div>

            <div v-if="matchSummary.team_improvements?.length">
              <div class="flex items-center gap-2 mb-2">
                <Icon name="lucide:users" class="w-4 h-4 text-blue-400" />
                <span :class="cn('text-xs font-semibold', isDarkMode ? 'text-blue-400' : 'text-blue-600')">Team improvements</span>
              </div>
              <ul class="list-disc list-inside text-sm space-y-1" :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">
                <li v-for="(item, i) in matchSummary.team_improvements" :key="i">{{ item }}</li>
              </ul>
            </div>
          </div>

          <div v-else class="text-sm text-center py-4" :class="isDarkMode ? 'text-white/50' : 'text-gray-500'">
            Select a match to see the full summary.
          </div>
        </UiCard>

        <!-- Advanced Analytics -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-purple-500/30'
                : 'bg-white border-purple-300'
            )
          "
        >
          <div class="flex items-center gap-2 mb-4">
            <Icon name="lucide:bar-chart-3" class="w-5 h-5 text-purple-400" />
            <h3 class="font-semibold">Advanced Match Analytics</h3>
          </div>
          <AdvancedAnalytics
            :matchId="selectedMatchId"
            :teams="teams"
            :isDarkMode="isDarkMode"
          />
        </UiCard>

        <!-- Player Comparison -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-orange-500/30'
                : 'bg-white border-orange-300'
            )
          "
        >
          <div class="flex items-center gap-2 mb-4">
            <Icon name="lucide:users" class="w-5 h-5 text-orange-400" />
            <h3 class="font-semibold">Player Comparison</h3>
          </div>
          <PlayerComparison
            :matchId="selectedMatchId"
            :players="players"
            :isDarkMode="isDarkMode"
          />
        </UiCard>

        <!-- Security Badge -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-blue-500/30'
                : 'bg-white border-blue-300'
            )
          "
        >
          <div class="flex items-center gap-2 mb-3">
            <Icon name="lucide:shield" class="w-5 h-5 text-blue-400" />
            <h3 class="font-semibold text-sm">Data Protected</h3>
          </div>

          <p
            :class="
              cn(
                'text-xs leading-relaxed mb-4',
                isDarkMode ? 'text-white/60' : 'text-gray-600'
              )
            "
          >
            Your performance data and tactical information are secured with
            professional-grade encryption. Audited by Hacktron CLI.
          </p>

          <UiButton
            size="sm"
            variant="outline"
            class="w-full border-blue-500/30 text-blue-400 hover:bg-blue-500/10 text-xs"
          >
            View Hacktron Audit Summary
            <Icon name="lucide:chevron-right" class="w-3 h-3 ml-2" />
          </UiButton>
        </UiCard>

        <!-- Team Stats -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-white/10'
                : 'bg-white border-gray-200'
            )
          "
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-sm">{{ selectedTeam }} Stats</h3>
            <UiBadge v-if="formationNumber" variant="outline" :class="cn('text-xs', isDarkMode ? 'border-white/20 text-white/70' : 'border-gray-300 text-gray-600')">
              {{ String(formationNumber).split('').join('-') }}
            </UiBadge>
          </div>

          <!-- Loading state -->
          <div v-if="isLoadingTeamStats" class="space-y-3">
            <div v-for="i in 4" :key="i" :class="cn('h-6 rounded animate-pulse', isDarkMode ? 'bg-white/10' : 'bg-gray-200')"></div>
          </div>

          <!-- Team stats -->
          <div v-else-if="teamStats" class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <!-- Possession -->
              <div :class="cn('rounded-lg p-3', isDarkMode ? 'bg-[#0a0b14]' : 'bg-blue-50')">
                <div :class="cn('text-lg font-bold', isDarkMode ? 'text-blue-400' : 'text-blue-600')">{{ teamStats.possession_pct }}</div>
                <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Possession</div>
              </div>
              <!-- Pass Accuracy -->
              <div :class="cn('rounded-lg p-3', isDarkMode ? 'bg-[#0a0b14]' : 'bg-emerald-50')">
                <div :class="cn('text-lg font-bold', isDarkMode ? 'text-emerald-400' : 'text-emerald-600')">{{ teamStats.pass_accuracy }}</div>
                <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Pass Accuracy</div>
              </div>
              <!-- Goals -->
              <div :class="cn('rounded-lg p-3', isDarkMode ? 'bg-[#0a0b14]' : 'bg-purple-50')">
                <div :class="cn('text-lg font-bold', isDarkMode ? 'text-purple-400' : 'text-purple-600')">{{ teamStats.goals }}</div>
                <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Goals</div>
              </div>
              <!-- Shots -->
              <div :class="cn('rounded-lg p-3', isDarkMode ? 'bg-[#0a0b14]' : 'bg-orange-50')">
                <div :class="cn('text-lg font-bold', isDarkMode ? 'text-orange-400' : 'text-orange-600')">{{ teamStats.shots }}</div>
                <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Shots ({{ teamStats.shots_on_target }} on target)</div>
              </div>
            </div>

            <!-- Additional stats -->
            <div :class="cn('pt-3 border-t space-y-2', isDarkMode ? 'border-white/10' : 'border-gray-200')">
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Total xT</span>
                <span :class="cn('font-semibold', (teamStats.total_xt ?? 0) >= 0 ? (isDarkMode ? 'text-emerald-400' : 'text-emerald-600') : (isDarkMode ? 'text-amber-400' : 'text-amber-600'))">
                  {{ teamStats.total_xt >= 0 ? '+' : '' }}{{ teamStats.total_xt?.toFixed(2) }}
                </span>
              </div>
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Progressive Passes</span>
                <span class="font-semibold">{{ teamStats.progressive_passes }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Key Passes</span>
                <span class="font-semibold">{{ teamStats.key_passes }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Passes into Box</span>
                <span class="font-semibold">{{ teamStats.passes_into_box }}</span>
              </div>
            </div>

            <!-- Defensive stats -->
            <div :class="cn('pt-3 border-t space-y-2', isDarkMode ? 'border-white/10' : 'border-gray-200')">
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Tackles</span>
                <span class="font-semibold">{{ teamStats.tackles }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Interceptions</span>
                <span class="font-semibold">{{ teamStats.interceptions }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Blocks</span>
                <span class="font-semibold">{{ teamStats.blocks }}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Clearances</span>
                <span class="font-semibold">{{ teamStats.clearances }}</span>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-else :class="cn('text-center py-4 text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')">
            Select a match to view team stats
          </div>
        </UiCard>
      </div>
    </div>

  </div>
</template>
