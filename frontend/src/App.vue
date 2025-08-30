<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)

// 初始化应用
onMounted(async () => {
  await authStore.initAuth()
  loading.value = false
})

// 判断是否显示布局
const showLayout = computed(() => {
  return route.name !== 'login' && authStore.isAuthenticated
})
</script>

<template>
  <div id="app">
    <el-config-provider>
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-icon size="48" class="loading-icon"><Loading /></el-icon>
        <p>正在加载...</p>
      </div>
      
      <!-- 主应用内容 -->
      <template v-else>
        <!-- 带布局的页面 -->
        <AppLayout v-if="showLayout">
          <RouterView />
        </AppLayout>
        
        <!-- 不带布局的页面（如登录页） -->
        <RouterView v-else />
      </template>
    </el-config-provider>
  </div>
</template>

<style>
#app {
  height: 100vh;
  overflow: hidden;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 16px;
}

.loading-container p {
  color: var(--el-text-color-secondary);
  margin: 0;
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

/* Element Plus 主题定制 */
:root {
  --el-color-primary: #409eff;
  --el-color-primary-light-3: #79bbff;
  --el-color-primary-light-5: #a0cfff;
  --el-color-primary-light-7: #c6e2ff;
  --el-color-primary-light-8: #d9ecff;
  --el-color-primary-light-9: #ecf5ff;
  --el-color-primary-dark-2: #337ecc;
}</style>
