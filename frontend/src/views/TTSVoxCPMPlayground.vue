<template>
  <div class="voxcpm-playground">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span class="title">VoxCPM 2.0 语音合成调参</span>
          <el-tag type="success" size="large">48kHz · 2B参数 · RTX 5090</el-tag>
        </div>
      </template>
    </el-card>

    <el-row :gutter="20">
      <el-col :md="12" :xs="24">
        <el-card>
          <template #header>参数设置</template>
          <el-form label-width="130px" label-position="top" size="default">
            <el-form-item label="快速预设">
              <el-button v-for="p in presets" :key="p.label" @click="loadPreset(p)" size="small" style="margin:3px" :type="activePreset?.label===p.label?'primary':'default'">{{ p.label }}</el-button>
              <div v-if="activePreset" class="preset-info">
                <strong>{{ activePreset.label }}</strong>
                <span class="hint">{{ activePreset.desc }}</span>
                <el-tag size="small" v-for="t in activePreset.tags" :key="t" style="margin:2px">{{ t }}</el-tag>
              </div>
            </el-form-item>

            <el-form-item label="合成模式">
              <el-radio-group v-model="form.mode">
                <el-radio-button value="base">音色设计（随机）</el-radio-button>
                <el-radio-button value="clone">声音克隆（固定音色）</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <!-- 克隆模式：选参考 -->
            <el-form-item v-if="form.mode==='clone'" label="选择参考音色">
              <el-select v-model="form.reference_audio" placeholder="选择已保存的参考" style="width:100%" clearable>
                <el-option v-for="r in references" :key="r.filename" :label="r.label" :value="r.path">
                  <span>{{ r.label }}</span>
                  <span class="hint" style="float:right;margin-left:8px">{{ r.params?.duration }}s</span>
                </el-option>
              </el-select>
              <span class="hint" v-if="!references.length">还没有参考，先音色设计生成一个满意的，点击"保存为参考"</span>
            </el-form-item>

            <el-form-item label="合成文本（≤500字）">
              <el-input v-model="form.text" type="textarea" :rows="3" maxlength="500" show-word-limit />
            </el-form-item>

            <el-form-item><template #label>CFG 引导强度：{{ form.cfg_value }}</template>
              <el-slider v-model="form.cfg_value" :min="1.0" :max="3.0" :step="0.1" show-input :marks="{1.0:'自然',2.0:'默认',3.0:'紧凑'}" />
              <span class="hint">控制语音节奏贴合度。低=自然松散，高=紧凑有力</span>
            </el-form-item>

            <el-form-item><template #label>推理步数：{{ form.inference_timesteps }}</template>
              <el-slider v-model="form.inference_timesteps" :min="5" :max="20" :step="1" show-input :marks="{5:'快速',10:'默认',15:'高质',20:'最高'}" />
              <span class="hint">步数越高质量越好，速度越慢</span>
            </el-form-item>

            <el-form-item><template #label>最大长度：{{ form.max_len }}</template>
              <el-slider v-model="form.max_len" :min="256" :max="4096" :step="256" show-input />
            </el-form-item>

            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="文本归一化"><el-switch v-model="form.normalize" /></el-form-item>
              </el-col>
              <el-col :span="12" v-if="form.mode==='clone'">
                <el-form-item label="降噪"><el-switch v-model="form.denoise" /></el-form-item>
              </el-col>
            </el-row>

            <el-button type="primary" size="large" :loading="generating" @click="synthesize" style="width:100%">
              {{ generating ? '生成中...' : '生成语音' }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :md="12" :xs="24">
        <!-- 参考管理 -->
        <el-card>
          <template #header>
            我的参考音色
            <el-button size="small" style="float:right" @click="loadRefs" :loading="loadingRefs">刷新</el-button>
          </template>
          <el-table :data="references" size="small" max-height="200" v-if="references.length">
            <el-table-column prop="label" label="名称" min-width="100" />
            <el-table-column prop="params.duration" label="时长" width="55" align="center"><template #default="{row}">{{ row.params?.duration || '-' }}s</template></el-table-column>
            <el-table-column label="播放" width="55" align="center">
              <template #default="{row}"><el-button size="small" @click="playRef(row)" circle><el-icon><VideoPlay /></el-icon></el-button></template>
            </el-table-column>
            <el-table-column label="操作" width="55" align="center">
              <template #default="{row}"><el-button size="small" @click="delRef(row)" circle type="danger"><el-icon><Delete /></el-icon></el-button></template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无参考。生成满意的音频后点击「保存为参考」" />
          <div v-if="refPlayer" style="margin-top:8px">
            <audio controls autoplay style="width:100%"><source :src="refPlayer.url" type="audio/wav" /></audio>
          </div>
        </el-card>

        <!-- 本次结果 -->
        <el-card v-if="result" style="margin-top:16px">
          <template #header>
            本次生成
            <el-button size="small" type="success" style="float:right" @click="saveRef(result)" v-if="form.mode==='base'">保存为参考</el-button>
          </template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="时长">{{ result.duration }}s</el-descriptions-item>
            <el-descriptions-item label="耗时">{{ result.runtime }}s</el-descriptions-item>
            <el-descriptions-item label="RTF">{{ result.rtf }}</el-descriptions-item>
            <el-descriptions-item label="采样率">{{ result.sample_rate }}Hz</el-descriptions-item>
          </el-descriptions>
          <audio v-if="result.audio_url" controls style="width:100%;margin-top:12px">
            <source :src="result.audio_url" type="audio/wav" />
          </audio>
        </el-card>

        <!-- 历史 -->
        <el-card style="margin-top:16px">
          <template #header>已生成音频 <el-button size="small" style="float:right" @click="loadHistory" :loading="loadingHistory">刷新</el-button></template>
          <el-table :data="historyFiles" size="small" max-height="250" @row-click="showParams" highlight-current-row v-if="historyFiles.length">
            <el-table-column prop="name" label="文件名" min-width="160" show-overflow-tooltip />
            <el-table-column label="时长" width="55" align="center"><template #default="{row}">{{ row.duration }}s</template></el-table-column>
            <el-table-column label="播放" width="55" align="center">
              <template #default="{row}"><el-button size="small" @click.stop="playHistory(row)" circle><el-icon><VideoPlay /></el-icon></el-button></template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无" />
          <div v-if="historyPlayer" style="margin-top:8px">
            <audio controls autoplay style="width:100%"><source :src="historyPlayer.url" type="audio/wav" /></audio>
          </div>
        </el-card>

        <!-- 参数详情 -->
        <el-card v-if="selectedParams" style="margin-top:16px">
          <template #header>参数详情</template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="模式">{{ selectedParams.mode==='clone'?'克隆':'音色设计' }}</el-descriptions-item>
            <el-descriptions-item label="CFG">{{ selectedParams.cfg_value }}</el-descriptions-item>
            <el-descriptions-item label="步数">{{ selectedParams.inference_timesteps }}</el-descriptions-item>
            <el-descriptions-item label="最大长度">{{ selectedParams.max_len||4096 }}</el-descriptions-item>
            <el-descriptions-item label="归一化">{{ selectedParams.normalize?'开':'关' }}</el-descriptions-item>
            <el-descriptions-item label="降噪">{{ selectedParams.denoise?'开':'关' }}</el-descriptions-item>
            <el-descriptions-item label="时长">{{ selectedParams.duration }}s</el-descriptions-item>
            <el-descriptions-item label="RTF">{{ selectedParams.rtf }}</el-descriptions-item>
            <el-descriptions-item label="采样率">{{ selectedParams.sample_rate }}Hz</el-descriptions-item>
            <el-descriptions-item label="时间">{{ selectedParams.timestamp }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top:8px"><strong>文本：</strong><p class="param-text">{{ selectedParams.text }}</p></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/services/api'

const generating = ref(false)
const loadingHistory = ref(false)
const loadingRefs = ref(false)
const activePreset = ref<any>(null)
const result = ref<any>(null)
const historyFiles = ref<any[]>([])
const historyPlayer = ref<any>(null)
const selectedParams = ref<any>(null)
const references = ref<any[]>([])
const refPlayer = ref<any>(null)

const form = reactive({
  text: '韩立站在黄枫谷的山门前，望着远处云雾缭绕的群山，心中不禁感慨万千。',
  mode: 'base', cfg_value: 2.0, inference_timesteps: 10,
  max_len: 4096, normalize: false, denoise: false,
  reference_audio: '',
})

const presets = [
  { label:'默认旁白', desc:'标准叙事', tags:['CFG2.0','步数10'], text:'韩立站在黄枫谷的山门前，望着远处云雾缭绕的群山，心中不禁感慨万千。他缓缓迈步，走进了坊市。', mode:'base', cfg_value:2.0, inference_timesteps:10, normalize:false, max_len:4096 },
  { label:'沉稳叙述', desc:'CFG提高+归一化', tags:['CFG2.5','步数12','归一化'], text:'夜幕降临，整座黄枫谷笼罩在一片寂静之中。唯有山门前的两盏长明灯，在夜风中微微摇曳。', mode:'base', cfg_value:2.5, inference_timesteps:12, normalize:true, max_len:4096 },
  { label:'轻快旁白', desc:'低CFG自然感', tags:['CFG1.5','步数8'], text:'第二天一早，韩立就收拾好了行装。今天是个好天气，阳光透过树叶洒在青石路上，斑驳陆离。', mode:'base', cfg_value:1.5, inference_timesteps:8, normalize:false, max_len:4096 },
  { label:'内心独白', desc:'内心思考语气', tags:['CFG1.8','步数10'], text:'这坊市比十年前热闹多了。那时我不过是个炼气期的小修士，如今却已踏入筑基之境，真是恍如隔世啊。', mode:'base', cfg_value:1.8, inference_timesteps:10, normalize:false, max_len:4096 },
  { label:'快速预览', desc:'极速试听', tags:['CFG2.0','步数5'], text:'韩立站在山门前，望着远处。', mode:'base', cfg_value:2.0, inference_timesteps:5, normalize:false, max_len:1024 },
  { label:'克隆韩立+降噪', desc:'固定韩立音色', tags:['CFG2.0','步数10','降噪'], text:'在下韩立，黄枫谷筑基期修士，见过道友。', mode:'clone', cfg_value:2.0, inference_timesteps:10, normalize:false, denoise:true, reference_audio:'' },
]

function loadPreset(p:any) {
  activePreset.value = p; form.text = p.text; form.mode = p.mode; form.cfg_value = p.cfg_value; form.inference_timesteps = p.inference_timesteps
  form.normalize = p.normalize ?? false; form.denoise = p.denoise ?? false; form.max_len = p.max_len ?? 4096
  if (!p.reference_audio && references.value.length) form.reference_audio = references.value[0].path
  ElMessage.success(`已加载：${p.label}`)
}

async function synthesize() {
  if (!form.text.trim()) { ElMessage.warning('请输入文本'); return }
  if (form.mode === 'clone' && !form.reference_audio) { ElMessage.warning('请选择参考音色'); return }
  generating.value = true; result.value = null
  try {
    const res = await api.post('/tts/voxcpm/synthesize/', {
      text: form.text, cfg_value: form.cfg_value, inference_timesteps: form.inference_timesteps,
      mode: form.mode, normalize: form.normalize, denoise: form.denoise, max_len: form.max_len,
      reference_audio: form.mode === 'clone' ? form.reference_audio : '',
    })
    if (res.success) {
      result.value = { ...res, audio_url: URL.createObjectURL(b64ToBlob(res.audio_base64, 'audio/wav')) }
      ElMessage.success(`完成！${res.duration}s，RTF ${res.rtf}`)
      loadHistory()
    } else { ElMessage.error(res.message || '失败') }
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || e?.message || '请求失败') }
  finally { generating.value = false }
}

async function saveRef(r: any) {
  const label = await ElMessageBox.prompt('参考名称', '保存为参考', { inputValue: '旁白音色', confirmButtonText: '保存', cancelButtonText: '取消' }).then(v=>v.value).catch(()=>null)
  if (!label) return
  try {
    await api.post('/tts/voxcpm/references/', { filename: r.filename, label })
    ElMessage.success('已保存为参考')
    loadRefs()
  } catch (e: any) { ElMessage.error(e?.response?.data?.message || '失败') }
}

async function delRef(r: any) {
  try { await ElMessageBox.confirm(`删除参考「${r.label}」？`); await api.delete(`/tts/voxcpm/references/${r.filename}/`); ElMessage.success('已删除'); loadRefs() } catch { }
}

async function playRef(r: any) { refPlayer.value = { url: `http://localhost:8000/api/tts/voxcpm/outputs/${r.filename}/` } }

async function loadRefs() {
  loadingRefs.value = true
  try { const res = await api.get('/tts/voxcpm/references/'); if (res.success) references.value = res.references }
  catch { }
  finally { loadingRefs.value = false }
}

async function loadHistory() {
  loadingHistory.value = true
  try { const res = await api.get('/tts/voxcpm/outputs/'); if (res.success) historyFiles.value = res.files }
  catch { }
  finally { loadingHistory.value = false }
}

function playHistory(row: any) { historyPlayer.value = { url: `http://localhost:8000/api${row.url}` } }
function showParams(row: any) { selectedParams.value = row.params && Object.keys(row.params).length ? row.params : null }
function b64ToBlob(b64:string, mime:string):Blob {
  const bytes = atob(b64), arr = new Uint8Array(bytes.length)
  for (let i=0;i<bytes.length;i++) arr[i]=bytes.charCodeAt(i)
  return new Blob([arr], {type:mime})
}
onMounted(() => { loadHistory(); loadRefs() })
</script>

<style scoped>
.voxcpm-playground { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 20px; font-weight: bold; }
.hint { font-size: 12px; color: var(--el-text-color-secondary); display: block; margin-top: 2px; }
.preset-info { margin-top: 8px; padding: 8px; background: var(--el-fill-color-light); border-radius: 4px; }
.param-text { font-size: 13px; color: var(--el-text-color-secondary); white-space: pre-wrap; max-height: 80px; overflow-y: auto; }
</style>
