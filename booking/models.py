from django.db import models
from django.conf import settings
from trips.models import Route

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
        ('cancelled', 'Скасовано'),
    ]

    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='bookings')
    trip_date = models.DateField(verbose_name="Дата поїздки")
    seats_count = models.PositiveIntegerField(default=1, verbose_name="Кількість місць")
    contact_phone = models.CharField(max_length=20, verbose_name="Номер телефону")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    departure_point = models.CharField(max_length=100, verbose_name="Місце посадки")
    arrival_point = models.CharField(max_length=100, verbose_name="Місце висадки")
    def __str__(self):
        return f"{self.passenger.username} - {self.route.title} ({self.trip_date})"