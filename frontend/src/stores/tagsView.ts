import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface TagView {
  name?: string
  path: string
  fullPath?: string
  title?: string
  meta?: any
  query?: any
  params?: any
}

export const useTagsViewStore = defineStore('tagsView', () => {
  const visitedViews = ref<TagView[]>([])
  const cachedViews = ref<string[]>([])

  const addView = (view: TagView) => {
    addVisitedView(view)
    addCachedView(view)
  }

  const addVisitedView = (view: TagView) => {
    if (visitedViews.value.some(v => v.path === view.path)) return
    visitedViews.value.push(
      Object.assign({}, view, {
        title: view.meta?.title || 'no-name'
      })
    )
  }

  const addCachedView = (view: TagView) => {
    if (cachedViews.value.includes(view.name!)) return
    if (!view.meta?.noCache) {
      cachedViews.value.push(view.name!)
    }
  }

  const delView = (view: TagView) => {
    return new Promise(resolve => {
      delVisitedView(view)
      delCachedView(view)
      resolve({
        visitedViews: [...visitedViews.value],
        cachedViews: [...cachedViews.value]
      })
    })
  }

  const delVisitedView = (view: TagView) => {
    return new Promise(resolve => {
      for (const [i, v] of visitedViews.value.entries()) {
        if (v.path === view.path) {
          visitedViews.value.splice(i, 1)
          break
        }
      }
      resolve([...visitedViews.value])
    })
  }

  const delCachedView = (view: TagView) => {
    return new Promise(resolve => {
      const index = cachedViews.value.indexOf(view.name!)
      index > -1 && cachedViews.value.splice(index, 1)
      resolve([...cachedViews.value])
    })
  }

  const delOthersViews = (view: TagView) => {
    return new Promise(resolve => {
      delOthersVisitedViews(view)
      delOthersCachedViews(view)
      resolve({
        visitedViews: [...visitedViews.value],
        cachedViews: [...cachedViews.value]
      })
    })
  }

  const delOthersVisitedViews = (view: TagView) => {
    return new Promise(resolve => {
      visitedViews.value = visitedViews.value.filter(v => {
        return v.meta?.affix || v.path === view.path
      })
      resolve([...visitedViews.value])
    })
  }

  const delOthersCachedViews = (view: TagView) => {
    return new Promise(resolve => {
      const index = cachedViews.value.indexOf(view.name!)
      if (index > -1) {
        cachedViews.value = cachedViews.value.slice(index, index + 1)
      } else {
        cachedViews.value = []
      }
      resolve([...cachedViews.value])
    })
  }

  const delAllViews = () => {
    return new Promise(resolve => {
      delAllVisitedViews()
      delAllCachedViews()
      resolve({
        visitedViews: [...visitedViews.value],
        cachedViews: [...cachedViews.value]
      })
    })
  }

  const delAllVisitedViews = () => {
    return new Promise(resolve => {
      const affixTags = visitedViews.value.filter(tag => tag.meta?.affix)
      visitedViews.value = affixTags
      resolve([...visitedViews.value])
    })
  }

  const delAllCachedViews = () => {
    return new Promise(resolve => {
      cachedViews.value = []
      resolve([...cachedViews.value])
    })
  }

  const updateVisitedView = (view: TagView) => {
    for (let v of visitedViews.value) {
      if (v.path === view.path) {
        v = Object.assign(v, view)
        break
      }
    }
  }

  return {
    visitedViews,
    cachedViews,
    addView,
    addVisitedView,
    addCachedView,
    delView,
    delVisitedView,
    delCachedView,
    delOthersViews,
    delOthersVisitedViews,
    delOthersCachedViews,
    delAllViews,
    delAllVisitedViews,
    delAllCachedViews,
    updateVisitedView
  }
})
