<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Search,
  Microphone,
  VideoPlay as Play,
  VideoPause as Pause,
  Download,
  Calendar,
  Document,
  Clock,
} from '@element-plus/icons-vue'
import type { AudioProject, AudioProjectForm, Novel } from '@/types'
import { apiService } from '@/services/api'

// 数据状态
const audioProjects = ref<AudioProject[]>([])
const novels = ref<Novel[]>([])
const loading = ref(false)
const searchText = ref('')
const dialogVisible = ref(false)
const editingProject = ref<AudioProject | null>(null)

// 表单数据
const projectForm = ref<AudioProjectForm>({
  name: '',
  novel_id: undefined,
  description: '',
  voice_model: '',
  status: 'pending',
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  novel_id: [
    { required: true, message: '请选择关联小说', trigger: 'change' },
  ],
  voice_model: [
    { required: true, message: '请输入语音模型', trigger: 'blur' },
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' },
  ],
}

// 状态选项
const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
]

// 语音模型选项
const voiceModelOptions = [
  { label: '标准男声', value: 'male_standard' },
  { label: '标准女声', value: 'female_standard' },
  { label: '温柔女声', value: 'female_gentle' },
  { label: '磁性男声', value: 'male_magnetic' },
  { label: '童声', value: 'child' },
  { label: '老者', value: 'elder' },
]

