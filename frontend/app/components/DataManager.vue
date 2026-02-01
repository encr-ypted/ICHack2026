<script setup lang="ts">
import { ref, onMounted } from "vue";
import { cn } from "~/utils/cn";

const props = withDefaults(
  defineProps<{
    isDarkMode?: boolean;
  }>(),
  {
    isDarkMode: true,
  }
);

const emit = defineEmits<{
  (e: "dataChanged"): void;
}>();

const API_BASE = "http://localhost:8000";

interface MatchStatus {
  match_id: number;
  match_title: string;
  label: string;
  stage: string;
  date?: string;
  has_events: boolean;
  has_lineups: boolean;
  is_complete: boolean;
  events_size_kb: number;
  lineups_size_kb: number;
  total_size_kb: number;
}

interface DataStatus {
  total_matches: number;
  cached_matches: number;
  missing_matches: number;
  statsbomb_available: boolean;
  matches: MatchStatus[];
}

const dataStatus = ref<DataStatus | null>(null);
const isLoading = ref(false);
const fetchingMatch = ref<number | null>(null);
const deletingMatch = ref<number | null>(null);
const fetchingAll = ref(false);
const error = ref<string | null>(null);

async function loadStatus() {
  isLoading.value = true;
  error.value = null;
  try {
    const response = await fetch(`${API_BASE}/api/data/status`);
    if (!response.ok) throw new Error("Failed to load data status");
    dataStatus.value = await response.json();
  } catch (e: any) {
    error.value = e.message || "Failed to connect to backend";
  } finally {
    isLoading.value = false;
  }
}

