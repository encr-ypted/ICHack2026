<script setup lang="ts">
import { cn } from "~/utils/cn";
import { ref, watch, computed } from "vue";

const props = defineProps<{
  matchId: number | null;
  players: { player_id: number; player_name: string; team: string; position: string | null }[];
  isDarkMode: boolean;
}>();

const API_BASE = "http://localhost:8000";

const player1Id = ref<number | null>(null);
const player2Id = ref<number | null>(null);
const comparisonData = ref<any>(null);
const isLoading = ref(false);

// Group players by team
const playersByTeam = computed(() => {
  const grouped: Record<string, typeof props.players> = {};
  for (const p of props.players) {
    if (!grouped[p.team]) grouped[p.team] = [];
    grouped[p.team].push(p);
  }
  return grouped;
});

async function comparePlayersApi() {
  if (!props.matchId || !player1Id.value || !player2Id.value) return;
  if (player1Id.value === player2Id.value) return;
  
  isLoading.value = true;
  try {
    const res = await fetch(
      `${API_BASE}/api/player/compare?player1_id=${player1Id.value}&player2_id=${player2Id.value}&match_id=${props.matchId}`
    );
    if (res.ok) {
      comparisonData.value = await res.json();
    }
  } catch (e) {
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}

watch([player1Id, player2Id], () => {
  if (player1Id.value && player2Id.value && player1Id.value !== player2Id.value) {
    comparePlayersApi();
  }
});

function getShortName(name: string) {
  const parts = name?.split(' ') || [];
  return parts.length > 1 ? parts[parts.length - 1] : name;
}

function formatStat(val: any, suffix = '') {
  if (val === undefined || val === null) return '—';
  if (typeof val === 'number') return val.toFixed(1) + suffix;
  return val;
}
</script>

<template>
  <div class="space-y-4">
    <!-- Player Selection -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label :class="cn('text-xs font-medium mb-1 block', isDarkMode ? 'text-white/70' : 'text-gray-600')">Player 1</label>
        <select
          v-model="player1Id"
          :class="cn('w-full px-3 py-2 rounded-lg text-sm', isDarkMode ? 'bg-white/10 text-white border-white/20' : 'bg-white border-gray-300 border')"
        >
          <option :value="null" disabled>Select player...</option>
          <optgroup v-for="(teamPlayers, team) in playersByTeam" :key="team" :label="team">
            <option v-for="p in teamPlayers" :key="p.player_id" :value="p.player_id">
              {{ p.player_name }} {{ p.position ? `(${p.position})` : '' }}
            </option>
          </optgroup>
        </select>
      </div>
      <div>
        <label :class="cn('text-xs font-medium mb-1 block', isDarkMode ? 'text-white/70' : 'text-gray-600')">Player 2</label>
        <select
          v-model="player2Id"
          :class="cn('w-full px-3 py-2 rounded-lg text-sm', isDarkMode ? 'bg-white/10 text-white border-white/20' : 'bg-white border-gray-300 border')"
        >
          <option :value="null" disabled>Select player...</option>
          <optgroup v-for="(teamPlayers, team) in playersByTeam" :key="team" :label="team">
            <option v-for="p in teamPlayers" :key="p.player_id" :value="p.player_id">
              {{ p.player_name }} {{ p.position ? `(${p.position})` : '' }}
            </option>
          </optgroup>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="text-center py-8">
      <Icon name="lucide:loader-2" class="w-6 h-6 animate-spin mx-auto text-cyan-400" />
    </div>

    <!-- Comparison Results -->
    <div v-else-if="comparisonData" class="space-y-4">
      <!-- Player Headers -->
      <div class="grid grid-cols-3 gap-4 text-center">
        <div :class="cn('p-3 rounded-lg', isDarkMode ? 'bg-blue-500/20' : 'bg-blue-100')">
          <div class="font-semibold">{{ getShortName(comparisonData.player1?.name) }}</div>
          <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">
            {{ comparisonData.player1?.stats?.total_actions || 0 }} actions
          </div>
        </div>
        <div :class="cn('p-3 rounded-lg', isDarkMode ? 'bg-white/5' : 'bg-gray-100')">
          <div class="font-semibold">VS</div>
        </div>
        <div :class="cn('p-3 rounded-lg', isDarkMode ? 'bg-red-500/20' : 'bg-red-100')">
          <div class="font-semibold">{{ getShortName(comparisonData.player2?.name) }}</div>
          <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">
            {{ comparisonData.player2?.stats?.total_actions || 0 }} actions
          </div>
        </div>
      </div>

      <!-- Stats Comparison -->
      <div class="space-y-2">
        <div
          v-for="stat in [
            { key: 'total_highlight_score', label: 'Net Impact', suffix: '' },
            { key: 'pass_accuracy', label: 'Pass Accuracy', suffix: '' },
            { key: 'total_xt', label: 'Total xT', suffix: '' },
            { key: 'progressive_passes', label: 'Progressive Passes', suffix: '' },
            { key: 'key_passes', label: 'Key Passes', suffix: '' },
            { key: 'shots', label: 'Shots', suffix: '' },
            { key: 'goals', label: 'Goals', suffix: '' },
          ]"
          :key="stat.key"
          class="grid grid-cols-3 gap-4 items-center"
        >
          <div class="text-right">
            <span
              :class="cn(
                'font-semibold',
                (comparisonData.player1?.stats?.[stat.key] || 0) > (comparisonData.player2?.stats?.[stat.key] || 0)
                  ? 'text-emerald-400'
                  : isDarkMode ? 'text-white' : 'text-gray-900'
              )"
            >
              {{ formatStat(comparisonData.player1?.stats?.[stat.key]) }}
            </span>
          </div>
          <div class="text-center">
            <span :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">{{ stat.label }}</span>
          </div>
          <div class="text-left">
            <span
              :class="cn(
                'font-semibold',
                (comparisonData.player2?.stats?.[stat.key] || 0) > (comparisonData.player1?.stats?.[stat.key] || 0)
                  ? 'text-emerald-400'
                  : isDarkMode ? 'text-white' : 'text-gray-900'
              )"
            >
              {{ formatStat(comparisonData.player2?.stats?.[stat.key]) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Heat Map Comparison -->
      <div class="grid grid-cols-2 gap-4">
        <div v-for="(player, idx) in [comparisonData.player1, comparisonData.player2]" :key="idx">
          <div :class="cn('text-xs text-center mb-2', isDarkMode ? 'text-white/50' : 'text-gray-500')">
            {{ getShortName(player?.name) }} Positions
          </div>
          <div class="w-full overflow-hidden rounded-lg" style="aspect-ratio: 120/80;">
            <svg viewBox="0 0 120 80" class="w-full h-full" :style="{ background: isDarkMode ? '#065f46' : '#4ade80' }">
              <rect x="0" y="0" width="120" height="80" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
              <line x1="60" y1="0" x2="60" y2="80" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.2" />
              <circle
                v-for="(pos, i) in player?.positions?.slice(0, 100)"
                :key="i"
                :cx="pos.x"
                :cy="pos.y"
                r="1.5"
                :fill="idx === 0 ? '#3b82f6' : '#ef4444'"
                opacity="0.5"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else :class="cn('text-center py-8 text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')">
      Select two players to compare their performance
    </div>
  </div>
</template>
