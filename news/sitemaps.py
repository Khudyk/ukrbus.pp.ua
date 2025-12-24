from django.contrib.sitemaps import Sitemap
from .models import News
from django.urls import reverse

class NewsSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return News.objects.all()

    def location(self, obj):
        return reverse('news:news_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.pub_date