<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, Upload } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const voices = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingVoice = ref<any>(null)

const voiceForm = ref({
  name: '',
  voice_type: 'custom',
  description: '',
  tags: '',
  is_active: true,
})

const voiceTypes = [
  { label: '旁白', value: 'narrator' },
  { label: '男声', value: 'male' },
  { label: '女声', value: 'female' },
  { label: '童声', value: 'child' },
  { label: '老者', value: 'elderly' },
  { label: '自定义', value: 'custom' },
]

const fetchVoices = async () => {
  loading.value = true
  try {
    const res: any = await apiService.tts.getVoices()
    voices.value = res.results || res || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleImport = async () => {
  try {
    const res: any = await apiService.tts.importVoices()
    if (res.success) {
      ElMessage.success(res.message)
      fetchVoices()
    }
  } catch (e) {
    ElMessage.error('导入失败')
  }
}

const handleDelete = async (voice: any) => {
  try {
    await ElMessageBox.confirm('确定删除此语音资源？', '提示', { type: 'warning' })
    await apiService.tts.deleteVoice(voice.id)
    ElMessage.success('已删除')
    fetchVoices()
  } catch (e) { /* cancel */ }
}

const openDialog = (voice?: any) => {
  editingVoice.value = voice || null
  if (voice) {
    voiceForm.value = { ...voice }
  } else {
    voiceForm.value = { name: '', voice_type: 'custom', description: '', tags: '', is_active: true }
  }
  dialogVisible.value = true
}

const saveVoice = async () => {
  try {
    if (editingVoice.value) {
      await apiService.tts.updateVoice(editingVoice.value.id, voiceForm.value)
    } else {
      await apiService.tts.createVoice(voiceForm.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchVoices()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchVoices)
</script>

<template>
  <div class="tts-voices-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>语音资源管理</span>
          <div>
            <el-button type="primary" size="small" @click="handleImport">
              <el-icon><Upload /></el-icon> 从媒体库导入
            </el-button>
            <el-button type="success" size="small" @click="openDialog()">
              <el-icon><Plus /></el-icon> 新增
            </el-button>
            <el-button size="small" circle @click="fetchVoices">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="voices" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="voice_type_display" label="类型" width="100" />
        <el-table-column prop="duration" label="时长(秒)" width="100">
          <template #default="{ row }">{{ row.duration ? row.duration.toFixed(1) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" circle @click="openDialog(row)">
              <el-icon><Upload /></el-icon>
            </el-button>
            <el-button type="danger" size="small" circle @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingVoice ? '编辑语音' : '新增语音'" width="500px">
      <el-form :model="voiceForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="voiceForm.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="voiceForm.voice_type" style="width: 100%">
            <el-option v-for="t in voiceTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="voiceForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="voiceForm.tags" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="voiceForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveVoice">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tts-voices-page { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
