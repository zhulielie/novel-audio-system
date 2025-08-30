from django.urls import path
from . import views

app_name = 'audios'

urlpatterns = [
    # 音频项目相关URL
    path('projects/', views.audio_project_list, name='audio_project_list'),
    path('projects/create/', views.create_audio_project, name='create_project'),
    path('projects/<int:project_id>/', views.audio_project_detail, name='project_detail'),
    
    # 情绪类型相关URL
    path('emotion-types/', views.emotion_type_list, name='emotion_type_list'),
    
    # 情绪音频相关URL
    path('emotion-audios/', views.emotion_audio_list, name='emotion_audio_list'),
    path('emotion-audios/upload/', views.upload_emotion_audio, name='upload_emotion_audio'),
    
    # 生成音频相关URL
    path('generated/', views.generated_audio_list, name='generated_audio_list'),
    path('generated/<int:audio_id>/download/', views.download_audio, name='download_audio'),
    path('generated/<int:audio_id>/delete/', views.delete_audio, name='delete_audio'),
    
    # 音频模板相关URL
    path('templates/', views.audio_template_list, name='template_list'),
]