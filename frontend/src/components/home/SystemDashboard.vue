<template>
  <div class="system-dashboard-section">
    <div class="section-header">
      <h3>📊 系统概览</h3>
      <div class="header-actions">
        <el-tag :type="systemStatus.overall === 'healthy' ? 'success' : 'warning'" size="small">
          {{ systemStatus.overall === 'healthy' ? '系统正常' : '需要关注' }}
        </el-tag>
      </div>
    </div>
    
    <div class="dashboard-grid">
      <!-- 今日统计 -->
      <div class="dashboard-card stats-card">
        <div class="card-header">
          <h4>📈 今日统计</h4>
          <span class="update-time">{{ formatUpdateTime(lastUpdate) }}</span>
        </div>
        <div class="stats-grid">
          <div class="stat-item" v-for="stat in todayStats" :key="stat.key">
            <div class="stat-icon" :class="stat.type">{{ stat.icon }}</div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
            <div class="stat-trend" :class="stat.trend">
              <span class="trend-icon">{{ getTrendIcon(stat.trend) }}</span>
              <span class="trend-value">{{ stat.change }}%</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 系统状态 -->
      <div class="dashboard-card status-card">
        <div class="card-header">
          <h4>🔧 系统状态</h4>
          <el-button @click="refreshStatus" size="small" type="primary" plain>
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="status-list">
          <div 
            class="status-item" 
            v-for="service in systemServices" 
            :key="service.key"
          >
            <div class="status-indicator">
              <div class="status-dot" :class="service.status"></div>
              <span class="status-label">{{ service.name }}</span>
            </div>
            <div class="status-info">
              <span class="status-text" :class="service.status">
                {{ getStatusText(service.status) }}
              </span>
              <span class="status-detail">{{ service.detail }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 性能监控 -->
      <div class="dashboard-card performance-card">
        <div class="card-header">
          <h4>⚡ 性能监控</h4>
        </div>
        <div class="performance-metrics">
          <div class="metric-item" v-for="metric in performanceMetrics" :key="metric.key">
            <div class="metric-header">
              <span class="metric-name">{{ metric.name }}</span>
              <span class="metric-value">{{ metric.value }}{{ metric.unit }}</span>
            </div>
            <div class="metric-bar">
              <div 
                class="metric-progress" 
                :class="getMetricLevel(metric.percentage)"
                :style="{ width: metric.percentage + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 快速操作 -->
      <div class="dashboard-card actions-card">
        <div class="card-header">
          <h4>🛠️ 快速操作</h4>
        </div>
        <div class="quick-actions">
          <el-button 
            v-for="action in quickActions" 
            :key="action.key"
            :type="action.type" 
            size="small"
            @click="handleQuickAction(action)"
            :loading="action.loading"
          >
            <span class="action-icon">{{ action.icon }}</span>
            {{ action.label }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const lastUpdate = ref(new Date())
const systemStatus = ref({ overall: 'healthy' })

// 今日统计数据
const todayStats = ref([
  {
    key: 'downloads',
    icon: '📥',
    label: '章节下载',
    value: 156,
    change: 12,
    trend: 'up',
    type: 'success'
  },
  {
    key: 'crawls',
    icon: '🕷️',
    label: '爬取任务',
    value: 8,
    change: -5,
    trend: 'down',
    type: 'warning'
  },
  {
    key: 'audio',
    icon: '🎵',
    label: '音频生成',
    value: 3,
    change: 25,
    trend: 'up',
    type: 'info'
  },
  {
    key: 'success_rate',
    icon: '✅',
    label: '成功率',
    value: '94.2%',
    change: 2.1,
    trend: 'up',
    type: 'primary'
  }
])

// 系统服务状态
const systemServices = ref([
  {
    key: 'crawler',
    name: '爬虫服务',
    status: 'healthy',
    detail: '运行正常'
  },
  {
    key: 'database',
    name: '数据库',
    status: 'healthy',
    detail: '连接稳定'
  },
  {
    key: 'audio',
    name: '音频服务',
    status: 'warning',
    detail: '队列繁忙'
  },
  {
    key: 'storage',
    name: '存储空间',
    status: 'healthy',
    detail: '75% 可用'
  }
])

// 性能指标
const performanceMetrics = ref([
  {
    key: 'cpu',
    name: 'CPU 使用率',
    value: 45,
    unit: '%',
    percentage: 45
  },
  {
    key: 'memory',
    name: '内存使用',
    value: 2.1,
    unit: 'GB',
    percentage: 68
  },
  {
    key: 'disk',
    name: '磁盘使用',
    value: 156,
    unit: 'GB',
    percentage: 32
  }
])

// 快速操作
const quickActions = reactive([
  {
    key: 'clear_cache',
    label: '清理缓存',
    icon: '🧹',
    type: 'warning',
    loading: false
  },
  {
    key: 'restart_crawler',
    label: '重启爬虫',
    icon: '🔄',
    type: 'primary',
    loading: false
  },
  {
    key: 'backup_data',
    label: '备份数据',
    icon: '💾',
    type: 'success',
    loading: false
  }
])

// 工具函数
const getTrendIcon = (trend) => {
  return trend === 'up' ? '↗️' : trend === 'down' ? '↘️' : '➡️'
}

const getStatusText = (status) => {
  const statusMap = {
    healthy: '正常',
    warning: '警告',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const getMetricLevel = (percentage) => {
  if (percentage < 50) return 'low'
  if (percentage < 80) return 'medium'
  return 'high'
}

const formatUpdateTime = (time) => {
  return time.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

// 事件处理
const refreshStatus = () => {
  lastUpdate.value = new Date()
  // 刷新统计数据
  todayStats.value.forEach(stat => {
    if (stat.key === 'downloads') {
      stat.value = Math.floor(Math.random() * 200) + 100
    } else if (stat.key === 'crawls') {
      stat.value = Math.floor(Math.random() * 15) + 5
    } else if (stat.key === 'audio') {
      stat.value = Math.floor(Math.random() * 8) + 2
    } else if (stat.key === 'success_rate') {
      stat.value = (Math.random() * 10 + 90).toFixed(1) + '%'
    }
  })
  ElMessage.success('状态已刷新')
}

const handleQuickAction = async (action) => {
  action.loading = true
  
  try {
    if (action.key === 'clear_cache') {
      // 模拟清理缓存
      await new Promise(resolve => setTimeout(resolve, 1500))
      ElMessage.success('缓存清理完成，释放了 156MB 空间')
    } else if (action.key === 'restart_crawler') {
      // 模拟重启爬虫
      await new Promise(resolve => setTimeout(resolve, 2500))
      // 更新爬虫服务状态
      const crawlerService = systemServices.value.find(s => s.key === 'crawler')
      if (crawlerService) {
        crawlerService.detail = '重启完成'
      }
      ElMessage.success('爬虫服务重启完成')
    } else if (action.key === 'backup_data') {
      // 模拟备份数据
      await new Promise(resolve => setTimeout(resolve, 3000))
      ElMessage.success('数据备份完成，保存到 backup_' + new Date().toISOString().slice(0, 10) + '.sql')
    }
  } catch (error) {
    ElMessage.error(`${action.label}失败: ${error.message}`)
  } finally {
    action.loading = false
  }
}

onMounted(() => {
  // 定时更新数据
  setInterval(() => {
    lastUpdate.value = new Date()
  }, 30000) // 30秒更新一次
})
</script>

<style scoped>
.system-dashboard-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.dashboard-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.dashboard-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.update-time {
  font-size: 0.8rem;
  color: #909399;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: #f5f7fa;
  transform: scale(1.02);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.stat-icon.success { background: #f0f9ff; }
.stat-icon.warning { background: #fef3e2; }
.stat-icon.info { background: #eff8ff; }
.stat-icon.primary { background: #f5f5f5; }

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
}

.stat-label {
  font-size: 0.8rem;
  color: #909399;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
}

.stat-trend.up { color: #67c23a; }
.stat-trend.down { color: #f56c6c; }

/* 状态卡片 */
.status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.healthy { background: #67c23a; }
.status-dot.warning { background: #e6a23c; }
.status-dot.error { background: #f56c6c; }

.status-label {
  font-weight: 500;
  color: #2c3e50;
}

.status-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.status-text {
  font-size: 0.9rem;
  font-weight: 500;
}

.status-text.healthy { color: #67c23a; }
.status-text.warning { color: #e6a23c; }
.status-text.error { color: #f56c6c; }

.status-detail {
  font-size: 0.8rem;
  color: #909399;
}

/* 性能卡片 */
.performance-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-name {
  font-size: 0.9rem;
  color: #606266;
}

.metric-value {
  font-weight: 600;
  color: #2c3e50;
}

.metric-bar {
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.metric-progress {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.metric-progress.low { background: #67c23a; }
.metric-progress.medium { background: #e6a23c; }
.metric-progress.high { background: #f56c6c; }

/* 操作卡片 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-icon {
  margin-right: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-card {
    padding: 16px;
  }
}
</style>
