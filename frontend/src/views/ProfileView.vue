<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Edit,
  Key,
  Setting,
  Check,
  Camera,
  Upload,
  Lock,
  Unlock,
} from '@element-plus/icons-vue'
import type { User as UserType } from '@/types'
import { useAuthStore } from '@/stores/auth'
import { apiService } from '@/services/api'

const authStore = useAuthStore()

// 数据状态
const loading = ref(false)
const editMode = ref(false)
const passwordDialogVisible = ref(false)
const avatarDialogVisible = ref(false)

// 用户信息表单
const userForm = ref({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  bio: '',
  phone: '',
  location: '',
})

// 密码修改表单
const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

// 头像上传
const avatarFile = ref<File | null>(null)
const avatarPreview = ref('')
const uploadLoading = ref(false)

// 表单验证规则
const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度在 3 到 30 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  first_name: [
    { max: 30, message: '名字长度不能超过 30 个字符', trigger: 'blur' },
  ],
  last_name: [
    { max: 30, message: '姓氏长度不能超过 30 个字符', trigger: 'blur' },
  ],
  bio: [
    { max: 500, message: '个人简介长度不能超过 500 个字符', trigger: 'blur' },
  ],
  phone: [
    { pattern: /^[\d\-\+\(\)\s]*$/, message: '请输入正确的电话号码', trigger: 'blur' },
  ],
}

const passwordFormRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 计算属性
const user = computed(() => authStore.user)
const fullName = computed(() => {
  const { first_name, last_name } = userForm.value
  return [first_name, last_name].filter(Boolean).join(' ') || userForm.value.username
})

const userStats = computed(() => [
  { label: '注册时间', value: user.value?.date_joined ? formatDate(user.value.date_joined) : '-' },
  { label: '最后登录', value: user.value?.last_login ? formatDate(user.value.last_login) : '-' },
  { label: '邮箱状态', value: user.value?.is_active ? '已激活' : '未激活' },
  { label: '用户类型', value: user.value?.is_staff ? '管理员' : '普通用户' },
])

// 初始化用户信息
const initUserForm = () => {
  if (user.value) {
    userForm.value = {
      username: user.value.username || '',
      email: user.value.email || '',
      first_name: user.value.first_name || '',
      last_name: user.value.last_name || '',
      bio: user.value.bio || '',
      phone: user.value.phone || '',
      location: user.value.location || '',
    }
  }
}

// 获取用户资料
const fetchProfile = async () => {
  loading.value = true
  try {
    await authStore.fetchProfile()
    initUserForm()
  } catch (error) {
    console.error('Failed to fetch profile:', error)
    ElMessage.error('获取用户资料失败')
  } finally {
    loading.value = false
  }
}

// 进入编辑模式
const enterEditMode = () => {
  editMode.value = true
  initUserForm()
}

// 取消编辑
const cancelEdit = () => {
  editMode.value = false
  initUserForm()
}

// 保存用户信息
const saveProfile = async () => {
  loading.value = true
  try {
    await apiService.auth.updateProfile(userForm.value)
    await authStore.fetchProfile()
    editMode.value = false
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    console.error('Failed to update profile:', error)
    ElMessage.error('更新失败')
  } finally {
    loading.value = false
  }
}

// 修改密码
const changePassword = async () => {
  loading.value = true
  try {
    await apiService.auth.changePassword(passwordForm.value)
    passwordDialogVisible.value = false
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: '',
    }
    ElMessage.success('密码修改成功')
  } catch (error) {
    console.error('Failed to change password:', error)
    ElMessage.error('密码修改失败')
  } finally {
    loading.value = false
  }
}

// 处理头像文件选择
const handleAvatarChange = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }

  avatarFile.value = file
  
  // 创建预览
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
  
  avatarDialogVisible.value = true
  return false // 阻止自动上传
}

// 上传头像
const uploadAvatar = async () => {
  if (!avatarFile.value) return
  
  uploadLoading.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', avatarFile.value)
    
    await apiService.auth.uploadAvatar(formData)
    await authStore.fetchProfile()
    
    avatarDialogVisible.value = false
    avatarFile.value = null
    avatarPreview.value = ''
    
    ElMessage.success('头像上传成功')
  } catch (error) {
    console.error('Failed to upload avatar:', error)
    ElMessage.error('头像上传失败')
  } finally {
    uploadLoading.value = false
  }
}

// 删除账户
const deleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除账户吗？此操作不可恢复，所有数据将被永久删除。',
      '确认删除账户',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger',
      }
    )
    
    // 二次确认
    await ElMessageBox.prompt(
      '请输入您的用户名以确认删除操作',
      '确认删除',
      {
        confirmButtonText: '删除账户',
        cancelButtonText: '取消',
        inputPattern: new RegExp(`^${user.value?.username}$`),
        inputErrorMessage: '用户名不匹配',
        inputPlaceholder: user.value?.username,
      }
    )
    
    await apiService.auth.deleteAccount()
    authStore.logout()
    ElMessage.success('账户已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete account:', error)
      ElMessage.error('删除账户失败')
    }
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取头像URL
const getAvatarUrl = (user: UserType | null) => {
  if (user?.avatar) {
    return user.avatar.startsWith('http') ? user.avatar : `http://127.0.0.1:8000${user.avatar}`
  }
  return ''
}

