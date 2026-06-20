<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="sidebar-container">
      <div class="logo-container">
        <div class="logo">
          <el-icon size="20" color="#ffffff"><Reading /></el-icon>
        </div>
        <h2 v-show="!isCollapse" class="logo-title">小说管理系统</h2>
      </div>
      
      <el-scrollbar class="sidebar-scrollbar">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="false"
          :collapse-transition="false"
          mode="vertical"
          background-color="#ffffff"
          text-color="#475569"
          active-text-color="#6366f1"
          router
        >
          <sidebar-item
            v-for="route in menuRoutes"
            :key="route.path"
            :item="route"
            :base-path="route.path"
          />
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航栏 -->
      <el-header class="navbar">
        <div class="navbar-left">
          <hamburger
            :is-active="isCollapse"
            class="hamburger-container"
            @toggleClick="toggleSidebar"
          />
          <breadcrumb class="breadcrumb-container" />
        </div>
        
        <div class="navbar-right">
          <el-tooltip content="全屏" effect="dark" placement="bottom">
            <screenfull class="right-menu-item hover-effect" />
          </el-tooltip>
          
          <el-tooltip content="布局大小" effect="dark" placement="bottom">
            <size-select class="right-menu-item hover-effect" />
          </el-tooltip>
          
          <!-- 用户下拉菜单 -->
          <el-dropdown class="avatar-container right-menu-item hover-effect" trigger="click">
            <div class="avatar-wrapper">
              <img :src="userInfo.avatar || defaultAvatar" class="user-avatar" />
              <span class="user-name">{{ userInfo.nickname || userInfo.username }}</span>
              <el-icon class="el-icon-caret-bottom">
                <CaretBottom />
              </el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <router-link to="/profile">
                  <el-dropdown-item>个人中心</el-dropdown-item>
                </router-link>
                <el-dropdown-item @click="showSettings = true">
                  <span>布局设置</span>
                </el-dropdown-item>
                <el-dropdown-item divided @click="logout">
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 标签页导航 -->
      <tags-view v-if="needTagsView" />

      <!-- 主要内容 -->
      <el-main class="app-main">
        <transition name="fade-transform" mode="out-in">
          <router-view :key="key" />
        </transition>
      </el-main>
    </el-container>

    <!-- 设置面板 -->
    <settings
      v-model="showSettings"
      @change="handleSettingsChange"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CaretBottom, Reading } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'
import SidebarItem from './components/Sidebar/SidebarItem.vue'
import Hamburger from './components/Hamburger/index.vue'
import Breadcrumb from './components/Breadcrumb/index.vue'
import TagsView from './components/TagsView/index.vue'
import Screenfull from './components/Screenfull/index.vue'
import SizeSelect from './components/SizeSelect/index.vue'
import Settings from './components/Settings/index.vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const permissionStore = usePermissionStore()

// 响应式数据
const showSettings = ref(false)
const defaultAvatar = '/default-avatar.png'

// 计算属性
const isCollapse = computed(() => !appStore.sidebar.opened)
const sidebarWidth = computed(() => appStore.sidebar.opened ? '210px' : '64px')
const needTagsView = computed(() => appStore.tagsView)
const userInfo = computed(() => userStore.userInfo)
const menuRoutes = computed(() => permissionStore.routes)

const activeMenu = computed(() => {
  const { meta, path } = route
  if (meta?.activeMenu) {
    return meta.activeMenu
  }
  return path
})

const key = computed(() => route.path)

// 方法
const toggleSidebar = () => {
  appStore.toggleSidebar()
}

const handleSettingsChange = (settings: any) => {
  // 处理设置变更
  console.log('Settings changed:', settings)
}

const logout = async () => {
  try {
    await ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await userStore.logout()
    router.push('/login')
    ElMessage.success('退出成功')
  } catch (error) {
    // 用户取消
  }
}

// 监听路由变化
watch(
  () => route.path,
  () => {
    if (appStore.device === 'mobile' && appStore.sidebar.opened) {
      appStore.closeSidebar(false)
    }
  }
)
</script>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;
  display: flex;
  background: var(--bg-body);
}

.sidebar-container {
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
  z-index: 10;
  
  .logo-container {
    display: flex;
    align-items: center;
    padding: 18px 20px;
    height: 64px;
    border-bottom: 1px solid var(--border-color);
    
    .logo {
      width: 32px;
      height: 32px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-500) 100%);
      padding: 6px;
    }
    
    .logo-title {
      margin-left: 12px;
      font-size: 17px;
      font-weight: 700;
      color: var(--text-primary);
      white-space: nowrap;
      letter-spacing: -0.02em;
    }
  }
  
  .sidebar-scrollbar {
    height: calc(100vh - 64px);
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.navbar {
  height: 64px;
  overflow: hidden;
  position: relative;
  background: var(--bg-navbar);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  
  .navbar-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .hamburger-container {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all 0.2s ease;
      -webkit-tap-highlight-color: transparent;
      color: var(--text-secondary);
      
      &:hover {
        background: var(--slate-100);
        color: var(--primary-600);
      }
    }
    
    .breadcrumb-container {
      font-size: 14px;
    }
  }
  
  .navbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .right-menu-item {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 38px;
      height: 38px;
      font-size: 18px;
      color: var(--text-secondary);
      border-radius: var(--radius-md);
      transition: all 0.2s ease;
      
      &.hover-effect {
        cursor: pointer;
        
        &:hover {
          background: var(--slate-100);
          color: var(--primary-600);
        }
      }
    }
    
    .avatar-container {
      margin-left: 8px;
      
      .avatar-wrapper {
        position: relative;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 12px 6px 6px;
        border-radius: var(--radius-full);
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        
        &:hover {
          background: var(--slate-100);
          border-color: var(--border-color);
        }
        
        .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          object-fit: cover;
          border: 2px solid var(--bg-card);
          box-shadow: var(--shadow-xs);
        }
        
        .user-name {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-secondary);
        }
        
        .el-icon-caret-bottom {
          font-size: 12px;
          color: var(--text-muted);
        }
      }
    }
  }
}

.app-main {
  min-height: calc(100vh - 64px);
  width: 100%;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px;
  background: var(--bg-body);
}

// 过渡动画
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
