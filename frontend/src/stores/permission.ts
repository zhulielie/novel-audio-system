import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemApi, type Menu } from '@/services/systemApi'
import { constantRoutes, asyncRoutes } from '@/router/routes'

export const usePermissionStore = defineStore('permission', () => {
  // 状态
  const routes = ref<any[]>([])
  const addRoutes = ref<any[]>([])
  const menus = ref<Menu[]>([])

  // 方法
  const setRoutes = (newRoutes: any[]) => {
    addRoutes.value = newRoutes
    routes.value = constantRoutes.concat(newRoutes)
  }

  const setMenus = (menuList: Menu[]) => {
    menus.value = menuList
  }

  // 根据角色过滤路由
  const filterAsyncRoutes = (routes: any[], roles: string[]) => {
    const res: any[] = []

    routes.forEach(route => {
      const tmp = { ...route }
      if (hasPermission(roles, tmp)) {
        if (tmp.children) {
          tmp.children = filterAsyncRoutes(tmp.children, roles)
        }
        res.push(tmp)
      }
    })

    return res
  }

  // 检查是否有权限
  const hasPermission = (roles: string[], route: any) => {
    if (route.meta && route.meta.roles) {
      return roles.some(role => route.meta.roles.includes(role))
    } else {
      return true
    }
  }

  // 生成路由
  const generateRoutes = async (roles: string[]) => {
    try {
      // 获取用户菜单
      const userMenus = await systemApi.getUserMenus()
      setMenus(userMenus)

      // 转换菜单为路由
      const accessedRoutes = convertMenusToRoutes(userMenus)
      
      setRoutes(accessedRoutes)
      return accessedRoutes
    } catch (error) {
      console.error('Generate routes error:', error)
      return []
    }
  }

  // 将菜单转换为路由
  const convertMenusToRoutes = (menus: Menu[]): any[] => {
    const routes: any[] = []

    menus.forEach(menu => {
      if (menu.menu_type === 'M' || menu.menu_type === 'C') {
        const route: any = {
          path: menu.path || `/${menu.name}`,
          name: menu.name,
          component: getComponent(menu.component),
          meta: {
            title: menu.name,
            icon: menu.icon,
            roles: menu.perms ? [menu.perms] : undefined,
            hidden: !menu.visible
          }
        }

        if (menu.children && menu.children.length > 0) {
          route.children = convertMenusToRoutes(menu.children)
        }

        routes.push(route)
      }
    })

    return routes
  }

  // 动态获取组件
  const getComponent = (componentPath?: string) => {
    if (!componentPath) return () => import('@/views/404.vue')
    
    // 处理布局组件
    if (componentPath === 'Layout') {
      return () => import('@/layout/AdminLayout.vue')
    }

    // 处理业务组件
    const componentMap: Record<string, any> = {
      // 系统管理
      'system/users/index': () => import('@/views/system/UsersView.vue'),
      'system/roles/index': () => import('@/views/system/RolesView.vue'),
      'system/menus/index': () => import('@/views/system/MenusView.vue'),
      'system/departments/index': () => import('@/views/system/DepartmentsView.vue'),
      
      // 小说管理
      'novels/list/index': () => import('@/views/NovelsView.vue'),
      'novels/chapters/index': () => import('@/views/ChaptersView.vue'),
      'novels/sources/index': () => import('@/views/NovelSourcesView.vue'),
      
      // 爬虫管理
      'crawler/tasks/index': () => import('@/views/BatchDownloadView.vue'),
      'crawler/batch/index': () => import('@/views/BatchImportView.vue'),
      
      // 音频管理
      'audio/projects/index': () => import('@/views/AudioProjectsView.vue'),
      'audio/characters/index': () => import('@/views/GeneratorsView.vue'),
      
      // 系统监控
      'monitor/operlog/index': () => import('@/views/system/OperationLogsView.vue'),
      'monitor/logininfor/index': () => import('@/views/system/LoginLogsView.vue'),
    }

    return componentMap[componentPath] || (() => import('@/views/404.vue'))
  }

  return {
    // 状态
    routes,
    addRoutes,
    menus,
    
    // 方法
    setRoutes,
    setMenus,
    filterAsyncRoutes,
    hasPermission,
    generateRoutes,
    convertMenusToRoutes
  }
})
