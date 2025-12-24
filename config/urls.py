from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# 1. Імпортуйте ваші класи Sitemap
from django.contrib.sitemaps.views import sitemap
from trips.sitemaps import StaticViewSitemap, RouteSitemap
from city.sitemaps import CitySitemap  # Додайте цей імпорт

# 2. Визначте повний словник sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'routes': RouteSitemap,
    'cities': CitySitemap,  # Додаємо міста сюди
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ukrbus.urls')),
    path('accounts/', include('accounts.urls')),
    path('route/', include('trips.urls')),
    path('booking/', include('booking.urls')),
    path('news/', include('news.urls')),
    path('citys/', include('city.urls')),

    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)