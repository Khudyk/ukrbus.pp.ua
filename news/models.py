from django.db import models
from django.urls import reverse

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")

    content = models.TextField(verbose_name="Текст новини")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публікації")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:new_detail', kwargs={'pk': self.pk})