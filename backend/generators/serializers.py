from rest_framework import serializers
from .models import GenerationWorkflow, ScriptGenerationTask, AudioGenerationTask
from novels.models import Chapter
from audios.models import AudioProject
from django.core.exceptions import ValidationError
import json


class WorkflowSerializer(serializers.ModelSerializer):
    """工作流序列化器"""
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GenerationWorkflow
        fields = '__all__'
        
    def get_tasks_count(self, obj):
        """获取任务数量"""
        # 计算关联的脚本任务和音频任务总数
        script_count = 1 if obj.script_task else 0
        audio_count = 1 if obj.audio_task else 0
        return script_count + audio_count
        
    def validate_workflow_config(self, value):
        """验证配置格式"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("配置必须是有效的JSON格式")
        return value


class WorkflowListSerializer(serializers.ModelSerializer):
    """工作流列表序列化器"""
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GenerationWorkflow
        fields = ['id', 'name', 'status', 'tasks_count', 'created_at', 'updated_at']
        
    def get_tasks_count(self, obj):
        """获取任务数量"""
        script_count = 1 if obj.script_task else 0
        audio_count = 1 if obj.audio_task else 0
        return script_count + audio_count


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    character_name = serializers.CharField(source='character.name', read_only=True)
    llm_model_name = serializers.CharField(source='llm_model.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = ScriptGenerationTask
        fields = '__all__'
        
    def get_progress_percentage(self, obj):
        """计算进度百分比"""
        if hasattr(obj, 'progress') and obj.progress is not None:
            return obj.progress
        return 0
        
    def get_duration_seconds(self, obj):
        """计算任务持续时间（秒）"""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None
        
    def validate_generation_params(self, value):
        """验证生成参数"""
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("生成参数必须是有效的JSON格式")
        return value


class TaskListSerializer(serializers.ModelSerializer):
    """任务列表序列化器"""
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    character_name = serializers.CharField(source='character.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = ScriptGenerationTask
        fields = ['id', 'name', 'chapter_title', 'character_name', 'status', 'progress_percentage', 'created_at']
        
    def get_progress_percentage(self, obj):
        """计算进度百分比"""
        if hasattr(obj, 'progress') and obj.progress is not None:
            return obj.progress
        return 0