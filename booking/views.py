import os
from datetime import datetime
from accounts.utils import send_carrier_notification
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Case, Exists, F, IntegerField, OuterRef,
    Q, Subquery, Sum, Value, When
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from booking.forms import BookingForm, MakeBookingForm
from booking.models import Booking
from booking.utils import get_cached_distance
from trips.models import City, Route, RouteStop


class BookingRouteListView(ListView):
    model = Route
    template_name = 'booking/route_list.html'
    context_object_name = 'routes'

    def get_queryset(self):
        start_city = self.request.GET.get('start_city')
        end_city = self.request.GET.get('end_city')
        date_str = self.request.GET.get('date')

        if not start_city or not end_city:
            return Route.objects.none()

        now = timezone.now()

        # Функція-помічник для виконання пошуку
        def perform_search(day=None):
            queryset = Route.objects.filter(is_active=True).select_related('carrier').prefetch_related('stops__city')

            # Фільтри для підзапитів
            start_stop_filter = {'route': OuterRef('pk'), 'city__name__icontains': start_city}
            if day:
                start_stop_filter['day_of_week'] = day

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

            return queryset.annotate(
                is_active_top=Case(
                    When(Q(top_until__isnull=False) & Q(top_until__gt=now), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).distinct().order_by('-is_active_top', '-top_until', '-id')

        # --- КРОК 1: Пошук на точну дату ---
        target_day = None
        if date_str:
            try:
                search_date = datetime.strptime(date_str, '%Y-%m-%d')
                target_day = search_date.weekday() + 1
            except ValueError:
                pass

        final_queryset = perform_search(day=target_day)
        self.is_nearby_dates = False

        # --- КРОК 2: "М'який пошук", якщо на точну дату порожньо ---
        if target_day and not final_queryset.exists():
            final_queryset = perform_search(day=None)  # Шукаємо на будь-який день
            if final_queryset.exists():
                self.is_nearby_dates = True

        # --- РОЗРАХУНОК ВІДСТАНІ ТА ЦІНИ ---
        city_a = City.objects.filter(name__icontains=start_city).first()
        city_b = City.objects.filter(name__icontains=end_city).first()
        distance = get_cached_distance(city_a, city_b) if city_a and city_b else None

        routes_list = list(final_queryset)
        for route in routes_list:
            route.calculated_distance = distance
            # Логіка ціни (як у вас була)
            p_km = float(route.price_per_km or 0)
            m_trip = float(route.min_trip_price or 0)
            if distance and p_km > 0:
                route.final_price = max(float(distance) * p_km, m_trip)
            else:
                route.final_price = m_trip

        return routes_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_cities'] = City.objects.values_list('name', flat=True).distinct().order_by('name')
        # Передаємо прапор у шаблон
        context['is_nearby_dates'] = getattr(self, 'is_nearby_dates', False)
        return context

# --- СТВОРЕННЯ БРОНЮВАННЯ (ДЛЯ ПАСАЖИРА) ---
class MakeBookingView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = MakeBookingForm
    template_name = 'booking/make_booking.html'
    success_url = reverse_lazy('passenger-bookings')

    def get_initial(self):
        initial = super().get_initial()
        route = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        initial.update({
            'departure_point': self.request.GET.get('start_city'),
            'arrival_point': self.request.GET.get('end_city'),
            'trip_date': self.request.GET.get('date'),
            'route_obj': route,
        })
        return initial

    def get_calculated_data(self):
        route = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        start_city_name = self.request.GET.get('start_city') or self.request.POST.get('departure_point')
        end_city_name = self.request.GET.get('end_city') or self.request.POST.get('arrival_point')

        city_a = City.objects.filter(name__icontains=start_city_name).first() if start_city_name else None
        city_b = City.objects.filter(name__icontains=end_city_name).first() if end_city_name else None

        distance = get_cached_distance(city_a, city_b) if city_a and city_b else None
        final_price_per_ticket = float(route.min_trip_price)

        if distance and route.price_per_km:
            calculated_price = float(distance) * float(route.price_per_km)
            final_price_per_ticket = max(calculated_price, float(route.min_trip_price))

        return {
            'route': route,
            'distance': distance,
            'final_price': final_price_per_ticket
        }

    def get_context_data(self, **kwargs):
        # 1. Отримуємо базовий контекст
        context = super().get_context_data(**kwargs)

        # 2. Отримуємо розраховані дані (ВАЖЛИВО: зберігаємо в змінну)
        calc_data = self.get_calculated_data()

        # 3. ОНОВЛЮЄМО контекст цими даними (тепер {{ route }} буде доступний)
        context.update(calc_data)

        # 4. Логіка для календаря
        route = calc_data['route']
        available_days = list(route.stops.values_list('day_of_week', flat=True).distinct())
        js_days = [d if d != 7 else 0 for d in available_days]

        context['available_days_json'] = js_days
        return context

    def form_valid(self, form):
        # Використовуємо той самий метод для отримання ціни при збереженні
        data = self.get_calculated_data()

        booking = form.save(commit=False)
        booking.passenger = self.request.user
        booking.route = data['route']
        seats = form.cleaned_data.get('seats_count', 1)
        booking.total_price = data['final_price'] * seats
        booking.save()

        # Логіка Telegram сповіщення (залишається без змін)
        try:
            carrier_prof = booking.route.carrier.carrier_profile
            try:
                p_phone = booking.passenger.passenger_profile.phone
            except Exception:
                p_phone = form.cleaned_data.get('passenger_phone') or "не вказано"

            full_name = f"{booking.passenger.first_name} {booking.passenger.last_name}".strip() or booking.passenger.username

            text = (
                f"🆕 <b>Нове замовлення </b>\n\n"
                f"🚌 <b>Рейс:</b> {booking.route.title}\n"
                f"📍 <b>Маршрут:</b> {booking.departure_point} — {booking.arrival_point}\n"
                f"📅 <b>Дата:</b> {booking.trip_date}\n"
                f"👥 <b>Місць:</b> {booking.seats_count}\n"
                f"💰 <b>Сума:</b> {booking.total_price} грн\n\n"
                f"👤 <b>Пасажир:</b> {full_name}\n"
                f"📞 <b>Телефон:</b> <code>{p_phone}</code>\n"

            )
            send_carrier_notification(carrier_prof, text)
        except Exception as e:
            print(f"Помилка відправки сповіщення: {e}")

        messages.success(self.request, f"Бронювання на суму ₴{booking.total_price} успішно створено!")
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
        # If grouped/target_date provided use them (callable reuse), otherwise build from request
        if not grouped or not target_date:
            date_str = request.GET.get('date')
            route_id = request.GET.get('route')

            if not date_str:
                return HttpResponse("Missing 'date' parameter", status=400)

            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return HttpResponse("Invalid 'date' format, expected YYYY-MM-DD", status=400)

            # Build base queryset (mirrors PassengerManifestView)
            queryset = Booking.objects.filter(
                trip_date=target_date,
                route__carrier=request.user
            ).exclude(status='cancelled').select_related(
                'passenger', 'route', 'passenger__passenger_profile'
            )

            if route_id and route_id.strip():
                try:
                    queryset = queryset.filter(route_id=int(route_id))
                except ValueError:
                    return HttpResponse("Invalid 'route' parameter", status=400)

            dep_order_subquery = RouteStop.objects.filter(
                route=OuterRef('route'),
                city__name__icontains=OuterRef('departure_point')
            ).values('order')[:1]

            qs = queryset.annotate(
                dep_order=Subquery(dep_order_subquery)
            ).order_by('route__id', 'dep_order', 'departure_point')

            # Grouping (same structure as PassengerManifestView)
            grouped = {}
            for b in qs:
                if b.route not in grouped:
                    grouped[b.route] = {
                        'list': [],
                        'total_seats': 0,
                        'total_bookings': 0
                    }
                grouped[b.route]['list'].append(b)
                grouped[b.route]['total_seats'] += b.seats_count
                grouped[b.route]['total_bookings'] += 1

        # --- FONT registration (kept as earlier) ---
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
        if not os.path.exists(font_path):
            # Return useful error instead of raising to keep response predictable
            return HttpResponse(f"Font not found at: {font_path}", status=500)

        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        # --------------------------------------------

        context = {
            'grouped_manifest': grouped,
            'selected_date': target_date,
        }

        template = get_template('booking/passenger_manifest_pdf.html')
        html = template.render(context, request=request)

        # For now return rendered HTML so the view is complete and predictable.
        # If PDF generation is desired, replace this with PDF generator logic.
        return HttpResponse(html, content_type='text/html')


def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    # ... логіка збереження ...

    # Сповіщаємо перевізника
    carrier_prof = booking.route.carrier.carrier_profile
    text = (
        f"🆕 <b>Нове замовлення!</b>\n"
        f" Маршрут: {booking.route.title}\n"
        f"👤 Пасажир: {booking.passenger_name}\n"
        f"📞 Тел: {booking.passenger_phone}\n"
        f"💰 Баланс: {carrier_prof.balance} грн"
    )
    send_carrier_notification(carrier_prof, text)
