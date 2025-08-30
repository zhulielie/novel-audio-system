<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Search,
  MagicStick,
  VideoPlay as Play,
  VideoPause as Pause,
  Top as Stop,
  Refresh,
  Document,
  Microphone,
  Clock,
  Setting,
} from '@element-plus/icons-vue'
import type { GenerationWorkflow, ScriptGenerationTask, AudioGenerationTask, Novel } from '@/types'
import { apiService } from '@/services/api'

// 数据状态
const workflows = ref<GenerationWorkflow[]>([])
const scriptTasks = ref<ScriptGenerationTask[]>([])
const audioTasks = ref<AudioGenerationTask[]>([])
const novels = ref<Novel[]>([])
const loading = ref(false)
const searchText = ref('')
const activeTab = ref('workflows')
const dialogVisible = ref(false)
const taskDialogVisible = ref(false)
const editingWorkflow = ref<GenerationWorkflow | null>(null)
const taskType = ref<'script' | 'audio'>('script')

// 表单数据
const workflowForm = ref({
  name: '',
  description: '',
  novel_id: null as number | null,
  config: {
    script_generation: {
      enabled: true,
      model: 'gpt-3.5-turbo',
      prompt_template: '',
      max_tokens: 2000,
    },
    audio_generation: {
      enabled: true,
      voice_model: 'female_standard',
      speed: 1.0,
      pitch: 1.0,
    },
  },
})

const scriptTaskForm = ref({
  workflow_id: null as number | null,
  chapter_id: null as number | null,
  prompt: '',
  model: 'gpt-3.5-turbo',
  max_tokens: 2000,
})

const audioTaskForm = ref({
  workflow_id: null as number | null,
  script_id: null as number | null,
  voice_model: 'female_standard',
  speed: 1.0,
  pitch: 1.0,
})

