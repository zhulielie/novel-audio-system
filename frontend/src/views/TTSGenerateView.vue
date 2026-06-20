<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Microphone,
  VideoPlay,
  Delete,
  Refresh,
  Download,
  Plus,
  ArrowRight,
  Document,
  User,
  Headset,
} from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const route = useRoute()

// 数据状态
const novels = ref<any[]>([])
const chapters = ref<any[]>([])
const voices = ref<any[]>([])
const engines = ref<any[]>([])
const tasks = ref<any[]>([])

const loading = ref(false)
const taskLoading = ref(false)

// 选择状态
const selectedNovel = ref<number | null>(null)
const selectedChapter = ref<number | null>(null)
const selectedEngine = ref<number | null>(null)

// 剧本编辑
const scriptData = ref<any[]>([])
const speakerVoiceMap = ref<Record<string, number>>({})
const taskName = ref('')

// 快速合成配置
const quickConfig = ref({
  narrator: '旁白',
  dialogue: '韩立',
})

// 计算属性
const filteredTasks = computed(() => {
  return tasks.value.slice(0, 20)
})

// 获取小说列表
const fetchNovels = async () => {
  try {
    const res: any = await apiService.novels.list()
    novels.value = res.results || res || []
  } catch (e) {
    console.error('获取小说失败', e)
  }
}

// 获取章节列表
const fetchChapters = async (novelId: number) => {
  try {
    const res: any = await apiService.novels.getChapters(novelId)
    chapters.value = res || []
  } catch (e) {
    console.error('获取章节失败', e)
  }
}

// 获取语音资源
const fetchVoices = async () => {
  try {
    const res: any = await apiService.tts.getVoices()
    voices.value = res.results || res || []
  } catch (e) {
    console.error('获取语音资源失败', e)
  }
}

// 获取引擎
const fetchEngines = async () => {
  try {
    const res: any = await apiService.tts.getEngines()
    engines.value = res.results || res || []
    const defaultEngine = engines.value.find((e: any) => e.is_default)
    if (defaultEngine) {
      selectedEngine.value = defaultEngine.id
    }
  } catch (e) {
    console.error('获取引擎失败', e)
  }
}

// 获取任务列表
const fetchTasks = async () => {
  taskLoading.value = true
  try {
    const res: any = await apiService.tts.getTasks()
    tasks.value = res.results || res || []
  } catch (e) {
    console.error('获取任务失败', e)
  } finally {
    taskLoading.value = false
  }
}

// 监听小说选择
watch(selectedNovel, (val) => {
  if (val) {
    fetchChapters(val)
    selectedChapter.value = null
    scriptData.value = []
  } else {
    chapters.value = []
  }
})

// 监听章节选择
watch(selectedChapter, (val) => {
  if (val) {
    const chapter = chapters.value.find((c: any) => c.id === val)
    if (chapter) {
      taskName.value = `${chapter.novel_title || ''} - ${chapter.title} 语音合成`
      // 自动生成剧本
      generateScriptFromChapter(chapter)
    }
  }
})

