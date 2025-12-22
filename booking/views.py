from datetime import datetime  # ВИПРАВЛЕНО: тепер strptime буде доступний

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, OuterRef, Subquery, Exists
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from booking.forms import BookingForm
from booking.models import Booking
from trips.models import Route, RouteStop, City


from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField, Q, F, OuterRef, Subquery, Exists

class BookingRouteListView(ListView):
    model = Route
    template_name = 'booking/route_list.html'
    context_object_name = 'routes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_cities'] = City.objects.values_list('name', flat=True).order_by('name')
        return context

    def get_queryset(self):
        now = timezone.now()
        # 1. Початковий запит з оптимізацією
        queryset = Route.objects.filter(is_active=True).select_related('carrier').prefetch_related('stops__city')

        # 2. Отримання параметрів фільтрації
        start_city = self.request.GET.get('start_city')
        end_city = self.request.GET.get('end_city')
        date_str = self.request.GET.get('date')

        target_day = None
        if date_str:
            try:
                search_date = datetime.strptime(date_str, '%Y-%m-%d')
                target_day = search_date.weekday() + 1
            except ValueError:
                pass

        # 3. Складна фільтрація по містах (ваша логіка Subquery)
        if start_city and end_city:
            start_stop_filter = {'route': OuterRef('pk'), 'city__name__icontains': start_city}
            if target_day:
                start_stop_filter['day_of_week'] = target_day

            start_stop_subquery = RouteStop.objects.filter(**start_stop_filter)
            end_stop_subquery = RouteStop.objects.filter(route=OuterRef('pk'), city__name__icontains=end_city)

            queryset = queryset.filter(
                Exists(start_stop_subquery),
                Exists(end_stop_subquery)
            ).annotate(
                start_order=Subquery(start_stop_subquery.values('order')[:1]),
                end_order=Subquery(end_stop_subquery.values('order')[:1])
            ).filter(
                start_order__lt=F('end_order')
            )
        elif start_city:
            filter_params = {'stops__city__name__icontains': start_city}
            if target_day:
                filter_params['stops__day_of_week'] = target_day
            queryset = queryset.filter(**filter_params)
        elif target_day:
            queryset = queryset.filter(stops__day_of_week=target_day)

        # 4. ДОДАЄМО РОЗУМНЕ СОРТУВАННЯ ТУТ
        # Ми анотуємо кожен запис ознакою: 1 - активний ТОП, 0 - звичайний
        queryset = queryset.annotate(
            is_active_top=Case(
                When(Q(top_until__isnull=False) & Q(top_until__gt=now), then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).distinct().order_by(
            '-is_active_top', # Спочатку активні ТОПи (1), потім інші (0)
            '-top_until',     # Серед ТОПів — ті, що закінчаться пізніше
            '-id'             # Потім за ID (новіші)
        )

        return queryset




from django.utils import timezone
from django.contrib import messages

class MakeBookingView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('profile')

    def get_initial(self):
        initial = super().get_initial()
        # Отримуємо дані з URL
        date_from_url = self.request.GET.get('date')
        start_city = self.request.GET.get('start_city')
        end_city = self.request.GET.get('end_city')

        if date_from_url:
            initial['trip_date'] = date_from_url
        if start_city:
            initial['departure_point'] = start_city
        if end_city:
            initial['arrival_point'] = end_city
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Важливо: використовуйте ту ж назву параметра, що і в urls.py (route_id)
        kwargs['route'] = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return kwargs

    def get_context_data(self, **kwargs):
        # Отримуємо базовий контекст
        context = super().get_context_data(**kwargs)
        # Гарантуємо, що об'єкт 'route' потрапить у шаблон
        context['route'] = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return context

    def form_valid(self, form):
        route = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        trip_date = form.cleaned_data.get('trip_date')
        today = timezone.now().date()

        # 1. Перевірка: Дата не в минулому
        if trip_date < today:
            form.add_error('trip_date', "Дата виїзду не може бути в минулому.")
            return self.form_invalid(form)

        # 2. Перевірка: День тижня (Пн=1, Нд=7)
        target_day = trip_date.weekday() + 1
        day_exists = route.stops.filter(day_of_week=target_day).exists()

        if not day_exists:
            form.add_error('trip_date',
                f"За цим маршрутом немає рейсів у цей день ({trip_date.strftime('%d.%m.%Y')}).")
            return self.form_invalid(form)

        # Збереження
        form.instance.passenger = self.request.user
        form.instance.route = route
        return super().form_valid(form)