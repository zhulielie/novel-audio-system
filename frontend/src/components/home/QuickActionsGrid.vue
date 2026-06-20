<template>
  <div class="quick-actions-section">
    <div class="section-header">
      <h2>快速操作</h2>
      <p>选择您需要的功能，一键直达</p>
    </div>
    
    <div class="actions-grid">
      <div 
        class="action-card" 
        v-for="action in actions" 
        :key="action.key"
        @click="handleActionClick(action)"
      >
        <div class="card-content">
          <div class="action-header">
            <div class="action-icon-wrapper" :class="action.type">
              <el-icon size="24">
                <component :is="action.icon" />
              </el-icon>
            </div>
            <div class="action-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
          
          <div class="action-body">
            <h3 class="action-title">{{ action.title }}</h3>
            <p class="action-description">{{ action.description }}</p>
          </div>
          
          <div class="action-footer" v-if="action.stats">
            <span class="stat-value">{{ action.stats.value }}</span>
            <span class="stat-label">{{ action.stats.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection, Reading, Headset, Lightning, ArrowRight } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const router = useRouter()

const statsData = ref({
  totalNovels: 0,
  audioProjects: 0,
  pendingTasks: 0,
  crawlerSuccessToday: 0
})

const fetchStats = async () => {
  try {
    const res = await apiService.get('/dashboard/stats/')
    statsData.value.totalNovels = res.stats?.novels || 0
    statsData.value.audioProjects = res.stats?.completed_audios || 0
    statsData.value.pendingTasks = res.stats?.tts_tasks || 0
    statsData.value.crawlerSuccessToday = 0
  } catch (e) {
    console.error('获取首页统计失败', e)
  }
}

onMounted(fetchStats)

const actions = computed(() => [
  {
    key: 'crawler',
    type: 'primary',
    icon: 'Connection',
    title: '智能爬虫',
    description: '一键获取小说内容，支持多个网站',
    route: '/crawler/integrated',
    stats: {
      value: statsData.value.crawlerSuccessToday,
      label: '今日成功'
    }
  },
  {
    key: 'novels',
    type: 'success',
    icon: 'Reading',
    title: '小说管理',
    description: '浏览和管理您的小说库',
    route: '/novels/list',
    stats: {
      value: statsData.value.totalNovels,
      label: '总计小说'
    }
  },
  {
    key: 'audio',
    type: 'warning',
    icon: 'Headset',
    title: '音频生成',
    description: '将文字转换为高质量语音',
    route: '/tts/synthesize',
    stats: {
      value: statsData.value.audioProjects,
      label: '音频项目'
    }
  },
  {
    key: 'batch',
    type: 'info',
    icon: 'Lightning',
    title: '批量导入',
    description: '快速批量处理小说数据',
    route: '/crawler/batch',
    stats: {
      value: statsData.value.pendingTasks,
      label: '待处理'
    }
  }
])

const handleActionClick = (action) => {
  if (action.route) {
    router.push(action.route)
  }
}
</script>

<style scoped>
.quick-actions-section {
  padding: 8px 24px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.section-header p {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.action-card {
  cursor: pointer;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.action-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-200);
}

.action-card:hover .action-arrow {
  background: var(--primary-50);
  color: var(--primary-600);
  transform: translateX(2px);
}

.card-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.action-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.action-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon-wrapper.primary {
  background: var(--primary-50);
  color: var(--primary-600);
}

.action-icon-wrapper.success {
  background: var(--success-50);
  color: var(--success-600);
}

.action-icon-wrapper.warning {
  background: var(--warning-50);
  color: var(--warning-600);
}

.action-icon-wrapper.info {
  background: var(--info-50);
  color: var(--info-600);
}

.action-arrow {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: all 0.2s ease;
}

.action-body {
  flex: 1;
  margin-bottom: 16px;
}

.action-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px 0;
}

.action-description {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.action-footer {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color-light);
}

.stat-value {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

@media (max-width: 1200px) {
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .quick-actions-section {
    padding: 8px 16px 24px;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .action-card {
    padding: 20px;
  }
}
</style>
