import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from './user'
import { systemApi } from '@/services/systemApi'

vi.mock('@/services/systemApi', () => ({
  systemApi: {
    login: vi.fn(),
    logout: vi.fn(),
    getUserProfile: vi.fn(),
    updateUserProfile: vi.fn(),
    changePassword: vi.fn()
  }
}))

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.resetAllMocks()
  })

  it('should initialize with empty token', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.roles).toEqual([])
  })

  it('should set token and persist to localStorage', () => {
    const store = useUserStore()
    store.setToken('fake-access-token', 'fake-refresh-token')

    expect(store.token).toBe('fake-access-token')
    expect(store.refreshToken).toBe('fake-refresh-token')
    expect(localStorage.getItem('access_token')).toBe('fake-access-token')
    expect(localStorage.getItem('refresh_token')).toBe('fake-refresh-token')
  })

  it('should login and store user info', async () => {
    const mockResponse = {
      access_token: 'access',
      refresh_token: 'refresh',
      user_info: {
        id: 1,
        username: 'admin',
        roles_info: [{ code: 'admin' }]
      }
    }
    vi.mocked(systemApi.login).mockResolvedValue(mockResponse)

    const store = useUserStore()
    const result = await store.login({ username: 'admin', password: 'admin' })

    expect(systemApi.login).toHaveBeenCalledWith({ username: 'admin', password: 'admin' })
    expect(result).toEqual(mockResponse)
    expect(store.token).toBe('access')
    expect(store.userInfo.username).toBe('admin')
    expect(store.roles).toEqual(['admin'])
  })

  it('should remove token on logout', async () => {
    vi.mocked(systemApi.logout).mockResolvedValue({})

    const store = useUserStore()
    store.setToken('access', 'refresh')
    await store.logout()

    expect(store.token).toBe('')
    expect(store.refreshToken).toBe('')
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
