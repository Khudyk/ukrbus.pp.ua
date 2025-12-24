from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode


class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    # Додаємо поле slug
    slug = models.SlugField(unique=True, max_length=255, blank=True, verbose_name="URL-адреса")
    #slug = models.SlugField(unique=False, max_length=255, blank=True, null=True, verbose_name="URL-адреса")

    content = models.TextField(verbose_name="Текст новини")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публікації")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # Автоматична генерація слага при збереженні
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.title))
        super().save(*args, **kwargs)

    # Оновлюємо посилання: тепер воно веде на slug, а не на pk
    def get_absolute_url(self):
        return reverse('news:news_detail', kwargs={'slug': self.slug})