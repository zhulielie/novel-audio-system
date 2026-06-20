<template>
  <div class="login-container">
    <div class="login-card">
      <!-- 顶部品牌区域 -->
      <div class="brand-header">
        <div class="logo">
          <el-icon size="40" color="#409eff"><Document /></el-icon>
        </div>
        <h1 class="brand-title">小说音频系统</h1>
        <p class="brand-subtitle">智能音频内容生成平台</p>
      </div>

      <!-- 登录提示信息 -->
      <div class="login-tip">
        <el-alert
          title="测试账号信息"
          :closable="false"
          type="info"
          show-icon
          class="login-alert"
        >
          <div class="test-accounts">
            <div class="account-item">
              <span class="label">普通用户:</span>
              <code>zhulielie / midnet88</code>
            </div>
            <div class="account-item">
              <span class="label">管理员:</span>
              <code>admin / admin123456</code>
            </div>
          </div>
        </el-alert>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            clearable
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            clearable
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <div class="form-options">
          <el-checkbox v-model="loginForm.remember">
            记住我
          </el-checkbox>
          <el-link type="primary" @click="handleForgotPassword">
            忘记密码？
          </el-link>
        </div>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '立即登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 功能特性 -->
      <div class="features">
        <div class="feature-item">
          <el-icon size="20" color="#67c23a"><Microphone /></el-icon>
          <span>高质量音频生成</span>
        </div>
        <div class="feature-item">
          <el-icon size="20" color="#e6a23c"><Cpu /></el-icon>
          <span>AI智能处理</span>
        </div>
        <div class="feature-item">
          <el-icon size="20" color="#f56c6c"><Setting /></el-icon>
          <span>项目管理</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, Document, Microphone, Cpu, Setting } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { LoginForm } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 加载状态
const loading = ref(false)

// 登录表单数据
const loginForm = reactive<LoginForm>({
  username: '',
  password: '',
  remember: false,
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    // 验证表单
    await loginFormRef.value.validate()

    loading.value = true

    // 调用登录API
    const result = await authStore.login({
      username: loginForm.username,
      password: loginForm.password,
    })

    if (result.success) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(result.message || '登录失败')
    }
  } catch (error: any) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else if (typeof error === 'string') {
      ElMessage.error(error)
    } else {
      ElMessage.error('登录失败，请检查用户名和密码')
    }
  } finally {
    loading.value = false
  }
}

// 处理忘记密码
const handleForgotPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh !important;
  width: 100vw !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 20px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  margin: 0 !important;
  box-sizing: border-box !important;
}

.login-card {
  width: 100%;
  max-width: 480px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  padding: 48px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.login-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.2);
}

.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a, #e6a23c, #f56c6c);
}

.login-tip {
  margin-bottom: 24px;
}

.login-alert {
  border-radius: 8px;
  border: 1px solid #e1e5e9;
}

.login-alert .el-alert__content {
  padding: 16px 20px;
}

.brand-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  margin-bottom: 20px;
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: scale(1.1);
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: 16px;
  color: #909399;
  margin: 0;
  font-weight: 400;
}

.login-wrapper {
  width: 100%;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 15px;
  color: #606266;
  margin: 0;
}

.login-form {
  margin-bottom: 28px;
}

.login-form .el-form-item {
  margin-bottom: 20px;
}

.login-form .el-input {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.login-form .el-input:hover {
  border-color: #409eff;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.features {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 0;
  padding: 24px 0;
  border-top: 1px solid #f0f0f0;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-item:hover {
  color: #409eff;
  transform: translateY(-2px);
}

.test-accounts {
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.account-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.account-item:hover {
  background: #f0f2f5;
}

.account-item .label {
  font-weight: 500;
  color: #606266;
}

.account-item code {
  color: #409eff;
  background: #ecf5ff;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    padding: 10px;
  }

  .login-card {
    padding: 30px 20px;
    border-radius: 15px;
  }

  .brand-title {
    font-size: 20px;
  }

  .features {
    flex-direction: column;
    gap: 15px;
    padding: 15px 0;
  }

  .feature-item {
    flex-direction: row;
    justify-content: center;
    gap: 10px;
  }

  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .account-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border: none;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.3);
}

.test-accounts {
  margin-top: 40px;
}

.account-list {
  margin-top: 20px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 13px;
}

.account-item .label {
  font-weight: 500;
  color: #495057;
}

.account-item code {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #dc3545;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-left {
    padding: 40px 40px;
  }

  .brand-title {
    font-size: 32px;
  }

  .brand-subtitle {
    font-size: 16px;
  }

  .login-right {
    padding: 30px 40px;
  }
}

@media (max-width: 768px) {
  .login-page {
    flex-direction: column;
  }

  .login-left {
    flex: none;
    padding: 40px 20px;
    min-height: 300px;
  }

  .brand-title {
    font-size: 28px;
  }

  .features {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
  }

  .feature-item {
    flex: 1;
    min-width: 200px;
  }

  .login-right {
    flex: 1;
    padding: 40px 20px;
  }

  .login-wrapper {
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .login-left {
    padding: 30px 20px;
    min-height: 250px;
  }

  .brand-title {
    font-size: 24px;
  }

  .brand-subtitle {
    font-size: 14px;
  }

  .features {
    gap: 12px;
  }

  .feature-item {
    min-width: 150px;
    font-size: 14px;
  }

  .login-right {
    padding: 30px 20px;
  }

  .login-header h2 {
    font-size: 24px;
  }

  .login-header p {
    font-size: 14px;
  }

  .form-options {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .account-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>