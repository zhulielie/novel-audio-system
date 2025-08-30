from django.contrib import admin
from .models import (
    AudioProject, EmotionType, EmotionAudio, GeneratedAudio,
    AudioTemplate, AudioProcessingLog
)


@admin.register(AudioProject)
class AudioProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'chapter', 'character', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'character__novel']
    search_fields = ['name', 'chapter__title', 'character__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'description']
        }),
        ('关联信息', {
            'fields': ['chapter', 'character']
        }),
        ('状态', {
            'fields': ['status']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'chapter__novel', 'character__novel'
        )


@admin.register(EmotionType)
class EmotionTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'color', 'is_active', 'audio_count']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    
    def audio_count(self, obj):
        return obj.audios.count()
    audio_count.short_description = '音频数量'


@admin.register(EmotionAudio)
class EmotionAudioAdmin(admin.ModelAdmin):
    list_display = ['character', 'emotion_type', 'file_type', 'duration', 'is_active', 'created_at']
    list_filter = ['emotion_type', 'file_type', 'is_active', 'created_at']
    search_fields = ['character__name', 'emotion_type__name']
    readonly_fields = ['file_size', 'created_at']
    ordering = ['character', 'emotion_type', 'file_type']
    fieldsets = [
        ('基本信息', {
            'fields': ['emotion_type', 'character', 'file_type']
        }),
        ('音频文件', {
            'fields': ['audio_file']
        }),
        ('音频属性', {
            'fields': ['duration', 'sample_rate', 'file_size'],
            'classes': ['collapse']
        }),
        ('状态', {
            'fields': ['is_active']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'emotion_type', 'character__novel'
        )


@admin.register(GeneratedAudio)
class GeneratedAudioAdmin(admin.ModelAdmin):
    list_display = ['project', 'sequence_number', 'emotion_type', 'duration', 'created_at']
    list_filter = ['emotion_type', 'created_at', 'project__status']
    search_fields = ['project__name', 'text_content']
    readonly_fields = ['created_at']
    ordering = ['project', 'sequence_number']
    fieldsets = [
        ('基本信息', {
            'fields': ['project', 'sequence_number', 'emotion_type']
        }),
        ('内容', {
            'fields': ['text_content']
        }),
        ('音频文件', {
            'fields': ['audio_file', 'duration']
        }),
        ('生成参数', {
            'fields': ['generation_params'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'project', 'emotion_type'
        )


@admin.register(AudioTemplate)
class AudioTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'character', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at', 'character__novel']
    search_fields = ['name', 'character__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-is_default', 'character', 'name']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'description', 'character']
        }),
        ('模板设置', {
            'fields': ['is_default']
        }),
        ('语音配置', {
            'fields': ['voice_settings'],
            'classes': ['collapse']
        }),
        ('情绪映射', {
            'fields': ['emotion_mapping'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'character__novel'
        )


@admin.register(AudioProcessingLog)
class AudioProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['project', 'step', 'status', 'processing_time', 'created_at']
    list_filter = ['status', 'created_at', 'step']
    search_fields = ['project__name', 'step', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['project', 'step', 'status']
        }),
        ('处理信息', {
            'fields': ['message', 'processing_time']
        }),
        ('错误信息', {
            'fields': ['error_details'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')


# 为AudioProject添加日志内联编辑
class AudioProcessingLogInline(admin.TabularInline):
    model = AudioProcessingLog
    extra = 0
    readonly_fields = ['created_at']
    fields = ['step', 'status', 'message', 'processing_time', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


class AudioProjectAdminWithLogs(AudioProjectAdmin):
    inlines = [AudioProcessingLogInline]


# 重新注册AudioProject管理器
admin.site.unregister(AudioProject)
admin.site.register(AudioProject, AudioProjectAdminWithLogs)
