# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(
        max_length=255,  # Збільшуємо ліміт
        unique=True,
        help_text="Будь-яка комбінація символів",
        validators=[],  # Прибираємо стандартні валідатори символів
    )
    """Кастомна модель користувача з прапорцями ролей"""
    is_passenger = models.BooleanField(default=False, verbose_name="Пасажир")
    is_carrier = models.BooleanField(default=False, verbose_name="Перевізник")

class PassengerProfile(models.Model):
    """Профіль з додатковими даними для пасажира"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    def __str__(self):
        return f"Пасажир: {self.user.username}"

class CarrierProfile(models.Model):
    """Профіль з додатковими даними для перевізника"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrier_profile')
    company_name = models.CharField(max_length=255, verbose_name="Назва компанії")
    contact_person = models.CharField(max_length=255, verbose_name="Контактна особа")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    telegram_bot = models.CharField(max_length=255, blank=True, null=True, verbose_name="Telegram Bot")

    def __str__(self):
        return self.company_name