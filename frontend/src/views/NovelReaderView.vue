<template>
  <div class="novel-reader">
    <!-- 阅读器头部 -->
    <div class="reader-header">
      <div class="header-left">
        <el-button @click="goBack" size="small" type="primary" plain>
          <el-icon><ArrowLeft /></el-icon>
          返回目录
        </el-button>
        <span class="novel-title">{{ novel?.title }}</span>
      </div>
      
      <div class="header-right">
        <!-- 阅读模式切换 -->
        <el-button-group>
          <el-button 
            :type="readingMode === 'page' ? 'primary' : 'default'"
            @click="setReadingMode('page')"
            size="small"
          >
            📄 翻页模式
          </el-button>
          <el-button 
            :type="readingMode === 'scroll' ? 'primary' : 'default'"
            @click="setReadingMode('scroll')"
            size="small"
          >
            📜 连续模式
          </el-button>
        </el-button-group>
        
        <!-- 阅读设置 -->
        <el-button @click="showSettings = true" size="small" type="info" plain>
          <el-icon><Setting /></el-icon>
          设置
        </el-button>
      </div>
    </div>

    <!-- 翻页模式 -->
    <div v-if="readingMode === 'page'" class="page-mode">
      <div class="page-container" v-if="currentChapter">
        <!-- 章节导航 -->
        <div class="chapter-nav">
          <el-button 
            @click="previousChapter" 
            :disabled="!hasPreviousChapter"
            size="small"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一章
          </el-button>
          
          <span class="chapter-info">
            {{ currentChapter.title }} ({{ currentChapterIndex + 1 }}/{{ totalChapters }})
          </span>
          
          <el-button 
            @click="nextChapter" 
            :disabled="!hasNextChapter"
            size="small"
          >
            下一章
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>

        <!-- 章节内容 -->
        <div class="chapter-content">
          <h2 class="chapter-title">{{ currentChapter.title }}</h2>
          <div class="chapter-text" v-html="formatChapterContent(currentChapter.content)"></div>
        </div>

        <!-- 底部导航 -->
        <div class="chapter-nav bottom-nav">
          <el-button 
            @click="previousChapter" 
            :disabled="!hasPreviousChapter"
            size="large"
          >
            <el-icon><ArrowLeft /></el-icon>
            上一章
          </el-button>
          
          <el-button 
            @click="nextChapter" 
            :disabled="!hasNextChapter"
            size="large"
            type="primary"
          >
            下一章
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-else class="loading-container">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>正在加载章节内容...</p>
      </div>
    </div>

    <!-- 连续滚动模式 -->
    <div v-else-if="readingMode === 'scroll'" class="scroll-mode">
      <div class="scroll-container" ref="scrollContainer" @scroll="handleScroll">
        <!-- 已加载的章节 -->
        <div 
          v-for="chapter in loadedChapters" 
          :key="chapter.id"
          class="scroll-chapter"
          :data-chapter-id="chapter.id"
        >
          <h2 class="chapter-title">{{ chapter.title }}</h2>
          <div class="chapter-text" v-html="formatChapterContent(chapter.content)"></div>
          <div class="chapter-separator"></div>
        </div>

        <!-- 加载更多指示器 -->
        <div v-if="hasMoreChapters" class="load-more-indicator">
          <el-icon v-if="loadingMore" class="loading-icon"><Loading /></el-icon>
          <p v-if="loadingMore">正在加载下一章...</p>
          <p v-else>滚动到底部加载更多</p>
        </div>

        <!-- 没有更多章节 -->
        <div v-else class="no-more-chapters">
          <p>🎉 已阅读完所有章节</p>
        </div>
      </div>

      <!-- 滚动进度条 -->
      <div class="scroll-progress">
        <div class="progress-bar" :style="{ width: scrollProgress + '%' }"></div>
      </div>

      <!-- 当前章节指示器 -->
      <div class="current-chapter-indicator">
        <span>{{ currentScrollChapter?.title || '加载中...' }}</span>
      </div>
    </div>

    <!-- 自动爬取状态提示 -->
    <div v-if="crawlingStatus" class="crawling-status">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>{{ crawlingStatus }}</span>
    </div>

    <!-- 自动爬取设置（在设置对话框中） -->
    <div v-if="readingMode === 'page'" class="auto-crawl-info">
      <div v-if="autoCrawlEnabled" class="crawl-enabled">
        <el-icon><Download /></el-icon>
        <span>智能爬取已启用</span>
      </div>
    </div>

    <!-- 阅读设置对话框 -->
    <el-dialog v-model="showSettings" title="阅读设置" width="400px">
      <div class="reading-settings">
        <div class="setting-item">
          <label>字体大小</label>
          <el-slider v-model="fontSize" :min="12" :max="24" :step="1" />
          <span>{{ fontSize }}px</span>
        </div>
        
        <div class="setting-item">
          <label>行间距</label>
          <el-slider v-model="lineHeight" :min="1.2" :max="2.5" :step="0.1" />
          <span>{{ lineHeight }}</span>
        </div>
        
        <div class="setting-item">
          <label>背景色</label>
          <el-radio-group v-model="backgroundColor">
            <el-radio label="white">白色</el-radio>
            <el-radio label="sepia">护眼</el-radio>
            <el-radio label="dark">夜间</el-radio>
          </el-radio-group>
        </div>
        
        <div class="setting-item">
          <label>智能爬取</label>
          <el-switch v-model="autoCrawlEnabled" />
          <span class="setting-desc">自动爬取新章节</span>
        </div>
        
        <div v-if="autoCrawlEnabled" class="setting-item">
          <label>提前爬取</label>
          <el-slider v-model="crawlAhead" :min="1" :max="10" :step="1" />
          <span>{{ crawlAhead }}章</span>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button @click="saveUserSettings" type="success">保存设置</el-button>
        <el-button type="primary" @click="applySettings">应用设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Setting, Loading, Download } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

