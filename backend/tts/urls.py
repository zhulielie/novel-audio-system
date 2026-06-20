from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import TTSEngineViewSet, VoiceAssetViewSet, TTSGenerationTaskViewSet

router = DefaultRouter()
router.register(r'engines', TTSEngineViewSet, basename='tts-engine')
router.register(r'voices', VoiceAssetViewSet, basename='voice-asset')
router.register(r'tasks', TTSGenerationTaskViewSet, basename='tts-task')

urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'tts'
