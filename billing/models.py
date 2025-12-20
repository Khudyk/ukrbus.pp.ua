from django.db import models
from django.conf import settings

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Поповнення'),
        ('withdrawal', 'Списання'),
        ('refund', 'Повернення'),
    ]

    # Зв'язок напряму з User, щоб бути гнучкими
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tx_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.amount} ({self.tx_type})"
class TopPlan(models.Model):
    days = models.PositiveIntegerField(unique=True, verbose_name="Кількість днів")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна (грн)")
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    class Meta:
        verbose_name = "Тариф ТОП"
        verbose_name_plural = "Тарифи ТОП"
        ordering = ['days']

    def __str__(self):
        return f"{self.days} днів — {self.price} грн"