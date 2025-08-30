from django.urls import path
from . import views
from . import batch_download_api
from . import api_views

app_name = 'novels'

urlpatterns = [
    # 小说相关URL
    path('', views.novel_list, name='novel_list'),
    path('create/', views.create_novel, name='create_novel'),
    path('<int:novel_id>/', views.novel_detail, name='novel_detail'),
    
    # 章节相关URL
    path('<int:novel_id>/chapters/', views.chapter_list, name='chapter_list'),
    path('<int:novel_id>/chapters/create/', views.create_chapter, name='create_chapter'),
    path('<int:novel_id>/chapters/import/', views.import_chapters, name='import_chapters'),
    path('<int:novel_id>/chapters/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    
    # 角色相关URL
    path('<int:novel_id>/characters/', views.character_list, name='character_list'),
    path('<int:novel_id>/characters/create/', views.create_character, name='create_character'),

    # MCP客户端功能URL
    path('<int:novel_id>/mcp/fix/', views.mcp_chapter_fix, name='mcp_chapter_fix'),
    path('<int:novel_id>/mcp/crawl/', views.mcp_crawl_chapters, name='mcp_crawl_chapters'),

    # Playwright监控功能URL
    path('playwright/monitor/', views.playwright_monitor, name='playwright_monitor'),
    path('playwright/keepalive/', views.playwright_keepalive, name='playwright_keepalive'),
    path('playwright/status/', views.playwright_status, name='playwright_status'),

    # 数据重置和爬取功能URL
    path('data/reset/', views.data_reset, name='data_reset'),
    path('data/recrawl/', views.data_recrawl, name='data_recrawl'),
    path('data/status/', views.data_operation_status, name='data_operation_status'),

    # 标签相关URL
    path('tags/', views.tag_list, name='tag_list'),
    
    # Vue爬虫管理界面
    path('crawler-vue/', views.crawler_vue_app, name='crawler_vue_app'),
    
    # 批量下载API
    path('batch-download/create/', batch_download_api.create_batch_download, name='create_batch_download'),
    path('batch-download/list/', batch_download_api.list_download_tasks, name='list_download_tasks'),
    path('batch-download/stats/', batch_download_api.get_task_stats, name='get_task_stats'),
    path('batch-download/batch-create/', batch_download_api.batch_create_downloads, name='batch_create_downloads'),
    path('batch-download/<int:task_id>/', batch_download_api.get_task_detail, name='get_task_detail'),
    path('batch-download/<int:task_id>/pause/', batch_download_api.pause_task, name='pause_task'),
    path('batch-download/<int:task_id>/resume/', batch_download_api.resume_task, name='resume_task'),
    path('batch-download/<int:task_id>/cancel/', batch_download_api.cancel_task, name='cancel_task'),
    
    # 用户阅读设置
    path('reading-settings/', api_views.user_reading_settings, name='user_reading_settings'),
]