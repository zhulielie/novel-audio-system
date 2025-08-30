<template>
  <div style="padding: 0 15px;" @click="toggleClick">
    <el-icon class="hamburger" :class="{ 'is-active': isActive }">
      <Expand v-if="isActive" />
      <Fold v-else />
    </el-icon>
  </div>
</template>

<script setup lang="ts">
import { Expand, Fold } from '@element-plus/icons-vue'

interface Props {
  isActive: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  toggleClick: []
}>()

const toggleClick = () => {
  emit('toggleClick')
}
</script>

<style lang="scss" scoped>
.hamburger {
  display: inline-block;
  vertical-align: middle;
  width: 20px;
  height: 20px;
  cursor: pointer;
  transition: transform 0.38s;
  transform-origin: 50% 50%;
  
  &.is-active {
    transform: rotate(90deg);
  }
}
</style>