const route = useRoute()
const router = useRouter()

// 基础数据
const novel = ref(null)
const chapters = ref([])
const loading = ref(true)

// 阅读模式：'page' 翻页模式，'scroll' 连续模式
const readingMode = ref('page')

// 翻页模式相关
const currentChapterIndex = ref(0)
const currentChapter = ref(null)

// 连续模式相关
const loadedChapters = ref([])
const loadingMore = ref(false)
const hasMoreChapters = ref(true)
const scrollContainer = ref(null)
const scrollProgress = ref(0)
const currentScrollChapter = ref(null)

// 自动爬取相关
const autoCrawlEnabled = ref(true)
const crawlAhead = ref(3) // 提前爬取几章
const crawlingStatus = ref('')
const lastCrawlChapter = ref(0)

// 阅读设置
const showSettings = ref(false)
const fontSize = ref(16)
const lineHeight = ref(1.6)
const backgroundColor = ref('white')

// 加载用户阅读设置
const loadUserSettings = async () => {
  try {
    const response = await apiService.get('/novels/reading-settings/')
    if (response.success !== false) {
      const settings = response.data || response
      autoCrawlEnabled.value = settings.auto_crawl_enabled ?? true
      crawlAhead.value = settings.crawl_ahead_chapters ?? 3
      fontSize.value = settings.font_size ?? 16
      lineHeight.value = settings.line_height ?? 1.6
      backgroundColor.value = settings.background_color ?? 'white'
      readingMode.value = settings.reading_mode ?? 'page'
      console.log('✅ 用户阅读设置加载成功:', settings)
    }
  } catch (error) {
    console.error('❌ 加载用户阅读设置失败:', error)
    // 使用默认设置
  }
}

// 保存用户阅读设置
const saveUserSettings = async () => {
  try {
    const settings = {
      auto_crawl_enabled: autoCrawlEnabled.value,
      crawl_ahead_chapters: crawlAhead.value,
      font_size: fontSize.value,
      line_height: lineHeight.value,
      background_color: backgroundColor.value,
      reading_mode: readingMode.value
    }
    
    const response = await apiService.post('/novels/reading-settings/', settings)
    if (response.success !== false) {
      ElMessage.success('阅读设置保存成功')
      console.log('✅ 用户阅读设置保存成功:', settings)
    } else {
      ElMessage.error('阅读设置保存失败')
    }
  } catch (error) {
    console.error('❌ 保存用户阅读设置失败:', error)
    ElMessage.error('保存设置失败，请重试')
  }
}

// 计算属性
const totalChapters = computed(() => chapters.value.length)
const hasPreviousChapter = computed(() => currentChapterIndex.value > 0)
const hasNextChapter = computed(() => currentChapterIndex.value < totalChapters.value - 1)

