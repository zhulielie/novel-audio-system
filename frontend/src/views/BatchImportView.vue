<template>
  <div class="batch-import-container">
    <el-card class="import-card">
      <template #header>
        <div class="card-header">
          <span>🧠 智能批量导入小说章节</span>
        </div>
      </template>
      
      <div class="import-form">
        <el-form :model="importForm" label-width="120px" :rules="formRules">
          <!-- 1. 小说来源（解析方式） -->
          <el-form-item label="小说来源" prop="sourceId">
            <el-select v-model="importForm.sourceId" placeholder="选择解析方式">
              <el-option 
                v-for="source in novelSources"
                :key="source.id"
                :label="source.name"
                :value="source.id"
              >
                <span>{{ source.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 13px">{{ source.source_type }}</span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <!-- 3. 小说链接（必填） -->
          <el-form-item label="小说链接" prop="novelUrl">
            <el-input 
              v-model="importForm.novelUrl" 
              placeholder="请输入小说目录页或任意章节页的完整URL"
              type="url"
            >
              <template #append>
                <el-button @click="analyzeUrl" :loading="analyzing" size="small">
                  🔍 分析
                </el-button>
              </template>
            </el-input>
            <div class="url-hint">
              <el-text size="small" type="info">
                💡 支持：目录页链接 | 任意章节页链接（系统会自动识别并找到目录）
              </el-text>
            </div>
          </el-form-item>
          
          <!-- 2. 自动检测的小说信息（只读显示） -->
          <el-form-item label="检测信息" v-if="detectedInfo.title">
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="小说标题">
                <el-tag type="success">{{ detectedInfo.title }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="作者" v-if="detectedInfo.author">
                <el-tag type="info">{{ detectedInfo.author }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="检测到章节">
                <el-tag type="warning">{{ detectedInfo.chapterCount || 0 }} 章</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-form-item>
          
          <!-- 4. 章节限制 -->
          <el-form-item label="章节限制">
            <el-radio-group v-model="importForm.chapterLimitType">
              <el-radio label="all">全部章节</el-radio>
              <el-radio label="before">前 N 章</el-radio>
              <el-radio label="after">从第 N 章开始</el-radio>
              <el-radio label="range">指定范围</el-radio>
            </el-radio-group>
            
            <!-- 前N章 -->
            <div v-if="importForm.chapterLimitType === 'before'" class="limit-input">
              <el-input-number v-model="importForm.beforeChapter" :min="1" :max="10000" placeholder="章节数" />
              <span class="limit-text">章</span>
            </div>
            
            <!-- 从第N章开始 -->
            <div v-if="importForm.chapterLimitType === 'after'" class="limit-input">
              <span class="limit-text">从第</span>
              <el-input-number v-model="importForm.afterChapter" :min="1" :max="10000" placeholder="起始章节" />
              <span class="limit-text">章开始</span>
            </div>
            
            <!-- 指定范围 -->
            <div v-if="importForm.chapterLimitType === 'range'" class="limit-input">
              <span class="limit-text">第</span>
              <el-input-number v-model="importForm.rangeStart" :min="1" :max="10000" placeholder="开始" />
              <span class="limit-text">章 至 第</span>
              <el-input-number v-model="importForm.rangeEnd" :min="1" :max="10000" placeholder="结束" />
              <span class="limit-text">章</span>
            </div>
          </el-form-item>
          
          <el-form-item label="速度控制">
            <el-radio-group v-model="importForm.speed">
              <el-radio label="slow">🐌 慢速 (3-6秒延时)</el-radio>
              <el-radio label="normal">⚡ 正常 (2-5秒延时)</el-radio>
              <el-radio label="fast">🚀 快速 (1-3秒延时)</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        
        <div class="action-buttons">
          <el-button 
            type="primary" 
            size="large" 
            @click="startImport" 
            :loading="importing"
            :disabled="!canImport"
          >
            🚀 开始智能导入
          </el-button>
          <el-button size="large" @click="resetForm">
            🔄 重置表单
          </el-button>
        </div>
      </div>
      
      <!-- 进度显示 -->
      <div v-if="importing || importLog.length > 0" class="import-progress">
        <el-divider content-position="left">导入进度</el-divider>
        
        <el-progress 
          v-if="importing"
          :percentage="importProgress" 
          :status="importStatus"
          :format="formatProgress"
        />
        
        <div class="import-log">
          <div 
            v-for="(log, index) in importLog" 
            :key="index" 
            :class="['log-item', log.type]"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
      
      <!-- 结果显示 -->
      <div v-if="importResult" class="import-result">
        <el-divider content-position="left">导入结果</el-divider>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="导入状态">
            <el-tag :type="importResult.success ? 'success' : 'danger'">
              {{ importResult.success ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总发现章节">{{ importResult.totalFound || 0 }}</el-descriptions-item>
          <el-descriptions-item label="成功导入">{{ importResult.imported || 0 }}</el-descriptions-item>
          <el-descriptions-item label="跳过章节">{{ importResult.skipped || 0 }}</el-descriptions-item>
          <el-descriptions-item label="失败章节">{{ importResult.failed || 0 }}</el-descriptions-item>
          <el-descriptions-item label="平均延时">{{ importResult.avgDelay || 0 }}秒</el-descriptions-item>
        </el-descriptions>
        
        <div class="result-actions">
          <el-button type="success" @click="viewNovel" v-if="importResult.novelId">
            📖 查看导入的小说
          </el-button>
          <el-button @click="resetImport">
            🔄 重新导入
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'

const router = useRouter()

// 表单数据
const importForm = ref({
  sourceId: 1, // 默认选择和图书网
  novelUrl: 'https://www.hetushu.com/book/38/26125.html', // 预设用户提供的链接
  chapterLimitType: 'before', // 默认选择前N章
  beforeChapter: 5, // 默认5章用于测试
  afterChapter: 1,
  rangeStart: 1,
  rangeEnd: 100,
  speed: 'normal'
})

// 表单验证规则
const formRules = {
  sourceId: [
    { required: true, message: '请选择小说来源', trigger: 'change' }
  ],
  novelUrl: [
    { required: true, message: '请输入小说链接', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
  ]
}

// 小说来源列表
const novelSources = ref<any[]>([])

// 检测到的小说信息
const detectedInfo = ref({
  title: '',
  author: '',
  chapterCount: 0
})

// 状态管理
const importing = ref(false)
const analyzing = ref(false)
const importProgress = ref(0)
const importStatus = ref('')
const importLog = ref<any[]>([])
const importResult = ref<any>(null)

// 计算属性 - 是否可以导入
const canImport = computed(() => {
  return importForm.value.sourceId && 
         importForm.value.novelUrl && 
         detectedInfo.value.title
})

// 加载小说来源
const loadNovelSources = async () => {
  try {
    const response: any = await apiService.novelSources.list()
    novelSources.value = response.results || response.data || response
  } catch (error) {
    console.error('加载小说来源失败:', error)
    ElMessage.error('加载小说来源失败')
  }
}

// 添加日志
const addLog = (message: string, type: string = 'info') => {
  importLog.value.push({
    time: new Date().toLocaleTimeString(),
    message,
    type
  })
}

// 格式化进度
const formatProgress = (percentage: number) => {
  return `${percentage}% ${importStatus.value}`
}

// 分析URL
const analyzeUrl = async () => {
  if (!importForm.value.novelUrl) {
    ElMessage.warning('请先输入小说链接')
    return
  }
  
  analyzing.value = true
  addLog('🔍 正在分析小说链接...', 'info')
  
  try {
    // 调用后端分析接口
    const response: any = await apiService.novels.test_source({ url: importForm.value.novelUrl })
    
    if (response.success) {
      detectedInfo.value = {
        title: response.title || '未知小说',
        author: response.author || '',
        chapterCount: response.chapter_count || 0
      }
      
      addLog('✅ URL分析成功！', 'success')
      addLog(`📚 检测到小说: ${detectedInfo.value.title}`, 'info')
      if (detectedInfo.value.author) {
        addLog(`👤 作者: ${detectedInfo.value.author}`, 'info')
      }
      addLog(`📝 检测到章节: ${detectedInfo.value.chapterCount} 章`, 'info')
      
      ElMessage.success('小说信息检测成功！')
    } else {
      addLog(`❌ URL分析失败: ${response.error}`, 'error')
      ElMessage.error('小说信息检测失败')
    }
  } catch (error: any) {
    addLog(`❌ URL分析出错: ${error.message}`, 'error')
    ElMessage.error('分析出错')
  } finally {
    analyzing.value = false
  }
}

// 计算章节限制参数
const getChapterLimits = () => {
  const limits: Record<string, number | null> = {
    max_chapters: null,
    start_chapter: null,
    end_chapter: null
  }
  
  switch (importForm.value.chapterLimitType) {
    case 'all':
      limits.max_chapters = null // 不限制
      break
    case 'before':
      limits.max_chapters = importForm.value.beforeChapter
      break
    case 'after':
      limits.start_chapter = importForm.value.afterChapter
      break
    case 'range':
      limits.start_chapter = importForm.value.rangeStart
      limits.end_chapter = importForm.value.rangeEnd
      break
  }
  
  return limits
}

// 开始导入
const startImport = async () => {
  if (!canImport.value) {
    ElMessage.warning('请先分析小说链接获取小说信息')
    return
  }
  
  importing.value = true
  importProgress.value = 0
  importStatus.value = '准备中...'
  importLog.value = []
  importResult.value = null
  
  const limits = getChapterLimits()
  
  addLog('🚀 开始智能批量导入...', 'info')
  addLog(`📚 小说: ${detectedInfo.value.title}`, 'info')
  addLog(`🔗 链接: ${importForm.value.novelUrl}`, 'info')
  addLog(`⚡ 速度: ${importForm.value.speed}`, 'info')
  
  // 显示章节限制信息
  switch (importForm.value.chapterLimitType) {
    case 'all':
      addLog('📋 章节限制: 全部章节', 'info')
      break
    case 'before':
      addLog(`📋 章节限制: 前 ${importForm.value.beforeChapter} 章`, 'info')
      break
    case 'after':
      addLog(`📋 章节限制: 从第 ${importForm.value.afterChapter} 章开始`, 'info')
      break
    case 'range':
      addLog(`📋 章节限制: 第 ${importForm.value.rangeStart}-${importForm.value.rangeEnd} 章`, 'info')
      break
  }
  
  try {
    // 调用后端测试批量导入API
    const response: any = await apiService.post('/api/test-batch-import/', {
      source_url: importForm.value.novelUrl,
      novel_title: detectedInfo.value.title,
      novel_author: detectedInfo.value.author,
      source_id: importForm.value.sourceId,
      speed: importForm.value.speed,
      ...limits
    })
    
    if (response.data.success) {
      importProgress.value = 100
      importStatus.value = '完成'
      addLog('🎉 智能批量导入完成！', 'success')
      
      importResult.value = {
        success: true,
        novelId: response.data.novel_id,
        totalFound: response.data.total_found,
        imported: response.data.chapters_imported,
        skipped: response.data.skipped_count,
        failed: response.data.failed_count,
        avgDelay: 3.5
      }
      
      ElMessage.success(`成功导入 ${response.data.chapters_imported} 章！`)
    } else {
      importStatus.value = '失败'
      addLog(`❌ 导入失败: ${response.data.error}`, 'error')
      importResult.value = { success: false, error: response.data.error }
      ElMessage.error('导入失败')
    }
  } catch (error: any) {
    importStatus.value = '出错'
    addLog(`❌ 导入出错: ${error.message}`, 'error')
    importResult.value = { success: false, error: error.message }
    ElMessage.error('导入出错')
  } finally {
    importing.value = false
  }
}

// 查看小说
const viewNovel = () => {
  if (importResult.value?.novelId) {
    router.push(`/novels/${importResult.value.novelId}`)
  }
}

// 重置表单
const resetForm = () => {
  importForm.value = {
    sourceId: 1,
    novelUrl: '',
    chapterLimitType: 'all',
    beforeChapter: 100,
    afterChapter: 1,
    rangeStart: 1,
    rangeEnd: 100,
    speed: 'normal'
  }
  detectedInfo.value = {
    title: '',
    author: '',
    chapterCount: 0
  }
  importing.value = false
  importProgress.value = 0
  importStatus.value = ''
  importLog.value = []
  importResult.value = null
}

// 重置导入
const resetImport = () => {
  importing.value = false
  importProgress.value = 0
  importStatus.value = ''
  importLog.value = []
  importResult.value = null
}

onMounted(async () => {
  await loadNovelSources()
  addLog('💡 提示: 请输入小说目录页或任意章节页的完整URL', 'info')
  addLog('⚠️ 为避免被封，系统会在爬取时自动添加随机延时', 'warning')
})
</script>

<style scoped>
.batch-import-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.import-card {
  border-radius: 10px;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.import-form {
  margin-bottom: 30px;
}

.url-hint {
  margin-top: 5px;
}

.limit-input {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.limit-text {
  font-size: 14px;
  color: #606266;
}

.action-buttons {
  text-align: center;
  margin-top: 30px;
}

.action-buttons .el-button {
  margin: 0 10px;
}

.import-progress {
  margin-top: 30px;
}

.import-log {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px;
  margin-top: 15px;
  background-color: #fafafa;
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

.import-result {
  margin-top: 30px;
}

.result-actions {
  text-align: center;
  margin-top: 20px;
}

.result-actions .el-button {
  margin: 0 10px;
}
</style>