<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { audioAPI } from '@/services/api'
import type { AudioProject, AudioItem } from '@/types'

const route = useRoute()

const project = ref<AudioProject | null>(null)
const audioItems = ref<AudioItem[]>([])
const loading = ref(true)

const projectId = Number(route.params.id)

const fetchProjectDetail = async () => {
  try {
    const [projectResponse, itemsResponse] = await Promise.all([
      audioAPI.getProject(projectId),
      audioAPI.getItems(projectId)
    ])
    project.value = projectResponse.data || projectResponse
    audioItems.value = itemsResponse.data || itemsResponse
  } catch (error) {
    console.error('获取音频项目详情失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProjectDetail()
})
</script>

<template>
  <div class="audio-project-detail">
    <div v-if="loading" class="loading">
      <el-icon size="48" class="loading-icon"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <template v-else-if="project">
      <div class="project-header">
        <h1>{{ project.name }}</h1>
        <p class="description">{{ project.description }}</p>
        <div class="project-meta">
          <span>创建时间: {{ new Date(project.created_at).toLocaleString() }}</span>
          <span>更新时间: {{ new Date(project.updated_at).toLocaleString() }}</span>
        </div>
      </div>

      <div class="project-actions">
        <el-button type="primary">开始生成</el-button>
        <el-button type="success">导出项目</el-button>
        <el-button>编辑项目</el-button>
      </div>

      <div class="audio-items-section">
        <h2>音频项目列表 ({{ audioItems.length }})</h2>
        <div class="audio-items-list">
          <div
            v-for="item in audioItems"
            :key="item.id"
            class="audio-item"
          >
            <div class="item-info">
              <h3>{{ item.title }}</h3>
              <p class="item-preview">{{ item.text_content.substring(0, 100) }}...</p>
            </div>
            <div class="item-meta">
              <span v-if="item.duration">时长: {{ item.duration }}秒</span>
              <span v-if="item.audio_file">已生成音频</span>
            </div>
            <div class="item-actions">
              <el-button size="small" v-if="!item.audio_file">生成音频</el-button>
              <el-button size="small" type="success" v-else>播放音频</el-button>
              <el-button size="small">编辑</el-button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="error">
      <p>音频项目不存在或加载失败</p>
    </div>
  </div>
</template>

<style scoped>
.audio-project-detail {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  gap: 16px;
}

.project-header {
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.project-header h1 {
  margin: 0 0 12px 0;
  color: #303133;
}

.description {
  color: #606266;
  margin: 0 0 16px 0;
  line-height: 1.6;
}

.project-meta {
  display: flex;
  gap: 24px;
  color: #909399;
  font-size: 14px;
}

.project-actions {
  margin-bottom: 32px;
  display: flex;
  gap: 12px;
}

.audio-items-section h2 {
  margin-bottom: 20px;
  color: #303133;
}

.audio-items-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audio-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.item-info {
  flex: 1;
}

.item-info h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.item-preview {
  margin: 0;
  color: #909399;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0 20px;
  color: #909399;
  font-size: 14px;
}

.item-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}
</style>
