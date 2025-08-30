<template>
  <div class="drawer-container">
    <el-drawer
      :model-value="modelValue"
      direction="rtl"
      size="300px"
      title="系统布局配置"
      @update:model-value="handleClose"
    >
      <div class="drawer-item">
        <span>主题色</span>
        <el-color-picker
          v-model="theme"
          :predefine="[
            '#409EFF',
            '#1890ff',
            '#304156',
            '#212121',
            '#11a983',
            '#13c2c2',
            '#6959CD',
            '#f5222d',
          ]"
          class="theme-picker"
          popper-class="theme-picker-dropdown"
        />
      </div>

      <div class="drawer-item">
        <span>开启 Tags-View</span>
        <el-switch v-model="tagsView" class="drawer-switch" />
      </div>

      <div class="drawer-item">
        <span>固定 Header</span>
        <el-switch v-model="fixedHeader" class="drawer-switch" />
      </div>

      <div class="drawer-item">
        <span>侧边栏 Logo</span>
        <el-switch v-model="sidebarLogo" class="drawer-switch" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/app'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  change: [settings: any]
}>()

const appStore = useAppStore()

const theme = ref('#409EFF')
const tagsView = computed({
  get: () => appStore.tagsView,
  set: (val) => appStore.setTagsView(val)
})
const fixedHeader = computed({
  get: () => appStore.fixedHeader,
  set: (val) => appStore.setFixedHeader(val)
})
const sidebarLogo = computed({
  get: () => appStore.sidebarLogo,
  set: (val) => appStore.setSidebarLogo(val)
})

const handleClose = (val: boolean) => {
  emit('update:modelValue', val)
}

watch([theme, tagsView, fixedHeader, sidebarLogo], () => {
  emit('change', {
    theme: theme.value,
    tagsView: tagsView.value,
    fixedHeader: fixedHeader.value,
    sidebarLogo: sidebarLogo.value
  })
})
</script>

<style lang="scss" scoped>
.drawer-container {
  .drawer-item {
    color: rgba(0, 0, 0, 0.65);
    font-size: 14px;
    padding: 12px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .drawer-switch {
    height: 26px;
  }
}
</style>
