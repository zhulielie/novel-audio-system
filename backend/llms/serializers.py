from rest_framework import serializers
from .models import LLMModel, LLMRequest


class LLMModelSerializer(serializers.ModelSerializer):
    """LLM模型序列化器"""
    requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LLMModel
        fields = ['id', 'name', 'provider', 'model_id', 'api_key',
                 'base_url', 'max_tokens', 'temperature', 'is_active', 'is_default_assistant',
                 'created_at', 'updated_at', 'requests_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True}  # API密钥只写不读
        }
    
    def get_requests_count(self, obj):
        """获取请求数量"""
        return obj.requests.count()
    
    def to_representation(self, instance):
        """自定义序列化输出"""
        data = super().to_representation(instance)
        # 隐藏API密钥，只显示是否已设置
        if instance.api_key:
            data['api_key_set'] = True
        else:
            data['api_key_set'] = False
        return data


class LLMModelListSerializer(serializers.ModelSerializer):
    """LLM模型列表序列化器（简化版）"""
    requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LLMModel
        fields = ['id', 'name', 'provider', 'model_id', 'is_active', 'is_default_assistant',
                 'created_at', 'requests_count']
        read_only_fields = ['id', 'created_at']
    
    def get_requests_count(self, obj):
        """获取请求数量"""
        return obj.requests.count()


class LLMRequestSerializer(serializers.ModelSerializer):
    """LLM请求序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = LLMRequest
        fields = ['id', 'model', 'model_name', 'prompt', 'response',
                 'parameters', 'status', 'error_message', 'tokens_used',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'response',
                           'status', 'error_message', 'tokens_used']
    
    def validate_prompt(self, value):
        """验证提示词"""
        if not value or not value.strip():
            raise serializers.ValidationError("提示词不能为空")
        if len(value) > 10000:
            raise serializers.ValidationError("提示词长度不能超过10000字符")
        return value.strip()


class LLMRequestListSerializer(serializers.ModelSerializer):
    """LLM请求列表序列化器（简化版）"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    prompt_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = LLMRequest
        fields = ['id', 'model', 'model_name', 'prompt_preview', 'status',
                 'tokens_used', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_prompt_preview(self, obj):
        """获取提示词预览（前100字符）"""
        if obj.prompt:
            return obj.prompt[:100] + '...' if len(obj.prompt) > 100 else obj.prompt
        return ''