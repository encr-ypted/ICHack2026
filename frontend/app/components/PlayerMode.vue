<script setup lang="ts">
import { cn } from "~/utils/cn";

const emit = defineEmits<{
  navigate: [screen: "landing" | "coach" | "player"];
}>();

const { isDarkMode, toggleTheme } = useTheme();

const criticalMoments = [
  {
    id: 1,
    time: "72:15",
    title: "Turnover in Final Third",
    description:
      "Lost possession under pressure from two defenders. Should have played a simple pass backwards to maintain possession.",
    videoUrl: "https://youtube.com/watch?v=example",
    timestamp: "4335",
    impact: "negative" as const,
    xTLost: -0.18,
  },
  {
    id: 2,
    time: "68:42",
    title: "Successful Progressive Run",
    description:
      "Excellent dribble through midfield created space for the attack. Good scanning before receiving the ball.",
    videoUrl: "https://youtube.com/watch?v=example",
    timestamp: "4122",
    impact: "positive" as const,
    xTGained: 0.24,
  },
  {
    id: 3,
    time: "61:28",
    title: "Missed Finishing Opportunity",
    description:
      "Shot from edge of box flew over the bar. Need to focus on composure and technique in high-pressure situations.",
    videoUrl: "https://youtube.com/watch?v=example",
    timestamp: "3688",
    impact: "negative" as const,
    xTLost: -0.31,
  },
  {
    id: 4,
    time: "54:10",
    title: "Key Defensive Recovery",
    description:
      "Outstanding recovery run to win back possession in dangerous area. Shows excellent work rate and tactical awareness.",
    videoUrl: "https://youtube.com/watch?v=example",
    timestamp: "3250",
    impact: "positive" as const,
    xTGained: 0.15,
  },
  {
    id: 5,
    time: "48:33",
    title: "Poor First Touch",
    description:
      "Heavy first touch gave away possession in transition. Work on receiving under pressure with better body positioning.",
    videoUrl: "https://youtube.com/watch?v=example",
    timestamp: "2913",
    impact: "negative" as const,
    xTLost: -0.12,
  },
];

const weeklyDrills = [
  {
    day: "Monday",
    title: "Scanning Drill: 360° Awareness",
    objective: "Improve pre-reception scanning to identify pressure",
    reps: "4 sets × 8 minutes",
    success: "Complete 30+ scans per set with accurate decision-making",
  },
  {
    day: "Tuesday",
    title: "First Touch Under Pressure",
    objective: "Develop composure receiving with defenders close",
    reps: "3 sets × 10 minutes",
    success: "Maintain possession in 80% of contested situations",
  },
  {
    day: "Wednesday",
    title: "Finishing: Box Composure",
    objective: "Practice shooting technique under match pressure",
    reps: "5 sets × 15 shots",
    success: "Hit target 70%+ with proper technique",
  },
  {
    day: "Thursday",
    title: "Recovery Run Conditioning",
    objective: "Build stamina for defensive transitions",
    reps: "6 sprints × 40 metres",
    success: "Complete all sprints under 6 seconds",
  },
  {
    day: "Friday",
    title: "Decision Making: Pass or Dribble",
    objective: "Improve choice-making in final third",
    reps: "4 sets × 12 minutes",
    success: "Make correct decision 85%+ of the time",
  },
  {
    day: "Saturday",
    title: "Small-Sided Game: Apply Learning",
    objective: "Implement all weekly focuses in match context",
    reps: "3 games × 15 minutes",
    success: "Demonstrate improved scanning and composure",
  },
  {
    day: "Sunday",
    title: "Recovery & Video Review",
    objective: "Rest and analyse your progress",
    reps: "Light stretching + film session",
    success: "Identify 3 areas of improvement for next week",
  },
];

