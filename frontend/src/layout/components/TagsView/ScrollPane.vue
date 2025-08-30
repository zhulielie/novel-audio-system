<template>
  <div class="scroll-container" ref="scrollContainer" @wheel="handleScroll">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const scrollContainer = ref()

const handleScroll = (e: WheelEvent) => {
  const eventDelta = e.wheelDelta || -e.deltaY * 40
  scrollContainer.value.scrollLeft = scrollContainer.value.scrollLeft + eventDelta / 4
}

const moveToTarget = (currentTag: HTMLElement) => {
  const container = scrollContainer.value
  const containerWidth = container.offsetWidth
  const tagList = container.querySelectorAll('.tags-view-item')
  
  let firstTag = null
  let lastTag = null
  
  if (tagList.length > 0) {
    firstTag = tagList[0]
    lastTag = tagList[tagList.length - 1]
  }
  
  if (firstTag === currentTag) {
    container.scrollLeft = 0
  } else if (lastTag === currentTag) {
    container.scrollLeft = container.scrollWidth - containerWidth
  } else {
    const currentIndex = Array.from(tagList).findIndex(item => item === currentTag)
    const prevTag = tagList[currentIndex - 1]
    const nextTag = tagList[currentIndex + 1]
    
    const afterNextTagOffsetLeft = nextTag ? nextTag.offsetLeft + nextTag.offsetWidth + 4 : 0
    const beforePrevTagOffsetLeft = prevTag ? prevTag.offsetLeft - 4 : 0
    
    if (afterNextTagOffsetLeft > container.scrollLeft + containerWidth) {
      container.scrollLeft = afterNextTagOffsetLeft - containerWidth
    } else if (beforePrevTagOffsetLeft < container.scrollLeft) {
      container.scrollLeft = beforePrevTagOffsetLeft
    }
  }
}

defineExpose({
  moveToTarget
})
</script>

<style lang="scss" scoped>
.scroll-container {
  white-space: nowrap;
  position: relative;
  overflow: hidden;
  width: 100%;
}
</style>
