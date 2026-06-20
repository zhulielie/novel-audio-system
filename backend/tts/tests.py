from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from novels.models import Novel, Chapter
from .models import TTSEngine, TTSGenerationTask




User = get_user_model()


class TTSAPITests(APITestCase):
    """TTS 接口测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.novel = Novel.objects.create(
            title='测试小说',
            author='测试作者',
            status='published'
        )
        self.chapter = Chapter.objects.create(
            novel=self.novel,
            title='第1章 测试章节',
            content='这是测试章节的内容。\n"这是对话内容。"',
            chapter_number='1',
            chapter_sort_number=1,
            is_published=True
        )
        self.engine = TTSEngine.objects.create(
            name='Edge TTS',
            engine_type='edge_tts',
            is_active=True,
            is_default=True
        )

    def test_list_tts_tasks(self):
        TTSGenerationTask.objects.create(
            name='测试任务',
            novel=self.novel,
            chapter=self.chapter,
            engine=self.engine,
            status='completed'
        )
        response = self.client.get('/api/tts-tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_quick_synthesize_creates_task(self):
        with patch('django_q.tasks.async_task') as mock_async_task:
            response = self.client.post(
                '/api/tts-tasks/quick_synthesize/',
                {
                    'novel_id': self.novel.id,
                    'chapter_id': self.chapter.id,
                    'speaker_configs': {
                        'narrator': '旁白',
                        'dialogue': '角色A'
                    }
                },
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertIn('task_id', response.data)
            mock_async_task.assert_called_once()

            task = TTSGenerationTask.objects.get(id=response.data['task_id'])
            self.assertEqual(task.novel, self.novel)
            self.assertEqual(task.chapter, self.chapter)
            self.assertEqual(task.status, 'pending')

    def test_quick_synthesize_missing_params(self):
        response = self.client.post('/api/tts-tasks/quick_synthesize/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
