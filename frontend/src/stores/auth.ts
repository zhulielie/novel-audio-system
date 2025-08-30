import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/services/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const login = async (credentials: { username: string; password: string }) => {
    loading.value = true
    try {
      const response = await authAPI.login(credentials)
      const data = response.data || response
      token.value = data.access
      user.value = data.user
      localStorage.setItem('token', data.access)
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.message || error.response?.data?.error || '登录失败'
      }
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      user.value = null
      token.value = null
      localStorage.removeItem('token')
    }
  }

  const fetchProfile = async () => {
    if (!token.value) return

    try {
      const response = await authAPI.getProfile()
      user.value = response.data || response
    } catch (error) {
      console.error('Fetch profile error:', error)
      // 如果获取用户信息失败，清除认证状态
      logout()
    }
  }

  const initAuth = async () => {
    if (token.value) {
      await fetchProfile()
    }
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    logout,
    fetchProfile,
    initAuth,
  }
})