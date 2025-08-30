from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
import json
import uuid
from datetime import datetime, timedelta

from .models import GenerationWorkflow, ScriptGenerationTask, AudioGenerationTask, ScriptSegment, GenerationStatistics
from novels.models import Novel, Chapter
from llms.models import LLMModel, APIKey
from audios.models import AudioProject


def workflow_list(request):
    """生成工作流列表视图"""
    workflows = GenerationWorkflow.objects.select_related(
        'script_task', 'audio_task'
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        workflows = workflows.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 按状态过滤
    is_active = request.GET.get('is_active')
    if is_active:
        workflows = workflows.filter(is_active=(is_active == 'true'))
    
    # 分页
    paginator = Paginator(workflows, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_is_active': is_active,
    }
    return render(request, 'generators/workflow_list.html', context)


def workflow_detail(request, workflow_id):
    """生成工作流详情视图"""
    workflow = get_object_or_404(
        GenerationWorkflow.objects.select_related('script_task', 'audio_task'),
        id=workflow_id
    )
    
    # 获取脚本片段
    script_segments = []
    if workflow.script_task:
        script_segments = ScriptSegment.objects.filter(
            script_task=workflow.script_task
        ).order_by('sequence_number')
    
    context = {
        'workflow': workflow,
        'script_segments': script_segments,
    }
    return render(request, 'generators/workflow_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_workflow(request):
    """创建生成工作流"""
    try:
        data = json.loads(request.body)
        
        # 创建工作流
        workflow = GenerationWorkflow.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            config=data.get('config', {}),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'success': True,
            'workflow_id': workflow.id,
            'message': '工作流创建成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_workflow(request, workflow_id):
    """启动生成工作流"""
    try:
        workflow = get_object_or_404(GenerationWorkflow, id=workflow_id)
        
        if not workflow.is_active:
            return JsonResponse({
                'success': False,
                'message': '工作流未激活'
            }, status=400)
        
        # 更新执行信息
        workflow.started_at = timezone.now()
        workflow.save()
        
        # 这里可以添加实际的工作流启动逻辑
        # 例如：启动脚本生成任务、音频生成任务等
        
        return JsonResponse({
            'success': True,
            'message': '工作流启动成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'启动失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_workflow(request, workflow_id):
    """停止生成工作流"""
    try:
        workflow = get_object_or_404(GenerationWorkflow, id=workflow_id)
        
        # 更新执行信息
        workflow.completed_at = timezone.now()
        workflow.save()
        
        return JsonResponse({
            'success': True,
            'message': '工作流停止成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'停止失败: {str(e)}'
        }, status=500)


def script_task_list(request):
    """脚本生成任务列表视图"""
    tasks = ScriptGenerationTask.objects.select_related(
        'chapter', 'llm_model', 'api_key'
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(chapter__title__icontains=search_query) |
            Q(prompt__icontains=search_query)
        )
    
    # 按状态过滤
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    # 分页
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 状态选择
    status_choices = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status,
        'status_choices': status_choices,
    }
    return render(request, 'generators/script_task_list.html', context)


def script_task_detail(request, task_id):
    """脚本生成任务详情视图"""
    task = get_object_or_404(
        ScriptGenerationTask.objects.select_related(
            'chapter', 'llm_model', 'api_key'
        ),
        id=task_id
    )
    
    # 获取脚本片段
    script_segments = ScriptSegment.objects.filter(
        script_task=task
    ).order_by('sequence_number')
    
    context = {
        'task': task,
        'script_segments': script_segments,
    }
    return render(request, 'generators/script_task_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_script_task(request):
    """创建脚本生成任务"""
    try:
        data = json.loads(request.body)
        
        # 获取相关对象
        chapter = get_object_or_404(Chapter, id=data['chapter_id'])
        llm_model = get_object_or_404(LLMModel, id=data['llm_model_id'])
        api_key = get_object_or_404(APIKey, id=data['api_key_id'])
        
        # 创建脚本生成任务
        task = ScriptGenerationTask.objects.create(
            chapter=chapter,
            llm_model=llm_model,
            api_key=api_key,
            prompt=data.get('prompt', ''),
            max_tokens=data.get('max_tokens', 4096),
            temperature=data.get('temperature', 0.7),
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': '脚本生成任务创建成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_script_task(request, task_id):
    """启动脚本生成任务"""
    try:
        task = get_object_or_404(ScriptGenerationTask, id=task_id)
        
        if task.status != 'pending':
            return JsonResponse({
                'success': False,
                'message': '任务状态不允许启动'
            }, status=400)
        
        # 更新任务状态
        task.status = 'processing'
        task.started_at = timezone.now()
        task.save()
        
        # 这里可以添加实际的脚本生成逻辑
        # 例如：调用LLM API生成脚本
        
        return JsonResponse({
            'success': True,
            'message': '脚本生成任务启动成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'启动失败: {str(e)}'
        }, status=500)


def audio_task_list(request):
    """音频生成任务列表视图"""
    tasks = AudioGenerationTask.objects.select_related(
        'script_task', 'audio_project'
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(script_task__chapter__title__icontains=search_query) |
            Q(audio_project__name__icontains=search_query)
        )
    
    # 按状态过滤
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    # 分页
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 状态选择
    status_choices = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status,
        'status_choices': status_choices,
    }
    return render(request, 'generators/audio_task_list.html', context)


def audio_task_detail(request, task_id):
    """音频生成任务详情视图"""
    task = get_object_or_404(
        AudioGenerationTask.objects.select_related(
            'script_task', 'audio_project'
        ),
        id=task_id
    )
    
    context = {
        'task': task,
    }
    return render(request, 'generators/audio_task_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_audio_task(request):
    """创建音频生成任务"""
    try:
        data = json.loads(request.body)
        
        # 获取相关对象
        script_task = get_object_or_404(ScriptGenerationTask, id=data['script_task_id'])
        audio_project = get_object_or_404(AudioProject, id=data['audio_project_id'])
        
        # 创建音频生成任务
        task = AudioGenerationTask.objects.create(
            script_task=script_task,
            audio_project=audio_project,
            config=data.get('config', {}),
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': '音频生成任务创建成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_audio_task(request, task_id):
    """启动音频生成任务"""
    try:
        task = get_object_or_404(AudioGenerationTask, id=task_id)
        
        if task.status != 'pending':
            return JsonResponse({
                'success': False,
                'message': '任务状态不允许启动'
            }, status=400)
        
        # 更新任务状态
        task.status = 'processing'
        task.started_at = timezone.now()
        task.save()
        
        # 这里可以添加实际的音频生成逻辑
        # 例如：调用音频生成API
        
        return JsonResponse({
            'success': True,
            'message': '音频生成任务启动成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'启动失败: {str(e)}'
        }, status=500)


def script_segment_list(request):
    """脚本片段列表视图"""
    segments = ScriptSegment.objects.select_related(
        'script_task', 'character'
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        segments = segments.filter(
            Q(content__icontains=search_query) |
            Q(character__name__icontains=search_query)
        )
    
    # 按类型过滤
    segment_type = request.GET.get('segment_type')
    if segment_type:
        segments = segments.filter(segment_type=segment_type)
    
    # 分页
    paginator = Paginator(segments, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 类型选择
    type_choices = [
        ('dialogue', '对话'),
        ('narration', '旁白'),
        ('description', '描述'),
        ('action', '动作'),
    ]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_segment_type': segment_type,
        'type_choices': type_choices,
    }
    return render(request, 'generators/script_segment_list.html', context)


def script_segment_detail(request, segment_id):
    """脚本片段详情视图"""
    segment = get_object_or_404(
        ScriptSegment.objects.select_related(
            'script_task', 'character'
        ),
        id=segment_id
    )
    
    context = {
        'segment': segment,
    }
    return render(request, 'generators/script_segment_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def edit_script_segment(request, segment_id):
    """编辑脚本片段"""
    try:
        segment = get_object_or_404(ScriptSegment, id=segment_id)
        data = json.loads(request.body)
        
        # 更新片段内容
        segment.content = data.get('content', segment.content)
        segment.segment_type = data.get('segment_type', segment.segment_type)
        segment.emotion = data.get('emotion', segment.emotion)
        segment.voice_settings = data.get('voice_settings', segment.voice_settings)
        segment.save()
        
        return JsonResponse({
            'success': True,
            'message': '脚本片段更新成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }, status=500)


def generation_statistics(request):
    """生成统计视图"""
    # 基本统计
    total_workflows = GenerationWorkflow.objects.count()
    active_workflows = GenerationWorkflow.objects.filter(is_active=True).count()
    total_script_tasks = ScriptGenerationTask.objects.count()
    completed_script_tasks = ScriptGenerationTask.objects.filter(status='completed').count()
    total_audio_tasks = AudioGenerationTask.objects.count()
    completed_audio_tasks = AudioGenerationTask.objects.filter(status='completed').count()
    
    # 成功率计算
    script_success_rate = (completed_script_tasks / total_script_tasks * 100) if total_script_tasks > 0 else 0
    audio_success_rate = (completed_audio_tasks / total_audio_tasks * 100) if total_audio_tasks > 0 else 0
    
    # 按日期统计（最近30天）
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=29)
    
    daily_stats = []
    current_date = start_date
    while current_date <= end_date:
        day_script_tasks = ScriptGenerationTask.objects.filter(
            created_at__date=current_date
        ).count()
        day_audio_tasks = AudioGenerationTask.objects.filter(
            created_at__date=current_date
        ).count()
        
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'script_tasks': day_script_tasks,
            'audio_tasks': day_audio_tasks
        })
        current_date += timedelta(days=1)
    
    # 获取或创建统计记录
    today = timezone.now().date()
    stats, created = GenerationStatistics.objects.get_or_create(
        date=today,
        defaults={
            'script_generation_count': completed_script_tasks,
            'audio_generation_count': completed_audio_tasks,
            'llm_usage_count': 0,  # 这里可以从LLM模块获取
        }
    )
    
    context = {
        'total_workflows': total_workflows,
        'active_workflows': active_workflows,
        'total_script_tasks': total_script_tasks,
        'completed_script_tasks': completed_script_tasks,
        'total_audio_tasks': total_audio_tasks,
        'completed_audio_tasks': completed_audio_tasks,
        'script_success_rate': round(script_success_rate, 2),
        'audio_success_rate': round(audio_success_rate, 2),
        'daily_stats': daily_stats,
        'stats': stats,
    }
    return render(request, 'generators/statistics.html', context)


def export_statistics(request):
    """导出统计数据"""
    try:
        # 获取统计数据
        stats = GenerationStatistics.objects.order_by('-date')[:30]
        
        # 构建CSV数据
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['日期', '脚本生成数量', '音频生成数量', 'LLM使用数量'])
        
        # 写入数据行
        for stat in stats:
            writer.writerow([
                stat.date.strftime('%Y-%m-%d'),
                stat.script_generation_count,
                stat.audio_generation_count,
                stat.llm_usage_count
            ])
        
        # 创建HTTP响应
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="generation_statistics_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'导出失败: {str(e)}'
        }, status=500)
