from rest_framework import serializers
from .models import Novel, Chapter, NovelSource
from .crawler_models import CrawlerTask, NovelCatalog, ChapterDownloadRecord
from .models import UserReadingSettings


class NovelSerializer(serializers.ModelSerializer):
    """小说序列化器"""
    chapters_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Novel
        fields = ['id', 'title', 'author', 'description', 'status', 
                 'created_at', 'updated_at', 'chapters_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_chapters_count(self, obj):
        """获取章节数量"""
        return obj.chapters.count()


class ChapterSerializer(serializers.ModelSerializer):
    """章节序列化器"""
    novel_title = serializers.CharField(source='novel.title', read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'novel', 'novel_title', 'title', 'content',
                 'chapter_number', 'chapter_sort_number', 'word_count', 'is_published',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_chapter_number(self, value):
        """验证章节号唯一性"""
        novel = self.initial_data.get('novel')
        if novel:
            existing = Chapter.objects.filter(
                novel_id=novel, 
                chapter_number=value
            ).exclude(id=self.instance.id if self.instance else None)
            if existing.exists():
                raise serializers.ValidationError("该小说中已存在相同章节号")
        return value


class ChapterListSerializer(serializers.ModelSerializer):
    """章节列表序列化器（简化版）"""
    novel_title = serializers.CharField(source='novel.title', read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'novel', 'novel_title', 'title', 'content', 'chapter_number',
                 'chapter_sort_number', 'word_count', 'is_published',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NovelSourceSerializer(serializers.ModelSerializer):
    """小说来源序列化器"""
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    
    class Meta:
        model = NovelSource
        fields = ['id', 'name', 'source_type', 'source_type_display', 'base_url', 
                 'chapter_url_pattern', 'encoding', 'is_active', 'priority', 
                 'last_crawl_at', 'crawl_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'last_crawl_at', 'crawl_count']

    def validate_base_url(self, value):
        """验证基础URL格式"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('URL必须以http://或https://开头')
        return value


class CrawlerTaskSerializer(serializers.ModelSerializer):
    """爬虫任务序列化器"""
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = CrawlerTask
        fields = ['id', 'task_id', 'task_type', 'task_type_display', 'status', 'status_display',
                 'novel', 'source_url', 'parameters', 'started_at', 'completed_at', 'progress',
                 'total_items', 'processed_items', 'success_items', 'failed_items',
                 'result_data', 'error_message', 'created_at', 'duration', 'success_rate']
        read_only_fields = ['id', 'created_at', 'duration', 'success_rate']
    
    def get_duration(self, obj):
        """获取任务执行时长"""
        return str(obj.duration) if obj.duration else None
    
    def get_success_rate(self, obj):
        """获取成功率"""
        return obj.success_rate


class NovelCatalogSerializer(serializers.ModelSerializer):
    """小说目录序列化器"""
    novel_title = serializers.CharField(source='novel.title', read_only=True)
    
    class Meta:
        model = NovelCatalog
        fields = ['id', 'novel', 'novel_title', 'source_url', 'title', 'author',
                 'description', 'total_chapters', 'chapters_data', 'extracted_at',
                 'extractor_version', 'is_valid', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChapterDownloadRecordSerializer(serializers.ModelSerializer):
    """章节下载记录序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    download_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ChapterDownloadRecord
        fields = ['id', 'task', 'chapter', 'chapter_title', 'chapter_number', 'source_url',
                 'status', 'status_display', 'content_length', 'watermark_removed',
                 'download_started_at', 'download_completed_at', 'retry_count',
                 'error_message', 'created_at', 'download_duration']
        read_only_fields = ['id', 'created_at', 'download_duration']
    
    def get_download_duration(self, obj):
        """获取下载耗时"""
        return str(obj.download_duration) if obj.download_duration else None


class UserReadingSettingsSerializer(serializers.ModelSerializer):
    """用户阅读设置序列化器"""
    
    class Meta:
        model = UserReadingSettings
        fields = [
            'id', 'auto_crawl_enabled', 'crawl_ahead_chapters', 
            'font_size', 'line_height', 'background_color', 'reading_mode',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """创建或更新用户阅读设置"""
        user = self.context['request'].user
        settings, created = UserReadingSettings.objects.get_or_create(
            user=user,
            defaults=validated_data
        )
        if not created:
            # 如果已存在，则更新
            for attr, value in validated_data.items():
                setattr(settings, attr, value)
            settings.save()
        return settings