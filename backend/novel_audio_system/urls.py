"""
URL configuration for novel_audio_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views, auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    
    # API路由
    path('api/', include('novel_audio_system.api_urls')),
    
    # 认证相关URL
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/ajax-login/', auth_views.ajax_login, name='ajax_login'),
    path('auth/profile/', auth_views.profile_view, name='profile'),
    
    # 应用模块URL
    path('novels/', include('novels.urls')),
    path('audios/', include('audios.urls')),
    path('llms/', include('llms.urls')),
    path('generators/', include('generators.urls')),
]

# 开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
