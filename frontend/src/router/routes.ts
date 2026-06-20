import type { RouteRecordRaw } from 'vue-router'

// 常量路由 - 不需要权限验证 (暂时包含所有路由)
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: '/redirect',
    component: () => import('@/layout/AdminLayout.vue'),
    meta: { hidden: true },
    children: [
      {
        path: '/redirect/:path(.*)',
        component: () => import('@/views/redirect/index.vue')
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/system/LoginView.vue'),
    meta: { hidden: true }
  },
  {
    path: '/404',
    name: '404',
    component: () => import('@/views/error-page/404.vue'),
    meta: { hidden: true }
  },
  {
    path: '/401',
    name: '401',
    component: () => import('@/views/error-page/401.vue'),
    meta: { hidden: true }
  },
  {
    path: '/',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '首页', icon: 'House', affix: true }
      }
    ]
  },
  {
    path: '/profile',
    component: () => import('@/layout/AdminLayout.vue'),
    meta: { hidden: true },
    children: [
      {
        path: '',
        name: 'Profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: '个人中心', icon: 'User' }
      }
    ]
  },
  // Demo 聚焦：隐藏系统管理
  // {
  //   path: '/system',
  //   component: () => import('@/layout/AdminLayout.vue'),
  //   redirect: '/system/users',
  //   name: 'System',
  //   meta: {
  //     title: '系统管理',
  //     icon: 'Setting'
  //   },
  //   children: [
  //     { path: 'users', name: 'SystemUsers', component: () => import('@/views/system/UsersView.vue'), meta: { title: '用户管理', icon: 'User' } },
  //     { path: 'roles', name: 'SystemRoles', component: () => import('@/views/system/RolesView.vue'), meta: { title: '角色管理', icon: 'UserFilled' } },
  //     { path: 'menus', name: 'SystemMenus', component: () => import('@/views/system/MenusView.vue'), meta: { title: '菜单管理', icon: 'Menu' } },
  //     { path: 'departments', name: 'SystemDepartments', component: () => import('@/views/system/DepartmentsView.vue'), meta: { title: '部门管理', icon: 'OfficeBuilding' } }
  //   ]
  // },
  {
    path: '/crawler',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/crawler/integrated',
    name: 'Crawler',
    meta: {
      title: '爬虫管理',
      icon: 'Connection'
    },
    children: [
      {
        path: 'integrated',
        name: 'CrawlerIntegrated',
        component: () => import('@/views/IntegratedCrawlerView.vue'),
        meta: {
          title: '智能爬虫',
          icon: 'MagicStick'
        }
      }
    ]
  },
  {
    path: '/novels',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/novels/list',
    name: 'Novels',
    meta: {
      title: '小说管理',
      icon: 'Reading'
    },
    children: [
      {
        path: 'list',
        name: 'NovelsList',
        component: () => import('@/views/NovelsView.vue'),
        meta: {
          title: '小说列表',
          icon: 'List'
        }
      },
      {
        path: 'chapters',
        name: 'NovelsChapters',
        component: () => import('@/views/ChaptersView.vue'),
        meta: {
          title: '章节管理',
          icon: 'Document'
        }
      },
      // Demo 聚焦：隐藏来源管理
      // {
      //   path: 'sources',
      //   name: 'NovelsSources',
      //   component: () => import('@/views/NovelSourcesView.vue'),
      //   meta: {
      //     title: '来源管理',
      //     icon: 'Link'
      //   }
      // },
      {
        path: ':id',
        name: 'NovelDetail',
        component: () => import('@/views/NovelDetailView.vue'),
        meta: {
          title: '小说详情',
          hidden: true
        }
      },
      {
        path: ':id/read',
        name: 'NovelReader',
        component: () => import('@/views/NovelReaderView.vue'),
        meta: {
          title: '阅读小说',
          hidden: true
        }
      }
    ]
  },
  {
    path: '/tts',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/tts/playground',
    name: 'TTS',
    meta: {
      title: '语音合成',
      icon: 'Microphone'
    },
    children: [
      // Demo 聚焦：隐藏 VoxCPM 调参
      // {
      //   path: 'playground',
      //   name: 'TTSPlayground',
      //   component: () => import('@/views/TTSVoxCPMPlayground.vue'),
      //   meta: {
      //     title: 'VoxCPM 调参',
      //     icon: 'SetUp'
      //   }
      // },
      {
        path: 'synthesize',
        name: 'TTSSynthesize',
        component: () => import('@/views/TTSGenerateView.vue'),
        meta: {
          title: 'TTS 合成',
          icon: 'Microphone'
        }
      },
      {
        path: 'voices',
        name: 'TTSVoices',
        component: () => import('@/views/TTSVoicesView.vue'),
        meta: {
          title: '语音资源',
          icon: 'Collection'
        }
      },
      {
        path: 'engines',
        name: 'TTSEngines',
        component: () => import('@/views/TTSEnginesView.vue'),
        meta: {
          title: '引擎配置',
          icon: 'SetUp'
        }
      }
    ]
  }
]

