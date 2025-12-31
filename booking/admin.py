from django.contrib import admin
from django.utils.html import format_html
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Відображення списку: додали колір для статусу та форматування ціни
    list_display = (
        'id', 'get_status_colored', 'route', 'passenger',
        'departure_point', 'arrival_point', 'trip_date', 'total_price_formatted'
    )

    # Фільтри справа
    list_filter = ('status', 'trip_date', 'route', 'created_at')

    # Пошук (виправили contact_phone на passenger__username)
    search_fields = ('passenger__username', 'departure_point', 'arrival_point', 'id')
 # Групування полів при редагуванні
    fieldsets = (
        ('Основна інформація', {
            'fields': ('passenger', 'route', 'status')
        }),
        ('Деталі поїздки', {
            'fields': ('trip_date', 'seats_count', 'departure_point', 'arrival_point')
        }),
        ('Фінанси', {
            'fields': ('total_price',),
            'classes': ('collapse',),  # Можна згорнути блок
        }),
    )

    # --- КАСТОМНІ МЕТОДИ ---

    @admin.display(description='Статус')
    def get_status_colored(self, obj):
        """Кольорове відображення статусів для зручності"""
        colors = {
            'pending': '#f39c12',  # Помаранчевий
            'confirmed': '#27ae60',  # Зелений
            'cancelled': '#e74c3c',  # Червоний
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    @admin.display(description='Вартість')
    def total_price_formatted(self, obj):
        """Форматування ціни з валютою"""
        return f"₴{obj.total_price}"

    # --- ПРАВА ДОСТУПУ ---

    def get_queryset(self, request):
        """Перевізник бачить тільки замовлення на свої маршрути"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(route__carrier=request.user)

    def has_change_permission(self, request, obj=None):
        """Перевізник може змінювати тільки свої замовлення"""
        if obj is not None and not request.user.is_superuser:
            return obj.route.carrier == request.user
        return super().has_change_permission(request, obj)