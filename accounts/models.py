from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        max_length=255,
        unique=True,
        help_text="Будь-яка комбінація символів",
    )
    is_passenger = models.BooleanField(default=False, verbose_name="Пасажир")
    is_carrier = models.BooleanField(default=False, verbose_name="Перевізник")


class PassengerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    def __str__(self):
        return f"Пасажир: {self.user.username}"


class CarrierProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrier_profile')
    company_name = models.CharField(max_length=255, verbose_name="Назва компанії")
    contact_person = models.CharField(max_length=255, verbose_name="Контактна особа")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    telegram_bot = models.CharField(max_length=255, blank=True, null=True, verbose_name="Telegram Bot")

    # НОВЕ ПОЛЕ: Баланс
    # Використовуємо DecimalField для грошей (ніколи не використовуйте FloatField для фінансів!)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Баланс (грн)"
    )

    def __str__(self):
        return f"{self.company_name} (Баланс: {self.balance} грн)"

    def has_sufficient_funds(self, amount):
        """Перевірка, чи достатньо грошей на балансі"""
        return self.balance >= amount