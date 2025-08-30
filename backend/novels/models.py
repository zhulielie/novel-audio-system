from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class NovelSource(models.Model):
    """小说来源模型"""
    name = models.CharField(max_length=100, verbose_name='来源名称')
    source_type = models.CharField(max_length=50, verbose_name='来源类型', help_text='网站类型或分类')
    base_url = models.URLField(verbose_name='基础URL')
    chapter_url_pattern = models.CharField(max_length=200, blank=True, verbose_name='章节URL模式')
    encoding = models.CharField(max_length=20, default='utf-8', verbose_name='页面编码')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    priority = models.PositiveIntegerField(default=1, verbose_name='优先级', help_text='数字越大优先级越高')
    last_crawl_at = models.DateTimeField(blank=True, null=True, verbose_name='最后爬取时间')
    crawl_count = models.PositiveIntegerField(default=0, verbose_name='爬取次数')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        verbose_name = '小说来源'
        verbose_name_plural = '小说来源'
        ordering = ['-priority', 'source_type']

    def __str__(self):
        return f'{self.name} ({self.source_type})'

    def get_source_type_display(self):
        """获取来源类型显示名称"""
        return self.source_type

    def get_crawler_class(self):
        """根据来源类型返回对应的爬虫类"""
        from .crawlers import get_crawler_class
        return get_crawler_class(self.source_type)


class Novel(models.Model):
    """小说模型"""
    title = models.CharField(max_length=200, verbose_name='小说标题')
    author = models.CharField(max_length=100, verbose_name='作者')
    description = models.TextField(blank=True, verbose_name='简介')
    source_url = models.URLField(blank=True, null=True, verbose_name='源URL', help_text='小说的原始网址，用于自动爬取')
    cover_image = models.ImageField(upload_to='novels/covers/', blank=True, null=True, verbose_name='封面')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    # 状态选择
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    class Meta:
        verbose_name = '小说'
        verbose_name_plural = '小说'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def chapter_count(self):
        return self.chapters.count()


class Chapter(models.Model):
    """章节模型"""
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters', verbose_name='所属小说')
    title = models.CharField(max_length=200, verbose_name='章节标题')
    content = models.TextField(verbose_name='章节内容')
    chapter_number = models.CharField(max_length=50, verbose_name='章节序号', help_text='支持中文数字，如"一千一百八十八"')
    chapter_sort_number = models.PositiveIntegerField(default=0, verbose_name='章节排序数字')
    volume = models.CharField(max_length=200, blank=True, null=True, verbose_name='卷信息', help_text='章节所属卷的信息，如"第十一卷真仙降世"')
    word_count = models.PositiveIntegerField(default=0, verbose_name='字数')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_published = models.BooleanField(default=False, verbose_name='是否发布')
    source_url = models.URLField(blank=True, null=True, verbose_name='来源链接', help_text='该章节的原始URL链接')
    
    class Meta:
        verbose_name = '章节'
        verbose_name_plural = '章节'
        ordering = ['novel', 'chapter_sort_number']
        unique_together = ['novel', 'chapter_sort_number']
    
    def __str__(self):
        return f'{self.novel.title} - 第{self.chapter_number}章 {self.title}'
    
    def save(self, *args, **kwargs):
        # 自动计算字数
        self.word_count = len(self.content)

        # 保护章节标题格式：但允许AI修复功能更新标题
        import re
        if hasattr(self, '_original_title') and self._original_title:
            # 检查是否有AI修复标记（在AI修复功能中设置）
            is_ai_fix = getattr(self, '_is_ai_fix', False)

            if not is_ai_fix:
                # 只有在非AI修复的情况下才保护原始标题格式
                if re.match(r'第[一二三四五六七八九十百千]+章$', self._original_title):
                    if not re.match(r'第[一二三四五六七八九十百千]+章$', self.title):
                        # 如果原始标题是中文格式但当前不是，恢复原始标题
                        print(f"警告：章节标题被意外修改，从 '{self.title}' 恢复为 '{self._original_title}'")
                        self.title = self._original_title

        super().save(*args, **kwargs)

        # 记录原始标题用于下次比较
        if not hasattr(self, '_original_title'):
            self._original_title = self.title


class NovelSourceRelation(models.Model):
    """小说与来源的关联模型"""
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, verbose_name='小说')
    source = models.ForeignKey(NovelSource, on_delete=models.CASCADE, verbose_name='来源')
    source_url = models.URLField(verbose_name='来源URL', help_text='具体的小说页面URL')
    is_primary = models.BooleanField(default=False, verbose_name='是否主来源')
    last_sync_at = models.DateTimeField(blank=True, null=True, verbose_name='最后同步时间')
    sync_count = models.PositiveIntegerField(default=0, verbose_name='同步次数')
    chapter_count = models.PositiveIntegerField(default=0, verbose_name='来源章节数')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        verbose_name = '小说来源关联'
        verbose_name_plural = '小说来源关联'
        unique_together = ['novel', 'source']
        ordering = ['-is_primary', '-last_sync_at']

    def __str__(self):
        return f'{self.novel.title} - {self.source.name}'


