import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface SidebarState {
  opened: boolean
  withoutAnimation: boolean
}

export interface AppState {
  sidebar: SidebarState
  device: 'desktop' | 'mobile'
  size: 'large' | 'default' | 'small'
  tagsView: boolean
  fixedHeader: boolean
  sidebarLogo: boolean
}

export const useAppStore = defineStore('app', () => {
  // 状态
  const sidebar = ref<SidebarState>({
    opened: localStorage.getItem('sidebarStatus') ? !!+localStorage.getItem('sidebarStatus')! : true,
    withoutAnimation: false
  })
  
  const device = ref<'desktop' | 'mobile'>('desktop')
  const size = ref<'large' | 'default' | 'small'>('default')
  const tagsView = ref(true)
  const fixedHeader = ref(false)
  const sidebarLogo = ref(true)

  // 计算属性
  const sidebarOpened = computed(() => sidebar.value.opened)

  // 方法
  const toggleSidebar = () => {
    sidebar.value.opened = !sidebar.value.opened
    sidebar.value.withoutAnimation = false
    if (sidebar.value.opened) {
      localStorage.setItem('sidebarStatus', '1')
    } else {
      localStorage.setItem('sidebarStatus', '0')
    }
  }

  const closeSidebar = (withoutAnimation: boolean = false) => {
    localStorage.setItem('sidebarStatus', '0')
    sidebar.value.opened = false
    sidebar.value.withoutAnimation = withoutAnimation
  }

  const toggleDevice = (deviceType: 'desktop' | 'mobile') => {
    device.value = deviceType
  }

  const setSize = (sizeType: 'large' | 'default' | 'small') => {
    size.value = sizeType
    localStorage.setItem('size', sizeType)
  }

  const setTagsView = (show: boolean) => {
    tagsView.value = show
  }

  const setFixedHeader = (fixed: boolean) => {
    fixedHeader.value = fixed
  }

  const setSidebarLogo = (show: boolean) => {
    sidebarLogo.value = show
  }

  // 初始化
  const initSettings = () => {
    const savedSize = localStorage.getItem('size') as 'large' | 'default' | 'small'
    if (savedSize) {
      size.value = savedSize
    }
  }

  return {
    // 状态
    sidebar,
    device,
    size,
    tagsView,
    fixedHeader,
    sidebarLogo,
    
    // 计算属性
    sidebarOpened,
    
    // 方法
    toggleSidebar,
    closeSidebar,
    toggleDevice,
    setSize,
    setTagsView,
    setFixedHeader,
    setSidebarLogo,
    initSettings
  }
})

// 初始化设置
const appStore = useAppStore()
appStore.initSettings()
