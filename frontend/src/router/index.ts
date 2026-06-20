import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'
import { constantRoutes } from './routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: constantRoutes,
  scrollBehavior: () => ({ left: 0, top: 0 })
})

// 白名单路由
const whiteList = ['/login', '/404', '/401']

// Demo 阶段路由守卫：未登录跳登录页；已登录时生成侧边栏菜单
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  if (userStore.token) {
    if (to.path === '/login') {
      next({ path: '/' })
      return
    }

    // 首次登录或刷新后侧边栏为空，生成菜单
    if (permissionStore.routes.length === 0) {
      try {
        await permissionStore.generateRoutes(userStore.roles)
      } catch (error) {
        console.error('Failed to generate routes in guard:', error)
      }
    }

    next()
  } else {
    if (whiteList.includes(to.path)) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
    }
  }
})

export default router
