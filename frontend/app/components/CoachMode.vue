<script setup lang="ts">
import { cn } from "~/utils/cn";

interface Props {
  streamLink?: string;
}

const props = withDefaults(defineProps<Props>(), {
  streamLink: "",
});

const emit = defineEmits<{
  navigate: [screen: "landing" | "coach" | "player"];
}>();

const { isDarkMode, toggleTheme } = useTheme();

const winProbability = ref(62);
const expectedThreat = ref(0.68);
const isLive = ref(true);
const matchTime = ref(68);
const showOverlay = ref(false);

// Display stream info
const streamConnected = computed(() => !!props.streamLink);
const truncatedStreamLink = computed(() => {
  if (!props.streamLink) return "";
  return props.streamLink.length > 40
    ? props.streamLink.substring(0, 40) + "..."
    : props.streamLink;
});

// Simulate live updates
let interval: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  interval = setInterval(() => {
    if (!isLive.value) return;
    winProbability.value = Math.max(
      45,
      Math.min(75, winProbability.value + (Math.random() - 0.5) * 3)
    );
    expectedThreat.value = Math.max(
      0.3,
      Math.min(0.9, expectedThreat.value + (Math.random() - 0.5) * 0.05)
    );
    matchTime.value = Math.min(90, matchTime.value + 0.1);
  }, 2000);
});

onUnmounted(() => {
  if (interval) clearInterval(interval);
});

const alerts = [
  {
    id: 1,
    time: "68:24",
    severity: "urgent" as const,
    title: "Opposition Overload Detected",
    description:
      "Coach, the opposition is overloading the left flank. Switch to a low block 4-5-1 to secure the lead.",
    confidence: 87,
    trend: "down" as const,
    winProbDrop: -12,
  },
  {
    id: 2,
    time: "64:15",
    severity: "warning" as const,
    title: "Midfield Pressure Increasing",
    description:
      "Rice is being bypassed in midfield. Recommend subbing on Jorginho to regain possession.",
    confidence: 78,
    trend: "down" as const,
    winProbDrop: -8,
  },
  {
    id: 3,
    time: "59:42",
    severity: "positive" as const,
    title: "Momentum Shift Detected",
    description:
      "Your team has gained control in the final third. Press the advantage with forward runs.",
    confidence: 82,
    trend: "up" as const,
    winProbDrop: 6,
  },
];

const momentumData = [
  { time: 50, value: 55 },
  { time: 52, value: 58 },
  { time: 54, value: 61 },
  { time: 56, value: 64 },
  { time: 58, value: 67 },
  { time: 60, value: 70 },
  { time: 62, value: 68 },
  { time: 64, value: 64 },
  { time: 66, value: 60 },
  { time: 68, value: 62 },
];