// 异步路由 - 需要权限验证
export const asyncRoutes: RouteRecordRaw[] = [
  {
    path: '/system',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/system/users',
    name: 'System',
    meta: {
      title: '系统管理',
      icon: 'Setting',
      roles: ['admin']
    },
    children: [
      {
        path: 'users',
        name: 'SystemUsers',
        component: () => import('@/views/system/UsersView.vue'),
        meta: {
          title: '用户管理',
          icon: 'User',
          roles: ['admin']
        }
      },
      {
        path: 'roles',
        name: 'SystemRoles',
        component: () => import('@/views/system/RolesView.vue'),
        meta: {
          title: '角色管理',
          icon: 'UserFilled',
          roles: ['admin']
        }
      },
      {
        path: 'menus',
        name: 'SystemMenus',
        component: () => import('@/views/system/MenusView.vue'),
        meta: {
          title: '菜单管理',
          icon: 'Menu',
          roles: ['admin']
        }
      },
      {
        path: 'departments',
        name: 'SystemDepartments',
        component: () => import('@/views/system/DepartmentsView.vue'),
        meta: {
          title: '部门管理',
          icon: 'OfficeBuilding',
          roles: ['admin']
        }
      }
    ]
  },
  {
    path: '/novels',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/novels/list',
    name: 'Novels',
    meta: {
      title: '小说管理',
      icon: 'Reading'
    },
    children: [
      {
        path: 'list',
        name: 'NovelsList',
        component: () => import('@/views/NovelsView.vue'),
        meta: {
          title: '小说列表',
          icon: 'List'
        }
      },
      {
        path: 'chapters',
        name: 'NovelsChapters',
        component: () => import('@/views/ChaptersView.vue'),
        meta: {
          title: '章节管理',
          icon: 'Document'
        }
      },
      {
        path: 'sources',
        name: 'NovelsSources',
        component: () => import('@/views/NovelSourcesView.vue'),
        meta: {
          title: '来源管理',
          icon: 'Link'
        }
      },
      {
        path: ':id',
        name: 'NovelDetail',
        component: () => import('@/views/NovelDetailView.vue'),
        meta: {
          title: '小说详情',
          hidden: true
        }
      },
      {
        path: ':id/read',
        name: 'NovelReader',
        component: () => import('@/views/NovelReaderView.vue'),
        meta: {
          title: '阅读小说',
          hidden: true
        }
      }
    ]
  },
  {
    path: '/crawler',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/crawler/tasks',
    name: 'Crawler',
    meta: {
      title: '爬虫管理',
      icon: 'Connection'
    },
    children: [
      {
        path: 'tasks',
        name: 'CrawlerTasks',
        component: () => import('@/views/BatchDownloadView.vue'),
        meta: {
          title: '爬虫任务',
          icon: 'Operation'
        }
      },
      {
        path: 'batch',
        name: 'CrawlerBatch',
        component: () => import('@/views/BatchImportView.vue'),
        meta: {
          title: '批量下载',
          icon: 'Download'
        }
      },
      {
        path: 'integrated',
        name: 'CrawlerIntegrated',
        component: () => import('@/views/IntegratedCrawlerView.vue'),
        meta: {
          title: '智能爬虫',
          icon: 'MagicStick'
        }
      }
    ]
  },
  {
    path: '/audio',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/audio/projects',
    name: 'Audio',
    meta: {
      title: '音频管理',
      icon: 'Headphone'
    },
    children: [
      {
        path: 'projects',
        name: 'AudioProjects',
        component: () => import('@/views/AudioProjectsView.vue'),
        meta: {
          title: '音频项目',
          icon: 'VideoPlay'
        }
      },
      {
        path: 'generators',
        name: 'AudioGenerators',
        component: () => import('@/views/GeneratorsView.vue'),
        meta: {
          title: '生成器',
          icon: 'MagicStick'
        }
      },
      {
        path: 'models',
        name: 'AudioModels',
        component: () => import('@/views/LLMModelsView.vue'),
        meta: {
          title: 'AI模型',
          icon: 'Cpu'
        }
      },
      {
        path: 'projects/:id',
        name: 'AudioProjectDetail',
        component: () => import('@/views/AudioProjectDetailView.vue'),
        meta: {
          title: '项目详情',
          hidden: true
        }
      }
    ]
  },
  {
    path: '/tts',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/tts/synthesize',
    name: 'TTS',
    meta: {
      title: '语音合成',
      icon: 'Microphone'
    },
    children: [
      {
        path: 'synthesize',
        name: 'TTSSynthesize',
        component: () => import('@/views/TTSGenerateView.vue'),
        meta: {
          title: 'TTS 合成',
          icon: 'Microphone'
        }
      },
      {
        path: 'voices',
        name: 'TTSVoices',
        component: () => import('@/views/TTSVoicesView.vue'),
        meta: {
          title: '语音资源',
          icon: 'Collection'
        }
      },
      {
        path: 'engines',
        name: 'TTSEngines',
        component: () => import('@/views/TTSEnginesView.vue'),
        meta: {
          title: '引擎配置',
          icon: 'SetUp'
        }
      },
      {
        path: 'playground',
        name: 'TTSPlayground',
        component: () => import('@/views/TTSVoxCPMPlayground.vue'),
        meta: {
          title: 'VoxCPM 调参',
          icon: 'SetUp'
        }
      }
    ]
  },
  {
    path: '/monitor',
    component: () => import('@/layout/AdminLayout.vue'),
    redirect: '/monitor/operlog',
    name: 'Monitor',
    meta: {
      title: '系统监控',
      icon: 'Monitor',
      roles: ['admin']
    },
    children: [
      {
        path: 'operlog',
        name: 'MonitorOperlog',
        component: () => import('@/views/system/OperationLogsView.vue'),
        meta: {
          title: '操作日志',
          icon: 'DocumentCopy',
          roles: ['admin']
        }
      },
      {
        path: 'logininfor',
        name: 'MonitorLogininfor',
        component: () => import('@/views/system/LoginLogsView.vue'),
        meta: {
          title: '登录日志',
          icon: 'Key',
          roles: ['admin']
        }
      }
    ]
  },
  // 404 页面必须放在最后
  { path: '/:pathMatch(.*)*', redirect: '/404', meta: { hidden: true } }
]
