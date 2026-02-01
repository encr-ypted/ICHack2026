<script setup lang="ts">
import { cn } from "~/utils/cn";
import { ref, watch, onMounted } from "vue";

const props = defineProps<{
  matchId: number | null;
  teams: string[];
  isDarkMode: boolean;
}>();

const API_BASE = "http://localhost:8000";

// Active tab
const activeTab = ref<'momentum' | 'score' | 'setpieces' | 'passing' | 'pressing' | 'substitutions'>('momentum');

// Data refs
const momentumData = ref<any>(null);
const scoreImpactData = ref<any>(null);
const setPieceData = ref<any>(null);
const passingNetworkData = ref<any>(null);
const pressingData = ref<any>(null);
const substitutionData = ref<any>(null);

const isLoading = ref(false);
const selectedTeam = ref<string>('');

// Fetch functions
async function fetchMomentum() {
  if (!props.matchId) return;
  isLoading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/match/momentum?match_id=${props.matchId}&interval_minutes=5`);
    if (res.ok) momentumData.value = await res.json();
  } catch (e) { console.error(e); }
  finally { isLoading.value = false; }
}

async function fetchScoreImpact() {
  if (!props.matchId) return;
  isLoading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/match/score-impact?match_id=${props.matchId}`);
    if (res.ok) scoreImpactData.value = await res.json();
  } catch (e) { console.error(e); }
  finally { isLoading.value = false; }
}

async function fetchSetPieces() {
  if (!props.matchId) return;
  isLoading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/match/set-pieces?match_id=${props.matchId}`);
    if (res.ok) setPieceData.value = await res.json();
  } catch (e) { console.error(e); }
  finally { isLoading.value = false; }
}

async function fetchPassingNetwork() {
  if (!props.matchId) return;
  isLoading.value = true;
  try {
    const team = selectedTeam.value || props.teams[0] || '';
    const res = await fetch(`${API_BASE}/api/match/passing-network?match_id=${props.matchId}&team=${encodeURIComponent(team)}&min_passes=2`);
    if (res.ok) passingNetworkData.value = await res.json();
  } catch (e) { console.error(e); }
  finally { isLoading.value = false; }
}

async function fetchPressing() {
  if (!props.matchId) return;
  isLoading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/match/pressing?match_id=${props.matchId}`);
    if (res.ok) pressingData.value = await res.json();
  } catch (e) { console.error(e); }
  finally { isLoading.value = false; }
}

