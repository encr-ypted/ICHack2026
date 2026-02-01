<script setup lang="ts">
import { computed } from "vue";

export interface PitchVizData {
  action_type?: string;
  player_name?: string;
  start_coords?: [number, number];
  end_coords?: [number, number];
  coords?: [number, number];
  outcome?: string;
  team_color?: string;
}

export interface PlayerPosition {
  x: number;
  y: number;
  type: string;
}

export interface FormationPlayer {
  player_name: string;
  short_name: string;
  jersey_number: number;
  position_name: string;
  x: number;
  y: number;
}

const props = withDefaults(
  defineProps<{
    activeAction: PitchVizData | null;
    allPositions?: PlayerPosition[];
    formation?: FormationPlayer[];
    isDarkMode?: boolean;
    showHeatMap?: boolean;
    showFormation?: boolean;
    teamColor?: string;
  }>(),
  {
    allPositions: () => [],
    formation: () => [],
    isDarkMode: true,
    showHeatMap: true,
    showFormation: false,
    teamColor: "#3b82f6",
  }
);

const svgWidth = 800;
const svgHeight = (svgWidth / 120) * 80;

const actionColor = computed(() => {
  if (!props.activeAction) return "#666";
  const outcome = (props.activeAction.outcome || "").toLowerCase();
  // Green for success
  if (["goal", "complete", "won", "success"].includes(outcome)) return "#22c55e";
  // Amber/red for failures
  if (["incomplete", "missed", "lost", "out", "pass offside", "unknown", "fail", "failed"].includes(outcome)) return "#ef4444";
  // Blue for saves/blocks
  if (["saved", "blocked"].includes(outcome)) return "#3b82f6";
  // Default: if outcome is empty/undefined, use team color; otherwise treat as failure
  if (!outcome) return props.activeAction.team_color || "#06b6d4";
  return "#ef4444"; // Unknown outcome = treat as failure
});

const isSuccess = computed(() => {
  if (!props.activeAction) return true;
  const outcome = (props.activeAction.outcome || "").toLowerCase();
  return ["goal", "complete", "won", "success"].includes(outcome);
});

const hasMovement = computed(() => {
  if (!props.activeAction) return false;
  const a = props.activeAction;
  return !!(a.start_coords && a.end_coords && ["pass", "carry", "dribble"].includes(a.action_type || ""));
});

const isPointAction = computed(() => {
  if (!props.activeAction) return false;
  const a = props.activeAction;
  if (["shot", "defense"].includes(a.action_type || "")) return true;
  if (a.action_type === "dribble" && a.coords) return true;
  if (a.coords && !(a.start_coords && a.end_coords)) return true;
  return false;
});

const hasDrawableCoords = computed(() => {
  if (!props.activeAction) return false;
  const a = props.activeAction;
  return (a.start_coords && a.end_coords) || (a.coords && a.coords.length >= 2);
});

const arrowId = computed(() => `arrow-${actionColor.value.replace("#", "")}`);

function getHeatColor(type: string) {
  const map: Record<string, string> = {
    Pass: "#3b82f6",
    Shot: "#ef4444",
    Dribble: "#8b5cf6",
    Carry: "#06b6d4",
    "Ball Recovery": "#22c55e",
    Interception: "#22c55e",
    Tackle: "#eab308",
    Block: "#f97316",
    Clearance: "#14b8a6",
  };
  return map[type] || "#94a3b8";
}
</script>

