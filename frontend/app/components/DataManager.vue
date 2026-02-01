<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { cn } from "~/utils/cn";

const props = withDefaults(
  defineProps<{
    isDarkMode?: boolean;
    isOpen?: boolean;
  }>(),
  {
    isDarkMode: true,
    isOpen: false,
  }
);

const emit = defineEmits<{
  (e: "close"): void;
  (e: "dataChanged"): void;
}>();

const API_BASE = "http://localhost:8000";

interface Competition {
  id: string;
  name: string;
  short_name: string;
  year: number;
  country: string;
  match_count: number;
}

interface MatchStatus {
  match_id: number;
  match_title: string;
  label: string;
  stage: string;
  date?: string;
  teams: string[];
  has_events: boolean;
  has_lineups: boolean;
  is_complete: boolean;
  events_size_kb: number;
  lineups_size_kb: number;
  total_size_kb: number;
}

interface DataStatus {
  competition: string;
  competition_name: string;
  total_matches: number;
  cached_matches: number;
  missing_matches: number;
  statsbomb_available: boolean;
  all_teams: string[];
  matches: MatchStatus[];
}

// Fallback when API fails - ensures dropdown always has options
const FALLBACK_COMPETITIONS: Competition[] = [
  { id: "wc2022", name: "FIFA World Cup 2022", short_name: "WC 2022", year: 2022, country: "International", match_count: 51 },
  { id: "euro2024", name: "UEFA Euro 2024", short_name: "Euro 2024", year: 2024, country: "Europe", match_count: 24 },
  { id: "euro2020", name: "UEFA Euro 2020", short_name: "Euro 2020", year: 2021, country: "Europe", match_count: 20 },
  { id: "wc2018", name: "FIFA World Cup 2018", short_name: "WC 2018", year: 2018, country: "International", match_count: 28 },
  { id: "copa2024", name: "Copa America 2024", short_name: "Copa 2024", year: 2024, country: "South America", match_count: 14 },
];

const competitions = ref<Competition[]>(FALLBACK_COMPETITIONS);
const selectedCompetition = ref<string>("wc2022");
const dataStatus = ref<DataStatus | null>(null);
const isLoading = ref(false);
const fetchingMatch = ref<number | null>(null);
const deletingMatch = ref<number | null>(null);
const fetchingAll = ref(false);
const error = ref<string | null>(null);
const selectedTeam = ref<string>("all");
const showOnlyCached = ref(false);

// Filtered matches based on team selection and cached filter
const filteredMatches = computed(() => {
  if (!dataStatus.value) return [];
  let matches = dataStatus.value.matches;
  
  if (showOnlyCached.value) {
    matches = matches.filter(m => m.is_complete);
  }
  
  return matches;
});

// Group matches by stage for display
const matchesByStage = computed(() => {
  const groups: Record<string, MatchStatus[]> = {};
  const stageOrder = ["Group Stage", "Round of 16", "Quarter-finals", "Semi-finals", "3rd Place", "Final"];
  
  for (const match of filteredMatches.value) {
    if (!groups[match.stage]) groups[match.stage] = [];
    groups[match.stage].push(match);
  }
  
  // Sort by stage order
  const sorted: { stage: string; matches: MatchStatus[] }[] = [];
  for (const stage of stageOrder) {
    if (groups[stage]) {
      sorted.push({ stage, matches: groups[stage].sort((a, b) => (a.date || "").localeCompare(b.date || "")) });
    }
  }
  return sorted;
});

async function loadCompetitions() {
  try {
    const response = await fetch(`${API_BASE}/api/data/competitions`);
    if (response.ok) {
      const data = await response.json();
      if (data.competitions?.length > 0) {
        competitions.value = data.competitions;
      }
      if (data.default) {
        selectedCompetition.value = data.default;
      }
    }
  } catch (e) {
    console.error("Failed to load competitions, using fallback");
    competitions.value = FALLBACK_COMPETITIONS;
  }
}

async function loadStatus() {
  isLoading.value = true;
  error.value = null;
  try {
    const params = new URLSearchParams();
    params.set("competition", selectedCompetition.value);
    if (selectedTeam.value !== "all") {
      params.set("team", selectedTeam.value);
    }
    const response = await fetch(`${API_BASE}/api/data/status?${params}`);
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
    const response = await fetch(`${API_BASE}/api/data/fetch/${matchId}?competition=${selectedCompetition.value}`, { method: "POST" });
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
  if (!confirm("Delete this match data?")) return;
  
  deletingMatch.value = matchId;
  error.value = null;
  try {
    const response = await fetch(`${API_BASE}/api/data/delete/${matchId}?competition=${selectedCompetition.value}`, { method: "DELETE" });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to delete");
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
    const response = await fetch(`${API_BASE}/api/data/fetch-all`, { method: "POST" });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Failed to fetch");
    }
    const result = await response.json();
    await loadStatus();
    emit("dataChanged");
    alert(`Fetched ${result.fetched} matches, ${result.errors} errors`);
  } catch (e: any) {
    error.value = e.message;
  } finally {
    fetchingAll.value = false;
  }
}

