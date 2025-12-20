from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PassengerProfile, CarrierProfile

class PassengerInline(admin.StackedInline):
    model = PassengerProfile
    can_delete = False

class CarrierInline(admin.StackedInline):
    model = CarrierProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_passenger', 'is_carrier', 'is_staff')
    inlines = (PassengerInline, CarrierInline)

admin.site.register(User, CustomUserAdmin)