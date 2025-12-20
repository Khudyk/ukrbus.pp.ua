from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from city.models import City


class Route(models.Model):
    carrier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name="Перевізник"
    )
    title = models.CharField(max_length=255, verbose_name="Назва маршруту")
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршрути"

    def __str__(self):
        return self.title


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
    order = models.PositiveIntegerField(verbose_name="Порядок")

    # Нові поля: День тижня та Час
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="День тижня")
    departure_time = models.TimeField(verbose_name="Час відправлення")

    class Meta:
        verbose_name = "Зупинка з розкладом"
        verbose_name_plural = "Зупинки з розкладом"
        ordering = ['day_of_week', 'departure_time']  # Сортування за часом

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.departure_time} - {self.city.name}"