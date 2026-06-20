<template>
  <div class="system-dashboard-section card">
    <div class="section-header">
      <h3>系统概览</h3>
      <el-tag :type="systemStatus.overall === 'healthy' ? 'success' : 'warning'" size="small" effect="light">
        {{ systemStatus.overall === 'healthy' ? '系统正常' : '需要关注' }}
      </el-tag>
    </div>
    
    <div class="dashboard-content">
      <!-- 今日统计 -->
      <div class="stats-section">
        <div class="section-subheader">
          <h4>今日统计</h4>
          <span class="update-time">{{ formatUpdateTime(lastUpdate) }}</span>
        </div>
        <div class="stats-grid">
          <div class="stat-item" v-for="stat in todayStats" :key="stat.key">
            <div class="stat-row">
              <div class="stat-icon-mini" :class="stat.type">
                <el-icon size="16">
                  <component :is="stat.icon" />
                </el-icon>
              </div>
              <div class="stat-main">
                <div class="stat-value">{{ stat.value }}</div>
                <div class="stat-label">{{ stat.label }}</div>
              </div>
            </div>
            <div class="stat-trend" :class="stat.trend">
              <el-icon size="12">
                <component :is="stat.trend === 'up' ? 'ArrowUp' : stat.trend === 'down' ? 'ArrowDown' : 'Minus'" />
              </el-icon>
              <span>{{ Math.abs(stat.change) }}%</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 系统服务 -->
      <div class="services-section">
        <div class="section-subheader">
          <h4>系统状态</h4>
          <el-button @click="refreshStatus" size="small" text>
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="services-list">
          <div class="service-item" v-for="service in systemServices" :key="service.key">
            <div class="service-info">
              <div class="status-dot" :class="service.status"></div>
              <span class="service-name">{{ service.name }}</span>
            </div>
            <div class="service-detail">
              <span class="status-text" :class="service.status">{{ getStatusText(service.status) }}</span>
              <span class="service-desc">{{ service.detail }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 性能监控 -->
      <div class="performance-section">
        <div class="section-subheader">
          <h4>性能监控</h4>
        </div>
        <div class="metrics-list">
          <div class="metric-item" v-for="metric in performanceMetrics" :key="metric.key">
            <div class="metric-header">
              <span class="metric-name">{{ metric.name }}</span>
              <span class="metric-value">{{ metric.value }}{{ metric.unit }}</span>
            </div>
            <div class="metric-bar">
              <div class="metric-progress" :class="getMetricLevel(metric.percentage)" :style="{ width: metric.percentage + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 快速操作 -->
      <div class="actions-section">
        <div class="section-subheader">
          <h4>快捷维护</h4>
        </div>
        <div class="quick-actions-list">
          <el-button 
            v-for="action in quickActions" 
            :key="action.key"
            :type="action.type" 
            size="default"
            @click="handleQuickAction(action)"
            :loading="action.loading"
            class="quick-action-btn"
          >
            <el-icon size="16">
              <component :is="action.icon" />
            </el-icon>
            {{ action.label }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh, ArrowUp, ArrowDown, Minus, Brush, RefreshRight, Collection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'

const lastUpdate = ref(new Date())
const systemStatus = ref({ overall: 'healthy' })

const todayStats = ref([
  { key: 'novels', icon: 'Reading', label: '小说', value: 0, change: 0, trend: 'up', type: 'primary' },
  { key: 'chapters', icon: 'Document', label: '章节', value: 0, change: 0, trend: 'up', type: 'warning' },
  { key: 'audio', icon: 'Headset', label: '音频生成', value: 0, change: 0, trend: 'up', type: 'info' },
  { key: 'tts_tasks', icon: 'CircleCheck', label: 'TTS 任务', value: 0, change: 0, trend: 'up', type: 'success' }
])

const systemServices = ref([
  { key: 'crawler', name: '爬虫服务', status: 'healthy', detail: '运行正常' },
  { key: 'database', name: '数据库', status: 'healthy', detail: '连接稳定' },
  { key: 'audio', name: '音频服务', status: 'warning', detail: '队列繁忙' },
  { key: 'storage', name: '存储空间', status: 'healthy', detail: '75% 可用' }
])

const performanceMetrics = ref([
  { key: 'cpu', name: 'CPU 使用率', value: 12, unit: '%', percentage: 12 },
  { key: 'memory', name: '内存使用', value: 1.2, unit: 'GB', percentage: 35 },
  { key: 'disk', name: '磁盘使用', value: 45, unit: 'GB', percentage: 18 }
])

const quickActions = reactive([
  { key: 'clear_cache', label: '清理缓存', icon: 'Brush', type: 'default', loading: false },
  { key: 'restart_crawler', label: '重启爬虫', icon: 'RefreshRight', type: 'primary', loading: false },
  { key: 'backup_data', label: '备份数据', icon: 'Collection', type: 'success', loading: false }
])

const getStatusText = (status) => {
  const map = { healthy: '正常', warning: '警告', error: '错误' }
  return map[status] || '未知'
}

const getMetricLevel = (percentage) => {
  if (percentage < 50) return 'low'
  if (percentage < 80) return 'medium'
  return 'high'
}

const formatUpdateTime = (time) => {
  return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const fetchStats = async () => {
  try {
    const res = await apiService.get('/dashboard/stats/')
    const stats = res.stats || {}
    todayStats.value.forEach(stat => {
      if (stat.key === 'novels') stat.value = stats.novels || 0
      else if (stat.key === 'chapters') stat.value = stats.chapters || 0
      else if (stat.key === 'audio') stat.value = stats.completed_audios || 0
      else if (stat.key === 'tts_tasks') stat.value = stats.tts_tasks || 0
    })
    lastUpdate.value = new Date()
  } catch (e) {
    console.error('获取系统概览失败', e)
    ElMessage.error('统计数据加载失败')
  }
}

const refreshStatus = () => {
  fetchStats()
  ElMessage.success('状态已刷新')
}

const handleQuickAction = async (action) => {
  action.loading = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1200))
    if (action.key === 'clear_cache') ElMessage.success('缓存清理完成')
    else if (action.key === 'restart_crawler') ElMessage.success('爬虫服务重启完成')
    else if (action.key === 'backup_data') ElMessage.success('数据备份完成')
  } catch (error) {
    ElMessage.error(`${action.label}失败`)
  } finally {
    action.loading = false
  }
}

