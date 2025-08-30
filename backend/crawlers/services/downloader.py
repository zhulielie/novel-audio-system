"""
================================================================================
通用小说下载器（模块说明）
================================================================================
用途:
    通过配置驱动，按站点规则批量抓取章节内容并保存为文本文件，同时统计与生成下载报告。
关键能力:
    - 多站点配置（选择器/请求/清洗/命名）
    - Playwright 异步抓取与重试机制
    - 清理内容中的链接乱码、空白与广告文本
    - 目录组织与文件命名规范化
适用场景:
    - 批量下载单本小说的多个章节
    - 基于 JSON 章节列表的离线内容采集
模块路径: backend/legacy_pachong
版本: v1.0
作者: 小说系统
"""

import asyncio
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import argparse
import sys
import logging
from urllib.parse import urljoin, urlparse

class UniversalNovelDownloader:
    """通用小说下载器 - 支持多网站配置"""
    
    def __init__(self, config_file="downloader_config.json"):
        self.config = self.load_config(config_file)
        self.current_site = None
        self.site_config = None
        self.download_report = []
        self.setup_logging()
        
    def load_config(self, config_file):
        """加载配置文件：读取JSON并返回配置字典"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 不存在")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """设置日志：控制台+文件输出，级别取自配置"""
        log_level = self.config['global_settings'].get('log_level', 'info').upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('downloader.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def detect_site(self, url):
        """根据URL自动检测网站类型：用域名匹配配置中的base_url"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for site_key, site_config in self.config['sites'].items():
            site_domain = urlparse(site_config['base_url']).netloc.lower()
            if site_domain in domain or domain in site_domain:
                return site_key
        
        return None
    
    def set_site(self, site_key):
        """设置当前网站配置：确定 current_site 与 site_config"""
        if site_key not in self.config['sites']:
            raise ValueError(f"不支持的网站: {site_key}")
        
        self.current_site = site_key
        self.site_config = self.config['sites'][site_key]
        self.logger.info(f"设置网站配置: {self.site_config['name']}")
    
    def clean_filename(self, filename):
        """根据配置清理文件名：移除/替换不需要的模式并截断长度"""
        if not self.site_config:
            return filename
        
        cleanup_config = self.site_config.get('content_processing', {}).get('title_cleanup', {})
        
        # 移除指定模式
        for pattern in cleanup_config.get('remove_patterns', []):
            filename = re.sub(pattern, '', filename)
        
        # 替换指定模式
        for pattern, replacement in cleanup_config.get('replace_patterns', {}).items():
            filename = re.sub(pattern, replacement, filename)
        
        # 限制文件名长度
        max_length = self.site_config.get('file_naming', {}).get('max_filename_length', 200)
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        return filename.strip()
    
    def clean_content(self, content):
        """根据配置清理内容：去广告与链接乱码，保持段落结构"""
        if not self.site_config:
            return content
        
        cleanup_config = self.site_config.get('content_processing', {}).get('content_cleanup', {})
        
        # 移除指定模式
        for pattern in cleanup_config.get('remove_patterns', []):
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # 清理各种形式的链接乱码（包括随机生成的变体）
        # 清理以中文字符开头后跟链接的模式
        content = re.sub(r'[\u4e00-\u9fff]https?://[^\s]*', lambda m: m.group(0)[0], content)
        # 清理各种字符编码的http/https链接
        content = re.sub(r'[hｈ][tｔ][tｔ][pｐ][sｓ]?://[^\s]*', '', content)
        content = re.sub(r'https?://[mｍ]\.[^\s]*', '', content)
        content = re.sub(r'https?://[^\s]*\.(com|net|org|cn)[^\s]*', '', content)
        # 清理包含域名特征的乱码
        content = re.sub(r'[^\s]*\.(com|net|org|cn)[^\s]*', '', content)
        # 清理包含www的乱码
        content = re.sub(r'[^\s]*www\.[^\s]*', '', content)
        # 清理混合字符的链接残留
        content = re.sub(r'[a-zA-Z\u4e00-\u9fff]*[hｈ][tｔ][tｔ][pｐ][sｓ][^\s]*', '', content)
        
        # 标准化空白字符，但保持段落结构
        if cleanup_config.get('normalize_whitespace', False):
            # 保持换行符，只清理行内的多余空格
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # 清理每行内部的多余空格，但保留行的结构
                cleaned_line = re.sub(r'[ \t]+', ' ', line.strip())
                cleaned_lines.append(cleaned_line)
            content = '\n'.join(cleaned_lines)
            # 清理多余的空行，但保持段落分隔
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content.strip()
    
    async def get_chapter_content(self, page, chapter_url, chapter_title=""):
        """获取章节内容：访问→定位→JS提取→清理→校验→返回结构体"""
        try:
            # 访问章节页面
            await page.goto(chapter_url, 
                          wait_until=self.site_config['request_config'].get('wait_for', 'networkidle'),
                          timeout=self.site_config['request_config'].get('timeout', 30000))
            
            # 等待页面加载
            await page.wait_for_timeout(1000)
            
            # 获取章节标题
            title = chapter_title
            title_selector = self.site_config['selectors'].get('title')
            if title_selector:
                try:
                    title_element = await page.query_selector(title_selector)
                    if title_element:
                        page_title = await title_element.text_content()
                        if page_title and page_title.strip():
                            title = page_title.strip()
                except Exception as e:
                    self.logger.warning(f"标题提取失败: {e}")
            
            # 获取章节内容
            content_selector = self.site_config['selectors'].get('content')
            if not content_selector:
                raise Exception("未配置内容选择器")
            
            content_element = await page.query_selector(content_selector)
            if content_element:
                self.logger.info("找到内容元素，开始提取内容")
                
                # 使用JavaScript提取，保持段落结构和换行
                try:
                    content = await page.evaluate('''
                        (selector) => {
                            const element = document.querySelector(selector);
                            if (!element) return null;
                            
                            // 递归提取文本内容，保持段落结构
                            function extractTextWithStructure(node) {
                                let result = '';
                                
                                for (let child of node.childNodes) {
                                    if (child.nodeType === Node.TEXT_NODE) {
                                        const text = child.textContent.trim();
                                        if (text) {
                                            result += text;
                                        }
                                    } else if (child.nodeType === Node.ELEMENT_NODE) {
                                        const tagName = child.tagName.toLowerCase();
                                        
                                        // 对于块级元素，添加换行
                                        if (['div', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
                                            const childText = extractTextWithStructure(child);
                                            if (childText.trim()) {
                                                result += '\\n' + childText.trim() + '\\n';
                                            } else if (tagName === 'br') {
                                                result += '\\n';
                                            }
                                        } else {
                                            // 对于行内元素，直接提取文本
                                            const childText = extractTextWithStructure(child);
                                            if (childText.trim()) {
                                                result += childText;
                                            }
                                        }
                                    }
                                }
                                
                                return result;
                            }
                            
                            const rawText = extractTextWithStructure(element);
                            // 清理多余的换行，但保持段落结构
                            return rawText.replace(/\\n\\s*\\n\\s*\\n+/g, '\\n\\n').trim();
                        }
                    ''', content_selector)
                    self.logger.info(f"JavaScript提取成功，内容长度: {len(content) if content else 0}")
                    
                    if not content:
                        self.logger.warning("JavaScript提取返回空内容，尝试简单文本提取")
                        # 备用方案：简单的文本提取
                        content = await content_element.text_content()
                        self.logger.info(f"简单提取结果，内容长度: {len(content) if content else 0}")
                        
                except Exception as extract_error:
                    self.logger.error(f"内容提取失败: {extract_error}")
                    content = None
                
                if content and content.strip():
                    self.logger.info(f"原始内容长度: {len(content)}")
                    self.logger.info(f"原始内容前200字符: {content[:200]}")
                    
                    # 清理内容
                    content = self.clean_content(content)
                    self.logger.info(f"清理后内容长度: {len(content)}")
                    self.logger.info(f"清理后内容前200字符: {content[:200]}")
                    
                    # 内容验证
                    if self.validate_content(content):
                        self.logger.info("内容验证通过")
                        return {
                            'title': title,
                            'content': content,
                            'url': chapter_url,
                            'status': '成功'
                        }
                    else:
                        self.logger.warning("内容验证失败")
                        raise Exception("内容验证失败")
                else:
                    self.logger.error("提取的内容为空")
                    raise Exception("提取的内容为空")
            else:
                self.logger.error("未找到内容元素")
                raise Exception("未找到内容元素")
            
        except Exception as e:
            self.logger.error(f"获取章节内容异常: {str(e)}")
            return {
                'title': chapter_title,
                'content': '',
                'url': chapter_url,
                'status': '失败',
                'error': str(e)
            }
    
    def validate_content(self, content):
        """验证内容是否有效：长度阈值+关键词包含/排除校验"""
        validation_config = self.config.get('advanced_features', {}).get('content_validation', {})
        
        # 检查最小长度
        min_length = validation_config.get('min_content_length', 100)
        if len(content) < min_length:
            return False
        
        # 检查必需关键词
        required_keywords = validation_config.get('required_keywords', [])
        for keyword in required_keywords:
            if keyword not in content:
                return False
        
        # 检查禁止关键词
        forbidden_keywords = validation_config.get('forbidden_keywords', [])
        for keyword in forbidden_keywords:
            if keyword in content:
                return False
        
        return True
    
    def save_chapter(self, chapter_data, output_dir=None):
        """保存章节到文件：目录组织、命名规整、模板化写入与回读校验"""
        title = chapter_data['title']
        content = chapter_data['content']
        url = chapter_data['url']
        status = chapter_data['status']
        
        # 确定输出目录
        if not output_dir:
            output_dir = self.config['global_settings'].get('output_directory', './downloads')
        
        base_dir = Path(output_dir)
        
        # 创建网站子目录
        if self.config['global_settings'].get('create_site_subdirectory', True):
            base_dir = base_dir / self.site_config['name']
        
        # 创建书籍子目录（如果有书名信息）
        if self.config['global_settings'].get('create_book_subdirectory', True):
            # 这里可以从URL或其他地方提取书名
            book_name = self.extract_book_name(url)
            if book_name:
                base_dir = base_dir / book_name
        
        # 创建章节内容目录
        content_dir_name = self.config['global_settings'].get('chapter_content_subdirectory', '章节内容')
        content_dir = base_dir / content_dir_name
        content_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名 - 为每个章节生成唯一文件名
        filename = self.clean_filename(title)
        if not filename or filename == '未知标题':
            # 使用备用文件名模式
            fallback_pattern = self.site_config.get('file_naming', {}).get('fallback_pattern', '未知标题_{timestamp}.txt')
            chapter_id = self.extract_chapter_id(url)
            filename = fallback_pattern.format(
                chapter_id=chapter_id,
                timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
            )
        
        # 为避免文件名冲突，添加章节ID或时间戳
        chapter_id = self.extract_chapter_id(url)
        if chapter_id:
            filename = f"{filename}_{chapter_id}"
        else:
            filename = f"{filename}_{datetime.now().strftime('%H%M%S')}"
        
        filepath = content_dir / f"{filename}.txt"
        
        try:
            # 调试：检查传入的内容
            self.logger.info(f"传入的章节内容长度: {len(content) if content else 0}")
            self.logger.info(f"传入的章节内容前100字符: {content[:100] if content else 'None'}")
            
            # 使用模板生成文件内容
            template = self.config.get('file_templates', {}).get('chapter_file', {})
            
            file_content = ""
            
            # 添加头部
            if 'header' in template:
                file_content += template['header'].format(
                    title=title,
                    url=url,
                    status=status,
                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            
            # 添加分隔符
            if 'separator' in template:
                file_content += template['separator'] + "\n\n"
            
            # 添加内容
            if 'content' in template:
                content_part = template['content'].format(content=content)
                self.logger.info(f"模板内容部分: {template['content']}")
                self.logger.info(f"格式化后内容长度: {len(content_part)}")
                file_content += content_part
            else:
                file_content += content
            
            # 添加尾部分隔符和尾部
            if 'separator' in template:
                file_content += "\n\n" + template['separator']
            if 'footer' in template:
                file_content += template['footer']
            
            # 如果没有模板或模板为空，使用默认格式
            if not template or not any(key in template for key in ['header', 'content', 'footer']):
                separator = '=' * 50
                file_content = f"标题: {title}\nURL: {url}\n获取状态: {status}\n获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{separator}\n\n{content}"
            
            # 如果使用了模板但没有内容，确保至少有基本信息
            if template and 'content' not in template and not file_content.strip():
                separator = '=' * 50
                file_content = f"标题: {title}\nURL: {url}\n获取状态: {status}\n获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{separator}\n\n{content}"
            
            self.logger.info(f"准备写入文件，内容长度: {len(file_content)}")
            self.logger.info(f"文件内容前100字符: {file_content[:100]}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
                
            # 验证文件是否正确写入
            with open(filepath, 'r', encoding='utf-8') as f:
                written_content = f.read()
                self.logger.info(f"文件写入后验证，长度: {len(written_content)}")
                self.logger.info(f"文件内容前100字符: {written_content[:100]}")
            
            return str(filepath)
        except Exception as e:
            self.logger.error(f"保存文件失败: {e}")
            return None
    
    def extract_book_name(self, url):
        """从URL提取书名（需按站点实现）：和图书示例用BS4尝试多选择器"""
        try:
            # 对于和图书网站，从书籍页面提取书名
            if 'hetushu.com' in url:
                import requests
                from bs4 import BeautifulSoup
                
                # 构造书籍主页URL
                book_id_match = re.search(r'/book/(\d+)/', url)
                if book_id_match:
                    book_id = book_id_match.group(1)
                    book_url = f"https://www.hetushu.com/book/{book_id}/index.html"
                    
                    response = requests.get(book_url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 尝试多种选择器提取书名
                    title_selectors = ['h2', 'h1', '.book-title', '.bookname h1', '.info h1', '#info h1']
                    for selector in title_selectors:
                        elem = soup.select_one(selector)
                        if elem and elem.get_text().strip():
                            book_title = elem.get_text().strip()
                            # 清理书名
                            book_title = re.sub(r'免费在线阅读.*', '', book_title)
                            book_title = re.sub(r'_.*', '', book_title)
                            if book_title and len(book_title) > 1:
                                return book_title
                    
                    # 从页面标题提取
                    if soup.title:
                        title_text = soup.title.get_text()
                        # 提取第一个书名（通常在标题开头）
                        title_parts = title_text.split('_')
                        if len(title_parts) > 1:
                            book_title = title_parts[0].strip()
                            book_title = re.sub(r'免费在线阅读.*', '', book_title)
                            if book_title and len(book_title) > 1:
                                return book_title
            
            # 其他网站的处理逻辑可以在这里添加
            
        except Exception as e:
            self.logger.warning(f"提取书名失败: {e}")
        
        return "未知书籍"
    
    def extract_chapter_id(self, url):
        """从URL提取章节ID：优先数字ID，回退时间戳"""
        # 尝试从URL中提取数字ID
        match = re.search(r'/(\d+)\.html?', url)
        if match:
            return match.group(1)
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    async def download_chapters(self, chapters, site_key=None, output_dir=None):
        """批量下载章节：站点设定→浏览器上下文→循环获取→模板保存→报告统计"""
        if not chapters:
            self.logger.error("没有章节可下载")
            return
        
        # 设置网站配置
        if site_key:
            self.set_site(site_key)
        elif not self.current_site:
            # 尝试从第一个章节URL自动检测
            first_url = chapters[0].get('url', '')
            detected_site = self.detect_site(first_url)
            if detected_site:
                self.set_site(detected_site)
            else:
                # 使用默认网站
                default_site = self.config['global_settings'].get('default_site')
                if default_site:
                    self.set_site(default_site)
                else:
                    raise Exception("无法确定网站类型，请指定site_key参数")
        
        self.logger.info(f"准备下载 {len(chapters)} 个章节")
        
        # 浏览器配置
        browser_config = self.config['global_settings'].get('browser_config', {})
        
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
            
            # 设置浏览器上下文
            context_options = {}
            if 'viewport' in browser_config:
                context_options['viewport'] = browser_config['viewport']
            if 'locale' in browser_config:
                context_options['locale'] = browser_config['locale']
            if 'timezone_id' in browser_config:
                context_options['timezone_id'] = browser_config['timezone']
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            # 设置请求头
            headers = self.site_config['request_config'].get('headers', {})
            if headers:
                await page.set_extra_http_headers(headers)
            
            success_count = 0
            failed_count = 0
            
            for i, chapter in enumerate(chapters, 1):
                chapter_title = chapter.get('title', '未知标题')
                chapter_url = chapter.get('url', '')
                
                self.logger.info(f"[{i}/{len(chapters)}] 正在下载: {chapter_title}")
                
                retry_count = 0
                max_retries = self.site_config['request_config'].get('retry_count', 3)
                retry_delay = self.site_config['request_config'].get('retry_delay', 5000)
                
                success = False
                
                while retry_count <= max_retries and not success:
                    try:
                        # 获取章节内容
                        content_data = await self.get_chapter_content(page, chapter_url, chapter_title)
                        
                        if content_data and content_data.get('content'):
                            # 保存章节
                            file_path = self.save_chapter(content_data, output_dir)
                            if file_path:
                                success_count += 1
                                self.download_report.append({
                                    'chapter': chapter_title,
                                    'url': chapter_url,
                                    'status': '成功',
                                    'filepath': file_path,
                                    'retry_count': retry_count,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                self.logger.info(f"✓ 下载成功: {Path(file_path).name}")
                                success = True
                            else:
                                raise Exception("保存文件失败")
                        else:
                            raise Exception("获取内容失败")
                    
                    except Exception as e:
                        retry_count += 1
                        if retry_count <= max_retries:
                            self.logger.warning(f"⚠ 重试 {retry_count}/{max_retries}: {e}")
                            await asyncio.sleep(retry_delay / 1000)
                        else:
                            failed_count += 1
                            self.download_report.append({
                                'chapter': chapter_title,
                                'url': chapter_url,
                                'status': '失败',
                                'error': str(e),
                                'retry_count': retry_count - 1,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            self.logger.error(f"✗ 下载失败: {e}")
                
                # 添加延迟
                delay = self.site_config['request_config'].get('delay_between_requests', 2000)
                if i < len(chapters):
                    await asyncio.sleep(delay / 1000)
            
            await browser.close()
            
            # 生成下载报告
            if self.config['global_settings'].get('generate_download_report', True):
                self.generate_report(success_count, failed_count, output_dir)
            
            self.logger.info(f"下载完成! 成功: {success_count}, 失败: {failed_count}")
    
    def generate_report(self, success_count, failed_count, output_dir=None):
        """生成下载报告：支持json/txt两种格式，含统计与明细"""
        try:
            if not output_dir:
                output_dir = self.config['global_settings'].get('output_directory', './downloads')
            
            base_dir = Path(output_dir)
            if self.config['global_settings'].get('create_site_subdirectory', True):
                base_dir = base_dir / self.site_config['name']
            
            report_format = self.config['global_settings'].get('report_format', 'json')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if report_format == 'json':
                report_file = base_dir / f"下载报告_{timestamp}.json"
                
                report_data = {
                    'summary': {
                        'total': len(self.download_report),
                        'success': success_count,
                        'failed': failed_count,
                        'success_rate': f"{success_count/len(self.download_report)*100:.1f}%" if self.download_report else "0%",
                        'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'site': self.site_config['name']
                    },
                    'details': self.download_report
                }
                
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            else:  # txt格式
                report_file = base_dir / f"下载报告_{timestamp}.txt"
                
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(f"下载报告\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"网站: {self.site_config['name']}\n")
                    f.write(f"总计: {len(self.download_report)} 章\n")
                    f.write(f"成功: {success_count} 章\n")
                    f.write(f"失败: {failed_count} 章\n")
                    f.write(f"成功率: {success_count/len(self.download_report)*100:.1f}%\n" if self.download_report else "成功率: 0%\n")
                    f.write(f"下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for item in self.download_report:
                        f.write(f"章节: {item['chapter']}\n")
                        f.write(f"状态: {item['status']}\n")
                        if 'error' in item:
                            f.write(f"错误: {item['error']}\n")
                        f.write(f"时间: {item['timestamp']}\n")
                        f.write("-" * 30 + "\n")
            
            self.logger.info(f"下载报告已保存: {report_file}")
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='通用小说下载器 - 支持多网站配置',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--config', '-c', type=str, default='downloader_config.json',
                       help='配置文件路径')
    parser.add_argument('--site', '-s', type=str, help='指定网站类型')
    parser.add_argument('--chapters-file', type=str, help='章节列表JSON文件')
    parser.add_argument('--output-dir', '-o', type=str, help='输出目录')
    parser.add_argument('--clear-before-download', action='store_true', help='下载前清空输出目录')
    parser.add_argument('--list-sites', action='store_true', help='列出支持的网站')
    
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    # 创建下载器实例
    downloader = UniversalNovelDownloader(args.config)
    
    # 列出支持的网站
    if args.list_sites:
        print("支持的网站:")
        for site_key, site_config in downloader.config['sites'].items():
            print(f"  {site_key}: {site_config['name']} ({site_config['base_url']})")
        return
    
    # 加载章节列表
    if args.chapters_file:
        try:
            with open(args.chapters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 处理不同的文件格式
                if isinstance(data, list):
                    chapters = data
                    book_info = {}
                else:
                    chapters = data.get('chapters', [])
                    book_info = data.get('book_info', {})
        except Exception as e:
            print(f"加载章节列表失败: {e}")
            return
    else:
        print("请指定章节列表文件 --chapters-file")
        return
    
    # 处理清空目录参数
    if args.clear_before_download:
        # 确定输出目录
        output_dir = args.output_dir
        if not output_dir:
            # 使用默认输出目录逻辑
            book_title = book_info.get('title', '未知书名')
            output_dir = downloader.clean_filename(book_title)
        
        output_path = Path(output_dir)
        if output_path.exists():
            print(f"正在清空输出目录: {output_path}")
            try:
                shutil.rmtree(output_path)
                print(f"已清空目录: {output_path}")
            except Exception as e:
                print(f"清空目录失败: {e}")
                return
    
    # 开始下载
    await downloader.download_chapters(chapters, args.site, args.output_dir)

if __name__ == "__main__":
    asyncio.run(main())