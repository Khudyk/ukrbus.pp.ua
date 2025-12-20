from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from . import views

from .views import *


from django.contrib.sitemaps import Sitemap



urlpatterns = [


    # --- Міста ---
    path('cities/', city_list_view, name='city_list'),
    path('cities/<int:city_id>/', city_detail_view, name='city_detail'),

]

