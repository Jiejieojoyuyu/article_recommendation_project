import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // State
  const isDark = ref(false)
  
  // Getters
  const theme = computed(() => isDark.value ? 'dark' : 'light')
  
  // Actions
  const setDarkMode = (dark: boolean) => {
    isDark.value = dark
    updateHtmlClass()
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }
  
  const toggleDarkMode = () => {
    setDarkMode(!isDark.value)
  }
  
  const updateHtmlClass = () => {
    const html = document.documentElement
    if (isDark.value) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }
  
  const initializeTheme = () => {
    // 检查本地存储
    const savedTheme = localStorage.getItem('theme')
    
    if (savedTheme) {
      setDarkMode(savedTheme === 'dark')
    } else {
      // 检查系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      setDarkMode(prefersDark)
    }
  }
  
  // 监听系统主题变化
  const setupSystemThemeListener = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const handleChange = (e: MediaQueryListEvent) => {
      // 只有在没有手动设置主题时才跟随系统
      if (!localStorage.getItem('theme')) {
        setDarkMode(e.matches)
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }
  
  return {
    // State
    isDark,
    
    // Getters
    theme,
    
    // Actions
    setDarkMode,
    toggleDarkMode,
    initializeTheme,
    setupSystemThemeListener
  }
})

