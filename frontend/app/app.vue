<script setup lang="ts">
type Screen = "landing" | "coach" | "player";

const currentScreen = ref<Screen>("landing");
const streamLink = ref<string>("");

const handleNavigation = (screen: Screen, link?: string) => {
  currentScreen.value = screen;
  if (link) {
    streamLink.value = link;
  }
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
      :stream-link="streamLink"
      @navigate="handleNavigation"
    />
    <PlayerMode
      v-else-if="currentScreen === 'player'"
      @navigate="handleNavigation"
    />
  </div>
</template>
