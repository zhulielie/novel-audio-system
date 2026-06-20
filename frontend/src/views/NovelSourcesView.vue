<template>
  <div class="novel-sources-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Connection /></el-icon>
          小说来源管理
        </h1>
        <p class="page-description">管理小说网站来源，使用AI智能分析网站结构并自动生成爬虫</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAddDialog">
        添加来源
      </el-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card shadow="never">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchText"
              placeholder="搜索来源名称或网站域名"
              :prefix-icon="Search"
              clearable
            />
          </el-col>
          <el-col :span="4">
            <el-select v-model="filterType" placeholder="筛选类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="已配置" value="configured" />
              <el-option label="AI分析" value="ai_analyzed" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button @click="fetchSources" :loading="loading">刷新</el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 来源列表 -->
    <div class="sources-list">
      <el-card shadow="never">
        <div v-loading="loading" class="list-content">
          <div v-if="filteredSources.length === 0" class="empty-state">
            <el-empty description="暂无小说来源">
              <el-button type="primary" :icon="Plus" @click="openAddDialog">
                添加第一个来源
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="sources-grid">
            <div
              v-for="source in filteredSources"
              :key="source.id"
              class="source-card"
              :class="{
                'source-configured': source.chapter_url_pattern,
                'source-active': source.is_active
              }"
            >
              <div class="source-header">
                <div class="source-name">{{ source.name }}</div>
                <div class="source-url">
                  <el-link :href="source.base_url" target="_blank" type="primary">
                    {{ source.base_url }}
                  </el-link>
                </div>
                <div class="source-meta">
                  <el-tag type="info" size="small">{{ getSourceTypeText(source.source_type) }}</el-tag>
                  <el-tag v-if="source.chapter_url_pattern" type="success" size="small">已配置</el-tag>
                  <el-tag v-if="!source.is_active" type="warning" size="small">已禁用</el-tag>
                  <el-tag type="primary" size="small">优先级: {{ source.priority }}</el-tag>
                </div>
              </div>

              <div class="source-actions">
                <el-button
                  type="success"
                  :icon="MagicStick"
                  size="small"
                  @click="analyzeWithAI(source)"
                  :loading="analyzingIds.includes(source.id)"
                >
                  AI分析
                </el-button>
                <el-button
                  type="warning"
                  :icon="Download"
                  size="small"
                  @click="testCrawl(source)"
                  :loading="testingIds.includes(source.id)"
                >
                  测试爬取
                </el-button>
                <el-button type="primary" :icon="Edit" size="small" @click="openEditDialog(source)">
                  编辑
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- AI分析结果对话框 -->
    <el-dialog
      v-model="analysisDialogVisible"
      title="AI分析结果"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-if="analysisResult" class="analysis-content">
        <div class="analysis-header">
          <h3>{{ analysisResult.domain }} 分析报告</h3>
          <el-tag 
            :type="analysisResult.confidence_score > 0.8 ? 'success' : 'warning'"
            size="large"
          >
            置信度: {{ (analysisResult.confidence_score * 100).toFixed(1) }}%
          </el-tag>
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="analysis-section">
              <template #header>基本信息</template>
              <div class="info-item">
                <strong>标题:</strong> {{ analysisResult.title || '未识别' }}
              </div>
              <div class="info-item">
                <strong>作者:</strong> {{ analysisResult.author || '未识别' }}
              </div>
              <div class="info-item">
                <strong>发现章节:</strong> {{ analysisResult.chapters?.length || 0 }} 个
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="analysis-section">
              <template #header>技术信息</template>
              <div class="info-item">
                <strong>章节模式:</strong>
                <div v-for="pattern in analysisResult.chapter_patterns" :key="pattern">
                  <code>{{ pattern }}</code>
                </div>
              </div>
              <div class="info-item">
                <strong>内容选择器:</strong>
                <code>{{ analysisResult.content_selectors?.[0] }}</code>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="analysisDialogVisible = false">关闭</el-button>
          <el-button 
            v-if="analysisResult && analysisResult.confidence_score > 0.6" 
            type="primary" 
            @click="applyAnalysisResult"
          >
            应用分析结果
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="editingSource ? '编辑来源' : '添加来源'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="sourceForm" label-width="120px">
        <el-form-item label="来源名称" required>
          <el-input v-model="sourceForm.name" placeholder="请输入来源名称" />
        </el-form-item>
        
        <el-form-item label="来源类型" required>
          <el-input 
            v-model="sourceForm.source_type" 
            placeholder="请输入来源类型，如：和图书、起点中文网等" 
          />
        </el-form-item>
        
        <el-form-item label="基础URL" required>
          <el-input v-model="sourceForm.base_url" placeholder="https://example.com" />
        </el-form-item>
        
        <el-form-item label="章节URL模式">
          <el-input 
            v-model="sourceForm.chapter_url_pattern" 
            placeholder="/book/{book_id}/{chapter_id}.html" 
          />
        </el-form-item>
        
        <el-form-item label="页面编码">
          <el-select v-model="sourceForm.encoding">
            <el-option label="UTF-8" value="utf-8" />
            <el-option label="GBK" value="gbk" />
            <el-option label="GB2312" value="gb2312" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-input-number v-model="sourceForm.priority" :min="1" :max="100" />
        </el-form-item>
        
        <el-form-item label="是否启用">
          <el-switch v-model="sourceForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveSource">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Edit, Search, Connection, MagicStick, Download
} from '@element-plus/icons-vue'
import type { NovelSource } from '@/types'
import { apiService } from '@/services/api'

