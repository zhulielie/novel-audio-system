<template>
  <div class="crawler-manager">
    <el-card class="manager-card">
      <template #header>
        <div class="card-header">
          <span>🕷️ 爬虫管理中心</span>
          <el-button type="primary" @click="refreshStatus" :loading="loadingStatus">
            刷新状态
          </el-button>
        </div>
      </template>

      <!-- 爬虫状态概览 -->
      <div v-if="crawlerStatus" class="status-overview">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总小说来源" :value="crawlerStatus.total_relations" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="活跃来源" :value="crawlerStatus.active_relations" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最近同步" :value="crawlerStatus.recent_synced" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="支持站点" :value="crawlerStatus.supported_sites?.length || 0" />
          </el-col>
        </el-row>
      </div>

      <!-- 支持的网站列表 -->
      <div class="supported-sites">
        <el-divider content-position="left">支持的小说网站</el-divider>
        <el-row :gutter="10">
          <el-col
            v-for="site in supportedSites"
            :key="site"
            :span="12"
          >
            <el-tag type="info" class="site-tag">{{ site }}</el-tag>
          </el-col>
        </el-row>
      </div>

      <!-- 快速操作区 -->
      <div class="quick-actions">
        <el-divider content-position="left">快速操作</el-divider>

        <!-- URL分析工具 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <span>🔍 URL分析工具</span>
          </template>
          <el-form :model="analysisForm" label-width="80px">
            <el-form-item label="小说URL">
              <el-input
                v-model="analysisForm.url"
                placeholder="请输入小说目录页或章节页URL"
                type="url"
              >
                <template #append>
                  <el-button @click="analyzeUrl" :loading="analyzing">
                    分析
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-form>

          <!-- 分析结果 -->
          <div v-if="analysisResult" class="analysis-result">
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="状态">
                <el-tag :type="analysisResult.success ? 'success' : 'danger'">
                  {{ analysisResult.success ? '成功' : '失败' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item v-if="analysisResult.title" label="小说标题">
                <strong>{{ analysisResult.title }}</strong>
              </el-descriptions-item>
              <el-descriptions-item v-if="analysisResult.author" label="作者">
                {{ analysisResult.author }}
              </el-descriptions-item>
              <el-descriptions-item v-if="analysisResult.chapter_count" label="章节数">
                {{ analysisResult.chapter_count }} 章
              </el-descriptions-item>
              <el-descriptions-item v-if="analysisResult.message" label="消息">
                {{ analysisResult.message }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- 快速导入按钮 -->
            <div v-if="analysisResult.success" class="quick-import-actions">
              <el-button type="primary" @click="quickImport" :loading="importing">
                🚀 快速导入
              </el-button>
              <el-button @click="gotoBatchImport">
                📋 高级导入
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 批量导入入口 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <span>📚 批量导入小说</span>
          </template>
          <p>使用完整的批量导入功能，支持自定义参数和进度监控</p>
          <el-button type="primary" @click="gotoBatchImport">
            前往批量导入
          </el-button>
        </el-card>

        <!-- 爬虫日志 -->
        <el-card class="action-card" shadow="hover">
          <template #header>
            <span>📝 爬虫日志</span>
          </template>
          <div class="log-preview">
            <div
              v-for="log in recentLogs"
              :key="log.id"
              class="log-item"
              :class="log.type"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <p v-if="recentLogs.length === 0" class="no-logs">暂无日志</p>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import CrawlerService, { type CrawlerStatus, type UrlAnalysisResult } from '@/services/crawlerService'

const router = useRouter()

// 状态管理
const loadingStatus = ref(false)
const analyzing = ref(false)
const importing = ref(false)

// 数据
const crawlerStatus = ref<CrawlerStatus | null>(null)
const supportedSites = ref<string[]>([])
const recentLogs = ref<any[]>([])

// 表单
const analysisForm = ref({
  url: 'https://www.hetushu.com/book/38/26125.html'
})

const analysisResult = ref<UrlAnalysisResult | null>(null)

// 刷新爬虫状态
const refreshStatus = async () => {
  loadingStatus.value = true
  try {
    const status = await CrawlerService.getStatus()
    crawlerStatus.value = status
    supportedSites.value = CrawlerService.getSupportedSites()

    addLog('✅ 爬虫状态刷新成功', 'success')
  } catch (error) {
    console.error('刷新状态失败:', error)
    addLog('❌ 刷新状态失败', 'error')
    ElMessage.error('刷新状态失败')
  } finally {
    loadingStatus.value = false
  }
}

// 添加日志
const addLog = (message: string, type: string = 'info') => {
  recentLogs.value.unshift({
    id: Date.now(),
    time: new Date().toLocaleTimeString(),
    message,
    type
  })

  // 只保留最近10条日志
  if (recentLogs.value.length > 10) {
    recentLogs.value = recentLogs.value.slice(0, 10)
  }
}

// 分析URL
const analyzeUrl = async () => {
  if (!analysisForm.value.url) {
    ElMessage.warning('请输入小说URL')
    return
  }

  analyzing.value = true
  addLog('🔍 开始分析URL...', 'info')

  try {
    const result = await CrawlerService.analyzeUrl(analysisForm.value.url)
    analysisResult.value = result

    if (result.success) {
      addLog('✅ URL分析成功', 'success')
      ElMessage.success('URL分析成功！')
    } else {
      addLog(`❌ URL分析失败: ${result.error}`, 'error')
      ElMessage.error(result.error || 'URL分析失败')
    }
  } catch (error: any) {
    addLog(`❌ URL分析出错: ${error.message}`, 'error')
    ElMessage.error('URL分析出错')
  } finally {
    analyzing.value = false
  }
}

// 快速导入
const quickImport = async () => {
  if (!analysisResult.value?.success) {
    ElMessage.warning('请先成功分析URL')
    return
  }

  importing.value = true
  addLog('🚀 开始快速导入...', 'info')

  try {
    const result = await CrawlerService.quickImport(analysisForm.value.url)

    if (result.success) {
      addLog('✅ 快速导入完成', 'success')
      ElMessage.success(`成功导入 ${result.chapters_imported} 章！`)

      // 清空分析结果
      analysisResult.value = null
      analysisForm.value.url = ''
    } else {
      addLog(`❌ 快速导入失败: ${result.error}`, 'error')
      ElMessage.error(result.error || '快速导入失败')
    }
  } catch (error: any) {
    addLog(`❌ 快速导入出错: ${error.message}`, 'error')
    ElMessage.error('快速导入出错')
  } finally {
    importing.value = false
  }
}

// 跳转到批量导入页面
const gotoBatchImport = () => {
  // 如果有分析结果，传递给批量导入页面
  if (analysisResult.value?.success) {
    router.push({
      name: 'CrawlerBatch',
      query: {
        url: analysisForm.value.url,
        title: analysisResult.value.title,
        author: analysisResult.value.author
      }
    })
  } else {
    router.push({ name: 'CrawlerBatch' })
  }
}

// 组件挂载时初始化
onMounted(async () => {
  await refreshStatus()
  addLog('🏠 爬虫管理中心已启动', 'info')
})
</script>

<style scoped>
.crawler-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.manager-card {
  border-radius: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.status-overview {
  margin-bottom: 30px;
}

.supported-sites {
  margin-bottom: 30px;
}

.site-tag {
  margin-bottom: 5px;
  display: block;
  text-align: center;
}

.quick-actions {
  margin-top: 30px;
}

.action-card {
  margin-bottom: 20px;
}

.action-card p {
  color: #666;
  margin-bottom: 15px;
}

.analysis-result {
  margin-top: 20px;
}

.quick-import-actions {
  margin-top: 15px;
  text-align: center;
}

.quick-import-actions .el-button {
  margin: 0 10px;
}

.log-preview {
  max-height: 200px;
  overflow-y: auto;
  background-color: #fafafa;
  border-radius: 4px;
  padding: 10px;
}

.log-item {
  margin-bottom: 5px;
  font-family: monospace;
  font-size: 12px;
}

.log-item.success {
  color: #67c23a;
}

.log-item.error {
  color: #f56c6c;
}

.log-item.warning {
  color: #e6a23c;
}

.log-time {
  color: #909399;
  margin-right: 10px;
}

.no-logs {
  color: #909399;
  text-align: center;
  margin: 20px 0;
}
</style>
