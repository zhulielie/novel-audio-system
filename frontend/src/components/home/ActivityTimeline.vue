<template>
  <div class="activity-timeline-section card">
    <div class="section-header">
      <h3>实时动态</h3>
      <el-button @click="refreshActivities" size="small" text>
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>
    
    <div class="timeline-container">
      <div 
        class="timeline-item" 
        :class="{ 'clickable': activity.clickable }"
        v-for="(activity, index) in activities" 
        :key="activity.id"
        @click="handleActivityClick(activity)"
      >
        <div class="timeline-line" v-if="index !== activities.length - 1"></div>
        <div class="timeline-dot" :class="activity.type">
          <el-icon size="14">
            <component :is="getActivityIcon(activity.type)" />
          </el-icon>
        </div>
        
        <div class="timeline-content">
          <div class="activity-header">
            <span class="activity-title">{{ activity.title }}</span>
            <span class="activity-time">{{ formatTime(activity.time) }}</span>
          </div>
          <div class="activity-description">{{ activity.description }}</div>
          <div class="activity-meta" v-if="activity.meta">
            <el-tag 
              v-for="tag in activity.meta" 
              :key="tag.key" 
              :type="tag.type" 
              size="small"
              effect="light"
            >
              {{ tag.label }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <div v-if="activities.length === 0" class="empty-state">
        <el-icon size="40" class="empty-icon"><Document /></el-icon>
        <p>暂无活动记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, CircleCheck, InfoFilled, WarningFilled, TopRight, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'

const router = useRouter()
const activities = ref([])

const buildActivities = (data) => {
  const list = []
  const recentNovels = data.recent_activity?.novels || []
  const recentChapters = data.recent_activity?.chapters || []
  const recentTasks = data.recent_activity?.tasks || []

  recentNovels.forEach((novel, index) => {
    list.push({
      id: `novel-${novel.id}`,
      type: 'success',
      title: `新增小说：${novel.title}`,
      description: '通过智能爬虫导入到书库',
      time: new Date(novel.created_at),
      clickable: true,
      route: `/novels/list`
    })
  })

  recentChapters.forEach((chapter) => {
    list.push({
      id: `chapter-${chapter.id}`,
      type: 'info',
      title: `新增章节：${chapter.title}`,
      description: `来自小说《${chapter.novel_title}》`,
      time: new Date(chapter.created_at)
    })
  })

  recentTasks.forEach((task) => {
    const statusMap = {
      completed: 'success',
      failed: 'danger',
      pending: 'info',
      generating: 'warning'
    }
    list.push({
      id: `task-${task.id}`,
      type: statusMap[task.status] || 'info',
      title: `TTS 任务：${task.name}`,
      description: `状态 ${task.status}`,
      time: new Date(task.created_at),
      clickable: true,
      route: '/tts/synthesize'
    })
  })

  return list.length ? list : [{
    id: 'empty',
    type: 'info',
    title: '暂无动态',
    description: '开始一次小说爬取或音频合成吧',
    time: new Date()
  }]
}

const fetchActivities = async () => {
  try {
    const res = await apiService.get('/dashboard/stats/')
    activities.value = buildActivities(res)
  } catch (e) {
    console.error('获取动态失败', e)
  }
}

const getActivityIcon = (type) => {
  const map = {
    success: 'CircleCheck',
    info: 'InfoFilled',
    warning: 'WarningFilled',
    primary: 'TopRight',
    danger: 'CircleClose'
  }
  return map[type] || 'Document'
}

const formatTime = (time) => {
  const diff = Date.now() - time
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
}

const handleActivityClick = (activity) => {
  if (activity.clickable && activity.route) {
    router.push(activity.route)
  }
}

const refreshActivities = () => {
  fetchActivities()
  ElMessage.success('活动数据已刷新')
}

onMounted(() => {
  fetchActivities()
})
</script>

<style scoped>
.activity-timeline-section {
  padding: 24px;
  height: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.timeline-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  position: relative;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 0;
  position: relative;
  transition: all 0.2s ease;
  border-radius: var(--radius-md);
}

.timeline-item:hover {
  background: var(--slate-50);
  margin: 0 -12px;
  padding-left: 12px;
  padding-right: 12px;
}

.timeline-item.clickable {
  cursor: pointer;
}

.timeline-line {
  position: absolute;
  left: 19px;
  top: 48px;
  bottom: -8px;
  width: 2px;
  background: var(--border-color);
}

.timeline-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 2;
  color: white;
}

.timeline-dot.success { background: var(--success-500); }
.timeline-dot.info { background: var(--info-500); }
.timeline-dot.warning { background: var(--warning-500); }
.timeline-dot.primary { background: var(--primary-500); }
.timeline-dot.danger { background: var(--danger-500); }

.timeline-content {
  flex: 1;
  min-width: 0;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 12px;
}

.activity-title {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 14px;
}

.activity-time {
  font-size: 12px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.activity-description {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 10px;
}

.activity-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-muted);
}

.empty-icon {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

@media (max-width: 768px) {
  .activity-timeline-section {
    padding: 20px;
  }
  
  .activity-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
