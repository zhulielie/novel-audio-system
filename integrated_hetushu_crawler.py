#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合版和图书爬虫系统
- 使用cloudscraper绕过Cloudflare
- 智能去除水印（只取第一层标签内容，丢弃子标签）
- 支持目录提取和批量下载
"""

import json
import time
import random
import re
import os
import sys
from urllib.parse import urljoin
import cloudscraper
from bs4 import BeautifulSoup, NavigableString

# Windows 控制台可能为 GBK，强制使用 UTF-8 以避免 emoji/中文输出异常
try:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


class CloudflareBlockedError(Exception):
    """和图书站被 Cloudflare 拦截，需要用户手动绕过"""
    pass


class IntegratedHetuShuCrawler:
    """整合版和图书爬虫"""
    
    def __init__(self):
        # 使用简单的scraper配置，与测试脚本保持一致
        self.scraper = cloudscraper.create_scraper()
    
    def set_cookies(self, cookies: dict):
        """设置请求 cookies，用于人工绕过 Cloudflare 后继续爬取"""
        if cookies:
            self.scraper.cookies.update(cookies)
    
    def _is_cloudflare_page(self, response_text: str, status_code: int) -> bool:
        """检测响应是否被 Cloudflare 拦截"""
        indicators = [
            'cloudflare',
            'cf-browser-verification',
            'checking your browser',
            'please wait while we check your browser',
            'ddos protection by cloudflare',
            'ray id',
            'turnstile',
            'challenge-platform'
        ]
        text_lower = response_text.lower()
        has_indicators = any(ind in text_lower for ind in indicators)
        return status_code in (403, 503, 429) or has_indicators
    
    def extract_catalog(self, url):
        """提取小说目录"""
        print(f"📚 提取和图书目录: {url}")
        print("=" * 60)
        
        try:
            print("📡 获取页面内容...")
            response = self.scraper.get(url, timeout=30)
            
            print(f"📊 状态码: {response.status_code}")
            print(f"📊 内容长度: {len(response.text)} 字符")
            
            if self._is_cloudflare_page(response.text, response.status_code):
                print("🛡️ 检测到 Cloudflare 拦截，需要用户手动绕过")
                raise CloudflareBlockedError("和图书站被 Cloudflare 拦截，请在真实浏览器中完成验证")
            
            if response.status_code != 200:
                print(f"❌ 获取失败: {response.status_code}")
                return None
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取书籍信息
            book_info = {
                'title': '',
                'author': '',
                'url': url,
                'chapters': []
            }
            
            # 提取书名
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                # 清理标题
                title_text = re.sub(r'免费在线阅读.*', '', title_text)
                title_text = re.sub(r'_.*', '', title_text)
                book_info['title'] = title_text.strip()
            
            print(f"📚 书名: {book_info['title']}")
            
            # 查找所有章节链接
            print("🔍 查找章节链接...")
            all_links = soup.find_all('a', href=True)
            
            chapters = []
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # 过滤章节链接
                if (href and text and 
                    '/book/' in href and 
                    '.html' in href and
                    '第' in text and '章' in text and
                    'm.hetushu.com' not in href):  # 排除手机版
                    
                    # 构建完整URL
                    full_url = urljoin(url, href)
                    
                    # 提取章节号
                    chapter_match = re.search(r'第(\d+)章', text)
                    chapter_num = int(chapter_match.group(1)) if chapter_match else 0
                    
                    chapters.append({
                        'chapter_num': chapter_num,
                        'title': text,
                        'url': full_url
                    })
            
            # 按章节号排序
            chapters.sort(key=lambda x: x['chapter_num'])
            
            book_info['chapters'] = chapters
            
            print(f"📑 找到章节: {len(chapters)} 章")
            
            if chapters:
                print("\n📖 章节预览 (前5章):")
                for i, chapter in enumerate(chapters[:5]):
                    print(f"  {i+1}. {chapter['title']}")
                    print(f"     URL: {chapter['url']}")
            
            return book_info
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            return None
    
    def extract_content_no_watermark(self, content_elem):
        """
        去水印内容提取 - 只取第一层标签的直接文本内容，丢弃所有子标签
        这样可以有效去除嵌套在子标签中的水印内容
        """
        if not content_elem:
            return ""
        
        print("🧹 使用去水印模式提取内容...")
        
        # 只提取第一层的直接文本节点，忽略所有子标签
        first_level_texts = []
        
        for child in content_elem.children:
            if isinstance(child, NavigableString):
                # 直接的文本节点
                text = str(child).strip()
                if text and len(text) > 3:  # 过滤太短的文本
                    first_level_texts.append(text)
            elif hasattr(child, 'name'):
                # 对于标签元素，只取其直接文本内容，不递归到子标签
                direct_text = ""
                for direct_child in child.children:
                    if isinstance(direct_child, NavigableString):
                        direct_text += str(direct_child)
                
                # 清理并添加
                direct_text = direct_text.strip()
                if direct_text and len(direct_text) > 3:
                    first_level_texts.append(direct_text)
        
        # 合并文本
        content = '\n'.join(first_level_texts)
        
        # 基本清理
        content = re.sub(r'\n\s*\n', '\n', content)  # 去除多余空行
        content = re.sub(r'[ \t]+', ' ', content)    # 合并多余空格
        content = content.strip()
        
        print(f"🧹 去水印后内容长度: {len(content)} 字符")
        
        return content
    
    def extract_content_normal(self, content_elem):
        """
        普通内容提取 - 提取所有文本内容（包含子标签）
        """
        if not content_elem:
            return ""
        
        print("📄 使用普通模式提取内容...")
        
        # 获取所有文本内容
        content_text = content_elem.get_text()
        
        # 清理文本
        lines = content_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        print(f"📄 普通模式内容长度: {len(content)} 字符")
        
        return content
    
    def download_chapter(self, chapter_url, chapter_title, remove_watermark=True):
        """下载单个章节"""
        print(f"📖 下载章节: {chapter_title}")
        print(f"🌐 URL: {chapter_url}")
        print(f"🧹 去水印模式: {'开启' if remove_watermark else '关闭'}")
        
        try:
            # 随机延迟
            delay = random.uniform(1, 3)
            print(f"⏱️ 等待 {delay:.1f} 秒...")
            time.sleep(delay)
            
            # 获取章节页面
            response = self.scraper.get(chapter_url, timeout=30)
            
            if self._is_cloudflare_page(response.text, response.status_code):
                print("🛡️ 检测到 Cloudflare 拦截，需要用户手动绕过")
                raise CloudflareBlockedError("和图书站被 Cloudflare 拦截，请在真实浏览器中完成验证")
            
            if response.status_code != 200:
                print(f"❌ HTTP错误: {response.status_code}")
                return None
            
            print(f"✅ 获取成功! 页面长度: {len(response.text)} 字符")
            
            # 解析内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种选择器
            content_selectors = ['#content', 'div#content', '.content']
            content_elem = None
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    print(f"🎯 使用选择器: {selector}")
                    break
            
            if not content_elem:
                print("❌ 未找到内容元素")
                # 调试信息
                print("🔍 调试信息:")
                divs = soup.find_all('div')
                print(f"   页面共有 {len(divs)} 个div元素")
                for div in divs[:3]:  # 显示前3个div的信息
                    text = div.get_text().strip()[:50]
                    print(f"   div: class={div.get('class')}, id={div.get('id')}, text={text}...")
                return None
            
            # 根据模式选择提取方法
            if remove_watermark:
                chapter_content = self.extract_content_no_watermark(content_elem)
            else:
                chapter_content = self.extract_content_normal(content_elem)
            
            if not chapter_content:
                print("❌ 提取的内容为空")
                return None
            
            print(f"✅ 内容提取成功! 最终长度: {len(chapter_content)} 字符")
            
            return {
                'title': chapter_title,
                'url': chapter_url,
                'content': chapter_content,
                'length': len(chapter_content),
                'watermark_removed': remove_watermark
            }
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return None
    
    def download_chapters_range(self, catalog_file, start_chapter, end_chapter, remove_watermark=True):
        """批量下载指定范围的章节"""
        print(f"📚 批量下载章节 {start_chapter}-{end_chapter}")
        print(f"🧹 去水印模式: {'开启' if remove_watermark else '关闭'}")
        print("=" * 60)
        
        # 读取目录
        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        
        print(f"📖 书名: {catalog['title']}")
        print(f"🎯 下载范围: 第{start_chapter}-{end_chapter}章")
        
        # 筛选目标章节
        target_chapters = []
        for chapter in catalog['chapters']:
            try:
                chapter_num = int(chapter['chapter_num'])
                if start_chapter <= chapter_num <= end_chapter:
                    target_chapters.append(chapter)
            except (ValueError, TypeError):
                # 如果chapter_num不是数字，跳过
                continue
        
        print(f"📑 目标章节: {len(target_chapters)} 章")
        
        if not target_chapters:
            print("❌ 没有找到指定范围的章节")
            return []
        
        # 创建保存目录
        book_title = re.sub(r'[<>:"/\\|?*]', '_', catalog['title'])
        watermark_suffix = "_去水印版" if remove_watermark else "_普通版"
        save_dir = f"hetushu_{book_title}_第{start_chapter}-{end_chapter}章{watermark_suffix}"
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        print(f"📁 保存目录: {save_dir}")
        
        # 下载章节
        downloaded_chapters = []
        
        for i, chapter in enumerate(target_chapters):
            print(f"\n📖 下载进度: {i+1}/{len(target_chapters)}")
            
            result = self.download_chapter(
                chapter['url'], 
                chapter['title'], 
                remove_watermark=remove_watermark
            )
            
            if result:
                # 保存单个章节文件
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', chapter['title'])
                filename = f"{safe_title}.txt"
                filepath = os.path.join(save_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"标题: {chapter['title']}\n")
                    f.write(f"URL: {chapter['url']}\n")
                    f.write(f"去水印: {'是' if remove_watermark else '否'}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(result['content'])
                
                print(f"💾 已保存: {filename}")
                
                downloaded_chapters.append(result)
                print(f"✅ 下载成功!")
            else:
                print(f"❌ 下载失败!")
        
        # 创建合并文件
        if downloaded_chapters:
            merged_filename = os.path.join(save_dir, f"{book_title}_第{start_chapter}-{end_chapter}章{watermark_suffix}_合并版.txt")
            
            with open(merged_filename, 'w', encoding='utf-8') as f:
                f.write(f"书名: {catalog['title']}\n")
                f.write(f"章节: 第{start_chapter}-{end_chapter}章\n")
                f.write(f"去水印: {'是' if remove_watermark else '否'}\n")
                f.write(f"下载时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                for chapter in downloaded_chapters:
                    f.write(f"\n\n{'='*20} {chapter['title']} {'='*20}\n\n")
                    f.write(chapter['content'])
                    f.write("\n\n")
            
            print(f"\n📚 合并文件已保存: {merged_filename}")
        
        # 输出统计
        print(f"\n🎉 下载完成!")
        print(f"✅ 成功: {len(downloaded_chapters)} 章")
        print(f"❌ 失败: {len(target_chapters) - len(downloaded_chapters)} 章")
        print(f"📁 保存位置: {save_dir}")
        print(f"🧹 去水印模式: {'开启' if remove_watermark else '关闭'}")
        
        # 显示下载的章节
        if downloaded_chapters:
            print(f"\n📖 成功下载的章节:")
            for chapter in downloaded_chapters:
                watermark_status = "去水印" if chapter['watermark_removed'] else "普通"
                print(f"  • {chapter['title']} ({chapter['length']} 字符) [{watermark_status}]")
        
        return downloaded_chapters
    
    def save_catalog(self, catalog, filename=None):
        """保存目录到文件"""
        if not filename:
            title = catalog.get('title', 'unknown')
            title = re.sub(r'[<>:"/\\|?*]', '_', title)
            filename = f"hetushu_{title}_catalog.json"
        
        print(f"💾 保存目录到: {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 保存完成!")
        return filename

def main():
    """主函数"""
    print("🚀 整合版和图书爬虫系统")
    print("=" * 70)
    
    crawler = IntegratedHetuShuCrawler()
    
    # 目录文件
    catalog_file = "hetushu_国医高手_catalog.json"
    
    # 检查目录文件是否存在
    if not os.path.exists(catalog_file):
        print(f"❌ 目录文件不存在: {catalog_file}")
        print("💡 请先运行目录提取器生成目录文件")
        return
    
    # 下载第1-5章，开启去水印模式
    start_chapter = 1
    end_chapter = 5
    
    print(f"🎯 下载章节范围: 第{start_chapter}章 - 第{end_chapter}章")
    print(f"🧹 去水印模式: 开启")
    
    # 执行下载
    chapters = crawler.download_chapters_range(
        catalog_file, 
        start_chapter, 
        end_chapter, 
        remove_watermark=True  # 开启去水印
    )
    
    if chapters:
        print(f"\n🎉 下载任务完成!")
        print(f"📚 书名: 国医高手")
        print(f"📑 下载章节: 第{start_chapter}-{end_chapter}章")
        print(f"✅ 成功下载: {len(chapters)} 章")
        print(f"🧹 已应用去水印技术")
    else:
        print("\n❌ 下载失败")

if __name__ == "__main__":
    main()
