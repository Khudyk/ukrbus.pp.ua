import os
from datetime import datetime

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

        # 1. Якщо хоча б одне поле порожнє — повертаємо порожній результат
        if not start_city or not end_city:
            return Route.objects.none()

        now = timezone.now()
        # Базовий запит з оптимізацією (prefetch_related для міст)
        queryset = Route.objects.filter(is_active=True).select_related('carrier').prefetch_related('stops__city')

        # --- ЛОГІКА ДАТИ ---
        date_str = self.request.GET.get('date')
        target_day = None
        if date_str:
            try:
                search_date = datetime.strptime(date_str, '%Y-%m-%d')
                target_day = search_date.weekday() + 1
            except ValueError:
                pass

        # --- ФІЛЬТРАЦІЯ ЗА МІСТАМИ ТА НАПРЯМКОМ ---
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

        # --- СОРТУВАННЯ ТА TOP ---
        queryset = queryset.annotate(
            is_active_top=Case(
                When(Q(top_until__isnull=False) & Q(top_until__gt=now), then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).distinct().order_by('-is_active_top', '-top_until', '-id')

        # --- РОЗРАХУНОК ВІДСТАНІ ТА КЕШУВАННЯ ---
        city_a = City.objects.filter(name__icontains=start_city).first()
        city_b = City.objects.filter(name__icontains=end_city).first()
        distance = get_cached_distance(city_a, city_b) if city_a and city_b else None

        # Перетворення у список для додавання цін
        routes_list = list(queryset)
        for route in routes_list:
            route.calculated_distance = distance
            if distance and route.price_per_km:
                price = float(distance) * float(route.price_per_km)
                route.final_price = max(price, float(route.min_trip_price))
            else:
                route.final_price = route.min_trip_price

        return routes_list

    def get_context_data(self, **kwargs):
        # Отримуємо базовий контекст від Django
        context = super().get_context_data(**kwargs)

        # Додаємо список усіх міст для нашого нового автозаповнення
        # values_list('name', flat=True) витягує лише назви одним списком ['Київ', 'Львів'...]
        context['available_cities'] = City.objects.values_list('name', flat=True).distinct().order_by('name')

        # Повертаємо оновлений контекст у шаблон
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
            'route_obj': route,  # Передаємо сам об'єкт для валідації
        })
        return initial

    def get_calculated_data(self):
        route = get_object_or_404(Route, id=self.kwargs.get('route_id'))
        # Беремо дані або з GET (при завантаженні), або з POST (при збереженні)
        start_city_name = self.request.GET.get('start_city') or self.request.POST.get('departure_point')
        end_city_name = self.request.GET.get('end_city') or self.request.POST.get('arrival_point')

        city_a = City.objects.filter(name__icontains=start_city_name).first()
        city_b = City.objects.filter(name__icontains=end_city_name).first()

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
        context = super().get_context_data(**kwargs)
        context.update(self.get_calculated_data())
        return context

    def form_valid(self, form):
        data = self.get_calculated_data()

        # Використовуємо commit=False для безпечного наповнення об'єкта
        booking = form.save(commit=False)
        booking.passenger = self.request.user
        booking.route = data['route']

        # Розраховуємо фінальну суму
        seats = form.cleaned_data.get('seats_count', 1)
        booking.total_price = data['final_price'] * seats

        booking.save()

        messages.success(self.request, f"Бронювання на суму ₴{booking.total_price} успішно створено!")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Якщо не зберігає — виведе помилку в консоль"""
        print("DEBUG: Помилки валідації:", form.errors)
        return super().form_invalid(form)


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