// 获取小说和章节数据
const fetchNovelData = async () => {
  try {
    const novelId = Number(route.params.id)
    const startChapter = Number(route.query.chapter) || 1
    
    console.log('开始获取小说数据...', { novelId, startChapter })
    
    // 获取小说信息
    const novelResponse = await apiService.get(`/novels/${novelId}/`)
    console.log('小说API完整响应:', novelResponse)
    // 直接使用响应对象，不是 .data
    novel.value = novelResponse.data || novelResponse
    console.log('小说信息:', novel.value)
    
    // 获取章节列表
    const chaptersResponse = await apiService.get(`/novels/${novelId}/chapters/`)
    console.log('章节API完整响应:', chaptersResponse)
    
    // 处理不同的响应格式
    let chaptersData = chaptersResponse.data || chaptersResponse
    console.log('章节数据:', chaptersData)
    
    if (chaptersData && chaptersData.results) {
      chapters.value = chaptersData.results
    } else if (Array.isArray(chaptersData)) {
      chapters.value = chaptersData
    } else {
      chapters.value = []
    }
    
    console.log('解析后的章节数据:', chapters.value)
    console.log('章节数量:', chapters.value.length)
    
    // 设置初始章节
    if (chapters.value.length > 0) {
      currentChapterIndex.value = Math.max(0, startChapter - 1)
      await loadCurrentChapter()
      
      // 如果是连续模式，预加载几章
      if (readingMode.value === 'scroll') {
        await loadInitialChapters()
      }
    }
    
    loading.value = false
  } catch (error) {
    console.error('获取小说数据失败:', error)
    ElMessage.error('加载失败，请重试')
    loading.value = false
  }
}

// 检查并自动爬取新章节
const checkAndLoadNewChapters = async () => {
  if (!novel.value || !autoCrawlEnabled.value) return
  
  const currentChapterNum = currentChapterIndex.value + 1
  const totalChapters = chapters.value.length
  
  // 如果是最后一章，立即检查并爬取新章节
  if (currentChapterNum === totalChapters) {
    console.log(`当前是最后一章(第${currentChapterNum}章)，开始自动爬取新章节...`)
    
    try {
      // 先检查数据库中是否已有新章节
      const checkResponse = await apiService.get(`/novels/${novel.value.id}/chapters/`)
      const existingChapters = checkResponse.data?.results || checkResponse.data || checkResponse
      
      if (existingChapters.length > totalChapters) {
        console.log(`数据库中发现新章节！从${totalChapters}章增加到${existingChapters.length}章`)
        
        // 更新章节列表
        chapters.value = existingChapters.map(chapter => ({
          id: chapter.id,
          title: chapter.title,
          content: chapter.content || '',
          chapter_number: chapter.chapter_number,
          created_at: chapter.created_at
        }))
        
        ElMessage.success(`发现${existingChapters.length - totalChapters}个新章节！`)
        return
      }
      
      // 如果数据库中没有新章节，则自动爬取
      console.log('数据库中没有新章节，开始自动爬取...')
      ElMessage.info('正在自动爬取新章节，请稍候...')
      
      const crawlResponse = await apiService.post('/crawler/auto-crawl/', {
        novel_id: novel.value.id,
        current_chapter: currentChapterNum,
        crawl_ahead: crawlAhead.value || 3
      })
      
      console.log('爬取API响应:', crawlResponse)
      
      if (crawlResponse?.data?.success || crawlResponse?.success) {
        const responseData = crawlResponse.data || crawlResponse
        console.log('自动爬取任务启动成功:', responseData)
        ElMessage.success('自动爬取任务已启动，正在后台下载新章节...')
        
        // 等待一段时间后重新检查章节
        setTimeout(async () => {
          try {
            console.log('重新检查章节列表...')
            const newCheckResponse = await apiService.get(`/novels/${novel.value.id}/chapters/`)
            const updatedChapters = newCheckResponse.data?.results || newCheckResponse.data || newCheckResponse
            
            if (updatedChapters.length > totalChapters) {
              chapters.value = updatedChapters.map(chapter => ({
                id: chapter.id,
                title: chapter.title,
                content: chapter.content || '',
                chapter_number: chapter.chapter_number,
                created_at: chapter.created_at
              }))
              
              ElMessage.success(`成功爬取${updatedChapters.length - totalChapters}个新章节！`)
            } else {
              ElMessage.warning('暂时没有发现新章节')
            }
          } catch (error) {
            console.error('重新检查章节失败:', error)
          }
        }, 10000) // 10秒后检查
        
      } else {
        const errorData = crawlResponse?.data || crawlResponse
        console.error('自动爬取失败:', errorData)
        ElMessage.error('自动爬取失败: ' + (errorData?.error || errorData?.message || '未知错误'))
      }
      
    } catch (error) {
      console.error('自动爬取新章节失败:', error)
      ElMessage.error('自动爬取失败: ' + (error.response?.data?.error || error.message))
    }
  }
}

