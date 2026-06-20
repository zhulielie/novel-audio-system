<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Search,
  Document,
  Calendar,
  User,
  View,
  Reading,
} from '@element-plus/icons-vue'
import type { Novel, NovelForm, NovelSource } from '@/types'
import { apiService } from '@/services/api'

const router = useRouter()

// 数据状态
const novels = ref<Novel[]>([])
const sources = ref<NovelSource[]>([])
const loading = ref(false)
const searchText = ref('')
const dialogVisible = ref(false)
const editingNovel = ref<Novel | null>(null)

// 表单数据
const novelForm = ref<NovelForm>({
  title: '',
  author: '',
  description: '',
  genre: '',
  status: 'draft',
  sources: [],
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入小说标题', trigger: 'blur' },
    { min: 1, max: 100, message: '标题长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  author: [
    { required: true, message: '请输入作者名称', trigger: 'blur' },
    { min: 1, max: 50, message: '作者名称长度在 1 到 50 个字符', trigger: 'blur' },
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' },
  ],
  genre: [
    { required: true, message: '请选择小说类型', trigger: 'change' },
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' },
  ],
}

// 小说类型选项
const genreOptions = [
  { label: '玄幻', value: 'fantasy' },
  { label: '都市', value: 'urban' },
  { label: '历史', value: 'history' },
  { label: '科幻', value: 'sci-fi' },
  { label: '武侠', value: 'wuxia' },
  { label: '言情', value: 'romance' },
  { label: '悬疑', value: 'mystery' },
  { label: '其他', value: 'other' },
]

// 状态选项
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '连载中', value: 'ongoing' },
  { label: '已完结', value: 'completed' },
  { label: '暂停', value: 'paused' },
]

