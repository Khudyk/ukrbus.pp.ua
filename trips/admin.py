from django.contrib import admin
from .models import Route, RouteStop


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 2  # Кількість порожніх рядків для нових зупинок
    fields = ('order', 'day_of_week', 'departure_time', 'city')
    # Сортування в інтерфейсі адмінки
    ordering = ('day_of_week', 'departure_time', 'order')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    # Відображення списку маршрутів
    list_display = ('title', 'carrier', 'is_active', 'get_stops_count')
    list_filter = ('carrier', 'is_active')
    search_fields = ('title', 'carrier__username', 'carrier__email')

    # Підключаємо зупинки до сторінки маршруту
    inlines = [RouteStopInline]

    # Метод для відображення кількості зупинок у списку
    def get_stops_count(self, obj):
        return obj.stops.count()

    get_stops_count.short_description = "К-сть зупинок"

    # Щоб адмін бачив лише маршрути свого перевізника (якщо потрібно)
    def save_model(self, request, obj, form, change):
        if not obj.pk and not request.user.is_superuser:
            obj.carrier = request.user
        super().save_model(request, obj, form, change)