// 加载当前章节内容
const loadCurrentChapter = async () => {
  if (!chapters.value[currentChapterIndex.value]) return
  
  try {
    const chapter = chapters.value[currentChapterIndex.value]
    console.log('加载章节:', chapter)
    
    // 如果章节已经有内容，直接使用
    if (chapter.content) {
      currentChapter.value = chapter
      
      // 检查是否需要加载新章节
      await checkAndLoadNewChapters()
      return
    }
    
    // 否则尝试从API获取详细内容
    const response = await apiService.get(`/chapters/${chapter.id}/`)
    currentChapter.value = response.data || response
    
    // 检查是否需要加载新章节
    await checkAndLoadNewChapters()
  } catch (error) {
    console.error('加载章节失败:', error)
    // 如果API失败，尝试使用已有的章节数据
    const chapter = chapters.value[currentChapterIndex.value]
    if (chapter) {
      currentChapter.value = chapter
      // 即使失败也要检查新章节
      await checkAndLoadNewChapters()
    } else {
      ElMessage.error('章节加载失败')
    }
  }
}

// 连续模式：加载初始章节
const loadInitialChapters = async () => {
  loadedChapters.value = []
  const initialCount = 3 // 初始加载3章
  
  for (let i = currentChapterIndex.value; i < Math.min(currentChapterIndex.value + initialCount, chapters.value.length); i++) {
    await loadChapterForScroll(i)
  }
  
  hasMoreChapters.value = currentChapterIndex.value + initialCount < chapters.value.length
}

// 连续模式：加载指定章节
const loadChapterForScroll = async (index) => {
  if (!chapters.value[index]) return
  
  try {
    const chapter = chapters.value[index]
    console.log('连续模式加载章节:', chapter)
    
    // 如果章节已经有内容，直接使用
    if (chapter.content) {
      loadedChapters.value.push(chapter)
      return
    }
    
    // 否则尝试从API获取详细内容
    try {
      const response = await apiService.get(`/chapters/${chapter.id}/`)
      loadedChapters.value.push(response.data || response)
    } catch (apiError) {
      // 如果API失败，使用已有的章节数据
      console.log('API调用失败，使用现有章节数据:', apiError)
      loadedChapters.value.push(chapter)
    }
  } catch (error) {
    console.error('加载章节失败:', error)
  }
}

// 翻页模式：上一章
const previousChapter = async () => {
  if (!hasPreviousChapter.value) return
  
  currentChapterIndex.value--
  await loadCurrentChapter()
  
  // 更新URL
  router.replace({
    query: { ...route.query, chapter: currentChapterIndex.value + 1 }
  })
}

// 翻页模式：下一章
const nextChapter = async () => {
  if (!hasNextChapter.value) return
  
  currentChapterIndex.value++
  await loadCurrentChapter()
  
  // 检查是否需要自动爬取
  if (autoCrawlEnabled.value) {
    checkAndAutoCrawl()
  }
  
  // 更新URL
  router.replace({
    query: { ...route.query, chapter: currentChapterIndex.value + 1 }
  })
}

// 设置阅读模式
const setReadingMode = async (mode) => {
  console.log('🔧 设置阅读模式:', mode)
  readingMode.value = mode
  
  if (mode === 'scroll') {
    console.log('📜 进入连续模式')
    console.log('📜 当前已加载章节数:', loadedChapters.value.length)
    
    if (loadedChapters.value.length === 0) {
      console.log('📜 开始加载初始章节...')
      await loadInitialChapters()
    } else {
      console.log('📜 章节已加载，跳过初始化')
    }
    
    // 确保滚动容器存在
    nextTick(() => {
      if (scrollContainer.value) {
        console.log('✅ 滚动容器已找到')
        console.log('✅ 滚动监听器应该已绑定到 @scroll="handleScroll"')
      } else {
        console.log('❌ 滚动容器未找到')
      }
    })
  } else {
    console.log('📄 进入翻页模式')
  }
}

