from django.contrib import admin

from city.models import City, Country


# Register your models here.
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    pass
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    pass