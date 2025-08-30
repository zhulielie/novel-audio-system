"""
批量下载API视图
提供批量下载任务的管理接口
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import BatchDownloadTask, DownloadTaskLog
from .batch_download_service_fixed import (
    BatchDownloadService, 
    pause_download_task, 
    resume_download_task, 
    cancel_download_task
)


class TaskPagination(PageNumberPagination):
    """任务分页"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_batch_download(request):
    """
    创建批量下载任务
    
    POST /api/novels/batch-download/create/
    {
        "source_url": "https://example.com/novel/123",
        "task_name": "小说名称（可选）"
    }
    """
    try:
        source_url = request.data.get('source_url')
        task_name = request.data.get('task_name')
        
        if not source_url:
            return Response({
                'success': False,
                'error': '请提供小说源链接'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查是否已有相同URL的进行中任务
        existing_task = BatchDownloadTask.objects.filter(
            source_url=source_url,
            status__in=['pending', 'running']
        ).first()
        
        if existing_task:
            return Response({
                'success': False,
                'error': '该小说已有进行中的下载任务',
                'existing_task_id': existing_task.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建下载任务
        service = BatchDownloadService()
        task = service.create_download_task(source_url, task_name)
        
        return Response({
            'success': True,
            'message': '下载任务创建成功',
            'task': {
                'id': task.id,
                'name': task.name,
                'source_url': task.source_url,
                'status': task.status,
                'created_at': task.created_at
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'创建任务失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_download_tasks(request):
    """
    获取下载任务列表
    
    GET /api/novels/batch-download/list/
    参数:
    - status: 任务状态筛选
    - search: 搜索任务名称
    """
    try:
        queryset = BatchDownloadTask.objects.all().order_by('-created_at')
        
        # 状态筛选
        task_status = request.GET.get('status')
        if task_status:
            queryset = queryset.filter(status=task_status)
        
        # 搜索
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(source_url__icontains=search)
            )
        
        # 分页
        paginator = TaskPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # 序列化数据
        tasks_data = []
        for task in page:
            tasks_data.append({
                'id': task.id,
                'name': task.name,
                'source_url': task.source_url,
                'status': task.status,
                'status_display': task.get_status_display(),
                'progress': task.progress,
                'total_chapters': task.total_chapters,
                'downloaded_chapters': task.downloaded_chapters,
                'failed_chapters': task.failed_chapters,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'novel': {
                    'id': task.novel.id,
                    'title': task.novel.title,
                    'author': task.novel.author
                } if task.novel else None
            })
        
        return paginator.get_paginated_response(tasks_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取任务列表失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_detail(request, task_id):
    """
    获取任务详情
    
    GET /api/novels/batch-download/{task_id}/
    """
    try:
        task = get_object_or_404(BatchDownloadTask, id=task_id)
        
        # 获取最近的日志
        recent_logs = task.logs.all()[:50]
        logs_data = [{
            'id': log.id,
            'level': log.level,
            'level_display': log.get_level_display(),
            'message': log.message,
            'chapter_number': log.chapter_number,
            'created_at': log.created_at
        } for log in recent_logs]
        
        return Response({
            'success': True,
            'task': {
                'id': task.id,
                'name': task.name,
                'source_url': task.source_url,
                'status': task.status,
                'status_display': task.get_status_display(),
                'progress': task.progress,
                'total_chapters': task.total_chapters,
                'downloaded_chapters': task.downloaded_chapters,
                'failed_chapters': task.failed_chapters,
                'auto_retry': task.auto_retry,
                'max_retries': task.max_retries,
                'download_delay': task.download_delay,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'error_message': task.error_message,
                'novel': {
                    'id': task.novel.id,
                    'title': task.novel.title,
                    'author': task.novel.author
                } if task.novel else None,
                'logs': logs_data
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取任务详情失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pause_task(request, task_id):
    """
    暂停下载任务
    
    POST /api/novels/batch-download/{task_id}/pause/
    """
    try:
        success = pause_download_task(task_id)
        
        if success:
            return Response({
                'success': True,
                'message': '任务已暂停'
            })
        else:
            return Response({
                'success': False,
                'error': '任务暂停失败，可能任务不存在或状态不允许暂停'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'暂停任务失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resume_task(request, task_id):
    """
    恢复下载任务
    
    POST /api/novels/batch-download/{task_id}/resume/
    """
    try:
        success = resume_download_task(task_id)
        
        if success:
            return Response({
                'success': True,
                'message': '任务已恢复'
            })
        else:
            return Response({
                'success': False,
                'error': '任务恢复失败，可能任务不存在或状态不允许恢复'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'恢复任务失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_task(request, task_id):
    """
    取消下载任务
    
    POST /api/novels/batch-download/{task_id}/cancel/
    """
    try:
        success = cancel_download_task(task_id)
        
        if success:
            return Response({
                'success': True,
                'message': '任务已取消'
            })
        else:
            return Response({
                'success': False,
                'error': '任务取消失败，可能任务不存在或状态不允许取消'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'取消任务失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_stats(request):
    """
    获取任务统计信息
    
    GET /api/novels/batch-download/stats/
    """
    try:
        from django.db.models import Count
        
        # 统计各状态的任务数量
        stats = BatchDownloadTask.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            running=Count('id', filter=Q(status='running')),
            completed=Count('id', filter=Q(status='completed')),
            failed=Count('id', filter=Q(status='failed')),
            cancelled=Count('id', filter=Q(status='cancelled')),
            paused=Count('id', filter=Q(status='paused'))
        )
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取统计信息失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_create_downloads(request):
    """
    批量创建下载任务
    
    POST /api/novels/batch-download/batch-create/
    {
        "urls": [
            {"url": "https://example.com/novel/1", "name": "小说1"},
            {"url": "https://example.com/novel/2", "name": "小说2"}
        ]
    }
    """
    try:
        urls_data = request.data.get('urls', [])
        
        if not urls_data:
            return Response({
                'success': False,
                'error': '请提供要下载的小说链接列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = BatchDownloadService()
        created_tasks = []
        failed_urls = []
        
        for url_info in urls_data:
            try:
                url = url_info.get('url')
                name = url_info.get('name')
                
                if not url:
                    failed_urls.append({'url': url_info, 'error': '缺少URL'})
                    continue
                
                # 检查是否已有相同URL的进行中任务
                existing_task = BatchDownloadTask.objects.filter(
                    source_url=url,
                    status__in=['pending', 'running']
                ).first()
                
                if existing_task:
                    failed_urls.append({'url': url, 'error': '已有进行中的任务'})
                    continue
                
                # 创建任务
                task = service.create_download_task(url, name)
                created_tasks.append({
                    'id': task.id,
                    'name': task.name,
                    'url': task.source_url
                })
                
            except Exception as e:
                failed_urls.append({'url': url_info.get('url', '未知'), 'error': str(e)})
        
        return Response({
            'success': True,
            'message': f'批量创建完成，成功 {len(created_tasks)} 个，失败 {len(failed_urls)} 个',
            'created_tasks': created_tasks,
            'failed_urls': failed_urls
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'批量创建失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
