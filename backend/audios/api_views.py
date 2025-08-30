from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import AudioProject, GeneratedAudio
from .serializers import (
    AudioProjectSerializer, AudioProjectListSerializer,
    GeneratedAudioSerializer, GeneratedAudioListSerializer
)


class AudioProjectViewSet(viewsets.ModelViewSet):
    """音频项目视图集"""
    queryset = AudioProject.objects.all().order_by('-created_at')
    serializer_class = AudioProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'chapter__novel']
    search_fields = ['name', 'description', 'chapter__title', 'chapter__novel__title']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def audio_files(self, request, pk=None):
        """获取项目的所有音频文件"""
        project = self.get_object()
        audio_files = project.generated_audios.all().order_by('created_at')
        serializer = GeneratedAudioListSerializer(audio_files, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_audio_file(self, request, pk=None):
        """为项目添加音频文件"""
        project = self.get_object()
        data = request.data.copy()
        data['project'] = project.id
        
        serializer = GeneratedAudioSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def start_generation(self, request, pk=None):
        """开始音频生成"""
        project = self.get_object()
        # TODO: 实现音频生成逻辑
        project.status = 'processing'
        project.save()
        return Response({'message': '音频生成已开始'})
    
    @action(detail=True, methods=['post'])
    def stop_generation(self, request, pk=None):
        """停止音频生成"""
        project = self.get_object()
        # TODO: 实现停止生成逻辑
        project.status = 'paused'
        project.save()
        return Response({'message': '音频生成已停止'})
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索音频项目"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})
        
        projects = self.queryset.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(chapter__title__icontains=query) |
            Q(chapter__novel__title__icontains=query)
        )
        
        page = self.paginate_queryset(projects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(projects, many=True)
        return Response({'results': serializer.data})


class GeneratedAudioViewSet(viewsets.ModelViewSet):
    """生成音频视图集"""
    queryset = GeneratedAudio.objects.all().order_by('-created_at')
    serializer_class = GeneratedAudioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'project']
    search_fields = ['filename', 'project__name']
    ordering_fields = ['created_at', 'updated_at', 'filename', 'duration']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return GeneratedAudioListSerializer
        return GeneratedAudioSerializer
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载音频文件"""
        audio_file = self.get_object()
        
        if not audio_file.file_path or not os.path.exists(audio_file.file_path):
            raise Http404("音频文件不存在")
        
        try:
            response = FileResponse(
                open(audio_file.file_path, 'rb'),
                content_type='audio/mpeg'
            )
            response['Content-Disposition'] = f'attachment; filename="{audio_file.filename}"'
            return response
        except Exception as e:
            return Response(
                {'error': f'下载失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """流式播放音频文件"""
        audio_file = self.get_object()
        
        if not audio_file.file_path or not os.path.exists(audio_file.file_path):
            raise Http404("音频文件不存在")
        
        try:
            response = FileResponse(
                open(audio_file.file_path, 'rb'),
                content_type='audio/mpeg'
            )
            response['Accept-Ranges'] = 'bytes'
            return response
        except Exception as e:
            return Response(
                {'error': f'播放失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """按项目获取音频文件列表"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': '需要提供project_id参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        audio_files = self.queryset.filter(project_id=project_id)
        page = self.paginate_queryset(audio_files)
        if page is not None:
            serializer = GeneratedAudioListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = GeneratedAudioListSerializer(audio_files, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索音频文件"""
        query = request.query_params.get('q', '')
        project_id = request.query_params.get('project_id')
        
        if not query:
            return Response({'results': []})
        
        audio_files = self.queryset.filter(
            Q(filename__icontains=query) | Q(project__name__icontains=query)
        )
        
        if project_id:
            audio_files = audio_files.filter(project_id=project_id)
        
        page = self.paginate_queryset(audio_files)
        if page is not None:
            serializer = AudioFileListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = GeneratedAudioListSerializer(audio_files, many=True)
        return Response({'results': serializer.data})