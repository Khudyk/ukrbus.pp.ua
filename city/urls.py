from django.urls import path
from . import views

app_name = 'city'

urlpatterns = [
    path('list/', views.city_list_view, name='city_list'),
    path('autocomplete/', views.city_autocomplete, name='city_autocomplete'),

    # Змінюємо <int:city_id> на <slug:slug>
    path('<slug:slug>/', views.city_detail_view, name='city_detail'),
]