async function fetchSubstitutions() {
  if (!props.matchId) return;
  isLoading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/match/substitutions?match_id=${props.matchId}`);
    if (res.ok) substitutionData.value = await res.json();
  } catch (e) { console.error(e); }
  finally { isLoading.value = false; }
}

// Fetch data when tab changes
watch(activeTab, (tab) => {
  if (tab === 'momentum' && !momentumData.value) fetchMomentum();
  else if (tab === 'score' && !scoreImpactData.value) fetchScoreImpact();
  else if (tab === 'setpieces' && !setPieceData.value) fetchSetPieces();
  else if (tab === 'passing' && !passingNetworkData.value) fetchPassingNetwork();
  else if (tab === 'pressing' && !pressingData.value) fetchPressing();
  else if (tab === 'substitutions' && !substitutionData.value) fetchSubstitutions();
});

watch(() => props.matchId, () => {
  // Reset data when match changes
  momentumData.value = null;
  scoreImpactData.value = null;
  setPieceData.value = null;
  passingNetworkData.value = null;
  pressingData.value = null;
  substitutionData.value = null;
  fetchMomentum();
});

watch(() => props.teams, (teams) => {
  if (teams.length > 0 && !selectedTeam.value) {
    selectedTeam.value = teams[0];
  }
}, { immediate: true });

watch(selectedTeam, () => {
  if (activeTab.value === 'passing') {
    passingNetworkData.value = null;
    fetchPassingNetwork();
  }
});

onMounted(() => {
  if (props.matchId) fetchMomentum();
});

// Helper to get max dominance for scaling
function getMaxDominance(data: any) {
  if (!data?.momentum) return 1;
  let max = 0;
  for (const interval of data.momentum) {
    for (const team in interval.teams) {
      max = Math.max(max, interval.teams[team].dominance_score || 0);
    }
  }
  return max || 1;
}
</script>

<template>
  <div class="space-y-4">
    <!-- Tab Navigation -->
    <div class="flex flex-wrap gap-2">
      <button
        v-for="tab in [
          { id: 'momentum', label: 'Momentum', icon: 'lucide:activity' },
          { id: 'score', label: 'Score Impact', icon: 'lucide:target' },
          { id: 'setpieces', label: 'Set Pieces', icon: 'lucide:flag' },
          { id: 'passing', label: 'Passing Network', icon: 'lucide:share-2' },
          { id: 'pressing', label: 'Pressing', icon: 'lucide:zap' },
          { id: 'substitutions', label: 'Substitutions', icon: 'lucide:users' },
        ]"
        :key="tab.id"
        @click="activeTab = tab.id as any"
        :class="cn(
          'px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2',
          activeTab === tab.id
            ? isDarkMode ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-cyan-100 text-cyan-700 border border-cyan-300'
            : isDarkMode ? 'bg-white/5 text-white/60 hover:text-white hover:bg-white/10' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        )"
      >
        <Icon :name="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" :class="cn('p-8 rounded-xl text-center', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
      <Icon name="lucide:loader-2" class="w-8 h-8 animate-spin mx-auto mb-2 text-cyan-400" />
      <p :class="isDarkMode ? 'text-white/50' : 'text-gray-500'">Loading analytics...</p>
    </div>

    <!-- Momentum Tracker -->
    <div v-else-if="activeTab === 'momentum'" class="space-y-4">
      <div v-if="momentumData" class="space-y-4">
        <div :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
          <h4 class="font-semibold mb-4 flex items-center gap-2">
            <Icon name="lucide:activity" class="w-4 h-4 text-cyan-400" />
            Match Momentum ({{ momentumData.interval_minutes }}-min intervals)
          </h4>
          
          <!-- Momentum Chart -->
          <div class="space-y-2">
            <div v-for="interval in momentumData.momentum?.slice(0, 18)" :key="interval.interval_start" class="flex items-center gap-2 text-xs">
              <span :class="cn('w-12 text-right', isDarkMode ? 'text-white/50' : 'text-gray-500')">{{ interval.interval_start }}'</span>
              <div class="flex-1 flex h-6 gap-1">
                <div
                  v-for="team in momentumData.teams"
                  :key="team"
                  :class="cn('rounded transition-all', team === momentumData.teams[0] ? 'bg-blue-500' : 'bg-red-500')"
                  :style="{ width: `${Math.min(100, (interval.teams[team]?.dominance_score || 0) / getMaxDominance(momentumData) * 100)}%`, opacity: 0.7 }"
                  :title="`${team}: ${interval.teams[team]?.dominance_score?.toFixed(1) || 0}`"
                ></div>
              </div>
            </div>
          </div>

          <!-- Legend -->
          <div class="flex justify-center gap-6 mt-4 text-xs">
            <div v-for="(team, idx) in momentumData.teams" :key="team" class="flex items-center gap-2">
              <div :class="cn('w-3 h-3 rounded', idx === 0 ? 'bg-blue-500' : 'bg-red-500')"></div>
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">{{ team }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else :class="cn('p-8 text-center', isDarkMode ? 'text-white/50' : 'text-gray-500')">
        Select a match to view momentum data
      </div>
    </div>

    <!-- Score Impact Analysis -->
    <div v-else-if="activeTab === 'score'" class="space-y-4">
      <div v-if="scoreImpactData" class="space-y-4">
        <!-- Goal Timeline -->
        <div v-if="scoreImpactData.goal_times?.length" :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
          <h4 class="font-semibold mb-3 flex items-center gap-2">
            <Icon name="lucide:flag" class="w-4 h-4 text-emerald-400" />
            Goals
          </h4>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="(goal, i) in scoreImpactData.goal_times"
              :key="i"
              :class="cn('px-3 py-1 rounded-full text-xs font-medium', isDarkMode ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-100 text-emerald-700')"
            >
              {{ goal.minute }}' - {{ goal.team }}
            </div>
          </div>
        </div>

        <!-- Stats by Game State -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div v-for="state in ['leading', 'drawing', 'trailing']" :key="state" :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
            <h4 :class="cn('font-semibold mb-3 capitalize', state === 'leading' ? 'text-emerald-400' : state === 'trailing' ? 'text-red-400' : 'text-amber-400')">
              When {{ state }}
            </h4>
            <div v-for="team in scoreImpactData.teams" :key="team" class="mb-3 last:mb-0">
              <p :class="cn('text-xs font-medium mb-1', isDarkMode ? 'text-white/70' : 'text-gray-600')">{{ team }}</p>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>Passes: {{ scoreImpactData.stats_by_state[state]?.[team]?.passes || 0 }}</div>
                <div>Accuracy: {{ scoreImpactData.stats_by_state[state]?.[team]?.pass_accuracy || '0%' }}</div>
                <div>Shots: {{ scoreImpactData.stats_by_state[state]?.[team]?.shots || 0 }}</div>
                <div>xT: {{ scoreImpactData.stats_by_state[state]?.[team]?.xT?.toFixed(2) || 0 }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Set Pieces -->
    <div v-else-if="activeTab === 'setpieces'" class="space-y-4">
      <div v-if="setPieceData" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="team in setPieceData.teams" :key="team" :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
          <h4 class="font-semibold mb-4">{{ team }}</h4>
          
          <div class="space-y-3">
            <!-- Corners -->
            <div class="flex items-center justify-between">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Corners</span>
              <div class="text-right">
                <span class="font-semibold">{{ setPieceData.set_pieces[team]?.corners?.total || 0 }}</span>
                <span :class="cn('text-xs ml-2', isDarkMode ? 'text-white/50' : 'text-gray-500')">
                  ({{ setPieceData.set_pieces[team]?.corners?.shots || 0 }} shots, {{ setPieceData.set_pieces[team]?.corners?.goals || 0 }} goals)
                </span>
              </div>
            </div>
            
            <!-- Free Kicks -->
            <div class="flex items-center justify-between">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Free Kicks</span>
              <div class="text-right">
                <span class="font-semibold">{{ setPieceData.set_pieces[team]?.free_kicks?.total || 0 }}</span>
                <span :class="cn('text-xs ml-2', isDarkMode ? 'text-white/50' : 'text-gray-500')">
                  ({{ setPieceData.set_pieces[team]?.free_kicks?.shots || 0 }} shots)
                </span>
              </div>
            </div>
            
            <!-- Throw-ins -->
            <div class="flex items-center justify-between">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Throw-ins</span>
              <span class="font-semibold">{{ setPieceData.set_pieces[team]?.throw_ins?.total || 0 }}</span>
            </div>
            
            <!-- Penalties -->
            <div class="flex items-center justify-between">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Penalties</span>
              <span class="font-semibold">
                {{ setPieceData.set_pieces[team]?.penalties?.scored || 0 }}/{{ setPieceData.set_pieces[team]?.penalties?.taken || 0 }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Passing Network -->
    <div v-else-if="activeTab === 'passing'" class="space-y-4">
      <!-- Team Selector -->
      <div class="flex items-center gap-2">
        <span :class="cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')">Team:</span>
        <select
          v-model="selectedTeam"
          :class="cn('px-3 py-1 rounded-lg text-sm', isDarkMode ? 'bg-white/10 text-white border-white/20' : 'bg-white border-gray-300')"
        >
          <option v-for="team in teams" :key="team" :value="team">{{ team }}</option>
        </select>
      </div>

      <div v-if="passingNetworkData" :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
        <h4 class="font-semibold mb-4">{{ passingNetworkData.team }} Passing Network</h4>
        
        <!-- Network Visualization (SVG) -->
        <div class="w-full overflow-hidden rounded-lg" style="aspect-ratio: 120/80;">
          <svg viewBox="0 0 120 80" class="w-full h-full" :style="{ background: isDarkMode ? '#065f46' : '#4ade80' }">
            <!-- Pitch lines -->
            <rect x="0" y="0" width="120" height="80" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.3" />
            <line x1="60" y1="0" x2="60" y2="80" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.2" />
            <circle cx="60" cy="40" r="9.15" fill="none" :stroke="isDarkMode ? '#34d399' : '#16a34a'" stroke-width="0.2" />
            
            <!-- Edges (passing connections) -->
            <line
              v-for="edge in passingNetworkData.edges"
              :key="`${edge.from}-${edge.to}`"
              :x1="passingNetworkData.nodes.find((n: any) => n.id === edge.from)?.avg_x || 60"
              :y1="passingNetworkData.nodes.find((n: any) => n.id === edge.from)?.avg_y || 40"
              :x2="passingNetworkData.nodes.find((n: any) => n.id === edge.to)?.avg_x || 60"
              :y2="passingNetworkData.nodes.find((n: any) => n.id === edge.to)?.avg_y || 40"
              :stroke="isDarkMode ? '#fff' : '#1f2937'"
              :stroke-width="0.3 + edge.weight * 1.5"
              :opacity="0.3 + edge.weight * 0.5"
            />
            
            <!-- Nodes (players) -->
            <g v-for="node in passingNetworkData.nodes" :key="node.id">
              <circle
                :cx="node.avg_x"
                :cy="node.avg_y"
                :r="2 + Math.min(node.passes / 10, 3)"
                fill="#3b82f6"
                :stroke="isDarkMode ? '#fff' : '#000'"
                stroke-width="0.3"
              />
              <text
                :x="node.avg_x"
                :y="node.avg_y + 5"
                font-size="2.5"
                :fill="isDarkMode ? '#fff' : '#1f2937'"
                text-anchor="middle"
                font-weight="500"
              >{{ node.short_name }}</text>
            </g>
          </svg>
        </div>

        <!-- Top Passers -->
        <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2">
          <div
            v-for="node in [...passingNetworkData.nodes].sort((a: any, b: any) => b.passes - a.passes).slice(0, 4)"
            :key="node.id"
            :class="cn('p-2 rounded-lg text-center', isDarkMode ? 'bg-white/5' : 'bg-white')"
          >
            <div class="font-semibold text-sm">{{ node.short_name }}</div>
            <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">{{ node.passes }} passes</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pressing Analysis -->
    <div v-else-if="activeTab === 'pressing'" class="space-y-4">
      <div v-if="pressingData" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="team in pressingData.teams" :key="team" :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')">
          <h4 class="font-semibold mb-4">{{ team }}</h4>
          
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div :class="cn('p-3 rounded-lg text-center', isDarkMode ? 'bg-white/5' : 'bg-white')">
              <div class="text-2xl font-bold text-cyan-400">{{ pressingData.pressing[team]?.total_pressures || 0 }}</div>
              <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Total Pressures</div>
            </div>
            <div :class="cn('p-3 rounded-lg text-center', isDarkMode ? 'bg-white/5' : 'bg-white')">
              <div class="text-2xl font-bold text-emerald-400">{{ pressingData.pressing[team]?.success_rate || '0%' }}</div>
              <div :class="cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')">Success Rate</div>
            </div>
          </div>

          <!-- Pressure Zones -->
          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">High Press (opp. third)</span>
              <span class="font-semibold">{{ pressingData.pressing[team]?.high_pressures || 0 }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Mid Press</span>
              <span class="font-semibold">{{ pressingData.pressing[team]?.mid_pressures || 0 }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'">Low Press (own third)</span>
              <span class="font-semibold">{{ pressingData.pressing[team]?.low_pressures || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Substitutions -->
    <div v-else-if="activeTab === 'substitutions'" class="space-y-4">
      <div v-if="substitutionData?.substitutions?.length" class="space-y-3">
        <div
          v-for="(sub, i) in substitutionData.substitutions"
          :key="i"
          :class="cn('p-4 rounded-xl', isDarkMode ? 'bg-white/5' : 'bg-gray-50')"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span :class="cn('px-2 py-1 rounded text-xs font-medium', isDarkMode ? 'bg-white/10' : 'bg-gray-200')">{{ sub.minute }}'</span>
              <span class="font-semibold">{{ sub.team }}</span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-red-400">{{ sub.player_off?.split(' ').pop() }}</span>
              <Icon name="lucide:arrow-right" class="w-4 h-4" />
              <span class="text-emerald-400">{{ sub.player_on?.split(' ').pop() }}</span>
            </div>
          </div>

          <!-- Impact Stats -->
          <div class="grid grid-cols-3 gap-4 text-xs">
            <div>
              <p :class="isDarkMode ? 'text-white/50' : 'text-gray-500'">Before (10 min)</p>
              <p>{{ sub.team_before_10min?.passes || 0 }} passes, {{ sub.team_before_10min?.shots || 0 }} shots</p>
            </div>
            <div>
              <p :class="isDarkMode ? 'text-white/50' : 'text-gray-500'">After (10 min)</p>
              <p>{{ sub.team_after_10min?.passes || 0 }} passes, {{ sub.team_after_10min?.shots || 0 }} shots</p>
            </div>
            <div>
              <p :class="isDarkMode ? 'text-white/50' : 'text-gray-500'">Impact</p>
              <p :class="(sub.impact_delta?.xT || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ (sub.impact_delta?.xT || 0) >= 0 ? '+' : '' }}{{ sub.impact_delta?.xT?.toFixed(2) || 0 }} xT
              </p>
            </div>
          </div>
        </div>
      </div>
      <div v-else :class="cn('p-8 text-center', isDarkMode ? 'text-white/50' : 'text-gray-500')">
        No substitutions in this match
      </div>
    </div>
  </div>
</template>
