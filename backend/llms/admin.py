from django.contrib import admin
from .models import (
    LLMProvider, LLMModel, APIKey, LLMRequest,
    PromptTemplate, LLMConfiguration
)


@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'model_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'code', 'description']
        }),
        ('API配置', {
            'fields': ['base_url', 'api_version']
        }),
        ('状态', {
            'fields': ['is_active']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def model_count(self, obj):
        return obj.models.count()
    model_count.short_description = '模型数量'


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_type', 'is_active', 'max_tokens', 'created_at']
    list_filter = ['provider', 'model_type', 'is_active', 'created_at']
    search_fields = ['name', 'model_id', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['provider', 'name']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'model_id', 'provider', 'model_type']
        }),
        ('模型配置', {
            'fields': ['max_tokens', 'context_length', 'description']
        }),
        ('定价信息', {
            'fields': ['input_price_per_token', 'output_price_per_token'],
            'classes': ['collapse']
        }),
        ('状态', {
            'fields': ['is_active']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'is_active', 'usage_count', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['name', 'provider__name']
    readonly_fields = ['created_at', 'updated_at', 'last_used_at']
    ordering = ['provider', 'name']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'provider']
        }),
        ('API密钥', {
            'fields': ['api_key'],
            'description': 'API密钥将被加密存储'
        }),
        ('使用统计', {
            'fields': ['usage_count', 'last_used_at'],
            'classes': ['collapse']
        }),
        ('状态', {
            'fields': ['is_active']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider')


@admin.register(LLMRequest)
class LLMRequestAdmin(admin.ModelAdmin):
    list_display = ['model', 'request_type', 'status', 'input_tokens', 'output_tokens', 'cost', 'created_at']
    list_filter = ['model__provider', 'request_type', 'status', 'created_at']
    search_fields = ['model__name', 'request_id']
    readonly_fields = ['created_at', 'completed_at', 'request_id']
    ordering = ['-created_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['request_id', 'model', 'request_type']
        }),
        ('请求内容', {
            'fields': ['prompt', 'parameters'],
            'classes': ['collapse']
        }),
        ('响应内容', {
            'fields': ['response', 'status'],
            'classes': ['collapse']
        }),
        ('统计信息', {
            'fields': ['input_tokens', 'output_tokens', 'cost', 'processing_time']
        }),
        ('错误信息', {
            'fields': ['error_message'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at', 'completed_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('model__provider')


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'usage_count', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    ordering = ['category', 'name']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'category', 'description']
        }),
        ('模板内容', {
            'fields': ['template_content']
        }),
        ('变量配置', {
            'fields': ['variables'],
            'classes': ['collapse']
        }),
        ('使用统计', {
            'fields': ['usage_count'],
            'classes': ['collapse']
        }),
        ('状态', {
            'fields': ['is_active']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]


@admin.register(LLMConfiguration)
class LLMConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'is_default', 'created_at']
    list_filter = ['model__provider', 'is_default', 'created_at']
    search_fields = ['name', 'model__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-is_default', 'model', 'name']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'model', 'description']
        }),
        ('配置设置', {
            'fields': ['is_default']
        }),
        ('参数配置', {
            'fields': ['parameters'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('model__provider')


# 为LLMProvider添加模型内联编辑
class LLMModelInline(admin.TabularInline):
    model = LLMModel
    extra = 0
    fields = ['name', 'model_id', 'model_type', 'max_tokens', 'is_active']
    readonly_fields = []


class LLMProviderAdminWithModels(LLMProviderAdmin):
    inlines = [LLMModelInline]


# 重新注册LLMProvider管理器
admin.site.unregister(LLMProvider)
admin.site.register(LLMProvider, LLMProviderAdminWithModels)


# 为LLMModel添加请求记录内联编辑
class LLMRequestInline(admin.TabularInline):
    model = LLMRequest
    extra = 0
    readonly_fields = ['created_at', 'request_id']
    fields = ['request_type', 'status', 'input_tokens', 'output_tokens', 'cost', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


class LLMModelAdminWithRequests(LLMModelAdmin):
    inlines = [LLMRequestInline]


# 重新注册LLMModel管理器
admin.site.unregister(LLMModel)
admin.site.register(LLMModel, LLMModelAdminWithRequests)
