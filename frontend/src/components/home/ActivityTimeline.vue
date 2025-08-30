<template>
  <div class="activity-timeline-section">
    <div class="section-header">
      <h3>🕐 实时动态</h3>
      <el-button @click="refreshActivities" size="small" type="primary" plain>
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
        :style="{ animationDelay: `${index * 0.1}s` }"
        @click="handleActivityClick(activity)"
      >
        <div class="timeline-dot" :class="activity.type">
          <span class="dot-icon">{{ getActivityIcon(activity.type) }}</span>
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
            >
              {{ tag.label }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="activities.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <p>暂无活动记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 响应式数据
const activities = ref([])

// 模拟活动数据
const mockActivities = [
  {
    id: 1,
    type: 'success',
    title: '爬虫任务完成',
    description: '成功导入小说《问鼎》前10章',
    time: new Date(Date.now() - 2 * 60 * 1000), // 2分钟前
    meta: [
      { key: 'chapters', label: '10章', type: 'success' },
      { key: 'source', label: '和图书网', type: 'info' }
    ],
    clickable: true,
    route: '/novels/47' // 问鼎小说的ID是47
  },
  {
    id: 2,
    type: 'info',
    title: '音频生成启动',
    description: '开始为《斗破苍穹》生成语音文件',
    time: new Date(Date.now() - 5 * 60 * 1000), // 5分钟前
    meta: [
      { key: 'voice', label: '男声', type: 'primary' },
      { key: 'quality', label: '高质量', type: 'success' }
    ]
  },
  {
    id: 3,
    type: 'warning',
    title: '目录提取',
    description: '正在提取《全职高手》章节目录...',
    time: new Date(Date.now() - 8 * 60 * 1000), // 8分钟前
    meta: [
      { key: 'status', label: '进行中', type: 'warning' }
    ]
  },
  {
    id: 4,
    type: 'primary',
    title: '系统启动',
    description: '智能小说管理系统启动完成',
    time: new Date(Date.now() - 15 * 60 * 1000), // 15分钟前
    meta: [
      { key: 'version', label: 'v2.0', type: 'primary' }
    ]
  },
  {
    id: 5,
    type: 'success',
    title: '批量导入完成',
    description: '成功导入5本小说，共计1,234章',
    time: new Date(Date.now() - 30 * 60 * 1000), // 30分钟前
    meta: [
      { key: 'novels', label: '5本', type: 'success' },
      { key: 'chapters', label: '1,234章', type: 'info' }
    ]
  }
]

// 获取活动图标
const getActivityIcon = (type) => {
  const iconMap = {
    success: '✅',
    info: 'ℹ️',
    warning: '⚠️',
    primary: '🚀',
    danger: '❌'
  }
  return iconMap[type] || '📝'
}

// 格式化时间
const formatTime = (time) => {
  const now = new Date()
  const diff = now - time
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  return `${days}天前`
}

// 处理活动点击
const handleActivityClick = (activity) => {
  if (activity.clickable && activity.route) {
    router.push(activity.route)
  }
}

// 刷新活动
const refreshActivities = () => {
  // 添加一个新的活动到列表顶部
  const newActivity = {
    id: Date.now(),
    type: 'info',
    title: '数据刷新',
    description: '首页数据已更新',
    time: new Date(),
    meta: [
      { key: 'status', label: '完成', type: 'success' }
    ]
  }
  activities.value = [newActivity, ...mockActivities]
  ElMessage.success('活动数据已刷新')
}

// 加载活动数据
const loadActivities = async () => {
  try {
    // 暂时使用模拟数据
    activities.value = mockActivities
  } catch (error) {
    console.error('加载活动数据失败:', error)
  }
}

onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-timeline-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  height: 400px;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.section-header h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.timeline-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.timeline-container::-webkit-scrollbar {
  width: 4px;
}

.timeline-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.timeline-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.timeline-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20px;
  position: relative;
  animation: slideInUp 0.5s ease-out;
  opacity: 0;
  animation-fill-mode: forwards;
}

.timeline-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 18px;
  top: 36px;
  bottom: -20px;
  width: 2px;
  background: linear-gradient(to bottom, #e0e0e0, transparent);
}

.timeline-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.timeline-dot.success {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.timeline-dot.info {
  background: linear-gradient(135deg, #409eff, #79bbff);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.timeline-dot.warning {
  background: linear-gradient(135deg, #e6a23c, #f0c78a);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
}

.timeline-dot.primary {
  background: linear-gradient(135deg, #606266, #909399);
  box-shadow: 0 4px 12px rgba(96, 98, 102, 0.3);
}

.timeline-dot.danger {
  background: linear-gradient(135deg, #f56c6c, #f89898);
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

.dot-icon {
  color: white;
  font-size: 0.9rem;
}

.timeline-content {
  flex: 1;
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  border-left: 3px solid #e0e0e0;
  transition: all 0.3s ease;
}

.timeline-item:hover .timeline-content {
  background: #f5f7fa;
  border-left-color: #409eff;
  transform: translateX(4px);
}

.timeline-item.clickable {
  cursor: pointer;
}

.timeline-item.clickable:hover {
  transform: scale(1.02);
  transition: all 0.2s ease;
}

.timeline-item.clickable .timeline-content {
  transition: all 0.3s ease;
}

.timeline-item.clickable:hover .timeline-content {
  background: #e8f4fd;
  border-left-color: #409eff;
  transform: translateX(8px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.activity-title {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.activity-time {
  font-size: 0.8rem;
  color: #909399;
}

.activity-description {
  color: #606266;
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 12px;
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
  color: #909399;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 0.9rem;
}

/* 动画效果 */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .activity-timeline-section {
    padding: 16px;
    height: 350px;
  }
  
  .timeline-dot {
    width: 32px;
    height: 32px;
    margin-right: 12px;
  }
  
  .dot-icon {
    font-size: 0.8rem;
  }
  
  .timeline-content {
    padding: 12px;
  }
  
  .activity-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
