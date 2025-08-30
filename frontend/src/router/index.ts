import { createRouter, createWebHistory } from 'vue-router'
import type { App } from 'vue'
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

// 简化的路由守卫 - 暂时允许所有访问
router.beforeEach(async (to, from, next) => {
  console.log('路由守卫:', to.path)
  
  // 暂时简化路由守卫，直接放行
  next()
  
  // TODO: 后续完善权限控制
  /*
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()
  
  if (userStore.token) {
    if (to.path === '/login') {
      next({ path: '/' })
    } else {
      if (!userStore.userInfo.id) {
        try {
          await userStore.getUserInfo()
          const accessRoutes = await permissionStore.generateRoutes(userStore.roles)
          accessRoutes.forEach(route => {
            router.addRoute(route)
          })
          next({ ...to, replace: true })
        } catch (error) {
          await userStore.logout()
          next(`/login?redirect=${to.path}`)
        }
      } else {
        next()
      }
    }
  } else {
    if (whiteList.indexOf(to.path) !== -1) {
      next()
    } else {
      next(`/login?redirect=${to.path}`)
    }
  }
  */
})

export default router
