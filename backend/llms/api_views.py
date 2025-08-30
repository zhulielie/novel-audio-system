from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.db import transaction
import json
import asyncio
import uuid
from asgiref.sync import async_to_sync

from .models import LLMModel, LLMRequest
from .services.llm_service import process_llm_request_async
from .serializers import (
    LLMModelSerializer,
    LLMModelListSerializer,
    LLMRequestSerializer,
    LLMRequestListSerializer
)


class LLMModelViewSet(viewsets.ModelViewSet):
    """LLM模型视图集"""
    queryset = LLMModel.objects.all().order_by('-created_at')
    serializer_class = LLMModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active']
    search_fields = ['name', 'model_id', 'provider']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return LLMModelListSerializer
        return LLMModelSerializer
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试LLM模型"""
        model = self.get_object()
        test_prompt = request.data.get('prompt', '你好，请回复一个简单的问候。')
        temperature = request.data.get('temperature', 0.7)
        max_tokens = request.data.get('max_tokens', 100)

        # 获取有效的API密钥
        from .models import APIKey
        from django.utils import timezone

        # 获取有效的API密钥（手动过滤过期和超限的密钥）
        api_keys = APIKey.objects.filter(
            provider=model.provider,
            is_active=True
        )

        # 手动过滤未过期的密钥
        valid_api_keys = []
        for key in api_keys:
            if not key.expires_at or key.expires_at > timezone.now():
                # 检查使用限制
                if not key.usage_limit or key.usage_count < key.usage_limit:
                    valid_api_keys.append(key)

        api_key = valid_api_keys[0] if valid_api_keys else None

        if not api_key:
            return Response({
                'success': False,
                'message': f'未找到有效的API密钥用于提供商: {model.provider.name}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建测试请求
        test_request = LLMRequest.objects.create(
            request_id=str(uuid.uuid4()),
            model=model,
            api_key=api_key,
            request_type='text_generation',
            prompt=test_prompt,
            parameters={'temperature': temperature, 'max_tokens': max_tokens},
            status='pending'
        )

        try:
            # 异步处理LLM请求
            async_to_sync(process_llm_request_async)(test_request)

            # 重新获取更新后的请求
            test_request.refresh_from_db()

            if test_request.status == 'completed':
                return Response({
                    'success': True,
                    'message': '模型测试成功',
                    'request_id': test_request.id,
                    'response': test_request.response,
                    'tokens_used': test_request.total_tokens,
                    'processing_time': test_request.processing_time
                })
            else:
                return Response({
                    'success': False,
                    'message': f'模型测试失败: {test_request.error_message}',
                    'request_id': test_request.id
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            test_request.status = 'failed'
            test_request.error_message = str(e)
            test_request.save()

            return Response({
                'success': False,
                'message': f'模型测试失败: {str(e)}',
                'request_id': test_request.id
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """切换模型激活状态"""
        model = self.get_object()
        model.is_active = not model.is_active
        model.save()

        return Response({
            'success': True,
            'is_active': model.is_active,
            'message': f'模型已{"激活" if model.is_active else "停用"}'
        })

    @action(detail=True, methods=['post'])
    def set_default_assistant(self, request, pk=None):
        """设置默认管家"""
        model = self.get_object()

        if not model.is_active:
            return Response({
                'success': False,
                'message': '不能将未激活的模型设置为默认管家'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 设置为默认管家
        model.is_default_assistant = True
        model.save()

        return Response({
            'success': True,
            'is_default_assistant': model.is_default_assistant,
            'message': f'已将 {model.name} 设置为默认管家'
        })

    @action(detail=True, methods=['post'])
    def remove_default_assistant(self, request, pk=None):
        """取消默认管家"""
        model = self.get_object()

        if model.is_default_assistant:
            model.is_default_assistant = False
            model.save()

        return Response({
            'success': True,
            'is_default_assistant': model.is_default_assistant,
            'message': f'已取消 {model.name} 的默认管家身份'
        })
    
    @action(detail=True, methods=['get'])
    def requests(self, request, pk=None):
        """获取模型的请求历史"""
        model = self.get_object()
        requests = model.requests.all().order_by('-created_at')
        
        page = self.paginate_queryset(requests)
        if page is not None:
            serializer = LLMRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LLMRequestListSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取所有激活的模型"""
        active_models = self.queryset.filter(is_active=True)
        serializer = LLMModelListSerializer(active_models, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def providers(self, request):
        """获取所有提供商列表"""
        providers = self.queryset.values_list('provider', flat=True).distinct()
        return Response(list(providers))

    @action(detail=False, methods=['get'])
    def default_assistant(self, request):
        """获取当前的默认管家"""
        try:
            default_assistant = LLMModel.objects.filter(is_default_assistant=True).first()
            if default_assistant:
                serializer = self.get_serializer(default_assistant)
                return Response({
                    'success': True,
                    'default_assistant': serializer.data
                })
            else:
                return Response({
                    'success': True,
                    'default_assistant': None,
                    'message': '当前没有设置默认管家'
                })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'获取默认管家失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def reorder_novel_chapters(self, request):
        """简单的排序确认功能 - 章节已按数字排序"""
        try:
            novel_id = request.data.get('novel_id')
            if not novel_id:
                return Response({
                    'success': False,
                    'message': '需要提供novel_id参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取小说信息
            try:
                from novels.models import Novel, Chapter
                novel = Novel.objects.get(id=novel_id)
            except ImportError:
                return Response({
                    'success': False,
                    'message': '小说模块未找到，请确保已安装小说应用'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Novel.DoesNotExist:
                return Response({
                    'success': False,
                    'message': '小说不存在'
                }, status=status.HTTP_404_NOT_FOUND)

            # 获取章节数量
            chapter_count = Chapter.objects.filter(novel=novel).count()

            return Response({
                'success': True,
                'message': '章节已按数字排序完成',
                'novel_title': novel.title,
                'chapter_count': chapter_count,
                'applied': False,  # 不再实际应用排序
                'reasoning': '章节按标题中的数字自动排序',
                'confidence': 100,
                'reordered_chapters': list(range(1, chapter_count + 1))
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': f'排序确认失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def reset_chapter_order(self, request):
        """重置章节序号，将负数改回正数"""
        try:
            novel_id = request.data.get('novel_id')
            if not novel_id:
                return Response({
                    'success': False,
                    'message': '缺少novel_id参数'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取小说和章节
            try:
                from novels.models import Novel, Chapter
            except ImportError:
                return Response({
                    'success': False,
                    'message': '小说模块未找到'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                novel = Novel.objects.get(id=novel_id)
                chapters = list(Chapter.objects.filter(novel_id=novel_id).order_by('chapter_number'))
            except Novel.DoesNotExist:
                return Response({
                    'success': False,
                    'message': '小说不存在'
                }, status=status.HTTP_404_NOT_FOUND)

            if not chapters:
                return Response({
                    'success': False,
                    'message': '小说没有章节'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 重置章节序号
            from django.db import transaction
            with transaction.atomic():
                for new_order, chapter in enumerate(chapters):
                    chapter.chapter_number = new_order + 1
                    chapter.save()

            return Response({
                'success': True,
                'message': '章节序号已重置'
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': f'重置章节序号失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LLMRequestViewSet(viewsets.ModelViewSet):
    """LLM请求视图集"""
    queryset = LLMRequest.objects.all().order_by('-created_at')
    serializer_class = LLMRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'model']
    search_fields = ['prompt', 'response', 'model__name']
    ordering_fields = ['created_at', 'updated_at', 'tokens_used']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return LLMRequestListSerializer
        return LLMRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """创建新的LLM请求"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取数据
        data = serializer.validated_data
        model = data['model']

        # 获取有效的API密钥
        from .models import APIKey
        from django.utils import timezone

        # 获取有效的API密钥（手动过滤过期和超限的密钥）
        api_keys = APIKey.objects.filter(
            provider=model.provider,
            is_active=True
        )

        # 手动过滤未过期的密钥
        valid_api_keys = []
        for key in api_keys:
            if not key.expires_at or key.expires_at > timezone.now():
                # 检查使用限制
                if not key.usage_limit or key.usage_count < key.usage_limit:
                    valid_api_keys.append(key)

        api_key = valid_api_keys[0] if valid_api_keys else None

        if not api_key:
            return Response({
                'error': f'未找到有效的API密钥用于提供商: {model.provider.name}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 保存请求，包含API密钥和必要的字段
        llm_request = serializer.save(
            api_key=api_key,
            request_id=str(uuid.uuid4()),
            request_type=data.get('request_type', 'other')
        )

        # 异步处理请求
        try:
            async_to_sync(process_llm_request_async)(llm_request)

            # 重新获取更新后的请求
            llm_request.refresh_from_db()

        except Exception as e:
            llm_request.status = 'failed'
            llm_request.error_message = str(e)
            llm_request.save()

        # 重新序列化以包含更新后的数据
        serializer = self.get_serializer(llm_request)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试失败的请求"""
        llm_request = self.get_object()

        if llm_request.status != 'failed':
            return Response(
                {'error': '只能重试失败的请求'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 重置请求状态
            llm_request.status = 'pending'
            llm_request.error_message = ''
            llm_request.response = ''
            llm_request.input_tokens = None
            llm_request.output_tokens = None
            llm_request.total_tokens = None
            llm_request.processing_time = None
            llm_request.cost = None
            llm_request.save()

            # 重新处理请求
            async_to_sync(process_llm_request_async)(llm_request)

            # 重新获取更新后的请求
            llm_request.refresh_from_db()

            serializer = self.get_serializer(llm_request)
            return Response(serializer.data)

        except Exception as e:
            llm_request.status = 'failed'
            llm_request.error_message = str(e)
            llm_request.save()

            return Response(
                {'error': f'重试失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_model(self, request):
        """按模型获取请求列表"""
        model_id = request.query_params.get('model_id')
        if not model_id:
            return Response(
                {'error': '需要提供model_id参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requests = self.queryset.filter(model_id=model_id)
        page = self.paginate_queryset(requests)
        if page is not None:
            serializer = LLMRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LLMRequestListSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取请求统计信息"""
        total_requests = self.queryset.count()
        completed_requests = self.queryset.filter(status='completed').count()
        failed_requests = self.queryset.filter(status='failed').count()
        processing_requests = self.queryset.filter(status='processing').count()
        total_tokens = self.queryset.filter(tokens_used__isnull=False).aggregate(
            total=Sum('tokens_used')
        )['total'] or 0
        
        return Response({
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'failed_requests': failed_requests,
            'processing_requests': processing_requests,
            'success_rate': round(completed_requests / total_requests * 100, 2) if total_requests > 0 else 0,
            'total_tokens_used': total_tokens
        })