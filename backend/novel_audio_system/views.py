from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from novels.models import Novel, Chapter
from audios.models import AudioProject
from generators.models import GenerationWorkflow, ScriptGenerationTask, AudioGenerationTask
from llms.models import LLMModel


@login_required
def index(request):
    """首页视图"""
    # 统计数据
    total_novels = Novel.objects.count()
    total_chapters = Chapter.objects.count()
    total_audio_projects = AudioProject.objects.count()
    total_workflows = GenerationWorkflow.objects.count()
    
    # 最近活动（模拟数据，实际项目中可以创建活动日志模型）
    recent_activities = []
    
    # 最近创建的小说
    recent_novels = Novel.objects.order_by('-created_at')[:3]
    for novel in recent_novels:
        recent_activities.append({
            'icon': 'book',
            'color': 'primary',
            'title': '创建了新小说',
            'description': f'《{novel.title}》',
            'created_at': novel.created_at
        })
    
    # 最近的生成任务
    recent_script_tasks = ScriptGenerationTask.objects.order_by('-created_at')[:2]
    for task in recent_script_tasks:
        recent_activities.append({
            'icon': 'file-alt',
            'color': 'success',
            'title': '脚本生成任务',
            'description': f'章节：{task.chapter.title}',
            'created_at': task.created_at
        })
    
    # 最近的音频任务
    recent_audio_tasks = AudioGenerationTask.objects.order_by('-created_at')[:2]
    for task in recent_audio_tasks:
        recent_activities.append({
            'icon': 'music',
            'color': 'warning',
            'title': '音频生成任务',
            'description': f'项目：{task.audio_project.name}',
            'created_at': task.created_at
        })
    
    # 按时间排序活动
    recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
    recent_activities = recent_activities[:5]  # 只显示最近5个活动
    
    context = {
        'total_novels': total_novels,
        'total_chapters': total_chapters,
        'total_audio_projects': total_audio_projects,
        'total_workflows': total_workflows,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'base/index.html', context)