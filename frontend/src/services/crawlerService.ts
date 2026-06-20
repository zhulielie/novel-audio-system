/**
 * 爬虫服务 - 专门为爬虫功能提供的高级服务
 * 基于现有的API接口，提供了更方便的调用方式
 */

// @ts-nocheck
import { apiService } from './api'

// 爬虫状态接口
export interface CrawlerStatus {
  total_relations: number
  active_relations: number
  recent_synced: number
  supported_sites: string[]
}

// URL分析结果接口
export interface UrlAnalysisResult {
  success: boolean
  title?: string
  author?: string
  chapter_count?: number
  description?: string
  catalog_url?: string
  message?: string
  error?: string
}

// 批量导入参数接口
export interface BatchImportParams {
  source_url: string
  novel_title: string
  novel_author?: string
  source_id?: number
  max_chapters?: number
  start_chapter?: number
  end_chapter?: number
  speed?: 'slow' | 'normal' | 'fast'
}

// 批量导入结果接口
export interface BatchImportResult {
  success: boolean
  novel_id?: number
  novel_title?: string
  chapters_imported?: number
  total_found?: number
  skipped_count?: number
  failed_count?: number
  message?: string
  error?: string
}

// 高级爬取选项接口
export interface AdvancedCrawlOptions {
  max_chapters?: number
  start_chapter?: number
  overwrite_existing?: boolean
  delay_between_requests?: number
  retry_count?: number
}

// 爬虫服务类
export class CrawlerService {

  /**
   * 获取爬虫状态统计
   */
  static async getStatus(): Promise<CrawlerStatus> {
    try {
      const response = await apiService.crawler.getStatus()
      return response
    } catch (error) {
      console.error('获取爬虫状态失败:', error)
      throw error
    }
  }

  /**
   * 分析小说URL
   * @param url 小说URL
   */
  static async analyzeUrl(url: string): Promise<UrlAnalysisResult> {
    try {
      const response = await apiService.crawler.analyzeUrl(url)
      return {
        success: response.success || false,
        title: response.title,
        author: response.author,
        chapter_count: response.chapter_count,
        description: response.description,
        catalog_url: response.catalog_url,
        message: response.message,
        error: response.error
      }
    } catch (error) {
      console.error('URL分析失败:', error)
      return {
        success: false,
        error: error.message || 'URL分析失败'
      }
    }
  }

  /**
   * 智能批量导入小说
   * @param params 导入参数
   */
  static async batchImport(params: BatchImportParams): Promise<BatchImportResult> {
    try {
      const response = await apiService.crawler.batchImport(params)
      return {
        success: response.success || false,
        novel_id: response.novel_id,
        novel_title: response.novel_title,
        chapters_imported: response.chapters_imported,
        total_found: response.total_found,
        skipped_count: response.skipped_count,
        failed_count: response.failed_count,
        message: response.message,
        error: response.error
      }
    } catch (error) {
      console.error('批量导入失败:', error)
      return {
        success: false,
        error: error.message || '批量导入失败'
      }
    }
  }

  /**
   * 基础爬取功能
   * @param relationId 小说来源关系ID
   */
  static async basicCrawl(relationId: number): Promise<any> {
    try {
      const response = await apiService.crawler.basicCrawl(relationId)
      return response
    } catch (error) {
      console.error('基础爬取失败:', error)
      throw error
    }
  }

  /**
   * 高级爬取功能
   * @param relationId 小说来源关系ID
   * @param options 高级选项
   */
  static async advancedCrawl(relationId: number, options: AdvancedCrawlOptions = {}): Promise<any> {
    try {
      const response = await apiService.crawler.advancedCrawl(relationId, options)
      return response
    } catch (error) {
      console.error('高级爬取失败:', error)
      throw error
    }
  }

  /**
   * 获取小说章节目录
   * @param novelId 小说ID
   */
  static async getChapterDirectory(novelId: number): Promise<any> {
    try {
      const response = await apiService.crawler.getChapterDirectory(novelId)
      return response
    } catch (error) {
      console.error('获取章节目录失败:', error)
      throw error
    }
  }

  /**
   * 格式化章节标题
   * @param novelId 小说ID
   * @param format 格式类型：'chinese' | 'arabic'
   */
  static async formatChapterTitles(novelId: number, format: 'chinese' | 'arabic' = 'chinese'): Promise<any> {
    try {
      const response = await apiService.crawler.formatChapterTitles(novelId, format)
      return response
    } catch (error) {
      console.error('格式化章节标题失败:', error)
      throw error
    }
  }

  /**
   * 搜索章节内容
   * @param query 搜索关键词
   * @param novelId 可选的小说ID，用于限定搜索范围
   */
  static async searchChapters(query: string, novelId?: number): Promise<any> {
    try {
      const response = await apiService.crawler.searchChapters(query, novelId)
      return response
    } catch (error) {
      console.error('搜索章节失败:', error)
      throw error
    }
  }

  /**
   * 便捷的单步导入方法
   * 结合URL分析和批量导入的便捷方法
   * @param url 小说URL
   * @param options 导入选项
   */
  static async quickImport(url: string, options: {
    max_chapters?: number
    start_chapter?: number
    end_chapter?: number
    speed?: 'slow' | 'normal' | 'fast'
  } = {}): Promise<BatchImportResult> {
    try {
      // 1. 先分析URL
      const analysis = await this.analyzeUrl(url)

      if (!analysis.success) {
        return {
          success: false,
          error: analysis.error || 'URL分析失败'
        }
      }

      // 2. 执行批量导入
      const importParams: BatchImportParams = {
        source_url: url,
        novel_title: analysis.title || '未知小说',
        novel_author: analysis.author,
        source_id: 1, // 默认使用和图书网
        ...options
      }

      const result = await this.batchImport(importParams)
      return result

    } catch (error) {
      console.error('快速导入失败:', error)
      return {
        success: false,
        error: error.message || '快速导入失败'
      }
    }
  }

  /**
   * 获取支持的网站列表
   */
  static getSupportedSites(): string[] {
    return [
      'hetushu.com - 和图书网',
      'biquge.com - 笔趣阁',
      'qidian.com - 起点中文网',
      'zongheng.com - 纵横中文网',
      '通用小说网站 (自动识别)'
    ]
  }

  /**
   * 获取推荐的爬取速度设置
   */
  static getSpeedRecommendations(): { [key: string]: { label: string; description: string } } {
    return {
      slow: {
        label: '🐌 慢速',
        description: '3-6秒延时，适合大量数据抓取，较为稳定'
      },
      normal: {
        label: '⚡ 正常',
        description: '2-5秒延时，平衡速度和稳定性'
      },
      fast: {
        label: '🚀 快速',
        description: '1-3秒延时，快速抓取但可能被限制'
      }
    }
  }
}

export default CrawlerService
