# booking/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404
from booking.forms import BookingForm
from booking.models import Booking
from trips.models import Route, RouteStop


class BookingRouteListView(ListView):
    model = Route
    template_name = 'booking/route_list.html'
    context_object_name = 'routes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Звертаємося до поля name через подвійне підкреслення 'city__name'
        cities = RouteStop.objects.values_list('city__name', flat=True).distinct().order_by('city__name')

        context['available_cities'] = cities

        return context

    def get_queryset(self):
        queryset = Route.objects.filter(is_active=True).prefetch_related('stops').distinct()

        start_city = self.request.GET.get('start_city')
        end_city = self.request.GET.get('end_city')

        if start_city:
            # Додаємо __name перед __icontains
            queryset = queryset.filter(stops__city__name__icontains=start_city)

        if end_city:
            # Додаємо __name перед __icontains
            queryset = queryset.filter(stops__city__name__icontains=end_city)

        return queryset.distinct()


class MakeBookingView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['route'] = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return context

    def form_valid(self, form):
        form.instance.passenger = self.request.user
        form.instance.route = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return super().form_valid(form)