// 连续模式：滚动处理
const handleScroll = async () => {
  console.log('🔄 滚动事件触发')
  
  if (!scrollContainer.value) {
    console.log('❌ 滚动容器不存在')
    return
  }
  
  const container = scrollContainer.value
  const { scrollTop, scrollHeight, clientHeight } = container
  
  console.log('📊 滚动数据:', {
    scrollTop: Math.round(scrollTop),
    scrollHeight: Math.round(scrollHeight),
    clientHeight: Math.round(clientHeight),
    distanceFromBottom: Math.round(scrollHeight - scrollTop - clientHeight),
    hasMoreChapters: hasMoreChapters.value,
    loadingMore: loadingMore.value,
    loadedChaptersCount: loadedChapters.value.length
  })
  
  // 更新进度条
  scrollProgress.value = (scrollTop / (scrollHeight - clientHeight)) * 100
  
  // 检测当前章节
  updateCurrentScrollChapter()
  
  // 滚动到底部时加载更多
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  if (distanceFromBottom <= 100) {
    console.log('📍 接近底部，距离底部:', Math.round(distanceFromBottom), 'px')
    
    if (hasMoreChapters.value) {
      console.log('✅ 有更多章节可加载')
      if (!loadingMore.value) {
        console.log('🚀 开始加载更多章节')
        await loadMoreChapters()
      } else {
        console.log('⏳ 正在加载中，跳过')
      }
    } else {
      console.log('🔚 没有更多章节了')
      
      // 连续模式下，当没有更多章节时，尝试自动爬取新章节
      if (autoCrawlEnabled.value && !loadingMore.value) {
        console.log('🔍 连续模式：尝试自动爬取新章节...')
        loadingMore.value = true
        
        try {
          await checkAndLoadNewChapters()
          
          // 检查是否有新章节被添加
          const totalChapters = chapters.value.length
          const loadedCount = loadedChapters.value.length
          
          if (totalChapters > loadedCount) {
            console.log('🎉 发现新章节！重新设置hasMoreChapters为true')
            hasMoreChapters.value = true
            
            // 立即加载新章节
            console.log('🚀 立即加载新发现的章节')
            await loadMoreChapters()
          } else {
            console.log('😔 没有发现新章节')
          }
        } catch (error) {
          console.error('❌ 自动爬取失败:', error)
        } finally {
          loadingMore.value = false
        }
      }
    }
  }
}

// 更新当前滚动章节
const updateCurrentScrollChapter = () => {
  if (!scrollContainer.value) return
  
  const container = scrollContainer.value
  const scrollTop = container.scrollTop
  const chapterElements = container.querySelectorAll('.scroll-chapter')
  
  for (let i = chapterElements.length - 1; i >= 0; i--) {
    const element = chapterElements[i]
    if (element.offsetTop <= scrollTop + 100) {
      const chapterId = element.dataset.chapterId
      currentScrollChapter.value = loadedChapters.value.find(c => c.id == chapterId)
      break
    }
  }
}

// 连续模式：加载更多章节
const loadMoreChapters = async () => {
  console.log('📚 loadMoreChapters 被调用')
  console.log('📚 当前状态:', {
    loadingMore: loadingMore.value,
    hasMoreChapters: hasMoreChapters.value,
    loadedChaptersCount: loadedChapters.value.length,
    totalChaptersCount: chapters.value.length
  })
  
  if (loadingMore.value || !hasMoreChapters.value) {
    console.log('❌ 跳过加载:', {
      loadingMore: loadingMore.value,
      hasMoreChapters: hasMoreChapters.value
    })
    return
  }
  
  loadingMore.value = true
  console.log('🔄 开始加载更多章节...')
  
  try {
    const nextIndex = loadedChapters.value.length
    const loadCount = 2 // 每次加载2章
    
    console.log('📖 加载更多章节，当前已加载:', nextIndex, '总章节数:', chapters.value.length)
    
    for (let i = nextIndex; i < Math.min(nextIndex + loadCount, chapters.value.length); i++) {
      console.log('📄 加载第', i + 1, '章')
      await loadChapterForScroll(i)
    }
    
    hasMoreChapters.value = nextIndex + loadCount < chapters.value.length
    console.log('✅ 加载完成，还有更多章节:', hasMoreChapters.value)
    
    // 连续模式下检查自动爬取 - 优化逻辑
    if (autoCrawlEnabled.value && !hasMoreChapters.value) {
      console.log('🤖 连续模式：已加载完所有现有章节，检查是否需要自动爬取新章节')
      
      // 使用简化的检查逻辑
      await checkAndLoadNewChapters()
      
      // 如果检测到新章节，重新设置hasMoreChapters
      if (chapters.value.length > nextIndex + loadCount) {
        hasMoreChapters.value = true
        console.log('🆕 检测到新章节，重新设置hasMoreChapters为true')
      }
    }
  } catch (error) {
    console.error('❌ 加载更多章节失败:', error)
    ElMessage.error('加载失败')
  } finally {
    loadingMore.value = false
    console.log('🏁 loadMoreChapters 完成')
  }
}

