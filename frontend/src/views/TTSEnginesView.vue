<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Refresh, SetUp } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const engines = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingEngine = ref<any>(null)

const engineForm = ref({
  name: '',
  engine_type: 'gpt_sovits',
  api_url: '',
  is_local: true,
  default_params: {} as any,
  is_active: true,
  priority: 1,
})

const engineTypes = [
  { label: 'GPT-SoVITS', value: 'gpt_sovits' },
  { label: 'CosyVoice', value: 'cosyvoice' },
  { label: 'XTTS', value: 'xtts' },
  { label: 'IndexTTS', value: 'indextts' },
  { label: 'Fish Speech', value: 'fish_speech' },
  { label: 'Edge TTS', value: 'edge_tts' },
]

const fetchEngines = async () => {
  loading.value = true
  try {
    const res: any = await apiService.tts.getEngines()
    engines.value = res.results || res || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const initDefaults = async () => {
  try {
    const res: any = await apiService.tts.initDefaultEngines()
    if (res.success) {
      ElMessage.success(res.message)
      fetchEngines()
    }
  } catch (e) {
    ElMessage.error('初始化失败')
  }
}

const setDefault = async (engine: any) => {
  try {
    const res: any = await apiService.tts.setDefaultEngine(engine.id)
    if (res.success) {
      ElMessage.success(res.message)
      fetchEngines()
    }
  } catch (e) {
    ElMessage.error('设置失败')
  }
}

const handleDelete = async (engine: any) => {
  try {
    await apiService.tts.deleteEngine(engine.id)
    ElMessage.success('已删除')
    fetchEngines()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const openDialog = (engine?: any) => {
  editingEngine.value = engine || null
  if (engine) {
    engineForm.value = { ...engine }
  } else {
    engineForm.value = { name: '', engine_type: 'gpt_sovits', api_url: '', is_local: true, default_params: {}, is_active: true, priority: 1 }
  }
  dialogVisible.value = true
}

const saveEngine = async () => {
  try {
    if (editingEngine.value) {
      await apiService.tts.updateEngine(editingEngine.value.id, engineForm.value)
    } else {
      await apiService.tts.createEngine(engineForm.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchEngines()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(fetchEngines)
</script>

<template>
  <div class="tts-engines-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>TTS 引擎配置</span>
          <div>
            <el-button type="warning" size="small" @click="initDefaults">
              <el-icon><SetUp /></el-icon> 初始化默认配置
            </el-button>
            <el-button type="success" size="small" @click="openDialog()">
              <el-icon><Plus /></el-icon> 新增
            </el-button>
            <el-button size="small" circle @click="fetchEngines">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="engines" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="engine_type_display" label="类型" width="120" />
        <el-table-column prop="api_url" label="API地址" show-overflow-tooltip />
        <el-table-column prop="is_local" label="部署方式" width="100">
          <template #default="{ row }">{{ row.is_local ? '本地' : '远程' }}</template>
        </el-table-column>
        <el-table-column prop="is_default" label="默认" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button v-if="!row.is_default" size="small" @click="setDefault(row)">设为默认</el-button>
            <el-button type="primary" size="small" circle @click="openDialog(row)">
              <el-icon><SetUp /></el-icon>
            </el-button>
            <el-button type="danger" size="small" circle @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingEngine ? '编辑引擎' : '新增引擎'" width="500px">
      <el-form :model="engineForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="engineForm.name" />
        </el-form-item>
        <el-form-item label="引擎类型">
          <el-select v-model="engineForm.engine_type" style="width: 100%">
            <el-option v-for="t in engineTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址">
          <el-input v-model="engineForm.api_url" placeholder="本地引擎可留空" />
        </el-form-item>
        <el-form-item label="本地部署">
          <el-switch v-model="engineForm.is_local" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="engineForm.priority" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="engineForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEngine">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tts-engines-page { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
