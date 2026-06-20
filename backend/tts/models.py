from django.db import models
from django.utils import timezone
from novels.models import Novel, Chapter, Character
import os


class TTSEngine(models.Model):
    """TTS 引擎配置模型"""
    ENGINE_CHOICES = [
        ('gpt_sovits', 'GPT-SoVITS'),
        ('cosyvoice', 'CosyVoice'),
        ('xtts', 'XTTS'),
        ('indextts', 'IndexTTS'),
        ('fish_speech', 'Fish Speech'),
        ('edge_tts', 'Edge TTS'),
    ]

    name = models.CharField(max_length=100, verbose_name='引擎名称')
    engine_type = models.CharField(max_length=20, choices=ENGINE_CHOICES, verbose_name='引擎类型')
    description = models.TextField(blank=True, verbose_name='引擎描述')

    # API 配置
    api_url = models.URLField(blank=True, verbose_name='API 地址')
    api_key = models.CharField(max_length=500, blank=True, verbose_name='API Key')
    is_local = models.BooleanField(default=True, verbose_name='是否本地部署')

    # 默认参数
    default_params = models.JSONField(default=dict, verbose_name='默认参数',
                                      help_text='如 {"speed": 1.0, "temperature": 0.7}')

    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_default = models.BooleanField(default=False, verbose_name='是否默认引擎')
    priority = models.PositiveIntegerField(default=1, verbose_name='优先级')

    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'TTS 引擎'
        verbose_name_plural = 'TTS 引擎'
        ordering = ['-is_default', '-priority', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_engine_type_display()})'


class VoiceAsset(models.Model):
    """语音资源（参考音频）模型"""
    VOICE_TYPE_CHOICES = [
        ('narrator', '旁白'),
        ('male', '男声'),
        ('female', '女声'),
        ('child', '童声'),
        ('elderly', '老者'),
        ('custom', '自定义'),
    ]

    name = models.CharField(max_length=100, verbose_name='声音名称')
    description = models.TextField(blank=True, verbose_name='声音描述')
    voice_type = models.CharField(max_length=20, choices=VOICE_TYPE_CHOICES, default='custom',
                                  verbose_name='声音类型')

    # 关联角色（可选）
    character = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='voice_assets', verbose_name='关联角色')

    # 音频文件
    audio_file = models.FileField(upload_to='voices/', blank=True, null=True, verbose_name='参考音频文件')
    duration = models.FloatField(null=True, blank=True, verbose_name='时长(秒)')
    sample_rate = models.IntegerField(null=True, blank=True, verbose_name='采样率')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小(字节)')

    # 适用引擎
    compatible_engines = models.JSONField(default=list, verbose_name='兼容引擎',
                                           help_text='如 ["gpt_sovits", "cosyvoice"]')

    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    tags = models.CharField(max_length=200, blank=True, verbose_name='标签',
                            help_text='逗号分隔的标签，如 温柔,沉稳,普通话')

    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '语音资源'
        verbose_name_plural = '语音资源'
        ordering = ['-is_active', 'voice_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_voice_type_display()})'

    def save(self, *args, **kwargs):
        if self.audio_file:
            self.file_size = self.audio_file.size
        super().save(*args, **kwargs)

    @property
    def audio_url(self):
        if self.audio_file:
            return self.audio_file.url
        return None


class TTSGenerationTask(models.Model):
    """TTS 音频生成任务模型"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('preparing', '准备中'),
        ('generating', '生成中'),
        ('merging', '合并中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    name = models.CharField(max_length=200, verbose_name='任务名称')
    description = models.TextField(blank=True, verbose_name='任务描述')

    # 关联数据
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='tts_tasks',
                               verbose_name='所属小说')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='tts_tasks', verbose_name='关联章节')

    # 引擎配置
    engine = models.ForeignKey(TTSEngine, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='generation_tasks', verbose_name='使用引擎')

    # 任务状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending',
                              verbose_name='状态')
    progress = models.PositiveIntegerField(default=0, verbose_name='进度百分比')

    # 剧本数据 - 多说话人配置
    script_data = models.JSONField(default=list, verbose_name='剧本数据',
                                    help_text='[{speaker, text, emotion, voice_asset_id}, ...]')

    # 角色到语音资源的映射
    speaker_voice_map = models.JSONField(default=dict, verbose_name='角色语音映射',
                                          help_text='{speaker_name: voice_asset_id}')

    # 生成参数
    generation_params = models.JSONField(default=dict, verbose_name='生成参数')

    # 结果数据
    output_dir = models.CharField(max_length=500, blank=True, verbose_name='输出目录')
    merged_audio_path = models.CharField(max_length=500, blank=True, verbose_name='合并音频路径')
    total_segments = models.PositiveIntegerField(default=0, verbose_name='总片段数')
    completed_segments = models.PositiveIntegerField(default=0, verbose_name='已完成片段数')
    failed_segments = models.PositiveIntegerField(default=0, verbose_name='失败片段数')
    total_duration = models.FloatField(null=True, blank=True, verbose_name='总时长(秒)')

    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    processing_log = models.TextField(blank=True, verbose_name='处理日志')

    # 时间记录
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')

    class Meta:
        verbose_name = 'TTS 生成任务'
        verbose_name_plural = 'TTS 生成任务'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.get_status_display()}'

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            if self.started_at:
                self.processing_time = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        if self.total_segments > 0:
            return (self.completed_segments / self.total_segments) * 100
        return 0


class TTSSegmentResult(models.Model):
    """TTS 生成片段结果模型"""
    task = models.ForeignKey(TTSGenerationTask, on_delete=models.CASCADE, related_name='segment_results',
                              verbose_name='所属任务')
    sequence_number = models.PositiveIntegerField(verbose_name='序列号')
    speaker = models.CharField(max_length=100, verbose_name='说话人')
    text = models.TextField(verbose_name='文本内容')
    emotion = models.CharField(max_length=50, blank=True, verbose_name='情绪')

    # 使用的语音资源
    voice_asset = models.ForeignKey(VoiceAsset, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='使用的语音')

    # 结果
    audio_file = models.FileField(upload_to='generated_tts/', blank=True, null=True,
                                   verbose_name='生成的音频文件')
    duration = models.FloatField(null=True, blank=True, verbose_name='时长(秒)')
    status = models.CharField(max_length=20, choices=[
        ('pending', '待处理'),
        ('generating', '生成中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ], default='pending', verbose_name='状态')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        verbose_name = 'TTS 片段结果'
        verbose_name_plural = 'TTS 片段结果'
        ordering = ['task', 'sequence_number']
        unique_together = ['task', 'sequence_number']

    def __str__(self):
        return f'{self.task.name} - 片段{self.sequence_number} ({self.speaker})'