// 计算属性
const filteredProjects = computed(() => {
  if (!searchText.value) return audioProjects.value
  return audioProjects.value.filter(project => 
    project.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
    (project.novel as any)?.title?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

// 获取音频项目列表
const fetchAudioProjects = async () => {
  loading.value = true
  try {
    const response = await apiService.audioProjects.list()
    audioProjects.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch audio projects:', error)
    ElMessage.error('获取音频项目列表失败')
  } finally {
    loading.value = false
  }
}

// 获取小说列表
const fetchNovels = async () => {
  try {
    const response = await apiService.novels.list()
    novels.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch novels:', error)
    ElMessage.error('获取小说列表失败')
  }
}

// 打开添加对话框
const openAddDialog = () => {
  editingProject.value = null
  projectForm.value = {
    name: '',
    novel_id: undefined,
    description: '',
    voice_model: '',
    status: 'pending',
  }
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (project: AudioProject) => {
  editingProject.value = project
  projectForm.value = {
    name: project.name,
    novel_id: project.novel_id,
    description: project.description || '',
    voice_model: project.voice_model,
    status: project.status,
  }
  dialogVisible.value = true
}

// 保存音频项目
const saveProject = async () => {
  try {
    if (editingProject.value) {
      // 编辑模式
      await apiService.audioProjects.update(editingProject.value.id, projectForm.value)
      ElMessage.success('音频项目更新成功')
    } else {
      // 添加模式
      await apiService.audioProjects.create(projectForm.value)
      ElMessage.success('音频项目创建成功')
    }
    dialogVisible.value = false
    await fetchAudioProjects()
  } catch (error) {
    console.error('Failed to save audio project:', error)
    ElMessage.error('保存失败')
  }
}

// 删除音频项目
const deleteProject = async (project: AudioProject) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除音频项目「${project.name}」吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiService.audioProjects.delete(project.id)
    ElMessage.success('删除成功')
    await fetchAudioProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete audio project:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option?.label || status
}

// 获取语音模型文本
const getVoiceModelText = (model: string) => {
  const option = voiceModelOptions.find(opt => opt.value === model)
  return option?.label || model
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 格式化时长
const formatDuration = (seconds: number) => {
  if (!seconds) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 播放音频
const playAudio = (project: AudioProject) => {
  // 这里应该实现音频播放逻辑
  ElMessage.info('音频播放功能开发中')
}

// 下载音频
const downloadAudio = (project: AudioProject) => {
  // 这里应该实现音频下载逻辑
  ElMessage.info('音频下载功能开发中')
}

// 组件挂载时获取数据
onMounted(() => {
  fetchAudioProjects()
  fetchNovels()
})
</script>

<template>
  <div class="audio-projects-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Microphone /></el-icon>
          音频项目
        </h1>
        <p class="page-description">管理音频生成项目，将小说转换为有声读物</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAddDialog">
        创建项目
      </el-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card shadow="never">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchText"
              placeholder="搜索项目名称或小说标题"
              :prefix-icon="Search"
              clearable
            />
          </el-col>
          <el-col :span="4">
            <el-button @click="fetchAudioProjects" :loading="loading">
              刷新
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 音频项目列表 -->
    <div class="projects-list">
      <el-card shadow="never">
        <div v-loading="loading" class="list-content">
          <div v-if="filteredProjects.length === 0" class="empty-state">
            <el-empty description="暂无音频项目">
              <el-button type="primary" :icon="Plus" @click="openAddDialog">
                创建第一个项目
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="projects-grid">
            <div
              v-for="project in filteredProjects"
              :key="project.id"
              class="project-card"
            >
              <div class="project-header">
                <div class="project-title">{{ project.name }}</div>
                <div class="project-actions">
                  <el-button
                    v-if="project.status === 'completed'"
                    type="success"
                    :icon="Play"
                    size="small"
                    circle
                    @click="playAudio(project)"
                  />
                  <el-button
                    v-if="project.status === 'completed'"
                    type="info"
                    :icon="Download"
                    size="small"
                    circle
                    @click="downloadAudio(project)"
                  />
                  <el-button
                    type="primary"
                    :icon="Edit"
                    size="small"
                    circle
                    @click="openEditDialog(project)"
                  />
                  <el-button
                    type="danger"
                    :icon="Delete"
                    size="small"
                    circle
                    @click="deleteProject(project)"
                  />
                </div>
              </div>
              
              <div class="project-meta">
                <div class="meta-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ (project.novel as any)?.title || '未关联小说' }}</span>
                </div>
                <div class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(project.created_at) }}</span>
                </div>
              </div>
              
              <div class="project-description">
                {{ project.description || '暂无描述' }}
              </div>
              
              <div class="project-details">
                <div class="detail-item">
                  <span class="detail-label">语音模型:</span>
                  <span class="detail-value">{{ getVoiceModelText(project.voice_model || '') }}</span>
                </div>
                <div v-if="project.duration" class="detail-item">
                  <span class="detail-label">时长:</span>
                  <span class="detail-value">
                    <el-icon><Clock /></el-icon>
                    {{ formatDuration(project.duration) }}
                  </span>
                </div>
              </div>
              
              <div class="project-footer">
                <div class="project-status">
                  <el-tag
                    :type="getStatusType(project.status || '')"
                    size="small"
                  >
                    {{ getStatusText(project.status || '') }}
                  </el-tag>
                </div>
                <div class="project-progress">
                  <el-progress
                    v-if="project.status === 'processing'"
                    :percentage="project.progress || 0"
                    :stroke-width="6"
                    :show-text="false"
                  />
                  <span v-if="project.status === 'processing'" class="progress-text">
                    {{ project.progress || 0 }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingProject ? '编辑音频项目' : '创建音频项目'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="projectForm"
        :rules="formRules"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="projectForm.name"
            placeholder="请输入项目名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="关联小说" prop="novel_id">
          <el-select
            v-model="projectForm.novel_id"
            placeholder="请选择关联的小说"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="novel in novels"
              :key="novel.id"
              :label="novel.title"
              :value="novel.id"
            >
              <span>{{ novel.title }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ novel.author }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="语音模型" prop="voice_model">
          <el-select
            v-model="projectForm.voice_model"
            placeholder="请选择语音模型"
            style="width: 100%"
          >
            <el-option
              v-for="option in voiceModelOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-select
            v-model="projectForm.status"
            placeholder="请选择状态"
            style="width: 100%"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveProject">
            {{ editingProject ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.audio-projects-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.search-section {
  margin-bottom: 20px;
}

.search-section .el-card {
  border: 1px solid #e4e7ed;
}

.projects-list .el-card {
  border: 1px solid #e4e7ed;
}

.list-content {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 20px;
}

.project-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
  cursor: pointer;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
  margin-right: 12px;
  line-height: 1.4;
}

.project-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.project-card:hover .project-actions {
  opacity: 1;
}

.project-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #7f8c8d;
}

.meta-item .el-icon {
  font-size: 14px;
}

.project-description {
  font-size: 14px;
  color: #5a6c7d;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.project-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-label {
  color: #7f8c8d;
  font-weight: 500;
}

.detail-value {
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 4px;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-status {
  display: flex;
  gap: 8px;
}

.project-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  margin-left: 16px;
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
  
  .projects-grid {
    grid-template-columns: 1fr;
  }
  
  .search-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section .el-col {
    width: 100%;
  }
  
  .project-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .project-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .project-progress {
    margin-left: 0;
  }
}
</style>