from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
import json
import os

from .models import (
    AudioProject, EmotionType, EmotionAudio, 
    GeneratedAudio, AudioTemplate, AudioProcessingLog
)
from novels.models import Novel, Chapter


def audio_project_list(request):
    """音频项目列表视图"""
    projects = AudioProject.objects.all().order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(novel__title__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'audios/project_list.html', context)


def audio_project_detail(request, project_id):
    """音频项目详情视图"""
    project = get_object_or_404(AudioProject, id=project_id)
    
    # 获取项目相关的生成音频
    generated_audios = GeneratedAudio.objects.filter(
        project=project
    ).order_by('-created_at')
    
    # 获取处理日志
    processing_logs = AudioProcessingLog.objects.filter(
        project=project
    ).order_by('-created_at')[:10]
    
    context = {
        'project': project,
        'generated_audios': generated_audios,
        'processing_logs': processing_logs,
    }
    return render(request, 'audios/project_detail.html', context)


def create_audio_project(request):
    """创建音频项目视图"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 获取关联的小说
            novel = None
            if data.get('novel_id'):
                novel = get_object_or_404(Novel, id=data['novel_id'])
            
            # 创建音频项目
            project = AudioProject.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                novel=novel,
                voice_settings=data.get('voice_settings', {}),
                output_format=data.get('output_format', 'mp3'),
                quality_level=data.get('quality_level', 'standard')
            )
            
            return JsonResponse({
                'success': True,
                'project_id': project.id,
                'message': '音频项目创建成功'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'创建失败: {str(e)}'
            }, status=400)
    
    # GET请求，显示创建表单
    novels = Novel.objects.all().order_by('-created_at')
    context = {
        'novels': novels,
    }
    return render(request, 'audios/create_project.html', context)


def emotion_type_list(request):
    """情绪类型列表视图"""
    emotion_types = EmotionType.objects.all().order_by('name')
    
    context = {
        'emotion_types': emotion_types,
    }
    return render(request, 'audios/emotion_type_list.html', context)


def emotion_audio_list(request):
    """情绪音频列表视图"""
    emotion_audios = EmotionAudio.objects.all().order_by('-created_at')
    
    # 按情绪类型过滤
    emotion_type_id = request.GET.get('emotion_type')
    if emotion_type_id:
        emotion_audios = emotion_audios.filter(emotion_type_id=emotion_type_id)
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        emotion_audios = emotion_audios.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(emotion_audios, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取所有情绪类型用于过滤器
    emotion_types = EmotionType.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'emotion_types': emotion_types,
        'selected_emotion_type': emotion_type_id,
        'search_query': search_query,
    }
    return render(request, 'audios/emotion_audio_list.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def upload_emotion_audio(request):
    """上传情绪音频"""
    try:
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        emotion_type_id = request.POST.get('emotion_type_id')
        audio_file = request.FILES.get('audio_file')
        
        if not all([name, emotion_type_id, audio_file]):
            return JsonResponse({
                'success': False,
                'message': '缺少必要参数'
            }, status=400)
        
        emotion_type = get_object_or_404(EmotionType, id=emotion_type_id)
        
        # 创建情绪音频记录
        emotion_audio = EmotionAudio.objects.create(
            name=name,
            description=description,
            emotion_type=emotion_type,
            audio_file=audio_file,
            file_size=audio_file.size,
            duration=0  # 需要后续处理获取实际时长
        )
        
        return JsonResponse({
            'success': True,
            'audio_id': emotion_audio.id,
            'message': '音频上传成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }, status=500)


def generated_audio_list(request):
    """生成音频列表视图"""
    generated_audios = GeneratedAudio.objects.all().order_by('-created_at')
    
    # 按项目过滤
    project_id = request.GET.get('project')
    if project_id:
        generated_audios = generated_audios.filter(project_id=project_id)
    
    # 按状态过滤
    status = request.GET.get('status')
    if status:
        generated_audios = generated_audios.filter(status=status)
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        generated_audios = generated_audios.filter(
            Q(original_text__icontains=search_query) |
            Q(project__name__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(generated_audios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取项目列表用于过滤器
    projects = AudioProject.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'projects': projects,
        'selected_project': project_id,
        'selected_status': status,
        'search_query': search_query,
        'status_choices': GeneratedAudio.STATUS_CHOICES,
    }
    return render(request, 'audios/generated_audio_list.html', context)


def audio_template_list(request):
    """音频模板列表视图"""
    templates = AudioTemplate.objects.all().order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 分页
    paginator = Paginator(templates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'audios/template_list.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def download_audio(request, audio_id):
    """下载音频文件"""
    try:
        audio = get_object_or_404(GeneratedAudio, id=audio_id)
        
        if not audio.audio_file or not os.path.exists(audio.audio_file.path):
            return JsonResponse({
                'success': False,
                'message': '音频文件不存在'
            }, status=404)
        
        # 更新下载次数
        audio.download_count += 1
        audio.save(update_fields=['download_count'])
        
        # 返回文件下载响应
        with open(audio.audio_file.path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='audio/mpeg')
            response['Content-Disposition'] = f'attachment; filename="{audio.audio_file.name}"'
            return response
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'下载失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_audio(request, audio_id):
    """删除音频文件"""
    try:
        audio = get_object_or_404(GeneratedAudio, id=audio_id)
        
        # 删除物理文件
        if audio.audio_file and os.path.exists(audio.audio_file.path):
            os.remove(audio.audio_file.path)
        
        # 删除数据库记录
        audio.delete()
        
        return JsonResponse({
            'success': True,
            'message': '音频删除成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }, status=500)