// 检查并执行自动爬取
const checkAndAutoCrawl = async () => {
  if (!autoCrawlEnabled.value || !novel.value) return
  
  const currentChapterNum = currentChapterIndex.value + 1
  const totalChapters = chapters.value.length
  
  // 优化触发逻辑：当到达最后几章时就触发（而不是必须超过才触发）
  const remainingChapters = totalChapters - currentChapterNum
  if (remainingChapters <= crawlAhead.value) {
    // 避免重复爬取
    if (lastCrawlChapter.value >= currentChapterNum) return
    
    console.log(`触发自动爬取: 当前第${currentChapterNum}章，总共${totalChapters}章，需要提前爬取${crawlAhead.value}章`)
    
    try {
      crawlingStatus.value = '正在自动爬取新章节...'
      lastCrawlChapter.value = currentChapterNum
      
      const response = await apiService.post('/crawler/auto-crawl/', {
        novel_id: novel.value.id,
        current_chapter: currentChapterNum,
        crawl_ahead: crawlAhead.value
      })
      
      if (response.data.success) {
        crawlingStatus.value = response.data.message || '自动爬取任务已启动'
        console.log('自动爬取任务启动:', response.data)
        ElMessage.success('正在后台爬取新章节...')
        
        // 等待一段时间后重新获取章节列表
        setTimeout(async () => {
          try {
            console.log('重新获取章节列表...')
            await fetchNovelData(novel.value.id, currentChapterNum)
            ElMessage.success('新章节已更新！')
            crawlingStatus.value = ''
          } catch (error) {
            console.error('更新章节列表失败:', error)
            crawlingStatus.value = ''
          }
        }, 8000) // 8秒后更新，给爬取更多时间
        
      } else {
        ElMessage.error(response.data.error || '自动爬取失败')
        crawlingStatus.value = '自动爬取失败'
        setTimeout(() => {
          crawlingStatus.value = ''
        }, 5000)
      }
    } catch (error) {
      console.error('自动爬取失败:', error)
      crawlingStatus.value = '自动爬取失败'
      setTimeout(() => {
        crawlingStatus.value = ''
      }, 5000)
    }
  }
}

// 刷新章节列表
const refreshChapterList = async () => {
  try {
    const novelId = Number(route.params.id)
    const chaptersResponse = await apiService.get(`/novels/${novelId}/chapters/`)
    
    let chaptersData = chaptersResponse.data || chaptersResponse
    if (chaptersData && chaptersData.results) {
      chapters.value = chaptersData.results
    } else if (Array.isArray(chaptersData)) {
      chapters.value = chaptersData
    }
    
    console.log('章节列表已刷新，当前章节数:', chapters.value.length)
  } catch (error) {
    console.error('刷新章节列表失败:', error)
  }
}

// 格式化章节内容
const formatChapterContent = (content) => {
  if (!content) return ''
  
  // 将换行符转换为段落
  return content
    .split('\n')
    .filter(line => line.trim())
    .map(line => `<p>${line.trim()}</p>`)
    .join('')
}

// 返回目录
const goBack = () => {
  router.push(`/novels/${route.params.id}`)
}

// 应用阅读设置
const applySettings = () => {
  const readerElement = document.querySelector('.novel-reader')
  if (readerElement) {
    readerElement.style.fontSize = fontSize.value + 'px'
    readerElement.style.lineHeight = lineHeight.value
    
    // 背景色设置
    const themes = {
      white: { bg: '#ffffff', color: '#333333' },
      sepia: { bg: '#f7f3e9', color: '#5c4b37' },
      dark: { bg: '#1a1a1a', color: '#e0e0e0' }
    }
    
    const theme = themes[backgroundColor.value]
    readerElement.style.backgroundColor = theme.bg
    readerElement.style.color = theme.color
  }
  
  showSettings.value = false
  ElMessage.success('设置已应用')
}