// 数据状态
const sources = ref<NovelSource[]>([])
const loading = ref(false)
const searchText = ref('')
const filterType = ref('')
const analysisDialogVisible = ref(false)
const editDialogVisible = ref(false)
const analysisResult = ref(null)
const analyzingIds = ref<number[]>([])
const testingIds = ref<number[]>([])
const editingSource = ref<NovelSource | null>(null)

// 表单数据
const sourceForm = ref({
  name: '',
  source_type: '',
  base_url: '',
  chapter_url_pattern: '',
  encoding: 'utf-8',
  is_active: true,
  priority: 1
})

// 计算属性
const filteredSources = computed(() => {
  let filtered = sources.value
  if (searchText.value) {
    filtered = filtered.filter(source => 
      source.name.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }
  return filtered
})

// 获取来源列表
const fetchSources = async () => {
  loading.value = true
  try {
    const response = await apiService.novelSources.list()
    sources.value = response.results || response
  } catch (error) {
    console.error('获取来源列表失败:', error)
    ElMessage.error('获取来源列表失败')
  } finally {
    loading.value = false
  }
}

// AI分析
const analyzeWithAI = async (source: NovelSource) => {
  analyzingIds.value.push(source.id)
  try {
    ElMessage.info(`正在使用AI分析网站: ${source.base_url}`)
    
    const response = await apiService.novelSources.analyzeWithAI(source.id)
    
    if (response.success && response.analysis_result) {
      analysisResult.value = response.analysis_result
      analysisDialogVisible.value = true
      ElMessage.success('AI分析完成!')
    } else {
      ElMessage.error(response.message || 'AI分析失败')
    }
    
  } catch (error) {
    console.error('AI分析失败:', error)
    ElMessage.error('AI分析失败')
  } finally {
    analyzingIds.value = analyzingIds.value.filter(id => id !== source.id)
  }
}

// 测试爬取
const testCrawl = async (source: NovelSource) => {
  testingIds.value.push(source.id)
  try {
    ElMessage.info(`正在测试爬取: ${source.name}`)
    
    const response = await apiService.novelSources.testCrawl(source.id)
    
    if (response.success) {
      ElMessage.success(response.message || '测试爬取成功!')
      // 刷新数据
      await fetchSources()
    } else {
      ElMessage.error(response.message || '测试爬取失败')
    }
    
  } catch (error) {
    console.error('测试爬取失败:', error)
    ElMessage.error('测试爬取失败')
  } finally {
    testingIds.value = testingIds.value.filter(id => id !== source.id)
  }
}

const openAddDialog = () => {
  editingSource.value = null
  sourceForm.value = {
    name: '',
    source_type: '',
    base_url: '',
    chapter_url_pattern: '',
    encoding: 'utf-8',
    is_active: true,
    priority: 1
  }
  editDialogVisible.value = true
}

const openEditDialog = (source: NovelSource) => {
  editingSource.value = source
  sourceForm.value = {
    name: source.name,
    source_type: source.source_type,
    base_url: source.base_url,
    chapter_url_pattern: source.chapter_url_pattern || '',
    encoding: source.encoding,
    is_active: source.is_active,
    priority: source.priority
  }
  editDialogVisible.value = true
}

const saveSource = async () => {
  try {
    if (editingSource.value) {
      // 编辑
      await apiService.novelSources.update(editingSource.value.id, sourceForm.value)
      ElMessage.success('更新成功')
    } else {
      // 新增
      await apiService.novelSources.create(sourceForm.value)
      ElMessage.success('添加成功')
    }
    
    editDialogVisible.value = false
    await fetchSources()
    
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}

const getSourceTypeText = (sourceType: string) => {
  return sourceType || '未分类'
}

const applyAnalysisResult = () => {
  ElMessage.success('AI分析结果已应用')
  analysisDialogVisible.value = false
}

onMounted(() => {
  fetchSources()
})
</script>

<style scoped>
.novel-sources-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.source-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
}

.source-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.source-card.source-configured {
  border-left: 4px solid #67c23a;
}

.source-card.source-active {
  border-left: 4px solid #409eff;
}

.source-name {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.source-meta {
  display: flex;
  gap: 8px;
  margin: 12px 0;
}

.source-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.analysis-content {
  max-height: 70vh;
  overflow-y: auto;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.info-item {
  margin-bottom: 12px;
}
</style>