const audioWaveHeights = Array.from({ length: 40 }, () => Math.random() * 100);
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
                >Player:</span
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
                <option>Marcus Rashford</option>
                <option>Bukayo Saka</option>
                <option>Phil Foden</option>
              </select>
            </div>

            <div class="flex items-center gap-2">
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
                <option>Arsenal vs Man City - 20 Jan 2026</option>
                <option>Chelsea vs Arsenal - 13 Jan 2026</option>
                <option>Arsenal vs Spurs - 06 Jan 2026</option>
              </select>
            </div>

            <UiButton class="bg-emerald-500 hover:bg-emerald-600 text-white">
              Generate Report
            </UiButton>
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
          <div class="flex items-center gap-2 mb-4">
            <div
              class="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center"
            >
              <span class="text-xl font-bold">MR</span>
            </div>
            <div>
              <div class="font-semibold">Marcus Rashford</div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Forward · #10
              </div>
            </div>
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
            <p
              :class="
                cn(
                  'text-sm leading-relaxed mb-4',
                  isDarkMode ? 'text-white/80' : 'text-gray-700'
                )
              "
            >
              Marcus, you were
              <span
                :class="
                  cn(
                    'font-semibold',
                    isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                  )
                "
                >elite in transition</span
              >
              today. Your progressive runs in the first half created significant
              threat, and your work rate on defensive recovery was outstanding.
            </p>
            <p
              :class="
                cn(
                  'text-sm leading-relaxed',
                  isDarkMode ? 'text-white/80' : 'text-gray-700'
                )
              "
            >
              However, your decision-making in the final third needs work. You
              lost possession
              <span
                :class="
                  cn(
                    'font-semibold',
                    isDarkMode ? 'text-amber-400' : 'text-amber-600'
                  )
                "
                >3 times under pressure</span
              >—each time choosing the risky option when a simple pass was
              available. Let's focus on composure this week.
            </p>
          </div>

          <div class="flex items-center gap-2 text-xs text-white/50 mb-4">
            <Icon name="lucide:volume-2" class="w-3 h-3" />
            <span>Analysed by Claude 3.5 Sonnet</span>
          </div>

          <UiButton
            variant="outline"
            class="w-full border-purple-500/30 text-purple-400 hover:bg-purple-500/10"
          >
            <Icon name="lucide:play" class="w-4 h-4 mr-2" />
            Play Full Audio Summary
          </UiButton>
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
          <h3 class="font-semibold mb-4">Key Metrics</h3>

          <div class="grid grid-cols-2 gap-4">
            <div
              :class="
                cn(
                  'rounded-lg p-4',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-emerald-50'
                )
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
                8.2
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Impact Score
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:trending-up"
                  class="w-3 h-3 text-emerald-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    )
                  "
                  >+1.4 vs avg</span
                >
              </div>
            </div>

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
                0.52
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                xT Generated
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:trending-up"
                  class="w-3 h-3 text-emerald-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    )
                  "
                  >Top 15%</span
                >
              </div>
            </div>

            <div
              :class="
                cn(
                  'rounded-lg p-4',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-amber-50'
                )
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
                3
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Turnovers (Pressure)
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:trending-down"
                  class="w-3 h-3 text-amber-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                  >Needs work</span
                >
              </div>
            </div>

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
                78%
              </div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Pass Accuracy (Final Third)
              </div>
              <div class="flex items-center gap-1 mt-2">
                <Icon
                  name="lucide:trending-down"
                  class="w-3 h-3 text-amber-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs',
                      isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                  >Below avg</span
                >
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
          <h3 class="font-semibold mb-4">Performance Breakdown</h3>

          <div class="space-y-4">
            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Attacking</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    )
                  "
                  >8.5/10</span
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
                <div class="h-full bg-emerald-500 w-[85%]"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Defensive Work Rate</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    )
                  "
                  >8.8/10</span
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
                <div class="h-full bg-emerald-500 w-[88%]"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Decision Making</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                  >6.2/10</span
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
                <div class="h-full bg-amber-500 w-[62%]"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Technical Execution</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      isDarkMode ? 'text-amber-400' : 'text-amber-600'
                    )
                  "
                  >7.1/10</span
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
                <div class="h-full bg-amber-500 w-[71%]"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-sm mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Positioning</span
                >
                <span
                  :class="
                    cn(
                      'font-semibold',
                      isDarkMode ? 'text-white' : 'text-gray-900'
                    )
                  "
                  >7.8/10</span
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
                <div class="h-full bg-blue-500 w-[78%]"></div>
              </div>
            </div>
          </div>
        </UiCard>
      </div>

      <!-- Centre Column - Video Highlights -->
      <div class="col-span-5 space-y-6">
        <div>
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="font-semibold text-lg">
                Video-Synchronised Highlights
              </h3>
              <p
                :class="
                  cn('text-sm', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                5 most critical moments identified
              </p>
            </div>
            <UiBadge variant="outline" class="border-red-500/30 text-red-400">
              <Icon name="lucide:video" class="w-3 h-3 mr-1" />
              YouTube Linked
            </UiBadge>
          </div>

          <div class="space-y-4">
            <UiCard
              v-for="moment in criticalMoments"
              :key="moment.id"
              :class="
                cn(
                  'p-5 transition-all hover:scale-[1.02] cursor-pointer',
                  moment.impact === 'negative'
                    ? isDarkMode
                      ? 'bg-[#12141f] border-amber-500/30 hover:border-amber-500/50'
                      : 'bg-white border-amber-300 hover:border-amber-400'
                    : isDarkMode
                    ? 'bg-[#12141f] border-emerald-500/30 hover:border-emerald-500/50'
                    : 'bg-white border-emerald-300 hover:border-emerald-400'
                )
              "
            >
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div
                    v-if="moment.impact === 'negative'"
                    class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0"
                  >
                    <Icon
                      name="lucide:alert-circle"
                      class="w-5 h-5 text-amber-400"
                    />
                  </div>
                  <div
                    v-else
                    class="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0"
                  >
                    <Icon
                      name="lucide:check-circle-2"
                      class="w-5 h-5 text-emerald-400"
                    />
                  </div>
                  <div>
                    <div class="font-semibold">{{ moment.title }}</div>
                    <div
                      :class="
                        cn(
                          'text-xs mt-1',
                          isDarkMode ? 'text-white/50' : 'text-gray-500'
                        )
                      "
                    >
                      {{ moment.time }}
                    </div>
                  </div>
                </div>
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
                  {{
                    moment.impact === "negative"
                      ? `${moment.xTLost?.toFixed(2)} xT`
                      : `+${moment.xTGained?.toFixed(2)} xT`
                  }}
                </UiBadge>
              </div>

              <p
                :class="
                  cn(
                    'text-sm mb-4 leading-relaxed',
                    isDarkMode ? 'text-white/70' : 'text-gray-600'
                  )
                "
              >
                {{ moment.description }}
              </p>

              <!-- Video Preview Placeholder -->
              <div
                :class="
                  cn(
                    'rounded-lg aspect-video mb-4 border relative overflow-hidden',
                    isDarkMode
                      ? 'bg-[#0a0b14] border-white/10'
                      : 'bg-gray-100 border-gray-200'
                  )
                "
              >
                <div
                  class="absolute inset-0 bg-gradient-to-br from-emerald-900/20 to-blue-900/20"
                ></div>
                <div class="absolute inset-0 flex items-center justify-center">
                  <div
                    class="w-16 h-16 rounded-full bg-white/10 backdrop-blur flex items-center justify-center"
                  >
                    <Icon
                      name="lucide:play"
                      :class="
                        cn(
                          'w-8 h-8 ml-1',
                          isDarkMode ? 'text-white/70' : 'text-gray-700'
                        )
                      "
                    />
                  </div>
                </div>
                <div
                  :class="
                    cn(
                      'absolute bottom-3 right-3 px-2 py-1 rounded text-xs font-medium',
                      isDarkMode
                        ? 'bg-black/70 text-white'
                        : 'bg-white/90 text-gray-900 border border-gray-300'
                    )
                  "
                >
                  {{ moment.time }}
                </div>
              </div>

              <div class="flex gap-2">
                <UiButton
                  size="sm"
                  :class="
                    cn(
                      'flex-1',
                      moment.impact === 'negative'
                        ? isDarkMode
                          ? 'bg-amber-500/30 hover:bg-amber-500/40 text-amber-300 border border-amber-500/50'
                          : 'bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-300'
                        : isDarkMode
                        ? 'bg-emerald-500/30 hover:bg-emerald-500/40 text-emerald-300 border border-emerald-500/50'
                        : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300'
                    )
                  "
                  variant="outline"
                >
                  <Icon name="lucide:play" class="w-3 h-3 mr-2" />
                  Jump to Timestamp
                </UiButton>
                <UiButton
                  size="sm"
                  variant="outline"
                  :class="
                    isDarkMode
                      ? 'border-white/20 text-white/70 hover:bg-white/5'
                      : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                  "
                >
                  <Icon name="lucide:external-link" class="w-3 h-3" />
                </UiButton>
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
          <div class="flex items-center gap-2 mb-4">
            <Icon name="lucide:target" class="w-5 h-5 text-emerald-400" />
            <div>
              <h3 class="font-semibold">1-Week Development Mission</h3>
              <p
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                Focus: Scanning Under Pressure
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <UiCard
              v-for="(drill, index) in weeklyDrills"
              :key="index"
              :class="
                cn(
                  'p-4 hover:border-emerald-500/30 transition-all',
                  isDarkMode
                    ? 'bg-[#0a0b14] border-white/10'
                    : 'bg-emerald-50 border-emerald-200'
                )
              "
            >
              <div class="flex items-start justify-between mb-2">
                <div>
                  <div
                    :class="
                      cn(
                        'font-semibold text-sm',
                        isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                      )
                    "
                  >
                    {{ drill.day }}
                  </div>
                  <div class="text-sm font-semibold mt-1">
                    {{ drill.title }}
                  </div>
                </div>
                <div
                  :class="
                    cn(
                      'w-6 h-6 rounded border-2 flex-shrink-0',
                      isDarkMode ? 'border-white/20' : 'border-emerald-300'
                    )
                  "
                ></div>
              </div>

              <div class="space-y-2 text-xs">
                <div>
                  <span :class="isDarkMode ? 'text-white/50' : 'text-gray-500'"
                    >Objective:
                  </span>
                  <span
                    :class="isDarkMode ? 'text-white/70' : 'text-gray-700'"
                    >{{ drill.objective }}</span
                  >
                </div>
                <div>
                  <span :class="isDarkMode ? 'text-white/50' : 'text-gray-500'"
                    >Reps:
                  </span>
                  <span
                    :class="isDarkMode ? 'text-white/70' : 'text-gray-700'"
                    >{{ drill.reps }}</span
                  >
                </div>
                <div>
                  <span :class="isDarkMode ? 'text-white/50' : 'text-gray-500'"
                    >Success:
                  </span>
                  <span
                    :class="isDarkMode ? 'text-white/70' : 'text-gray-700'"
                    >{{ drill.success }}</span
                  >
                </div>
              </div>
            </UiCard>
          </div>

          <UiButton
            class="w-full mt-4 bg-emerald-500 hover:bg-emerald-600 text-white"
          >
            <Icon name="lucide:check-circle-2" class="w-4 h-4 mr-2" />
            Start Development Mission
          </UiButton>
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

        <!-- Progress Tracking -->
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
          <h3 class="font-semibold mb-4 text-sm">Season Progress</h3>

          <div class="space-y-3">
            <div>
              <div class="flex justify-between text-xs mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Matches Analysed</span
                >
                <span class="font-semibold">12/38</span>
              </div>
              <div
                :class="
                  cn(
                    'h-1.5 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div class="h-full bg-emerald-500 w-[32%]"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Drills Completed</span
                >
                <span class="font-semibold">45/84</span>
              </div>
              <div
                :class="
                  cn(
                    'h-1.5 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div class="h-full bg-blue-500 w-[54%]"></div>
              </div>
            </div>

            <div>
              <div class="flex justify-between text-xs mb-2">
                <span :class="isDarkMode ? 'text-white/70' : 'text-gray-600'"
                  >Improvement Areas Addressed</span
                >
                <span class="font-semibold">7/10</span>
              </div>
              <div
                :class="
                  cn(
                    'h-1.5 rounded-full overflow-hidden',
                    isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-200'
                  )
                "
              >
                <div class="h-full bg-purple-500 w-[70%]"></div>
              </div>
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
            <div class="flex items-center justify-between">
              <span
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
                >Overall Rating Trend</span
              >
              <div class="flex items-center gap-1">
                <Icon
                  name="lucide:trending-up"
                  class="w-3 h-3 text-emerald-400"
                />
                <span
                  :class="
                    cn(
                      'text-xs font-semibold',
                      isDarkMode ? 'text-emerald-400' : 'text-emerald-600'
                    )
                  "
                  >+1.2</span
                >
              </div>
            </div>
          </div>
        </UiCard>
      </div>
    </div>
  </div>
</template>
