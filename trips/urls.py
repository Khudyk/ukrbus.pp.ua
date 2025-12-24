from django.urls import path

from .views import RouteCreateView, RouteUpdateView



urlpatterns = [
    path('add/', RouteCreateView.as_view(), name='route_add'),
    path('<int:pk>/edit/', RouteUpdateView.as_view(), name='route_edit'),
]
