#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合爬虫系统API接口
"""

import os
import sys
import uuid
import json
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import Novel, Chapter
from .crawler_models import CrawlerTask, NovelCatalog, ChapterDownloadRecord
from .serializers import NovelSerializer, ChapterSerializer

# 导入 WebBridge 辅助工具
from . import webbridge_helper

import logging
logger = logging.getLogger(__name__)

# 导入爬虫及异常（项目根目录在 sys.path）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from integrated_novel_crawler import IntegratedNovelCrawler, CloudflareBlockedError


class CrawlerAPIViewSet(viewsets.ViewSet):
    """整合爬虫API视图集"""
    
    permission_classes = [AllowAny]  # 暂时允许匿名访问，方便测试
    
    def _get_crawler(self):
        """获取爬虫实例"""
        return IntegratedNovelCrawler()
    
    @action(detail=False, methods=['post'])
    def extract_catalog(self, request):
        """提取小说目录"""
        try:
            source_url = request.data.get('source_url', '').strip()
            
            if not source_url:
                return Response({
                    'success': False,
                    'error': '请提供源URL'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建任务
            task_id = f"catalog_{uuid.uuid4().hex[:8]}"
            task = CrawlerTask.objects.create(
                task_id=task_id,
                task_type='catalog_extract',
                source_url=source_url,
                status='running',
                started_at=timezone.now(),
                parameters={'source_url': source_url}
            )
            
            try:
                # 获取爬虫实例
                crawler = self._get_crawler()
                
                # 提取目录
                catalog_data = crawler.extract_catalog(source_url)
                
                if catalog_data:
                    # 更新任务状态
                    task.status = 'completed'
                    task.completed_at = timezone.now()
                    task.total_items = len(catalog_data.get('chapters', []))
                    task.success_items = task.total_items
                    task.progress = 100
                    task.result_data = catalog_data
                    task.save()
                    
                    return Response({
                        'success': True,
                        'task_id': task_id,
                        'catalog': catalog_data,
                        'message': f'成功提取目录，共 {len(catalog_data.get("chapters", []))} 章'
                    })
                else:
                    # 任务失败：示例站点等站点可能返回了页面但无章节，提示人工绕过
                    task.status = 'failed'
                    task.completed_at = timezone.now()
                    task.error_message = '无法提取目录信息'
                    task.save()
                    
                    if 'example.com' in source_url:
                        return Response({
                            'success': False,
                            'needs_manual_bypass': True,
                            'task_id': task_id,
                            'source_url': source_url,
                            'error': '未能解析到章节，页面可能被 Cloudflare 保护',
                            'message': '未能解析到章节，建议在真实浏览器中完成验证后继续'
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    return Response({
                        'success': False,
                        'task_id': task_id,
                        'error': '无法提取目录信息'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except CloudflareBlockedError as e:
                # 被 Cloudflare 拦截，提示用户手动绕过
                task.status = 'failed'
                task.completed_at = timezone.now()
                task.error_message = str(e)
                task.save()
                
                return Response({
                    'success': False,
                    'needs_manual_bypass': True,
                    'task_id': task_id,
                    'source_url': source_url,
                    'error': str(e),
                    'message': '示例站点站被 Cloudflare 拦截，请在真实浏览器中完成验证后继续'
                }, status=status.HTTP_403_FORBIDDEN)
                
            except Exception as e:
                # 任务失败
                task.status = 'failed'
                task.completed_at = timezone.now()
                task.error_message = str(e)
                task.save()
                
                return Response({
                    'success': False,
                    'task_id': task_id,
                    'error': f'目录提取失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'系统错误: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def request_manual_bypass(self, request):
        """请求在用户真实浏览器中打开 URL，用于人工绕过 Cloudflare"""
        source_url = request.data.get('source_url', '').strip()
        if not source_url:
            return Response({'success': False, 'error': '请提供源URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not webbridge_helper.check_status():
            return Response({
                'success': False,
                'error': 'Kimi WebBridge 未运行，无法打开用户浏览器'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            session = webbridge_helper.open_user_browser(source_url)
            return Response({
                'success': True,
                'session': session,
                'source_url': source_url,
                'message': '已在您的浏览器中打开验证页面，请完成验证后点击“继续提取”'
            })
        except Exception as e:
            logger.exception("打开用户浏览器失败")
            return Response({
                'success': False,
                'error': f'打开浏览器失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def complete_manual_bypass(self, request):
        """用户完成浏览器验证后，直接在浏览器 DOM 中提取目录"""
        source_url = request.data.get('source_url', '').strip()
        session = request.data.get('session', '').strip()
        
        if not source_url or not session:
            return Response({'success': False, 'error': '请提供源URL和 session'}, status=status.HTTP_400_BAD_REQUEST)
        
        task_id = f"catalog_{uuid.uuid4().hex[:8]}"
        task = CrawlerTask.objects.create(
            task_id=task_id,
            task_type='catalog_extract',
            source_url=source_url,
            status='running',
            started_at=timezone.now(),
            parameters={'source_url': source_url, 'manual_bypass': True}
        )
        
        try:
            # 直接在用户浏览器中解析已渲染好的页面目录
            catalog_data = webbridge_helper.extract_catalog_from_browser(session, source_url)
            cookies = webbridge_helper.get_cookies(session)
            
            if catalog_data and catalog_data.get('chapters'):
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.total_items = len(catalog_data.get('chapters', []))
                task.success_items = task.total_items
                task.progress = 100
                task.result_data = catalog_data
                task.save()
                
                return Response({
                    'success': True,
                    'task_id': task_id,
                    'catalog': catalog_data,
                    'cookies': cookies,
                    'message': f'人工绕过成功，共提取 {len(catalog_data.get("chapters", []))} 章'
                })
            else:
                task.status = 'failed'
                task.completed_at = timezone.now()
                task.error_message = '未能在浏览器页面中解析到章节，请确认页面已正常加载'
                task.save()
                return Response({
                    'success': False,
                    'error': '未能在浏览器页面中解析到章节，请确认页面已正常加载'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            task.status = 'failed'
            task.completed_at = timezone.now()
            task.error_message = str(e)
            task.save()
            return Response({
                'success': False,
                'error': f'提取失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def download_chapters(self, request):
        """批量下载章节"""
        try:
            # 获取参数
            catalog_data = request.data.get('catalog')
            start_chapter = request.data.get('start_chapter', 1)
            end_chapter = request.data.get('end_chapter', 5)
            remove_watermark = request.data.get('remove_watermark', True)
            novel_title = request.data.get('novel_title', '')
            cookies = request.data.get('cookies', {}) or {}
            
            if not catalog_data:
                return Response({
                    'success': False,
                    'error': '请提供目录数据'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 如果catalog_data是字符串，尝试解析为JSON
            if isinstance(catalog_data, str):
                try:
                    catalog_data = json.loads(catalog_data)
                except json.JSONDecodeError:
                    return Response({
                        'success': False,
                        'error': '目录数据格式错误'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建任务
            task_id = f"download_{uuid.uuid4().hex[:8]}"
            task = CrawlerTask.objects.create(
                task_id=task_id,
                task_type='chapter_download',
                source_url=catalog_data.get('url', ''),
                status='running',
                started_at=timezone.now(),
                parameters={
                    'start_chapter': start_chapter,
                    'end_chapter': end_chapter,
                    'remove_watermark': remove_watermark,
                    'novel_title': novel_title
                }
            )
            
            try:
                # 获取爬虫实例
                crawler = self._get_crawler()
                if cookies:
                    crawler.set_cookies(cookies)
                
                # 筛选目标章节
                chapters = catalog_data.get('chapters', [])
                target_chapters = []
                for ch in chapters:
                    try:
                        chapter_num = int(ch.get('chapter_num', 0))
                        if start_chapter <= chapter_num <= end_chapter:
                            target_chapters.append(ch)
                    except (ValueError, TypeError):
                        continue
                
                if not target_chapters:
                    task.status = 'failed'
                    task.completed_at = timezone.now()
                    task.error_message = '没有找到指定范围的章节'
                    task.save()
                    
                    return Response({
                        'success': False,
                        'task_id': task_id,
                        'error': '没有找到指定范围的章节'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 更新任务总数
                task.total_items = len(target_chapters)
                task.save()
                
                # 下载章节
                downloaded_chapters = []
                
                for i, chapter_info in enumerate(target_chapters):
                    download_record = None
                    try:
                        # 创建下载记录
                        download_record = ChapterDownloadRecord.objects.create(
                            task=task,
                            chapter_title=chapter_info.get('title', ''),
                            chapter_number=chapter_info.get('chapter_num', 0),
                            source_url=chapter_info.get('url', ''),
                            status='downloading',
                            download_started_at=timezone.now()
                        )
                        
                        # 下载章节内容
                        result = crawler.download_chapter(
                            chapter_info.get('url'),
                            chapter_info.get('title'),
                            remove_watermark=remove_watermark
                        )
                    except CloudflareBlockedError as cfe:
                        if download_record:
                            download_record.status = 'failed'
                            download_record.download_completed_at = timezone.now()
                            download_record.error_message = str(cfe)
                            download_record.save()
                        task.status = 'failed'
                        task.completed_at = timezone.now()
                        task.error_message = str(cfe)
                        task.save()
                        return Response({
                            'success': False,
                            'needs_manual_bypass': True,
                            'error': str(cfe),
                            'message': '下载章节时再次被 Cloudflare 拦截，请重新完成浏览器验证'
                        }, status=status.HTTP_403_FORBIDDEN)
                    except Exception as chapter_error:
                        # 章节下载异常
                        if download_record:
                            download_record.status = 'failed'
                            download_record.download_completed_at = timezone.now()
                            download_record.error_message = str(chapter_error)
                            download_record.save()
                        
                        # 更新任务进度
                        task.update_progress(
                            processed=i + 1,
                            failed=task.failed_items + 1
                        )
                        continue
                    
                    if result:
                        # 下载成功
                        download_record.status = 'completed'
                        download_record.download_completed_at = timezone.now()
                        download_record.content_length = result.get('length', 0)
                        download_record.watermark_removed = result.get('watermark_removed', False)
                        download_record.save()
                        
                        downloaded_chapters.append(result)
                        
                        # 更新任务进度
                        task.update_progress(
                            processed=i + 1,
                            success=len(downloaded_chapters)
                        )
                    else:
                        # 下载失败
                        download_record.status = 'failed'
                        download_record.download_completed_at = timezone.now()
                        download_record.error_message = '章节内容为空'
                        download_record.save()
                        
                        # 更新任务进度
                        task.update_progress(
                            processed=i + 1,
                            failed=task.failed_items + 1
                        )
                
                # 任务完成
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.progress = 100
                task.result_data = {
                    'downloaded_chapters': len(downloaded_chapters),
                    'total_chapters': len(target_chapters),
                    'success_rate': (len(downloaded_chapters) / len(target_chapters)) * 100
                }
                task.save()
                
                return Response({
                    'success': True,
                    'task_id': task_id,
                    'downloaded_chapters': len(downloaded_chapters),
                    'total_chapters': len(target_chapters),
                    'failed_chapters': len(target_chapters) - len(downloaded_chapters),
                    'chapters': downloaded_chapters,
                    'message': f'成功下载 {len(downloaded_chapters)}/{len(target_chapters)} 章'
                })
                
            except Exception as e:
                # 任务失败
                task.status = 'failed'
                task.completed_at = timezone.now()
                task.error_message = str(e)
                task.save()
                
                return Response({
                    'success': False,
                    'task_id': task_id,
                    'error': f'章节下载失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'系统错误: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def batch_import_to_db(self, request):
        """批量导入到数据库"""
        try:
            # 获取参数
            catalog_data = request.data.get('catalog')
            chapters_data = request.data.get('chapters', [])
            novel_title = request.data.get('novel_title', '')
            novel_author = request.data.get('novel_author', '')
            
            if not catalog_data or not chapters_data:
                return Response({
                    'success': False,
                    'error': '请提供目录和章节数据'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建任务
            task_id = f"import_{uuid.uuid4().hex[:8]}"
            task = CrawlerTask.objects.create(
                task_id=task_id,
                task_type='batch_import',
                source_url=catalog_data.get('url', ''),
                status='running',
                started_at=timezone.now(),
                total_items=len(chapters_data),
                parameters={
                    'novel_title': novel_title,
                    'novel_author': novel_author
                }
            )
            
            try:
                with transaction.atomic():
                    # 创建或获取小说
                    novel, created = Novel.objects.get_or_create(
                        title=novel_title or catalog_data.get('title', '未知小说'),
                        defaults={
                            'author': novel_author or catalog_data.get('author', '未知作者'),
                            'description': f'从 {catalog_data.get("url", "")} 自动导入',
                            'status': 'published',
                            'is_active': True
                        }
                    )
                    
                    # 更新任务关联小说
                    task.novel = novel
                    task.save()
                    
                    # 创建目录记录
                    catalog, _ = NovelCatalog.objects.get_or_create(
                        novel=novel,
                        defaults={
                            'source_url': catalog_data.get('url', ''),
                            'title': catalog_data.get('title', ''),
                            'author': catalog_data.get('author', ''),
                            'total_chapters': len(catalog_data.get('chapters', [])),
                            'chapters_data': catalog_data.get('chapters', []),
                            'extracted_at': timezone.now(),
                            'extractor_version': 'integrated_v1.0'
                        }
                    )
                    
                    # 导入章节
                    imported_count = 0
                    skipped_count = 0
                    
                    for i, chapter_data in enumerate(chapters_data):
                        chapter_title = chapter_data.get('title', '')
                        chapter_content = chapter_data.get('content', '')
                        
                        if not chapter_title or not chapter_content:
                            task.update_progress(
                                processed=i + 1,
                                failed=task.failed_items + 1
                            )
                            continue
                        
                        # 检查章节是否已存在
                        existing_chapter = Chapter.objects.filter(
                            novel=novel,
                            title=chapter_title
                        ).first()
                        
                        if existing_chapter:
                            skipped_count += 1
                        else:
                            # 创建新章节
                            Chapter.objects.create(
                                novel=novel,
                                title=chapter_title,
                                content=chapter_content,
                                chapter_number=str(i + 1),
                                chapter_sort_number=i + 1,
                                word_count=len(chapter_content),
                                is_published=True
                            )
                            imported_count += 1
                        
                        # 更新任务进度
                        task.update_progress(
                            processed=i + 1,
                            success=imported_count
                        )
                    
                    # 任务完成
                    task.status = 'completed'
                    task.completed_at = timezone.now()
                    task.progress = 100
                    task.result_data = {
                        'novel_id': novel.id,
                        'imported_count': imported_count,
                        'skipped_count': skipped_count,
                        'total_count': len(chapters_data)
                    }
                    task.save()
                    
                    return Response({
                        'success': True,
                        'task_id': task_id,
                        'novel_id': novel.id,
                        'novel_title': novel.title,
                        'imported_count': imported_count,
                        'skipped_count': skipped_count,
                        'total_count': len(chapters_data),
                        'message': f'成功导入 {imported_count} 章到小说《{novel.title}》'
                    })
                    
            except Exception as e:
                # 任务失败
                task.status = 'failed'
                task.completed_at = timezone.now()
                task.error_message = str(e)
                task.save()
                
                return Response({
                    'success': False,
                    'task_id': task_id,
                    'error': f'数据库导入失败: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'系统错误: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def task_status(self, request):
        """获取任务状态"""
        task_id = request.query_params.get('task_id')
        
        if not task_id:
            return Response({
                'success': False,
                'error': '请提供task_id参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            task = CrawlerTask.objects.get(task_id=task_id)
            
            # 获取下载记录
            download_records = []
            if task.task_type == 'chapter_download':
                records = ChapterDownloadRecord.objects.filter(task=task).order_by('chapter_number')
                download_records = [
                    {
                        'chapter_title': record.chapter_title,
                        'chapter_number': record.chapter_number,
                        'status': record.status,
                        'content_length': record.content_length,
                        'watermark_removed': record.watermark_removed,
                        'error_message': record.error_message
                    }
                    for record in records
                ]
            
            return Response({
                'success': True,
                'task': {
                    'task_id': task.task_id,
                    'task_type': task.get_task_type_display(),
                    'status': task.get_status_display(),
                    'progress': task.progress,
                    'total_items': task.total_items,
                    'processed_items': task.processed_items,
                    'success_items': task.success_items,
                    'failed_items': task.failed_items,
                    'success_rate': task.success_rate,
                    'duration': str(task.duration) if task.duration else None,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'error_message': task.error_message,
                    'result_data': task.result_data,
                    'download_records': download_records
                }
            })
            
        except CrawlerTask.DoesNotExist:
            return Response({
                'success': False,
                'error': '任务不存在'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def task_list(self, request):
        """获取任务列表"""
        tasks = CrawlerTask.objects.all().order_by('-created_at')[:20]  # 最近20个任务
        
        task_list = []
        for task in tasks:
            task_list.append({
                'task_id': task.task_id,
                'task_type': task.get_task_type_display(),
                'status': task.get_status_display(),
                'progress': task.progress,
                'novel_title': task.novel.title if task.novel else '',
                'created_at': task.created_at,
                'completed_at': task.completed_at,
                'duration': str(task.duration) if task.duration else None,
                'success_rate': task.success_rate
            })
        
        return Response({
            'success': True,
            'tasks': task_list
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def quick_crawl(request):
    """快速爬取接口 - 一键完成目录提取+章节下载+数据库导入"""
    try:
        # 获取参数
        source_url = request.data.get('source_url', '').strip()
        start_chapter = request.data.get('start_chapter', 1)
        end_chapter = request.data.get('end_chapter', 5)
        remove_watermark = request.data.get('remove_watermark', True)
        novel_title = request.data.get('novel_title', '')
        novel_author = request.data.get('novel_author', '')

        if not source_url:
            return Response({
                'success': False,
                'error': '请提供源URL'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建总任务
        task_id = f"quick_{uuid.uuid4().hex[:8]}"
        downloaded_chapters = []
        catalog_chapters_count = 0

        # 获取爬虫实例
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        sys.path.insert(0, project_root)

        from integrated_novel_crawler import IntegratedNovelCrawler
        crawler = IntegratedNovelCrawler()

        # 步骤1: 提取目录
        print(f"🔍 步骤1: 提取目录 - {source_url}")
        catalog_data = crawler.extract_catalog(source_url)

        if not catalog_data:
            raise Exception('无法提取目录信息')

        catalog_chapters_count = len(catalog_data.get('chapters', []))

        # 步骤2: 下载章节
        print(f"📖 步骤2: 下载章节 {start_chapter}-{end_chapter}")
        chapters = catalog_data.get('chapters', [])
        target_chapters = []
        for ch in chapters:
            try:
                chapter_num = int(ch.get('chapter_num', 0))
                if start_chapter <= chapter_num <= end_chapter:
                    target_chapters.append(ch)
            except (ValueError, TypeError):
                continue

        if not target_chapters:
            raise Exception('没有找到指定范围的章节')

        for chapter_info in target_chapters:
            result = crawler.download_chapter(
                chapter_info.get('url'),
                chapter_info.get('title'),
                remove_watermark=remove_watermark
            )
            if result:
                downloaded_chapters.append(result)

        # 步骤3: 导入数据库
        print(f"💾 步骤3: 导入数据库")
        with transaction.atomic():
            novel, created = Novel.objects.get_or_create(
                title=novel_title or '未知小说',
                defaults={
                    'author': novel_author or '未知作者',
                    'description': f'从 {source_url} 快速导入',
                    'status': 'published',
                    'is_active': True
                }
            )

            # 创建任务记录
            task = CrawlerTask.objects.create(
                task_id=task_id,
                task_type='batch_import',
                novel=novel,
                source_url=source_url,
                status='completed',
                started_at=timezone.now(),
                completed_at=timezone.now(),
                total_items=len(downloaded_chapters),
                processed_items=len(downloaded_chapters),
                success_items=len(downloaded_chapters),
                progress=100,
                parameters={
                    'start_chapter': start_chapter,
                    'end_chapter': end_chapter,
                    'remove_watermark': remove_watermark,
                    'novel_title': novel_title,
                    'novel_author': novel_author
                },
                result_data={
                    'novel_id': novel.id,
                    'catalog_extracted': True,
                    'chapters_downloaded': len(downloaded_chapters),
                    'chapters_imported': 0
                }
            )

            # 导入章节
            imported_count = 0
            for i, chapter_data in enumerate(downloaded_chapters):
                chapter_title = chapter_data.get('title', '')
                chapter_content = chapter_data.get('content', '')

                if chapter_title and chapter_content:
                    # 检查章节是否已存在
                    existing_chapter = Chapter.objects.filter(
                        novel=novel,
                        title=chapter_title
                    ).first()

                    if not existing_chapter:
                        Chapter.objects.create(
                            novel=novel,
                            title=chapter_title,
                            content=chapter_content,
                            chapter_number=str(chapter_data.get('chapter_num', start_chapter + i)),
                            chapter_sort_number=chapter_data.get('chapter_num', start_chapter + i),
                            word_count=len(chapter_content),
                            is_published=True
                        )
                        imported_count += 1

            # 更新任务结果
            task.result_data['chapters_imported'] = imported_count
            task.save()

            message = f'快速导入完成！小说《{novel.title}》共处理 {len(downloaded_chapters)} 章，新增 {imported_count} 章'

            return Response({
                'success': True,
                'task_id': task_id,
                'novel_id': novel.id,
                'novel_title': novel.title,
                'novel_author': novel.author,
                'catalog_chapters': catalog_chapters_count,
                'downloaded_chapters': len(downloaded_chapters),
                'imported_chapters': imported_count,
                'watermark_removed': remove_watermark,
                'message': message
            })

    except Exception as e:
        return Response({
            'success': False,
            'error': f'系统错误: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_crawl_next_chapters(request):
    """
    自动爬取新章节 - 边看边下功能
    """
    try:
        novel_id = request.data.get('novel_id')
        current_chapter = request.data.get('current_chapter', 1)
        crawl_ahead = request.data.get('crawl_ahead', 3)  # 提前爬取几章
        
        if not novel_id:
            return Response({
                'success': False,
                'error': '缺少小说ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取小说信息
        try:
            novel = Novel.objects.get(id=novel_id)
        except Novel.DoesNotExist:
            return Response({
                'success': False,
                'error': '小说不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 检查小说是否有源URL
        if not novel.source_url:
            return Response({
                'success': False,
                'error': '小说没有源URL，无法自动爬取'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取已有章节数量
        existing_chapters = Chapter.objects.filter(novel=novel).count()
        logger.info(f"小说《{novel.title}》当前有 {existing_chapters} 章")
        
        # 计算需要爬取的章节范围
        target_chapter = current_chapter + crawl_ahead
        if target_chapter <= existing_chapters:
            return Response({
                'success': True,
                'message': f'章节已存在，无需爬取（当前有{existing_chapters}章）',
                'existing_chapters': existing_chapters,
                'target_chapter': target_chapter
            })
        
        # 创建爬取任务
        task_id = f"auto_crawl_{uuid.uuid4().hex[:8]}"
        
        # 异步执行爬取任务
        import threading
        def crawl_task():
            try:
                logger.info(f"开始自动爬取任务: {task_id}")
                
                # 获取爬虫实例
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_dir))
                sys.path.insert(0, project_root)
                
                from integrated_novel_crawler import IntegratedNovelCrawler
                crawler = IntegratedNovelCrawler()
                
                # 提取目录
                logger.info(f"提取小说目录: {novel.source_url}")
                catalog_data = crawler.extract_catalog(novel.source_url)
                
                if not catalog_data:
                    logger.error(f"目录提取失败")
                    return
                total_chapters = len(catalog_data['chapters'])
                logger.info(f"目录中共有 {total_chapters} 章")
                
                # 计算需要下载的章节
                start_chapter = existing_chapters + 1
                end_chapter = min(target_chapter, total_chapters)
                
                if start_chapter > total_chapters:
                    logger.info(f"已是最新章节，无需爬取")
                    return
                
                logger.info(f"准备爬取第 {start_chapter}-{end_chapter} 章")
                
                # 下载新章节
                downloaded_chapters = []
                for i in range(start_chapter, end_chapter + 1):
                    if i <= len(catalog_data['chapters']):
                        chapter_info = catalog_data['chapters'][i - 1]
                        logger.info(f"下载第 {i} 章: {chapter_info['title']}")
                        
                        result = crawler.download_chapter(chapter_info['url'], chapter_info['title'])
                        if result and 'content' in result:
                            downloaded_chapters.append({
                                'chapter_num': i,
                                'title': chapter_info['title'],
                                'content': result['content'],
                                'url': chapter_info['url']
                            })
                        else:
                            logger.error(f"第 {i} 章下载失败")
                
                download_result = {
                    'success': len(downloaded_chapters) > 0,
                    'chapters': downloaded_chapters
                }
                
                if download_result['success']:
                    # 导入到数据库
                    logger.info(f"开始导入 {len(downloaded_chapters)} 章到数据库")
                    
                    imported_count = 0
                    for chapter_data in downloaded_chapters:
                        try:
                            # 检查章节是否已存在
                            existing_chapter = Chapter.objects.filter(
                                novel=novel,
                                chapter_number=chapter_data['chapter_num']
                            ).first()
                            
                            if not existing_chapter:
                                # 创建新章节
                                Chapter.objects.create(
                                    novel=novel,
                                    title=chapter_data['title'],
                                    content=chapter_data['content'],
                                    chapter_number=chapter_data['chapter_num'],
                                    chapter_sort_number=chapter_data['chapter_num'],  # 确保排序字段正确
                                    source_url=chapter_data['url']
                                )
                                imported_count += 1
                                logger.info(f"成功导入第 {chapter_data['chapter_num']} 章")
                            else:
                                logger.info(f"第 {chapter_data['chapter_num']} 章已存在，跳过")
                                
                        except Exception as e:
                            logger.error(f"导入第 {chapter_data['chapter_num']} 章失败: {e}")
                    
                    import_result = {
                        'success': imported_count > 0,
                        'imported_count': imported_count,
                        'total_chapters': len(downloaded_chapters)
                    }
                    
                    if import_result['success']:
                        logger.info(f"自动爬取完成: 成功爬取 {len(download_result['chapters'])} 章")
                    else:
                        logger.error(f"导入数据库失败: {import_result.get('error', '未知错误')}")
                else:
                    logger.error(f"章节下载失败: {download_result.get('error', '未知错误')}")
                    
            except Exception as e:
                logger.error(f"自动爬取任务失败: {str(e)}")
        
        # 启动后台任务
        thread = threading.Thread(target=crawl_task)
        thread.daemon = True
        thread.start()
        
        return Response({
            'success': True,
            'task_id': task_id,
            'message': f'自动爬取任务已启动，目标爬取到第{target_chapter}章',
            'current_chapters': existing_chapters,
            'target_chapter': target_chapter
        })
        
    except Exception as e:
        logger.error(f"自动爬取API失败: {str(e)}")
        return Response({
            'success': False,
            'error': f'自动爬取失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