async function fetchMatch(matchId: number) {
  fetchingMatch.value = matchId;
  error.value = null;
  try {
    const response = await fetch(`${API_BASE}/api/data/fetch/${matchId}`, {
      method: "POST",
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to fetch match");
    }
    await loadStatus();
    emit("dataChanged");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    fetchingMatch.value = null;
  }
}

async function deleteMatch(matchId: number) {
  if (!confirm("Are you sure you want to delete this match data?")) return;
  
  deletingMatch.value = matchId;
  error.value = null;
  try {
    const response = await fetch(`${API_BASE}/api/data/delete/${matchId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to delete match");
    }
    await loadStatus();
    emit("dataChanged");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    deletingMatch.value = null;
  }
}

async function fetchAllMissing() {
  if (!confirm("Fetch all missing match data? This may take a while.")) return;
  
  fetchingAll.value = true;
  error.value = null;
  try {
    const response = await fetch(`${API_BASE}/api/data/fetch-all`, {
      method: "POST",
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to fetch matches");
    }
    await loadStatus();
    emit("dataChanged");
  } catch (e: any) {
    error.value = e.message;
  } finally {
    fetchingAll.value = false;
  }
}

onMounted(() => {
  loadStatus();
});
</script>

<template>
  <div class="space-y-4">
    <!-- Header with stats -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Icon name="lucide:database" class="w-5 h-5 text-purple-400" />
        <h3 class="font-semibold">Match Data Manager</h3>
      </div>
      <button
        @click="loadStatus"
        :disabled="isLoading"
        :class="cn(
          'p-2 rounded-lg transition-colors',
          isDarkMode ? 'hover:bg-white/10' : 'hover:bg-gray-100',
          isLoading ? 'opacity-50 cursor-wait' : ''
        )"
      >
        <Icon name="lucide:refresh-cw" :class="cn('w-4 h-4', isLoading ? 'animate-spin' : '')" />
      </button>
    </div>

    <!-- Error message -->
    <div
      v-if="error"
      :class="cn(
        'p-3 rounded-lg text-sm',
        isDarkMode ? 'bg-red-500/20 text-red-300' : 'bg-red-50 text-red-600'
      )"
    >
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-if="isLoading && !dataStatus" class="text-center py-8">
      <Icon name="lucide:loader-2" class="w-6 h-6 animate-spin mx-auto mb-2 text-purple-400" />
      <p :class="cn('text-sm', isDarkMode ? 'text-white/60' : 'text-gray-500')">Loading...</p>
    </div>

    <!-- Data status -->
    <template v-else-if="dataStatus">
      <!-- Summary cards -->
      <div class="grid grid-cols-3 gap-3">
        <div :class="cn('p-3 rounded-lg text-center', isDarkMode ? 'bg-emerald-500/10' : 'bg-emerald-50')">
          <div class="text-2xl font-bold text-emerald-400">{{ dataStatus.cached_matches }}</div>
          <div :class="cn('text-xs', isDarkMode ? 'text-white/60' : 'text-gray-500')">Cached</div>
        </div>
        <div :class="cn('p-3 rounded-lg text-center', isDarkMode ? 'bg-amber-500/10' : 'bg-amber-50')">
          <div class="text-2xl font-bold text-amber-400">{{ dataStatus.missing_matches }}</div>
          <div :class="cn('text-xs', isDarkMode ? 'text-white/60' : 'text-gray-500')">Missing</div>
        </div>
        <div :class="cn('p-3 rounded-lg text-center', isDarkMode ? 'bg-blue-500/10' : 'bg-blue-50')">
          <div class="text-2xl font-bold text-blue-400">{{ dataStatus.total_matches }}</div>
          <div :class="cn('text-xs', isDarkMode ? 'text-white/60' : 'text-gray-500')">Total</div>
        </div>
      </div>

      <!-- StatsBomb status -->
      <div
        :class="cn(
          'flex items-center gap-2 p-2 rounded-lg text-sm',
          dataStatus.statsbomb_available
            ? isDarkMode ? 'bg-emerald-500/10 text-emerald-300' : 'bg-emerald-50 text-emerald-600'
            : isDarkMode ? 'bg-amber-500/10 text-amber-300' : 'bg-amber-50 text-amber-600'
        )"
      >
        <Icon
          :name="dataStatus.statsbomb_available ? 'lucide:check-circle' : 'lucide:alert-circle'"
          class="w-4 h-4"
        />
        <span v-if="dataStatus.statsbomb_available">StatsBomb API available - can fetch new data</span>
        <span v-else>StatsBomb not installed - install with: pip install statsbombpy</span>
      </div>

      <!-- Fetch all button -->
      <button
        v-if="dataStatus.statsbomb_available && dataStatus.missing_matches > 0"
        @click="fetchAllMissing"
        :disabled="fetchingAll"
        :class="cn(
          'w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors',
          isDarkMode
            ? 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30'
            : 'bg-purple-100 hover:bg-purple-200 text-purple-700',
          fetchingAll ? 'opacity-50 cursor-wait' : ''
        )"
      >
        <Icon v-if="fetchingAll" name="lucide:loader-2" class="w-4 h-4 animate-spin inline mr-2" />
        {{ fetchingAll ? 'Fetching...' : `Fetch All Missing (${dataStatus.missing_matches})` }}
      </button>

      <!-- Match list -->
      <div class="space-y-2 max-h-80 overflow-y-auto">
        <div
          v-for="match in dataStatus.matches"
          :key="match.match_id"
          :class="cn(
            'flex items-center justify-between p-3 rounded-lg',
            isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
          )"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <Icon
                :name="match.is_complete ? 'lucide:check-circle' : 'lucide:circle'"
                :class="cn('w-4 h-4', match.is_complete ? 'text-emerald-400' : 'text-amber-400')"
              />
              <span class="font-medium text-sm truncate">{{ match.label }}</span>
            </div>
            <div :class="cn('text-xs mt-1', isDarkMode ? 'text-white/50' : 'text-gray-500')">
              {{ match.stage }} · {{ match.date || 'No date' }}
              <span v-if="match.is_complete"> · {{ match.total_size_kb }}KB</span>
            </div>
          </div>
          
          <div class="flex items-center gap-2 ml-2">
            <!-- Fetch button -->
            <button
              v-if="!match.is_complete && dataStatus.statsbomb_available"
              @click="fetchMatch(match.match_id)"
              :disabled="fetchingMatch === match.match_id"
              :class="cn(
                'p-1.5 rounded transition-colors',
                isDarkMode ? 'hover:bg-emerald-500/20 text-emerald-400' : 'hover:bg-emerald-100 text-emerald-600',
                fetchingMatch === match.match_id ? 'opacity-50 cursor-wait' : ''
              )"
              title="Fetch data"
            >
              <Icon
                :name="fetchingMatch === match.match_id ? 'lucide:loader-2' : 'lucide:download'"
                :class="cn('w-4 h-4', fetchingMatch === match.match_id ? 'animate-spin' : '')"
              />
            </button>
            
            <!-- Delete button -->
            <button
              v-if="match.is_complete"
              @click="deleteMatch(match.match_id)"
              :disabled="deletingMatch === match.match_id"
              :class="cn(
                'p-1.5 rounded transition-colors',
                isDarkMode ? 'hover:bg-red-500/20 text-red-400' : 'hover:bg-red-100 text-red-600',
                deletingMatch === match.match_id ? 'opacity-50 cursor-wait' : ''
              )"
              title="Delete data"
            >
              <Icon
                :name="deletingMatch === match.match_id ? 'lucide:loader-2' : 'lucide:trash-2'"
                :class="cn('w-4 h-4', deletingMatch === match.match_id ? 'animate-spin' : '')"
              />
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
