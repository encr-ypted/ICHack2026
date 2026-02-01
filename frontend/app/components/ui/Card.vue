<script setup lang="ts">
import { cn } from '~/utils/cn'

interface Props {
  class?: string
}

const props = defineProps<Props>()

const computedClass = computed(() =>
  cn('bg-card text-card-foreground flex flex-col rounded-xl border', props.class)
)
</script>

<template>
  <div :class="computedClass">
    <slot />
  </div>
</template>
