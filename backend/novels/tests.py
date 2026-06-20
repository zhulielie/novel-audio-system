from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Novel, Chapter

User = get_user_model()


class NovelAPITests(APITestCase):
    """小说与章节接口测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.novel = Novel.objects.create(
            title='测试小说',
            author='测试作者',
            description='这是一个测试小说',
            status='published'
        )
        self.chapter = Chapter.objects.create(
            novel=self.novel,
            title='第1章 测试章节',
            content='这是测试章节的内容。',
            chapter_number='1',
            chapter_sort_number=1,
            is_published=True
        )

    def test_list_novels(self):
        response = self.client.get('/api/novels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], '测试小说')

    def test_retrieve_novel(self):
        response = self.client.get(f'/api/novels/{self.novel.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '测试小说')
        self.assertEqual(response.data['chapters_count'], 1)

    def test_list_chapters(self):
        response = self.client.get(f'/api/novels/{self.novel.id}/chapters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], '第1章 测试章节')

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/novels/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