// 模型选项
const llmModels = [
  { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
  { label: 'GPT-4', value: 'gpt-4' },
  { label: 'Claude-3', value: 'claude-3' },
  { label: 'Qwen', value: 'qwen' },
]

const voiceModels = [
  { label: '标准女声', value: 'female_standard' },
  { label: '标准男声', value: 'male_standard' },
  { label: '温柔女声', value: 'female_gentle' },
  { label: '磁性男声', value: 'male_magnetic' },
  { label: '童声', value: 'child' },
  { label: '老者', value: 'elder' },
]

// 状态选项
const statusOptions = [
  { label: '待处理', value: 'pending', type: 'info' },
  { label: '运行中', value: 'running', type: 'warning' },
  { label: '已完成', value: 'completed', type: 'success' },
  { label: '失败', value: 'failed', type: 'danger' },
  { label: '已暂停', value: 'paused', type: 'info' },
]

// 计算属性
const filteredWorkflows = computed(() => {
  if (!searchText.value) return workflows.value
  return workflows.value.filter(workflow => 
    workflow.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
    workflow.description?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const filteredScriptTasks = computed(() => {
  if (!searchText.value) return scriptTasks.value
  return scriptTasks.value.filter(task => 
    (task.workflow as any)?.name?.toLowerCase().includes(searchText.value.toLowerCase()) ||
    (task.chapter as any)?.title?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const filteredAudioTasks = computed(() => {
  if (!searchText.value) return audioTasks.value
  return audioTasks.value.filter(task => 
    (task.workflow as any)?.name?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

// 获取数据
const fetchWorkflows = async () => {
  loading.value = true
  try {
    const response = await apiService.workflows.list()
    workflows.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch workflows:', error)
    ElMessage.error('获取工作流列表失败')
  } finally {
    loading.value = false
  }
}

const fetchScriptTasks = async () => {
  try {
    const response = await apiService.scriptTasks.list()
    scriptTasks.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch script tasks:', error)
    ElMessage.error('获取脚本任务列表失败')
  }
}

const fetchAudioTasks = async () => {
  try {
    const response = await apiService.audioTasks.list()
    audioTasks.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch audio tasks:', error)
    ElMessage.error('获取音频任务列表失败')
  }
}

const fetchNovels = async () => {
  try {
    const response = await apiService.novels.list()
    const data = (response as any)?.results || (response as any)?.data?.results || []
    novels.value = Array.isArray(data) ? data.filter(novel => novel && novel.id) : []
  } catch (error) {
    console.error('Failed to fetch novels:', error)
    novels.value = []
  }
}

// 工作流操作
const openAddWorkflowDialog = () => {
  editingWorkflow.value = null
  workflowForm.value = {
    name: '',
    description: '',
    novel_id: null,
    config: {
      script_generation: {
        enabled: true,
        model: 'gpt-3.5-turbo',
        prompt_template: '',
        max_tokens: 2000,
      },
      audio_generation: {
        enabled: true,
        voice_model: 'female_standard',
        speed: 1.0,
        pitch: 1.0,
      },
    },
  }
  dialogVisible.value = true
}

const openEditWorkflowDialog = (workflow: GenerationWorkflow) => {
  editingWorkflow.value = workflow
  workflowForm.value = {
    name: workflow.name,
    description: workflow.description || '',
    novel_id: workflow.novel_id || null,
    config: workflow.config || workflowForm.value.config,
  }
  dialogVisible.value = true
}

const saveWorkflow = async () => {
  try {
    if (editingWorkflow.value) {
      await apiService.workflows.update(editingWorkflow.value.id, workflowForm.value)
      ElMessage.success('工作流更新成功')
    } else {
      await apiService.workflows.create(workflowForm.value)
      ElMessage.success('工作流创建成功')
    }
    dialogVisible.value = false
    await fetchWorkflows()
  } catch (error) {
    console.error('Failed to save workflow:', error)
    ElMessage.error('保存失败')
  }
}

const deleteWorkflow = async (workflow: GenerationWorkflow) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除工作流「${workflow.name}」吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiService.workflows.delete(workflow.id)
    ElMessage.success('删除成功')
    await fetchWorkflows()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete workflow:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 任务操作
const openAddTaskDialog = (type: 'script' | 'audio') => {
  taskType.value = type
  if (type === 'script') {
    scriptTaskForm.value = {
      workflow_id: null,
      chapter_id: null,
      prompt: '',
      model: 'gpt-3.5-turbo',
      max_tokens: 2000,
    }
  } else {
    audioTaskForm.value = {
      workflow_id: null,
      script_id: null,
      voice_model: 'female_standard',
      speed: 1.0,
      pitch: 1.0,
    }
  }
  taskDialogVisible.value = true
}

const saveTask = async () => {
  try {
    if (taskType.value === 'script') {
      await apiService.scriptTasks.create(scriptTaskForm.value)
      ElMessage.success('脚本任务创建成功')
      await fetchScriptTasks()
    } else {
      await apiService.audioTasks.create(audioTaskForm.value)
      ElMessage.success('音频任务创建成功')
      await fetchAudioTasks()
    }
    taskDialogVisible.value = false
  } catch (error) {
    console.error('Failed to save task:', error)
    ElMessage.error('保存失败')
  }
}

// 任务控制
const startTask = async (taskId: number, type: 'script' | 'audio') => {
  try {
    if (type === 'script') {
      await apiService.scriptTasks.start(taskId)
    } else {
      await apiService.audioTasks.start(taskId)
    }
    ElMessage.success('任务已启动')
    if (type === 'script') {
      await fetchScriptTasks()
    } else {
      await fetchAudioTasks()
    }
  } catch (error) {
    console.error('Failed to start task:', error)
    ElMessage.error('启动任务失败')
  }
}

const pauseTask = async (taskId: number, type: 'script' | 'audio') => {
  try {
    if (type === 'script') {
      await apiService.scriptTasks.pause(taskId)
    } else {
      await apiService.audioTasks.pause(taskId)
    }
    ElMessage.success('任务已暂停')
    if (type === 'script') {
      await fetchScriptTasks()
    } else {
      await fetchAudioTasks()
    }
  } catch (error) {
    console.error('Failed to pause task:', error)
    ElMessage.error('暂停任务失败')
  }
}

const stopTask = async (taskId: number, type: 'script' | 'audio') => {
  try {
    if (type === 'script') {
      await apiService.scriptTasks.stop(taskId)
    } else {
      await apiService.audioTasks.stop(taskId)
    }
    ElMessage.success('任务已停止')
    if (type === 'script') {
      await fetchScriptTasks()
    } else {
      await fetchAudioTasks()
    }
  } catch (error) {
    console.error('Failed to stop task:', error)
    ElMessage.error('停止任务失败')
  }
}

// 工具函数
const getStatusInfo = (status: string) => {
  return statusOptions.find(opt => opt.value === status) || statusOptions[0]
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number) => {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${remainingSeconds}秒`
  } else {
    return `${remainingSeconds}秒`
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchWorkflows()
  fetchScriptTasks()
  fetchAudioTasks()
  fetchNovels()
})
</script>

<template>
  <div class="generators-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><MagicStick /></el-icon>
          生成器
        </h1>
        <p class="page-description">管理脚本生成和音频生成工作流</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="openAddWorkflowDialog">
          创建工作流
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card shadow="never">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchText"
              placeholder="搜索工作流或任务"
              :prefix-icon="Search"
              clearable
            />
          </el-col>
          <el-col :span="4">
            <el-button @click="fetchWorkflows" :loading="loading">
              刷新
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 工作流标签页 -->
      <el-tab-pane label="工作流" name="workflows">
        <div class="workflows-content">
          <div v-if="filteredWorkflows.length === 0" class="empty-state">
            <el-empty description="暂无工作流">
              <el-button type="primary" :icon="Plus" @click="openAddWorkflowDialog">
                创建第一个工作流
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="workflows-grid">
            <div
              v-for="workflow in filteredWorkflows"
              :key="workflow.id"
              class="workflow-card"
            >
              <div class="workflow-header">
                <div class="workflow-title">{{ workflow.name }}</div>
                <div class="workflow-actions">
                  <el-button
                    type="primary"
                    :icon="Edit"
                    size="small"
                    circle
                    @click="openEditWorkflowDialog(workflow)"
                  />
                  <el-button
                    type="danger"
                    :icon="Delete"
                    size="small"
                    circle
                    @click="deleteWorkflow(workflow)"
                  />
                </div>
              </div>
              
              <div class="workflow-description">
                {{ workflow.description || '暂无描述' }}
              </div>
              
              <div class="workflow-meta">
                <div class="meta-item">
                  <span class="meta-label">关联小说:</span>
                  <span class="meta-value">{{ (workflow.novel as any)?.title || '未关联' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">创建时间:</span>
                  <span class="meta-value">{{ formatDate(workflow.created_at) }}</span>
                </div>
              </div>
              
              <div class="workflow-config">
                <div class="config-item">
                  <el-icon><Document /></el-icon>
                  <span>脚本生成: {{ workflow.config?.script_generation?.enabled ? '启用' : '禁用' }}</span>
                </div>
                <div class="config-item">
                  <el-icon><Microphone /></el-icon>
                  <span>音频生成: {{ workflow.config?.audio_generation?.enabled ? '启用' : '禁用' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      
      <!-- 脚本任务标签页 -->
      <el-tab-pane label="脚本任务" name="script-tasks">
        <div class="tasks-header">
          <el-button type="primary" :icon="Plus" @click="openAddTaskDialog('script')">
            创建脚本任务
          </el-button>
        </div>
        
        <div class="tasks-content">
          <div v-if="filteredScriptTasks.length === 0" class="empty-state">
            <el-empty description="暂无脚本任务">
              <el-button type="primary" :icon="Plus" @click="openAddTaskDialog('script')">
                创建第一个脚本任务
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="tasks-list">
            <div
              v-for="task in filteredScriptTasks"
              :key="task.id"
              class="task-card"
            >
              <div class="task-header">
                <div class="task-info">
                  <div class="task-title">{{ (task.workflow as any)?.name || '未知工作流' }}</div>
                  <div class="task-subtitle">{{ (task.chapter as any)?.title || '未知章节' }}</div>
                </div>
                <div class="task-status">
                  <el-tag :type="getStatusInfo(task.status).type" size="small">
                    {{ getStatusInfo(task.status).label }}
                  </el-tag>
                </div>
              </div>
              
              <div class="task-meta">
                <div class="meta-item">
                  <span class="meta-label">模型:</span>
                  <span class="meta-value">{{ task.model }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">创建时间:</span>
                  <span class="meta-value">{{ formatDate(task.created_at) }}</span>
                </div>
                <div v-if="task.duration" class="meta-item">
                  <span class="meta-label">耗时:</span>
                  <span class="meta-value">
                    <el-icon><Clock /></el-icon>
                    {{ formatDuration(task.duration) }}
                  </span>
                </div>
              </div>
              
              <div class="task-actions">
                <el-button
                  v-if="task.status === 'pending' || task.status === 'paused'"
                  type="success"
                  :icon="Play"
                  size="small"
                  @click="startTask(task.id, 'script')"
                >
                  启动
                </el-button>
                <el-button
                  v-if="task.status === 'running'"
                  type="warning"
                  :icon="Pause"
                  size="small"
                  @click="pauseTask(task.id, 'script')"
                >
                  暂停
                </el-button>
                <el-button
                  v-if="task.status === 'running' || task.status === 'paused'"
                  type="danger"
                  :icon="Stop"
                  size="small"
                  @click="stopTask(task.id, 'script')"
                >
                  停止
                </el-button>
              </div>
              
              <div v-if="task.status === 'running' && task.progress" class="task-progress">
                <el-progress
                  :percentage="task.progress"
                  :stroke-width="6"
                  :show-text="false"
                />
                <span class="progress-text">{{ task.progress }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      
      <!-- 音频任务标签页 -->
      <el-tab-pane label="音频任务" name="audio-tasks">
        <div class="tasks-header">
          <el-button type="primary" :icon="Plus" @click="openAddTaskDialog('audio')">
            创建音频任务
          </el-button>
        </div>
        
        <div class="tasks-content">
          <div v-if="filteredAudioTasks.length === 0" class="empty-state">
            <el-empty description="暂无音频任务">
              <el-button type="primary" :icon="Plus" @click="openAddTaskDialog('audio')">
                创建第一个音频任务
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="tasks-list">
            <div
              v-for="task in filteredAudioTasks"
              :key="task.id"
              class="task-card"
            >
              <div class="task-header">
                <div class="task-info">
                  <div class="task-title">{{ (task.workflow as any)?.name || '未知工作流' }}</div>
                  <div class="task-subtitle">音频生成任务</div>
                </div>
                <div class="task-status">
                  <el-tag :type="getStatusInfo(task.status).type" size="small">
                    {{ getStatusInfo(task.status).label }}
                  </el-tag>
                </div>
              </div>
              
              <div class="task-meta">
                <div class="meta-item">
                  <span class="meta-label">语音模型:</span>
                  <span class="meta-value">{{ task.voice_model }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">语速:</span>
                  <span class="meta-value">{{ task.speed }}x</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">音调:</span>
                  <span class="meta-value">{{ task.pitch }}x</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">创建时间:</span>
                  <span class="meta-value">{{ formatDate(task.created_at) }}</span>
                </div>
                <div v-if="task.duration" class="meta-item">
                  <span class="meta-label">耗时:</span>
                  <span class="meta-value">
                    <el-icon><Clock /></el-icon>
                    {{ formatDuration(task.duration) }}
                  </span>
                </div>
              </div>
              
              <div class="task-actions">
                <el-button
                  v-if="task.status === 'pending' || task.status === 'paused'"
                  type="success"
                  :icon="Play"
                  size="small"
                  @click="startTask(task.id, 'audio')"
                >
                  启动
                </el-button>
                <el-button
                  v-if="task.status === 'running'"
                  type="warning"
                  :icon="Pause"
                  size="small"
                  @click="pauseTask(task.id, 'audio')"
                >
                  暂停
                </el-button>
                <el-button
                  v-if="task.status === 'running' || task.status === 'paused'"
                  type="danger"
                  :icon="Stop"
                  size="small"
                  @click="stopTask(task.id, 'audio')"
                >
                  停止
                </el-button>
              </div>
              
              <div v-if="task.status === 'running' && task.progress" class="task-progress">
                <el-progress
                  :percentage="task.progress"
                  :stroke-width="6"
                  :show-text="false"
                />
                <span class="progress-text">{{ task.progress }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 工作流对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingWorkflow ? '编辑工作流' : '创建工作流'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="workflowForm"
        label-width="120px"
        label-position="left"
      >
        <el-form-item label="工作流名称" required>
          <el-input
            v-model="workflowForm.name"
            placeholder="请输入工作流名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="关联小说">
          <el-select
            v-model="workflowForm.novel_id"
            placeholder="请选择关联的小说（可选）"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="novel in novels"
              :key="novel.id"
              :label="novel.title"
              :value="novel.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="workflowForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入工作流描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-divider>脚本生成配置</el-divider>
        
        <el-form-item label="启用脚本生成">
          <el-switch v-model="workflowForm.config.script_generation.enabled" />
        </el-form-item>
        
        <template v-if="workflowForm.config.script_generation.enabled">
          <el-form-item label="LLM模型">
            <el-select
              v-model="workflowForm.config.script_generation.model"
              placeholder="请选择LLM模型"
              style="width: 100%"
            >
              <el-option
                v-for="model in llmModels"
                :key="model.value"
                :label="model.label"
                :value="model.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="最大Token数">
            <el-input-number
              v-model="workflowForm.config.script_generation.max_tokens"
              :min="100"
              :max="8000"
              :step="100"
              style="width: 100%"
            />
          </el-form-item>
        </template>
        
        <el-divider>音频生成配置</el-divider>
        
        <el-form-item label="启用音频生成">
          <el-switch v-model="workflowForm.config.audio_generation.enabled" />
        </el-form-item>
        
        <template v-if="workflowForm.config.audio_generation.enabled">
          <el-form-item label="语音模型">
            <el-select
              v-model="workflowForm.config.audio_generation.voice_model"
              placeholder="请选择语音模型"
              style="width: 100%"
            >
              <el-option
                v-for="model in voiceModels"
                :key="model.value"
                :label="model.label"
                :value="model.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="语速">
            <el-slider
              v-model="workflowForm.config.audio_generation.speed"
              :min="0.5"
              :max="2.0"
              :step="0.1"
              show-input
              :show-input-controls="false"
            />
          </el-form-item>
          
          <el-form-item label="音调">
            <el-slider
              v-model="workflowForm.config.audio_generation.pitch"
              :min="0.5"
              :max="2.0"
              :step="0.1"
              show-input
              :show-input-controls="false"
            />
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveWorkflow">
            {{ editingWorkflow ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 任务对话框 -->
    <el-dialog
      v-model="taskDialogVisible"
      :title="`创建${taskType === 'script' ? '脚本' : '音频'}任务`"
      width="600px"
      :close-on-click-modal="false"
    >
      <!-- 脚本任务表单 -->
      <el-form
        v-if="taskType === 'script'"
        ref="scriptFormRef"
        :model="scriptTaskForm"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="工作流" required>
          <el-select
            v-model="scriptTaskForm.workflow_id"
            placeholder="请选择工作流"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="workflow in workflows"
              :key="workflow.id"
              :label="workflow.name"
              :value="workflow.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="LLM模型" required>
          <el-select
            v-model="scriptTaskForm.model"
            placeholder="请选择LLM模型"
            style="width: 100%"
          >
            <el-option
              v-for="model in llmModels"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="最大Token数">
          <el-input-number
            v-model="scriptTaskForm.max_tokens"
            :min="100"
            :max="8000"
            :step="100"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="提示词">
          <el-input
            v-model="scriptTaskForm.prompt"
            type="textarea"
            :rows="4"
            placeholder="请输入生成提示词（可选）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <!-- 音频任务表单 -->
      <el-form
        v-else
        ref="audioFormRef"
        :model="audioTaskForm"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="工作流" required>
          <el-select
            v-model="audioTaskForm.workflow_id"
            placeholder="请选择工作流"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="workflow in workflows"
              :key="workflow.id"
              :label="workflow.name"
              :value="workflow.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="语音模型" required>
          <el-select
            v-model="audioTaskForm.voice_model"
            placeholder="请选择语音模型"
            style="width: 100%"
          >
            <el-option
              v-for="model in voiceModels"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="语速">
          <el-slider
            v-model="audioTaskForm.speed"
            :min="0.5"
            :max="2.0"
            :step="0.1"
            show-input
            :show-input-controls="false"
          />
        </el-form-item>
        
        <el-form-item label="音调">
          <el-slider
            v-model="audioTaskForm.pitch"
            :min="0.5"
            :max="2.0"
            :step="0.1"
            show-input
            :show-input-controls="false"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="taskDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTask">
            创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.generators-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%);
  border-radius: 8px;
  color: white;
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-section {
  margin-bottom: 20px;
}

.search-section .el-card {
  border: 1px solid #e4e7ed;
}

.main-tabs {
  background: white;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e4e7ed;
}

.tasks-header {
  margin-bottom: 20px;
  text-align: right;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.workflows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.workflow-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
}

.workflow-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.workflow-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
  margin-right: 12px;
}

.workflow-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.workflow-card:hover .workflow-actions {
  opacity: 1;
}

.workflow-description {
  font-size: 14px;
  color: #5a6c7d;
  line-height: 1.5;
  margin-bottom: 16px;
  min-height: 42px;
}

.workflow-meta {
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.meta-label {
  color: #7f8c8d;
  font-weight: 500;
}

.meta-value {
  color: #2c3e50;
}

.workflow-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #5a6c7d;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
}

.task-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.task-subtitle {
  font-size: 14px;
  color: #7f8c8d;
}

.task-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.task-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 12px;
  color: #7f8c8d;
  min-width: 35px;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .workflows-grid {
    grid-template-columns: 1fr;
  }
  
  .search-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section .el-col {
    width: 100%;
  }
  
  .task-meta {
    grid-template-columns: 1fr;
  }
  
  .task-actions {
    flex-wrap: wrap;
  }
}
</style>