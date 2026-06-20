<template>
  <div class="integrated-crawler-container">
    <el-card class="crawler-card">
      <template #header>
        <div class="card-header">
          <span>🚀 粘贴和图书 URL，一键下载章节</span>
          <el-tag type="success" size="small">支持去水印</el-tag>
        </div>
      </template>
      
      <div class="crawler-form">
        <el-form :model="crawlerForm" label-width="120px" :rules="formRules">
          <!-- 小说链接 -->
          <el-form-item label="小说链接" prop="sourceUrl">
            <el-input 
              v-model="crawlerForm.sourceUrl" 
              placeholder="请输入和图书网小说目录页URL"
              type="url"
            >
              <template #append>
                <el-button @click="extractCatalog" :loading="extracting" size="small">
                  📚 提取目录
                </el-button>
              </template>
            </el-input>
            <div class="url-hint">
              <el-text size="small" type="info">
                💡 示例：https://www.example.com/book/1234/index.html
              </el-text>
            </div>
          </el-form-item>
          
          <!-- 目录信息显示 -->
          <div v-if="catalogData" class="catalog-info">
            <el-divider content-position="left">📖 目录信息</el-divider>
            
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="小说标题">
                <el-tag type="primary">{{ catalogData.title }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="作者">
                <el-tag type="info">{{ catalogData.author || '未知' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="总章节数">
                <el-tag type="warning">{{ catalogData.chapters?.length || 0 }} 章</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="来源">
                <el-tag type="success">和图书网</el-tag>
              </el-descriptions-item>
            </el-descriptions>
            
            <!-- 章节范围选择 -->
            <el-form-item label="下载范围" style="margin-top: 20px;">
              <div class="range-selector">
                <el-input-number 
                  v-model="crawlerForm.startChapter" 
                  :min="1" 
                  :max="catalogData.chapters?.length || 1"
                  placeholder="起始章节"
                  size="small"
                />
                <span style="margin: 0 10px;">至</span>
                <el-input-number 
                  v-model="crawlerForm.endChapter" 
                  :min="crawlerForm.startChapter || 1" 
                  :max="catalogData.chapters?.length || 1"
                  placeholder="结束章节"
                  size="small"
                />
                <el-button 
                  @click="setQuickRange(1, 5)" 
                  size="small" 
                  type="primary" 
                  plain
                  style="margin-left: 10px;"
                >
                  前5章
                </el-button>
                <el-button 
                  @click="setQuickRange(1, 10)" 
                  size="small" 
                  type="success" 
                  plain
                >
                  前10章
                </el-button>
              </div>
            </el-form-item>
            
            <!-- 去水印选项 -->
            <el-form-item label="去水印模式">
              <el-switch 
                v-model="crawlerForm.removeWatermark"
                active-text="开启"
                inactive-text="关闭"
                active-color="#13ce66"
                inactive-color="#ff4949"
              />
              <div class="watermark-hint">
                <el-text size="small" type="info">
                  🧹 开启后将智能去除文章中的水印内容，提供更纯净的阅读体验
                </el-text>
              </div>
            </el-form-item>
            
            <!-- 小说信息 -->
            <el-form-item label="小说标题">
              <el-input v-model="crawlerForm.novelTitle" placeholder="可自定义小说标题" />
            </el-form-item>
            
            <el-form-item label="作者">
              <el-input v-model="crawlerForm.novelAuthor" placeholder="可自定义作者名称" />
            </el-form-item>
          </div>
        </el-form>
        
        <!-- 操作按钮 -->
        <div class="action-buttons" v-if="catalogData">
          <el-button 
            type="primary" 
            size="large"
            @click="downloadChapters"
            :loading="downloading"
            :disabled="!isValidRange"
          >
            <el-icon><Download /></el-icon>
            下载章节 ({{ chapterCount }}章)
          </el-button>
          
          <el-button 
            type="success" 
            size="large"
            @click="quickCrawl"
            :loading="quickCrawling"
            :disabled="!isValidRange"
          >
            <el-icon><Download /></el-icon>
            导入并生成有声书
          </el-button>
        </div>
        
        <!-- Demo fallback：目录提取失败时仍可一键导入 -->
        <div v-if="!catalogData && crawlerForm.sourceUrl" class="action-buttons fallback-buttons" style="margin-top: 10px;">
          <el-alert
            title="若和图书被 Cloudflare 拦截，可点击下方按钮使用本地示例数据继续体验"
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 16px;"
          />
          <el-button
            type="warning"
            size="large"
            @click="quickCrawl"
            :loading="quickCrawling"
          >
            <el-icon><Download /></el-icon>
            直接体验 Demo 导入（1-5 章）
          </el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 人工绕过 Cloudflare 弹窗 -->
    <el-dialog
      v-model="manualBypassVisible"
      title="🛡️ 需要人工验证"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div style="line-height: 1.8;">
        <p>和图书站当前启用了 Cloudflare 防护，自动爬虫无法直接访问。</p>
        <p>请点击下方按钮在您的真实浏览器中打开该页面，完成验证（如点击“我不是机器人”）后，再点击“继续提取”。</p>
        <p style="margin-top: 12px; word-break: break-all; color: #666;">
          <strong>目标 URL：</strong>{{ crawlerForm.sourceUrl }}
        </p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="manualBypassVisible = false">取消</el-button>
          <el-button type="primary" @click="openUserBrowser" :loading="openingBrowser">
            打开浏览器验证
          </el-button>
          <el-button type="success" @click="completeManualBypass" :loading="completingBypass" :disabled="!manualBypassSession">
            我已完成验证，继续提取
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 任务进度 -->
    <el-card v-if="currentTask" class="task-progress-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>📊 任务进度</span>
          <el-tag :type="getTaskStatusType(currentTask.status)">
            {{ currentTask.status_display || currentTask.status }}
          </el-tag>
        </div>
      </template>
      
      <div class="task-info">
        <el-descriptions :column="2" size="small">
          <el-descriptions-item label="任务ID">{{ currentTask.task_id }}</el-descriptions-item>
          <el-descriptions-item label="任务类型">{{ currentTask.task_type_display }}</el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress 
              :percentage="currentTask.progress" 
              :status="currentTask.progress === 100 ? 'success' : 'active'"
            />
          </el-descriptions-item>
          <el-descriptions-item label="成功率">
            {{ currentTask.success_rate?.toFixed(1) || 0 }}%
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="currentTask.download_records?.length" style="margin-top: 20px;">
          <el-divider content-position="left">章节下载详情</el-divider>
          <el-table :data="currentTask.download_records" size="small" max-height="300">
            <el-table-column prop="chapter_number" label="章节号" width="80" />
            <el-table-column prop="chapter_title" label="章节标题" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getRecordStatusType(row.status)" size="small">
                  {{ getRecordStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="content_length" label="字数" width="80" />
            <el-table-column prop="watermark_removed" label="去水印" width="80">
              <template #default="{ row }">
                <el-icon v-if="row.watermark_removed" color="#67c23a"><Check /></el-icon>
                <el-icon v-else color="#f56c6c"><Close /></el-icon>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-if="currentTask.error_message" class="error-message">
          <el-alert 
            :title="currentTask.error_message" 
            type="error" 
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-card>
    
    <!-- 下载结果 -->
    <el-card v-if="downloadResult" class="result-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>📥 下载结果</span>
          <el-tag type="success">完成</el-tag>
        </div>
      </template>
      
      <div class="result-info">
        <el-result
          :icon="downloadResult.success ? 'success' : 'error'"
          :title="downloadResult.message"
        >
          <template #extra>
            <el-descriptions :column="2" size="small">
              <el-descriptions-item label="导入章节">
                {{ downloadResult.imported_chapters || downloadResult.downloaded_chapters || 0 }}
              </el-descriptions-item>
              <el-descriptions-item v-if="downloadResult.novel_id" label="小说">
                {{ downloadResult.novel_title || downloadResult.novel_id }}
              </el-descriptions-item>
              <el-descriptions-item v-if="downloadResult.watermark_removed !== undefined" label="去水印">
                <el-tag :type="downloadResult.watermark_removed ? 'success' : 'info'">
                  {{ downloadResult.watermark_removed ? '已应用' : '未应用' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <el-alert
              v-if="downloadResult.use_local_fallback"
              title="和图书当前有 Cloudflare 保护，已自动使用 Demo 本地示例数据完成导入"
              type="warning"
              :closable="false"
              show-icon
              style="margin-top: 16px;"
            />
            <div v-if="downloadResult.novel_id" style="margin-top: 16px; text-align: center;">
              <el-button type="warning" size="large" @click="goToTTS(downloadResult.novel_id)">
                <el-icon><Headset /></el-icon>
                下一步：生成 MP3 有声书
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
        </el-result>
      </div>
    </el-card>
    
    <!-- 任务历史 -->
    <el-card class="task-history-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>📋 任务历史</span>
          <el-button @click="loadTaskHistory" size="small" type="primary" plain>
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="taskHistory" size="small" v-loading="loadingHistory">
        <el-table-column prop="task_id" label="任务ID" width="120" />
        <el-table-column prop="task_type" label="类型" width="100" />
        <el-table-column prop="novel_title" label="小说" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusType(row.status)" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :show-text="false" />
          </template>
        </el-table-column>
        <el-table-column prop="success_rate" label="成功率" width="80">
          <template #default="{ row }">
            {{ row.success_rate?.toFixed(1) || 0 }}%
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button @click="viewTaskDetail(row.task_id)" size="small" type="primary" plain>
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Check, Close, Refresh, Headset, ArrowRight } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()

// 响应式数据
const crawlerForm = reactive({
  sourceUrl: '',
  startChapter: 1,
  endChapter: 5,
  removeWatermark: true,
  novelTitle: '',
  novelAuthor: ''
})

const catalogData = ref(null)
const currentTask = ref(null)
const downloadResult = ref(null)
const taskHistory = ref([])

// 人工绕过 Cloudflare
const manualBypassVisible = ref(false)
const manualBypassSession = ref('')
const manualBypassCookies = ref(null)
const openingBrowser = ref(false)
const completingBypass = ref(false)

// 状态控制
const extracting = ref(false)
const downloading = ref(false)
const quickCrawling = ref(false)
const loadingHistory = ref(false)

// 表单验证规则
const formRules = {
  sourceUrl: [
    { required: true, message: '请输入小说链接', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

// 计算属性
const isValidRange = computed(() => {
  return crawlerForm.startChapter >= 1 && 
         crawlerForm.endChapter >= crawlerForm.startChapter &&
         catalogData.value?.chapters?.length > 0
})

const chapterCount = computed(() => {
  if (!isValidRange.value) return 0
  return crawlerForm.endChapter - crawlerForm.startChapter + 1
})

// 方法
const extractCatalog = async () => {
  if (!crawlerForm.sourceUrl) {
    ElMessage.warning('请输入小说链接')
    return
  }
  
  extracting.value = true
  manualBypassCookies.value = null
  manualBypassSession.value = ''
  try {
    const response = await axios.post('/api/crawler/extract_catalog/', {
      source_url: crawlerForm.sourceUrl
    })
    
    if (response.data.success) {
      catalogData.value = response.data.catalog
      crawlerForm.novelTitle = catalogData.value.title
      crawlerForm.novelAuthor = catalogData.value.author
      
      // 设置默认下载范围
      const totalChapters = catalogData.value.chapters?.length || 0
      crawlerForm.endChapter = Math.min(5, totalChapters)
      
      ElMessage.success(`成功提取目录，共 ${totalChapters} 章`)
    } else {
      ElMessage.error(response.data.error || '目录提取失败')
    }
  } catch (error) {
    console.error('目录提取错误:', error)
    const errData = error.response?.data
    if (errData?.needs_manual_bypass) {
      manualBypassVisible.value = true
      ElMessage.warning(errData.message || '需要人工绕过 Cloudflare')
    } else {
      ElMessage.error('目录提取失败: ' + (errData?.error || error.message))
    }
  } finally {
    extracting.value = false
  }
}

const openUserBrowser = async () => {
  openingBrowser.value = true
  try {
    const response = await axios.post('/api/crawler/request_manual_bypass/', {
      source_url: crawlerForm.sourceUrl
    })
    if (response.data.success) {
      manualBypassSession.value = response.data.session
      ElMessage.success('已在您的浏览器中打开验证页面，请完成验证后返回点击“继续提取”')
    } else {
      ElMessage.error(response.data.error || '打开浏览器失败')
    }
  } catch (error) {
    console.error('打开浏览器失败:', error)
    ElMessage.error('打开浏览器失败: ' + (error.response?.data?.error || error.message))
  } finally {
    openingBrowser.value = false
  }
}

const completeManualBypass = async () => {
  if (!manualBypassSession.value) {
    ElMessage.warning('请先点击“打开浏览器验证”')
    return
  }
  completingBypass.value = true
  try {
    const response = await axios.post('/api/crawler/complete_manual_bypass/', {
      source_url: crawlerForm.sourceUrl,
      session: manualBypassSession.value
    })
    if (response.data.success) {
      catalogData.value = response.data.catalog
      crawlerForm.novelTitle = catalogData.value.title
      crawlerForm.novelAuthor = catalogData.value.author
      manualBypassCookies.value = response.data.cookies || null
      manualBypassVisible.value = false
      
      const totalChapters = catalogData.value.chapters?.length || 0
      crawlerForm.endChapter = Math.min(5, totalChapters)
      ElMessage.success(`人工绕过成功，共提取 ${totalChapters} 章`)
    } else {
      ElMessage.error(response.data.error || '绕过失败')
    }
  } catch (error) {
    console.error('绕过失败:', error)
    const errData = error.response?.data
    if (errData?.needs_manual_bypass) {
      ElMessage.warning(errData.message || '仍未通过验证，请重新完成')
    } else {
      ElMessage.error('绕过失败: ' + (errData?.error || error.message))
    }
  } finally {
    completingBypass.value = false
  }
}

const downloadChapters = async () => {
  if (!catalogData.value || !isValidRange.value) {
    ElMessage.warning('请先提取目录并设置有效的章节范围')
    return
  }
  
  downloading.value = true
  downloadResult.value = null
  currentTask.value = null
  
  try {
    const response = await axios.post('/api/crawler/download_chapters/', {
      catalog: catalogData.value,
      start_chapter: crawlerForm.startChapter,
      end_chapter: crawlerForm.endChapter,
      remove_watermark: crawlerForm.removeWatermark,
      novel_title: crawlerForm.novelTitle,
      cookies: manualBypassCookies.value
    })
    
    if (response.data.success) {
      downloadResult.value = response.data
      
      // 开始轮询任务状态
      if (response.data.task_id) {
        pollTaskStatus(response.data.task_id)
      }
      
      ElMessage.success(`开始下载 ${chapterCount.value} 章`)
    } else {
      ElMessage.error(response.data.error || '章节下载失败')
    }
  } catch (error) {
    console.error('章节下载错误:', error)
    const errData = error.response?.data
    if (errData?.needs_manual_bypass) {
      manualBypassVisible.value = true
      ElMessage.warning(errData.message || '下载章节时再次被拦截，请重新验证')
    } else {
      ElMessage.error('章节下载失败: ' + (errData?.error || error.message))
    }
  } finally {
    downloading.value = false
  }
}

const quickCrawl = async () => {
  if (!crawlerForm.sourceUrl) {
    ElMessage.warning('请输入小说链接')
    return
  }
  
  // 需要先提取目录才能导入
  if (!catalogData.value) {
    ElMessage.warning('请先提取目录')
    return
  }

  const start = crawlerForm.startChapter
  const end = crawlerForm.endChapter

  try {
    await ElMessageBox.confirm(
      `确定要一键导入《${crawlerForm.novelTitle}》的第 ${start}-${end} 章到数据库吗？`,
      '确认导入',
      {
        confirmButtonText: '确定导入',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return // 用户取消
  }
  
  quickCrawling.value = true
  downloadResult.value = null
  currentTask.value = null
  
  try {
    const response = await axios.post('/api/crawler/quick-crawl/', {
      source_url: crawlerForm.sourceUrl,
      start_chapter: start,
      end_chapter: end,
      remove_watermark: crawlerForm.removeWatermark,
      novel_title: crawlerForm.novelTitle,
      novel_author: crawlerForm.novelAuthor
    })
    
    if (response.data.success) {
      downloadResult.value = response.data
      ElMessage.success(`成功导入小说《${response.data.novel_title}》`)
      
      // 刷新任务历史
      loadTaskHistory()
    } else {
      ElMessage.error(response.data.error || '一键导入失败')
    }
  } catch (error) {
    console.error('一键导入错误:', error)
    ElMessage.error('一键导入失败: ' + (error.response?.data?.error || error.message))
  } finally {
    quickCrawling.value = false
  }
}

const pollTaskStatus = async (taskId) => {
  try {
    const response = await axios.get(`/api/crawler/task_status/?task_id=${taskId}`)
    
    if (response.data.success) {
      currentTask.value = response.data.task
      
      // 如果任务还在进行中，继续轮询
      if (response.data.task.status === 'running') {
        setTimeout(() => pollTaskStatus(taskId), 2000)
      }
    }
  } catch (error) {
    console.error('获取任务状态错误:', error)
  }
}

const loadTaskHistory = async () => {
  loadingHistory.value = true
  try {
    const response = await axios.get('/api/crawler/task_list/')
    
    if (response.data.success) {
      taskHistory.value = response.data.tasks
    }
  } catch (error) {
    console.error('加载任务历史错误:', error)
    ElMessage.error('加载任务历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const viewTaskDetail = async (taskId) => {
  try {
    const response = await axios.get(`/api/crawler/task_status/?task_id=${taskId}`)
    
    if (response.data.success) {
      currentTask.value = response.data.task
      ElMessage.success('任务详情已加载')
    }
  } catch (error) {
    console.error('获取任务详情错误:', error)
    ElMessage.error('获取任务详情失败')
  }
}

const setQuickRange = (start, end) => {
  const maxChapters = catalogData.value?.chapters?.length || 0
  crawlerForm.startChapter = start
  crawlerForm.endChapter = Math.min(end, maxChapters)
}

const goToTTS = (novelId) => {
  router.push({
    path: '/tts/synthesize',
    query: { novel_id: novelId }
  })
}

// 辅助方法
const getTaskStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning', 
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

const getRecordStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'downloading': 'warning',
    'completed': 'success', 
    'failed': 'danger',
    'skipped': 'info'
  }
  return statusMap[status] || 'info'
}

const getRecordStatusText = (status) => {
  const statusMap = {
    'pending': '等待',
    'downloading': '下载中',
    'completed': '完成',
    'failed': '失败',
    'skipped': '跳过'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return ''
  return new Date(dateTimeStr).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadTaskHistory()
})
</script>

<style scoped>
.integrated-crawler-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.crawler-card, .task-progress-card, .result-card, .task-history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.url-hint {
  margin-top: 5px;
}

.catalog-info {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.range-selector {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.watermark-hint {
  margin-top: 5px;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.task-info, .result-info {
  padding: 10px 0;
}

.error-message {
  margin-top: 15px;
}

@media (max-width: 768px) {
  .integrated-crawler-container {
    padding: 10px;
  }
  
  .range-selector {
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>
