<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'
import type { Chapter, Novel } from '@/types'

const chapters = ref<Chapter[]>([])
const novels = ref<Novel[]>([])
const loading = ref(true)
const dialogVisible = ref(false)
const editingChapter = ref<Chapter | null>(null)

// 表单数据
const chapterForm = ref({
  novel: '',
  title: '',
  content: '',
  chapter_number: '一',
  chapter_sort_number: 1,
  is_published: false
})

const fetchChapters = async () => {
  try {
    loading.value = true
    const response = await apiService.chapters.list()
    const data = response.data || response
    chapters.value = Array.isArray(data) ? data.filter(chapter => chapter && chapter.id) : []
  } catch (error) {
    console.error('获取章节列表失败:', error)
    chapters.value = []
  } finally {
    loading.value = false
  }
}

const fetchNovels = async () => {
  try {
    const response = await apiService.novels.list()
    const data = response.data || response
    novels.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取小说列表失败:', error)
  }
}

const openCreateDialog = () => {
  editingChapter.value = null
  chapterForm.value = {
    novel: '',
    title: '',
    content: '',
    chapter_number: '一',
    chapter_sort_number: 1,
    is_published: false
  }
  dialogVisible.value = true
}

const openEditDialog = (chapter: Chapter) => {
  editingChapter.value = chapter
  chapterForm.value = {
    novel: chapter.novel.toString(),
    title: chapter.title,
    content: chapter.content || '',
    chapter_number: chapter.chapter_number,
    chapter_sort_number: chapter.chapter_sort_number,
    is_published: chapter.is_published || false
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    const submitData = {
      ...chapterForm.value,
      novel: parseInt(chapterForm.value.novel)
    }
    
    if (editingChapter.value) {
      await apiService.chapters.update(editingChapter.value.id, submitData)
      ElMessage.success('章节更新成功！')
    } else {
      await apiService.chapters.create(submitData)
      ElMessage.success('章节创建成功！')
    }
    
    dialogVisible.value = false
    await fetchChapters()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(editingChapter.value ? '更新失败' : '创建失败')
  }
}

const handleDelete = async (chapter: Chapter) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除章节"${chapter.title}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiService.chapters.delete(chapter.id)
    ElMessage.success('删除成功！')
    await fetchChapters()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchChapters()
  fetchNovels()
})
</script>

<template>
  <div class="chapters-view">
    <div class="header">
      <h1>章节管理</h1>
      <el-button type="primary" size="large" @click="openCreateDialog" :icon="Plus">
        新建章节
      </el-button>
    </div>

    <div v-if="loading" class="loading">
      <el-icon size="48" class="loading-icon"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <div v-else-if="chapters.length === 0" class="empty-state">
      <p>暂无章节</p>
      <el-button type="primary" @click="openCreateDialog" :icon="Plus">
        创建第一个章节
      </el-button>
    </div>

    <div v-else class="chapters-list">
      <div
        v-for="chapter in chapters"
        :key="chapter.id || chapter.title"
        class="chapter-item"
      >
        <div class="chapter-info">
          <h3>{{ chapter.title }}</h3>
          <p class="chapter-meta">
            {{ chapter.title }} | {{ chapter.word_count }}字
          </p>
          <p class="chapter-preview">{{ chapter.content ? chapter.content.substring(0, 100) : '暂无内容预览' }}...</p>
        </div>
        <div class="chapter-actions">
          <el-button size="small" @click="openEditDialog(chapter)" :icon="Edit">
            编辑
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(chapter)" :icon="Delete">
            删除
          </el-button>
        </div>
      </div>
    </div>
  </div>

  <!-- 创建/编辑章节对话框 -->
  <el-dialog
    v-model="dialogVisible"
    :title="editingChapter ? '编辑章节' : '创建章节'"
    width="80%"
    :before-close="() => dialogVisible = false"
  >
    <el-form :model="chapterForm" label-width="100px">
      <el-form-item label="所属小说" required>
        <el-select v-model="chapterForm.novel" placeholder="请选择小说" style="width: 100%">
          <el-option
            v-for="novel in novels"
            :key="novel.id"
            :label="`${novel.title} (${novel.author})`"
            :value="novel.id.toString()"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="章节标题" required>
        <el-input v-model="chapterForm.title" placeholder="请输入章节标题" />
      </el-form-item>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="章节序号">
            <el-input v-model="chapterForm.chapter_number" placeholder="如：一、二、三..." />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="排序数字">
            <el-input-number v-model="chapterForm.chapter_sort_number" :min="1" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item label="章节内容">
        <el-input
          v-model="chapterForm.content"
          type="textarea"
          :rows="15"
          placeholder="请输入章节内容"
        />
      </el-form-item>
      
      <el-form-item label="发布状态">
        <el-switch v-model="chapterForm.is_published" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          {{ editingChapter ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.chapters-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.header h1 {
  margin: 0;
  color: #303133;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  gap: 16px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.chapters-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chapter-info {
  flex: 1;
}

.chapter-info h3 {
  margin: 0 0 8px 0;
  color: #303133;
}

.chapter-meta {
  margin: 0 0 12px 0;
  color: #909399;
  font-size: 14px;
}

.chapter-preview {
  margin: 0;
  color: #606266;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.chapter-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-left: 20px;
}
</style>
