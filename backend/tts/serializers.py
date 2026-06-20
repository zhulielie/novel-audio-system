from rest_framework import serializers
from .models import TTSEngine, VoiceAsset, TTSGenerationTask, TTSSegmentResult


class TTSEngineSerializer(serializers.ModelSerializer):
    engine_type_display = serializers.CharField(source='get_engine_type_display', read_only=True)

    class Meta:
        model = TTSEngine
        fields = '__all__'


class TTSEngineListSerializer(serializers.ModelSerializer):
    engine_type_display = serializers.CharField(source='get_engine_type_display', read_only=True)

    class Meta:
        model = TTSEngine
        fields = ['id', 'name', 'engine_type', 'engine_type_display', 'is_active', 'is_default', 'priority']


class VoiceAssetSerializer(serializers.ModelSerializer):
    voice_type_display = serializers.CharField(source='get_voice_type_display', read_only=True)
    audio_url = serializers.CharField(read_only=True)
    character_name = serializers.CharField(source='character.name', read_only=True, default=None)

    class Meta:
        model = VoiceAsset
        fields = '__all__'


class VoiceAssetListSerializer(serializers.ModelSerializer):
    voice_type_display = serializers.CharField(source='get_voice_type_display', read_only=True)
    character_name = serializers.CharField(source='character.name', read_only=True, default=None)

    class Meta:
        model = VoiceAsset
        fields = ['id', 'name', 'voice_type', 'voice_type_display', 'character_name',
                  'duration', 'is_active', 'tags', 'created_at']


class TTSSegmentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TTSSegmentResult
        fields = '__all__'


class TTSGenerationTaskSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    novel_title = serializers.CharField(source='novel.title', read_only=True)
    chapter_title = serializers.CharField(source='chapter.title', read_only=True, default=None)
    engine_name = serializers.CharField(source='engine.name', read_only=True, default=None)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = TTSGenerationTask
        fields = '__all__'


class TTSGenerationTaskListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    novel_title = serializers.CharField(source='novel.title', read_only=True)
    chapter_title = serializers.CharField(source='chapter.title', read_only=True, default=None)
    engine_name = serializers.CharField(source='engine.name', read_only=True, default=None)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = TTSGenerationTask
        fields = ['id', 'name', 'status', 'status_display', 'progress', 'progress_percentage',
                  'novel_title', 'chapter_title', 'engine_name',
                  'total_segments', 'completed_segments', 'total_duration',
                  'created_at', 'started_at', 'completed_at']


class TTSGenerationRequestSerializer(serializers.Serializer):
    """TTS 生成请求序列化器"""
    name = serializers.CharField(max_length=200, required=True, label='任务名称')
    novel_id = serializers.IntegerField(required=True, label='小说ID')
    chapter_id = serializers.IntegerField(required=False, allow_null=True, label='章节ID')
    engine_id = serializers.IntegerField(required=False, allow_null=True, label='引擎ID')
    script_data = serializers.ListSerializer(
        child=serializers.DictField(),
        required=True,
        label='剧本数据'
    )
    speaker_voice_map = serializers.DictField(
        required=True,
        label='角色语音映射'
    )
    generation_params = serializers.DictField(required=False, default=dict, label='生成参数')
