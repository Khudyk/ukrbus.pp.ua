from django.test import TestCase, Client
from django.urls import reverse
from .models import City, Country  # Додайте модель Country

class CityWebTest(TestCase):
    def setUp(self):
        # 1. Спочатку створюємо країну
        self.country = Country.objects.create(
            name="Україна",
            # додайте інші обов'язкові поля країни, якщо вони є (наприклад, code="UA")
        )

        # 2. Створюємо місто, передаючи створену країну
        self.city = City.objects.create(
            name="Київ",
            slug="kyiv",
            country=self.country  # ТЕПЕР ПОМИЛКИ НЕ БУДЕ
        )
        self.client = Client()

    def test_city_list_view(self):
        """Тест сторінки списку міст"""
        url = reverse('city:city_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Київ")

    def test_city_autocomplete(self):
        """Тест автокомпліту (пошук)"""
        url = reverse('city:city_autocomplete')
        response = self.client.get(url, {'term': 'киї'})
        self.assertEqual(response.status_code, 200)
        # Отримуємо результати з JSON
        results = response.json().get('results', [])
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]['text'], "Київ")

    def test_city_detail_view(self):
        """Тест сторінки детальної інформації за слагом"""
        url = reverse('city:city_detail', kwargs={'slug': self.city.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Київ")