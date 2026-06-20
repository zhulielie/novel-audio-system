<template>
  <div class="batch-download-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>📚 批量下载管理</h1>
      <p class="subtitle">填写小说链接，全自动下载完整小说</p>
    </div>

    <!-- 快速添加区域 -->
    <div class="quick-add-section">
      <div class="add-card">
        <h2>🚀 快速添加下载</h2>
        
        <!-- 单个链接添加 -->
        <div class="single-add">
          <div class="input-group">
            <input 
              v-model="singleUrl" 
              type="url" 
              placeholder="请输入小说链接，如：https://www.example.com/book/123/"
              class="url-input"
              @keyup.enter="addSingleDownload"
            />
            <input 
              v-model="singleName" 
              type="text" 
              placeholder="任务名称（可选）"
              class="name-input"
            />
            <button 
              @click="addSingleDownload" 
              :disabled="!singleUrl || isAdding"
              class="add-btn"
            >
              {{ isAdding ? '添加中...' : '开始下载' }}
            </button>
          </div>
        </div>

        <!-- 批量链接添加 -->
        <div class="batch-add">
          <h3>📋 批量添加（一行一个链接）</h3>
          <textarea 
            v-model="batchUrls" 
            placeholder="每行一个链接，格式：&#10;https://www.example.com/book/123/ 小说名称1&#10;https://www.example.com/book/456/ 小说名称2"
            class="batch-textarea"
            rows="5"
          ></textarea>
          <button 
            @click="addBatchDownloads" 
            :disabled="!batchUrls.trim() || isBatchAdding"
            class="batch-add-btn"
          >
            {{ isBatchAdding ? '批量添加中...' : '批量开始下载' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 任务统计 -->
    <div class="stats-section" v-if="stats">
      <div class="stats-grid">
        <div class="stat-card total">
          <div class="stat-number">{{ stats.total }}</div>
          <div class="stat-label">总任务</div>
        </div>
        <div class="stat-card running">
          <div class="stat-number">{{ stats.running }}</div>
          <div class="stat-label">下载中</div>
        </div>
        <div class="stat-card pending">
          <div class="stat-number">{{ stats.pending }}</div>
          <div class="stat-label">等待中</div>
        </div>
        <div class="stat-card completed">
          <div class="stat-number">{{ stats.completed }}</div>
          <div class="stat-label">已完成</div>
        </div>
        <div class="stat-card failed">
          <div class="stat-number">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="tasks-section">
      <div class="section-header">
        <h2>📋 下载任务列表</h2>
        <div class="filters">
          <select v-model="statusFilter" @change="loadTasks" class="status-filter">
            <option value="">全部状态</option>
            <option value="pending">等待中</option>
            <option value="running">下载中</option>
            <option value="paused">已暂停</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
            <option value="cancelled">已取消</option>
          </select>
          <button @click="loadTasks" class="refresh-btn">🔄 刷新</button>
        </div>
      </div>

      <!-- 任务卡片列表 -->
      <div class="tasks-list" v-if="tasks.length > 0">
        <div v-for="task in tasks" :key="task.id" class="task-card" :class="task.status">
          <div class="task-header">
            <div class="task-info">
              <h3 class="task-name">{{ task.name }}</h3>
              <div class="task-url">{{ task.source_url }}</div>
            </div>
            <div class="task-status" :class="task.status">
              {{ task.status_display }}
            </div>
          </div>

          <!-- 进度条 -->
          <div class="progress-section" v-if="task.total_chapters > 0">
            <div class="progress-info">
              <span>进度: {{ task.downloaded_chapters }}/{{ task.total_chapters }} 章</span>
              <span class="progress-percent">{{ Math.round(task.progress) }}%</span>
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: task.progress + '%' }"
                :class="task.status"
              ></div>
            </div>
            <div class="progress-details" v-if="task.failed_chapters > 0">
              <span class="failed-count">失败: {{ task.failed_chapters }} 章</span>
            </div>
          </div>

          <!-- 任务信息 -->
          <div class="task-details">
            <div class="detail-item">
              <span class="label">创建时间:</span>
              <span>{{ formatDate(task.created_at) }}</span>
            </div>
            <div class="detail-item" v-if="task.started_at">
              <span class="label">开始时间:</span>
              <span>{{ formatDate(task.started_at) }}</span>
            </div>
            <div class="detail-item" v-if="task.completed_at">
              <span class="label">完成时间:</span>
              <span>{{ formatDate(task.completed_at) }}</span>
            </div>
            <div class="detail-item" v-if="task.novel">
              <span class="label">小说:</span>
              <span>{{ task.novel.title }} - {{ task.novel.author }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="task-actions">
            <button 
              v-if="task.status === 'running'" 
              @click="pauseTask(task.id)"
              class="action-btn pause"
            >
              ⏸️ 暂停
            </button>
            <button 
              v-if="task.status === 'paused'" 
              @click="resumeTask(task.id)"
              class="action-btn resume"
            >
              ▶️ 恢复
            </button>
            <button 
              v-if="['pending', 'running', 'paused'].includes(task.status)" 
              @click="cancelTask(task.id)"
              class="action-btn cancel"
            >
              ❌ 取消
            </button>
            <button 
              @click="viewTaskDetail(task.id)"
              class="action-btn detail"
            >
              📋 详情
            </button>
            <button 
              v-if="task.novel" 
              @click="viewNovel(task.novel.id)"
              class="action-btn view"
            >
              📖 查看小说
            </button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon">📭</div>
        <div class="empty-text">暂无下载任务</div>
        <div class="empty-hint">添加小说链接开始自动下载吧！</div>
      </div>
    </div>

    <!-- 任务详情弹窗 -->
    <div v-if="showTaskDetail" class="modal-overlay" @click="closeTaskDetail">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📋 任务详情</h3>
          <button @click="closeTaskDetail" class="close-btn">✕</button>
        </div>
        <div class="modal-body" v-if="taskDetail">
          <!-- 任务基本信息 -->
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">任务名称:</span>
                <span>{{ taskDetail.name }}</span>
              </div>
              <div class="info-item">
                <span class="label">源链接:</span>
                <span class="url-text">{{ taskDetail.source_url }}</span>
              </div>
              <div class="info-item">
                <span class="label">状态:</span>
                <span class="status-badge" :class="taskDetail.status">{{ taskDetail.status_display }}</span>
              </div>
              <div class="info-item">
                <span class="label">进度:</span>
                <span>{{ taskDetail.downloaded_chapters }}/{{ taskDetail.total_chapters }} 章 ({{ Math.round(taskDetail.progress) }}%)</span>
              </div>
            </div>
          </div>

          <!-- 下载日志 -->
          <div class="detail-section" v-if="taskDetail.logs && taskDetail.logs.length > 0">
            <h4>下载日志</h4>
            <div class="logs-container">
              <div 
                v-for="log in taskDetail.logs" 
                :key="log.id" 
                class="log-item" 
                :class="log.level"
              >
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
                <span class="log-level">{{ log.level_display }}</span>
                <span class="log-message">{{ log.message }}</span>
                <span v-if="log.chapter_number" class="log-chapter">第{{ log.chapter_number }}章</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiService } from '@/services/api'

export default {
  name: 'BatchDownloadView',
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const singleUrl = ref('')
    const singleName = ref('')
    const batchUrls = ref('')
    const isAdding = ref(false)
    const isBatchAdding = ref(false)
    
    const tasks = ref([])
    const stats = ref(null)
    const statusFilter = ref('')
    
    const showTaskDetail = ref(false)
    const taskDetail = ref(null)
    
    // WebSocket连接管理
    const ws = ref(null)
    const wsConnected = ref(false)
    const wsReconnectAttempts = ref(0)
    const maxReconnectAttempts = 5

    // 加载任务统计
    const loadStats = async () => {
      try {
        const response = await apiService.batchDownload.stats()
        if (response.success) {
          stats.value = response.stats
        }
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    }
    
    // 加载任务列表
    const loadTasks = async () => {
      try {
        const params = {}
        if (statusFilter.value) {
          params.status = statusFilter.value
        }
        
        const response = await apiService.batchDownload.list(params)
        if (response.results) {
          tasks.value = response.results
        }
      } catch (error) {
        console.error('加载任务列表失败:', error)
        ElMessage.error('加载任务列表失败')
      }
    }
    
    // 添加单个下载任务
    const addSingleDownload = async () => {
      if (!singleUrl.value.trim()) {
        ElMessage.warning('请输入小说链接')
        return
      }
      
      isAdding.value = true
      try {
        const response = await apiService.batchDownload.create({
          source_url: singleUrl.value.trim(),
          task_name: singleName.value.trim() || undefined
        })
        
        if (response.success) {
          ElMessage.success('下载任务创建成功！')
          singleUrl.value = ''
          singleName.value = ''
          await loadTasks()
          await loadStats()
        } else {
          ElMessage.error(response.error || '创建任务失败')
        }
      } catch (error) {
        console.error('创建任务失败:', error)
        ElMessage.error('创建任务失败')
      } finally {
        isAdding.value = false
      }
    }
    
    // 批量添加下载任务
    const addBatchDownloads = async () => {
      if (!batchUrls.value.trim()) {
        ElMessage.warning('请输入小说链接')
        return
      }
      
      // 解析批量链接
      const lines = batchUrls.value.trim().split('\n')
      const urlsData = []
      
      for (const line of lines) {
        const trimmedLine = line.trim()
        if (!trimmedLine) continue
        
        const parts = trimmedLine.split(/\s+/)
        const url = parts[0]
        const name = parts.slice(1).join(' ')
        
        if (url.startsWith('http')) {
          urlsData.push({ url, name: name || undefined })
        }
      }
      
      if (urlsData.length === 0) {
        ElMessage.warning('没有找到有效的链接')
        return
      }
      
      isBatchAdding.value = true
      try {
        const response = await apiService.batchDownload.batchCreate({
          urls: urlsData
        })
        
        if (response.success) {
          ElMessage.success(response.message)
          batchUrls.value = ''
          await loadTasks()
          await loadStats()
          
          // 显示详细结果
          if (response.failed_urls.length > 0) {
            const failedInfo = response.failed_urls.map(f => `${f.url}: ${f.error}`).join('\n')
            ElMessageBox.alert(`失败的链接:\n${failedInfo}`, '批量添加结果', {
              type: 'warning'
            })
          }
        } else {
          ElMessage.error(response.error || '批量创建失败')
        }
      } catch (error) {
        console.error('批量创建失败:', error)
        ElMessage.error('批量创建失败')
      } finally {
        isBatchAdding.value = false
      }
    }
    
    // 暂停任务
    const pauseTask = async (taskId) => {
      try {
        const response = await apiService.batchDownload.pause(taskId)
        if (response.success) {
          ElMessage.success('任务已暂停')
          await loadTasks()
          await loadStats()
        } else {
          ElMessage.error(response.error || '暂停失败')
        }
      } catch (error) {
        console.error('暂停任务失败:', error)
        ElMessage.error('暂停任务失败')
      }
    }
    
    // 恢复任务
    const resumeTask = async (taskId) => {
      try {
        const response = await apiService.batchDownload.resume(taskId)
        if (response.success) {
          ElMessage.success('任务已恢复')
          await loadTasks()
          await loadStats()
        } else {
          ElMessage.error(response.error || '恢复失败')
        }
      } catch (error) {
        console.error('恢复任务失败:', error)
        ElMessage.error('恢复任务失败')
      }
    }
    
    // 取消任务
    const cancelTask = async (taskId) => {
      try {
        await ElMessageBox.confirm('确定要取消这个下载任务吗？', '确认取消', {
          type: 'warning'
        })
        
        const response = await apiService.batchDownload.cancel(taskId)
        if (response.success) {
          ElMessage.success('任务已取消')
          await loadTasks()
          await loadStats()
        } else {
          ElMessage.error(response.error || '取消失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('取消任务失败:', error)
          ElMessage.error('取消任务失败')
        }
      }
    }
    
    // 查看任务详情
    const viewTaskDetail = async (taskId) => {
      try {
        const response = await apiService.batchDownload.get(taskId)
        if (response.success) {
          taskDetail.value = response.task
          showTaskDetail.value = true
        } else {
          ElMessage.error('获取任务详情失败')
        }
      } catch (error) {
        console.error('获取任务详情失败:', error)
        ElMessage.error('获取任务详情失败')
      }
    }
    
    // 关闭任务详情
    const closeTaskDetail = () => {
      showTaskDetail.value = false
      taskDetail.value = null
    }
    
    // 查看小说
    const viewNovel = (novelId) => {
      router.push(`/novels/${novelId}/read`)
    }
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    // 格式化时间（简短）
    const formatTime = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleTimeString('zh-CN')
    }
    
    // 建立WebSocket连接
    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.host}/ws/batch-download/`
        
        ws.value = new WebSocket(wsUrl)
        
        ws.value.onopen = () => {
          wsConnected.value = true
          wsReconnectAttempts.value = 0
          
          // 发送认证信息
          const token = localStorage.getItem('token')
          if (token) {
            ws.value.send(JSON.stringify({
              type: 'auth',
              token: token
            }))
          }
        }
        
        ws.value.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            switch (data.type) {
              case 'task_update':
                handleTaskUpdate(data.data)
                break
              case 'task_complete':
                handleTaskComplete(data.data)
                break
              case 'task_error':
                handleTaskError(data.data)
                break
              case 'auth_success':
                break
              default:
                console.warn('未知WebSocket消息类型:', data.type)
            }
          } catch (error) {
            console.error('❌ 解析WebSocket消息失败:', error)
          }
        }
        
        ws.value.onclose = (event) => {
          wsConnected.value = false
          
          // 自动重连
          if (wsReconnectAttempts.value < maxReconnectAttempts) {
            wsReconnectAttempts.value++
            const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempts.value), 10000)
            setTimeout(connectWebSocket, delay)
          } else {
            console.error('❌ WebSocket重连失败，请刷新页面重试')
            ElMessage.error('WebSocket连接失败，请刷新页面重试')
          }
        }
        
        ws.value.onerror = (error) => {
          console.error('❌ WebSocket错误:', error)
        }
        
      } catch (error) {
        console.error('❌ 创建WebSocket连接失败:', error)
        ElMessage.error('WebSocket连接失败，请刷新页面重试')
      }
    }

    // 处理任务更新
    const handleTaskUpdate = (taskData) => {
      const taskIndex = tasks.value.findIndex(t => t.id === taskData.id)
      if (taskIndex >= 0) {
        tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...taskData }
      }
      updateStats()
    }

    // 处理任务完成
    const handleTaskComplete = (taskData) => {
      const taskIndex = tasks.value.findIndex(t => t.id === taskData.id)
      if (taskIndex >= 0) {
        tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...taskData }
        ElMessage.success(`任务 "${taskData.name}" 已完成！`)
      }
      updateStats()
    }

    // 处理任务错误
    const handleTaskError = (taskData) => {
      const taskIndex = tasks.value.findIndex(t => t.id === taskData.id)
      if (taskIndex >= 0) {
        tasks.value[taskIndex] = { ...tasks.value[taskIndex], ...taskData }
        ElMessage.error(`任务 "${taskData.name}" 出错: ${taskData.error}`)
      }
      updateStats()
    }
    
    // 初始化
    onMounted(() => {
      loadTasks()
      loadStats()
      connectWebSocket() // 启动WebSocket连接
      
      // 组件卸载时清除定时器
      return () => {
        if (ws.value) {
          ws.value.close()
        }
      }
    })
    
    return {
      // 数据
      singleUrl,
      singleName,
      batchUrls,
      isAdding,
      isBatchAdding,
      tasks,
      stats,
      statusFilter,
      showTaskDetail,
      taskDetail,
      
      // 方法
      addSingleDownload,
      addBatchDownloads,
      loadTasks,
      pauseTask,
      resumeTask,
      cancelTask,
      viewTaskDetail,
      closeTaskDetail,
      viewNovel,
      formatDate,
      formatTime
    }
  }
}
</script>

<style scoped>
.batch-download-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  color: #7f8c8d;
  font-size: 1.1em;
}

/* 快速添加区域 */
.quick-add-section {
  margin-bottom: 30px;
}

.add-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.add-card h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.url-input {
  flex: 2;
  min-width: 300px;
  padding: 12px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 14px;
}

.name-input {
  flex: 1;
  min-width: 150px;
  padding: 12px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 14px;
}

.add-btn {
  padding: 12px 24px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s;
}

.add-btn:hover:not(:disabled) {
  background: #219a52;
}

.add-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.batch-add {
  border-top: 1px solid #ecf0f1;
  padding-top: 20px;
}

.batch-add h3 {
  color: #34495e;
  margin-bottom: 15px;
}

.batch-textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 14px;
  font-family: monospace;
  resize: vertical;
  margin-bottom: 15px;
}

.batch-add-btn {
  padding: 12px 24px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s;
}

.batch-add-btn:hover:not(:disabled) {
  background: #2980b9;
}

.batch-add-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* 统计区域 */
.stats-section {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #bdc3c7;
}

.stat-card.total { border-left-color: #34495e; }
.stat-card.running { border-left-color: #f39c12; }
.stat-card.pending { border-left-color: #3498db; }
.stat-card.completed { border-left-color: #27ae60; }
.stat-card.failed { border-left-color: #e74c3c; }

.stat-number {
  font-size: 2em;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  color: #7f8c8d;
  margin-top: 5px;
}

/* 任务列表区域 */
.tasks-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.section-header h2 {
  color: #2c3e50;
  margin: 0;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.status-filter {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.refresh-btn {
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.refresh-btn:hover {
  background: #2980b9;
}

/* 任务卡片 */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.task-card {
  border: 1px solid #e1e8ed;
  border-radius: 12px;
  padding: 20px;
  background: #fafbfc;
  border-left: 4px solid #bdc3c7;
}

.task-card.pending { border-left-color: #3498db; }
.task-card.running { border-left-color: #f39c12; }
.task-card.completed { border-left-color: #27ae60; }
.task-card.failed { border-left-color: #e74c3c; }
.task-card.paused { border-left-color: #95a5a6; }
.task-card.cancelled { border-left-color: #7f8c8d; }

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.task-info {
  flex: 1;
}

.task-name {
  font-size: 1.2em;
  color: #2c3e50;
  margin: 0 0 5px 0;
}

.task-url {
  color: #7f8c8d;
  font-size: 0.9em;
  word-break: break-all;
}

.task-status {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: bold;
  color: white;
}

.task-status.pending { background: #3498db; }
.task-status.running { background: #f39c12; }
.task-status.completed { background: #27ae60; }
.task-status.failed { background: #e74c3c; }
.task-status.paused { background: #95a5a6; }
.task-status.cancelled { background: #7f8c8d; }

/* 进度条 */
.progress-section {
  margin-bottom: 15px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 0.9em;
  color: #34495e;
}

.progress-percent {
  font-weight: bold;
}

.progress-bar {
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.pending { background: #3498db; }
.progress-fill.running { background: #f39c12; }
.progress-fill.completed { background: #27ae60; }
.progress-fill.failed { background: #e74c3c; }
.progress-fill.paused { background: #95a5a6; }

.progress-details {
  margin-top: 5px;
}

.failed-count {
  color: #e74c3c;
  font-size: 0.85em;
}

/* 任务详情 */
.task-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  gap: 8px;
  font-size: 0.9em;
}

.detail-item .label {
  color: #7f8c8d;
  font-weight: bold;
  min-width: 80px;
}

/* 操作按钮 */
.task-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.3s;
}

.action-btn.pause { background: #f39c12; color: white; }
.action-btn.resume { background: #27ae60; color: white; }
.action-btn.cancel { background: #e74c3c; color: white; }
.action-btn.detail { background: #3498db; color: white; }
.action-btn.view { background: #9b59b6; color: white; }

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
}

.empty-icon {
  font-size: 4em;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 1.3em;
  margin-bottom: 10px;
}

.empty-hint {
  font-size: 1em;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  max-height: 80vh;
  width: 90%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-bottom: 1px solid #ecf0f1;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
  color: #7f8c8d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 25px;
  overflow-y: auto;
  flex: 1;
}

.detail-section {
  margin-bottom: 25px;
}

.detail-section h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  gap: 10px;
}

.info-item .label {
  font-weight: bold;
  color: #7f8c8d;
  min-width: 80px;
}

.url-text {
  word-break: break-all;
  color: #3498db;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: bold;
  color: white;
}

.status-badge.pending { background: #3498db; }
.status-badge.running { background: #f39c12; }
.status-badge.completed { background: #27ae60; }
.status-badge.failed { background: #e74c3c; }
.status-badge.paused { background: #95a5a6; }
.status-badge.cancelled { background: #7f8c8d; }

/* 日志样式 */
.logs-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ecf0f1;
  border-radius: 8px;
  background: #f8f9fa;
}

.log-item {
  display: flex;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid #ecf0f1;
  font-size: 0.85em;
  align-items: center;
}

.log-item:last-child {
  border-bottom: none;
}

.log-item.error {
  background: #fdf2f2;
  border-left: 3px solid #e74c3c;
}

.log-item.success {
  background: #f0f9f4;
  border-left: 3px solid #27ae60;
}

.log-item.warning {
  background: #fef9e7;
  border-left: 3px solid #f39c12;
}

.log-time {
  color: #7f8c8d;
  font-family: monospace;
  min-width: 80px;
}

.log-level {
  font-weight: bold;
  min-width: 50px;
}

.log-level.error { color: #e74c3c; }
.log-level.success { color: #27ae60; }
.log-level.warning { color: #f39c12; }
.log-level.info { color: #3498db; }

.log-message {
  flex: 1;
}

.log-chapter {
  color: #7f8c8d;
  font-size: 0.8em;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-download-container {
    padding: 15px;
  }
  
  .input-group {
    flex-direction: column;
  }
  
  .url-input,
  .name-input {
    min-width: auto;
  }
  
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .task-header {
    flex-direction: column;
  }
  
  .task-details {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
