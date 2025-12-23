# booking/urls.py
from django.urls import path
from . import utils
from .views import (
    BookingRouteListView,
    MakeBookingView,
    CarrierBookingListView,
    PassengerBookingListView,
    CancelBookingView,
    PassengerManifestView,
    ExportPassengerPDFView,
)

urlpatterns = [
    path('', BookingRouteListView.as_view(), name='booking_route_list'),
    path('reserve/<int:route_id>/', MakeBookingView.as_view(), name='make_booking'),
    path('bookings/', CarrierBookingListView.as_view(), name='carrier-bookings'),
    path('my-bookings/', PassengerBookingListView.as_view(), name='passenger-bookings'),
    path('booking/<int:booking_id>/cancel/', CancelBookingView.as_view(), name='cancel-booking'),

    # Новий шлях для відомості (маніфесту)
    path('manifest/', PassengerManifestView.as_view(), name='passenger_manifest'),

    path('api/get-route-data/',utils.get_osm_road_distance, name='get_route_data'),


]
