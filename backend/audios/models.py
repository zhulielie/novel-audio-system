from django.db import models
from django.utils import timezone
from novels.models import Chapter, Character
import os


class AudioProject(models.Model):
    """音频项目模型"""
    name = models.CharField(max_length=200, verbose_name='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='audio_projects', verbose_name='关联章节')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='audio_projects', verbose_name='主要角色')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='draft',
        verbose_name='状态'
    )
    
    class Meta:
        verbose_name = '音频项目'
        verbose_name_plural = '音频项目'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} - {self.chapter.title}'


class EmotionType(models.Model):
    """情绪类型模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='情绪名称')
    code = models.CharField(max_length=20, unique=True, verbose_name='情绪代码')
    description = models.TextField(blank=True, verbose_name='情绪描述')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='显示颜色')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '情绪类型'
        verbose_name_plural = '情绪类型'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EmotionAudio(models.Model):
    """情绪音频模型"""
    emotion_type = models.ForeignKey(EmotionType, on_delete=models.CASCADE, related_name='audios', verbose_name='情绪类型')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='emotion_audios', verbose_name='角色')
    audio_file = models.FileField(upload_to='emotion_audios/', verbose_name='音频文件')
    file_type = models.CharField(
        max_length=20,
        choices=[
            ('main', '主要音频'),
            ('short', '短音频'),
            ('long', '长音频'),
            ('alt1', '备选音频1'),
            ('alt2', '备选音频2'),
        ],
        default='main',
        verbose_name='文件类型'
    )
    duration = models.FloatField(null=True, blank=True, verbose_name='时长(秒)')
    sample_rate = models.IntegerField(null=True, blank=True, verbose_name='采样率')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小(字节)')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '情绪音频'
        verbose_name_plural = '情绪音频'
        ordering = ['emotion_type', 'character', 'file_type']
        unique_together = ['emotion_type', 'character', 'file_type']
    
    def __str__(self):
        return f'{self.character.name} - {self.emotion_type.name} - {self.get_file_type_display()}'
    
    def save(self, *args, **kwargs):
        if self.audio_file:
            # 获取文件大小
            self.file_size = self.audio_file.size
        super().save(*args, **kwargs)


class GeneratedAudio(models.Model):
    """生成的音频模型"""
    project = models.ForeignKey(AudioProject, on_delete=models.CASCADE, related_name='generated_audios', verbose_name='所属项目')
    text_content = models.TextField(verbose_name='文本内容')
    emotion_type = models.ForeignKey(EmotionType, on_delete=models.CASCADE, verbose_name='情绪类型')
    audio_file = models.FileField(upload_to='generated_audios/', verbose_name='生成的音频文件')
    sequence_number = models.PositiveIntegerField(verbose_name='序列号')
    duration = models.FloatField(null=True, blank=True, verbose_name='时长(秒)')
    generation_params = models.JSONField(default=dict, blank=True, verbose_name='生成参数')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '生成音频'
        verbose_name_plural = '生成音频'
        ordering = ['project', 'sequence_number']
        unique_together = ['project', 'sequence_number']
    
    def __str__(self):
        return f'{self.project.name} - 片段{self.sequence_number}'


class AudioTemplate(models.Model):
    """音频模板模型"""
    name = models.CharField(max_length=100, verbose_name='模板名称')
    description = models.TextField(blank=True, verbose_name='模板描述')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='audio_templates', verbose_name='适用角色')
    voice_settings = models.JSONField(default=dict, verbose_name='语音设置')
    emotion_mapping = models.JSONField(default=dict, verbose_name='情绪映射')
    is_default = models.BooleanField(default=False, verbose_name='是否默认模板')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '音频模板'
        verbose_name_plural = '音频模板'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f'{self.character.name} - {self.name}'


class AudioProcessingLog(models.Model):
    """音频处理日志模型"""
    project = models.ForeignKey(AudioProject, on_delete=models.CASCADE, related_name='processing_logs', verbose_name='所属项目')
    step = models.CharField(max_length=100, verbose_name='处理步骤')
    status = models.CharField(
        max_length=20,
        choices=[
            ('started', '开始'),
            ('processing', '处理中'),
            ('completed', '完成'),
            ('failed', '失败'),
        ],
        verbose_name='状态'
    )
    message = models.TextField(blank=True, verbose_name='消息')
    error_details = models.TextField(blank=True, verbose_name='错误详情')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '音频处理日志'
        verbose_name_plural = '音频处理日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.project.name} - {self.step} - {self.get_status_display()}'
