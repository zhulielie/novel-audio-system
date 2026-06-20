<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

import { apiService } from '@/services/api'
import type { Novel, Chapter } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const novel = ref<Novel | null>(null)
const chapters = ref<Chapter[]>([])
const loading = ref(true)
const readingChapter = ref<Chapter | null>(null)
const readingDialogVisible = ref(false)



// 分页相关
const currentPage = ref(1)
const pageSize = ref(50)
const totalChapters = ref(0)

// 分页设置
const directoryPageSize = ref(50)

// 连续阅读相关功能已移除

// 批量导入相关
const batchImportVisible = ref(false)
const batchImportLoading = ref(false)
const batchImportForm = ref<{
  source_id: number | null
  max_chapters: number
}>({
  source_id: 1, // 默认选择示例站点网 (ID: 1)
  max_chapters: 100
})
const availableSources = ref<any[]>([])

const novelId = Number(route.params.id)

// 排序相关
const sortOrder = ref('asc') // 默认正序

// 处理排序变化
const handleSortChange = async () => {
  currentPage.value = 1 // 重置到第一页
  await fetchNovelDetail()
}

const fetchNovelDetail = async () => {
  try {
    const [novelResponse, chaptersResponse] = await Promise.all([
      apiService.novels.get(novelId),
      apiService.chapters.list({
        novel: novelId,
        page: currentPage.value,
        page_size: directoryPageSize.value,
        ordering: sortOrder.value === 'desc' ? '-chapter_sort_number' : 'chapter_sort_number'
      })
    ])

    novel.value = novelResponse.data || novelResponse
    const chaptersData = chaptersResponse.data || chaptersResponse

    let newChapters = Array.isArray(chaptersData) ? chaptersData : chaptersData.results || []
    totalChapters.value = chaptersData.count || chaptersData.total || newChapters.length

    // 从章节内容的第一行提取标题
    newChapters = newChapters.map((chapter: any) => {
      const processedChapter = { ...chapter }

      // 如果内容不为空，尝试从内容第一行提取标题
      if (processedChapter.content && processedChapter.content.trim()) {
        const contentLines = processedChapter.content.split('\n').filter((line: string) => line.trim())
        if (contentLines.length > 0) {
          const firstLine = contentLines[0].trim()
          // 检查第一行是否看起来像章节标题（更宽松的匹配）
          if (firstLine.match(/^第[一二三四五六七八九十百千]+章/) ||
              firstLine.match(/^第\d+章/) ||
              firstLine.match(/^第[一二三四五六七八九十百千\d]+章/)) {
            processedChapter.title = firstLine
          }
        }
      }

      return processedChapter
    })

    chapters.value = newChapters
  } catch (error) {
    console.error('获取小说详情失败:', error)
    chapters.value = []
    totalChapters.value = 0
  } finally {
    loading.value = false
  }
}

// 目录显示模式切换功能已移除，只保留分页模式

// 分页处理
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchNovelDetail()
}

// 处理每页数量变化
const handleSizeChange = (size: number) => {
  directoryPageSize.value = size
  currentPage.value = 1
  fetchNovelDetail()
}

// 连续阅读相关函数已移除

// 滚动监听器已移除（连续阅读功能已删除）



// 开始阅读 - 从第一章开始
const startReading = () => {
  if (!novel.value?.id) {
    ElMessage.warning('小说信息未加载，请稍后重试')
    return
  }
  router.push({
    name: 'NovelReader',
    params: { id: novel.value.id },
    query: { chapter: 1 }
  })
}

// 阅读章节 - 跳转到新的阅读器
const readChapter = (chapter: Chapter) => {
  if (!novel.value?.id) {
    ElMessage.warning('小说信息未加载，请稍后重试')
    return
  }
  // 使用章节的实际排序编号，而不是当前页面中的索引
  const chapterNumber = chapter.chapter_sort_number || 1
  router.push({
    name: 'NovelReader',
    params: { id: novel.value.id },
    query: { chapter: chapterNumber }
  })
}

// 获取章节内容（如果需要单独获取）
const fetchChapterContent = async (chapter: Chapter) => {
  try {
    // 如果章节内容为空，尝试单独获取
    if (!chapter.content) {
      const response = await apiService.chapters.get(chapter.id)
      const chapterData = response.data || response
      if (chapterData && chapterData.content) {
        // 更新章节内容
        const chapterIndex = chapters.value.findIndex(c => c.id === chapter.id)
        if (chapterIndex >= 0) {
          chapters.value[chapterIndex] = { ...chapter, content: chapterData.content }
        }
        return chapterData.content
      }
    }
    return chapter.content
  } catch (error) {
    console.error('获取章节内容失败:', error)
    return chapter.content || '内容加载失败'
  }
}

