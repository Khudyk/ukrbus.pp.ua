
from .models import Route, RouteStop , DistanceCache
from django.contrib import admin


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






@admin.register(DistanceCache)
class DistanceCacheAdmin(admin.ModelAdmin):
    # Відображення колонок у списку
    list_display = ('city_from', 'city_to', 'distance_km', 'created_at')

    # Фільтрація за містами
    list_filter = ('city_from', 'city_to')

    # Пошук за назвою міст
    search_fields = ('city_from__name', 'city_to__name')

    # Можливість швидкого редагування відстані прямо у списку
    list_editable = ('distance_km',)

    # Тільки для читання дата створення
    readonly_fields = ('created_at',)

    # Організація полів у формі редагування
    fieldsets = (
        (None, {
            'fields': ('city_from', 'city_to', 'distance_km')
        }),
        ('Метадані', {
            'fields': ('created_at',),
            'classes': ('collapse',)  # Приховати за замовчуванням
        }),
    )