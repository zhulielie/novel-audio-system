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
  console.log(`[Router] 导航请求: ${from.path} -> ${to.path}`)
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  if (userStore.token) {
    if (to.path === '/login') {
      console.log('[Router] 已登录，阻止访问登录页，重定向到 /')
      next({ path: '/' })
      return
    }

    // 首次登录或刷新后侧边栏为空，生成菜单
    if (permissionStore.routes.length === 0) {
      try {
        console.log('[Router] 首次加载，生成侧边栏菜单')
        await permissionStore.generateRoutes(userStore.roles)
        console.log('[Router] 侧边栏菜单生成完成，路由数:', permissionStore.routes.length)
      } catch (error) {
        console.error('[Router] 生成菜单失败:', error)
      }
    }

    console.log('[Router] 允许导航到:', to.path)
    next()
  } else {
    if (whiteList.includes(to.path)) {
      console.log('[Router] 白名单路径，允许访问:', to.path)
      next()
    } else {
      console.log('[Router] 未登录，重定向到登录页，原目标:', to.path)
      next(`/login?redirect=${to.path}`)
    }
  }
})

router.afterEach((to, from) => {
  console.log(`[Router] 导航完成: ${from.path} -> ${to.path}`)
})

router.onError((error) => {
  console.error('[Router] 导航错误:', error)
})

export default router
