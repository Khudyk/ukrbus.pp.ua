
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ukrbus.urls')),  # Всі маршрути будуть починатися з /accounts/
    path('accounts/', include('accounts.urls')), # Всі маршрути будуть починатися з /accounts/

    path('route/', include('trips.urls')),
    path('booking/', include('booking.urls')),
    path('citys/', include('city.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)