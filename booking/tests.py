from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from trips.models import Route
from booking.models import Booking

User = get_user_model()


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.route = Route.objects.create(
            title="Київ - Львів",
            carrier=self.user,
            price_per_km=1.5,
            min_trip_price=100
        )

    def test_booking_creation_success(self):
        today = timezone.now().date()
        booking = Booking.objects.create(
            passenger=self.user,
            route=self.route,
            trip_date=today,
            seats_count=2,
            departure_point="Київ",
            arrival_point="Львів",
            total_price=500.00
        )
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(Booking.objects.count(), 1)

    def test_clean_past_date_error(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        booking = Booking(
            passenger=self.user,
            route=self.route,
            trip_date=yesterday,
            seats_count=1,
            departure_point="Київ",
            arrival_point="Львів"
        )
        with self.assertRaises(ValidationError):
            booking.save()

    def test_clean_seats_count_error(self):
        booking = Booking(
            passenger=self.user,
            route=self.route,
            trip_date=timezone.now().date(),
            seats_count=0,
            departure_point="Київ",
            arrival_point="Львів"
        )
        with self.assertRaises(ValidationError):
            booking.save()

    def test_is_cancellable_property(self):
        """Перевірка логіки властивості is_cancellable (ВИПРАВЛЕНО)"""
        today = timezone.now().date()
        booking = Booking.objects.create(
            passenger=self.user,
            route=self.route,
            trip_date=today,
            seats_count=1,
            departure_point="Київ",  # Додано обов'язкове поле
            arrival_point="Львів",  # Додано обов'язкове поле
            status='pending'
        )

        self.assertTrue(booking.is_cancellable)

        booking.status = 'cancelled'
        booking.save()
        self.assertFalse(booking.is_cancellable)

    def test_str_representation(self):
        """Перевірка методу __str__ (ВИПРАВЛЕНО)"""
        booking = Booking.objects.create(
            passenger=self.user,
            route=self.route,
            trip_date=timezone.now().date(),
            departure_point="Київ",  # Додано обов'язкове поле
            arrival_point="Львів"  # Додано обов'язкове поле
        )
        expected_str = f"№{booking.id}: {self.user.username} -> {self.route.title}"
        self.assertEqual(str(booking), expected_str)