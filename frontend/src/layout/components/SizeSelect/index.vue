<template>
  <el-dropdown trigger="click" @command="handleSetSize">
    <div>
      <el-icon>
        <Operation />
      </el-icon>
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item :disabled="size === 'default'" command="default">
          默认
        </el-dropdown-item>
        <el-dropdown-item :disabled="size === 'large'" command="large">
          大号
        </el-dropdown-item>
        <el-dropdown-item :disabled="size === 'small'" command="small">
          小号
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Operation } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { ElMessage } from 'element-plus'

const appStore = useAppStore()

const size = computed(() => appStore.size)

const handleSetSize = (size: 'large' | 'default' | 'small') => {
  appStore.setSize(size)
  ElMessage.success('设置成功')
}
</script>

<style scoped>
div {
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
}
</style>
