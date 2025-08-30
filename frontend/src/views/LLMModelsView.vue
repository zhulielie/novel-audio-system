<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Search,
  Cpu,
  Connection,
  Key,
  Setting,
  Check,
  Close,
  Refresh,
} from '@element-plus/icons-vue'
import type { LLMModel, LLMModelForm } from '@/types'
import { apiService } from '@/services/api'

// 数据状态
const models = ref<LLMModel[]>([])
const loading = ref(false)
const searchText = ref('')
const dialogVisible = ref(false)
const testDialogVisible = ref(false)
const editingModel = ref<LLMModel | null>(null)
const testingModel = ref<LLMModel | null>(null)
const testResult = ref('')
const testLoading = ref(false)

// 表单数据
const modelForm = ref<LLMModelForm>({
  name: '',
  provider: '',
  model_id: '',
  model_name: '',
  api_key: '',
  api_base: '',
  max_tokens: 2000,
  temperature: 0.7,
  is_active: true,
  config: {},
})

// 测试表单
const testForm = ref({
  prompt: '你好，请介绍一下你自己。',
  max_tokens: 100,
  temperature: 0.7,
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度在 1 到 100 个字符', trigger: 'blur' },
  ],
  provider: [
    { required: true, message: '请选择提供商', trigger: 'change' },
  ],
  model_name: [
    { required: true, message: '请输入模型标识', trigger: 'blur' },
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' },
  ],
  max_tokens: [
    { required: true, message: '请输入最大Token数', trigger: 'blur' },
    { type: 'number', min: 1, max: 32000, message: 'Token数范围在 1 到 32000', trigger: 'blur' },
  ],
  temperature: [
    { required: true, message: '请输入温度值', trigger: 'blur' },
    { type: 'number', min: 0, max: 2, message: '温度值范围在 0 到 2', trigger: 'blur' },
  ],
}

// 提供商选项
const providerOptions = [
  { label: 'OpenAI', value: 'openai', icon: '🤖' },
  { label: 'Anthropic', value: 'anthropic', icon: '🧠' },
  { label: '阿里云', value: 'aliyun', icon: '☁️' },
  { label: '百度', value: 'baidu', icon: '🔍' },
  { label: '腾讯', value: 'tencent', icon: '🐧' },
  { label: '智谱AI', value: 'zhipu', icon: '⚡' },
  { label: '其他', value: 'other', icon: '🔧' },
]

// 常用模型选项
const modelOptions: Record<string, string[]> = {
  openai: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'],
  anthropic: ['claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus'],
  aliyun: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
  baidu: ['ernie-bot', 'ernie-bot-turbo', 'ernie-bot-4'],
  tencent: ['hunyuan-lite', 'hunyuan-standard', 'hunyuan-pro'],
  zhipu: ['glm-3-turbo', 'glm-4', 'glm-4v'],
  other: [],
}

