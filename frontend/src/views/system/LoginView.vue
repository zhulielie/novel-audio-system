<template>
  <div class="login-container">
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-logo">
          <el-icon size="32" color="#ffffff"><Reading /></el-icon>
        </div>
        <h1 class="brand-title">智能小说管理系统</h1>
        <p class="brand-subtitle">小说爬取 · 章节管理 · 音频合成 · 工作流编排</p>
        
        <div class="brand-features">
          <div class="feature-item" v-for="(feature, index) in features" :key="index">
            <div class="feature-icon">
              <el-icon size="18" color="#6366f1"><component :is="feature.icon" /></el-icon>
            </div>
            <div class="feature-text">
              <div class="feature-title">{{ feature.title }}</div>
              <div class="feature-desc">{{ feature.desc }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="brand-pattern">
        <div class="pattern-circle c1"></div>
        <div class="pattern-circle c2"></div>
        <div class="pattern-circle c3"></div>
      </div>
    </div>
    
    <div class="login-form-wrapper">
      <div class="login-form">
        <div class="form-header">
          <h2 class="form-title">欢迎回来</h2>
          <p class="form-subtitle">请登录您的管理员账号</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form-content"
          autocomplete="on"
        >
          <el-form-item prop="username">
            <div class="input-label">用户名</div>
            <el-input
              ref="username"
              v-model="loginForm.username"
              placeholder="请输入用户名"
              name="username"
              type="text"
              tabindex="1"
              autocomplete="on"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <div class="input-label">
              <span>密码</span>
              <a href="#" class="forgot-link" @click.prevent>忘记密码？</a>
            </div>
            <el-input
              :key="passwordType"
              ref="password"
              v-model="loginForm.password"
              :type="passwordType"
              placeholder="请输入密码"
              name="password"
              tabindex="2"
              autocomplete="on"
              size="large"
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            >
              <template #suffix>
                <el-icon class="password-toggle" @click="showPwd">
                  <component :is="passwordType === 'password' ? 'View' : 'Hide'" />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button
            :loading="loading"
            type="primary"
            size="large"
            class="login-button"
            @click.prevent="handleLogin"
          >
            登录
          </el-button>
        </el-form>

        <div class="form-tips">
          <span>默认账号: admin</span>
          <span class="dot">·</span>
          <span>默认密码: admin</span>
        </div>
      </div>
      
      <div class="login-footer">
        © 2026 智能小说管理系统 · All rights reserved
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, View, Hide, Reading, Connection, Headset, MagicStick } from '@element-plus/icons-vue'
import { systemApi } from '@/services/systemApi'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  username: 'admin',
  password: 'admin'
})

const loginRules = {
  username: [{ required: true, trigger: 'blur', message: '请输入用户名' }],
  password: [{ required: true, trigger: 'blur', message: '请输入密码' }]
}

const passwordType = ref('password')
const loading = ref(false)
const loginFormRef = ref()
const username = ref()
const password = ref()

const features = [
  { icon: 'Connection', title: '智能爬虫', desc: '支持多站点小说内容自动获取' },
  { icon: 'Reading', title: '小说管理', desc: '统一的章节与元数据管理' },
  { icon: 'Headset', title: '语音合成', desc: '高质量 TTS 音频一键生成' },
  { icon: 'MagicStick', title: 'AI 工作流', desc: '脚本生成与音频合成自动化' }
]

const showPwd = () => {
  passwordType.value = passwordType.value === 'password' ? '' : 'password'
  nextTick(() => {
    password.value.focus()
  })
}

const handleLogin = () => {
  loginFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        const response = await systemApi.login(loginForm)
        userStore.setToken(response.access_token, response.refresh_token)
        userStore.setUserInfo(response.user_info)
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } catch (error: any) {
        console.error('登录失败:', error)
        ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  width: 100%;
  display: flex;
  background: var(--bg-body);
}

.login-brand {
  flex: 1;
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}

.brand-pattern {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.pattern-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.15);
  filter: blur(60px);
}

.pattern-circle.c1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
}

.pattern-circle.c2 {
  width: 300px;
  height: 300px;
  bottom: 10%;
  left: -50px;
  background: rgba(139, 92, 246, 0.12);
}

.pattern-circle.c3 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  right: 20%;
  background: rgba(59, 130, 246, 0.1);
}

.brand-content {
  position: relative;
  z-index: 1;
  max-width: 480px;
}

.brand-logo {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-500) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
  box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
}

.brand-title {
  font-size: 42px;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 12px 0;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.brand-subtitle {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.65);
  margin: 0 0 48px 0;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(4px);
}

.feature-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 2px;
}

.feature-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.login-form-wrapper {
  width: 520px;
  min-width: 520px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 48px;
  position: relative;
}

.login-form {
  width: 100%;
  max-width: 400px;
}

.form-header {
  margin-bottom: 32px;
}

.form-title {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
}

.form-subtitle {
  font-size: 15px;
  color: var(--text-muted);
  margin: 0;
}

.input-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.forgot-link {
  color: var(--primary-600);
  font-weight: 500;
  font-size: 12px;
}

.forgot-link:hover {
  color: var(--primary-700);
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
  padding: 4px 12px;
}

:deep(.el-input__inner) {
  height: 44px;
  font-size: 15px;
}

.password-toggle {
  cursor: pointer;
  color: var(--text-muted);
  transition: color 0.2s;
}

.password-toggle:hover {
  color: var(--primary-600);
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
  border-radius: var(--radius-md);
}

.form-tips {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.form-tips .dot {
  color: var(--border-color);
}

.login-footer {
  position: absolute;
  bottom: 24px;
  font-size: 12px;
  color: var(--text-muted);
}

@media (max-width: 1024px) {
  .login-brand {
    display: none;
  }
  
  .login-form-wrapper {
    width: 100%;
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .login-form-wrapper {
    padding: 32px 24px;
  }
  
  .form-title {
    font-size: 24px;
  }
}
</style>
