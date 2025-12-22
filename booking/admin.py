# booking/admin.py
from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'route', 'passenger', 'departure_point', 'arrival_point', 'trip_date', 'status','total_price')
    list_filter = ('status', 'trip_date', 'route')
    search_fields = ('passenger__username', 'contact_phone', 'departure_point', 'arrival_point')

    # Якщо хочете, щоб перевізник бачив тільки свої замовлення:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(route__carrier=request.user)