// 从章节内容生成剧本
const generateScriptFromChapter = (chapter: any) => {
  const content = chapter.content || ''
  const paragraphs = content.split('\n').filter((p: string) => p.trim())

  scriptData.value = paragraphs.slice(0, 30).map((text: string, index: number) => {
    const hasQuotes = /["""']/.test(text)
    const speaker = hasQuotes ? quickConfig.value.dialogue : quickConfig.value.narrator
    return {
      speaker,
      text: text.trim(),
      emotion: '',
    }
  })

  // 自动映射语音
  autoMapVoices()
}

// 自动映射语音
const autoMapVoices = () => {
  const speakers = [...new Set(scriptData.value.map(s => s.speaker))]
  speakerVoiceMap.value = {}

  speakers.forEach(speaker => {
    // 查找匹配的语音资源
    const match = voices.value.find((v: any) =>
      v.name.includes(speaker) ||
      (v.character_name && v.character_name.includes(speaker)) ||
      (speaker.includes('旁白') && v.voice_type === 'narrator')
    )
    if (match) {
      speakerVoiceMap.value[speaker] = match.id
    }
  })
}

// 添加剧本片段
const addSegment = () => {
  scriptData.value.push({
    speaker: quickConfig.value.narrator,
    text: '',
    emotion: '',
  })
}

// 删除剧本片段
const removeSegment = (index: number) => {
  scriptData.value.splice(index, 1)
}

// 快速合成
const handleQuickSynthesize = async () => {
  if (!selectedNovel.value || !selectedChapter.value) {
    ElMessage.warning('请选择小说和章节')
    return
  }

  loading.value = true
  try {
    const res: any = await apiService.tts.quickSynthesize({
      novel_id: selectedNovel.value,
      chapter_id: selectedChapter.value,
      speaker_configs: quickConfig.value,
    })

    if (res.success) {
      ElMessage.success(res.message)
      fetchTasks()
    } else {
      ElMessage.error(res.message || '合成失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '合成请求失败')
  } finally {
    loading.value = false
  }
}

// 高级合成（自定义剧本）
const handleAdvancedSynthesize = async () => {
  if (!selectedNovel.value) {
    ElMessage.warning('请选择小说')
    return
  }
  if (scriptData.value.length === 0) {
    ElMessage.warning('剧本不能为空')
    return
  }

  // 检查语音映射
  const speakers = [...new Set(scriptData.value.map(s => s.speaker))]
  const unmapped = speakers.filter(s => !speakerVoiceMap.value[s])
  if (unmapped.length > 0) {
    ElMessage.warning(`角色 ${unmapped.join(', ')} 未配置语音资源`)
    return
  }

  loading.value = true
  try {
    const res: any = await apiService.tts.createTask({
      name: taskName.value || '自定义语音合成',
      novel_id: selectedNovel.value,
      chapter_id: selectedChapter.value,
      engine_id: selectedEngine.value,
      script_data: scriptData.value,
      speaker_voice_map: speakerVoiceMap.value,
      generation_params: {},
    })

    if (res.success) {
      ElMessage.success(res.message)
      fetchTasks()
    } else {
      ElMessage.error(res.message || '创建任务失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '创建任务失败')
  } finally {
    loading.value = false
  }
}

// 取消任务
const cancelTask = async (task: any) => {
  try {
    await ElMessageBox.confirm('确定要取消这个任务吗？', '提示', { type: 'warning' })
    const res: any = await apiService.tts.cancelTask(task.id)
    if (res.success) {
      ElMessage.success('任务已取消')
      fetchTasks()
    }
  } catch (e) {
    // 用户取消
  }
}

// 重试任务
const retryTask = async (task: any) => {
  try {
    const res: any = await apiService.tts.retryTask(task.id)
    if (res.success) {
      ElMessage.success('任务已重试')
      fetchTasks()
    }
  } catch (e) {
    ElMessage.error('重试失败')
  }
}

// 删除任务
const deleteTask = async (task: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '提示', { type: 'warning' })
    await apiService.delete(`/tts-tasks/${task.id}/`)
    ElMessage.success('任务已删除')
    fetchTasks()
  } catch (e) {
    // 用户取消
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    preparing: 'warning',
    generating: 'warning',
    merging: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    preparing: '准备中',
    generating: '生成中',
    merging: '合并中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[status] || status
}

// 获取语音名称
const getVoiceName = (voiceId: number) => {
  const voice = voices.value.find((v: any) => v.id === voiceId)
  return voice?.name || `语音#${voiceId}`
}

onMounted(async () => {
  await fetchNovels()
  fetchVoices()
  fetchEngines()
  fetchTasks()

  // 从爬虫页面跳转过来时自动选择小说和第一章
  const queryNovelId = route.query.novel_id
  if (queryNovelId) {
    const novelId = Number(queryNovelId)
    const novel = novels.value.find((n: any) => n.id === novelId)
    if (novel) {
      selectedNovel.value = novelId
      // 章节列表加载后自动选择第一章
      const unwatch = watch(chapters, (list) => {
        if (list && list.length > 0) {
          selectedChapter.value = list[0].id
          unwatch()
        }
      })
    }
  }
})
</script>

<template>
  <div class="tts-generate-page">
    <el-row :gutter="20">
      <!-- 左侧：配置面板 -->
      <el-col :xs="24" :lg="14">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Microphone /></el-icon> TTS 语音合成</span>
            </div>
          </template>

          <!-- 基本信息 -->
          <el-form label-width="100px" class="config-form">
            <el-form-item label="任务名称">
              <el-input v-model="taskName" placeholder="输入任务名称" />
            </el-form-item>

            <el-form-item label="选择小说">
              <el-select v-model="selectedNovel" placeholder="选择小说" style="width: 100%">
                <el-option
                  v-for="novel in novels"
                  :key="novel.id"
                  :label="novel.title"
                  :value="novel.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="选择章节">
              <el-select v-model="selectedChapter" placeholder="选择章节" style="width: 100%">
                <el-option
                  v-for="chapter in chapters"
                  :key="chapter.id"
                  :label="chapter.title"
                  :value="chapter.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="TTS 引擎">
              <el-select v-model="selectedEngine" placeholder="选择引擎" style="width: 100%">
                <el-option
                  v-for="engine in engines"
                  :key="engine.id"
                  :label="engine.name"
                  :value="engine.id"
                />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- 快速合成配置 -->
          <el-divider>快速合成配置</el-divider>
          <el-row :gutter="10">
            <el-col :span="12">
              <el-form-item label="旁白角色">
                <el-input v-model="quickConfig.narrator" placeholder="旁白角色名" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="对话角色">
                <el-input v-model="quickConfig.dialogue" placeholder="对话角色名" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-button type="primary" :loading="loading" @click="handleQuickSynthesize" style="width: 100%; margin-bottom: 10px">
            <el-icon><VideoPlay /></el-icon> 快速合成（自动解析章节）
          </el-button>

          <!-- 剧本编辑 -->
          <el-divider>剧本编辑（高级）</el-divider>

          <div class="script-editor">
            <div v-for="(segment, index) in scriptData" :key="index" class="script-segment">
              <el-row :gutter="5" align="middle">
                <el-col :span="4">
                  <el-input v-model="segment.speaker" size="small" placeholder="角色" />
                </el-col>
                <el-col :span="16">
                  <el-input v-model="segment.text" size="small" type="textarea" :rows="1" placeholder="文本内容" />
                </el-col>
                <el-col :span="3">
                  <el-select v-model="segment.emotion" size="small" placeholder="情绪">
                    <el-option label="无" value="" />
                    <el-option label="平静" value="calm" />
                    <el-option label="兴奋" value="excited" />
                    <el-option label="悲伤" value="sad" />
                    <el-option label="愤怒" value="angry" />
                  </el-select>
                </el-col>
                <el-col :span="1">
                  <el-button type="danger" size="small" circle @click="removeSegment(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>

            <el-button type="dashed" @click="addSegment" style="width: 100%; margin-top: 10px">
              <el-icon><Plus /></el-icon> 添加片段
            </el-button>
          </div>

          <!-- 角色语音映射 -->
          <el-divider>角色语音映射</el-divider>
          <div class="voice-mapping">
            <el-row v-for="speaker in [...new Set(scriptData.map(s => s.speaker))]" :key="speaker" :gutter="10" align="middle" style="margin-bottom: 8px">
              <el-col :span="6">
                <el-tag type="primary">{{ speaker }}</el-tag>
              </el-col>
              <el-col :span="18">
                <el-select v-model="speakerVoiceMap[speaker]" placeholder="选择语音" style="width: 100%" size="small">
                  <el-option
                    v-for="voice in voices"
                    :key="voice.id"
                    :label="voice.name"
                    :value="voice.id"
                  />
                </el-select>
              </el-col>
            </el-row>
          </div>

          <el-button type="success" :loading="loading" @click="handleAdvancedSynthesize" style="width: 100%; margin-top: 15px">
            <el-icon><Microphone /></el-icon> 高级合成（自定义剧本）
          </el-button>
        </el-card>
      </el-col>

      <!-- 右侧：任务列表 -->
      <el-col :xs="24" :lg="10">
        <el-card class="tasks-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Headset /></el-icon> 合成任务</span>
              <el-button size="small" circle @click="fetchTasks">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>

          <el-table :data="filteredTasks" v-loading="taskLoading" size="small" style="width: 100%">
            <el-table-column prop="name" label="任务" show-overflow-tooltip>
              <template #default="{ row }">
                <div class="task-name">{{ row.name }}</div>
                <div class="task-meta">{{ row.novel_title }} {{ row.chapter_title ? '- ' + row.chapter_title : '' }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.progress || 0" :status="row.status === 'failed' ? 'exception' : undefined" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button-group size="small">
                  <el-button v-if="row.status === 'failed'" type="primary" circle @click="retryTask(row)">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                  <el-button v-if="['pending', 'preparing', 'generating'].includes(row.status)" type="warning" circle @click="cancelTask(row)">
                    <el-icon><VideoPlay /></el-icon>
                  </el-button>
                  <el-button type="danger" circle @click="deleteTask(row)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="tasks.length === 0" description="暂无合成任务" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.tts-generate-page {
  padding: 20px;
}

.config-card, .tasks-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.card-header .el-icon {
  margin-right: 6px;
  vertical-align: middle;
}

.config-form {
  margin-top: 10px;
}

.script-editor {
  max-height: 400px;
  overflow-y: auto;
  padding: 5px;
}

.script-segment {
  padding: 6px;
  margin-bottom: 6px;
  background: #f8f9fa;
  border-radius: 6px;
}

.script-segment:hover {
  background: #e9ecef;
}

.voice-mapping {
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.task-name {
  font-weight: 500;
  font-size: 13px;
}

.task-meta {
  font-size: 11px;
  color: #909399;
}
</style>
