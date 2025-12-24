from .models import Route
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'monthly'
    def items(self):
        return ['home']
    def location(self, item):
        return reverse(item)
class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'monthly'

    def items(self):
        # Залиш тільки ті назви, які є у твоїх urls.py
        return ['home']

    def location(self, item):
        return reverse(item)





class RouteSitemap(Sitemap):
    priority = 0.7
    changefreq = 'daily'

    def items(self):
        # Отримуємо маршрути, у яких 2 або більше зупинок
        return Route.objects.filter(is_active=True).prefetch_related('stops__city')

    def location(self, obj):
        # Цей метод за замовчуванням повертає одне посилання.
        # Але ми використаємо хитрість: повернемо головну пару,
        # а для інших комбінацій краще створити окрему логіку.
        stops = obj.stops.all().order_by('order')
        if stops.count() >= 2:
            return f"/booking/?start_city={stops.first().city.name}&end_city={stops.last().city.name}"
        return "/booking/"

    # Щоб проіндексувати ВСІ зупинки, краще перевизначити логіку:
    def get_urls(self, site=None, **kwargs):
        urls = []
        for route in self.items():
            stops = list(route.stops.all().order_by('order'))
            # Генеруємо всі можливі пари міст (зберігаючи черговість)
            for i in range(len(stops)):
                for j in range(i + 1, len(stops)):
                    start = stops[i].city.name
                    end = stops[j].city.name

                    url_info = {
                        'item': route,
                        'location': f"https://{site.domain}/booking/?start_city={start}&end_city={end}",
                        'lastmod': None,  # Можна додати дату оновлення маршруту
                        'changefreq': self.changefreq,
                        'priority': self.priority
                    }
                    urls.append(url_info)
        return urls