// 计算属性
const filteredNovels = computed(() => {
  if (!searchText.value) return novels.value
  return novels.value.filter(novel => 
    novel.title.toLowerCase().includes(searchText.value.toLowerCase()) ||
    novel.author.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

// 获取小说列表
const fetchNovels = async () => {
  loading.value = true
  try {
    const response = await apiService.novels.list()
    novels.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch novels:', error)
    ElMessage.error('获取小说列表失败')
  } finally {
    loading.value = false
  }
}

// 获取小说来源列表
const fetchSources = async () => {
  try {
    const response = await apiService.novelSources.list()
    sources.value = (response as any)?.results || (response as any)?.data?.results || []
  } catch (error) {
    console.error('Failed to fetch sources:', error)
    ElMessage.error('获取来源列表失败')
  }
}

// 打开添加对话框
const openAddDialog = () => {
  editingNovel.value = null
  novelForm.value = {
    title: '',
    author: '',
    description: '',
    genre: '',
    status: 'draft',
    sources: [],
  }
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (novel: Novel) => {
  editingNovel.value = novel
  novelForm.value = {
    title: novel.title,
    author: novel.author,
    description: novel.description || '',
    genre: novel.genre,
    status: novel.status,
    sources: novel.sources || [],  // 如果没有sources信息，默认为空数组
  }
  dialogVisible.value = true
}

// 保存小说
const saveNovel = async () => {
  try {
    if (editingNovel.value) {
      // 编辑模式
      await apiService.novels.update(editingNovel.value.id, novelForm.value)
      ElMessage.success('小说更新成功')
    } else {
      // 添加模式
      await apiService.novels.create(novelForm.value)
      ElMessage.success('小说创建成功')
    }
    dialogVisible.value = false
    await fetchNovels()
  } catch (error) {
    console.error('Failed to save novel:', error)
    ElMessage.error('保存失败')
  }
}

// 查看小说详情
const viewNovelDetail = (novel: Novel) => {
  console.log('[Novels] 查看小说详情:', novel.title, 'ID:', novel.id)
  router.push(`/novels/${novel.id}`)
}

// 开始阅读小说
const startReadingNovel = (novel: Novel) => {
  console.log('[Novels] 开始阅读小说:', novel.title, 'ID:', novel.id)
  router.push({
    name: 'NovelReader',
    params: { id: novel.id },
    query: { chapter: 1 }
  })
}

// 删除小说
const deleteNovel = async (novel: Novel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除小说《${novel.title}》吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiService.novels.delete(novel.id)
    ElMessage.success('删除成功')
    await fetchNovels()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete novel:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: 'info',
    ongoing: 'success',
    completed: 'primary',
    paused: 'warning',
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option?.label || status
}

// 获取类型文本
const getGenreText = (genre: string) => {
  const option = genreOptions.find(opt => opt.value === genre)
  return option?.label || genre
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 获取来源类型文本
const getSourceTypeText = (sourceType: string) => {
  const typeMap: Record<string, string> = {
    'hetushu': '和图书',
    'qidian': '起点中文网',
    'zongheng': '纵横中文网',
    'custom': '自定义',
  }
  return typeMap[sourceType] || sourceType
}

// 组件挂载时获取数据
onMounted(() => {
  fetchNovels()
  fetchSources()
})
</script>

<template>
  <div class="novels-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Document /></el-icon>
          小说管理
        </h1>
        <p class="page-description">管理您的小说作品，添加章节和生成音频</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAddDialog">
        添加小说
      </el-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card shadow="never">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchText"
              placeholder="搜索小说标题或作者"
              :prefix-icon="Search"
              clearable
            />
          </el-col>
          <el-col :span="4">
            <el-button @click="fetchNovels" :loading="loading">
              刷新
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 小说列表 -->
    <div class="novels-list">
      <el-card shadow="never">
        <div v-loading="loading" class="list-content">
          <div v-if="filteredNovels.length === 0" class="empty-state">
            <el-empty description="暂无小说数据">
              <el-button type="primary" :icon="Plus" @click="openAddDialog">
                添加第一部小说
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="novels-grid">
            <div
              v-for="novel in filteredNovels"
              :key="novel.id"
              class="novel-card"
            >
              <div class="novel-header">
                <div class="novel-title" @click="viewNovelDetail(novel)">{{ novel.title }}</div>
                <div class="novel-actions">
                  <el-button
                    type="info"
                    :icon="View"
                    size="small"
                    circle
                    @click="viewNovelDetail(novel)"
                    title="小说详情"
                  />
                  <el-button
                    type="success"
                    :icon="Reading"
                    size="small"
                    circle
                    @click="startReadingNovel(novel)"
                    title="开始阅读"
                  />
                  <el-button
                    type="primary"
                    :icon="Edit"
                    size="small"
                    circle
                    @click="openEditDialog(novel)"
                    title="编辑小说"
                  />
                  <el-button
                    type="danger"
                    :icon="Delete"
                    size="small"
                    circle
                    @click="deleteNovel(novel)"
                    title="删除小说"
                  />
                </div>
              </div>
              
              <div class="novel-meta" @click="viewNovelDetail(novel)">
                <div class="meta-item">
                  <el-icon><User /></el-icon>
                  <span>{{ novel.author }}</span>
                </div>
                <div class="meta-item">
                  <el-icon><Calendar /></el-icon>
                  <span>{{ formatDate(novel.created_at) }}</span>
                </div>
              </div>
              
              <div class="novel-description">
                {{ novel.description || '暂无描述' }}
              </div>
              
              <div class="novel-footer">
                <div class="novel-tags">
                  <el-tag size="small">{{ getGenreText(novel.genre || '') }}</el-tag>
                  <el-tag
                    :type="getStatusType(novel.status || '')"
                    size="small"
                  >
                    {{ getStatusText(novel.status || '') }}
                  </el-tag>
                </div>
                <div class="novel-stats">
                  <span class="stat-item">{{ novel.chapters_count || 0 }} 章节</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingNovel ? '编辑小说' : '添加小说'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="novelForm"
        :rules="formRules"
        label-width="80px"
        label-position="left"
      >
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="novelForm.title"
            placeholder="请输入小说标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="作者" prop="author">
          <el-input
            v-model="novelForm.author"
            placeholder="请输入作者名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="类型" prop="genre">
          <el-select
            v-model="novelForm.genre"
            placeholder="请选择小说类型"
            style="width: 100%"
          >
            <el-option
              v-for="option in genreOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-select
            v-model="novelForm.status"
            placeholder="请选择状态"
            style="width: 100%"
          >
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="来源">
          <el-select
            v-model="novelForm.sources"
            placeholder="请选择小说来源（可多选）"
            style="width: 100%"
            multiple
            clearable
            filterable
          >
            <el-option
              v-for="source in sources.filter(s => s.is_active)"
              :key="source.id"
              :label="source.name"
              :value="source.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ source.name }}</span>
                <el-tag size="small" type="info">{{ getSourceTypeText(source.source_type) }}</el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-item-tip">
            <el-text type="info" size="small">
              选择小说来源网站，可同时选择多个来源用于爬取内容
            </el-text>
          </div>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="novelForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入小说描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveNovel">
            {{ editingNovel ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.novels-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: -0.02em;
}

.page-description {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.search-section {
  margin-bottom: 24px;
}

.list-content {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.novels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.novel-card {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  background: var(--bg-card);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.novel-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-3px);
  border-color: var(--primary-200);
}

.novel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.novel-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
  margin-right: 12px;
  line-height: 1.4;
  cursor: pointer;
  transition: color 0.2s;
}

.novel-title:hover {
  color: var(--primary-600);
}

.novel-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}

.novel-card:hover .novel-actions {
  opacity: 1;
}

.novel-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
  cursor: pointer;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--text-muted);
}

.meta-item .el-icon {
  font-size: 14px;
  color: var(--text-placeholder);
}

.novel-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 18px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 45px;
}

.novel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.novel-tags {
  display: flex;
  gap: 8px;
}

.novel-stats {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

.dialog-footer {
  text-align: right;
}

.form-item-tip {
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .novels-grid {
    grid-template-columns: 1fr;
  }
  
  .search-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section .el-col {
    width: 100%;
  }
}
</style>