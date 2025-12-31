from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Route, RouteStop
from city.models import City, Country

# Ми не імпортуємо CarrierProfile, якщо він викликає помилку.
# Замість цього ми використовуємо доступ через атрибут користувача.

User = get_user_model()


class RouteScheduleTest(TestCase):
    def setUp(self):
        # 1. Створюємо користувача (перевізника)
        self.user = User.objects.create_user(username='carrier', password='password123')

        # 2. Створюємо країну та місто для зупинок
        self.country = Country.objects.create(name="Україна")
        self.city_kyiv = City.objects.create(name="Київ", slug="kyiv", country=self.country)
        self.city_lviv = City.objects.create(name="Львів", slug="lviv", country=self.country)

        # 3. Створюємо базовий маршрут
        self.route = Route.objects.create(
            carrier=self.user,
            title="Київ - Львів (Експрес)",
            price_per_km=2.0
        )

        self.client = Client()
        self.client.login(username='carrier', password='password123')

    def test_get_schedule_days_method(self):
        """Тест властивості get_schedule_days, яка збирає дні тижня"""
        # Створюємо зупинки на Пн (1) та Ср (3)
        RouteStop.objects.create(
            route=self.route,
            city=self.city_kyiv,
            day_of_week=1,
            departure_time="08:00"
        )
        RouteStop.objects.create(
            route=self.route,
            city=self.city_lviv,
            day_of_week=3,
            departure_time="14:00"
        )

        # Очікуємо рядок "Пн, Ср"
        self.assertEqual(self.route.get_schedule_days(), "Пн, Ср")

    def test_route_is_boosted_property(self):
        """Перевірка властивості ТОП-статусу"""
        # Сьогоднішній ТОП має бути активним
        self.route.top_until = timezone.now().date() + timezone.timedelta(days=1)
        self.assertTrue(self.route.is_boosted)

        # Вчорашній ТОП має бути неактивним
        self.route.top_until = timezone.now().date() - timezone.timedelta(days=1)
        self.assertFalse(self.route.is_boosted)

    def test_route_stop_ordering(self):
        """Перевірка, що зупинки сортуються за днем тижня та часом"""
        # Створюємо пізнішу зупинку першою
        RouteStop.objects.create(route=self.route, city=self.city_lviv, day_of_week=2, departure_time="10:00")
        # Створюємо ранню зупинку пізніше
        RouteStop.objects.create(route=self.route, city=self.city_kyiv, day_of_week=1, departure_time="09:00")

        stops = self.route.stops.all()
        self.assertEqual(stops[0].city, self.city_kyiv)  # Понеділок має бути першим
        self.assertEqual(stops[1].city, self.city_lviv)  # Вівторок другим