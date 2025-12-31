from django.test import TestCase, Client
from django.urls import reverse
from .models import Post


class NewsViewTest(TestCase):
    def setUp(self):
        self.active_post = Post.objects.create(
            title="Активна новина",
            slug="active-news",
            content="Зміст...",
            is_active=True
        )
        self.inactive_post = Post.objects.create(
            title="Чернетка",
            slug="draft-news",
            content="Зміст чернетки...",
            is_active=False
        )
        self.client = Client()

    def test_news_list_view_filters_active(self):
        """Перевірка, що у списку відображаються лише активні новини"""
        # ВИПРАВЛЕНО: 'news_list' замість 'list'
        url = reverse('news:news_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.active_post, response.context['posts'])
        self.assertNotIn(self.inactive_post, response.context['posts'])

    def test_news_detail_view_active(self):
        """Перевірка доступу до активної новини"""
        # ВИПРАВЛЕНО: 'news_detail' замість 'detail'
        url = reverse('news:news_detail', kwargs={'slug': self.active_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.active_post)

    def test_news_detail_view_inactive_returns_404(self):
        """Перевірка, що неактивна новина видає помилку 404"""
        # ВИПРАВЛЕНО: 'news_detail' замість 'detail'
        url = reverse('news:news_detail', kwargs={'slug': self.inactive_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)