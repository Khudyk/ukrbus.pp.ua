import io
import os
from django.conf import settings
from django.template.loader import get_template
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xhtml2pdf import pisa


from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Case, When, Value, IntegerField, F, OuterRef, Subquery, Exists
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView
from django.utils import timezone
from django.contrib import messages
from booking.forms import BookingForm
from booking.models import Booking
from trips.models import Route, RouteStop, City


# --- СПИСОК МАРШРУТІВ (ДЛЯ ВСІХ) ---
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
        queryset = Route.objects.filter(is_active=True).select_related('carrier').prefetch_related('stops__city')

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

        queryset = queryset.annotate(
            is_active_top=Case(
                When(Q(top_until__isnull=False) & Q(top_until__gt=now), then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).distinct().order_by('-is_active_top', '-top_until', '-id')

        return queryset


# --- СТВОРЕННЯ БРОНЮВАННЯ (ДЛЯ ПАСАЖИРА) ---
class MakeBookingView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('passenger-bookings')  # Змінено на список квитків

    def get_initial(self):
        initial = super().get_initial()
        date_from_url = self.request.GET.get('date')
        start_city = self.request.GET.get('start_city')
        end_city = self.request.GET.get('end_city')

        if date_from_url: initial['trip_date'] = date_from_url
        if start_city: initial['departure_point'] = start_city
        if end_city: initial['arrival_point'] = end_city
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['route'] = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['route'] = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        return context

    def form_valid(self, form):
        route = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        departure_city_name = form.cleaned_data.get('departure_point')
        arrival_city_name = form.cleaned_data.get('arrival_point')
        trip_date = form.cleaned_data.get('trip_date')

        # 1. Отримуємо зупинки для цього маршруту
        try:
            dep_stop = route.stops.get(city__name__icontains=departure_city_name)
            arr_stop = route.stops.get(city__name__icontains=arrival_city_name)

            # 2. ПЕРЕВІРКА: чи не йде висадка раніше посадки
            if dep_stop.order >= arr_stop.order:
                form.add_error('arrival_point', "Помилка: зупинка висадки повинна бути після зупинки посадки.")
                return self.form_invalid(form)

        except RouteStop.DoesNotExist:
            form.add_error('departure_point', "Вибрані міста не знайдені в цьому маршруті.")
            return self.form_invalid(form)

        # 3. Перевірка дати (як була раніше)
        if trip_date < timezone.now().date():
            form.add_error('trip_date', "Дата виїзду не може бути в минулому.")
            return self.form_invalid(form)

        # Збереження
        form.instance.passenger = self.request.user
        form.instance.route = route
        messages.success(self.request, "Бронювання успішно створено!")
        return super().form_valid(form)


# --- ПАНЕЛЬ КЕРУВАННЯ ПЕРЕВІЗНИКА ---
class CarrierBookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking/carrier_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        queryset = Booking.objects.filter(
            route__carrier=self.request.user
        ).select_related('passenger', 'passenger__passenger_profile', 'route').order_by('-created_at')

        # Фільтрація (search, status, route, dates)
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(passenger__username__icontains=search_query) |
                Q(passenger__passenger_profile__phone__icontains=search_query) |
                Q(departure_point__icontains=search_query) |
                Q(arrival_point__icontains=search_query)
            )

        status = self.request.GET.get('status')
        if status: queryset = queryset.filter(status=status)

        route_id = self.request.GET.get('route')
        if route_id: queryset = queryset.filter(route_id=route_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_routes'] = Route.objects.filter(carrier=self.request.user)
        context['status_choices'] = Booking.STATUS_CHOICES
        stats = self.get_queryset().aggregate(total_money=Sum('total_price'), total_seats=Sum('seats_count'))
        context['total_money'] = stats['total_money'] or 0
        context['total_seats'] = stats['total_seats'] or 0
        return context

    def post(self, request, *args, **kwargs):
        booking_id = request.POST.get('booking_id')
        new_status = request.POST.get('status')
        booking = get_object_or_404(Booking, id=booking_id, route__carrier=request.user)
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f"Статус замовлення №{booking.id} змінено.")
        return redirect(request.META.get('HTTP_REFERER', 'carrier-bookings'))


# --- МОЇ КВИТКИ (ДЛЯ ПАСАЖИРА) ---


class PassengerBookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking/passenger_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(passenger=self.request.user).select_related(
            'route', 'route__carrier'
        ).order_by('-trip_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ЦЕЙ РЯДОК ОБОВ'ЯЗКОВИЙ:
        context['today_date'] = timezone.now().date()
        return context

# --- СКАСУВАННЯ (ДЛЯ ПАСАЖИРА) ---
class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        # Шукаємо бронювання пасажира
        booking = get_object_or_404(Booking, id=booking_id, passenger=request.user)

        # Отримуємо сьогоднішню дату
        today = timezone.now().date()

        # ПЕРЕВІРКА: чи не минула дата виїзду
        if booking.trip_date < today:
            messages.error(request, "Неможливо скасувати поїздку, дата якої вже минула.")
            return redirect('passenger-bookings')

        # Якщо дата актуальна, скасовуємо
        if booking.status != 'cancelled':
            booking.status = 'cancelled'
            booking.save()
            messages.warning(request, "Ваше бронювання успішно скасовано.")
        else:
            messages.info(request, "Це бронювання вже було скасовано.")

        return redirect('passenger-bookings')


class PassengerManifestView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking/passenger_manifest.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        date_str = self.request.GET.get('date')
        route_id = self.request.GET.get('route')

        if not date_str:
            return Booking.objects.none()

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Базовий запит з усіма зв'язками
            queryset = Booking.objects.filter(
                trip_date=target_date,
                route__carrier=self.request.user
            ).exclude(status='cancelled').select_related(
                'passenger', 'route', 'passenger__passenger_profile'
            )

            # Фільтр по конкретному маршруту
            if route_id and route_id.strip():
                queryset = queryset.filter(route_id=int(route_id))

            # --- ЛОГІКА СОРТУВАННЯ ЗА МІСЦЕМ ПОСАДКИ ---
            # Шукаємо порядковий номер (order) для зупинки, назва якої збігається з містом посадки
            dep_order_subquery = RouteStop.objects.filter(
                route=OuterRef('route'),
                city__name__icontains=OuterRef('departure_point')
            ).values('order')[:1]

            return queryset.annotate(
                dep_order=Subquery(dep_order_subquery)
            ).order_by('route__id', 'dep_order', 'departure_point')
            # Сортуємо: спочатку по маршруту, потім по черзі зупинок, потім за назвою (якщо order однаковий)

        except (ValueError, TypeError):
            return Booking.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_routes'] = Route.objects.filter(carrier=self.request.user)
        context['selected_date'] = self.request.GET.get('date', '')

        qs = self.get_queryset()
        grouped = {}
        total_seats_sum = 0
        total_bookings_sum = 0
        total_money_sum = 0

        for b in qs:
            if b.route not in grouped:
                grouped[b.route] = {
                    'list': [],
                    'total_seats': 0,
                    'total_bookings': 0  # Кількість замовлень для кожного маршруту окремо
                }

            grouped[b.route]['list'].append(b)
            # Сумуємо кількість місць
            grouped[b.route]['total_seats'] += b.seats_count
            # Рахуємо кількість бронювань
            grouped[b.route]['total_bookings'] += 1

            # Загальна статистика для всієї сторінки
            total_seats_sum += b.seats_count
            total_bookings_sum += 1
            total_money_sum += b.total_price

        context['grouped_manifest'] = grouped
        context['total_seats'] = total_seats_sum
        context['total_bookings'] = total_bookings_sum
        context['total_money'] = total_money_sum
        return context


class ExportPassengerPDFView(LoginRequiredMixin, View):
    def get(self, request, grouped=None, target_date=None, *args, **kwargs):
        # ... (ваш код отримання дати та queryset) ...

        # --- ОСЬ ТУТ ВСТАВЛЯЄМО РЕЄСТРАЦІЮ ШРИФТУ ---
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')

        # Перевіряємо, чи файл фізично існує, щоб не було нової помилки
        if not os.path.exists(font_path):
            return HttpResponse(f"Шрифт не знайдено за шляхом: {font_path}", status=500)

        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        # --------------------------------------------

        context = {
            'grouped_manifest': grouped,
            'selected_date': target_date,
            # font_path у контексті більше не потрібен, якщо ми зареєстрували його тут
        }

        template = get_template('booking/passenger_manifest_pdf.html')
        html = template.render(context)

        result = io.BytesIO()
        # Створюємо PDF
        pdf = pisa.pisaDocument(
            io.BytesIO(html.encode("UTF-8")),
            result,
            encoding='UTF-8'
        )
        # ... (решта коду з HttpResponse)