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

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()
  
  if (userStore.token) {
    if (to.path === '/login') {
      // 已登录且要跳转的页面是登录页
      next({ path: '/' })
    } else {
      // 判断当前用户是否已拉取完user_info信息
      if (!userStore.userInfo.id) {
        try {
          // 获取用户信息
          await userStore.getUserInfo()
          
          // 根据用户角色生成可访问的路由表
          const accessRoutes = await permissionStore.generateRoutes(userStore.roles)
          
          // 动态添加可访问路由表
          accessRoutes.forEach(route => {
            router.addRoute(route)
          })
          
          // hack方法 确保addRoutes已完成
          next({ ...to, replace: true })
        } catch (error) {
          // 移除token并跳转登录页
          await userStore.logout()
          next(`/login?redirect=${to.path}`)
        }
      } else {
        next()
      }
    }
  } else {
    // 没有token
    if (whiteList.indexOf(to.path) !== -1) {
      // 在免登录白名单，直接进入
      next()
    } else {
      // 否则全部重定向到登录页
      next(`/login?redirect=${to.path}`)
    }
  }
})

export default router
