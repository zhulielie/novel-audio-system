<template>
  <div v-if="!item.hidden && !item.meta?.hidden">
    <template v-if="hasOneShowingChild(item.children, item) && (!onlyOneChild.children || onlyOneChild.noShowingChildren) && !item.alwaysShow">
      <app-link v-if="onlyOneChild.meta && isExternal(resolvePath(onlyOneChild.path))" :to="resolvePath(onlyOneChild.path)">
        <el-menu-item :index="resolvePath(onlyOneChild.path)" :class="{'submenu-title-noDropdown': !isNest}">
          <item :icon="onlyOneChild.meta.icon || (item.meta && item.meta.icon)" :title="onlyOneChild.meta.title" />
        </el-menu-item>
      </app-link>
      <el-menu-item
        v-else-if="onlyOneChild.meta"
        ref="menuItemRef"
        :index="resolvePath(onlyOneChild.path)"
        :class="{'submenu-title-noDropdown': !isNest}"
      >
        <item :icon="onlyOneChild.meta.icon || (item.meta && item.meta.icon)" :title="onlyOneChild.meta.title" />
      </el-menu-item>
    </template>

    <el-sub-menu v-else ref="subMenu" :index="resolvePath(item.path)" popper-append-to-body>
      <template #title>
        <item v-if="item.meta" :icon="item.meta.icon" :title="item.meta.title" />
      </template>
      <sidebar-item
        v-for="child in item.children"
        :key="child.path"
        :is-nest="true"
        :item="child"
        :base-path="resolvePath(child.path)"
        class="nest-menu"
      />
    </el-sub-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, onUpdated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { isExternal } from '@/utils/validate'
import Item from './Item.vue'
import AppLink from './Link.vue'

interface Props {
  item: any
  isNest?: boolean
  basePath?: string
}

const props = withDefaults(defineProps<Props>(), {
  isNest: false,
  basePath: ''
})

const router = useRouter()
const menuItemRef = ref<any>(null)
const onlyOneChild = ref<any>({})

let clickHandler: ((e: Event) => void) | null = null

const hasOneShowingChild = (children: any[] = [], parent: any) => {
  const showingChildren = children.filter((item: any) => {
    if (item.hidden || item.meta?.hidden) {
      return false
    } else {
      onlyOneChild.value = item
      return true
    }
  })

  if (showingChildren.length === 1) {
    return true
  }

  if (showingChildren.length === 0) {
    onlyOneChild.value = { ...parent, path: '', noShowingChildren: true }
    return true
  }

  return false
}

const resolvePath = (routePath: string) => {
  if (isExternal(routePath)) {
    return routePath
  }
  if (isExternal(props.basePath)) {
    return props.basePath
  }
  return path.resolve(props.basePath, routePath)
}

const navigate = (route: any) => {
  const targetPath = resolvePath(route.path)
  if (isExternal(targetPath)) {
    window.open(targetPath, '_blank')
    return
  }
  if (targetPath === router.currentRoute.value.path) {
    return
  }
  router.push(targetPath)
}

const detachClickListener = () => {
  if (clickHandler && menuItemRef.value?.$el) {
    menuItemRef.value.$el.removeEventListener('click', clickHandler, true)
    clickHandler = null
  }
}

const attachClickListener = () => {
  detachClickListener()
  const el = menuItemRef.value?.$el
  if (!el) return
  clickHandler = (e: Event) => {
    e.stopPropagation()
    if (onlyOneChild.value?.meta) {
      navigate(onlyOneChild.value)
    }
  }
  el.addEventListener('click', clickHandler, true)
}

onMounted(() => {
  nextTick(() => attachClickListener())
})

onUpdated(() => {
  nextTick(() => attachClickListener())
})

onUnmounted(() => {
  detachClickListener()
})

const path = {
  resolve: (basePath: string, relativePath: string) => {
    if (relativePath.startsWith('/')) {
      return relativePath
    }
    const baseSegments = basePath.split('/').filter(Boolean)
    const relativeSegments = relativePath.split('/').filter(Boolean)
    return '/' + [...baseSegments, ...relativeSegments].join('/')
  }
}
</script>

<style lang="scss" scoped>
.nest-menu .el-submenu > .el-submenu__title,
.el-submenu .el-menu-item {
  background-color: var(--bg-sidebar) !important;

  &:hover {
    background-color: var(--primary-50) !important;
  }
}

:deep(.el-menu-item) {
  border-radius: var(--radius-md);
  margin: 4px 10px;
  height: 44px;
  line-height: 44px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;

  &:hover {
    background-color: var(--primary-50) !important;
    color: var(--primary-600) !important;
  }

  &.is-active {
    background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-500) 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  }
}

:deep(.el-sub-menu__title) {
  border-radius: var(--radius-md);
  margin: 4px 10px;
  height: 44px;
  line-height: 44px;
  font-weight: 500;

  &:hover {
    background-color: var(--primary-50) !important;
    color: var(--primary-600) !important;
  }
}

:deep(.el-sub-menu.is-active > .el-sub-menu__title) {
  color: var(--primary-600) !important;
}
</style>
