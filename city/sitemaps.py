from city.models import City
 
from django.contrib.sitemaps import Sitemap
from django.urls import reverse



class CitySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        # Повертаємо всі міста, у яких заповнений slug
        return City.objects.exclude(slug__isnull=True).exclude(slug="")

    def location(self, obj):
        # 'city' — це app_name, 'city_detail' — назва path у urls.py
        return reverse('city:city_detail', kwargs={'slug': obj.slug})