<template>
  <div class="w-full overflow-hidden rounded-xl shadow-lg bg-black/5">
    <svg
      :viewBox="'0 0 120 80'"
      :width="svgWidth"
      :height="svgHeight"
      class="w-full h-auto block"
    >
      <defs>
        <linearGradient id="pitchGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" :stop-color="isDarkMode ? '#064e3b' : '#86efac'" />
          <stop offset="50%" :stop-color="isDarkMode ? '#065f46' : '#4ade80'" />
          <stop offset="100%" :stop-color="isDarkMode ? '#064e3b' : '#86efac'" />
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="heatBlur" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="2" />
        </filter>
        <marker
          :id="arrowId"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <path d="M0,0 L0,6 L9,3 z" :fill="actionColor">
            <animate attributeName="opacity" values="0.85;1;0.85" dur="1.2s" repeatCount="indefinite" />
          </path>
        </marker>
      </defs>

      <!-- Pitch -->
      <rect x="0" y="0" width="120" height="80" fill="url(#pitchGrad)" />
      <g :opacity="isDarkMode ? 0.1 : 0.15">
        <rect v-for="i in 12" :key="'s'+i" :x="(i-1)*10" y="0" width="5" height="80" fill="#fff" />
      </g>
      <rect x="0" y="0" width="120" height="80" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.4" />
      <line x1="60" y1="0" x2="60" y2="80" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <circle cx="60" cy="40" r="9.15" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <circle cx="60" cy="40" r="0.4" :fill="isDarkMode ? '#34d399' : '#16a34a'" />
      <rect x="0" y="18" width="18" height="44" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <rect x="0" y="30" width="6" height="20" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <circle cx="12" cy="40" r="0.4" :fill="isDarkMode ? '#34d399' : '#16a34a'" />
      <path d="M 18 29 A 9.15 9.15 0 0 1 18 51" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <rect x="102" y="18" width="18" height="44" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <rect x="114" y="30" width="6" height="20" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <circle cx="108" cy="40" r="0.4" :fill="isDarkMode ? '#34d399' : '#16a34a'" />
      <path d="M 102 29 A 9.15 9.15 0 0 0 102 51" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <path d="M 0 1 A 1 1 0 0 0 1 0" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <path d="M 119 0 A 1 1 0 0 0 120 1" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <path d="M 0 79 A 1 1 0 0 1 1 80" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <path d="M 119 80 A 1 1 0 0 1 120 79" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
      <rect x="-2" y="36" width="2" height="8" :fill="isDarkMode ? '#fff' : '#374151'" fill-opacity="0.6" rx="0.3" />
      <rect x="120" y="36" width="2" height="8" :fill="isDarkMode ? '#fff' : '#374151'" fill-opacity="0.6" rx="0.3" />

      <!-- Heat map -->
      <g v-if="showHeatMap && allPositions.length > 0" opacity="0.5">
        <circle
          v-for="(pos, idx) in allPositions"
          :key="'h'+idx"
          :cx="pos.x"
          :cy="pos.y"
          r="2"
          :fill="getHeatColor(pos.type)"
          opacity="0.5"
          filter="url(#heatBlur)"
        />
      </g>

      <!-- Formation display -->
      <g v-if="showFormation && formation.length > 0">
        <g v-for="(player, idx) in formation" :key="'f'+idx">
          <!-- Player circle -->
          <circle
            :cx="player.x"
            :cy="player.y"
            r="4"
            :fill="teamColor"
            :stroke="isDarkMode ? '#fff' : '#000'"
            stroke-width="0.4"
            opacity="0.9"
          />
          <!-- Jersey number -->
          <text
            :x="player.x"
            :y="player.y + 0.8"
            font-size="3"
            fill="#fff"
            text-anchor="middle"
            dominant-baseline="middle"
            font-weight="bold"
          >{{ player.jersey_number }}</text>
          <!-- Player name label -->
          <rect
            :x="player.x - 8"
            :y="player.y + 5"
            width="16"
            height="3.5"
            :fill="isDarkMode ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.9)'"
            rx="0.5"
          />
          <text
            :x="player.x"
            :y="player.y + 7"
            font-size="2"
            :fill="isDarkMode ? '#fff' : '#1f2937'"
            text-anchor="middle"
            font-weight="500"
          >{{ player.short_name }}</text>
        </g>
      </g>

      <!-- Active action: movement (pass/carry) -->
      <g v-if="hasMovement && activeAction?.start_coords && activeAction?.end_coords" filter="url(#glow)">
        <!-- Glow line -->
        <line
          :x1="activeAction.start_coords[0]"
          :y1="activeAction.start_coords[1]"
          :x2="activeAction.end_coords[0]"
          :y2="activeAction.end_coords[1]"
          :stroke="actionColor"
          stroke-width="2"
          opacity="0.3"
        />
        <!-- Main line with flow animation for successful passes -->
        <line
          :x1="activeAction.start_coords[0]"
          :y1="activeAction.start_coords[1]"
          :x2="activeAction.end_coords[0]"
          :y2="activeAction.end_coords[1]"
          :stroke="actionColor"
          stroke-width="0.8"
          :stroke-dasharray="isSuccess ? 'none' : '2,1'"
          :marker-end="isSuccess ? 'url(#' + arrowId + ')' : ''"
          :class="isSuccess ? 'pass-line-animated' : ''"
        />
        <!-- Start point -->
        <circle :cx="activeAction.start_coords[0]" :cy="activeAction.start_coords[1]" r="3" :fill="actionColor" fill-opacity="0.3" />
        <circle :cx="activeAction.start_coords[0]" :cy="activeAction.start_coords[1]" r="2" :fill="actionColor" />
        <!-- End point: checkmark for success, X for failure -->
        <g v-if="isSuccess">
          <circle :cx="activeAction.end_coords[0]" :cy="activeAction.end_coords[1]" r="1.5" :fill="actionColor" :stroke="isDarkMode ? '#fff' : '#000'" stroke-width="0.3" />
        </g>
        <g v-else>
          <!-- X marker for failed pass -->
          <circle :cx="activeAction.end_coords[0]" :cy="activeAction.end_coords[1]" r="2.5" fill="#ef4444" fill-opacity="0.3" />
          <line :x1="activeAction.end_coords[0]-1.5" :y1="activeAction.end_coords[1]-1.5" :x2="activeAction.end_coords[0]+1.5" :y2="activeAction.end_coords[1]+1.5" stroke="#ef4444" stroke-width="0.6" />
          <line :x1="activeAction.end_coords[0]+1.5" :y1="activeAction.end_coords[1]-1.5" :x2="activeAction.end_coords[0]-1.5" :y2="activeAction.end_coords[1]+1.5" stroke="#ef4444" stroke-width="0.6" />
        </g>
        <!-- Player name label -->
        <rect :x="activeAction.start_coords[0]-10" :y="activeAction.start_coords[1]-7" width="20" height="4" :fill="isDarkMode ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.9)'" rx="1" />
        <text :x="activeAction.start_coords[0]" :y="activeAction.start_coords[1]-4" font-size="2.5" :fill="isDarkMode ? '#fff' : '#1f2937'" text-anchor="middle" font-weight="600">{{ activeAction.player_name || '' }}</text>
        <!-- Outcome label at end point -->
        <rect :x="activeAction.end_coords[0]-8" :y="activeAction.end_coords[1]+3" width="16" height="3.5" :fill="isSuccess ? 'rgba(34,197,94,0.9)' : 'rgba(239,68,68,0.9)'" rx="0.5" />
        <text :x="activeAction.end_coords[0]" :y="activeAction.end_coords[1]+5.2" font-size="2" fill="#fff" text-anchor="middle" font-weight="600">{{ isSuccess ? 'COMPLETE' : 'INCOMPLETE' }}</text>
      </g>

      <!-- Active action: point (shot/defense/dribble/other) -->
      <g v-else-if="isPointAction && activeAction?.coords && activeAction.coords.length >= 2" filter="url(#glow)">
        <circle :cx="activeAction.coords[0]" :cy="activeAction.coords[1]" r="5" :fill="actionColor" fill-opacity="0.2" />
        <circle :cx="activeAction.coords[0]" :cy="activeAction.coords[1]" r="3" :fill="actionColor" fill-opacity="0.4" :stroke="actionColor" stroke-width="0.8" />
        <circle :cx="activeAction.coords[0]" :cy="activeAction.coords[1]" r="1.5" :fill="actionColor" />
        <line v-if="activeAction.action_type === 'shot'" :x1="activeAction.coords[0]" :y1="activeAction.coords[1]" x2="120" y2="40" :stroke="actionColor" stroke-width="0.5" stroke-dasharray="1,1" opacity="0.6" />
        <text :x="activeAction.coords[0]" :y="activeAction.coords[1]-5" font-size="3" :fill="isDarkMode ? '#fff' : '#1f2937'" text-anchor="middle" font-weight="600">{{ activeAction.player_name || '' }}</text>
        <text :x="activeAction.coords[0]" :y="activeAction.coords[1]+6" font-size="2.5" :fill="actionColor" text-anchor="middle" font-weight="500">{{ activeAction.outcome || '' }}</text>
      </g>

      <!-- Empty state -->
      <text
        v-else
        x="60"
        y="40"
        font-size="4"
        :fill="isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)'"
        text-anchor="middle"
        dominant-baseline="middle"
      >
        {{ allPositions.length > 0 ? 'Click a moment below' : 'Select a player' }}
      </text>
    </svg>
  </div>
</template>

<style scoped>
.pass-line-animated {
  animation: line-flow 1s ease-in-out infinite;
}

@keyframes line-flow {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}
</style>