// 组件挂载时获取数据
onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div class="profile-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><User /></el-icon>
          个人资料
        </h1>
        <p class="page-description">管理您的个人信息和账户设置</p>
      </div>
    </div>

    <div v-loading="loading" class="profile-content">
      <el-row :gutter="20">
        <!-- 左侧：基本信息 -->
        <el-col :lg="16" :md="24">
          <el-card shadow="never" class="profile-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon><User /></el-icon>
                  基本信息
                </span>
                <div class="card-actions">
                  <el-button
                    v-if="!editMode"
                    type="primary"
                    :icon="Edit"
                    @click="enterEditMode"
                  >
                    编辑资料
                  </el-button>
                  <div v-else class="edit-actions">
                    <el-button @click="cancelEdit">取消</el-button>
                    <el-button type="primary" @click="saveProfile" :loading="loading">
                      保存
                    </el-button>
                  </div>
                </div>
              </div>
            </template>

            <!-- 头像区域 -->
            <div class="avatar-section">
              <div class="avatar-container">
                <el-avatar
                  :size="100"
                  :src="getAvatarUrl(user)"
                  :icon="User"
                  class="user-avatar"
                />
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleAvatarChange"
                  accept="image/*"
                  class="avatar-upload"
                >
                  <el-button
                    type="primary"
                    :icon="Camera"
                    size="small"
                    circle
                    class="upload-btn"
                  />
                </el-upload>
              </div>
              <div class="avatar-info">
                <h3 class="user-name">{{ fullName }}</h3>
                <p class="user-email">{{ user?.email }}</p>
                <el-tag
                  :type="user?.is_active ? 'success' : 'warning'"
                  size="small"
                >
                  {{ user?.is_active ? '已激活' : '未激活' }}
                </el-tag>
              </div>
            </div>

            <!-- 表单区域 -->
            <div class="form-section">
              <el-form
                ref="userFormRef"
                :model="userForm"
                :rules="userFormRules"
                label-width="100px"
                label-position="left"
                :disabled="!editMode"
              >
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="用户名" prop="username">
                      <el-input
                        v-model="userForm.username"
                        placeholder="请输入用户名"
                        :disabled="true"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="邮箱" prop="email">
                      <el-input
                        v-model="userForm.email"
                        placeholder="请输入邮箱地址"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="名字" prop="first_name">
                      <el-input
                        v-model="userForm.first_name"
                        placeholder="请输入名字"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="姓氏" prop="last_name">
                      <el-input
                        v-model="userForm.last_name"
                        placeholder="请输入姓氏"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-form-item label="电话" prop="phone">
                  <el-input
                    v-model="userForm.phone"
                    placeholder="请输入电话号码"
                  />
                </el-form-item>
                
                <el-form-item label="位置" prop="location">
                  <el-input
                    v-model="userForm.location"
                    placeholder="请输入所在位置"
                  />
                </el-form-item>
                
                <el-form-item label="个人简介" prop="bio">
                  <el-input
                    v-model="userForm.bio"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入个人简介"
                    maxlength="500"
                    show-word-limit
                  />
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：账户信息和操作 -->
        <el-col :lg="8" :md="24">
          <!-- 账户统计 -->
          <el-card shadow="never" class="stats-card">
            <template #header>
              <span class="card-title">
                <el-icon><Setting /></el-icon>
                账户信息
              </span>
            </template>
            
            <div class="stats-list">
              <div
                v-for="stat in userStats"
                :key="stat.label"
                class="stat-item"
              >
                <span class="stat-label">{{ stat.label }}</span>
                <span class="stat-value">{{ stat.value }}</span>
              </div>
            </div>
          </el-card>

          <!-- 安全操作 -->
          <el-card shadow="never" class="security-card">
            <template #header>
              <span class="card-title">
                <el-icon><Lock /></el-icon>
                安全设置
              </span>
            </template>
            
            <div class="security-actions">
              <el-button
                type="warning"
                :icon="Key"
                @click="passwordDialogVisible = true"
                block
              >
                修改密码
              </el-button>
              
              <el-divider />
              
              <el-button
                type="danger"
                plain
                @click="deleteAccount"
                block
              >
                删除账户
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordFormRules"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="当前密码" prop="current_password">
          <el-input
            v-model="passwordForm.current_password"
            type="password"
            placeholder="请输入当前密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="changePassword" :loading="loading">
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 头像上传对话框 -->
    <el-dialog
      v-model="avatarDialogVisible"
      title="上传头像"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="avatar-upload-content">
        <div class="avatar-preview">
          <el-avatar
            :size="150"
            :src="avatarPreview"
            :icon="User"
          />
        </div>
        <p class="upload-tips">
          支持 JPG、PNG 格式，文件大小不超过 2MB
        </p>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="avatarDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :icon="Upload"
            @click="uploadAvatar"
            :loading="uploadLoading"
          >
            上传头像
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.profile-container {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.header-content {
  text-align: center;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.page-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.profile-content {
  min-height: 600px;
}

.profile-card,
.stats-card,
.security-card {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.edit-actions {
  display: flex;
  gap: 8px;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.avatar-container {
  position: relative;
  display: inline-block;
}

.user-avatar {
  border: 3px solid #e4e7ed;
}

.avatar-upload {
  position: absolute;
  bottom: 0;
  right: 0;
}

.upload-btn {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-info {
  flex: 1;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.user-email {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0 0 12px 0;
}

.form-section {
  padding-top: 0;
}

.stats-list {
  padding: 0;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
}

.security-actions {
  padding: 0;
}

.security-actions .el-button {
  margin-bottom: 12px;
}

.security-actions .el-button:last-child {
  margin-bottom: 0;
}

.avatar-upload-content {
  text-align: center;
  padding: 20px 0;
}

.avatar-preview {
  margin-bottom: 20px;
}

.upload-tips {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .avatar-section {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .card-actions {
    justify-content: center;
  }
  
  .edit-actions {
    justify-content: center;
  }
}
</style>