from rest_framework import serializers
from .models import AudioProject, GeneratedAudio


class AudioProjectSerializer(serializers.ModelSerializer):
    """音频项目序列化器"""
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    novel_title = serializers.CharField(source='chapter.novel.title', read_only=True)
    audio_files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioProject
        fields = '__all__'
        
    def get_audio_files_count(self, obj):
        """获取音频文件数量"""
        return obj.generated_audios.count()


class AudioProjectListSerializer(serializers.ModelSerializer):
    """音频项目列表序列化器"""
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    novel_title = serializers.CharField(source='chapter.novel.title', read_only=True)
    audio_files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioProject
        fields = ['id', 'name', 'chapter_title', 'novel_title', 'status', 'audio_files_count', 'created_at']
        
    def get_audio_files_count(self, obj):
        """获取音频文件数量"""
        return obj.generated_audios.count()


class GeneratedAudioSerializer(serializers.ModelSerializer):
    """生成音频序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    emotion_name = serializers.CharField(source='emotion_type.name', read_only=True)
    
    class Meta:
        model = GeneratedAudio
        fields = '__all__'


class GeneratedAudioListSerializer(serializers.ModelSerializer):
    """生成音频列表序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    emotion_name = serializers.CharField(source='emotion_type.name', read_only=True)
    
    class Meta:
        model = GeneratedAudio
        fields = ['id', 'project_name', 'emotion_name', 'sequence_number', 'duration', 'created_at']