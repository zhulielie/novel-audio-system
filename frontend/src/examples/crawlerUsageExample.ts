/**
 * 爬虫API使用示例
 * 展示如何在前端项目中使用新的爬虫功能
 */

import CrawlerService from '@/services/crawlerService'
import { apiService } from '@/services/api'

// 示例1: 基本URL分析
export const exampleUrlAnalysis = async () => {
  try {
    const url = 'https://www.hetushu.com/book/38/26125.html'
    console.log('🔍 分析小说URL:', url)

    const result = await CrawlerService.analyzeUrl(url)

    if (result.success) {
      console.log('✅ 分析成功!')
      console.log('📚 标题:', result.title)
      console.log('👤 作者:', result.author)
      console.log('📝 章节数:', result.chapter_count)
      console.log('📖 描述:', result.description)
    } else {
      console.log('❌ 分析失败:', result.error)
    }
  } catch (error) {
    console.error('分析出错:', error)
  }
}

// 示例2: 快速批量导入
export const exampleQuickImport = async () => {
  try {
    const url = 'https://www.hetushu.com/book/38/26125.html'

    console.log('🚀 开始快速导入...')

    const result = await CrawlerService.quickImport(url, {
      max_chapters: 10,  // 只导入前10章
      speed: 'normal'    // 使用正常速度
    })

    if (result.success) {
      console.log('✅ 导入成功!')
      console.log('📚 小说ID:', result.novel_id)
      console.log('📝 导入章节:', result.chapters_imported)
      console.log('📊 发现总数:', result.total_found)
    } else {
      console.log('❌ 导入失败:', result.error)
    }
  } catch (error) {
    console.error('导入出错:', error)
  }
}

// 示例3: 高级批量导入（带完整参数）
export const exampleAdvancedImport = async () => {
  try {
    const importParams = {
      source_url: 'https://www.hetushu.com/book/38/26125.html',
      novel_title: '测试小说',
      novel_author: '测试作者',
      source_id: 1,  // 和图书网
      max_chapters: 50,  // 最多导入50章
      start_chapter: 1,  // 从第1章开始
      end_chapter: 50,   // 到第50章结束
      speed: 'slow' as const  // 慢速模式
    }

    console.log('🚀 开始高级批量导入...')

    const result = await CrawlerService.batchImport(importParams)

    if (result.success) {
      console.log('✅ 高级导入成功!')
      console.log('📊 结果详情:', result)
    } else {
      console.log('❌ 高级导入失败:', result.error)
    }
  } catch (error) {
    console.error('高级导入出错:', error)
  }
}

// 示例4: 获取爬虫状态
export const exampleGetStatus = async () => {
  try {
    console.log('📊 获取爬虫状态...')

    const status = await CrawlerService.getStatus()

    console.log('📈 爬虫状态:')
    console.log('- 总小说来源:', status.total_relations)
    console.log('- 活跃来源:', status.active_relations)
    console.log('- 最近同步:', status.recent_synced)
    console.log('- 支持站点:', status.supported_sites)
  } catch (error) {
    console.error('获取状态出错:', error)
  }
}

// 示例5: 获取小说章节目录
export const exampleGetChapterDirectory = async (novelId: number) => {
  try {
    console.log('📚 获取章节目录，novelId:', novelId)

    const directory = await CrawlerService.getChapterDirectory(novelId)

    console.log('📖 章节目录:')
    console.log('- 小说标题:', directory.novel.title)
    console.log('- 作者:', directory.novel.author)
    console.log('- 总章节数:', directory.novel.total_chapters)
    console.log('- 章节列表:', directory.chapters.slice(0, 5))  // 只显示前5章
  } catch (error) {
    console.error('获取章节目录出错:', error)
  }
}

// 示例6: 搜索章节内容
export const exampleSearchChapters = async (query: string, novelId?: number) => {
  try {
    console.log('🔍 搜索章节内容:', query)

    const searchResult = await CrawlerService.searchChapters(query, novelId)

    console.log('📝 搜索结果:')
    console.log('- 找到结果数:', searchResult.results?.length || 0)
    if (searchResult.results?.length > 0) {
      console.log('- 第一个结果:', searchResult.results[0])
    }
  } catch (error) {
    console.error('搜索出错:', error)
  }
}

// 示例7: 在Vue组件中使用
export const exampleVueUsage = `
<template>
  <div class="crawler-demo">
    <el-button @click="analyzeUrl" :loading="analyzing">
      分析URL
    </el-button>
    <el-button @click="quickImport" :loading="importing">
      快速导入
    </el-button>

    <div v-if="analysisResult">
      <h3>分析结果</h3>
      <p>标题: {{ analysisResult.title }}</p>
      <p>作者: {{ analysisResult.author }}</p>
      <p>章节数: {{ analysisResult.chapter_count }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CrawlerService from '@/services/crawlerService'

const analyzing = ref(false)
const importing = ref(false)
const analysisResult = ref(null)

const analyzeUrl = async () => {
  analyzing.value = true
  try {
    const result = await CrawlerService.analyzeUrl(
      'https://www.hetushu.com/book/38/26125.html'
    )
    analysisResult.value = result
  } catch (error) {
    console.error('分析失败:', error)
  } finally {
    analyzing.value = false
  }
}

const quickImport = async () => {
  if (!analysisResult.value?.success) return

  importing.value = true
  try {
    const result = await CrawlerService.quickImport(
      'https://www.hetushu.com/book/38/26125.html',
      { max_chapters: 10, speed: 'normal' }
    )
    console.log('导入结果:', result)
  } catch (error) {
    console.error('导入失败:', error)
  } finally {
    importing.value = false
  }
}
</script>
`

// 示例8: React Hook风格的使用（如果需要）
export const exampleReactHook = `
import { useState, useCallback } from 'react'
import CrawlerService from '@/services/crawlerService'

export const useCrawler = () => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const analyzeUrl = useCallback(async (url: string) => {
    setLoading(true)
    try {
      const analysisResult = await CrawlerService.analyzeUrl(url)
      setResult(analysisResult)
      return analysisResult
    } catch (error) {
      console.error('分析失败:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  const quickImport = useCallback(async (url: string, options = {}) => {
    setLoading(true)
    try {
      const importResult = await CrawlerService.quickImport(url, options)
      return importResult
    } catch (error) {
      console.error('导入失败:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    result,
    analyzeUrl,
    quickImport
  }
}
`

// 导出所有示例
export const crawlerExamples = {
  exampleUrlAnalysis,
  exampleQuickImport,
  exampleAdvancedImport,
  exampleGetStatus,
  exampleGetChapterDirectory,
  exampleSearchChapters,
  exampleVueUsage,
  exampleReactHook
}
