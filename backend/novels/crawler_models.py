#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫相关数据模型
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import json


class CrawlerTask(models.Model):
    """爬虫任务模型"""
    
    TASK_STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('catalog_extract', '目录提取'),
        ('chapter_download', '章节下载'),
        ('batch_import', '批量导入'),
    ]
    
    # 基本信息
    task_id = models.CharField(max_length=100, unique=True, verbose_name='任务ID')
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending', verbose_name='任务状态')
    
    # 关联信息
    novel = models.ForeignKey('Novel', on_delete=models.CASCADE, null=True, blank=True, verbose_name='关联小说')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='创建用户')
    
    # 任务参数
    source_url = models.URLField(verbose_name='源URL')
    parameters = models.JSONField(default=dict, verbose_name='任务参数')
    
    # 执行信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    
    # 结果信息
    result_data = models.JSONField(default=dict, verbose_name='结果数据')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 统计信息
    total_items = models.IntegerField(default=0, verbose_name='总项目数')
    processed_items = models.IntegerField(default=0, verbose_name='已处理项目数')
    success_items = models.IntegerField(default=0, verbose_name='成功项目数')
    failed_items = models.IntegerField(default=0, verbose_name='失败项目数')
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '爬虫任务'
        verbose_name_plural = '爬虫任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.get_task_type_display()} - {self.task_id}'
    
    @property
    def duration(self):
        """任务执行时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return timezone.now() - self.started_at
        return None
    
    @property
    def success_rate(self):
        """成功率"""
        if self.processed_items > 0:
            return (self.success_items / self.processed_items) * 100
        return 0
    
    def update_progress(self, processed=None, success=None, failed=None, progress=None):
        """更新任务进度"""
        if processed is not None:
            self.processed_items = processed
        if success is not None:
            self.success_items = success
        if failed is not None:
            self.failed_items = failed
        if progress is not None:
            self.progress = progress
        elif self.total_items > 0:
            self.progress = int((self.processed_items / self.total_items) * 100)
        
        self.save(update_fields=['processed_items', 'success_items', 'failed_items', 'progress', 'updated_at'])


class CrawlerConfig(models.Model):
    """爬虫配置模型"""
    
    CONFIG_TYPE_CHOICES = [
        ('site_config', '站点配置'),
        ('selector_config', '选择器配置'),
        ('request_config', '请求配置'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='配置名称')
    config_type = models.CharField(max_length=50, choices=CONFIG_TYPE_CHOICES, verbose_name='配置类型')
    site_domain = models.CharField(max_length=200, verbose_name='站点域名')
    
    # 配置数据
    config_data = models.JSONField(default=dict, verbose_name='配置数据')
    
    # 状态信息
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    priority = models.IntegerField(default=1, verbose_name='优先级')
    
    # 统计信息
    success_count = models.IntegerField(default=0, verbose_name='成功次数')
    fail_count = models.IntegerField(default=0, verbose_name='失败次数')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='最后使用时间')
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '爬虫配置'
        verbose_name_plural = '爬虫配置'
        ordering = ['-priority', 'site_domain']
        unique_together = ['name', 'site_domain']
    
    def __str__(self):
        return f'{self.name} - {self.site_domain}'
    
    @property
    def success_rate(self):
        """成功率"""
        total = self.success_count + self.fail_count
        if total > 0:
            return (self.success_count / total) * 100
        return 0


class CrawlerLog(models.Model):
    """爬虫日志模型"""
    
    LOG_LEVEL_CHOICES = [
        ('debug', 'DEBUG'),
        ('info', 'INFO'),
        ('warning', 'WARNING'),
        ('error', 'ERROR'),
        ('critical', 'CRITICAL'),
    ]
    
    task = models.ForeignKey(CrawlerTask, on_delete=models.CASCADE, related_name='logs', verbose_name='关联任务')
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, verbose_name='日志级别')
    message = models.TextField(verbose_name='日志消息')
    
    # 额外数据
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='额外数据')
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '爬虫日志'
        verbose_name_plural = '爬虫日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.get_level_display()} - {self.message[:50]}'


class NovelCatalog(models.Model):
    """小说目录模型"""
    
    novel = models.OneToOneField('Novel', on_delete=models.CASCADE, related_name='catalog', verbose_name='关联小说')
    source_url = models.URLField(verbose_name='目录源URL')
    
    # 目录信息
    title = models.CharField(max_length=200, verbose_name='小说标题')
    author = models.CharField(max_length=100, verbose_name='作者')
    description = models.TextField(blank=True, verbose_name='简介')
    
    # 章节信息
    total_chapters = models.IntegerField(default=0, verbose_name='总章节数')
    chapters_data = models.JSONField(default=list, verbose_name='章节数据')
    
    # 提取信息
    extracted_at = models.DateTimeField(null=True, blank=True, verbose_name='提取时间')
    extractor_version = models.CharField(max_length=50, blank=True, verbose_name='提取器版本')
    
    # 状态信息
    is_valid = models.BooleanField(default=True, verbose_name='是否有效')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='最后更新')
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '小说目录'
        verbose_name_plural = '小说目录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.title} - 目录 ({self.total_chapters}章)'
    
    def get_chapter_by_number(self, chapter_num):
        """根据章节号获取章节信息"""
        for chapter in self.chapters_data:
            if chapter.get('chapter_num') == chapter_num:
                return chapter
        return None
    
    def get_chapters_range(self, start_num, end_num):
        """获取指定范围的章节"""
        return [
            chapter for chapter in self.chapters_data
            if start_num <= chapter.get('chapter_num', 0) <= end_num
        ]


class ChapterDownloadRecord(models.Model):
    """章节下载记录模型"""
    
    DOWNLOAD_STATUS_CHOICES = [
        ('pending', '等待下载'),
        ('downloading', '下载中'),
        ('completed', '下载完成'),
        ('failed', '下载失败'),
        ('skipped', '已跳过'),
    ]
    
    task = models.ForeignKey(CrawlerTask, on_delete=models.CASCADE, related_name='download_records', verbose_name='关联任务')
    chapter = models.ForeignKey('Chapter', on_delete=models.CASCADE, null=True, blank=True, verbose_name='关联章节')
    
    # 章节信息
    chapter_title = models.CharField(max_length=200, verbose_name='章节标题')
    chapter_number = models.IntegerField(verbose_name='章节号')
    source_url = models.URLField(verbose_name='章节源URL')
    
    # 下载状态
    status = models.CharField(max_length=20, choices=DOWNLOAD_STATUS_CHOICES, default='pending', verbose_name='下载状态')
    
    # 内容信息
    content_length = models.IntegerField(default=0, verbose_name='内容长度')
    watermark_removed = models.BooleanField(default=False, verbose_name='是否去除水印')
    
    # 执行信息
    download_started_at = models.DateTimeField(null=True, blank=True, verbose_name='下载开始时间')
    download_completed_at = models.DateTimeField(null=True, blank=True, verbose_name='下载完成时间')
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间戳
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '章节下载记录'
        verbose_name_plural = '章节下载记录'
        ordering = ['task', 'chapter_number']
        unique_together = ['task', 'chapter_number']
    
    def __str__(self):
        return f'{self.chapter_title} - {self.get_status_display()}'
    
    @property
    def download_duration(self):
        """下载耗时"""
        if self.download_started_at and self.download_completed_at:
            return self.download_completed_at - self.download_started_at
        return None
