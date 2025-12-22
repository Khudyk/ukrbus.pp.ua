from django.conf import settings
from django.db import models
from django.utils import timezone

from city.models import City


class Route(models.Model):
    carrier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='routes',
                                verbose_name="Перевізник")
    title = models.CharField(max_length=255, verbose_name="Назва маршруту")
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    top_until = models.DateTimeField(null=True, blank=True, verbose_name="ТОП діє до")

    is_passenger = models.BooleanField(
        default=True,
        verbose_name="Пасажирські перевезення",
        help_text="Чи доступне бронювання місць для пасажирів"
    )
    is_parcel = models.BooleanField(
        default=True,
        verbose_name="Доставка посилок",
        help_text="Чи приймає цей маршрут посилки для передачі"
    )

    # --- Поля для цін (залишаються як були) ---
    min_trip_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                         verbose_name="Мінімальна ціна поїздки")
    price_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ціна за 1 км")
    min_parcel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           verbose_name="Мінімальна ціна посилки")
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ціна за 1 кг")

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршрути"
        ordering = ['-top_until', '-id']

    def __str__(self):
        return self.title

    @property
    def is_boosted(self):
        if self.top_until:
            return self.top_until > timezone.now()
        return False

    # === ВСТАВЛЯЙТЕ СЮДИ (всередині класу Route) ===
    def get_schedule_days(self):
        # Отримуємо всі унікальні номери днів із зупинок цього маршруту
        day_numbers = self.stops.values_list('day_of_week', flat=True).distinct().order_by('day_of_week')

        # Словник для перетворення цифр у назви
        days_map = {
            1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Нд'
        }

        if not day_numbers:
            return None

        return ", ".join([days_map.get(d) for d in day_numbers])
    # ===============================================


class RouteStop(models.Model):
    DAYS_OF_WEEK = [
        (1, 'Понеділок'),
        (2, 'Вівторок'),
        (3, 'Середа'),
        (4, 'Четвер'),
        (5, "П'ятниця"),
        (6, 'Субота'),
        (7, 'Неділя'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="Місто")
    order = models.PositiveIntegerField(
        verbose_name="Порядок",
        default=1,
        blank=True,
        null=True
    )

    # Нові поля: День тижня та Час
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="День тижня")
    departure_time = models.TimeField(verbose_name="Час відправлення")

    class Meta:
        verbose_name = "Зупинка з розкладом"
        verbose_name_plural = "Зупинки з розкладом"
        ordering = ['day_of_week', 'departure_time']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.departure_time} - {self.city.name}"
