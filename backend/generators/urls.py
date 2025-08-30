from django.urls import path
from . import views

app_name = 'generators'

urlpatterns = [
    # 生成工作流相关URL
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/create/', views.create_workflow, name='create_workflow'),
    path('workflows/<int:workflow_id>/', views.workflow_detail, name='workflow_detail'),
    path('workflows/<int:workflow_id>/start/', views.start_workflow, name='start_workflow'),
    path('workflows/<int:workflow_id>/stop/', views.stop_workflow, name='stop_workflow'),
    
    # 脚本生成任务相关URL
    path('script-tasks/', views.script_task_list, name='script_task_list'),
    path('script-tasks/create/', views.create_script_task, name='create_script_task'),
    path('script-tasks/<int:task_id>/', views.script_task_detail, name='script_task_detail'),
    path('script-tasks/<int:task_id>/start/', views.start_script_task, name='start_script_task'),
    
    # 音频生成任务相关URL
    path('audio-tasks/', views.audio_task_list, name='audio_task_list'),
    path('audio-tasks/create/', views.create_audio_task, name='create_audio_task'),
    path('audio-tasks/<int:task_id>/', views.audio_task_detail, name='audio_task_detail'),
    path('audio-tasks/<int:task_id>/start/', views.start_audio_task, name='start_audio_task'),
    
    # 脚本片段相关URL
    path('script-segments/', views.script_segment_list, name='script_segment_list'),
    path('script-segments/<int:segment_id>/', views.script_segment_detail, name='script_segment_detail'),
    path('script-segments/<int:segment_id>/edit/', views.edit_script_segment, name='edit_script_segment'),
    
    # 统计相关URL
    path('statistics/', views.generation_statistics, name='statistics'),
    path('statistics/export/', views.export_statistics, name='export_statistics'),
]