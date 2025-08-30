import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 如果响应已经是被data处理过的，直接返回
    return response.data || response
  },
  (error) => {
    if (error.response?.status === 401) {
      // 清除token并跳转到登录页
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/', credentials),
  logout: () => api.post('/auth/logout/'),
  getProfile: () => api.get('/auth/profile/'),
}

// 小说相关API
export const novelAPI = {
  getList: (params?: any) => api.get('/novels/', { params }),
  getDetail: (id: number) => api.get(`/novels/${id}/`),
  create: (data: any) => api.post('/novels/', data),
  update: (id: number, data: any) => api.put(`/novels/${id}/`, data),
  delete: (id: number) => api.delete(`/novels/${id}/`),
  getChapters: (novelId: number) => api.get(`/novels/${novelId}/chapters/`),
}

// 章节相关API
export const chapterAPI = {
  getList: (params?: any) => api.get('/chapters/', { params }),
  getDetail: (id: number) => api.get(`/chapters/${id}/`),
  create: (data: any) => api.post('/chapters/', data),
  update: (id: number, data: any) => api.put(`/chapters/${id}/`, data),
  delete: (id: number) => api.delete(`/chapters/${id}/`),
}

// 音频相关API
export const audioAPI = {
  getProjects: (params?: any) => api.get('/audio-projects/', { params }),
  getProject: (id: number) => api.get(`/audio-projects/${id}/`),
  createProject: (data: any) => api.post('/audio-projects/', data),
  updateProject: (id: number, data: any) => api.put(`/audio-projects/${id}/`, data),
  deleteProject: (id: number) => api.delete(`/audio-projects/${id}/`),
  getItems: (projectId: number) => api.get(`/audio-projects/${projectId}/items/`),
}

// LLM相关API
export const llmAPI = {
  getModels: () => api.get('/llm-models/'),
  getRequests: (params?: any) => api.get('/llm-requests/', { params }),
  createRequest: (data: any) => api.post('/llm-requests/', data),
}

// 生成器相关API
export const generatorAPI = {
  getWorkflows: (params?: any) => api.get('/generation-workflows/', { params }),
  createWorkflow: (data: any) => api.post('/generation-workflows/', data),
  getScriptTasks: (params?: any) => api.get('/script-generation-tasks/', { params }),
  createScriptTask: (data: any) => api.post('/script-generation-tasks/', data),
  getAudioTasks: (params?: any) => api.get('/audio-generation-tasks/', { params }),
  createAudioTask: (data: any) => api.post('/audio-generation-tasks/', data),
}

// 统一的API服务对象
export const apiService = {
  auth: {
    login: (credentials: { username: string; password: string }) =>
      api.post('/auth/login/', credentials),
    logout: () => api.post('/auth/logout/'),
    getProfile: () => api.get('/auth/profile/'),
    updateProfile: (data: any) => api.put('/auth/profile/', data),
    changePassword: (data: any) => api.post('/auth/change-password/', data),
    uploadAvatar: (formData: FormData) => api.post('/auth/upload-avatar/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    deleteAccount: () => api.delete('/auth/delete-account/'),
  },
  novels: {
    list: (params?: any) => api.get('/novels/', { params }),
    get: (id: number) => api.get(`/novels/${id}/`),
    create: (data: any) => api.post('/novels/', data),
    update: (id: number, data: any) => api.put(`/novels/${id}/`, data),
    delete: (id: number) => api.delete(`/novels/${id}/`),
    getChapters: (novelId: number, params?: any) => api.get(`/novels/${novelId}/chapters/`, { params }),
    getChapter: (novelId: number, chapterId: number) => api.get(`/novels/${novelId}/chapters/${chapterId}/`),
    batchImport: (novelId: number, data: any) => api.post(`/novels/${novelId}/batch_import/`, data),
    // 新增的方法
    simple_batch_import: (data: any) => api.post('/novels/simple_batch_import/', data),
    test_source: (params: any) => api.get('/novels/test_source/', { params }),
  },
  novelSources: {
    list: (params?: any) => api.get('/novel-sources/', { params }),
    get: (id: number) => api.get(`/novel-sources/${id}/`),
    create: (data: any) => api.post('/novel-sources/', data),
    update: (id: number, data: any) => api.put(`/novel-sources/${id}/`, data),
    delete: (id: number) => api.delete(`/novel-sources/${id}/`),
    analyzeWithAI: (id: number) => api.post(`/novel-sources/${id}/analyze-ai/`),
    testCrawl: (id: number) => api.post(`/novel-sources/${id}/test-crawl/`),
  },
  chapters: {
    list: (params?: any) => api.get('/chapters/', { params }),
    get: (id: number) => api.get(`/chapters/${id}/`),
    create: (data: any) => api.post('/chapters/', data),
    update: (id: number, data: any) => api.put(`/chapters/${id}/`, data),
    delete: (id: number) => api.delete(`/chapters/${id}/`),
    // 新增API方法
    getDirectory: (novelId: number) => api.get('/chapters/chapter_directory/', { params: { novel_id: novelId } }),
    formatTitles: (novelId: number, format: string) => api.get('/chapters/format_chapter_titles/', { params: { novel_id: novelId, format } }),
  },
  audioProjects: {
    list: (params?: any) => api.get('/audio-projects/', { params }),
    get: (id: number) => api.get(`/audio-projects/${id}/`),
    create: (data: any) => api.post('/audio-projects/', data),
    update: (id: number, data: any) => api.put(`/audio-projects/${id}/`, data),
    delete: (id: number) => api.delete(`/audio-projects/${id}/`),
    getItems: (projectId: number) => api.get(`/audio-projects/${projectId}/items/`),
  },
  llmModels: {
    list: () => api.get('/llm-models/'),
    get: (id: number) => api.get(`/llm-models/${id}/`),
    create: (data: any) => api.post('/llm-models/', data),
    update: (id: number, data: any) => api.put(`/llm-models/${id}/`, data),
    delete: (id: number) => api.delete(`/llm-models/${id}/`),
    test: (id: number, data: any) => api.post(`/llm-models/${id}/test/`, data),
    setDefaultAssistant: (id: number) => api.post(`/llm-models/${id}/set_default_assistant/`),
    removeDefaultAssistant: (id: number) => api.post(`/llm-models/${id}/remove_default_assistant/`),
    defaultAssistant: () => api.get('/llm-models/default_assistant/'),
  },
  llmRequests: {
    list: (params?: any) => api.get('/llm-requests/', { params }),
    create: (data: any) => api.post('/llm-requests/', data),
  },
  workflows: {
    list: (params?: any) => api.get('/workflows/', { params }),
    get: (id: number) => api.get(`/workflows/${id}/`),
    create: (data: any) => api.post('/workflows/', data),
    update: (id: number, data: any) => api.put(`/workflows/${id}/`, data),
    delete: (id: number) => api.delete(`/workflows/${id}/`),
  },
  scriptTasks: {
    list: (params?: any) => api.get('/tasks/', { params: { ...params, task_type: 'script' } }),
    get: (id: number) => api.get(`/tasks/${id}/`),
    create: (data: any) => api.post('/tasks/', data),
    update: (id: number, data: any) => api.put(`/tasks/${id}/`, data),
    delete: (id: number) => api.delete(`/tasks/${id}/`),
    start: (id: number) => api.post(`/tasks/${id}/start/`),
    pause: (id: number) => api.post(`/tasks/${id}/pause/`),
    stop: (id: number) => api.post(`/tasks/${id}/stop/`),
  },
  audioTasks: {
    list: (params?: any) => api.get('/tasks/', { params: { ...params, task_type: 'audio' } }),
    get: (id: number) => api.get(`/tasks/${id}/`),
    create: (data: any) => api.post('/tasks/', data),
    update: (id: number, data: any) => api.put(`/tasks/${id}/`, data),
    delete: (id: number) => api.delete(`/tasks/${id}/`),
    start: (id: number) => api.post(`/tasks/${id}/start/`),
    pause: (id: number) => api.post(`/tasks/${id}/pause/`),
    stop: (id: number) => api.post(`/tasks/${id}/stop/`),
  },
  // 爬虫相关API - 专门为爬虫功能设计的接口
  crawler: {
    // 智能批量导入小说
    batchImport: (data: {
      source_url: string;
      novel_title: string;
      novel_author?: string;
      source_id?: number;
      max_chapters?: number;
      start_chapter?: number;
      end_chapter?: number;
      speed?: 'slow' | 'normal' | 'fast';
    }) => api.post('/novels/simple_batch_import/', data),

    // 分析和测试小说URL
    analyzeUrl: (url: string) => api.get('/novels/test_source/', { params: { url } }),

    // 获取爬取状态统计
    getStatus: () => api.get('/novel-sources/crawl_status/'),

    // 基础爬取功能
    basicCrawl: (relationId: number) => api.post(`/novel-sources/${relationId}/crawl_basic/`),

    // 高级爬取功能
    advancedCrawl: (relationId: number, options: {
      max_chapters?: number;
      start_chapter?: number;
      overwrite_existing?: boolean;
      delay_between_requests?: number;
      retry_count?: number;
    }) => api.post(`/novel-sources/${relationId}/crawl_advanced/`, options),

    // 获取小说章节目录
    getChapterDirectory: (novelId: number) => api.get('/chapters/chapter_directory/', { params: { novel_id: novelId } }),

    // 格式化章节标题
    formatChapterTitles: (novelId: number, format: 'chinese' | 'arabic') =>
      api.get('/chapters/format_chapter_titles/', { params: { novel_id: novelId, format } }),

    // 搜索章节内容
    searchChapters: (query: string, novelId?: number) => api.get('/chapters/search/', {
      params: { q: query, novel_id: novelId }
    }),
  },

  // 批量下载相关API
  batchDownload: {
    // 创建单个下载任务
    create: (data: { source_url: string; task_name?: string }) => 
      api.post('/novels/batch-download/create/', data),
    
    // 批量创建下载任务
    batchCreate: (data: { urls: Array<{ url: string; name?: string }> }) => 
      api.post('/novels/batch-download/batch-create/', data),
    
    // 获取任务列表
    list: (params?: { status?: string; search?: string; page?: number }) => 
      api.get('/novels/batch-download/list/', { params }),
    
    // 获取任务详情
    get: (taskId: number) => 
      api.get(`/novels/batch-download/${taskId}/`),
    
    // 暂停任务
    pause: (taskId: number) => 
      api.post(`/novels/batch-download/${taskId}/pause/`),
    
    // 恢复任务
    resume: (taskId: number) => 
      api.post(`/novels/batch-download/${taskId}/resume/`),
    
    // 取消任务
    cancel: (taskId: number) => 
      api.post(`/novels/batch-download/${taskId}/cancel/`),
    
    // 获取统计信息
    stats: () => 
      api.get('/novels/batch-download/stats/'),
  },

  // 通用GET和POST方法
  get: (url: string, params?: any) => api.get(url, { params }),
  post: (url: string, data?: any) => api.post(url, data),
  put: (url: string, data?: any) => api.put(url, data),
  delete: (url: string) => api.delete(url),
}

// 导入系统API
export { systemApi } from './systemApi'

export { api }
export default api