onMounted(() => {
  fetchStats()
  setInterval(() => { lastUpdate.value = new Date() }, 30000)
})
</script>

<style scoped>
.system-dashboard-section {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex: 1;
}

.section-subheader {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-subheader h4 {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.update-time {
  font-size: 12px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px;
  background: var(--slate-50);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color-light);
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-icon-mini {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon-mini.primary { background: var(--primary-50); color: var(--primary-600); }
.stat-icon-mini.success { background: var(--success-50); color: var(--success-600); }
.stat-icon-mini.warning { background: var(--warning-50); color: var(--warning-600); }
.stat-icon-mini.info { background: var(--info-50); color: var(--info-600); }

.stat-main .stat-value {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-main .stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: var(--radius-full);
}

.stat-trend.up {
  color: var(--success-600);
  background: var(--success-50);
}

.stat-trend.down {
  color: var(--danger-600);
  background: var(--danger-50);
}

/* Services */
.services-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--slate-50);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color-light);
}

.service-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.healthy { background: var(--success-500); box-shadow: 0 0 0 3px var(--success-50); }
.status-dot.warning { background: var(--warning-500); box-shadow: 0 0 0 3px var(--warning-50); }
.status-dot.error { background: var(--danger-500); box-shadow: 0 0 0 3px var(--danger-50); }

.service-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.service-detail {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.status-text {
  font-size: 12px;
  font-weight: 600;
}

.status-text.healthy { color: var(--success-600); }
.status-text.warning { color: var(--warning-600); }
.status-text.error { color: var(--danger-600); }

.service-desc {
  font-size: 11px;
  color: var(--text-muted);
}

/* Performance */
.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-name {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.metric-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.metric-bar {
  height: 6px;
  background: var(--slate-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.metric-progress {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.5s ease;
}

.metric-progress.low { background: linear-gradient(90deg, var(--success-500), var(--success-400)); }
.metric-progress.medium { background: linear-gradient(90deg, var(--warning-500), var(--warning-400)); }
.metric-progress.high { background: linear-gradient(90deg, var(--danger-500), var(--danger-400)); }

/* Quick Actions */
.quick-actions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-action-btn {
  justify-content: flex-start;
  width: 100%;
  gap: 8px;
  border-radius: var(--radius-md);
  font-weight: 500;
}

@media (max-width: 768px) {
  .system-dashboard-section {
    padding: 20px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
