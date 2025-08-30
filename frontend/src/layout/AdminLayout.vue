<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="sidebar-container">
      <div class="logo-container">
        <img src="/logo.svg" alt="Logo" class="logo" />
        <h2 v-show="!isCollapse" class="logo-title">小说管理系统</h2>
      </div>
      
      <el-scrollbar class="sidebar-scrollbar">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="false"
          :collapse-transition="false"
          mode="vertical"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
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
import { CaretBottom } from '@element-plus/icons-vue'
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
}

.sidebar-container {
  background-color: #304156;
  transition: width 0.28s;
  
  .logo-container {
    display: flex;
    align-items: center;
    padding: 20px;
    background-color: #2b2f3a;
    
    .logo {
      width: 32px;
      height: 32px;
    }
    
    .logo-title {
      margin-left: 12px;
      font-size: 18px;
      font-weight: bold;
      color: #fff;
      white-space: nowrap;
    }
  }
  
  .sidebar-scrollbar {
    height: calc(100vh - 72px);
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.navbar {
  height: 50px;
  overflow: hidden;
  position: relative;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  
  .navbar-left {
    display: flex;
    align-items: center;
    
    .hamburger-container {
      line-height: 46px;
      height: 100%;
      float: left;
      cursor: pointer;
      transition: background 0.3s;
      -webkit-tap-highlight-color: transparent;
      
      &:hover {
        background: rgba(0, 0, 0, 0.025);
      }
    }
    
    .breadcrumb-container {
      margin-left: 16px;
    }
  }
  
  .navbar-right {
    display: flex;
    align-items: center;
    
    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 100%;
      font-size: 18px;
      color: #5a5e66;
      vertical-align: text-bottom;
      
      &.hover-effect {
        cursor: pointer;
        transition: background 0.3s;
        
        &:hover {
          background: rgba(0, 0, 0, 0.025);
        }
      }
    }
    
    .avatar-container {
      margin-right: 30px;
      
      .avatar-wrapper {
        margin-top: 5px;
        position: relative;
        display: flex;
        align-items: center;
        
        .user-avatar {
          cursor: pointer;
          width: 32px;
          height: 32px;
          border-radius: 50%;
        }
        
        .user-name {
          margin-left: 8px;
          font-size: 14px;
          color: #606266;
        }
        
        .el-icon-caret-bottom {
          cursor: pointer;
          position: absolute;
          right: -20px;
          top: 25px;
          font-size: 12px;
        }
      }
    }
  }
}

.app-main {
  min-height: calc(100vh - 50px);
  width: 100%;
  position: relative;
  overflow: hidden;
  padding: 20px;
  background-color: #f0f2f5;
}

// 过渡动画
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.5s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