// 获取上一章
const getPreviousChapter = () => {
  if (!readingChapter.value) return null
  const currentIndex = chapters.value.findIndex(ch => ch.id === readingChapter.value?.id)
  return currentIndex > 0 ? chapters.value[currentIndex - 1] : null
}

// 获取下一章
const getNextChapter = () => {
  if (!readingChapter.value) return null
  const currentIndex = chapters.value.findIndex(ch => ch.id === readingChapter.value?.id)
  return currentIndex < chapters.value.length - 1 ? chapters.value[currentIndex + 1] : null
}

// 对话框打开时的处理
const onDialogOpen = async () => {
  if (readingChapter.value && !readingChapter.value.content) {
    try {
      const content = await fetchChapterContent(readingChapter.value)
      if (content && readingChapter.value) {
        readingChapter.value.content = content
      }
    } catch (error) {
      console.error('加载章节内容失败:', error)
    }
  }
}

// 格式化章节内容
const formatChapterContent = (content: string) => {
  if (!content) return '暂无内容'
  // 将换行符转换为HTML换行
  return content.replace(/\n/g, '<br>')
}

// 获取可用的小说来源
const fetchAvailableSources = async () => {
  try {
    const response = await apiService.get('/novel-sources/')
    // Django REST framework分页响应结构：{count, next, previous, results}
    // 由于响应拦截器返回response.data，所以这里response就是分页数据
    availableSources.value = (response as any).results || (response as any).data || response || []
  } catch (error: any) {
    console.error('获取小说来源失败:', error)
    ElMessage.error('获取小说来源失败: ' + (error.message || '未知错误'))
  }
}

// 打开批量导入对话框
const openBatchImportDialog = async () => {
  // 如果还没有获取来源，先获取
  if (availableSources.value.length === 0) {
    await fetchAvailableSources()
  }
  
  // 重置表单
  batchImportForm.value = {
    source_id: null,
    max_chapters: 100
  }
  
  // 强制设置对话框为可见
  batchImportVisible.value = true
  
  // 用nextTick确保 DOM 更新后再执行验证
  await nextTick()
  
  // 强制刷新显示（在下一个事件循环中）
  setTimeout(() => {
    const dialog = document.querySelector('.batch-import-dialog')
    if (dialog) {
      const wrapper = dialog.closest('.el-dialog__wrapper') || dialog.parentElement
      if (wrapper) {
        ;(wrapper as HTMLElement).style.display = 'flex'
        ;(wrapper as HTMLElement).style.visibility = 'visible'
        ;(wrapper as HTMLElement).style.opacity = '1'
        ;(wrapper as HTMLElement).style.zIndex = '3000'
      }
    }
  }, 100)
}

// 执行批量导入
const executeBatchImport = async () => {
  if (!batchImportForm.value.source_id) {
    ElMessage.warning('请选择小说来源')
    return
  }

  batchImportLoading.value = true
  try {
    const response = await apiService.post(`/novels/${novelId}/batch_import/`, batchImportForm.value)
    const result = response.data || response

    if (result.success) {
      ElMessage.success({
        message: `批量导入完成！导入 ${result.imported_count} 章，跳过 ${result.skipped_count} 章，失败 ${result.failed_count} 章`,
        duration: 5000
      })
      batchImportVisible.value = false
      // 刷新章节列表
      await fetchNovelDetail()
    } else {
      ElMessage.error(result.message || '批量导入失败')
    }
  } catch (error: any) {
    console.error('批量导入失败:', error)
    ElMessage.error('批量导入失败: ' + (error.response?.data?.message || error.message || '未知错误'))
  } finally {
    batchImportLoading.value = false
  }
}

onMounted(() => {
  fetchNovelDetail()
  fetchAvailableSources()
})
</script>

