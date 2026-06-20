// 用户相关类型
export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  date_joined?: string
  last_login?: string
  is_active?: boolean
  is_staff?: boolean
  bio?: string
  phone?: string
  location?: string
  avatar?: string
}

// 小说相关类型
export interface Novel {
  id: number
  title: string
  author: string
  description?: string
  cover_image?: string
  genre?: string
  status?: string
  created_at: string
  updated_at: string
  chapters_count?: number
  sources?: number[]  // 关联的来源ID数组
}

export interface Chapter {
  id: number
  novel: number
  title: string
  content: string
  chapter_number: number
  chapter_sort_number?: number
  word_count: number
  is_published?: boolean
  created_at: string
  updated_at: string
}

// 音频相关类型
export interface AudioProject {
  id: number
  name: string
  description?: string
  novel?: number
  novel_id?: number
  voice_model?: string
  status?: string
  duration?: number
  progress?: number
  created_at: string
  updated_at: string
  item_count?: number
}

export interface AudioItem {
  id: number
  project: number
  title: string
  text_content: string
  audio_file?: string
  duration?: number
  voice_settings?: any
  created_at: string
  updated_at: string
}

// LLM相关类型
export interface LLMModel {
  id: number
  name: string
  provider: string
  model_id: string
  model_name?: string
  api_key?: string
  api_base?: string
  max_tokens?: number
  temperature?: number
  config?: any
  description?: string
  is_active: boolean
  is_default_assistant?: boolean
  created_at: string
}

export interface LLMModelForm {
  name: string
  provider: string
  model_id: string
  model_name?: string
  api_key?: string
  api_base?: string
  max_tokens?: number
  temperature?: number
  config?: any
  description?: string
  is_active?: boolean
  is_default_assistant?: boolean
}

export interface LLMRequest {
  id: number
  model: number
  prompt: string
  response?: string
  tokens_used?: number
  cost?: number
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
}

// 生成器相关类型
export interface GenerationWorkflow {
  id: number
  name: string
  description?: string
  novel?: number
  chapter?: number
  novel_id?: number
  config?: any
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}

export interface GenerationWorkflowForm {
  name: string
  description?: string
  novel?: number
  novel_id?: number
  config?: any
  status?: string
}

export interface ScriptGenerationTask {
  id: number
  workflow: number
  chapter: number
  llm_model: number
  generated_script?: string
  model?: string
  duration?: number
  progress?: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  created_at: string
  completed_at?: string
}

export interface AudioGenerationTask {
  id: number
  workflow: number
  script_task: number
  audio_project: number
  generated_audio?: string
  voice_model?: string
  speed?: number
  pitch?: number
  duration?: number
  progress?: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  created_at: string
  completed_at?: string
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  errors?: any
}

export interface PaginatedResponse<T> {
  count: number
  next?: string
  previous?: string
  results: T[]
}

// 表单相关类型
export interface LoginForm {
  username: string
  password: string
  remember?: boolean
}

export interface NovelForm {
  title: string
  author: string
  description?: string
  cover_image?: File
  genre?: string
  status?: string
  sources?: number[]  // 小说来源ID数组
}

export interface ChapterForm {
  novel: number | string
  title: string
  content: string
  chapter_number: number | string
  chapter_sort_number?: number
  is_published?: boolean
}

// 小说来源相关类型
export interface NovelSource {
  id: number
  name: string
  source_type: string
  base_url: string
  chapter_url_pattern?: string
  encoding: string
  is_active: boolean
  priority: number
  last_crawl_at?: string
  crawl_count: number
  created_at: string
}

export interface NovelSourceRelation {
  id: number
  novel: number
  source: number
  source_url: string
  is_primary: boolean
  last_sync_at?: string
  sync_count: number
  chapter_count: number
  created_at: string
}

export interface AudioProjectForm {
  name: string
  description?: string
  novel?: number
  novel_id?: number
  voice_model?: string
  status?: string
}