<template>
  <div class="hero-section">
    <div class="hero-background">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">
            <span class="icon">🎯</span>
            智能小说管理系统
          </h1>
          <p class="hero-subtitle">您的专属小说数字化助手，让阅读更智能</p>
        </div>
        
        <div class="live-stats">
          <div class="stat-item" v-for="stat in stats" :key="stat.key">
            <div class="stat-number">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
      
      <!-- 装饰性元素 -->
      <div class="hero-decoration">
        <div class="floating-element" v-for="n in 6" :key="n" :style="getFloatingStyle(n)">
          {{ getFloatingIcon(n) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

// 响应式数据
const dashboardData = ref({
  total_novels: 0,
  total_chapters: 0,
  today_downloads: 0,
  crawler_success_today: 0
})

// 计算统计数据
const stats = computed(() => [
  {
    key: 'novels',
    value: dashboardData.value.total_novels,
    label: '本小说'
  },
  {
    key: 'chapters', 
    value: dashboardData.value.total_chapters,
    label: '个章节'
  },
  {
    key: 'downloads',
    value: dashboardData.value.today_downloads,
    label: '今日下载'
  },
  {
    key: 'success',
    value: dashboardData.value.crawler_success_today,
    label: '爬取成功'
  }
])

// 装饰元素样式
const getFloatingStyle = (index) => {
  const positions = [
    { top: '10%', left: '10%', animationDelay: '0s' },
    { top: '20%', right: '15%', animationDelay: '1s' },
    { top: '60%', left: '5%', animationDelay: '2s' },
    { top: '70%', right: '10%', animationDelay: '0.5s' },
    { top: '30%', left: '80%', animationDelay: '1.5s' },
    { top: '80%', left: '70%', animationDelay: '2.5s' }
  ]
  return positions[index - 1] || {}
}

const getFloatingIcon = (index) => {
  const icons = ['📚', '🎵', '⚡', '🕷️', '📊', '🚀']
  return icons[index - 1] || '✨'
}

// 获取首页数据
const loadDashboardData = async () => {
  try {
    // 暂时使用模拟数据，后面会添加真实API
    dashboardData.value = {
      total_novels: 47,
      total_chapters: 2208,
      today_downloads: 156,
      crawler_success_today: 12
    }
  } catch (error) {
    console.error('加载首页数据失败:', error)
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.hero-section {
  margin: -20px -20px 30px -20px;
  position: relative;
  overflow: hidden;
}

.hero-background {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  position: relative;
  padding: 60px 40px;
  color: white;
  min-height: 200px;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

.hero-text {
  flex: 1;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-title .icon {
  font-size: 3rem;
  animation: pulse 2s infinite;
}

.hero-subtitle {
  font-size: 1.2rem;
  margin: 0;
  opacity: 0.9;
  font-weight: 300;
}

.live-stats {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  min-width: 120px;
}

.stat-item:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-5px);
}

.stat-number {
  font-size: 2.2rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  font-weight: 400;
}

.hero-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.floating-element {
  position: absolute;
  font-size: 2rem;
  opacity: 0.1;
  animation: float 6s ease-in-out infinite;
}

/* 动画效果 */
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes float {
  0%, 100% { 
    transform: translateY(0px) rotate(0deg);
    opacity: 0.1;
  }
  50% { 
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.3;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-content {
    flex-direction: column;
    text-align: center;
    gap: 30px;
  }
  
  .hero-title {
    font-size: 2rem;
    justify-content: center;
  }
  
  .live-stats {
    justify-content: center;
    gap: 20px;
  }
  
  .stat-item {
    min-width: 100px;
    padding: 15px;
  }
  
  .stat-number {
    font-size: 1.8rem;
  }
}

@media (max-width: 480px) {
  .hero-background {
    padding: 40px 20px;
  }
  
  .hero-title {
    font-size: 1.8rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .live-stats {
    flex-direction: column;
    align-items: center;
  }
}
</style>
