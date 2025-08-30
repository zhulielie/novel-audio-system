from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator
import json
import uuid


class LLMProvider(models.Model):
    """LLM提供商模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='提供商名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='提供商代码')
    base_url = models.URLField(verbose_name='API基础URL')
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'LLM提供商'
        verbose_name_plural = 'LLM提供商'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LLMModel(models.Model):
    """LLM模型信息"""
    provider = models.ForeignKey(LLMProvider, on_delete=models.CASCADE, related_name='models', verbose_name='提供商')
    name = models.CharField(max_length=100, verbose_name='模型名称')
    model_id = models.CharField(max_length=100, verbose_name='模型ID')
    model_type = models.CharField(max_length=50, choices=[
        ('text', '文本生成'),
        ('chat', '对话模型'),
        ('embedding', '嵌入模型'),
        ('image', '图像模型'),
    ], default='text', verbose_name='模型类型')
    description = models.TextField(blank=True, verbose_name='模型描述')
    max_tokens = models.PositiveIntegerField(default=4096, verbose_name='最大令牌数')
    context_length = models.PositiveIntegerField(default=4096, verbose_name='上下文长度')
    supports_functions = models.BooleanField(default=False, verbose_name='支持函数调用')
    supports_vision = models.BooleanField(default=False, verbose_name='支持视觉')
    input_price_per_token = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name='输入价格/令牌')
    output_price_per_token = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name='输出价格/令牌')
    cost_per_1k_input = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='每1K输入令牌成本')
    cost_per_1k_output = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='每1K输出令牌成本')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_default_assistant = models.BooleanField(default=False, verbose_name='是否为默认管家')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'LLM模型'
        verbose_name_plural = 'LLM模型'
        ordering = ['provider', 'name']
        unique_together = ['provider', 'model_id']

    def __str__(self):
        return f'{self.provider.name} - {self.name}'

    def save(self, *args, **kwargs):
        # 如果设置为默认管家，确保只有一个默认管家
        if self.is_default_assistant:
            # 清除其他模型的默认管家标记
            LLMModel.objects.filter(is_default_assistant=True).exclude(pk=self.pk).update(is_default_assistant=False)
        super().save(*args, **kwargs)


class APIKey(models.Model):
    """API密钥模型"""
    provider = models.ForeignKey(LLMProvider, on_delete=models.CASCADE, related_name='api_keys', verbose_name='提供商')
    name = models.CharField(max_length=100, verbose_name='密钥名称')
    api_key = models.TextField(verbose_name='API密钥')  # 重命名为api_key
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    usage_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name='使用限制')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='使用次数')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='最后使用时间')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')  # 添加updated_at字段
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='过期时间')
    
    class Meta:
        verbose_name = 'API密钥'
        verbose_name_plural = 'API密钥'
        ordering = ['-is_active', 'provider', 'name']
    
    def __str__(self):
        return f'{self.provider.name} - {self.name}'
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_limit_exceeded(self):
        if self.usage_limit:
            return self.usage_count >= self.usage_limit
        return False


class LLMRequest(models.Model):
    """LLM请求记录模型"""
    request_id = models.CharField(max_length=100, unique=True, verbose_name='请求ID')  # 添加request_id字段
    model = models.ForeignKey(LLMModel, on_delete=models.CASCADE, related_name='requests', verbose_name='使用模型')
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='requests', verbose_name='使用密钥')
    request_type = models.CharField(
        max_length=50,
        choices=[
            ('emotion_analysis', '情绪分析'),
            ('text_generation', '文本生成'),
            ('script_generation', '脚本生成'),
            ('content_optimization', '内容优化'),
            ('other', '其他'),
        ],
        verbose_name='请求类型'
    )
    prompt = models.TextField(verbose_name='提示词')
    parameters = models.JSONField(default=dict, blank=True, verbose_name='请求参数')  # 重命名为parameters
    response = models.TextField(blank=True, verbose_name='响应内容')
    input_tokens = models.PositiveIntegerField(null=True, blank=True, verbose_name='输入令牌数')
    output_tokens = models.PositiveIntegerField(null=True, blank=True, verbose_name='输出令牌数')
    total_tokens = models.PositiveIntegerField(null=True, blank=True, verbose_name='总令牌数')
    cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='成本')
    processing_time = models.FloatField(null=True, blank=True, verbose_name='处理时间(秒)')  # 重命名为processing_time
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '完成'),
            ('failed', '失败'),
        ],
        default='pending',
        verbose_name='状态'
    )
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    class Meta:
        verbose_name = 'LLM请求记录'
        verbose_name_plural = 'LLM请求记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.model.name} - {self.get_request_type_display()} - {self.get_status_display()}'
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()

        # 自动生成 request_id 如果没有提供
        if not self.request_id:
            self.request_id = str(uuid.uuid4())

        super().save(*args, **kwargs)


class PromptTemplate(models.Model):
    """提示词模板模型"""
    name = models.CharField(max_length=100, verbose_name='模板名称')
    category = models.CharField(
        max_length=50,
        choices=[
            ('emotion_analysis', '情绪分析'),
            ('text_generation', '文本生成'),
            ('script_generation', '脚本生成'),
            ('content_optimization', '内容优化'),
        ],
        verbose_name='模板类别'
    )
    template_content = models.TextField(verbose_name='模板内容')
    variables = models.JSONField(default=list, blank=True, verbose_name='变量列表')
    description = models.TextField(blank=True, verbose_name='模板描述')
    usage_count = models.PositiveIntegerField(default=0, verbose_name='使用次数')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '提示词模板'
        verbose_name_plural = '提示词模板'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f'{self.get_category_display()} - {self.name}'
    
    def render(self, **kwargs):
        """渲染模板"""
        template = self.template_content
        for key, value in kwargs.items():
            template = template.replace(f'{{{key}}}', str(value))
        return template


class LLMConfiguration(models.Model):
    """LLM配置模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='配置名称')
    model = models.ForeignKey(LLMModel, on_delete=models.CASCADE, related_name='configurations', verbose_name='默认模型')
    default_temperature = models.FloatField(default=0.7, verbose_name='默认温度')
    default_max_tokens = models.PositiveIntegerField(default=1000, verbose_name='默认最大令牌数')
    default_top_p = models.FloatField(default=1.0, verbose_name='默认Top-P')
    retry_count = models.PositiveIntegerField(default=3, verbose_name='重试次数')
    timeout_seconds = models.PositiveIntegerField(default=30, verbose_name='超时时间(秒)')
    rate_limit_per_minute = models.PositiveIntegerField(default=60, verbose_name='每分钟请求限制')
    is_default = models.BooleanField(default=False, verbose_name='是否默认配置')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'LLM配置'
        verbose_name_plural = 'LLM配置'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # 确保只有一个默认配置
            LLMConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
