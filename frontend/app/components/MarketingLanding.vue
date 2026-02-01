<script setup lang="ts">
import { cn } from "~/utils/cn";

const emit = defineEmits<{
  navigate: [screen: "landing" | "coach" | "player"];
}>();

const { isDarkMode, toggleTheme } = useTheme();

const mobileMenuOpen = ref(false);
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
    <!-- Navigation -->
    <nav
      :class="
        cn(
          'fixed top-0 w-full backdrop-blur-sm border-b z-50',
          isDarkMode
            ? 'bg-[#0a0b14]/95 border-white/10'
            : 'bg-white/95 border-gray-200'
        )
      "
    >
      <div class="max-w-[1440px] mx-auto px-6 lg:px-12">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <div
            class="flex items-center gap-2 cursor-pointer"
            @click="emit('navigate', 'landing')"
          >
            <div
              class="w-8 h-8 rounded-full border-2 border-emerald-400/50 flex items-center justify-center relative"
            >
              <div class="w-3 h-3 rounded-full bg-emerald-400/30"></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <Icon name="lucide:activity" class="w-4 h-4 text-emerald-400" />
              </div>
            </div>
            <span class="font-semibold text-lg">PitchPilot</span>
          </div>

          <!-- Desktop Navigation -->
          <div class="hidden lg:flex items-center gap-8">
            <button
              @click="emit('navigate', 'landing')"
              :class="
                cn(
                  'text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              Landing Page
            </button>
            <button
              @click="emit('navigate', 'coach')"
              :class="
                cn(
                  'text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              CoachMode
            </button>
            <button
              @click="emit('navigate', 'player')"
              :class="
                cn(
                  'text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              PlayerMode
            </button>
          </div>

          <!-- Desktop CTAs + Theme Toggle -->
          <div class="hidden lg:flex items-center gap-3">
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
            <UiButton
              variant="outline"
              :class="
                isDarkMode
                  ? 'border-white/30 bg-white/5 text-white hover:bg-white/10'
                  : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
              "
            >
              View Demo
            </UiButton>
            <UiButton class="bg-emerald-500 hover:bg-emerald-600 text-white">
              Open App
            </UiButton>
          </div>

          <!-- Mobile Menu Button -->
          <button class="lg:hidden" @click="mobileMenuOpen = !mobileMenuOpen">
            <Icon v-if="mobileMenuOpen" name="lucide:x" class="w-6 h-6" />
            <Icon v-else name="lucide:menu" class="w-6 h-6" />
          </button>
        </div>

        <!-- Mobile Menu -->
        <div
          v-if="mobileMenuOpen"
          :class="
            cn(
              'lg:hidden py-4 border-t',
              isDarkMode ? 'border-white/10' : 'border-gray-200'
            )
          "
        >
          <div class="flex flex-col gap-4">
            <button
              @click="emit('navigate', 'landing')"
              :class="
                cn(
                  'text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              Landing Page
            </button>
            <button
              @click="emit('navigate', 'coach')"
              :class="
                cn(
                  'text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              CoachMode
            </button>
            <button
              @click="emit('navigate', 'player')"
              :class="
                cn(
                  'text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              PlayerMode
            </button>
            <button
              @click="toggleTheme"
              :class="
                cn(
                  'flex items-center gap-2 text-sm transition-colors',
                  isDarkMode
                    ? 'text-white/70 hover:text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )
              "
            >
              <Icon v-if="isDarkMode" name="lucide:sun" class="w-4 h-4" />
              <Icon v-else name="lucide:moon" class="w-4 h-4" />
              <span>{{ isDarkMode ? "Light Mode" : "Dark Mode" }}</span>
            </button>
            <div class="flex flex-col gap-2 pt-2">
              <UiButton
                variant="outline"
                :class="
                  cn(
                    'w-full',
                    isDarkMode
                      ? 'border-white/30 bg-white/5 text-white hover:bg-white/10'
                      : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                  )
                "
              >
                View Demo
              </UiButton>
              <UiButton
                class="bg-emerald-500 hover:bg-emerald-600 text-white w-full"
              >
                Open App
              </UiButton>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="pt-32 pb-20 px-6 lg:px-12">
      <div class="max-w-[1440px] mx-auto">
        <div class="max-w-4xl mx-auto text-center mb-12">
          <h1 class="text-5xl lg:text-7xl font-bold mb-6 tracking-tight">
            PitchPilot
          </h1>
          <p class="text-xl lg:text-2xl text-emerald-500 mb-6">
            The ML-Powered Bridge from the Touchline to the Locker Room.
          </p>
          <p
            :class="
              cn(
                'text-base lg:text-lg max-w-3xl mx-auto mb-8 leading-relaxed',
                isDarkMode ? 'text-white/70' : 'text-gray-600'
              )
            "
          >
            An end-to-end sports intelligence ecosystem that turns live match
            data into voice tactical decisions for coaches, then delivers honest
            post-match mentoring, video timestamps, and drills for players.
          </p>

          <div
            class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
          >
            <UiButton
              size="lg"
              class="bg-emerald-500 hover:bg-emerald-600 text-white px-8"
              @click="emit('navigate', 'player')"
            >
              Start the Wow Demo
              <Icon name="lucide:chevron-right" class="w-4 h-4 ml-2" />
            </UiButton>
            <UiButton
              size="lg"
              variant="outline"
              :class="
                cn(
                  'px-8',
                  isDarkMode
                    ? 'border-white/30 bg-white/5 text-white hover:bg-white/10'
                    : 'border-gray-300 bg-white text-gray-900 hover:bg-gray-50'
                )
              "
              @click="emit('navigate', 'coach')"
            >
              Explore CoachMode
            </UiButton>
          </div>

          <!-- Trust Strip -->
          <div
            :class="
              cn(
                'flex flex-wrap items-center justify-center gap-6 text-sm',
                isDarkMode ? 'text-white/50' : 'text-gray-500'
              )
            "
          >
            <div class="flex items-center gap-2">
              <Icon name="lucide:trending-up" class="w-4 h-4" />
              <span>ML</span>
            </div>
            <div class="flex items-center gap-2">
              <Icon name="lucide:volume-2" class="w-4 h-4" />
              <span>Voice</span>
            </div>
            <div class="flex items-center gap-2">
              <Icon name="lucide:shield" class="w-4 h-4" />
              <span>Security</span>
            </div>
            <div class="flex items-center gap-2">
              <Icon name="lucide:video" class="w-4 h-4" />
              <span>Video</span>
            </div>
          </div>
        </div>

        <!-- Hero Visual Split Screen -->
        <div class="grid lg:grid-cols-2 gap-6 max-w-6xl mx-auto">
          <!-- CoachMode Preview -->
          <UiCard
            :class="
              cn(
                'p-6 transition-all cursor-pointer',
                isDarkMode
                  ? 'bg-[#12141f] border-white/10 hover:border-amber-500/30'
                  : 'bg-white border-gray-200 hover:border-amber-400'
              )
            "
            @click="emit('navigate', 'coach')"
          >
            <div class="flex items-center gap-2 mb-4">
              <Icon name="lucide:radio" class="w-5 h-5 text-amber-400" />
              <span
                :class="
                  cn(
                    'font-semibold',
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  )
                "
                >CoachMode Live</span
              >
              <UiBadge
                class="bg-red-500/20 text-red-400 border-red-500/30 ml-auto"
              >
                <span
                  class="w-2 h-2 bg-red-500 rounded-full mr-1 animate-pulse"
                ></span>
                LIVE
              </UiBadge>
            </div>
            <div
              :class="
                cn(
                  'rounded-lg p-4 border border-amber-500/30',
                  isDarkMode ? 'bg-[#0a0b14]' : 'bg-gray-50'
                )
              "
            >
              <div
                :class="
                  cn(
                    'text-xs mb-2',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                TACTICAL ALERT
              </div>
              <p
                :class="
                  cn(
                    'text-sm mb-3',
                    isDarkMode ? 'text-white/80' : 'text-gray-700'
                  )
                "
              >
                Coach, the opposition is overloading the left flank. Switch to a
                low block 4-5-1 to secure the lead.
              </p>
              <div
                :class="
                  cn(
                    'flex items-center gap-2 text-xs',
                    isDarkMode ? 'text-white/50' : 'text-gray-500'
                  )
                "
              >
                <Icon name="lucide:volume-2" class="w-3 h-3" />
                <span>Commanding Voice</span>
              </div>
            </div>
            <div
              class="mt-4 h-32 bg-gradient-to-br from-emerald-500/10 to-amber-500/10 rounded-lg flex items-center justify-center"
            >
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/30' : 'text-gray-400')
                "
              >
                Pitch Map Overlay
              </div>
            </div>
          </UiCard>

          <!-- PlayerMode Preview -->
          <UiCard
            :class="
              cn(
                'p-6 transition-all cursor-pointer',
                isDarkMode
                  ? 'bg-[#12141f] border-white/10 hover:border-emerald-500/30'
                  : 'bg-white border-gray-200 hover:border-emerald-400'
              )
            "
            @click="emit('navigate', 'player')"
          >
            <div class="flex items-center gap-2 mb-4">
              <Icon name="lucide:target" class="w-5 h-5 text-emerald-400" />
              <span
                :class="
                  cn(
                    'font-semibold',
                    isDarkMode ? 'text-white' : 'text-gray-900'
                  )
                "
                >PlayerMode Review</span
              >
              <UiBadge
                class="bg-emerald-500/20 text-emerald-500 border-emerald-500/30 ml-auto"
              >
                POST-MATCH
              </UiBadge>
            </div>
            <div class="space-y-3">
              <div
                :class="
                  cn(
                    'rounded-lg p-3 border',
                    isDarkMode
                      ? 'bg-[#0a0b14] border-white/10'
                      : 'bg-gray-50 border-gray-200'
                  )
                "
              >
                <div
                  :class="
                    cn(
                      'text-xs mb-1',
                      isDarkMode ? 'text-white/50' : 'text-gray-500'
                    )
                  "
                >
                  Impact Score
                </div>
                <div class="text-2xl font-bold text-emerald-500">8.2</div>
              </div>
              <div
                :class="
                  cn(
                    'rounded-lg p-3 border',
                    isDarkMode
                      ? 'bg-[#0a0b14] border-white/10'
                      : 'bg-gray-50 border-gray-200'
                  )
                "
              >
                <div class="flex items-center gap-2 mb-2">
                  <Icon
                    name="lucide:video"
                    :class="
                      cn(
                        'w-4 h-4',
                        isDarkMode ? 'text-white/50' : 'text-gray-500'
                      )
                    "
                  />
                  <span
                    :class="
                      cn(
                        'text-sm',
                        isDarkMode ? 'text-white/80' : 'text-gray-700'
                      )
                    "
                    >Critical Moment - 72:15</span
                  >
                </div>
                <UiButton
                  size="sm"
                  variant="outline"
                  :class="
                    cn(
                      'text-xs w-full',
                      isDarkMode
                        ? 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border-emerald-500/40'
                        : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-300'
                    )
                  "
                >
                  <Icon name="lucide:play" class="w-3 h-3 mr-2" />
                  Jump to Timestamp
                </UiButton>
              </div>
            </div>
          </UiCard>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer
      :class="
        cn(
          'py-12 px-6 lg:px-12 border-t',
          isDarkMode ? 'border-white/10' : 'border-gray-200'
        )
      "
    >
      <div class="max-w-[1440px] mx-auto">
        <div
          class="flex flex-col lg:flex-row items-center justify-between gap-6"
        >
          <div class="flex items-center gap-2">
            <div
              class="w-8 h-8 rounded-full border-2 border-emerald-400/50 flex items-center justify-center relative"
            >
              <div class="w-3 h-3 rounded-full bg-emerald-400/30"></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <Icon name="lucide:activity" class="w-4 h-4 text-emerald-400" />
              </div>
            </div>
            <div>
              <div class="font-semibold">PitchPilot</div>
              <div
                :class="
                  cn('text-xs', isDarkMode ? 'text-white/50' : 'text-gray-500')
                "
              >
                The ML-Powered Bridge from the Touchline to the Locker Room
              </div>
            </div>
          </div>

          <div
            :class="
              cn(
                'flex flex-wrap items-center justify-center gap-6 text-sm',
                isDarkMode ? 'text-white/60' : 'text-gray-600'
              )
            "
          >
            <button
              @click="emit('navigate', 'landing')"
              :class="isDarkMode ? 'hover:text-white' : 'hover:text-gray-900'"
            >
              Landing Page
            </button>
            <button
              @click="emit('navigate', 'coach')"
              :class="isDarkMode ? 'hover:text-white' : 'hover:text-gray-900'"
            >
              CoachMode
            </button>
            <button
              @click="emit('navigate', 'player')"
              :class="isDarkMode ? 'hover:text-white' : 'hover:text-gray-900'"
            >
              PlayerMode
            </button>
          </div>
        </div>

        <div
          :class="
            cn(
              'mt-8 pt-6 border-t text-center text-sm',
              isDarkMode
                ? 'border-white/10 text-white/40'
                : 'border-gray-200 text-gray-400'
            )
          "
        >
          Designed for real-time coaching constraints and post-match
          development.
        </div>
      </div>
    </footer>
  </div>
</template>
