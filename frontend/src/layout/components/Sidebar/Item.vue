<template>
  <div>
    <el-icon v-if="icon" class="menu-icon">
      <component :is="icon" />
    </el-icon>
    <span v-if="title" class="menu-title">{{ title }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as ElementPlusIcons from '@element-plus/icons-vue'

interface Props {
  icon?: string
  title?: string
}

const props = defineProps<Props>()

// 动态获取图标组件
const icon = computed(() => {
  if (!props.icon) return null
  
  // 如果是 Element Plus 图标
  if (ElementPlusIcons[props.icon as keyof typeof ElementPlusIcons]) {
    return ElementPlusIcons[props.icon as keyof typeof ElementPlusIcons]
  }
  
  // 默认图标
  return ElementPlusIcons.Document
})
</script>

<style lang="scss" scoped>
.menu-icon {
  margin-right: 8px;
  font-size: 16px;
}

.menu-title {
  font-size: 14px;
}
</style>
