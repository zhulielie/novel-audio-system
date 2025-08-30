#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
统一爬虫模块（后端集成版）
================================================================================
用途:
    汇聚项目中的爬虫能力，结合Django模型进行持久化，支持来源站点、小说、章节等
    实体的统一采集与入库，兼顾安全请求、反爬处理与限流。
关键能力:
    - 统一的 requests 会话与报头
    - 反爬虫检测与重试等待
    - 解析工具与字段清洗
    - 与 `novels` 应用模型对接持久化
适用场景:
    - 后端批处理任务
    - 管理端触发的采集作业
模块路径: backend/crawlers
版本: v1.0
作者: 小说系统
"""
import os
import sys
import django
import time
import requests
import random
import logging
import re
import asyncio
from typing import List, Dict, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not available, using requests only")

# 设置Django环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novel_audio_system.settings')
django.setup()

from novels.models import Novel, NovelSource, Chapter, NovelSourceRelation

logger = logging.getLogger(__name__)


class UnifiedCrawler:
    """统一爬虫类 - 整合所有爬虫功能"""
    
    def __init__(self, min_delay: float = 2.0, max_delay: float = 8.0):
        """初始化爬虫
        
        Args:
            min_delay: 最小延时(秒)
            max_delay: 最大延时(秒)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.delay = max_delay  # 默认使用最大延时
        print(f"🕷️ 统一爬虫初始化完成 (延时: {min_delay}-{max_delay}秒)")
    
    def safe_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """安全请求页面，支持重试和反爬虫检测"""
        # 如果是和图书网且Playwright可用，优先使用Playwright
        if PLAYWRIGHT_AVAILABLE and "hetushu.com" in url:
            try:
                html_content = asyncio.run(self._playwright_request(url))
                if html_content:
                    # 创建一个模拟的Response对象
                    class MockResponse:
                        def __init__(self, text, status_code=200):
                            self.text = text
                            self.status_code = status_code
                            self.content = text.encode('utf-8')
                    return MockResponse(html_content)
            except Exception as e:
                print(f"⚠️ Playwright请求失败，回退到requests: {str(e)}")
        
        # 使用原有的requests方法
        for attempt in range(max_retries):
            try:
                print(f"🌐 请求页面: {url} (尝试 {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=30)
                
                # 检测反爬虫页面
                if response.status_code == 403:
                    print(f"⚠️ 403 Forbidden - 可能被反爬虫系统拦截")
                    if attempt < max_retries - 1:
                        time.sleep(self.delay)
                        continue
                    return None
                
                # 检测Cloudflare等反爬虫页面
                if "Just a moment" in response.text or "Checking your browser" in response.text:
                    print(f"⚠️ 检测到反爬虫页面 - Cloudflare或类似服务")
                    if attempt < max_retries - 1:
                        time.sleep(self.delay)
                        continue
                    return None
                
                if response.status_code == 200:
                    print(f"✅ 页面请求成功: {len(response.text)} 字符")
                    return response
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
                
            if attempt < max_retries - 1:
                print(f"⏳ 等待 {self.delay} 秒后重试...")
                time.sleep(self.delay)
        
        print(f"❌ 所有重试失败")
        return None
    
    async def _playwright_request(self, url: str) -> Optional[str]:
        """使用Playwright请求页面"""
        print(f"🎭 使用Playwright请求: {url}")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                # 设置超时
                page.set_default_timeout(60000)  # 增加超时时间
                
                # 访问页面
                await page.goto(url, wait_until='domcontentloaded')
                
                # 检查是否遇到Cloudflare保护
                title = await page.title()
                if "Just a moment" in title or "Checking your browser" in title:
                    print(f"⏳ 检测到Cloudflare保护，等待验证完成...")
                    
                    # 等待Cloudflare验证完成，最多等待30秒
                    try:
                        await page.wait_for_function(
                            "document.title !== 'Just a moment...' && !document.title.includes('Checking')",
                            timeout=30000
                        )
                        print(f"✅ Cloudflare验证完成")
                    except Exception:
                        print(f"⚠️ Cloudflare验证超时，继续尝试获取内容")
                
                # 额外等待页面完全加载
                await page.wait_for_timeout(3000)
                
                # 获取页面内容
                content = await page.content()
                
                # 再次检查内容是否有效
                if "Just a moment" in content or "Checking your browser" in content:
                    print(f"⚠️ 页面仍显示Cloudflare保护页面")
                    # 尝试等待更长时间
                    await page.wait_for_timeout(5000)
                    content = await page.content()
                
                await browser.close()
                
                print(f"✅ Playwright请求成功: {len(content)} 字符")
                return content
                
        except Exception as e:
            print(f"❌ Playwright请求失败: {str(e)}")
            return None
    
    def random_delay(self):
        """随机延时，避免被检测"""
        delay = random.uniform(self.min_delay, self.max_delay)  # 在[min,max]间取随机延时
        print(f"⏳ 随机延时 {delay:.1f} 秒")
        time.sleep(delay)
    
    def parse_novel_info(self, url: str) -> Optional[Dict]:
        """解析小说基本信息
        
        Args:
            url: 小说主页URL
            
        Returns:
            包含小说信息的字典或None
        """
        print(f"📖 开始解析小说信息: {url}")
        
        response = self.safe_request(url)  # 使用带重试与反爬检测的安全请求
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')  # 解析HTML，后续用多策略提取
            
            # 和图书网解析逻辑
            if 'hetushu.com' in url:  # 针对和图书站点的专用解析
                return self._parse_hetushu_info(soup, url)
            # 可以添加其他网站的解析逻辑
            else:
                return self._parse_generic_info(soup, url)
                
        except Exception as e:
            print(f"❌ 解析小说信息失败: {str(e)}")
            return None
    
    def _parse_hetushu_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """解析和图书网小说信息"""
        try:
            # 获取小说标题
            title_elem = soup.find('h1') or soup.find('title')  # 标题优先从h1获取，回退到<title>
            title = title_elem.get_text().strip() if title_elem else "未知标题"
            
            # 清理标题
            title = re.sub(r'[_\-\s]*和图书.*$', '', title).strip()  # 去除站点附加信息
            title = re.sub(r'[_\-\s]*最新章节.*$', '', title).strip()
            
            # 获取作者
            author = "未知作者"
            author_patterns = [  # 多种作者位置的容错匹配
                soup.find('meta', {'name': 'author'}),
                soup.find(text=re.compile(r'作者[:：]\s*(.+)')),
                soup.find('span', string=re.compile(r'作者')),
            ]
            
            for pattern in author_patterns:
                if pattern:
                    if hasattr(pattern, 'get'):
                        author = pattern.get('content', '').strip()
                    else:
                        match = re.search(r'作者[:：]\s*(.+)', str(pattern))
                        if match:
                            author = match.group(1).strip()
                    if author and author != "未知作者":
                        break
            
            # 获取简介
            description = ""
            desc_elem = soup.find('div', class_='intro') or soup.find('div', id='intro')  # 简介常见位置
            if desc_elem:
                description = desc_elem.get_text().strip()
            
            # 获取章节列表链接
            chapter_links = []
            for link in soup.find_all('a', href=re.compile(r'/book/\d+/\d+.*\.html')):  # 章节URL样式
                href = urljoin(url, link['href'])
                chapter_title = link.get_text().strip()
                if chapter_title and href not in [c['url'] for c in chapter_links]:
                    chapter_links.append({
                        'title': chapter_title,
                        'url': href
                    })
            
            result = {
                'title': title,
                'author': author,
                'description': description,
                'source_url': url,
                'chapter_count': len(chapter_links),
                'chapters': chapter_links[:50]  # 限制返回前50章
            }
            
            print(f"✅ 和图书网解析成功: {title} by {author} ({len(chapter_links)}章)")
            return result
            
        except Exception as e:
            print(f"❌ 和图书网解析失败: {str(e)}")
            return None
    
    def _parse_generic_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """通用网站解析逻辑"""
        try:
            # 通用标题解析
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "未知标题"
            
            # 通用作者解析
            author = "未知作者"
            
            result = {
                'title': title,
                'author': author,
                'description': "",
                'source_url': url,
                'chapter_count': 0,
                'chapters': []
            }
            
            print(f"✅ 通用解析完成: {title}")
            return result
            
        except Exception as e:
            print(f"❌ 通用解析失败: {str(e)}")
            return None
    
    def crawl_chapter_content(self, chapter_url: str) -> Optional[Dict]:
        """爬取单个章节内容
        
        Args:
            chapter_url: 章节URL
            
        Returns:
            包含章节信息的字典或None
        """
        print(f"📄 开始爬取章节: {chapter_url}")
        
        response = self.safe_request(chapter_url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if 'hetushu.com' in chapter_url:
                return self._parse_hetushu_chapter(soup, chapter_url)
            else:
                return self._parse_generic_chapter(soup, chapter_url)
                
        except Exception as e:
            print(f"❌ 章节解析失败: {str(e)}")
            return None
    
    def _parse_hetushu_chapter(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """解析和图书网章节内容"""
        try:
            # 获取章节标题
            title_elem = soup.find('h1') or soup.find('h2')
            title = title_elem.get_text().strip() if title_elem else "未知章节"
            
            # 获取章节内容
            content = ""
            content_selectors = [
                'div#content',
                'div.content',
                'div#chapter_content',
                'div.chapter_content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    break
            
            if not content:
                # 尝试其他方法获取内容
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            result = {
                'title': title,
                'content': content,
                'source_url': url,
                'word_count': len(content)
            }
            
            print(f"✅ 章节解析成功: {title} ({len(content)}字)")
            return result
            
        except Exception as e:
            print(f"❌ 和图书网章节解析失败: {str(e)}")
            return None
    
    def _parse_generic_chapter(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """通用章节解析逻辑"""
        try:
            title_elem = soup.find('h1') or soup.find('h2')
            title = title_elem.get_text().strip() if title_elem else "未知章节"
            
            # 尝试获取内容
            content = soup.get_text().strip()
            
            result = {
                'title': title,
                'content': content,
                'source_url': url,
                'word_count': len(content)
            }
            
            print(f"✅ 通用章节解析完成: {title}")
            return result
            
        except Exception as e:
            print(f"❌ 通用章节解析失败: {str(e)}")
            return None
    
    def batch_crawl_chapters(self, novel_info: Dict, max_chapters: int = 20) -> List[Dict]:
        """批量爬取章节
        
        Args:
            novel_info: 小说信息字典
            max_chapters: 最大章节数
            
        Returns:
            章节列表
        """
        print(f"📚 开始批量爬取章节，最多 {max_chapters} 章")
        
        chapters = []
        chapter_links = novel_info.get('chapters', [])[:max_chapters]
        
        for i, chapter_link in enumerate(chapter_links, 1):
            print(f"📖 爬取第 {i}/{len(chapter_links)} 章: {chapter_link['title']}")
            
            chapter_data = self.crawl_chapter_content(chapter_link['url'])
            if chapter_data:
                chapters.append(chapter_data)
            
            # 随机延时避免被封
            if i < len(chapter_links):
                self.random_delay()
        
        print(f"✅ 批量爬取完成，成功获取 {len(chapters)} 章")
        return chapters
    
    def save_to_database(self, novel_info: Dict, chapters: List[Dict], source_id: int = 1) -> Optional[Novel]:
        """保存到数据库
        
        Args:
            novel_info: 小说信息
            chapters: 章节列表
            source_id: 来源ID
            
        Returns:
            Novel对象或None
        """
        try:
            print(f"💾 开始保存到数据库: {novel_info['title']}")
            
            # 创建或获取小说
            novel, created = Novel.objects.get_or_create(
                title=novel_info['title'],
                defaults={
                    'author': novel_info['author'],
                    'description': novel_info.get('description', ''),
                    'status': 'ongoing'
                }
            )
            
            if created:
                print(f"✅ 创建新小说: {novel.title}")
            else:
                print(f"📖 使用现有小说: {novel.title}")
            
            # 保存章节
            saved_count = 0
            for chapter_data in chapters:
                chapter, chapter_created = Chapter.objects.get_or_create(
                    novel=novel,
                    title=chapter_data['title'],
                    defaults={
                        'content': chapter_data['content'],
                        'word_count': chapter_data['word_count'],
                        'source_url': chapter_data['source_url']
                    }
                )
                
                if chapter_created:
                    saved_count += 1
            
            print(f"✅ 保存完成: {saved_count} 个新章节")
            return novel
            
        except Exception as e:
            print(f"❌ 数据库保存失败: {str(e)}")
            return None


# 为了兼容性，保留原有的类名
class HetushuCrawler(UnifiedCrawler):
    """和图书网爬虫 - 兼容性别名"""
    pass


# 智能批量爬虫 - 兼容性别名
class IntelligentBatchCrawler(UnifiedCrawler):
    """智能批量爬虫 - 兼容性别名"""
    pass
