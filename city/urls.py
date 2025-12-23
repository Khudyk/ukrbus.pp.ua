from django.urls import path
from . import views

app_name = 'city'  # ЦЕ ВАЖЛИВО

urlpatterns = [
    path('list/', views.city_list_view, name='city_list'),
    path('autocomplete/', views.city_autocomplete, name='city_autocomplete'),
    path('<int:city_id>/', views.city_detail_view, name='city_detail'),
]