# booking/urls.py
from django.urls import path
from .views import BookingRouteListView, MakeBookingView  # ,# MakeBookingView, PassengerBookingsView

urlpatterns = [
    # Повна адреса: /booking/ - список доступних для замовлення рейсів
    path('', BookingRouteListView.as_view(), name='booking_route_list'),

    # Повна адреса: /booking/reserve/5/ - оформлення квитка на конкретний рейс
    path('reserve/<int:route_id>/', MakeBookingView.as_view(), name='make_booking'),
    #
    # # Повна адреса: /booking/my-tickets/ - список квитків пасажира
    # path('my-tickets/', PassengerBookingsView.as_view(), name='my_bookings'),
]