import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  affiliation?: string
  research_interests: string[]
  created_at: string
}

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userInitials = computed(() => {
    if (!user.value) return 'U'
    return user.value.full_name
      .split(' ')
      .map(name => name[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  })

  // Actions
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('auth_token', newToken)
  }

  const clearToken = () => {
    token.value = null
    localStorage.removeItem('auth_token')
  }

  const setUser = (userData: User) => {
    user.value = userData
  }

  const clearUser = () => {
    user.value = null
  }

  const register = async (userData: any) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await api.auth.register(userData)
      
      // 注册成功后自动登录
      const loginResponse = await api.auth.login({
        username: userData.username,
        password: userData.password
      })
      
      setToken(loginResponse.data.access_token)
      
      // 获取用户信息
      await fetchProfile()
      
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '注册失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const login = async (credentials: any) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await api.auth.login(credentials)
      setToken(response.data.access_token)
      
      // 获取用户信息
      await fetchProfile()
      
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '登录失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    clearToken()
    clearUser()
    error.value = null
  }

  const fetchProfile = async () => {
    try {
      const response = await api.auth.getProfile()
      setUser(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取用户信息失败'
      logout()
      throw err
    }
  }

  const updateProfile = async (data: Partial<User>) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await api.auth.updateProfile(data)
      setUser(response.data)
      
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '更新资料失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const changePassword = async (passwordData: any) => {
    try {
      loading.value = true
      error.value = null
      
      await api.auth.changePassword(passwordData)
      
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '修改密码失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const initializeAuth = async () => {
    if (token.value) {
      try {
        await fetchProfile()
      } catch (err) {
        // Token可能已过期，清除本地存储
        logout()
      }
    }
  }

  return {
    // State
    user,
    token,
    loading,
    error,
    
    // Getters
    isAuthenticated,
    userInitials,
    
    // Actions
    register,
    login,
    logout,
    fetchProfile,
    updateProfile,
    changePassword,
    initializeAuth,
    setToken,
    clearToken,
    setUser,
    clearUser
  }
})

