from django.db import transaction
from .models import Transaction


class BillingService:
    @staticmethod
    @transaction.atomic
    def process_payment(user, amount, description, tx_type='withdrawal'):
        """
        Універсальна функція для списання або нарахування коштів.
        """
        profile = user.carrier_profile

        if tx_type == 'withdrawal' and profile.balance < amount:
            return False, "Недостатньо коштів"

        # 1. Створюємо транзакцію
        Transaction.objects.create(
            user=user,
            amount=-amount if tx_type == 'withdrawal' else amount,
            tx_type=tx_type,
            description=description
        )

        # 2. Оновлюємо баланс у профілі
        if tx_type == 'withdrawal':
            profile.balance -= amount
        else:
            profile.balance += amount

        profile.save()
        return True, "Успішно"