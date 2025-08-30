<template>
  <div @click="click">
    <el-icon>
      <FullScreen v-if="!isFullscreen" />
      <Aim v-else />
    </el-icon>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { FullScreen, Aim } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const isFullscreen = ref(false)

const click = () => {
  if (!document.fullscreenEnabled) {
    ElMessage.warning('您的浏览器不支持全屏模式')
    return false
  }
  
  if (!isFullscreen.value) {
    requestFullscreen()
  } else {
    exitFullscreen()
  }
}

const requestFullscreen = () => {
  const element = document.documentElement
  if (element.requestFullscreen) {
    element.requestFullscreen()
  }
}

const exitFullscreen = () => {
  if (document.exitFullscreen) {
    document.exitFullscreen()
  }
}

const change = () => {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  document.addEventListener('fullscreenchange', change)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', change)
})
</script>

<style scoped>
div {
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
}
</style>
