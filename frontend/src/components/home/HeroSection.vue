<template>
  <div class="hero-section">
    <div class="hero-content">
      <div class="hero-text">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          系统运行正常
        </div>
        <h1 class="hero-title">智能小说管理系统</h1>
        <p class="hero-subtitle">您的专属小说数字化助手，让阅读、创作与音频生成更加智能高效</p>
        
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="handleBrowseNovels">
            浏览小说库
          </el-button>
          <el-button size="large" plain @click="handleStartCrawler">
            开始爬取
          </el-button>
        </div>
      </div>
      
      <div class="hero-stats">
        <div class="stat-card" v-for="stat in stats" :key="stat.key">
          <div class="stat-icon-wrapper" :class="stat.type">
            <el-icon size="22">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Reading, Document, Headset, CircleCheck } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const stats = ref([
  { key: 'novels', value: 0, label: '本小说', icon: 'Reading', type: 'primary' },
  { key: 'chapters', value: 0, label: '个章节', icon: 'Document', type: 'success' },
  { key: 'audio', value: 0, label: '已生成音频', icon: 'Headset', type: 'warning' },
  { key: 'tts', value: 0, label: 'TTS 任务', icon: 'CircleCheck', type: 'info' }
])

const router = useRouter()

const handleBrowseNovels = () => {
  router.push('/novels/list')
}

const handleStartCrawler = () => {
  router.push('/crawler/integrated')
}

const loadStats = async () => {
  try {
    const response = await apiService.get('/dashboard/stats/')
    const data = response?.stats || {}
    stats.value[0].value = data.novels || 0
    stats.value[1].value = data.chapters || 0
    stats.value[2].value = data.completed_audios || 0
    stats.value[3].value = data.tts_tasks || 0
  } catch (error) {
    console.warn('加载统计数据失败，使用默认值:', error)
    stats.value[0].value = 0
    stats.value[1].value = 0
    stats.value[2].value = 0
    stats.value[3].value = 0
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.hero-section {
  padding: 32px 24px 24px;
}

.hero-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 48px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 40px 48px;
  box-shadow: var(--shadow-sm);
}

.hero-text {
  flex: 1;
  max-width: 560px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--success-50);
  color: var(--success-600);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 16px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success-500);
  animation: pulse 2s infinite;
}

.hero-title {
  font-size: 36px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 12px 0;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--text-muted);
  margin: 0 0 28px 0;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  min-width: 360px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon-wrapper {
  width: 46px;
  height: 46px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-wrapper.primary {
  background: var(--primary-50);
  color: var(--primary-600);
}

.stat-icon-wrapper.success {
  background: var(--success-50);
  color: var(--success-600);
}

.stat-icon-wrapper.warning {
  background: var(--warning-50);
  color: var(--warning-600);
}

.stat-icon-wrapper.info {
  background: var(--info-50);
  color: var(--info-600);
}

.stat-number {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (max-width: 1024px) {
  .hero-content {
    flex-direction: column;
    align-items: flex-start;
    padding: 32px;
  }
  
  .hero-stats {
    width: 100%;
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 20px 16px 16px;
  }
  
  .hero-content {
    padding: 24px;
  }
  
  .hero-title {
    font-size: 28px;
  }
  
  .hero-stats {
    grid-template-columns: 1fr;
  }
  
  .hero-actions {
    flex-direction: column;
    width: 100%;
  }
}
</style>
