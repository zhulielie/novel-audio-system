"""
服务化章节提取器（整合版）：从 legacy_pachong/chapter_extractor.py 复制并内聚到 services。
"""

import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
import argparse
import logging
from pathlib import Path


class ChapterExtractor:
    """章节列表提取器：从目录页解析出章节标题与URL列表"""
    
    def __init__(self, config_file="enhanced_downloader_config.json"):
        self.config = self.load_config(config_file)
        self.current_site = None
        self.site_config = None
        self.setup_logging()
    
    def load_config(self, config_file):
        """加载配置文件：读取增强版配置（含日志级别等）"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 不存在")
            return None
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            return None
    
    def setup_logging(self):
        """设置日志：按配置级别输出基础运行信息"""
        if not self.config:
            return
        
        log_level = self.config.get('global_settings', {}).get('log_level', 'info').upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def detect_site(self, url):
        """根据URL自动检测网站类型：域名匹配配置中base_url"""
        if not self.config:
            return None
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for site_key, site_config in self.config.get('sites', {}).items():
            site_domain = urlparse(site_config['base_url']).netloc.lower()
            if site_domain in domain or domain in site_domain:
                return site_key
        
        return None
    
    def set_site(self, site_key):
        """设置当前网站配置：记录current_site与site_config"""
        if not self.config or site_key not in self.config.get('sites', {}):
            raise ValueError(f"不支持的网站: {site_key}")
        
        self.current_site = site_key
        self.site_config = self.config['sites'][site_key]
        self.logger.info(f"设置网站配置: {self.site_config['name']}")
    
    def clean_chapter_title(self, title):
        """清理章节标题：移除编号/冗余词，保持简洁"""
        if not title or not self.site_config:
            return title
        
        cleanup_config = self.site_config.get('content_processing', {}).get('title_cleanup', {})
        
        # 移除指定模式
        for pattern in cleanup_config.get('remove_patterns', []):
            title = re.sub(pattern, '', title)
        
        # 替换指定模式
        for pattern, replacement in cleanup_config.get('replace_patterns', {}).items():
            title = re.sub(pattern, replacement, title)
        
        return title.strip()
    
    def extract_chapter_id(self, url):
        """从URL提取章节ID：多模式回退匹配，取首个命中"""
        # 尝试从URL中提取数字ID
        patterns = [
            r'/(\d+)\.html?$',  # 标准数字ID
            r'/chapter/(\d+)',   # chapter/数字
            r'/read/\d+/(\d+)',  # read/书籍ID/章节ID
            r'chapter_id=(\d+)', # 查询参数
            r'id=(\d+)'          # 通用ID参数
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 如果没有找到数字ID，使用URL的最后一部分
        try:
            return url.split('/')[-1].split('.')[0]
        except:
            return str(hash(url) % 100000)
    
    async def extract_chapters_from_page(self, page, index_url):
        """从目录页面提取章节列表"""
        try:
            # 访问目录页面
            await page.goto(index_url, 
                          wait_until=self.site_config['request_config'].get('wait_for', 'networkidle'),
                          timeout=self.site_config['request_config'].get('timeout', 30000))
            
            # 等待页面加载
            await page.wait_for_timeout(2000)
            
            # 获取章节列表选择器
            chapter_list_selector = self.site_config['selectors'].get('chapter_list')
            if not chapter_list_selector:
                # 使用通用选择器作为备选
                chapter_list_selector = 'a[href*="chapter"], a[href*="read"], .chapter-list a, .list a'
                self.logger.warning("未配置章节列表选择器，使用通用选择器")
            
            # 查找所有章节链接
            chapter_elements = await page.query_selector_all(chapter_list_selector)
            
            if not chapter_elements:
                self.logger.warning(f"未找到章节链接，选择器: {chapter_list_selector}")
                return []
            
            chapters = []
            base_url = self.site_config.get('url_patterns', {}).get('relative_url_base', self.site_config['base_url'])
            
            for i, element in enumerate(chapter_elements):
                try:
                    # 获取章节标题
                    title = await element.text_content()
                    if not title or not title.strip():
                        continue
                    
                    title = title.strip()
                    try:
                        title = title.encode('utf-8').decode('utf-8')
                        title = title.replace('\u00a0', ' ')
                        title = title.replace('\u3000', ' ')
                        title = title.replace('\ufeff', '')
                    except:
                        pass
                    
                    # 获取章节链接
                    href = await element.get_attribute('href')
                    if not href:
                        continue
                    
                    # 处理相对链接
                    if href.startswith('/'):
                        chapter_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        chapter_url = href
                    else:
                        chapter_url = urljoin(index_url, href)
                    
                    clean_title = self.clean_chapter_title(title)
                    chapter_id = self.extract_chapter_id(chapter_url)
                    
                    chapters.append({
                        'id': chapter_id,
                        'title': clean_title or title,
                        'original_title': title,
                        'url': chapter_url,
                        'index': i + 1
                    })
                except Exception as e:
                    self.logger.warning(f"处理章节元素失败: {e}")
                    continue
            
            self.logger.info(f"成功提取 {len(chapters)} 个章节")
            return chapters
            
        except Exception as e:
            self.logger.error(f"提取章节列表失败: {e}")
            return []
    
    async def extract_book_info(self, page, index_url):
        """提取书籍信息"""
        try:
            book_info = {
                'title': '未知书籍',
                'author': '未知作者',
                'description': '',
                'url': index_url,
                'site': self.site_config['name']
            }
            
            title_selectors = ['h1', '.book-title', '.bookname h1', '.info h1', '#info h1', '.book-info h1', 'title', '.novel-title', '.book-name']
            for selector in title_selectors:
                try:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        title_text = await title_element.text_content()
                        if title_text and title_text.strip():
                            title_text = title_text.strip()
                            try:
                                title_text = title_text.encode('utf-8').decode('utf-8')
                                title_text = title_text.replace('\u00a0', ' ')
                                title_text = title_text.replace('\u3000', ' ')
                                title_text = title_text.replace('\ufeff', '')
                            except:
                                pass
                            book_info['title'] = title_text
                            break
                except:
                    continue
            
            author_selectors = ['.author', '.book-author', '#info p:nth-child(2)', '.info .author', '[class*="author"]']
            for selector in author_selectors:
                try:
                    author_element = await page.query_selector(selector)
                    if author_element:
                        author_text = await author_element.text_content()
                        if author_text and author_text.strip():
                            author_text = author_text.strip()
                            author_text = author_text.replace('\u00a0', ' ')
                            author_text = author_text.replace('\u3000', ' ')
                            author_text = author_text.replace('\ufeff', '')
                            author = re.sub(r'^作者[：:]*\s*', '', author_text)
                            book_info['author'] = author
                            break
                except:
                    continue
            
            desc_selectors = ['.intro', '.description', '#intro', '.book-desc', '.summary']
            for selector in desc_selectors:
                try:
                    desc_element = await page.query_selector(selector)
                    if desc_element:
                        desc_text = await desc_element.text_content()
                        if desc_text and desc_text.strip():
                            desc_text = desc_text.strip()
                            desc_text = desc_text.replace('\u00a0', ' ')
                            desc_text = desc_text.replace('\u3000', ' ')
                            desc_text = desc_text.replace('\ufeff', '')
                            book_info['description'] = desc_text[:500]
                            break
                except:
                    continue
            
            return book_info
        except Exception as e:
            self.logger.warning(f"提取书籍信息失败: {e}")
            return {
                'title': '未知书籍',
                'author': '未知作者',
                'description': '',
                'url': index_url,
                'site': self.site_config['name']
            }
    
    async def extract_chapters(self, index_url, site_key=None, output_file=None):
        """提取章节列表的主函数"""
        if not self.config:
            print("配置文件加载失败")
            return None
        
        if site_key:
            self.set_site(site_key)
        else:
            detected_site = self.detect_site(index_url)
            if detected_site:
                self.set_site(detected_site)
            else:
                print(f"无法识别网站类型，请手动指定 --site 参数")
                print("支持的网站:")
                for key, config in self.config.get('sites', {}).items():
                    print(f"  {key}: {config['name']}")
                return None
        
        self.logger.info(f"开始提取章节列表: {index_url}")
        browser_config = self.config.get('global_settings', {}).get('browser_config', {})
        
        async with async_playwright() as p:
            # 准备浏览器启动参数
            launch_options = {
                'headless': browser_config.get('headless', True)
            }
            
            # 添加代理配置（如果启用）
            advanced_features = self.config.get('advanced_features', {})
            if advanced_features.get('use_proxy', False):
                proxy_config = advanced_features.get('proxy_config', {})
                proxy_server = proxy_config.get('server', '')
                if proxy_server:
                    launch_options['proxy'] = {'server': proxy_server}
                    self.logger.info(f"使用代理: {proxy_server}")
            
            browser = await p.chromium.launch(**launch_options)
            context_options = {}
            if 'viewport' in browser_config:
                context_options['viewport'] = browser_config['viewport']
            if 'locale' in browser_config:
                context_options['locale'] = browser_config['locale']
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            headers = self.site_config['request_config'].get('headers', {})
            if headers:
                await page.set_extra_http_headers(headers)
            
            try:
                book_info = await self.extract_book_info(page, index_url)
                chapters = await self.extract_chapters_from_page(page, index_url)
                if not chapters:
                    self.logger.error("未能提取到任何章节")
                    return None
                result = {
                    'book_info': book_info,
                    'chapters': chapters,
                    'total_chapters': len(chapters),
                    'extraction_time': self.get_current_time(),
                    'site_config': {
                        'site_key': self.current_site,
                        'site_name': self.site_config['name'],
                        'base_url': self.site_config['base_url']
                    }
                }
                if output_file:
                    self.save_chapters_to_file(result, output_file)
                await browser.close()
                self.logger.info(f"章节提取完成: {len(chapters)} 个章节")
                return result
            except Exception as e:
                self.logger.error(f"提取过程中发生错误: {e}")
                await browser.close()
                return None
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def save_chapters_to_file(self, result, output_file):
        """保存章节列表到文件"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.info(f"章节列表已保存到: {output_file}")
        except Exception as e:
            self.logger.error(f"保存文件失败: {e}")
    
    def print_chapters_summary(self, result):
        """打印章节摘要"""
        if not result:
            return
        book_info = result['book_info']
        chapters = result['chapters']
        print(f"\n书籍信息:")
        print(f"  书名: {book_info['title']}")
        print(f"  作者: {book_info['author']}")
        print(f"  网站: {book_info['site']}")
        print(f"  章节数: {len(chapters)}")
        if chapters:
            print(f"\n章节预览 (前5章):")
            for i, chapter in enumerate(chapters[:5]):
                print(f"  {i+1:3d}. {chapter['title']}")
            if len(chapters) > 5:
                print(f"  ... 还有 {len(chapters) - 5} 章")


__all__ = ["ChapterExtractor"]


