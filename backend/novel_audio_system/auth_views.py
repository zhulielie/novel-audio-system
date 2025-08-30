from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
import json


def login_view(request):
    """登录视图"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # 设置会话过期时间
                if not remember:
                    # 如果没有勾选"记住我"，浏览器关闭时会话过期
                    request.session.set_expiry(0)
                else:
                    # 记住我：30天
                    request.session.set_expiry(30 * 24 * 60 * 60)
                
                # 获取next参数，如果没有则跳转到首页
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, '用户名或密码错误')
        else:
            messages.error(request, '请填写完整的登录信息')
    
    return render(request, 'registration/login.html')


@login_required
def logout_view(request):
    """登出视图"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login')


@csrf_exempt
@require_http_methods(["POST"])
def ajax_login(request):
    """AJAX登录接口"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '请填写完整的登录信息'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 设置会话过期时间
            if not remember:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(30 * 24 * 60 * 60)
            
            return JsonResponse({
                'success': True,
                'message': '登录成功',
                'redirect_url': '/'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': '用户名或密码错误'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '请求格式错误'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': '服务器错误，请稍后重试'
        }, status=500)


def profile_view(request):
    """用户资料页面"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {
        'user': request.user
    }
    return render(request, 'registration/profile.html', context)