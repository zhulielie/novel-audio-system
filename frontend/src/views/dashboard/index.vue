<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>欢迎使用小说管理系统</h1>
      <p>基于 Django-Vue3-Admin 架构的现代化管理平台</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon novels">
              <el-icon><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.novels }}</div>
              <div class="stat-label">小说总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon chapters">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.chapters }}</div>
              <div class="stat-label">章节总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon tasks">
              <el-icon><Operation /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.tasks }}</div>
              <div class="stat-label">爬虫任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon users">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.users }}</div>
              <div class="stat-label">系统用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <div class="action-buttons">
            <el-button type="primary" icon="Plus" @click="goToNovels">
              添加小说
            </el-button>
            <el-button type="success" icon="Download" @click="goToBatch">
              批量下载
            </el-button>
            <el-button type="info" icon="VideoPlay" @click="goToAudio">
              音频项目
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
            </div>
          </template>
          <div class="activity-list">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <el-icon class="activity-icon"><Bell /></el-icon>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-time">{{ formatRelativeTime(activity.time) }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          <div class="system-info">
            <div class="info-item">
              <span class="info-label">Django版本:</span>
              <span class="info-value">5.2.5</span>
            </div>
            <div class="info-item">
              <span class="info-label">Vue版本:</span>
              <span class="info-value">3.5.18</span>
            </div>
            <div class="info-item">
              <span class="info-label">Element Plus:</span>
              <span class="info-value">2.10.7</span>
            </div>
            <div class="info-item">
              <span class="info-label">运行时间:</span>
              <span class="info-value">{{ uptime }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Reading, Document, Operation, User, Plus, Download, VideoPlay, Bell } from '@element-plus/icons-vue'
import { formatRelativeTime } from '@/utils/date'
import { apiService } from '@/services/api'

const router = useRouter()

const goToNovels = () => router.push('/novels/list')
const goToBatch = () => router.push('/crawler/batch')
const goToAudio = () => router.push('/audio/projects')

// 响应式数据
const stats = ref({
  novels: 0,
  chapters: 0,
  tasks: 0,
  users: 0
})

const recentActivities = ref([
  {
    id: 1,
    title: '新增小说《测试小说》',
    time: new Date(Date.now() - 1000 * 60 * 30) // 30分钟前
  },
  {
    id: 2,
    title: '完成批量下载任务',
    time: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2小时前
  },
  {
    id: 3,
    title: '生成音频项目',
    time: new Date(Date.now() - 1000 * 60 * 60 * 24) // 1天前
  }
])

const uptime = ref('2天 5小时 30分钟')

// 方法
const loadStats = async () => {
  try {
    // 加载统计数据
    const [novelsRes, chaptersRes] = await Promise.all([
      apiService.novels.list({ page_size: 1 }),
      apiService.chapters.list({ page_size: 1 })
    ])
    
    stats.value.novels = (novelsRes as any).count || 0
    stats.value.chapters = (chaptersRes as any).count || 0
    stats.value.tasks = 15 // 模拟数据
    stats.value.users = 3 // 模拟数据
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 生命周期
onMounted(() => {
  loadStats()
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 30px;
  
  h1 {
    font-size: 28px;
    color: #303133;
    margin-bottom: 10px;
  }
  
  p {
    font-size: 16px;
    color: #909399;
  }
}

.stats-cards {
  margin-bottom: 30px;
  
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      
      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        font-size: 24px;
        color: white;
        
        &.novels {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.chapters {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.tasks {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.users {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-info {
        .stat-number {
          font-size: 24px;
          font-weight: bold;
          color: #303133;
          line-height: 1;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
}

.quick-actions {
  .card-header {
    font-weight: bold;
    color: #303133;
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .el-button {
      justify-content: flex-start;
    }
  }
  
  .activity-list {
    .activity-item {
      display: flex;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .activity-icon {
        color: #409eff;
        margin-right: 12px;
      }
      
      .activity-content {
        flex: 1;
        
        .activity-title {
          font-size: 14px;
          color: #303133;
          margin-bottom: 4px;
        }
        
        .activity-time {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }
  
  .system-info {
    .info-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .info-label {
        font-size: 14px;
        color: #606266;
      }
      
      .info-value {
        font-size: 14px;
        color: #303133;
        font-weight: 500;
      }
    }
  }
}
</style>
