from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# 导入各应用的API视图
from novels.api_views import NovelViewSet, ChapterViewSet, NovelSourceViewSet, NovelSourceRelationViewSet, test_batch_import
from novels.simple_batch_import import simple_batch_import
from novels.crawler_api_views import CrawlerAPIViewSet, quick_crawl, auto_crawl_next_chapters
from novels import batch_download_api
from audios.api_views import AudioProjectViewSet, GeneratedAudioViewSet
from llms.api_views import LLMModelViewSet, LLMRequestViewSet
from generators.api_views import WorkflowViewSet, TaskViewSet
from tts.api_views import TTSEngineViewSet, VoiceAssetViewSet, TTSGenerationTaskViewSet, voxcpm_synthesize, voxcpm_outputs, voxcpm_output_file, voxcpm_references, voxcpm_reference_delete
from .api_views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    UserProfileView,
    ChangePasswordView,
    logout_view,
    user_info_view,
    delete_account_view,
    check_username_view,
    check_email_view,
    dashboard_stats_view
)

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'novels', NovelViewSet)
router.register(r'novel-sources', NovelSourceViewSet)
router.register(r'novel-source-relations', NovelSourceRelationViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'crawler', CrawlerAPIViewSet, basename='crawler')
router.register(r'audio-projects', AudioProjectViewSet)
router.register(r'generated-audios', GeneratedAudioViewSet)
router.register(r'llm-models', LLMModelViewSet)
router.register(r'llm-requests', LLMRequestViewSet)
router.register(r'workflows', WorkflowViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'tts-engines', TTSEngineViewSet)
router.register(r'tts-voices', VoiceAssetViewSet)
router.register(r'tts-tasks', TTSGenerationTaskViewSet)

# URL模式
urlpatterns = [
    # 认证相关
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/user/', user_info_view, name='user_info'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/delete-account/', delete_account_view, name='delete_account'),
    path('auth/check-username/', check_username_view, name='check_username'),
    path('auth/check-email/', check_email_view, name='check_email'),
    
    # 仪表板
    path('dashboard/stats/', dashboard_stats_view, name='dashboard_stats'),
    
    # 测试API
    path('test-batch-import/', test_batch_import, name='test_batch_import'),
    
    # 简化批量导入API
    path('simple_batch_import/', simple_batch_import, name='simple_batch_import'),
    
    # 整合爬虫API
    path('crawler/quick-crawl/', quick_crawl, name='quick_crawl'),
    path('crawler/auto-crawl/', auto_crawl_next_chapters, name='auto_crawl_next_chapters'),
    
    # 批量下载API
    path('novels/batch-download/create/', batch_download_api.create_batch_download, name='create_batch_download'),
    path('novels/batch-download/list/', batch_download_api.list_download_tasks, name='list_download_tasks'),
    path('novels/batch-download/stats/', batch_download_api.get_task_stats, name='get_task_stats'),
    path('novels/batch-download/batch-create/', batch_download_api.batch_create_downloads, name='batch_create_downloads'),
    path('novels/batch-download/<int:task_id>/', batch_download_api.get_task_detail, name='get_task_detail'),
    path('novels/batch-download/<int:task_id>/pause/', batch_download_api.pause_task, name='pause_task'),
    path('novels/batch-download/<int:task_id>/resume/', batch_download_api.resume_task, name='resume_task'),
    path('novels/batch-download/<int:task_id>/cancel/', batch_download_api.cancel_task, name='cancel_task'),
    
    # VoxCPM 2.0 合成 API
    path('tts/voxcpm/synthesize/', voxcpm_synthesize, name='voxcpm_synthesize'),
    path('tts/voxcpm/outputs/', voxcpm_outputs, name='voxcpm_outputs'),
    path('tts/voxcpm/outputs/<str:filename>/', voxcpm_output_file, name='voxcpm_output_file'),
    path('tts/voxcpm/references/', voxcpm_references, name='voxcpm_references'),
    path('tts/voxcpm/references/<str:filename>/', voxcpm_reference_delete, name='voxcpm_reference_delete'),
    
    # 包含路由器的URL
    path('', include(router.urls)),
]