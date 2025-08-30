from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
import json
import requests
from datetime import datetime, timedelta

from .models import LLMModel, LLMRequest, APIKey


def llm_model_list(request):
    """LLM模型列表视图"""
    models = LLMModel.objects.annotate(
        request_count=Count('llmrequest')
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        models = models.filter(
            Q(name__icontains=search_query) |
            Q(provider__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 按提供商过滤
    provider = request.GET.get('provider')
    if provider:
        models = models.filter(provider=provider)
    
    # 按状态过滤
    is_active = request.GET.get('is_active')
    if is_active:
        models = models.filter(is_active=(is_active == 'true'))
    
    # 分页
    paginator = Paginator(models, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取提供商列表
    providers = LLMModel.objects.values_list('provider', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_provider': provider,
        'selected_is_active': is_active,
        'providers': providers,
    }
    return render(request, 'llms/model_list.html', context)


def llm_model_detail(request, model_id):
    """LLM模型详情视图"""
    model = get_object_or_404(LLMModel, id=model_id)
    
    # 获取最近的请求记录
    recent_requests = LLMRequest.objects.filter(
        model=model
    ).order_by('-created_at')[:10]
    
    # 统计信息
    total_requests = LLMRequest.objects.filter(model=model).count()
    success_requests = LLMRequest.objects.filter(
        model=model,
        status='completed'
    ).count()
    
    success_rate = (success_requests / total_requests * 100) if total_requests > 0 else 0
    
    # 平均响应时间
    avg_response_time = LLMRequest.objects.filter(
        model=model,
        status='completed',
        response_time__isnull=False
    ).aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
    
    context = {
        'model': model,
        'recent_requests': recent_requests,
        'total_requests': total_requests,
        'success_requests': success_requests,
        'success_rate': round(success_rate, 2),
        'avg_response_time': round(avg_response_time, 2),
    }
    return render(request, 'llms/model_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_llm_model(request):
    """创建LLM模型"""
    try:
        data = json.loads(request.body)
        
        # 创建模型
        model = LLMModel.objects.create(
            name=data['name'],
            provider=data['provider'],
            model_id=data['model_id'],
            description=data.get('description', ''),
            max_tokens=data.get('max_tokens', 4096),
            temperature=data.get('temperature', 0.7),
            top_p=data.get('top_p', 1.0),
            frequency_penalty=data.get('frequency_penalty', 0.0),
            presence_penalty=data.get('presence_penalty', 0.0),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'success': True,
            'model_id': model.id,
            'message': 'LLM模型创建成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }, status=500)


def api_key_list(request):
    """API密钥列表视图"""
    api_keys = APIKey.objects.annotate(
        request_count=Count('llmrequest')
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        api_keys = api_keys.filter(
            Q(name__icontains=search_query) |
            Q(provider__icontains=search_query)
        )
    
    # 按提供商过滤
    provider = request.GET.get('provider')
    if provider:
        api_keys = api_keys.filter(provider=provider)
    
    # 按状态过滤
    is_active = request.GET.get('is_active')
    if is_active:
        api_keys = api_keys.filter(is_active=(is_active == 'true'))
    
    # 分页
    paginator = Paginator(api_keys, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取提供商列表
    providers = APIKey.objects.values_list('provider', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_provider': provider,
        'selected_is_active': is_active,
        'providers': providers,
    }
    return render(request, 'llms/api_key_list.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_api_key(request):
    """创建API密钥"""
    try:
        data = json.loads(request.body)
        
        # 创建API密钥
        api_key = APIKey.objects.create(
            name=data['name'],
            provider=data['provider'],
            key_value=data['key_value'],
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
        return JsonResponse({
            'success': True,
            'api_key_id': api_key.id,
            'message': 'API密钥创建成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_api_key(request, api_key_id):
    """测试API密钥"""
    try:
        api_key = get_object_or_404(APIKey, id=api_key_id)
        
        # 根据提供商进行不同的测试
        if api_key.provider.lower() == 'siliconflow':
            # SiliconFlow API测试
            url = 'https://api.siliconflow.cn/v1/models'
            headers = {
                'Authorization': f'Bearer {api_key.key_value}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                model_count = len(models_data.get('data', []))
                
                return JsonResponse({
                    'success': True,
                    'message': f'API密钥测试成功，可访问 {model_count} 个模型',
                    'details': {
                        'status_code': response.status_code,
                        'model_count': model_count
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'API密钥测试失败: HTTP {response.status_code}',
                    'details': {
                        'status_code': response.status_code,
                        'response': response.text[:200]
                    }
                })
        
        else:
            return JsonResponse({
                'success': False,
                'message': f'暂不支持 {api_key.provider} 提供商的测试'
            })
            
    except requests.RequestException as e:
        return JsonResponse({
            'success': False,
            'message': f'网络请求失败: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }, status=500)


def llm_request_list(request):
    """LLM请求记录列表视图"""
    requests_qs = LLMRequest.objects.select_related(
        'model', 'api_key'
    ).order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        requests_qs = requests_qs.filter(
            Q(request_id__icontains=search_query) |
            Q(model__name__icontains=search_query) |
            Q(prompt__icontains=search_query)
        )
    
    # 按状态过滤
    status = request.GET.get('status')
    if status:
        requests_qs = requests_qs.filter(status=status)
    
    # 按模型过滤
    model_id = request.GET.get('model_id')
    if model_id:
        requests_qs = requests_qs.filter(model_id=model_id)
    
    # 按时间范围过滤
    date_range = request.GET.get('date_range')
    if date_range:
        if date_range == 'today':
            start_date = timezone.now().date()
        elif date_range == 'week':
            start_date = timezone.now().date() - timedelta(days=7)
        elif date_range == 'month':
            start_date = timezone.now().date() - timedelta(days=30)
        else:
            start_date = None
        
        if start_date:
            requests_qs = requests_qs.filter(created_at__date__gte=start_date)
    
    # 分页
    paginator = Paginator(requests_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取模型列表用于过滤
    models = LLMModel.objects.filter(is_active=True).order_by('name')
    
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
        'selected_model_id': model_id,
        'selected_date_range': date_range,
        'models': models,
        'status_choices': status_choices,
    }
    return render(request, 'llms/request_list.html', context)


def llm_request_detail(request, request_id):
    """LLM请求详情视图"""
    llm_request = get_object_or_404(
        LLMRequest.objects.select_related('llm_model', 'api_key'),
        id=request_id
    )
    
    context = {
        'llm_request': llm_request,
    }
    return render(request, 'llms/request_detail.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def send_llm_request(request):
    """发送LLM请求"""
    try:
        data = json.loads(request.body)
        
        # 获取模型和API密钥
        model = get_object_or_404(LLMModel, id=data['model_id'])
        api_key = get_object_or_404(APIKey, id=data['api_key_id'])
        
        if not model.is_active:
            return JsonResponse({
                'success': False,
                'message': '选择的模型未激活'
            }, status=400)
        
        if not api_key.is_active:
            return JsonResponse({
                'success': False,
                'message': '选择的API密钥未激活'
            }, status=400)
        
        # 创建请求记录
        llm_request = LLMRequest.objects.create(
            model=model,
            api_key=api_key,
            prompt=data['prompt'],
            max_tokens=data.get('max_tokens', model.max_tokens),
            temperature=data.get('temperature', model.temperature),
            top_p=data.get('top_p', model.top_p),
            frequency_penalty=data.get('frequency_penalty', model.frequency_penalty),
            presence_penalty=data.get('presence_penalty', model.presence_penalty),
            status='pending'
        )
        
        # 发送请求到LLM API
        try:
            start_time = timezone.now()
            
            if api_key.provider.lower() == 'siliconflow':
                # SiliconFlow API调用
                url = 'https://api.siliconflow.cn/v1/chat/completions'
                headers = {
                    'Authorization': f'Bearer {api_key.key_value}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': model.model_id,
                    'messages': [
                        {'role': 'user', 'content': data['prompt']}
                    ],
                    'max_tokens': llm_request.max_tokens,
                    'temperature': llm_request.temperature,
                    'top_p': llm_request.top_p,
                    'frequency_penalty': llm_request.frequency_penalty,
                    'presence_penalty': llm_request.presence_penalty
                }
                
                llm_request.status = 'processing'
                llm_request.save()
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                end_time = timezone.now()
                response_time = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # 提取响应内容
                    if 'choices' in response_data and len(response_data['choices']) > 0:
                        response_text = response_data['choices'][0]['message']['content']
                        
                        # 更新请求记录
                        llm_request.response = response_text
                        llm_request.status = 'completed'
                        llm_request.response_time = response_time
                        llm_request.tokens_used = response_data.get('usage', {}).get('total_tokens', 0)
                        llm_request.completed_at = end_time
                        llm_request.save()
                        
                        return JsonResponse({
                            'success': True,
                            'request_id': llm_request.id,
                            'response': response_text,
                            'response_time': response_time,
                            'tokens_used': llm_request.tokens_used
                        })
                    else:
                        llm_request.status = 'failed'
                        llm_request.error_message = '响应格式错误'
                        llm_request.save()
                        
                        return JsonResponse({
                            'success': False,
                            'message': '响应格式错误'
                        }, status=500)
                else:
                    llm_request.status = 'failed'
                    llm_request.error_message = f'HTTP {response.status_code}: {response.text}'
                    llm_request.save()
                    
                    return JsonResponse({
                        'success': False,
                        'message': f'API请求失败: HTTP {response.status_code}'
                    }, status=500)
            
            else:
                llm_request.status = 'failed'
                llm_request.error_message = f'不支持的提供商: {api_key.provider}'
                llm_request.save()
                
                return JsonResponse({
                    'success': False,
                    'message': f'不支持的提供商: {api_key.provider}'
                }, status=400)
                
        except requests.RequestException as e:
            llm_request.status = 'failed'
            llm_request.error_message = f'网络请求失败: {str(e)}'
            llm_request.save()
            
            return JsonResponse({
                'success': False,
                'message': f'网络请求失败: {str(e)}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'请求失败: {str(e)}'
        }, status=500)


def llm_statistics(request):
    """LLM使用统计视图"""
    # 基本统计
    total_requests = LLMRequest.objects.count()
    completed_requests = LLMRequest.objects.filter(status='completed').count()
    failed_requests = LLMRequest.objects.filter(status='failed').count()
    
    success_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    # 按模型统计
    model_stats = LLMModel.objects.annotate(
        request_count=Count('llmrequest'),
        success_count=Count('llmrequest', filter=Q(llmrequest__status='completed')),
        avg_response_time=Avg('llmrequest__response_time', filter=Q(llmrequest__status='completed'))
    ).order_by('-request_count')
    
    # 按日期统计（最近30天）
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=29)
    
    daily_stats = []
    current_date = start_date
    while current_date <= end_date:
        day_requests = LLMRequest.objects.filter(
            created_at__date=current_date
        ).count()
        day_success = LLMRequest.objects.filter(
            created_at__date=current_date,
            status='completed'
        ).count()
        
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'requests': day_requests,
            'success': day_success
        })
        current_date += timedelta(days=1)
    
    context = {
        'total_requests': total_requests,
        'completed_requests': completed_requests,
        'failed_requests': failed_requests,
        'success_rate': round(success_rate, 2),
        'model_stats': model_stats,
        'daily_stats': daily_stats,
    }
    return render(request, 'llms/statistics.html', context)
