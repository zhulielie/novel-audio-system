from django.db import models
from django.utils import timezone
from novels.models import Chapter, Character
from audios.models import AudioProject, EmotionType
from llms.models import LLMModel, LLMRequest
import json


class ScriptGenerationTask(models.Model):
    """脚本生成任务模型"""
    name = models.CharField(max_length=200, verbose_name='任务名称')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='script_tasks', verbose_name='源章节')
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='script_tasks', verbose_name='主要角色')
    llm_model = models.ForeignKey(LLMModel, on_delete=models.CASCADE, related_name='script_tasks', verbose_name='使用模型')
    
    # 生成参数
    generation_params = models.JSONField(default=dict, verbose_name='生成参数')
    emotion_analysis_enabled = models.BooleanField(default=True, verbose_name='启用情绪分析')
    segment_length = models.PositiveIntegerField(default=200, verbose_name='分段长度')
    
    # 任务状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('analyzing', '分析中'),
            ('generating', '生成中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='pending',
        verbose_name='状态'
    )
    
    # 结果数据
    generated_script = models.TextField(blank=True, verbose_name='生成的脚本')
    emotion_analysis_result = models.JSONField(default=dict, blank=True, verbose_name='情绪分析结果')
    processing_log = models.TextField(blank=True, verbose_name='处理日志')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    result = models.JSONField(default=dict, blank=True, verbose_name='结果数据')  # 添加result字段
    progress = models.PositiveIntegerField(default=0, verbose_name='进度百分比')  # 添加progress字段
    
    # 时间记录
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')
    
    class Meta:
        verbose_name = '脚本生成任务'
        verbose_name_plural = '脚本生成任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} - {self.chapter.title}'
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            if self.started_at:
                self.processing_time = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)


class ScriptSegment(models.Model):
    """脚本片段模型"""
    task = models.ForeignKey(ScriptGenerationTask, on_delete=models.CASCADE, related_name='segments', verbose_name='所属任务')
    sequence_number = models.PositiveIntegerField(verbose_name='序列号')
    original_text = models.TextField(verbose_name='原始文本')
    processed_text = models.TextField(verbose_name='处理后文本')
    content = models.TextField(verbose_name='内容')  # 添加content字段
    character = models.ForeignKey(Character, on_delete=models.CASCADE, null=True, blank=True, verbose_name='角色')  # 添加character字段
    emotion_type = models.ForeignKey(EmotionType, on_delete=models.CASCADE, null=True, blank=True, verbose_name='情绪类型')
    emotion_confidence = models.FloatField(null=True, blank=True, verbose_name='情绪置信度')
    speaker = models.CharField(max_length=100, blank=True, verbose_name='说话人')
    duration_estimate = models.FloatField(null=True, blank=True, verbose_name='预估时长(秒)')
    processing_notes = models.TextField(blank=True, verbose_name='处理备注')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='元数据')  # 添加metadata字段
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '脚本片段'
        verbose_name_plural = '脚本片段'
        ordering = ['task', 'sequence_number']
        unique_together = ['task', 'sequence_number']
    
    def __str__(self):
        return f'{self.task.name} - 片段{self.sequence_number}'
    
    @property
    def word_count(self):
        """计算字数"""
        return len(self.content) if self.content else 0


