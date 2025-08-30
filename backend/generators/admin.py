from django.contrib import admin
from .models import (
    ScriptGenerationTask, ScriptSegment, AudioGenerationTask,
    GenerationWorkflow, GenerationStatistics
)


@admin.register(ScriptGenerationTask)
class ScriptGenerationTaskAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'llm_model', 'status', 'segment_count', 'created_at']
    list_filter = ['status', 'llm_model__provider', 'created_at']
    search_fields = ['chapter__title', 'chapter__novel__title']
    readonly_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['chapter', 'llm_model']
        }),
        ('生成参数', {
            'fields': ['generation_params'],
            'classes': ['collapse']
        }),
        ('状态信息', {
            'fields': ['status', 'progress']
        }),
        ('结果', {
            'fields': ['result'],
            'classes': ['collapse']
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
    
    def segment_count(self, obj):
        return obj.segments.count()
    segment_count.short_description = '脚本片段数量'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'chapter__novel', 'llm_model__provider'
        )


@admin.register(ScriptSegment)
class ScriptSegmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'sequence_number', 'character', 'emotion_type', 'word_count']
    list_filter = ['emotion_type', 'character', 'task__status']
    search_fields = ['content', 'character__name', 'task__chapter__title']
    readonly_fields = ['word_count']
    ordering = ['task', 'sequence_number']
    fieldsets = [
        ('基本信息', {
            'fields': ['task', 'sequence_number']
        }),
        ('角色信息', {
            'fields': ['character', 'emotion_type']
        }),
        ('内容', {
            'fields': ['content', 'word_count']
        }),
        ('元数据', {
            'fields': ['metadata'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'task__chapter', 'character', 'emotion_type'
        )


@admin.register(AudioGenerationTask)
class AudioGenerationTaskAdmin(admin.ModelAdmin):
    list_display = ['script_task', 'audio_project', 'status', 'audio_count', 'total_duration', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['script_task__chapter__title', 'audio_project__name']
    readonly_fields = ['created_at', 'completed_at', 'total_duration']
    ordering = ['-created_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['script_task', 'audio_project']
        }),
        ('生成参数', {
            'fields': ['generation_params'],
            'classes': ['collapse']
        }),
        ('状态信息', {
            'fields': ['status', 'progress']
        }),
        ('统计信息', {
            'fields': ['total_duration']
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
    
    def audio_count(self, obj):
        return obj.audio_project.generated_audios.count() if obj.audio_project else 0
    audio_count.short_description = '音频数量'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'script_task__chapter', 'audio_project'
        )


# GenerationWorkflow admin removed - will be defined later


@admin.register(GenerationStatistics)
class GenerationStatisticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'script_tasks_completed', 'audio_tasks_completed', 'total_audio_duration', 'llm_total_cost', 'created_at']
    list_filter = ['date', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date']
    
    fieldsets = (
        ('统计日期', {
            'fields': ('date',)
        }),
        ('脚本生成统计', {
            'fields': ('script_tasks_created', 'script_tasks_completed', 'script_tasks_failed', 'total_script_processing_time')
        }),
        ('音频生成统计', {
            'fields': ('audio_tasks_created', 'audio_tasks_completed', 'audio_tasks_failed', 'total_audio_processing_time', 'total_audio_duration')
        }),
        ('LLM使用统计', {
            'fields': ('llm_requests_count', 'llm_total_tokens', 'llm_total_cost')
        }),
        ('时间记录', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# 为ScriptGenerationTask添加脚本片段内联编辑
class ScriptSegmentInline(admin.TabularInline):
    model = ScriptSegment
    extra = 0
    readonly_fields = ['word_count']
    fields = ['sequence_number', 'character', 'emotion_type', 'content', 'word_count']
    
    def has_add_permission(self, request, obj=None):
        return obj and obj.status == 'completed'


class ScriptGenerationTaskAdminWithSegments(ScriptGenerationTaskAdmin):
    inlines = [ScriptSegmentInline]


# 重新注册ScriptGenerationTask管理器
admin.site.unregister(ScriptGenerationTask)
admin.site.register(ScriptGenerationTask, ScriptGenerationTaskAdminWithSegments)


# WorkflowTaskInline removed - no ForeignKey relationship exists


@admin.register(GenerationWorkflow)
class GenerationWorkflowAdminWithTasks(admin.ModelAdmin):
    list_display = ['name', 'status', 'current_step', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'is_template', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'description', 'is_template', 'is_active']
        }),
        ('关联任务', {
            'fields': ['script_task', 'audio_task']
        }),
        ('工作流配置', {
            'fields': ['workflow_config'],
            'classes': ['collapse']
        }),
        ('执行状态', {
            'fields': ['status', 'current_step', 'execution_log', 'error_message']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at', 'started_at', 'completed_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'script_task', 'audio_task'
        )

# GenerationWorkflow is registered with decorator above