// 键盘快捷键
const handleKeyPress = (event) => {
  if (readingMode.value === 'page') {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      previousChapter()
    } else if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      nextChapter()
    }
  }
}

// 生命周期
onMounted(() => {
  fetchNovelData()
  document.addEventListener('keydown', handleKeyPress)
  loadUserSettings() // 加载用户阅读设置
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
})

// 监听阅读模式变化
watch(readingMode, (newMode) => {
  if (newMode === 'scroll') {
    nextTick(() => {
      if (scrollContainer.value) {
        scrollContainer.value.scrollTop = 0
      }
    })
  }
})
</script>

<style scoped>
.novel-reader {
  min-height: 100vh;
  background: #ffffff;
  font-size: 16px;
  line-height: 1.6;
  transition: all 0.3s ease;
  /* 为 fixed header 留出空间 */
  padding-top: 56px;
}

/* 头部样式 */
.reader-header {
  position: fixed;
  top: 64px;
  left: var(--sidebar-width, 210px);
  right: 0;
  z-index: 100;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 12px 20px;
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  box-sizing: border-box;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.novel-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 翻页模式样式 */
.page-mode {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.page-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  overflow: hidden;
}

.chapter-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.chapter-nav.bottom-nav {
  border-bottom: none;
  border-top: 1px solid #e0e0e0;
  justify-content: center;
  gap: 20px;
}

.chapter-info {
  font-weight: 500;
  color: #2c3e50;
}

.chapter-content {
  padding: 30px;
}

.chapter-title {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  text-align: center;
}

.chapter-text {
  font-size: inherit;
  line-height: inherit;
  color: #333;
}

.chapter-text :deep(p) {
  margin-bottom: 16px;
  text-indent: 2em;
}

/* 连续模式样式 */
.scroll-mode {
  position: relative;
}

.scroll-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
}

.scroll-chapter {
  background: white;
  border-radius: 8px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chapter-separator {
  height: 2px;
  background: linear-gradient(to right, transparent, #e0e0e0, transparent);
  margin: 30px 0;
}

.load-more-indicator,
.no-more-chapters {
  text-align: center;
  padding: 20px;
  color: #666;
}

/* 滚动进度条 */
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: #f0f0f0;
  z-index: 1000;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(to right, #409eff, #67c23a);
  transition: width 0.3s ease;
}

/* 当前章节指示器 */
.current-chapter-indicator {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: rgba(0,0,0,0.8);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  z-index: 100;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #666;
}

.loading-icon {
  font-size: 32px;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 阅读设置 */
.reading-settings {
  padding: 20px 0;
}

.setting-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.setting-item label {
  width: 80px;
  font-weight: 500;
}

.setting-desc {
  font-size: 12px;
  color: #666;
}

/* 自动爬取状态 */
.crawling-status {
  position: fixed;
  top: 80px;
  right: 20px;
  background: rgba(64, 158, 255, 0.9);
  color: white;
  padding: 12px 20px;
  border-radius: 20px;
  font-size: 14px;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.auto-crawl-info {
  position: fixed;
  bottom: 80px;
  right: 20px;
  z-index: 100;
}

.crawl-enabled {
  background: rgba(103, 194, 58, 0.9);
  color: white;
  padding: 8px 16px;
  border-radius: 16px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .reader-header {
    padding: 8px 16px;
    flex-direction: column;
    gap: 12px;
  }
  
  .page-mode,
  .scroll-container {
    padding: 16px;
  }
  
  .chapter-content {
    padding: 20px;
  }
  
  .chapter-nav {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
  }
  
  .chapter-nav.bottom-nav {
    flex-direction: row;
  }
}

/* 主题样式 */
.novel-reader.sepia {
  background: #f7f3e9;
  color: #5c4b37;
}

.novel-reader.sepia .page-container,
.novel-reader.sepia .scroll-chapter {
  background: #f7f3e9;
}

.novel-reader.dark {
  background: #1a1a1a;
  color: #e0e0e0;
}

.novel-reader.dark .reader-header {
  background: #2c2c2c;
  border-color: #404040;
}

.novel-reader.dark .page-container,
.novel-reader.dark .scroll-chapter {
  background: #2c2c2c;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}

.novel-reader.dark .chapter-nav {
  background: #3c3c3c;
  border-color: #404040;
}
</style>
