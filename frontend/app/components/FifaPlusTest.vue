<script setup>
import { ref } from 'vue';

// --- CONFIGURATION ---
// **IMPORTANT:** Replace this with the ACTUAL FIFA+ URL for the 2022 Final
const FIFA_PLUS_MATCH_URL = "https://www.fifa.com/fifaplus/en/watch/match/400235473"; 
const PLAYER_NAME = 'Lionel Andrés Messi Cuccittini'; 

// --- HARDCODED MOCK HIGHLIGHTS DATA ---
// This mimics the structure your backend would eventually return.
// The 'display_time_str' should be manually calculated for the FIFA+ video.
const moments = ref([
  {
    description: "GOAL SCORED (Penalty)",
    event_type: "Shot",
    highlight_score: 0.933,
    video_info: {
      base_url: FIFA_PLUS_MATCH_URL,
      display_time_str: "22:10", // Messi's first goal (Penalty)
    },
  },
  {
    description: "Goal Assist",
    event_type: "Pass",
    highlight_score: 0.970,
    video_info: {
      base_url: FIFA_PLUS_MATCH_URL,
      display_time_str: "35:35", // Key pass before Di Maria's goal
    },
  },
  {
    description: "GOAL SCORED (Extra Time)",
    event_type: "Shot",
    highlight_score: 0.850,
    video_info: {
      base_url: FIFA_PLUS_MATCH_URL,
      display_time_str: "108:00", // Messi's ET goal
    },
  },
  {
    description: "Key Pass (Chance Created)",
    event_type: "Pass",
    highlight_score: 0.605,
    video_info: {
      base_url: FIFA_PLUS_MATCH_URL,
      display_time_str: "93:57", // Late chance creation
    },
  },
  {
    description: "Pass Failed (Lost Territory)",
    event_type: "Pass",
    highlight_score: -0.402, // Lowlight
    video_info: {
      base_url: FIFA_PLUS_MATCH_URL,
      display_time_str: "34:23", // Turnover before his goal
    },
  },
  {
    description: "Failed Dribble (Dispossessed)",
    event_type: "Dribble",
    highlight_score: -0.250, // Lowlight
    video_info: {
      base_url: FIFA_PLUS_MATCH_URL,
      display_time_str: "64:06", // Lost the ball
    },
  },
]);

// Sort: Highlights first (positive, descending), then lowlights (negative, ascending)
const highlights = computed(() => 
  moments.value.filter(m => m.highlight_score > 0).sort((a, b) => b.highlight_score - a.highlight_score)
);
const lowlights = computed(() => 
  moments.value.filter(m => m.highlight_score < 0).sort((a, b) => a.highlight_score - b.highlight_score)
);

// No loading/error states needed as data is hardcoded
const loading = ref(false); 
const error = ref(null);
</script>

<template>
  <div class="p-8 bg-gray-900 min-h-screen text-white font-sans">
    <h1 class="text-4xl font-extrabold mb-2 text-center text-blue-400">
      PitchPilot: FIFA+ Integration Test
    </h1>
    <p class="text-center text-gray-400 mb-8">
      Player: <span class="text-white font-semibold">{{ PLAYER_NAME }}</span>
    </p>

    <div v-if="loading" class="text-center text-2xl text-blue-300 animate-pulse">
      Loading player highlights...
    </div>

    <div v-else-if="error" class="text-center text-2xl text-red-500">
      Error: {{ error }}
    </div>

    <div v-else class="max-w-4xl mx-auto">
      <!-- Instructions -->
      <div class="bg-gray-800 p-4 rounded-lg mb-8 text-center">
        <p class="text-gray-300">
          <strong>Frontend Test Mode:</strong> Using hardcoded data.<br />
          Click any moment to open FIFA+ in a new tab, then scrub to the indicated time.
        </p>
      </div>

      <!-- Highlights Section -->
      <div class="mb-10">
        <h2 class="text-2xl font-bold text-green-400 mb-4 flex items-center">
          <span class="mr-2">✅</span> Top Highlights
        </h2>
        <div class="space-y-4">
          <div 
            v-for="(moment, index) in highlights" 
            :key="'h-' + index" 
            class="bg-gray-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between transition-all hover:bg-gray-750 hover:shadow-xl"
          >
            <div class="mb-3 md:mb-0 md:pr-4 flex-1">
              <p class="text-xl font-semibold text-green-300">
                {{ moment.description }}
              </p>
              <p class="text-gray-400 text-sm">
                {{ moment.event_type }} | Score: <span class="text-green-400 font-mono">+{{ moment.highlight_score?.toFixed(3) }}</span>
              </p>
            </div>
            <a 
              :href="moment.video_info?.base_url" 
              target="_blank" 
              class="px-5 py-2.5 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg shadow-md flex items-center justify-center text-base whitespace-nowrap transition-colors"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {{ moment.video_info?.display_time_str }}
            </a>
          </div>
        </div>
      </div>

      <!-- Lowlights Section -->
      <div>
        <h2 class="text-2xl font-bold text-red-400 mb-4 flex items-center">
          <span class="mr-2">⚠️</span> Areas for Improvement
        </h2>
        <div class="space-y-4">
          <div 
            v-for="(moment, index) in lowlights" 
            :key="'l-' + index" 
            class="bg-gray-800 p-5 rounded-xl shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between transition-all hover:bg-gray-750 hover:shadow-xl border-l-4 border-red-500"
          >
            <div class="mb-3 md:mb-0 md:pr-4 flex-1">
              <p class="text-xl font-semibold text-red-300">
                {{ moment.description }}
              </p>
              <p class="text-gray-400 text-sm">
                {{ moment.event_type }} | Score: <span class="text-red-400 font-mono">{{ moment.highlight_score?.toFixed(3) }}</span>
              </p>
            </div>
            <a 
              :href="moment.video_info?.base_url" 
              target="_blank" 
              class="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-md flex items-center justify-center text-base whitespace-nowrap transition-colors"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              {{ moment.video_info?.display_time_str }}
            </a>
          </div>
        </div>
      </div>

      <!-- Stats Summary -->
      <div class="mt-10 bg-gray-800 p-6 rounded-xl">
        <h3 class="text-xl font-bold text-blue-400 mb-4">Session Summary</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <p class="text-3xl font-bold text-white">{{ moments.length }}</p>
            <p class="text-gray-400 text-sm">Total Moments</p>
          </div>
          <div>
            <p class="text-3xl font-bold text-green-400">{{ highlights.length }}</p>
            <p class="text-gray-400 text-sm">Highlights</p>
          </div>
          <div>
            <p class="text-3xl font-bold text-red-400">{{ lowlights.length }}</p>
            <p class="text-gray-400 text-sm">Lowlights</p>
          </div>
          <div>
            <p class="text-3xl font-bold text-blue-400">
              {{ (moments.reduce((sum, m) => sum + m.highlight_score, 0)).toFixed(2) }}
            </p>
            <p class="text-gray-400 text-sm">Net Impact</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
