import { api } from './api'

export interface User {
  id?: number
  username: string
  nickname?: string
  email?: string
  phone?: string
  password?: string
  is_active?: boolean
  roles?: number[]
  roles_info?: Array<{
    id: number
    name: string
    code: string
  }>
  created_at?: string
  updated_at?: string
}

export interface Role {
  id?: number
  name: string
  code: string
  description?: string
  data_scope?: number
  is_active?: boolean
  menu_ids?: number[]
  department_ids?: number[]
  created_at?: string
  updated_at?: string
}

export interface Menu {
  id?: number
  name: string
  parent?: number
  menu_type: 'M' | 'C' | 'F'
  path?: string
  component?: string
  perms?: string
  icon?: string
  sort?: number
  visible?: boolean
  is_frame?: boolean
  is_cache?: boolean
  children?: Menu[]
  created_at?: string
  updated_at?: string
}

export interface Department {
  id?: number
  name: string
  code: string
  parent?: number
  level?: number
  sort?: number
  leader?: number
  phone?: string
  email?: string
  description?: string
  is_active?: boolean
  children?: Department[]
  created_at?: string
  updated_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user_info: User
}

export interface ApiResponse<T> {
  count?: number
  results?: T[]
  data?: T
}

export const systemApi = {
  // 认证相关
  login: (data: LoginRequest): Promise<LoginResponse> =>
    api.post('/system/auth/login/', data),

  logout: (refresh_token: string): Promise<void> =>
    api.post('/system/auth/logout/', { refresh_token }),

  refreshToken: (refresh_token: string): Promise<{ access_token: string }> =>
    api.post('/system/auth/refresh/', { refresh_token }),

  // 用户管理
  getUsers: (params?: any): Promise<ApiResponse<User>> =>
    api.get('/system/users/', { params }),

  getUser: (id: number): Promise<User> =>
    api.get(`/system/users/${id}/`),

  createUser: (data: User): Promise<User> =>
    api.post('/system/users/', data),

  updateUser: (id: number, data: Partial<User>): Promise<User> =>
    api.put(`/system/users/${id}/`, data),

  deleteUser: (id: number): Promise<void> =>
    api.delete(`/system/users/${id}/`),

  resetUserPassword: (id: number, password?: string): Promise<{ message: string }> =>
    api.post(`/system/users/${id}/reset_password/`, { password }),

  getUserProfile: (): Promise<User> =>
    api.get('/system/users/profile/'),

  updateUserProfile: (data: Partial<User>): Promise<User> =>
    api.put('/system/users/update_profile/', data),

  changePassword: (data: { old_password: string; new_password: string; confirm_password: string }): Promise<{ message: string }> =>
    api.post('/system/users/change_password/', data),

  // 角色管理
  getRoles: (params?: any): Promise<ApiResponse<Role>> =>
    api.get('/system/roles/', { params }),

  getRole: (id: number): Promise<Role> =>
    api.get(`/system/roles/${id}/`),

  createRole: (data: Role): Promise<Role> =>
    api.post('/system/roles/', data),

  updateRole: (id: number, data: Partial<Role>): Promise<Role> =>
    api.put(`/system/roles/${id}/`, data),

  deleteRole: (id: number): Promise<void> =>
    api.delete(`/system/roles/${id}/`),

  getRoleMenus: (id: number): Promise<{ menu_ids: number[] }> =>
    api.get(`/system/roles/${id}/menus/`),

  assignRoleMenus: (id: number, menu_ids: number[]): Promise<{ message: string }> =>
    api.post(`/system/roles/${id}/assign_menus/`, { menu_ids }),

  // 菜单管理
  getMenus: (params?: any): Promise<ApiResponse<Menu>> =>
    api.get('/system/menus/', { params }),

  getMenu: (id: number): Promise<Menu> =>
    api.get(`/system/menus/${id}/`),

  createMenu: (data: Menu): Promise<Menu> =>
    api.post('/system/menus/', data),

  updateMenu: (id: number, data: Partial<Menu>): Promise<Menu> =>
    api.put(`/system/menus/${id}/`, data),

  deleteMenu: (id: number): Promise<void> =>
    api.delete(`/system/menus/${id}/`),

  getMenuTree: (): Promise<Menu[]> =>
    api.get('/system/menus/tree/'),

  getUserMenus: (): Promise<Menu[]> =>
    api.get('/system/menus/user_menus/'),

  // 部门管理
  getDepartments: (params?: any): Promise<ApiResponse<Department>> =>
    api.get('/system/departments/', { params }),

  getDepartment: (id: number): Promise<Department> =>
    api.get(`/system/departments/${id}/`),

  createDepartment: (data: Department): Promise<Department> =>
    api.post('/system/departments/', data),

  updateDepartment: (id: number, data: Partial<Department>): Promise<Department> =>
    api.put(`/system/departments/${id}/`, data),

  deleteDepartment: (id: number): Promise<void> =>
    api.delete(`/system/departments/${id}/`),

  getDepartmentTree: (): Promise<Department[]> =>
    api.get('/system/departments/tree/'),

  // 字典管理
  getDicts: (params?: any): Promise<ApiResponse<any>> =>
    api.get('/system/dicts/', { params }),

  getDictData: (params?: any): Promise<ApiResponse<any>> =>
    api.get('/system/dict-data/', { params }),

  getDictDataByType: (type: string): Promise<any[]> =>
    api.get('/system/dict-data/by_type/', { params: { type } }),

  // 日志管理
  getOperationLogs: (params?: any): Promise<ApiResponse<any>> =>
    api.get('/system/operation-logs/', { params }),

  getLoginLogs: (params?: any): Promise<ApiResponse<any>> =>
    api.get('/system/login-logs/', { params }),
}
