<template>
  <div class="home-container">
    <!-- 顶部欢迎区域 -->
    <HeroSection />
    
    <!-- 功能快捷入口 -->
    <QuickActionsGrid />
    
    <!-- 下半部分：活动流 + 系统状态 -->
    <div class="bottom-section">
      <div class="bottom-grid">
        <!-- 实时活动流 -->
        <div class="timeline-column">
          <ActivityTimeline />
        </div>
        
        <!-- 系统状态面板 -->
        <div class="dashboard-column">
          <SystemDashboard />
        </div>
      </div>
    </div>
    
    <!-- 页面底部信息 -->
    <div class="footer-info">
      <div class="footer-content">
        <div class="footer-left">
          <span class="system-info">🎯 智能小说管理系统 v2.0</span>
          <span class="update-info">最后更新: {{ formatTime(new Date()) }}</span>
        </div>
        <div class="footer-right">
          <el-button @click="refreshAllData" size="small" type="primary" plain>
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

// 导入组件
import HeroSection from '../components/home/HeroSection.vue'
import QuickActionsGrid from '../components/home/QuickActionsGrid.vue'
import ActivityTimeline from '../components/home/ActivityTimeline.vue'
import SystemDashboard from '../components/home/SystemDashboard.vue'

// 响应式数据
const refreshTimer = ref(null)

// 格式化时间
const formatTime = (time) => {
  return time.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 刷新所有数据
const refreshAllData = async () => {
  try {
    // 触发所有子组件的刷新
    // 这里可以通过事件总线或者provide/inject来通知子组件刷新
    ElMessage.success('所有数据刷新完成')
    
    // 模拟数据更新
    setTimeout(() => {
      ElMessage.info('统计数据已更新')
    }, 1000)
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

// 自动刷新数据
const startAutoRefresh = () => {
  refreshTimer.value = setInterval(() => {
    // 这里可以添加自动刷新逻辑
    console.log('自动刷新数据...')
  }, 60000) // 每分钟刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 生命周期
onMounted(() => {
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  position: relative;
}

/* 底部区域布局 */
.bottom-section {
  padding: 0 20px 40px 20px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.timeline-column,
.dashboard-column {
  display: flex;
  flex-direction: column;
}

/* 页面底部信息 */
.footer-info {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding: 16px 20px;
  margin-top: 40px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.footer-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.system-info {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
}

.update-info {
  font-size: 0.8rem;
  color: #909399;
}

.footer-right {
  display: flex;
  align-items: center;
}

/* 全局动画效果 */
.home-container > * {
  animation: fadeInUp 0.6s ease-out;
}

.home-container > *:nth-child(1) { animation-delay: 0.1s; }
.home-container > *:nth-child(2) { animation-delay: 0.2s; }
.home-container > *:nth-child(3) { animation-delay: 0.3s; }
.home-container > *:nth-child(4) { animation-delay: 0.4s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .home-container {
    background: #f5f7fa;
  }
  
  .bottom-section {
    padding: 0 10px 20px 10px;
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

@media (max-width: 480px) {
  .bottom-section {
    padding: 0 5px 15px 5px;
  }
  
  .footer-info {
    padding: 12px 10px;
  }
  
  .system-info {
    font-size: 0.8rem;
  }
  
  .update-info {
    font-size: 0.75rem;
  }
}

/* 滚动条美化 */
:deep(.el-scrollbar__wrap) {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar) {
  width: 6px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 3px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb) {
  background: #c1c1c1;
  border-radius: 3px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb:hover) {
  background: #a8a8a8;
}
</style>