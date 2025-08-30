<template>
  <div class="quick-actions-section">
    <div class="section-header">
      <h2>🚀 快速操作</h2>
      <p>选择您需要的功能，一键直达</p>
    </div>
    
    <div class="actions-grid">
      <div 
        class="action-card" 
        v-for="action in actions" 
        :key="action.key"
        :class="action.type"
        @click="handleActionClick(action)"
      >
        <div class="card-background">
          <div class="card-content">
            <div class="action-icon">{{ action.icon }}</div>
            <h3 class="action-title">{{ action.title }}</h3>
            <p class="action-description">{{ action.description }}</p>
            
            <div class="action-stats" v-if="action.stats">
              <div class="stat-badge">
                <span class="stat-value">{{ action.stats.value }}</span>
                <span class="stat-label">{{ action.stats.label }}</span>
              </div>
            </div>
            
            <div class="action-button">
              <span>立即使用</span>
              <i class="arrow">→</i>
            </div>
          </div>
          
          <!-- 装饰性背景图案 -->
          <div class="card-pattern">
            <div class="pattern-dot" v-for="n in 12" :key="n"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 模拟统计数据（后面会从API获取）
const statsData = ref({
  totalNovels: 47,
  audioProjects: 12,
  pendingTasks: 3,
  crawlerSuccessToday: 8
})

// 快捷操作配置
const actions = computed(() => [
  {
    key: 'crawler',
    type: 'primary',
    icon: '🕷️',
    title: '智能爬虫',
    description: '一键获取小说内容，支持多个网站',
    route: '/integrated-crawler',
    stats: {
      value: statsData.value.crawlerSuccessToday,
      label: '今日成功'
    }
  },
  {
    key: 'novels',
    type: 'success',
    icon: '📚',
    title: '小说管理',
    description: '浏览和管理您的小说库',
    route: '/novels',
    stats: {
      value: statsData.value.totalNovels,
      label: '总计小说'
    }
  },
  {
    key: 'audio',
    type: 'warning',
    icon: '🎵',
    title: '音频生成',
    description: '将文字转换为高质量语音',
    route: '/audio-projects',
    stats: {
      value: statsData.value.audioProjects,
      label: '音频项目'
    }
  },
  {
    key: 'batch',
    type: 'info',
    icon: '⚡',
    title: '批量导入',
    description: '快速批量处理小说数据',
    route: '/batch-import',
    stats: {
      value: statsData.value.pendingTasks,
      label: '待处理'
    }
  }
])

// 处理点击事件
const handleActionClick = (action) => {
  if (action.route) {
    router.push(action.route)
  }
}
</script>

<style scoped>
.quick-actions-section {
  margin-bottom: 40px;
}

.section-header {
  text-align: center;
  margin-bottom: 40px;
}

.section-header h2 {
  font-size: 2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.section-header p {
  font-size: 1rem;
  color: #7f8c8d;
  margin: 0;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.action-card {
  cursor: pointer;
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  height: 200px;
}

.action-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.card-background {
  position: relative;
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}

/* 不同类型的卡片颜色 */
.action-card.primary .card-background {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.action-card.success .card-background {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
  color: white;
}

.action-card.warning .card-background {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.action-card.info .card-background {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.card-content {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.action-icon {
  font-size: 3rem;
  margin-bottom: 12px;
  display: block;
}

.action-title {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.action-description {
  font-size: 0.9rem;
  margin: 0 0 16px 0;
  opacity: 0.9;
  line-height: 1.4;
  flex: 1;
}

.action-stats {
  margin-bottom: 16px;
}

.stat-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.2);
  padding: 6px 12px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
}

.stat-label {
  font-size: 0.8rem;
  opacity: 0.8;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.2);
  padding: 12px 16px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.action-card:hover .action-button {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(4px);
}

.action-button span {
  font-weight: 500;
}

.action-button .arrow {
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}

.action-card:hover .arrow {
  transform: translateX(4px);
}

/* 装饰性背景图案 */
.card-pattern {
  position: absolute;
  top: 0;
  right: 0;
  width: 100px;
  height: 100px;
  opacity: 0.1;
  z-index: 1;
}

.pattern-dot {
  position: absolute;
  width: 4px;
  height: 4px;
  background: white;
  border-radius: 50%;
}

.pattern-dot:nth-child(1) { top: 10px; right: 10px; }
.pattern-dot:nth-child(2) { top: 10px; right: 25px; }
.pattern-dot:nth-child(3) { top: 10px; right: 40px; }
.pattern-dot:nth-child(4) { top: 25px; right: 10px; }
.pattern-dot:nth-child(5) { top: 25px; right: 25px; }
.pattern-dot:nth-child(6) { top: 25px; right: 40px; }
.pattern-dot:nth-child(7) { top: 40px; right: 10px; }
.pattern-dot:nth-child(8) { top: 40px; right: 25px; }
.pattern-dot:nth-child(9) { top: 40px; right: 40px; }
.pattern-dot:nth-child(10) { top: 55px; right: 10px; }
.pattern-dot:nth-child(11) { top: 55px; right: 25px; }
.pattern-dot:nth-child(12) { top: 55px; right: 40px; }

/* 响应式设计 */
@media (max-width: 768px) {
  .actions-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .action-card {
    height: 180px;
  }
  
  .card-background {
    padding: 20px;
  }
  
  .action-icon {
    font-size: 2.5rem;
  }
  
  .action-title {
    font-size: 1.2rem;
  }
}

@media (max-width: 480px) {
  .section-header h2 {
    font-size: 1.6rem;
  }
  
  .action-card {
    height: 160px;
  }
  
  .card-background {
    padding: 16px;
  }
  
  .action-icon {
    font-size: 2rem;
    margin-bottom: 8px;
  }
  
  .action-title {
    font-size: 1.1rem;
  }
  
  .action-description {
    font-size: 0.85rem;
  }
}
</style>
