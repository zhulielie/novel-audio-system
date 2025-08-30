import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
    },
    {
      path: '/novels',
      name: 'novels',
      component: () => import('../views/NovelsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/novels/:id',
      name: 'novel-detail',
      component: () => import('../views/NovelDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/novels/:id/read',
      name: 'novel-reader',
      component: () => import('../views/NovelReaderView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/batch-download',
      name: 'batch-download',
      component: () => import('../views/BatchDownloadView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/chapters',
      name: 'chapters',
      component: () => import('../views/ChaptersView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/audio-projects',
      name: 'audio-projects',
      component: () => import('../views/AudioProjectsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/audio-projects/:id',
      name: 'audio-project-detail',
      component: () => import('../views/AudioProjectDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/generators',
      name: 'generators',
      component: () => import('../views/GeneratorsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/llm-models',
      name: 'llm-models',
      component: () => import('../views/LLMModelsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/novel-sources',
      name: 'novel-sources',
      component: () => import('../views/NovelSourcesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/batch-import',
      name: 'batch-import',
      component: () => import('../views/BatchImportView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/integrated-crawler',
      name: 'integrated-crawler',
      component: () => import('../views/IntegratedCrawlerView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  if (authStore.token && !authStore.user) {
    await authStore.initAuth()
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 检查是否需要游客状态（如登录页）
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
    return
  }

  next()
})

export default router
