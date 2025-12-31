from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from trips.models import Route


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
        ('cancelled', 'Скасовано'),
    ]

    # Зв'язки
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Дані поїздки
    trip_date = models.DateField(verbose_name="Дата поїздки",db_index=True)
    seats_count = models.PositiveIntegerField(default=1, verbose_name="Кількість місць")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending',db_index=True)

    # Маршрутні точки (зберігаємо текстом, щоб дані лишилися навіть якщо зупинку видалять)
    departure_point = models.CharField(max_length=100, verbose_name="Місце посадки",db_index=True)
    arrival_point = models.CharField(max_length=100, verbose_name="Місце висадки",db_index=True)

    # Фінанси
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Загальна вартість"
    )

    # Системні поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Корисно для відстеження змін статусу

    class Meta:
        verbose_name = "Бронювання"
        verbose_name_plural = "Бронювання"
        ordering = ['-created_at']

    def __str__(self):
        return f"№{self.id}: {self.passenger.username} -> {self.route.title}"

    def clean(self):
        """Валідація даних перед збереженням"""
        # 1. Перевірка дати (не можна бронювати на минуле)
        if self.trip_date < timezone.now().date():
            raise ValidationError({'trip_date': "Не можна створити бронювання на минулу дату."})

        # 2. Перевірка кількості місць
        if self.seats_count < 1:
            raise ValidationError({'seats_count': "Кількість місць повинна бути не менше 1."})

    def save(self, *args, **kwargs):
        """Автоматизація перед записом в БД"""
        self.full_clean()  # Викликає метод clean() перед збереженням
        super().save(*args, **kwargs)

    @property
    def is_cancellable(self):
        """Перевірка, чи можна ще скасувати це бронювання"""
        return self.status != 'cancelled' and self.trip_date >= timezone.now().date()