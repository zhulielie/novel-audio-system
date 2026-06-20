<template>
  <div class="menu-item-content">
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

const icon = computed(() => {
  if (!props.icon) return null
  
  if (ElementPlusIcons[props.icon as keyof typeof ElementPlusIcons]) {
    return ElementPlusIcons[props.icon as keyof typeof ElementPlusIcons]
  }
  
  return ElementPlusIcons.Document
})
</script>

<style lang="scss" scoped>
.menu-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.menu-icon {
  font-size: 17px;
  width: 17px;
  height: 17px;
}

.menu-title {
  font-size: 14px;
  font-weight: 500;
}
</style>
