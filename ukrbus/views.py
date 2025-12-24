# views.py
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from accounts.models import CarrierProfile
from accounts.utils import send_carrier_notification
from city.models import City


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Додаємо список міст, щоб JavaScript у формі міг їх побачити
        context['available_cities'] = City.objects.values_list('name', flat=True).distinct().order_by('name')
        return context