// 计算属性
const filteredModels = computed(() => {
  if (!searchText.value) return models.value
  return models.value.filter(model => 
    model.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
    model.provider.toLowerCase().includes(searchText.value.toLowerCase()) ||
    model.model_name?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const currentModelOptions = computed(() => {
  return modelOptions[modelForm.value.provider] || []
})

// 获取模型列表
const fetchModels = async () => {
  loading.value = true
  try {
    const response = await apiService.llmModels.list()
    const data = (response as any)?.results || (response as any)?.data?.results || []
    models.value = Array.isArray(data) ? data.filter(model => model && model.id) : []
  } catch (error) {
    console.error('Failed to fetch models:', error)
    ElMessage.error('获取模型列表失败')
    models.value = []
  } finally {
    loading.value = false
  }
}

// 打开添加对话框
const openAddDialog = () => {
  editingModel.value = null
  modelForm.value = {
    name: '',
    provider: '',
    model_id: '',
    model_name: '',
    api_key: '',
    api_base: '',
    max_tokens: 2000,
    temperature: 0.7,
    is_active: true,
    is_default_assistant: false,
    config: {},
  }
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (model: LLMModel) => {
  editingModel.value = model
  modelForm.value = {
    name: model.name,
    provider: model.provider,
    model_id: model.model_id,
    model_name: model.model_name,
    api_key: model.api_key,
    api_base: model.api_base || '',
    max_tokens: model.max_tokens,
    temperature: model.temperature,
    is_active: model.is_active,
    is_default_assistant: model.is_default_assistant || false,
    config: model.config || {},
  }
  dialogVisible.value = true
}

// 保存模型
const saveModel = async () => {
  try {
    if (editingModel.value) {
      // 编辑模式
      await apiService.llmModels.update(editingModel.value.id, modelForm.value)
      ElMessage.success('模型更新成功')
    } else {
      // 添加模式
      await apiService.llmModels.create(modelForm.value)
      ElMessage.success('模型创建成功')
    }
    dialogVisible.value = false
    await fetchModels()
  } catch (error) {
    console.error('Failed to save model:', error)
    ElMessage.error('保存失败')
  }
}

// 删除模型
const deleteModel = async (model: LLMModel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型「${model.name}」吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiService.llmModels.delete(model.id)
    ElMessage.success('删除成功')
    await fetchModels()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete model:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 切换模型状态
const toggleModelStatus = async (model: LLMModel) => {
  try {
    await apiService.llmModels.update(model.id, {
      ...model,
      is_active: !model.is_active,
    })
    model.is_active = !model.is_active
    ElMessage.success(`模型已${model.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('Failed to toggle model status:', error)
    ElMessage.error('状态切换失败')
  }
}

// 设置默认管家
const setDefaultAssistant = async (model: LLMModel) => {
  try {
    await apiService.llmModels.setDefaultAssistant(model.id)
    ElMessage.success(`已将 ${model.name} 设置为默认管家`)
    await fetchModels()
  } catch (error) {
    console.error('Failed to set default assistant:', error)
    let errorMessage = '设置默认管家失败'
    if ((error as any)?.response?.data?.message) {
      errorMessage = (error as any).response.data.message
    }
    ElMessage.error(errorMessage)
  }
}

// 取消默认管家
const removeDefaultAssistant = async (model: LLMModel) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消 ${model.name} 的默认管家身份吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await apiService.llmModels.removeDefaultAssistant(model.id)
    ElMessage.success(`已取消 ${model.name} 的默认管家身份`)
    await fetchModels()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to remove default assistant:', error)
      let errorMessage = '取消默认管家失败'
      if ((error as any)?.response?.data?.message) {
        errorMessage = (error as any).response.data.message
      }
      ElMessage.error(errorMessage)
    }
  }
}

// 测试模型
const openTestDialog = (model: LLMModel) => {
  testingModel.value = model
  testForm.value = {
    prompt: '你好，请介绍一下你自己。',
    max_tokens: 100,
    temperature: 0.7,
  }
  testResult.value = ''
  testDialogVisible.value = true
}

const testModel = async () => {
  if (!testingModel.value) return
  
  testLoading.value = true
  testResult.value = ''
  
  try {
    const response = await apiService.llmModels.test(testingModel.value.id, {
      prompt: testForm.value.prompt,
      max_tokens: testForm.value.max_tokens,
      temperature: testForm.value.temperature,
    })
    testResult.value = response.data?.response || response.data || '测试成功，但未返回响应内容'
    ElMessage.success('模型测试成功')
  } catch (error) {
    console.error('Failed to test model:', error)

    // 处理后端返回的错误响应
    let errorMessage = '未知错误'
    if ((error as any)?.response?.data?.message) {
      errorMessage = (error as any).response.data.message
    } else if ((error as any)?.response?.data?.error) {
      errorMessage = (error as any).response.data.error
    } else if ((error as any)?.message) {
      errorMessage = (error as any).message
    }

    testResult.value = `测试失败: ${errorMessage}`
    ElMessage.error('模型测试失败')
  } finally {
    testLoading.value = false
  }
}

// 获取提供商图标
const getProviderIcon = (provider: string) => {
  const option = providerOptions.find(opt => opt.value === provider)
  return option?.icon || '🔧'
}

// 获取提供商名称
const getProviderName = (provider: string) => {
  const option = providerOptions.find(opt => opt.value === provider)
  return option?.label || provider
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 隐藏API密钥
const maskApiKey = (apiKey: string) => {
  if (!apiKey || apiKey.length <= 8) return apiKey
  return apiKey.substring(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.substring(apiKey.length - 4)
}

// 组件挂载时获取数据
onMounted(() => {
  fetchModels()
})
</script>

<template>
  <div class="llm-models-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Cpu /></el-icon>
          LLM模型
        </h1>
        <p class="page-description">配置和管理大语言模型，用于脚本生成</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAddDialog">
        添加模型
      </el-button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-card shadow="never">
        <el-row :gutter="20" align="middle">
          <el-col :span="8">
            <el-input
              v-model="searchText"
              placeholder="搜索模型名称、提供商或模型标识"
              :prefix-icon="Search"
              clearable
            />
          </el-col>
          <el-col :span="4">
            <el-button @click="fetchModels" :loading="loading">
              刷新
            </el-button>
          </el-col>
        </el-row>
      </el-card>
    </div>

    <!-- 模型列表 -->
    <div class="models-list">
      <el-card shadow="never">
        <div v-loading="loading" class="list-content">
          <div v-if="filteredModels.length === 0" class="empty-state">
            <el-empty description="暂无LLM模型">
              <el-button type="primary" :icon="Plus" @click="openAddDialog">
                添加第一个模型
              </el-button>
            </el-empty>
          </div>
          
          <div v-else class="models-grid">
            <div
              v-for="model in filteredModels"
              :key="model.id"
              class="model-card"
              :class="{ 'model-inactive': !model.is_active }"
            >
              <div class="model-header">
                <div class="model-info">
                  <div class="model-provider">
                    <span class="provider-icon">{{ getProviderIcon(model.provider) }}</span>
                    <span class="provider-name">{{ getProviderName(model.provider) }}</span>
                    <el-tag
                      v-if="model.is_default_assistant"
                      type="success"
                      size="small"
                      class="default-assistant-tag"
                    >
                      🤖 默认管家
                    </el-tag>
                  </div>
                  <div class="model-name">{{ model.name }}</div>
                </div>
                <div class="model-status">
                  <el-switch
                    v-model="model.is_active"
                    @change="toggleModelStatus(model)"
                    :active-icon="Check"
                    :inactive-icon="Close"
                  />
                </div>
              </div>
              
              <div class="model-details">
                <div class="detail-item">
                  <span class="detail-label">模型标识:</span>
                  <span class="detail-value">{{ model.model_name }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">API密钥:</span>
                  <span class="detail-value api-key">{{ maskApiKey(model.api_key || '') }}</span>
                </div>
                <div v-if="model.api_base" class="detail-item">
                  <span class="detail-label">API地址:</span>
                  <span class="detail-value">{{ model.api_base }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">最大Token:</span>
                  <span class="detail-value">{{ model.max_tokens }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">温度值:</span>
                  <span class="detail-value">{{ model.temperature }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">创建时间:</span>
                  <span class="detail-value">{{ formatDate(model.created_at) }}</span>
                </div>
              </div>
              
              <div class="model-actions">
                <el-button
                  type="success"
                  :icon="Connection"
                  size="small"
                  @click="openTestDialog(model)"
                  :disabled="!model.is_active"
                >
                  测试
                </el-button>
                <el-button
                  v-if="!model.is_default_assistant && model.is_active"
                  type="warning"
                  :icon="Cpu"
                  size="small"
                  @click="setDefaultAssistant(model)"
                >
                  设置管家
                </el-button>
                <el-button
                  v-if="model.is_default_assistant"
                  type="info"
                  :icon="Cpu"
                  size="small"
                  @click="removeDefaultAssistant(model)"
                >
                  取消管家
                </el-button>
                <el-button
                  type="primary"
                  :icon="Edit"
                  size="small"
                  @click="openEditDialog(model)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  :icon="Delete"
                  size="small"
                  @click="deleteModel(model)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingModel ? '编辑LLM模型' : '添加LLM模型'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="modelForm"
        :rules="formRules"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="模型名称" prop="name">
          <el-input
            v-model="modelForm.name"
            placeholder="请输入模型名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="提供商" prop="provider">
          <el-select
            v-model="modelForm.provider"
            placeholder="请选择提供商"
            style="width: 100%"
            @change="modelForm.model_name = ''"
          >
            <el-option
              v-for="option in providerOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            >
              <span>{{ option.icon }} {{ option.label }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型标识" prop="model_name">
          <el-select
            v-if="currentModelOptions.length > 0"
            v-model="modelForm.model_name"
            placeholder="请选择或输入模型标识"
            style="width: 100%"
            filterable
            allow-create
          >
            <el-option
              v-for="model in currentModelOptions"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          <el-input
            v-else
            v-model="modelForm.model_name"
            placeholder="请输入模型标识"
          />
        </el-form-item>
        
        <el-form-item label="API密钥" prop="api_key">
          <el-input
            v-model="modelForm.api_key"
            type="password"
            placeholder="请输入API密钥"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="API地址">
          <el-input
            v-model="modelForm.api_base"
            placeholder="请输入API基础地址（可选）"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最大Token" prop="max_tokens">
              <el-input-number
                v-model="modelForm.max_tokens"
                :min="1"
                :max="32000"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度值" prop="temperature">
              <el-input-number
                v-model="modelForm.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="启用状态">
          <el-switch
            v-model="modelForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>

        <el-form-item label="默认管家">
          <el-switch
            v-model="modelForm.is_default_assistant"
            active-text="是"
            inactive-text="否"
            :disabled="!modelForm.is_active"
          />
          <div class="form-item-tip">
            <el-text type="info" size="small">
              只能将启用的模型设置为默认管家，且系统中只能有一个默认管家
            </el-text>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveModel">
            {{ editingModel ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试LLM模型"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="test-content">
        <div class="test-info">
          <h4>测试模型: {{ testingModel?.name }}</h4>
          <p>提供商: {{ getProviderName(testingModel?.provider || '') }}</p>
          <p>模型标识: {{ testingModel?.model_name }}</p>
        </div>
        
        <el-form label-width="100px">
          <el-form-item label="测试提示词">
            <el-input
              v-model="testForm.prompt"
              type="textarea"
              :rows="4"
              placeholder="请输入测试提示词"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="最大Token">
                <el-input-number
                  v-model="testForm.max_tokens"
                  :min="1"
                  :max="2000"
                  :step="10"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="温度值">
                <el-input-number
                  v-model="testForm.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  :precision="1"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        
        <div class="test-actions">
          <el-button
            type="primary"
            :icon="Connection"
            @click="testModel"
            :loading="testLoading"
          >
            开始测试
          </el-button>
        </div>
        
        <div v-if="testResult" class="test-result">
          <h4>测试结果:</h4>
          <div class="result-content">
            {{ testResult }}
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="testDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.llm-models-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f56c6c 0%, #f89898 100%);
  border-radius: 8px;
  color: white;
}

.header-content {
  flex: 1;
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

.page-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.search-section {
  margin-bottom: 20px;
}

.search-section .el-card {
  border: 1px solid #e4e7ed;
}

.models-list .el-card {
  border: 1px solid #e4e7ed;
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

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.model-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
}

.model-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.model-card.model-inactive {
  opacity: 0.6;
  background: #f8f9fa;
}

/* 默认管家样式 */
.default-assistant-tag {
  margin-left: 8px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.form-item-tip {
  margin-top: 8px;
}

.form-item-tip .el-text {
  font-size: 12px;
  line-height: 1.4;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.model-info {
  flex: 1;
}

.model-provider {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.provider-icon {
  font-size: 20px;
}

.provider-name {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.model-name {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.model-status {
  display: flex;
  align-items: center;
}

.model-details {
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-label {
  color: #7f8c8d;
  font-weight: 500;
  min-width: 80px;
}

.detail-value {
  color: #2c3e50;
  flex: 1;
  text-align: right;
}

.detail-value.api-key {
  font-family: monospace;
  font-size: 12px;
}

.model-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.test-content {
  padding: 0;
}

.test-info {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.test-info h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.test-info p {
  margin: 4px 0;
  color: #7f8c8d;
  font-size: 14px;
}

.test-actions {
  margin: 20px 0;
  text-align: center;
}

.test-result {
  margin-top: 20px;
}

.test-result h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
}

.result-content {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .models-grid {
    grid-template-columns: 1fr;
  }
  
  .search-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section .el-col {
    width: 100%;
  }
  
  .model-actions {
    flex-wrap: wrap;
  }
  
  .detail-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .detail-value {
    text-align: left;
  }
}
</style>