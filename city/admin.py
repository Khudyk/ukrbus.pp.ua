from django.contrib import admin
from .models import City, Country


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    # Відображення колонок у списку
    list_display = ('name', 'country', 'slug')

    # Додає блок фільтрації справа
    list_filter = ('country',)

    # Додає поле пошуку (можна шукати за назвою міста або назвою країни)
    search_fields = ('name', 'country__name')

    # Автозаповнення слага (працює в реальному часі при написанні назви)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')