const audioWaveHeights = Array.from({ length: 40 }, () => Math.random() * 100);
const overlayWaveHeights = Array.from(
  { length: 20 },
  () => Math.random() * 100
);
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
              <Icon name="lucide:radio" class="w-5 h-5 text-amber-400" />
              <div>
                <h1 class="font-semibold">CoachMode</h1>
                <p
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  Live Tactical Advisor
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

            <!-- Stream Connection Status -->
            <div
              v-if="streamConnected"
              :class="
                cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg border',
                  isDarkMode
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-emerald-50 border-emerald-200'
                )
              "
            >
              <Icon name="lucide:link" class="w-4 h-4 text-emerald-400" />
              <span
                :class="
                  cn(
                    'text-sm',
                    isDarkMode ? 'text-emerald-300' : 'text-emerald-700'
                  )
                "
              >
                {{ truncatedStreamLink }}
              </span>
              <span
                class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"
              ></span>
            </div>
            <div v-else class="flex items-center gap-2">
              <span
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')
                "
                >Match:</span
              >
              <select
                :class="
                  cn(
                    'border rounded-lg px-3 py-2 text-sm',
                    isDarkMode
                      ? 'bg-[#12141f] border-white/10 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  )
                "
              >
                <option>Arsenal vs Man City (Live)</option>
                <option>Chelsea vs Liverpool</option>
                <option>Spurs vs Man Utd</option>
              </select>
            </div>

            <div class="flex items-center gap-2">
              <span
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/70' : 'text-gray-600')
                "
                >Alert Threshold:</span
              >
              <select
                :class="
                  cn(
                    'border rounded-lg px-3 py-2 text-sm',
                    isDarkMode
                      ? 'bg-[#12141f] border-white/10 text-white'
                      : 'bg-white border-gray-300 text-gray-900'
                  )
                "
              >
                <option>-10% Win Prob</option>
                <option>-15% Win Prob</option>
                <option>-20% Win Prob</option>
              </select>
            </div>

            <div
              :class="
                cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg border',
                  isDarkMode
                    ? 'bg-[#12141f] border-white/10'
                    : 'bg-gray-50 border-gray-200'
                )
              "
            >
              <Icon name="lucide:volume-2" class="w-4 h-4 text-blue-400" />
              <span class="text-sm">Audio: Active</span>
            </div>

            <UiBadge
              :class="
                isDarkMode
                  ? 'bg-white/10 text-white/70 border-white/20'
                  : 'bg-red-500/20 text-red-400 border-red-500/30'
              "
            >
              <span
                :class="
                  cn(
                    'w-2 h-2 rounded-full mr-2 animate-pulse',
                    isDarkMode ? 'bg-white/70' : 'bg-red-500'
                  )
                "
              ></span>
              LIVE
            </UiBadge>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-12 gap-6 p-6">
      <!-- Left Column - Live Metrics -->
      <div class="col-span-3 space-y-6">
        <!-- Win Probability -->
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
            <h3
              :class="
                cn(
                  'font-semibold text-sm',
                  isDarkMode ? 'text-white/70' : 'text-gray-600'
                )
              "
            >
              Win Probability
            </h3>
            <UiBadge
              variant="outline"
              :class="
                cn(
                  'text-xs',
                  isDarkMode
                    ? 'border-white/20 text-white/70'
                    : 'border-emerald-500/30 text-emerald-400'
                )
              "
            >
              Live
            </UiBadge>
          </div>

          <div class="relative">
            <div class="text-5xl font-bold mb-2 text-emerald-400">
              {{ winProbability.toFixed(0) }}%
            </div>
            <div class="flex items-center gap-2 mb-4">
              <template v-if="winProbability > 60">
                <Icon
                  name="lucide:trending-up"
                  class="w-4 h-4 text-emerald-400"
                />
                <span class="text-sm text-emerald-400">Strong position</span>
              </template>
              <template v-else>
                <Icon
                  name="lucide:trending-down"
                  class="w-4 h-4 text-amber-400"
                />
                <span class="text-sm text-amber-400">Under pressure</span>
              </template>
            </div>

            <!-- Mini trend chart -->
            <div class="h-20 flex items-end gap-1">
              <div
                v-for="(point, i) in momentumData"
                :key="i"
                class="flex-1 bg-emerald-500/30 rounded-t"
                :style="{ height: `${(point.value / 100) * 100}%` }"
              ></div>
            </div>

            <div
              :class="
                cn(
                  'flex justify-between text-xs mt-2',
                  isDarkMode ? 'text-white/40' : 'text-gray-400'
                )
              "
            >
              <span>50'</span>
              <span>68'</span>
            </div>
          </div>
        </UiCard>

        <!-- Expected Threat -->
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
            <h3
              :class="
                cn(
                  'font-semibold text-sm',
                  isDarkMode ? 'text-white/70' : 'text-gray-600'
                )
              "
            >
              Expected Threat (xT)
            </h3>
            <Icon name="lucide:activity" class="w-4 h-4 text-blue-400" />
          </div>

          <div class="text-4xl font-bold mb-2 text-blue-400">
            {{ expectedThreat.toFixed(2) }}
          </div>
          <p class="text-sm text-white/50">Per possession</p>

          <div class="mt-4 h-2 bg-[#0a0b14] rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-500"
              :style="{ width: `${expectedThreat * 100}%` }"
            ></div>
          </div>
        </UiCard>

        <!-- Momentum Timeline -->
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
          <h3
            :class="
              cn(
                'font-semibold text-sm mb-4',
                isDarkMode ? 'text-white/70' : 'text-gray-600'
              )
            "
          >
            Match Timeline
          </h3>

          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <div
                :class="
                  cn(
                    'w-12 text-xs',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                68'
              </div>
              <div class="h-px flex-1 bg-red-500/30"></div>
              <Icon name="lucide:alert-triangle" class="w-3 h-3 text-red-400" />
            </div>

            <div class="flex items-center gap-3">
              <div
                :class="
                  cn(
                    'w-12 text-xs',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                64'
              </div>
              <div class="h-px flex-1 bg-amber-500/30"></div>
              <Icon
                name="lucide:trending-down"
                class="w-3 h-3 text-amber-400"
              />
            </div>

            <div class="flex items-center gap-3">
              <div
                :class="
                  cn(
                    'w-12 text-xs',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                59'
              </div>
              <div class="h-px flex-1 bg-emerald-500/30"></div>
              <Icon
                name="lucide:trending-up"
                class="w-3 h-3 text-emerald-400"
              />
            </div>

            <div class="flex items-center gap-3">
              <div
                :class="
                  cn(
                    'w-12 text-xs',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                45'
              </div>
              <div
                :class="
                  cn('h-px flex-1', isDarkMode ? 'bg-white/10' : 'bg-gray-200')
                "
              ></div>
              <div
                :class="
                  cn(
                    'w-3 h-3 rounded-full border-2',
                    isDarkMode ? 'border-white/30' : 'border-gray-300'
                  )
                "
              ></div>
            </div>
          </div>

          <div
            :class="
              cn(
                'mt-4 pt-4 border-t',
                isDarkMode ? 'border-white/10' : 'border-gray-200'
              )
            "
          >
            <div class="text-2xl font-bold text-center">
              {{ matchTime.toFixed(0) }}'
            </div>
            <div
              :class="
                cn(
                  'text-xs text-center mt-1',
                  isDarkMode ? 'text-white/50' : 'text-gray-500'
                )
              "
            >
              Match Time
            </div>
          </div>
        </UiCard>
      </div>

      <!-- Centre Column - Pitch Map -->
      <div class="col-span-5 space-y-6">
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
            <h3
              :class="
                cn(
                  'font-semibold text-sm',
                  isDarkMode ? 'text-white/70' : 'text-gray-600'
                )
              "
            >
              Pitch Overview
            </h3>
            <div class="flex gap-2">
              <UiBadge
                variant="outline"
                :class="
                  cn(
                    'text-xs',
                    isDarkMode
                      ? 'border-white/20 text-white/70'
                      : 'border-gray-300 text-gray-600'
                  )
                "
                >Heat Map</UiBadge
              >
              <UiBadge
                variant="outline"
                :class="
                  cn(
                    'text-xs',
                    isDarkMode
                      ? 'border-white/20 text-white/70'
                      : 'border-gray-300 text-gray-600'
                  )
                "
                >Positions</UiBadge
              >
            </div>
          </div>

          <!-- Pitch visualization -->
          <div
            class="aspect-[2/3] bg-gradient-to-b from-emerald-950/30 to-emerald-900/20 rounded-lg border border-emerald-500/20 relative p-4"
          >
            <!-- Pitch lines -->
            <div class="absolute inset-4 border-2 border-white/20 rounded">
              <div
                class="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-16 border-2 border-white/20 border-t-0"
              ></div>
              <div
                class="absolute bottom-0 left-1/2 -translate-x-1/2 w-24 h-16 border-2 border-white/20 border-b-0"
              ></div>
              <div
                class="absolute top-1/2 left-0 right-0 h-px bg-white/20"
              ></div>
              <div
                class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 border-2 border-white/20 rounded-full"
              ></div>
            </div>

            <!-- Overload indicator -->
            <div
              class="absolute top-1/4 left-8 w-32 h-32 bg-red-500/20 rounded-full blur-xl"
            ></div>
            <div
              class="absolute top-1/4 left-8 flex items-center gap-2 text-xs"
            >
              <Icon name="lucide:alert-triangle" class="w-4 h-4 text-red-400" />
              <span class="text-red-400 font-semibold">Overload Zone</span>
            </div>

            <!-- Player dots (opponent heavy on left) -->
            <div
              class="absolute top-1/4 left-12 w-2 h-2 bg-red-400 rounded-full"
            ></div>
            <div
              class="absolute top-1/3 left-16 w-2 h-2 bg-red-400 rounded-full"
            ></div>
            <div
              class="absolute top-1/4 left-20 w-2 h-2 bg-red-400 rounded-full"
            ></div>

            <!-- Your team -->
            <div
              class="absolute top-2/3 left-1/2 w-2 h-2 bg-emerald-400 rounded-full"
            ></div>
            <div
              class="absolute top-1/2 left-1/3 w-2 h-2 bg-emerald-400 rounded-full"
            ></div>
            <div
              class="absolute top-1/2 right-1/3 w-2 h-2 bg-emerald-400 rounded-full"
            ></div>
          </div>
        </UiCard>

        <!-- Event Feed -->
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
          <h3
            :class="
              cn(
                'font-semibold text-sm mb-4',
                isDarkMode ? 'text-white/70' : 'text-gray-600'
              )
            "
          >
            Live Event Feed
          </h3>

          <div class="space-y-3 max-h-64 overflow-y-auto">
            <div
              :class="
                cn(
                  'flex items-start gap-3 p-3 rounded-lg',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-xs w-12',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                68:24
              </div>
              <div class="flex-1">
                <div
                  :class="
                    cn(
                      'text-sm',
                      isDarkMode ? 'text-white/70' : 'text-gray-600'
                    )
                  "
                >
                  Opponent pass completed (left flank)
                </div>
                <div
                  :class="
                    cn(
                      'text-xs mt-1',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  xT: +0.12
                </div>
              </div>
            </div>

            <div
              :class="
                cn(
                  'flex items-start gap-3 p-3 rounded-lg',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-xs w-12',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                68:18
              </div>
              <div class="flex-1">
                <div
                  :class="
                    cn(
                      'text-sm',
                      isDarkMode ? 'text-white/70' : 'text-gray-600'
                    )
                  "
                >
                  Saka loses possession
                </div>
                <div class="text-xs text-amber-400 mt-1">
                  Turnover under pressure
                </div>
              </div>
            </div>

            <div
              :class="
                cn(
                  'flex items-start gap-3 p-3 rounded-lg',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-xs w-12',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                67:52
              </div>
              <div class="flex-1">
                <div
                  :class="
                    cn(
                      'text-sm',
                      isDarkMode ? 'text-white/70' : 'text-gray-600'
                    )
                  "
                >
                  Rice interception
                </div>
                <div class="text-xs text-emerald-400 mt-1">
                  Regained possession
                </div>
              </div>
            </div>

            <div
              :class="
                cn(
                  'flex items-start gap-3 p-3 rounded-lg',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-xs w-12',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                67:31
              </div>
              <div class="flex-1">
                <div
                  :class="
                    cn(
                      'text-sm',
                      isDarkMode ? 'text-white/70' : 'text-gray-600'
                    )
                  "
                >
                  Opponent shot on target
                </div>
                <div
                  :class="
                    cn(
                      'text-xs mt-1',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  xG: 0.24
                </div>
              </div>
            </div>
          </div>
        </UiCard>
      </div>

      <!-- Right Column - Tactical Alerts -->
      <div class="col-span-4 space-y-6">
        <!-- Projected Outcomes -->
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
            <div>
              <h3
                :class="
                  cn(
                    'font-semibold text-sm',
                    isDarkMode ? 'text-white/70' : 'text-gray-600'
                  )
                "
              >
                Projected Final Score
              </h3>
              <p
                :class="
                  cn(
                    'text-xs mt-1',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                If current trends continue
              </p>
            </div>
            <UiButton
              size="sm"
              variant="ghost"
              @click="showOverlay = true"
              :class="
                isDarkMode
                  ? 'text-white/70 hover:text-white'
                  : 'text-gray-600 hover:text-gray-900'
              "
            >
              <Icon name="lucide:maximize-2" class="w-4 h-4" />
            </UiButton>
          </div>

          <div class="space-y-3">
            <!-- Best Case -->
            <div
              class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Icon
                    name="lucide:trending-up"
                    class="w-4 h-4 text-emerald-400"
                  />
                  <span class="text-sm font-semibold text-emerald-400"
                    >Best Case</span
                  >
                </div>
                <UiBadge
                  variant="outline"
                  class="text-xs border-emerald-500/30 text-emerald-400"
                >
                  75% Win Prob
                </UiBadge>
              </div>
              <div class="text-3xl font-bold text-center py-2">
                <span class="text-emerald-400">3</span>
                <span class="text-white/30 mx-3">-</span>
                <span class="text-white/50">1</span>
              </div>
              <p class="text-xs text-white/60 text-center mt-2">
                If you maintain possession and press advantage
              </p>
            </div>

            <!-- Most Likely -->
            <div
              class="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Icon name="lucide:activity" class="w-4 h-4 text-blue-400" />
                  <span class="text-sm font-semibold text-blue-400"
                    >Most Likely</span
                  >
                </div>
                <UiBadge
                  variant="outline"
                  class="text-xs border-blue-500/30 text-blue-400"
                >
                  62% Win Prob
                </UiBadge>
              </div>
              <div class="text-3xl font-bold text-center py-2">
                <span class="text-blue-400">2</span>
                <span class="text-white/30 mx-3">-</span>
                <span class="text-white/50">1</span>
              </div>
              <p class="text-xs text-white/60 text-center mt-2">
                Based on current momentum and xT trends
              </p>
            </div>

            <!-- Worst Case -->
            <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Icon
                    name="lucide:trending-down"
                    class="w-4 h-4 text-red-400"
                  />
                  <span class="text-sm font-semibold text-red-400"
                    >Worst Case</span
                  >
                </div>
                <UiBadge
                  variant="outline"
                  class="text-xs border-red-500/30 text-red-400"
                >
                  38% Win Prob
                </UiBadge>
              </div>
              <div class="text-3xl font-bold text-center py-2">
                <span class="text-white/50">1</span>
                <span class="text-white/30 mx-3">-</span>
                <span class="text-red-400">2</span>
              </div>
              <p class="text-xs text-white/60 text-center mt-2">
                If left flank overload continues unchecked
              </p>
            </div>
          </div>

          <div class="mt-4 pt-4 border-t border-white/10">
            <p class="text-xs text-white/40 text-center">
              Scenarios calculated from ML models using current match state
            </p>
          </div>
        </UiCard>

        <div>
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold">Tactical Alerts</h3>
            <UiBadge
              variant="outline"
              class="text-xs border-red-500/30 text-red-400"
            >
              {{ alerts.length }} Active
            </UiBadge>
          </div>

          <div class="space-y-4">
            <UiCard
              v-for="alert in alerts"
              :key="alert.id"
              :class="
                cn(
                  'p-5',
                  alert.severity === 'urgent'
                    ? 'bg-red-500/10 border-red-500/30'
                    : alert.severity === 'warning'
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-emerald-500/10 border-emerald-500/30'
                )
              "
            >
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-2">
                  <Icon
                    v-if="alert.severity === 'urgent'"
                    name="lucide:alert-triangle"
                    class="w-5 h-5 text-red-400"
                  />
                  <Icon
                    v-else-if="alert.severity === 'warning'"
                    name="lucide:trending-down"
                    class="w-5 h-5 text-amber-400"
                  />
                  <Icon
                    v-else
                    name="lucide:trending-up"
                    class="w-5 h-5 text-emerald-400"
                  />
                  <span class="text-xs text-white/50">{{ alert.time }}</span>
                </div>
                <UiBadge
                  variant="outline"
                  :class="
                    cn(
                      'text-xs',
                      alert.severity === 'urgent'
                        ? 'border-red-500/30 text-red-400'
                        : alert.severity === 'warning'
                        ? 'border-amber-500/30 text-amber-400'
                        : 'border-emerald-500/30 text-emerald-400'
                    )
                  "
                >
                  {{
                    alert.severity === "urgent"
                      ? "URGENT"
                      : alert.severity === "warning"
                      ? "WARNING"
                      : "POSITIVE"
                  }}
                </UiBadge>
              </div>

              <h4
                :class="
                  cn(
                    'font-semibold mb-2',
                    isDarkMode ? 'text-white/70' : 'text-gray-600'
                  )
                "
              >
                {{ alert.title }}
              </h4>
              <p
                :class="
                  cn(
                    'text-sm mb-4 leading-relaxed',
                    isDarkMode ? 'text-white/60' : 'text-gray-500'
                  )
                "
              >
                {{ alert.description }}
              </p>

              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                  <Icon
                    v-if="alert.trend === 'down'"
                    name="lucide:trending-down"
                    class="w-4 h-4 text-red-400"
                  />
                  <Icon
                    v-else
                    name="lucide:trending-up"
                    class="w-4 h-4 text-emerald-400"
                  />
                  <span
                    :class="
                      cn(
                        'text-sm font-semibold',
                        alert.trend === 'down'
                          ? 'text-red-400'
                          : 'text-emerald-400'
                      )
                    "
                  >
                    {{ alert.winProbDrop > 0 ? "+" : ""
                    }}{{ alert.winProbDrop }}% Win Prob
                  </span>
                </div>
                <span class="text-xs text-white/50">
                  Confidence: {{ alert.confidence }}%
                </span>
              </div>

              <UiButton
                size="sm"
                :class="
                  cn(
                    'w-full',
                    alert.severity === 'urgent'
                      ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30'
                      : alert.severity === 'warning'
                      ? 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30'
                      : 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30'
                  )
                "
                variant="outline"
              >
                <Icon name="lucide:volume-2" class="w-4 h-4 mr-2" />
                Play Voice Alert
              </UiButton>
            </UiCard>
          </div>
        </div>

        <!-- Voice Integration -->
        <UiCard
          :class="
            cn(
              'p-6',
              isDarkMode
                ? 'bg-[#12141f] border-blue-500/30'
                : 'bg-white border-blue-500/30'
            )
          "
        >
          <div class="flex items-center gap-2 mb-4">
            <Icon name="lucide:volume-2" class="w-5 h-5 text-blue-400" />
            <h3
              :class="
                cn(
                  'font-semibold text-sm',
                  isDarkMode ? 'text-white/70' : 'text-gray-600'
                )
              "
            >
              Voice Integration
            </h3>
          </div>

          <div
            :class="
              cn(
                'rounded-lg p-4 mb-4',
                isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
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
                  class="flex-1 bg-blue-400/50 rounded-full animate-pulse"
                  :style="{
                    height: `${height}%`,
                    animationDelay: `${i * 0.05}s`,
                  }"
                ></div>
              </div>
            </div>
            <div
              :class="
                cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
              "
            >
              Commanding Voice via ElevenLabs
            </div>
          </div>

          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span :class="isDarkMode ? 'text-white/50' : 'text-gray-500'"
                >Status:</span
              >
              <span class="text-emerald-400">Active</span>
            </div>
            <div class="flex justify-between">
              <span :class="isDarkMode ? 'text-white/50' : 'text-gray-500'"
                >Voice Profile:</span
              >
              <span>Commanding</span>
            </div>
            <div class="flex justify-between">
              <span :class="isDarkMode ? 'text-white/50' : 'text-gray-500'"
                >Alerts Delivered:</span
              >
              <span>3</span>
            </div>
          </div>
        </UiCard>
      </div>
    </div>

    <!-- Match Overlay Modal -->
    <div
      v-if="showOverlay"
      class="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-6"
      @click="showOverlay = false"
    >
      <div class="max-w-7xl w-full" @click.stop>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold">Match Overlay Preview</h2>
          <UiButton
            size="sm"
            variant="ghost"
            @click="showOverlay = false"
            class="text-white/70 hover:text-white"
          >
            Close
          </UiButton>
        </div>

        <!-- Simulated Match Feed with Overlay -->
        <div
          class="relative bg-gradient-to-b from-emerald-950/50 to-blue-950/50 rounded-lg overflow-hidden aspect-video border border-white/20"
        >
          <!-- Simulated Match Background -->
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="text-6xl text-white/10">⚽ LIVE MATCH FEED</div>
          </div>

          <!-- Top Overlay Bar -->
          <div
            class="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/80 to-transparent"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2 text-sm">
                  <span class="font-bold">Arsenal</span>
                  <span class="text-2xl font-bold text-emerald-400">2</span>
                </div>
                <span class="text-white/50">-</span>
                <div class="flex items-center gap-2 text-sm">
                  <span class="text-2xl font-bold">1</span>
                  <span class="font-bold">Man City</span>
                </div>
                <div class="ml-4 px-2 py-1 bg-white/10 rounded text-xs">
                  68:24
                </div>
              </div>

              <UiBadge class="bg-red-500/20 text-red-400 border-red-500/30">
                <span
                  class="w-2 h-2 bg-red-500 rounded-full mr-2 animate-pulse"
                ></span>
                LIVE
              </UiBadge>
            </div>
          </div>

          <!-- Corner Metrics Overlay - Top Right -->
          <div class="absolute top-4 right-4 space-y-2">
            <div
              class="bg-black/80 backdrop-blur-sm border border-emerald-500/30 rounded-lg p-3 min-w-[160px]"
            >
              <div class="text-xs text-white/50 mb-1">Win Probability</div>
              <div class="text-2xl font-bold text-emerald-400">62%</div>
              <div class="flex items-center gap-1 mt-1">
                <Icon
                  name="lucide:trending-up"
                  class="w-3 h-3 text-emerald-400"
                />
                <span class="text-xs text-emerald-400">Strong</span>
              </div>
            </div>

            <div
              class="bg-black/80 backdrop-blur-sm border border-blue-500/30 rounded-lg p-3 min-w-[160px]"
            >
              <div class="text-xs text-white/50 mb-1">Expected Threat</div>
              <div class="text-2xl font-bold text-blue-400">0.68</div>
              <div class="h-1 bg-white/10 rounded-full mt-2">
                <div class="h-full bg-blue-400 rounded-full w-[68%]"></div>
              </div>
            </div>
          </div>

          <!-- Alert Overlay - Bottom Centre -->
          <div
            class="absolute bottom-4 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4"
          >
            <div
              class="bg-red-500/95 backdrop-blur-sm border border-red-400 rounded-lg p-4 shadow-2xl"
            >
              <div class="flex items-start gap-3">
                <div
                  class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0"
                >
                  <Icon
                    name="lucide:alert-triangle"
                    class="w-6 h-6 text-white"
                  />
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs font-semibold text-white/80"
                      >URGENT TACTICAL ALERT</span
                    >
                    <UiBadge
                      class="bg-white/20 text-white border-white/30 text-xs"
                    >
                      87% Confidence
                    </UiBadge>
                  </div>
                  <p class="text-white font-semibold mb-2">
                    Coach, the opposition is overloading the left flank. Switch
                    to a low block 4-5-1 to secure the lead.
                  </p>
                  <div class="flex items-center gap-2">
                    <Icon name="lucide:volume-2" class="w-4 h-4 text-white" />
                    <div class="flex gap-0.5 items-end h-4 flex-1">
                      <div
                        v-for="(height, i) in overlayWaveHeights"
                        :key="i"
                        class="flex-1 bg-white/60 rounded-full animate-pulse"
                        :style="{
                          height: `${height}%`,
                          animationDelay: `${i * 0.05}s`,
                        }"
                      ></div>
                    </div>
                    <span class="text-xs text-white/80">Playing now...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Projected Scores Overlay - Bottom Left -->
          <div class="absolute bottom-4 left-4">
            <div
              class="bg-black/80 backdrop-blur-sm border border-white/20 rounded-lg p-3 space-y-2"
            >
              <div class="text-xs text-white/50 mb-2">
                Projected Final Score
              </div>
              <div class="flex items-center gap-3">
                <div class="flex flex-col items-center">
                  <span class="text-xs text-emerald-400 mb-1">Best</span>
                  <div class="text-lg font-bold">
                    <span class="text-emerald-400">3</span>
                    <span class="text-white/30 mx-1">-</span>
                    <span class="text-white/50">1</span>
                  </div>
                </div>
                <div class="flex flex-col items-center">
                  <span class="text-xs text-blue-400 mb-1">Likely</span>
                  <div class="text-lg font-bold">
                    <span class="text-blue-400">2</span>
                    <span class="text-white/30 mx-1">-</span>
                    <span class="text-white/50">1</span>
                  </div>
                </div>
                <div class="flex flex-col items-center">
                  <span class="text-xs text-red-400 mb-1">Worst</span>
                  <div class="text-lg font-bold">
                    <span class="text-white/50">1</span>
                    <span class="text-white/30 mx-1">-</span>
                    <span class="text-red-400">2</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <p class="text-sm text-white/60 text-center mt-4">
          This overlay appears on the coach's tablet or second screen during the
          match, providing real-time insights without disrupting their view of
          play.
        </p>
      </div>
    </div>
  </div>
</template>
