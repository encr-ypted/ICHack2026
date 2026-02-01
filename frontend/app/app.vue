<script setup lang="ts">
type Screen = "landing" | "coach" | "player";

const currentScreen = ref<Screen>("landing");

const handleNavigation = (screen: Screen) => {
  currentScreen.value = screen;
};
</script>

<template>
  <div>
    <MarketingLanding
      v-if="currentScreen === 'landing'"
      @navigate="handleNavigation"
    />
    <CoachMode
      v-else-if="currentScreen === 'coach'"
      @navigate="handleNavigation"
    />
    <PlayerMode
      v-else-if="currentScreen === 'player'"
      @navigate="handleNavigation"
    />
  </div>
</template>