<template>
  <div class="novel-detail">
    <div v-if="loading" class="loading">
      <el-icon size="48" class="loading-icon"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <template v-else-if="novel">
      <div class="novel-header">
        <div class="header-content">
          <h1>{{ novel.title }}</h1>
          <p class="author">作者: {{ novel.author }}</p>
          <p class="description">{{ novel.description }}</p>
        </div>
        <div class="header-actions">
          <el-button 
            type="primary" 
            size="large" 
            @click="startReading"
            v-if="chapters.length > 0"
          >
            📖 开始阅读
          </el-button>
        </div>
      </div>

      <div class="chapters-section">
        <div class="chapters-header">
          <div class="header-left">
            <h2>章节目录</h2>
            <p class="chapters-count">共 {{ totalChapters }} 章</p>
          </div>
          <div class="header-actions">
            <!-- 按钮已删除，只保留必要的功能 -->
          </div>
        </div>

        <div class="chapters-list">
          <div v-if="chapters.length === 0 && !loading" class="no-chapters">
            <p>暂无章节数据</p>
            <el-button @click="fetchNovelDetail" :loading="loading">重新加载</el-button>
          </div>
          <div
            v-for="chapter in chapters"
            :key="chapter.id"
            class="chapter-item"
          >
            <div class="chapter-info">
              <h3>{{ chapter.title || '未命名章节' }}</h3>
              <p class="chapter-meta">
                {{ chapter.title || '未命名章节' }} | {{ chapter.word_count || 0 }}字 |
                <span class="chapter-number">第{{ chapter.chapter_sort_number }}章</span>
              </p>
            </div>
            <div class="chapter-actions">
              <el-button size="small" type="success" @click="readChapter(chapter)">阅读</el-button>
              <el-button size="small" type="primary">编辑</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 简单排序工具栏 -->
      <div class="sort-tools" v-if="novel">
        <div class="sort-controls">
          <el-select v-model="sortOrder" @change="handleSortChange" placeholder="选择排序方式" style="width: 150px;">
            <el-option label="正序" value="asc"></el-option>
            <el-option label="倒序" value="desc"></el-option>
          </el-select>
          <span class="sort-info">当前有 {{ totalChapters }} 个章节</span>
        </div>
        <div class="batch-import-tools">
          <el-button @click="openBatchImportDialog" type="primary" size="small">🚀 智能批量导入</el-button>
        </div>
        <div class="directory-mode-info">
          <p>📄 分页显示模式：每页显示 {{ directoryPageSize }} 个章节</p>
        </div>
      </div>



      <!-- 分页组件 -->
      <div class="pagination-wrapper" v-if="totalChapters > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="directoryPageSize"
          :total="totalChapters"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          :hide-on-single-page="false"
        />

      </div>

      <!-- 连续阅读模式已移除 -->
    </template>

    <div v-else class="error">
      <p>小说不存在或加载失败</p>
    </div>

    <!-- 章节阅读对话框 -->
    <el-dialog
      v-model="readingDialogVisible"
      :title="readingChapter?.title || '章节阅读'"
      width="900px"
      :close-on-click-modal="false"
      @open="onDialogOpen"
    >
      <div v-if="readingChapter" class="chapter-content">
        <div class="chapter-header">
          <h3>{{ readingChapter.title }}</h3>
          <p class="chapter-info">
            {{ readingChapter.title }} | {{ readingChapter.word_count }}字
          </p>
        </div>
        <div class="chapter-text">
          <div v-if="!readingChapter.content" class="loading-content">
            <el-icon size="24" class="loading-icon"><Loading /></el-icon>
            <p>正在加载章节内容...</p>
          </div>
          <div v-else class="content-wrapper">
            <p v-html="formatChapterContent(readingChapter.content)"></p>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="readingDialogVisible = false">关闭</el-button>
          <el-button
            v-if="readingChapter && getPreviousChapter()"
            @click="readChapter(getPreviousChapter()!)"
          >
            上一章
          </el-button>
          <el-button
            v-if="readingChapter && getNextChapter()"
            type="primary"
            @click="readChapter(getNextChapter()!)"
          >
            下一章
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog
      v-model="batchImportVisible"
      title="🚀 智能批量导入章节"
      width="500px"
      :close-on-click-modal="false"
      :z-index="3000"
      :modal="true"
      :append-to-body="true"
      class="batch-import-dialog"
    >
      <div class="batch-import-form">
        <el-form ref="formRef" :model="batchImportForm" label-width="120px">
          <el-form-item label="小说来源" required>
            <el-select
              v-model="batchImportForm.source_id"
              placeholder="请选择小说来源网站"
              style="width: 100%"
              size="large"
              clearable
              filterable
            >
              <el-option
                v-for="source in availableSources"
                :key="source.id"
                :label="`${source.name} - ${source.source_type}`"
                :value="source.id"
              >
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-weight: 500; color: #303133;">{{ source.name }}</span>
                  <span style="color: #909399; font-size: 12px; background: #f5f7fa; padding: 2px 6px; border-radius: 12px;">{{ source.source_type }}</span>
                </div>
                <div style="color: #c0c4cc; font-size: 11px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{ source.base_url }}</div>
              </el-option>
            </el-select>
            <!-- 调试信息 -->
            <div style="margin-top: 8px; font-size: 12px; color: #909399;">
              <div v-if="availableSources.length > 0">
                ✅ 已找到 {{ availableSources.length }} 个小说来源
              </div>
              <div v-else style="color: #f56c6c;">
                ⚠️ 未找到可用的小说来源，请先在来源管理中添加网站来源
              </div>
            </div>
          </el-form-item>
          
          <el-form-item label="最大章节数">
            <el-input-number
              v-model="batchImportForm.max_chapters"
              :min="1"
              :max="10000"
              placeholder="限制导入的章节数量"
              style="width: 100%"
            />
          </el-form-item>
          
          <el-alert
            title="智能导入说明"
            type="info"
            :closable="false"
            show-icon
          >
            <ul style="margin: 0; padding-left: 20px;">
              <li>🧠 使用内置LLM智能分析网站结构</li>
              <li>⏱️ 自动控制爬取速度(2-5秒延时)避免被封</li>
              <li>🔗 每个章节都会记录源链接</li>
              <li>🔄 支持断点续传，跳过已存在章节</li>
              <li>🧪 默认使用示例站点网进行测试</li>
            </ul>
          </el-alert>
        </el-form>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="batchImportVisible = false" :disabled="batchImportLoading">
            取消
          </el-button>
          <el-button 
            type="primary" 
            @click="executeBatchImport"
            :loading="batchImportLoading"
          >
            {{ batchImportLoading ? '正在导入...' : '开始导入' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<style scoped>
/* 批量导入对话框强制显示样式 */
.batch-import-dialog {
  z-index: 3000 !important;
}

:deep(.batch-import-dialog .el-dialog__wrapper) {
  z-index: 3000 !important;
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background-color: rgba(0, 0, 0, 0.5) !important;
  align-items: center !important;
  justify-content: center !important;
}

:deep(.batch-import-dialog .el-dialog) {
  position: relative !important;
  z-index: 3001 !important;
  background-color: white !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

.novel-detail {
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

.novel-header {
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.header-content {
  flex: 1;
}

.header-actions {
  flex-shrink: 0;
}

.novel-header h1 {
  margin: 0 0 12px 0;
  color: #303133;
}

.author {
  color: #606266;
  margin: 0 0 16px 0;
  font-size: 16px;
}

.description {
  color: #909399;
  line-height: 1.6;
  margin: 0;
}

.chapters-section .chapters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 4px 0;
  color: #303133;
}

.chapters-count {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.chapters-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.chapter-info h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-weight: 600;
  font-size: 16px;
  line-height: 1.4;
}

.chapter-meta {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.chapter-number {
  color: #409eff;
  font-weight: 500;
}

.chapter-actions {
  display: flex;
  gap: 8px;
}

.error {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.chapter-content {
  max-height: 600px;
  overflow-y: auto;
}

.chapter-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.chapter-header h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
}

.chapter-info {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.chapter-text {
  line-height: 1.8;
  color: #606266;
  font-size: 16px;
  text-align: justify;
}

.chapter-text p {
  margin: 0;
  text-indent: 2em;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
}



/* 分页样式 */
.pagination-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 30px;
  padding: 20px 0;
}

.batch-import-tools {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.directory-mode-info {
  margin-top: 10px;
  text-align: center;
  color: #409eff;
  font-weight: 500;
}

/* 章节目录样式 */
.chapters-list {
  max-height: 70vh;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 10px;
  background: #fafafa;
}

/* 连续阅读模式样式已移除 */

/* 章节内容加载状态 */
.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
  color: #909399;
}

.loading-content p {
  margin: 0;
  font-size: 14px;
}

/* 章节内容样式 */
.content-wrapper {
  line-height: 1.8;
  color: #606266;
  font-size: 16px;
  text-align: justify;
}

.content-wrapper p {
  margin: 0 0 16px 0;
  text-indent: 2em;
}

.content-wrapper p:last-child {
  margin-bottom: 0;
}

/* 排序工具栏样式 */
.sort-tools {
  margin: 20px 0;
  padding: 15px 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.sort-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.sort-info {
  color: #6c757d;
  font-size: 14px;
}

/* 批量导入对话框样式 */
.batch-import-form {
  padding: 10px 0;
}

.batch-import-form .el-alert {
  margin-top: 15px;
}

.batch-import-form .el-alert ul {
  font-size: 13px;
  line-height: 1.6;
}

.batch-import-form .el-alert li {
  margin-bottom: 5px;
}

</style>
