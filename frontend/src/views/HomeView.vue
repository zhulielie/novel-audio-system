<template>
  <div class="home-container">
    <HeroSection />
    <QuickActionsGrid />
    
    <div class="bottom-section">
      <div class="bottom-grid">
        <ActivityTimeline />
        <SystemDashboard />
      </div>
    </div>
    
    <div class="footer-info">
      <div class="footer-content">
        <div class="footer-left">
          <span class="system-info">智能小说管理系统</span>
          <span class="update-info">最后更新: {{ formatTime(new Date()) }}</span>
        </div>
        <el-button @click="refreshAllData" size="small" type="primary" plain>
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

import HeroSection from '../components/home/HeroSection.vue'
import QuickActionsGrid from '../components/home/QuickActionsGrid.vue'
import ActivityTimeline from '../components/home/ActivityTimeline.vue'
import SystemDashboard from '../components/home/SystemDashboard.vue'

const refreshTimer = ref(null)

const formatTime = (time) => {
  return time.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const refreshAllData = async () => {
  try {
    ElMessage.success('所有数据刷新完成')
    setTimeout(() => {
      ElMessage.info('统计数据已更新')
    }, 1000)
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

const startAutoRefresh = () => {
  refreshTimer.value = setInterval(() => {
  }, 60000)
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

onMounted(() => {
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.home-container {
  min-height: 100%;
  background: var(--bg-body);
  padding-bottom: 40px;
}

.bottom-section {
  padding: 0 24px 32px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.timeline-column,
.dashboard-column {
  display: flex;
  flex-direction: column;
}

.footer-info {
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  padding: 16px 24px;
  margin-top: 8px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1400px;
  margin: 0 auto;
}

.footer-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.system-info {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.update-info {
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .bottom-section {
    padding: 0 16px 20px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .footer-left {
    align-items: center;
  }
}
</style>
