"""
批量下载服务模块
提供全自动的小说批量下载功能
"""
import os
import sys
import time
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from django.db import transaction
from django_q.tasks import async_task

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from .models import Novel, Chapter, BatchDownloadTask, DownloadTaskLog

# 设置日志
logger = logging.getLogger(__name__)


class BatchDownloadService:
    """批量下载服务类"""
    
    def __init__(self):
        self.crawler = None
        self._init_crawler()
    
    def _init_crawler(self):
        """初始化爬虫"""
        try:
            from integrated_novel_crawler import IntegratedNovelCrawler
            self.crawler = IntegratedNovelCrawler()
            logger.info("爬虫初始化成功")
        except ImportError as e:
            logger.error(f"爬虫初始化失败: {e}")
            self.crawler = None
    
    def create_download_task(self, source_url: str, task_name: str = None) -> BatchDownloadTask:
        """
        创建下载任务
        
        Args:
            source_url: 小说源链接
            task_name: 任务名称（可选）
        
        Returns:
            BatchDownloadTask: 创建的下载任务
        """
        if not task_name:
            task_name = f"自动下载任务 - {timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 检查并清理相同URL的旧任务
        existing_tasks = BatchDownloadTask.objects.filter(source_url=source_url)
        for old_task in existing_tasks:
            if old_task.status in ['failed', 'cancelled']:
                # 删除失败或取消的任务
                old_task.delete()
                logger.info(f"删除旧的失败任务: {old_task.id}")
            elif old_task.status in ['pending', 'running']:
                # 如果有进行中的任务，返回现有任务
                logger.info(f"返回现有的进行中任务: {old_task.id}")
                return old_task
        
        # 创建任务记录
        task = BatchDownloadTask.objects.create(
            name=task_name,
            source_url=source_url,
            status='pending'
        )
        
        # 记录日志
        self._log_task(task, 'info', f'创建下载任务: {source_url}')
        
        # 提交到后台队列
        task_id = async_task(
            'novels.batch_download_service_fixed.execute_download_task',
            task.id,
            task_name=f'batch_download_{task.id}'
        )
        
        # 保存后台任务ID
        task.task_id = task_id
        task.save(update_fields=['task_id'])
        
        logger.info(f"创建下载任务成功: {task.id}, 后台任务ID: {task_id}")
        return task
    
    def _log_task(self, task: BatchDownloadTask, level: str, message: str, chapter_number: int = None):
        """记录任务日志"""
        DownloadTaskLog.objects.create(
            task=task,
            level=level,
            message=message,
            chapter_number=chapter_number
        )
        
        # 同时记录到系统日志
        log_func = getattr(logger, level, logger.info)
        log_func(f"任务 {task.id}: {message}")
    
    def _execute_download(self, task: BatchDownloadTask) -> bool:
        """
        执行具体的下载逻辑
        
        Args:
            task: 下载任务
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.crawler:
                self._log_task(task, 'error', '爬虫未初始化')
                return False
            
            # 1. 提取小说目录
            self._log_task(task, 'info', f'开始提取目录: {task.source_url}')
            catalog_data = self.crawler.extract_catalog(task.source_url)
            
            if not catalog_data or 'chapters' not in catalog_data:
                self._log_task(task, 'error', '目录提取失败')
                return False
            
            chapters = catalog_data['chapters']
            total_chapters = len(chapters)
            
            # 更新任务信息
            task.total_chapters = total_chapters
            task.save(update_fields=['total_chapters'])
            
            self._log_task(task, 'info', f'目录提取成功，共 {total_chapters} 章')
            
            # 2. 创建或获取小说记录
            novel = self._get_or_create_novel(task, catalog_data)
            if not novel:
                self._log_task(task, 'error', '小说记录创建失败')
                return False
            
            task.novel = novel
            task.save(update_fields=['novel'])
            
            # 3. 批量下载章节
            downloaded_count = 0
            failed_count = 0
            
            for i, chapter_info in enumerate(chapters, 1):
                try:
                    # 检查任务是否被取消或暂停
                    task.refresh_from_db()
                    if task.status in ['cancelled', 'paused']:
                        self._log_task(task, 'info', f'任务已{task.get_status_display()}，停止下载')
                        break
                    
                    # 检查章节是否已存在
                    existing_chapter = Chapter.objects.filter(
                        novel=novel,
                        chapter_sort_number=i
                    ).first()
                    
                    if existing_chapter:
                        self._log_task(task, 'info', f'第 {i} 章已存在，跳过', i)
                        downloaded_count += 1
                        continue
                    
                    # 下载章节
                    self._log_task(task, 'info', f'下载第 {i} 章: {chapter_info["title"]}', i)
                    
                    result = self.crawler.download_chapter(
                        chapter_info['url'], 
                        chapter_info['title']
                    )
                    
                    if result and 'content' in result:
                        # 保存章节到数据库，处理重复情况
                        try:
                            chapter, created = Chapter.objects.get_or_create(
                                novel=novel,
                                chapter_sort_number=i,
                                defaults={
                                    'title': chapter_info['title'],
                                    'content': result['content'],
                                    'source_url': chapter_info['url']
                                }
                            )
                            
                            if created:
                                downloaded_count += 1
                                self._log_task(task, 'success', f'第 {i} 章下载成功', i)
                            else:
                                downloaded_count += 1  # 已存在的章节也算成功
                                self._log_task(task, 'info', f'第 {i} 章已存在，跳过', i)
                        except Exception as db_error:
                            # 数据库冲突，尝试重新获取
                            try:
                                existing_chapter = Chapter.objects.get(
                                    novel=novel,
                                    chapter_sort_number=i
                                )
                                downloaded_count += 1
                                self._log_task(task, 'info', f'第 {i} 章已存在（冲突解决），跳过', i)
                            except Chapter.DoesNotExist:
                                failed_count += 1
                                self._log_task(task, 'error', f'第 {i} 章保存失败: {db_error}', i)
                    else:
                        failed_count += 1
                        self._log_task(task, 'error', f'第 {i} 章下载失败', i)
                    
                    # 更新进度
                    task.downloaded_chapters = downloaded_count
                    task.failed_chapters = failed_count
                    task.update_progress()
                    
                    # 下载间隔
                    if task.download_delay > 0:
                        time.sleep(task.download_delay)
                
                except Exception as e:
                    failed_count += 1
                    self._log_task(task, 'error', f'第 {i} 章下载异常: {e}', i)
                    
                    # 更新失败计数
                    task.failed_chapters = failed_count
                    task.save(update_fields=['failed_chapters'])
            
            # 4. 完成下载
            success_rate = (downloaded_count / total_chapters) * 100 if total_chapters > 0 else 0
            self._log_task(task, 'info', f'下载完成，成功率: {success_rate:.1f}% ({downloaded_count}/{total_chapters})')
            
            return success_rate > 80  # 成功率超过80%认为成功
            
        except Exception as e:
            self._log_task(task, 'error', f'下载执行异常: {e}')
            return False
    
    def _get_or_create_novel(self, task: BatchDownloadTask, catalog_data: Dict[str, Any]) -> Optional[Novel]:
        """获取或创建小说记录"""
        try:
            title = catalog_data.get('title', '未知小说')
            author = catalog_data.get('author', '未知作者')
            
            # 尝试根据标题和作者查找现有小说
            novel = Novel.objects.filter(
                title=title,
                author=author
            ).first()
            
            if novel:
                self._log_task(task, 'info', f'找到现有小说: {title}')
                return novel
            
            # 创建新小说
            novel = Novel.objects.create(
                title=title,
                author=author,
                description=catalog_data.get('description', ''),
                source_url=task.source_url,
                status='ongoing'  # 默认连载中
            )
            
            self._log_task(task, 'info', f'创建新小说: {title}')
            return novel
            
        except Exception as e:
            self._log_task(task, 'error', f'小说记录处理异常: {e}')
            return None


def execute_download_task(task_id: int):
    """
    执行下载任务的后台函数
    这个函数会被 Django-Q 调用
    
    Args:
        task_id: 下载任务ID
    """
    try:
        # 获取任务
        task = BatchDownloadTask.objects.get(id=task_id)
        service = BatchDownloadService()
        
        # 更新任务状态
        task.status = 'running'
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at'])
        
        service._log_task(task, 'info', '开始执行下载任务')
        
        # 执行下载
        success = service._execute_download(task)
        
        if success:
            task.status = 'completed'
            task.completed_at = timezone.now()
            service._log_task(task, 'success', '下载任务完成')
        else:
            task.status = 'failed'
            service._log_task(task, 'error', '下载任务失败')
        
        task.save(update_fields=['status', 'completed_at'])
        
    except Exception as e:
        logger.error(f"执行下载任务 {task_id} 时发生错误: {e}")
        try:
            task = BatchDownloadTask.objects.get(id=task_id)
            task.status = 'failed'
            task.error_message = str(e)
            task.save(update_fields=['status', 'error_message'])
            
            service = BatchDownloadService()
            service._log_task(task, 'error', f'任务执行异常: {e}')
        except:
            pass


# 任务管理函数
def pause_download_task(task_id: int) -> bool:
    """暂停下载任务"""
    try:
        task = BatchDownloadTask.objects.get(id=task_id)
        if task.status == 'running':
            task.status = 'paused'
            task.save(update_fields=['status'])
            return True
        return False
    except:
        return False


def resume_download_task(task_id: int) -> bool:
    """恢复下载任务"""
    try:
        task = BatchDownloadTask.objects.get(id=task_id)
        if task.status == 'paused':
            # 重新提交到队列
            new_task_id = async_task(
                'novels.batch_download_service_fixed.execute_download_task',
                task.id,
                task_name=f'batch_download_{task.id}_resume'
            )
            
            task.status = 'pending'
            task.task_id = new_task_id
            task.save(update_fields=['status', 'task_id'])
            return True
        return False
    except:
        return False


def cancel_download_task(task_id: int) -> bool:
    """取消下载任务"""
    try:
        task = BatchDownloadTask.objects.get(id=task_id)
        if task.status in ['pending', 'running', 'paused']:
            task.status = 'cancelled'
            task.save(update_fields=['status'])
            return True
        return False
    except:
        return False
