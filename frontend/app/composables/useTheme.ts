export function useTheme() {
  const colorMode = useColorMode()
  
  const isDarkMode = computed(() => colorMode.value === 'dark')
  
  const toggleTheme = () => {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
  }
  
  return {
    isDarkMode,
    toggleTheme,
    colorMode,
  }
}
