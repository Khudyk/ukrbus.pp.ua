from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Transaction, TopPlan

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # Поля, які відображаються в списку
    list_display = ('timestamp_display', 'user', 'type_badge', 'amount_display', 'description')

    # Фільтри справа
    list_filter = ('tx_type', 'created_at')

    # Пошук за користувачем, описом та назвою компанії
    search_fields = ('user__username', 'description', 'user__carrier_profile__company_name')

    # Тільки для читання
    readonly_fields = ('created_at',)

    # --- ОБМЕЖЕННЯ ПРАВ (БЕЗПЕКА) ---
    def has_delete_permission(self, request, obj=None):
        """Забороняє видалення транзакцій усім, крім суперкористувачів"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Забороняє редагування транзакцій (фінансова цілісність)"""
        return request.user.is_superuser

    # --- ВІДОБРАЖЕННЯ ПОЛІВ ---
    def timestamp_display(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")
    timestamp_display.short_description = "Дата"

    def amount_display(self, obj):
        return f"{obj.amount} грн"
    amount_display.short_description = "Сума"

    def type_badge(self, obj):
        """Кольорове відображення типу транзакції"""
        colors = {
            'deposit': 'green',
            'withdrawal': 'red',
            'refund': 'blue',
        }
        color = colors.get(obj.tx_type, 'black')
        return format_html(
            '<b style="color: {};">{}</b>',
            color,
            obj.get_tx_type_display()
        )
    type_badge.short_description = "Тип"

    # Додаємо підсумок (Total) внизу списку
    def changelist_view(self, request, extra_context=None):
        result = Transaction.objects.aggregate(total=Sum('amount'))
        extra_context = extra_context or {}
        extra_context['total_balance'] = result['total'] or 0
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(TopPlan)
class TopPlanAdmin(admin.ModelAdmin):
    # Поля у таблиці
    list_display = ('days_display', 'price_display', 'is_active', 'is_popular_status')

    # Редагування активності прямо зі списку
    list_editable = ('is_active',)

    # Сортування за кількістю днів
    ordering = ('days',)

    def days_display(self, obj):
        return f"{obj.days} днів"
    days_display.short_description = "Термін"

    def price_display(self, obj):
        return f"{obj.price} грн"
    price_display.short_description = "Вартість"

    def is_popular_status(self, obj):
        """Візуальний індикатор популярного плану"""
        if getattr(obj, 'is_popular', False):
            return format_html('<span style="color: orange;">⭐ Популярний</span>')
        return "-"
    is_popular_status.short_description = "Статус"