class AudioGenerationTask(models.Model):
    """音频生成任务模型"""
    name = models.CharField(max_length=200, verbose_name='任务名称')
    script_task = models.ForeignKey(ScriptGenerationTask, on_delete=models.CASCADE, related_name='audio_tasks', verbose_name='脚本任务')
    audio_project = models.ForeignKey(AudioProject, on_delete=models.CASCADE, related_name='generation_tasks', verbose_name='音频项目')
    
    # 生成参数
    voice_settings = models.JSONField(default=dict, verbose_name='语音设置')
    quality_level = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿质量'),
            ('standard', '标准质量'),
            ('high', '高质量'),
            ('premium', '顶级质量'),
        ],
        default='standard',
        verbose_name='质量等级'
    )
    
    # 任务状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('preparing', '准备中'),
            ('generating', '生成中'),
            ('post_processing', '后处理中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='pending',
        verbose_name='状态'
    )
    
    # 进度信息
    total_segments = models.PositiveIntegerField(default=0, verbose_name='总片段数')
    completed_segments = models.PositiveIntegerField(default=0, verbose_name='已完成片段数')
    failed_segments = models.PositiveIntegerField(default=0, verbose_name='失败片段数')
    
    # 结果数据
    output_file_path = models.CharField(max_length=500, blank=True, verbose_name='输出文件路径')
    total_duration = models.FloatField(null=True, blank=True, verbose_name='总时长(秒)')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小(字节)')
    processing_log = models.TextField(blank=True, verbose_name='处理日志')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    generation_params = models.JSONField(default=dict, blank=True, verbose_name='生成参数')  # 添加generation_params字段
    progress = models.PositiveIntegerField(default=0, verbose_name='进度百分比')  # 添加progress字段
    
    # 时间记录
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')
    
    class Meta:
        verbose_name = '音频生成任务'
        verbose_name_plural = '音频生成任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} - {self.script_task.chapter.title}'
    
    @property
    def progress_percentage(self):
        if self.total_segments > 0:
            return (self.completed_segments / self.total_segments) * 100
        return 0
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            if self.started_at:
                self.processing_time = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)


class GenerationWorkflow(models.Model):
    """生成工作流模型"""
    name = models.CharField(max_length=200, verbose_name='工作流名称')
    description = models.TextField(blank=True, verbose_name='工作流描述')
    
    # 工作流配置
    workflow_config = models.JSONField(default=dict, verbose_name='工作流配置')
    is_template = models.BooleanField(default=False, verbose_name='是否为模板')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 关联的任务
    script_task = models.ForeignKey(ScriptGenerationTask, on_delete=models.CASCADE, null=True, blank=True, related_name='workflows', verbose_name='脚本任务')
    audio_task = models.ForeignKey(AudioGenerationTask, on_delete=models.CASCADE, null=True, blank=True, related_name='workflows', verbose_name='音频任务')
    
    # 工作流状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('running', '运行中'),
            ('paused', '暂停'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='draft',
        verbose_name='状态'
    )
    
    # 执行信息
    current_step = models.CharField(max_length=100, blank=True, verbose_name='当前步骤')
    execution_log = models.TextField(blank=True, verbose_name='执行日志')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间记录
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    class Meta:
        verbose_name = '生成工作流'
        verbose_name_plural = '生成工作流'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class GenerationStatistics(models.Model):
    """生成统计模型"""
    date = models.DateField(verbose_name='统计日期')
    
    # 脚本生成统计
    script_tasks_created = models.PositiveIntegerField(default=0, verbose_name='创建的脚本任务数')
    script_tasks_completed = models.PositiveIntegerField(default=0, verbose_name='完成的脚本任务数')
    script_tasks_failed = models.PositiveIntegerField(default=0, verbose_name='失败的脚本任务数')
    total_script_processing_time = models.FloatField(default=0, verbose_name='脚本处理总时间(秒)')
    
    # 音频生成统计
    audio_tasks_created = models.PositiveIntegerField(default=0, verbose_name='创建的音频任务数')
    audio_tasks_completed = models.PositiveIntegerField(default=0, verbose_name='完成的音频任务数')
    audio_tasks_failed = models.PositiveIntegerField(default=0, verbose_name='失败的音频任务数')
    total_audio_processing_time = models.FloatField(default=0, verbose_name='音频处理总时间(秒)')
    total_audio_duration = models.FloatField(default=0, verbose_name='生成音频总时长(秒)')
    
    # LLM使用统计
    llm_requests_count = models.PositiveIntegerField(default=0, verbose_name='LLM请求次数')
    llm_total_tokens = models.PositiveIntegerField(default=0, verbose_name='LLM总令牌数')
    llm_total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0, verbose_name='LLM总成本')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '生成统计'
        verbose_name_plural = '生成统计'
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f'{self.date} 统计数据'
