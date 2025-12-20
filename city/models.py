

# Create your models here.
from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Країна")
    code = models.CharField(max_length=3, unique=True, verbose_name="Код країни (ISO)")
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Країна"
        verbose_name_plural = "Країни"

class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="Місто")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities', verbose_name="Країна")
    description = models.TextField(blank=True, verbose_name="Короткий опис міста")
    latitude = models.FloatField(null=True, blank=True, verbose_name="Широта")  # широта
    longitude = models.FloatField(null=True, blank=True, verbose_name="Довгота")  # довгота
    image = models.ImageField(upload_to='cities/', blank=True, null=True, verbose_name="Зображення міста")
    def __str__(self):
        return f"{self.name}, {self.country.code}"
    class Meta:
        verbose_name = "Місто"
        verbose_name_plural = "Міста"
        unique_together = ('name', 'country')