class Character(models.Model):
    """角色模型"""
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='characters', verbose_name='所属小说')
    name = models.CharField(max_length=100, verbose_name='角色名称')
    description = models.TextField(blank=True, verbose_name='角色描述')
    voice_style = models.CharField(max_length=50, blank=True, verbose_name='语音风格')
    avatar = models.ImageField(upload_to='characters/avatars/', blank=True, null=True, verbose_name='头像')
    is_main_character = models.BooleanField(default=False, verbose_name='是否主角')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '角色'
        verbose_name_plural = '角色'
        ordering = ['-is_main_character', 'name']
    
    def __str__(self):
        return f'{self.novel.title} - {self.name}'


class NovelTag(models.Model):
    """小说标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='标签颜色')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class NovelTagRelation(models.Model):
    """小说标签关联模型"""
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='tag_relations')
    tag = models.ForeignKey(NovelTag, on_delete=models.CASCADE, related_name='novel_relations')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '小说标签关联'
        verbose_name_plural = '小说标签关联'
        unique_together = ['novel', 'tag']
    
    def __str__(self):
        return f'{self.novel.title} - {self.tag.name}'


# 导入爬虫相关模型
from .crawler_models import (
    CrawlerTask,
    CrawlerConfig, 
    CrawlerLog,
    NovelCatalog,
    ChapterDownloadRecord
)


class BatchDownloadTask(models.Model):
    """批量下载任务模型"""
    TASK_STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '下载中'),
        ('paused', '已暂停'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    # 基本信息
    name = models.CharField(max_length=200, verbose_name='任务名称')
    source_url = models.URLField(verbose_name='小说源链接')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, null=True, blank=True, verbose_name='关联小说')
    
    # 任务状态
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='pending', verbose_name='任务状态')
    progress = models.FloatField(default=0.0, verbose_name='下载进度', help_text='0-100的百分比')
    
    # 下载统计
    total_chapters = models.PositiveIntegerField(default=0, verbose_name='总章节数')
    downloaded_chapters = models.PositiveIntegerField(default=0, verbose_name='已下载章节数')
    failed_chapters = models.PositiveIntegerField(default=0, verbose_name='失败章节数')
    
    # 配置选项
    auto_retry = models.BooleanField(default=True, verbose_name='自动重试')
    max_retries = models.PositiveIntegerField(default=3, verbose_name='最大重试次数')
    download_delay = models.FloatField(default=1.0, verbose_name='下载间隔(秒)')
    
    # 时间信息
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # Django-Q 任务ID
    task_id = models.CharField(max_length=100, blank=True, verbose_name='后台任务ID')
    
    class Meta:
        verbose_name = '批量下载任务'
        verbose_name_plural = '批量下载任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'
    
    @property
    def progress_percentage(self):
        """获取进度百分比"""
        if self.total_chapters == 0:
            return 0
        return (self.downloaded_chapters / self.total_chapters) * 100
    
    def update_progress(self):
        """更新下载进度"""
        self.progress = self.progress_percentage
        self.save(update_fields=['progress'])


class DownloadTaskLog(models.Model):
    """下载任务日志模型"""
    LOG_LEVEL_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('success', '成功'),
    ]
    
    task = models.ForeignKey(BatchDownloadTask, on_delete=models.CASCADE, related_name='logs', verbose_name='关联任务')
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info', verbose_name='日志级别')
    message = models.TextField(verbose_name='日志消息')
    chapter_number = models.PositiveIntegerField(null=True, blank=True, verbose_name='章节号')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '下载任务日志'
        verbose_name_plural = '下载任务日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.task.name} - {self.get_level_display()}: {self.message[:50]}'


class UserReadingSettings(models.Model):
    """用户阅读设置模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reading_settings', verbose_name='用户')
    
    # 阅读偏好设置
    auto_crawl_enabled = models.BooleanField(default=True, verbose_name='启用自动爬取')
    crawl_ahead_chapters = models.PositiveIntegerField(default=3, verbose_name='提前爬取章节数')
    font_size = models.PositiveIntegerField(default=16, verbose_name='字体大小')
    line_height = models.FloatField(default=1.6, verbose_name='行高')
    background_color = models.CharField(max_length=20, default='white', verbose_name='背景颜色')
    reading_mode = models.CharField(max_length=20, default='page', verbose_name='阅读模式', choices=[
        ('page', '翻页模式'),
        ('scroll', '连续模式')
    ])
    
    # 自动保存设置
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户阅读设置'
        verbose_name_plural = '用户阅读设置'
    
    def __str__(self):
        return f'{self.user.username} 的阅读设置'
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """获取或创建用户的阅读设置"""
        settings, created = cls.objects.get_or_create(user=user)
        return settings
