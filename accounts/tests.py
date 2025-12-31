from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from trips.models import Route, RouteStop
from booking.models import Booking
from city.models import City, Country
from datetime import date

User = get_user_model()


class AccountsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Створюємо Пасажира
        self.passenger = User.objects.create_user(
            username='passenger',
            password='password123',
            is_carrier=False
        )

        # 2. Створюємо Перевізника
        self.carrier = User.objects.create_user(
            username='carrier',
            password='password123',
            is_carrier=True
        )

        # Створюємо країну та місто (необхідно для RouteStop та валідації)
        self.country = Country.objects.create(name="Україна")
        self.city_a = City.objects.create(name="Київ", slug="kyiv", country=self.country)
        self.city_b = City.objects.create(name="Львів", slug="lviv", country=self.country)

        # 3. Створюємо Маршрут
        self.route = Route.objects.create(
            title="Київ - Львів",
            carrier=self.carrier,
            is_active=True,
            price_per_km=2.0
        )

        # 4. Створюємо Бронювання (з виправленими полями для валідації full_clean)
        self.booking = Booking.objects.create(
            passenger=self.passenger,
            route=self.route,
            seats_count=2,
            total_price=1000,
            trip_date=date.today(),
            status='confirmed',
            # Обов'язкові поля, через які виникала помилка ValidationError:
            departure_point="Київ",
            arrival_point="Львів"
        )

    # --- Тести Профілю ---

    def test_profile_view_passenger(self):
        """Перевірка профілю пасажира: має бути кількість бронювань"""
        self.client.login(username='passenger', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_passenger.html')
        # Перевіряємо, що в контексті є 1 бронювання
        self.assertEqual(response.context['bookings_count'], 1)

    def test_profile_view_carrier(self):
        """Перевірка профілю перевізника: мають бути маршрути та вхідні бронювання"""
        self.client.login(username='carrier', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_carrier.html')
        self.assertIn(self.route, response.context['routes'])
        self.assertIn(self.booking, response.context['incoming_bookings'])

    # --- Тести Статистики ---

    def test_statistics_passenger(self):
        """Тест розрахунку бонусів та витрат пасажира"""
        self.client.login(username='passenger', password='password123')
        # Переконайтеся, що назва 'statistics' збігається з вашим urls.py
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(response.context['spent_money']), 1000.0)
        # Припустимо, 1 поїздка = 10 бонусів
        self.assertEqual(response.context['bonuses'], 10)

    def test_statistics_carrier_aggregation(self):
        """Тест складної статистики перевізника (Revenue та Кількість пасажирів)"""
        self.client.login(username='carrier', password='password123')
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(response.context['total_revenue']), 1000.0)
        self.assertEqual(response.context['total_passengers'], 2)

        # Перевірка Subquery: дохід конкретного маршруту
        route_from_ctx = response.context['routes_list'][0]
        self.assertEqual(float(route_from_ctx.route_revenue), 1000.0)

    def test_statistics_date_filter(self):
        """Тест фільтрації статистики по датах"""
        self.client.login(username='carrier', password='password123')
        # Фільтруємо період, де немає поїздок
        response = self.client.get(reverse('statistics'), {
            'start_date': '2000-01-01',
            'end_date': '2000-01-02'
        })
        self.assertEqual(float(response.context['total_revenue']), 0.0)

    # --- Тести безпеки ---

    def test_login_required_redirect(self):
        """Перевірка, що неавторизованого юзера редиректить з профілю"""
        self.client.logout()
        response = self.client.get(reverse('profile'))
        # 302 - це редирект на сторінку логіну
        self.assertEqual(response.status_code, 302)

    def test_check_balance_redirect_for_non_carrier(self):
        """Пасажира має редиректити з перевірки балансу (бо немає carrier_profile)"""
        self.client.login(username='passenger', password='password123')
        # Переконайтеся, що назва 'check_balance' збігається з вашим urls.py
        response = self.client.get(reverse('check_balance'))
        self.assertEqual(response.status_code, 302)