// Watch for competition change
watch(selectedCompetition, () => {
  selectedTeam.value = "all"; // Reset team filter when competition changes
  loadStatus();
});

// Watch for team change
watch(selectedTeam, () => {
  loadStatus();
});

// Load when modal opens
watch(() => props.isOpen, (open) => {
  if (open) {
    loadCompetitions();
    loadStatus();
  }
});

onMounted(() => {
  // Always load competitions so dropdown is ready when modal opens
  loadCompetitions();
});
</script>

<template>
  <!-- Modal Backdrop -->
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="emit('close')"
        ></div>
        
        <!-- Modal Content -->
        <div
          :class="cn(
            'relative w-full max-w-4xl max-h-[85vh] rounded-2xl shadow-2xl overflow-hidden flex flex-col',
            isDarkMode ? 'bg-[#12141f] border border-white/10' : 'bg-white border border-gray-200'
          )"
        >
          <!-- Header -->
          <div
            :class="cn(
              'flex items-center justify-between p-6 border-b',
              isDarkMode ? 'border-white/10' : 'border-gray-200'
            )"
          >
            <div class="flex items-center gap-3">
              <Icon name="lucide:database" class="w-6 h-6 text-purple-400" />
              <div>
                <h2 class="text-xl font-bold">Match Database</h2>
                <p :class="cn('text-sm', isDarkMode ? 'text-white/60' : 'text-gray-500')">
                  {{ dataStatus?.competition_name || 'StatsBomb Open Data' }}
                </p>
              </div>
            </div>
            <button
              @click="emit('close')"
              :class="cn(
                'p-2 rounded-lg transition-colors',
                isDarkMode ? 'hover:bg-white/10' : 'hover:bg-gray-100'
              )"
            >
              <Icon name="lucide:x" class="w-5 h-5" />
            </button>
          </div>

          <!-- Filters & Stats Bar -->
          <div
            :class="cn(
              'flex flex-wrap items-center gap-4 p-4 border-b',
              isDarkMode ? 'border-white/10 bg-[#0a0b14]' : 'border-gray-200 bg-gray-50'
            )"
          >
            <!-- Competition Filter -->
            <div class="flex items-center gap-2">
              <label :class="cn('text-sm font-medium', isDarkMode ? 'text-white/70' : 'text-gray-600')">Competition:</label>
              <select
                v-model="selectedCompetition"
                :class="cn(
                  'px-3 py-1.5 rounded-lg text-sm border font-medium',
                  isDarkMode
                    ? 'bg-purple-500/20 border-purple-500/30 text-purple-300'
                    : 'bg-purple-50 border-purple-300 text-purple-700'
                )"
              >
                <option v-for="comp in competitions" :key="comp.id" :value="comp.id">
                  {{ comp.short_name }} ({{ comp.match_count }} matches)
                </option>
              </select>
            </div>

            <!-- Team Filter -->
            <div class="flex items-center gap-2">
              <label :class="cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')">Team:</label>
              <select
                v-model="selectedTeam"
                :class="cn(
                  'px-3 py-1.5 rounded-lg text-sm border',
                  isDarkMode
                    ? 'bg-[#12141f] border-white/10 text-white'
                    : 'bg-white border-gray-300'
                )"
              >
                <option value="all">All Teams</option>
                <option v-for="team in dataStatus?.all_teams" :key="team" :value="team">
                  {{ team }}
                </option>
              </select>
            </div>

            <!-- Show only cached toggle -->
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                v-model="showOnlyCached"
                class="w-4 h-4 rounded border-gray-300"
              />
              <span :class="cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')">
                Cached only
              </span>
            </label>

            <!-- Stats -->
            <div class="flex items-center gap-4 ml-auto">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
                <span :class="cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')">
                  {{ dataStatus?.cached_matches || 0 }} cached
                </span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-amber-400"></div>
                <span :class="cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')">
                  {{ dataStatus?.missing_matches || 0 }} missing
                </span>
              </div>
              <button
                @click="loadStatus"
                :disabled="isLoading"
                :class="cn(
                  'p-1.5 rounded-lg transition-colors',
                  isDarkMode ? 'hover:bg-white/10' : 'hover:bg-gray-200'
                )"
              >
                <Icon name="lucide:refresh-cw" :class="cn('w-4 h-4', isLoading ? 'animate-spin' : '')" />
              </button>
            </div>
          </div>

          <!-- Error -->
          <div
            v-if="error"
            :class="cn('mx-4 mt-4 p-3 rounded-lg text-sm', isDarkMode ? 'bg-red-500/20 text-red-300' : 'bg-red-50 text-red-600')"
          >
            {{ error }}
          </div>

          <!-- StatsBomb Status Banner -->
          <div
            v-if="dataStatus && !dataStatus.statsbomb_available"
            :class="cn('mx-4 mt-4 p-3 rounded-lg text-sm flex items-center gap-2', isDarkMode ? 'bg-amber-500/20 text-amber-300' : 'bg-amber-50 text-amber-700')"
          >
            <Icon name="lucide:alert-triangle" class="w-4 h-4" />
            <span>StatsBomb not installed. Run <code class="px-1 py-0.5 rounded bg-black/20">pip install statsbombpy</code> to fetch new data.</span>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto p-4">
            <!-- Loading -->
            <div v-if="isLoading && !dataStatus" class="text-center py-12">
              <Icon name="lucide:loader-2" class="w-8 h-8 animate-spin mx-auto mb-3 text-purple-400" />
              <p :class="cn('text-sm', isDarkMode ? 'text-white/60' : 'text-gray-500')">Loading match data...</p>
            </div>

            <!-- Match List by Stage -->
            <div v-else-if="dataStatus" class="space-y-6">
              <div v-for="group in matchesByStage" :key="group.stage">
                <h3
                  :class="cn(
                    'text-sm font-semibold uppercase tracking-wider mb-3',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )"
                >
                  {{ group.stage }}
                </h3>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div
                    v-for="match in group.matches"
                    :key="match.match_id"
                    :class="cn(
                      'flex items-center justify-between p-3 rounded-xl border transition-colors',
                      match.is_complete
                        ? isDarkMode ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-emerald-50 border-emerald-200'
                        : isDarkMode ? 'bg-[#0a0b14] border-white/5' : 'bg-gray-50 border-gray-200'
                    )"
                  >
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <Icon
                          :name="match.is_complete ? 'lucide:check-circle' : 'lucide:circle-dashed'"
                          :class="cn('w-4 h-4 flex-shrink-0', match.is_complete ? 'text-emerald-400' : 'text-white/30')"
                        />
                        <span class="font-medium text-sm truncate">{{ match.label }}</span>
                      </div>
                      <div :class="cn('text-xs mt-1 ml-6', isDarkMode ? 'text-white/40' : 'text-gray-500')">
                        {{ match.date }}
                        <span v-if="match.is_complete" class="ml-2">{{ match.total_size_kb }}KB</span>
                      </div>
                    </div>
                    
                    <div class="flex items-center gap-1 ml-2">
                      <button
                        v-if="!match.is_complete && dataStatus.statsbomb_available"
                        @click="fetchMatch(match.match_id)"
                        :disabled="fetchingMatch === match.match_id"
                        :class="cn(
                          'p-2 rounded-lg transition-colors',
                          isDarkMode ? 'hover:bg-emerald-500/20 text-emerald-400' : 'hover:bg-emerald-100 text-emerald-600'
                        )"
                        title="Download"
                      >
                        <Icon
                          :name="fetchingMatch === match.match_id ? 'lucide:loader-2' : 'lucide:download'"
                          :class="cn('w-4 h-4', fetchingMatch === match.match_id ? 'animate-spin' : '')"
                        />
                      </button>
                      
                      <button
                        v-if="match.is_complete"
                        @click="deleteMatch(match.match_id)"
                        :disabled="deletingMatch === match.match_id"
                        :class="cn(
                          'p-2 rounded-lg transition-colors',
                          isDarkMode ? 'hover:bg-red-500/20 text-red-400' : 'hover:bg-red-100 text-red-600'
                        )"
                        title="Delete"
                      >
                        <Icon
                          :name="deletingMatch === match.match_id ? 'lucide:loader-2' : 'lucide:trash-2'"
                          :class="cn('w-4 h-4', deletingMatch === match.match_id ? 'animate-spin' : '')"
                        />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty state -->
              <div v-if="filteredMatches.length === 0" class="text-center py-12">
                <Icon name="lucide:inbox" :class="cn('w-12 h-12 mx-auto mb-3', isDarkMode ? 'text-white/20' : 'text-gray-300')" />
                <p :class="cn('text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')">
                  No matches found for this filter
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div
            :class="cn(
              'flex items-center justify-between p-4 border-t',
              isDarkMode ? 'border-white/10 bg-[#0a0b14]' : 'border-gray-200 bg-gray-50'
            )"
          >
            <p :class="cn('text-xs', isDarkMode ? 'text-white/40' : 'text-gray-400')">
              Data source: StatsBomb Open Data (CC BY-NC-SA 4.0)
            </p>
            
            <div class="flex items-center gap-2">
              <button
                v-if="dataStatus?.statsbomb_available && dataStatus?.missing_matches > 0"
                @click="fetchAllMissing"
                :disabled="fetchingAll"
                :class="cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  isDarkMode
                    ? 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30'
                    : 'bg-purple-100 hover:bg-purple-200 text-purple-700'
                )"
              >
                <Icon v-if="fetchingAll" name="lucide:loader-2" class="w-4 h-4 animate-spin inline mr-2" />
                {{ fetchingAll ? 'Fetching...' : 'Fetch All Missing' }}
              </button>
              
              <button
                @click="emit('close')"
                :class="cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  isDarkMode
                    ? 'bg-white/10 hover:bg-white/20'
                    : 'bg-gray-200 hover:bg-gray-300'
                )"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
