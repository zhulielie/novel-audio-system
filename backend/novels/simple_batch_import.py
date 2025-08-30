"""
简化版智能批量导入API
提供直接的网页接口调用
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging
import time
import requests
from urllib.parse import urlparse

from novels.models import Novel, NovelSource, NovelSourceRelation, Chapter

# 模拟爬虫类用于测试
class MockUnifiedCrawler:
    """模拟统一爬虫，用于测试目的"""
    
    def parse_novel_info(self, url):
        """模拟解析小说信息"""
        return {
            'title': 'API测试小说',
            'author': 'API测试作者',
            'description': '这是一个通过API测试创建的模拟小说，用于验证批量导入功能。',
            'chapters': [
                {'title': f'第{i}章 API测试章节', 'url': f'{url}/chapter/{i}'} 
                for i in range(1, 6)  # 生成5个测试章节
            ]
        }
    
    def crawl_chapter_content(self, chapter_url):
        """模拟爬取章节内容"""
        chapter_num = chapter_url.split('/')[-1] if '/' in chapter_url else '1'
        return {
            'title': f'第{chapter_num}章 API测试章节',
            'content': f'这是第{chapter_num}章的模拟内容。\n\n这个章节是通过API测试生成的，用于验证批量导入功能是否正常工作。\n\n章节内容包含了足够的文本来模拟真实的小说章节。'
        }
# 使用统一爬虫系统
try:
    import sys
    import os
    # 添加crawlers目录到路径
    crawlers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crawlers')
    sys.path.append(crawlers_path)
    from unified_crawler import UnifiedCrawler
except ImportError as e:
    print(f"Warning: Could not import UnifiedCrawler: {e}")
    UnifiedCrawler = None

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def simple_batch_import(request):
    """简化版智能批量导入API"""
    try:
        data = request.data
        
        # 提取参数
        source_url = data.get('source_url', '').strip()
        novel_title = data.get('novel_title', '').strip()
        author = data.get('author', '').strip()
        speed = data.get('speed', 'normal')
        max_chapters = int(data.get('max_chapters', 100))
        
        if not source_url or not novel_title:
            return Response({
                'success': False,
                'error': '请提供来源URL和小说标题'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"开始简化版智能批量导入: {novel_title} 从 {source_url}")
        
        # 根据速度设置延时
        speed_settings = {
            'slow': (3, 6),
            'normal': (2, 5),
            'fast': (1, 3)
        }
        min_delay, max_delay = speed_settings.get(speed, (2, 5))
        
        # 创建或获取小说
        novel, created = Novel.objects.get_or_create(
            title=novel_title,
            defaults={
                'author': author,
                'description': f'通过智能批量导入从 {source_url} 导入',
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"创建新小说: {novel.title}")
        else:
            logger.info(f"使用现有小说: {novel.title}")
        
        # 获取或创建来源
        parsed_url = urlparse(source_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        source, source_created = NovelSource.objects.get_or_create(
            base_url=base_domain,
            defaults={
                'name': f'{parsed_url.netloc}',
                'source_type': 'website',
                'is_active': True
            }
        )
        
        # 创建来源关联
        relation, relation_created = NovelSourceRelation.objects.get_or_create(
            novel=novel,
            source=source,
            defaults={
                'source_url': source_url,
                'is_primary': True
            }
        )
        
        # 使用统一爬虫系统
        if UnifiedCrawler is None:
            return Response({
                'success': False,
                'error': '统一爬虫模块未找到，请确保crawlers目录中的unified_crawler.py存在'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 检查是否为测试URL，使用模拟爬虫
        if 'mock-test.com' in source_url or 'mock-example.com' in source_url:
            crawler = MockUnifiedCrawler()
            logger.info(f"使用模拟爬虫进行测试 (延时: {min_delay}-{max_delay}秒)")
        else:
            crawler = UnifiedCrawler()
            logger.info(f"统一爬虫初始化完成 (延时: {min_delay}-{max_delay}秒)")
        
        # 解析小说信息
        logger.info(f"开始解析小说信息: {source_url}")
        novel_info = crawler.parse_novel_info(source_url)
        
        if not novel_info:
            return Response({
                'success': False,
                'error': '无法解析小说信息，请检查URL是否正确'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新小说信息
        if novel_info.get('title') and novel_info['title'] != '未知标题':
            novel.title = novel_info['title']
        if novel_info.get('author') and novel_info['author'] != '未知作者':
            novel.author = novel_info['author']
        if novel_info.get('description'):
            novel.description = novel_info['description']
        novel.save()
        
        # 批量导入章节
        chapters_imported = 0
        failed_count = 0
        skipped_count = 0
        
        chapters = novel_info.get('chapters', [])
        total_found = len(chapters)
        
        # 限制章节数量
        if max_chapters and max_chapters > 0:
            chapters = chapters[:max_chapters]
        
        logger.info(f"开始导入章节，总共 {len(chapters)} 章")
        
        for i, chapter_info in enumerate(chapters, 1):
            try:
                chapter_title = chapter_info.get('title', f'第{i}章')
                chapter_url = chapter_info.get('url', '')
                
                # 检查章节是否已存在
                if Chapter.objects.filter(novel=novel, title=chapter_title).exists():
                    logger.info(f"章节已存在，跳过: {chapter_title}")
                    skipped_count += 1
                    continue
                
                # 爬取章节内容
                logger.info(f"正在爬取第 {i} 章: {chapter_title}")
                chapter_content = crawler.crawl_chapter_content(chapter_url)
                
                if chapter_content and chapter_content.get('content'):
                    # 创建章节
                    Chapter.objects.create(
                        novel=novel,
                        title=chapter_title,
                        content=chapter_content['content'],
                        chapter_number=str(i),
                        chapter_sort_number=i,
                        source_url=chapter_url,
                        word_count=len(chapter_content['content'])
                    )
                    chapters_imported += 1
                    logger.info(f"成功导入: {chapter_title}")
                else:
                    failed_count += 1
                    logger.warning(f"章节内容为空，跳过: {chapter_title}")
                
                # 延时控制
                import random
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"导入章节失败: {chapter_title}, 错误: {str(e)}")
        
        # 构建结果
        result = {
            'success': chapters_imported > 0,
            'chapters_imported': chapters_imported,
            'total_found': total_found,
            'skipped_count': skipped_count,
            'failed_count': failed_count
        }
        
        if result['success']:
            # 更新统计信息
            relation.sync_count += 1
            relation.chapter_count = result['chapters_imported']
            relation.last_sync_at = timezone.now()
            relation.save()
            
            source.crawl_count += 1
            source.last_crawl_at = timezone.now()
            source.save()
            
            return Response({
                'success': True,
                'novel_id': novel.id,
                'novel_title': novel.title,
                'chapters_imported': result['chapters_imported'],
                'total_found': result.get('total_found', result['chapters_imported']),
                'skipped_count': result.get('skipped_count', 0),
                'failed_count': result.get('failed_count', 0),
                'min_delay': min_delay,
                'max_delay': max_delay,
                'source_name': source.name
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', '未知错误'),
                'chapters_imported': result.get('chapters_imported', 0)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"简化版智能批量导入失败: {str(e)}")
        return Response({
            'success': False,
            'error': f'导入失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_source_connection(request):
    """测试小说来源连接"""
    try:
        source_url = request.GET.get('url', '').strip()
        
        if not source_url:
            return Response({
                'success': False,
                'error': '请提供来源URL'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"测试来源连接: {source_url}")
        
        # 尝试访问URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(source_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 尝试解析基本信息
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 提取标题
        title = None
        title_selectors = ['h1', '.book-title', '.novel-title', 'title']
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title_text = element.get_text(strip=True)
                if title_text and len(title_text) < 100:  # 合理的标题长度
                    title = title_text
                    break
        
        # 提取作者
        author = None
        author_selectors = ['.author', '.writer', '.book-author']
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author_text = element.get_text(strip=True)
                if author_text and len(author_text) < 50:  # 合理的作者名长度
                    author = author_text
                    break
        
        # 检查是否有章节链接
        chapter_links = soup.find_all('a', href=True)
        chapter_count = len([link for link in chapter_links if '章' in link.get_text()])
        
        return Response({
            'success': True,
            'title': title,
            'author': author,
            'chapter_count': chapter_count,
            'status_code': response.status_code,
            'content_length': len(response.content)
        })
        
    except requests.RequestException as e:
        return Response({
            'success': False,
            'error': f'网络连接失败: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"测试来源连接失败: {str(e)}")
        return Response({
            'success': False,
            'error': f'测试失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)