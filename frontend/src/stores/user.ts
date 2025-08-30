import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemApi, type User } from '@/services/systemApi'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<User>({} as User)
  const roles = ref<string[]>([])
  const permissions = ref<string[]>([])

  // 方法
  const setToken = (accessToken: string, refreshTokenValue?: string) => {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)
    
    if (refreshTokenValue) {
      refreshToken.value = refreshTokenValue
      localStorage.setItem('refresh_token', refreshTokenValue)
    }
  }

  const removeToken = () => {
    token.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  const setUserInfo = (info: User) => {
    userInfo.value = info
    localStorage.setItem('user_info', JSON.stringify(info))
    
    // 设置角色和权限
    if (info.roles_info) {
      roles.value = info.roles_info.map(role => role.code)
    }
  }

  const login = async (loginData: { username: string; password: string }) => {
    try {
      const response = await systemApi.login(loginData)
      
      setToken(response.access_token, response.refresh_token)
      setUserInfo(response.user_info)
      
      return response
    } catch (error) {
      throw error
    }
  }

  const logout = async () => {
    try {
      if (refreshToken.value) {
        await systemApi.logout(refreshToken.value)
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      removeToken()
      resetUserInfo()
    }
  }

  const resetUserInfo = () => {
    userInfo.value = {} as User
    roles.value = []
    permissions.value = []
  }

  const getUserInfo = async () => {
    try {
      const info = await systemApi.getUserProfile()
      setUserInfo(info)
      return info
    } catch (error) {
      throw error
    }
  }

  const updateProfile = async (data: Partial<User>) => {
    try {
      const updatedInfo = await systemApi.updateUserProfile(data)
      setUserInfo(updatedInfo)
      return updatedInfo
    } catch (error) {
      throw error
    }
  }

  const changePassword = async (data: {
    old_password: string
    new_password: string
    confirm_password: string
  }) => {
    try {
      return await systemApi.changePassword(data)
    } catch (error) {
      throw error
    }
  }

  // 初始化用户信息
  const initUserInfo = () => {
    const savedUserInfo = localStorage.getItem('user_info')
    if (savedUserInfo) {
      try {
        const info = JSON.parse(savedUserInfo)
        setUserInfo(info)
      } catch (error) {
        console.error('Parse user info error:', error)
        removeToken()
      }
    }
  }

  // 检查权限
  const hasRole = (role: string) => {
    return roles.value.includes(role)
  }

  const hasPermission = (permission: string) => {
    return permissions.value.includes(permission)
  }

  const hasAnyRole = (roleList: string[]) => {
    return roleList.some(role => roles.value.includes(role))
  }

  const hasAnyPermission = (permissionList: string[]) => {
    return permissionList.some(permission => permissions.value.includes(permission))
  }

  // 初始化
  if (token.value) {
    initUserInfo()
  }

  return {
    // 状态
    token,
    refreshToken,
    userInfo,
    roles,
    permissions,
    
    // 方法
    setToken,
    removeToken,
    setUserInfo,
    login,
    logout,
    resetUserInfo,
    getUserInfo,
    updateProfile,
    changePassword,
    initUserInfo,
    hasRole,
    hasPermission,
    hasAnyRole,
    hasAnyPermission
  }
})
