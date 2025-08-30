from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone

from .models import GenerationWorkflow, ScriptGenerationTask, AudioGenerationTask
from .serializers import (
    WorkflowSerializer,
    WorkflowListSerializer,
    TaskSerializer,
    TaskListSerializer
)


class WorkflowViewSet(viewsets.ModelViewSet):
    """工作流视图集"""
    queryset = GenerationWorkflow.objects.all().order_by('-created_at')
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return WorkflowListSerializer
        return WorkflowSerializer
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """获取工作流的所有任务"""
        workflow = self.get_object()
        tasks = workflow.tasks.all().order_by('-created_at')
        
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_task(self, request, pk=None):
        """为工作流创建任务"""
        workflow = self.get_object()
        data = request.data.copy()
        data['workflow'] = workflow.id
        
        serializer = TaskSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """切换工作流激活状态"""
        workflow = self.get_object()
        workflow.is_active = not workflow.is_active
        workflow.save()
        
        return Response({
            'success': True,
            'is_active': workflow.is_active,
            'message': f'工作流已{"激活" if workflow.is_active else "停用"}'
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取所有激活的工作流"""
        active_workflows = self.queryset.filter(is_active=True)
        serializer = WorkflowListSerializer(active_workflows, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """获取所有工作流类型"""
        types = self.queryset.values_list('workflow_type', flat=True).distinct()
        return Response(list(types))


class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    queryset = ScriptGenerationTask.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name']
    ordering_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动任务"""
        task = self.get_object()
        
        if task.status != 'pending':
            return Response(
                {'error': '只能启动待处理状态的任务'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: 实现实际的任务启动逻辑
            task.status = 'running'
            task.started_at = timezone.now()
            task.progress = 0
            task.save()
            
            # 模拟任务处理
            # 这里应该启动异步任务处理
            
            return Response({
                'success': True,
                'message': '任务已启动',
                'task_id': task.id
            })
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
            
            return Response(
                {'error': f'任务启动失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """暂停任务"""
        task = self.get_object()
        
        if task.status != 'running':
            return Response(
                {'error': '只能暂停运行中的任务'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: 实现实际的任务暂停逻辑
            task.status = 'paused'
            task.save()
            
            return Response({
                'success': True,
                'message': '任务已暂停'
            })
            
        except Exception as e:
            return Response(
                {'error': f'任务暂停失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """恢复任务"""
        task = self.get_object()
        
        if task.status != 'paused':
            return Response(
                {'error': '只能恢复暂停状态的任务'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: 实现实际的任务恢复逻辑
            task.status = 'running'
            task.save()
            
            return Response({
                'success': True,
                'message': '任务已恢复'
            })
            
        except Exception as e:
            return Response(
                {'error': f'任务恢复失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止任务"""
        task = self.get_object()
        
        if task.status not in ['running', 'paused']:
            return Response(
                {'error': '只能停止运行中或暂停状态的任务'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: 实现实际的任务停止逻辑
            task.status = 'cancelled'
            task.completed_at = timezone.now()
            task.save()
            
            return Response({
                'success': True,
                'message': '任务已停止'
            })
            
        except Exception as e:
            return Response(
                {'error': f'任务停止失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试失败的任务"""
        task = self.get_object()
        
        if task.status != 'failed':
            return Response(
                {'error': '只能重试失败的任务'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: 实现实际的任务重试逻辑
            task.status = 'pending'
            task.error_message = ''
            task.progress = 0
            task.started_at = None
            task.completed_at = None
            task.save()
            
            return Response({
                'success': True,
                'message': '任务已重置，可以重新启动'
            })
            
        except Exception as e:
            return Response(
                {'error': f'任务重试失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_workflow(self, request):
        """按工作流获取任务列表"""
        workflow_id = request.query_params.get('workflow_id')
        if not workflow_id:
            return Response(
                {'error': '需要提供workflow_id参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self.queryset.filter(workflow_id=workflow_id)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def running(self, request):
        """获取所有运行中的任务"""
        running_tasks = self.queryset.filter(status='running')
        serializer = TaskListSerializer(running_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取任务统计信息"""
        total_tasks = self.queryset.count()
        pending_tasks = self.queryset.filter(status='pending').count()
        running_tasks = self.queryset.filter(status='running').count()
        completed_tasks = self.queryset.filter(status='completed').count()
        failed_tasks = self.queryset.filter(status='failed').count()
        cancelled_tasks = self.queryset.filter(status='cancelled').count()
        paused_tasks = self.queryset.filter(status='paused').count()
        
        return Response({
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'cancelled_tasks': cancelled_tasks,
            'paused_tasks': paused_tasks,
            'success_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        })