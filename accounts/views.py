from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F, OuterRef, Subquery

from .forms import PassengerRegistrationForm, CarrierRegistrationForm
from trips.models import Route
from booking.models import Booking

User = get_user_model()

# --- Реєстрація ---

class PassengerSignUpView(CreateView):
    model = User
    form_class = PassengerRegistrationForm
    template_name = 'accounts/signup_passenger.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('profile')


class CarrierSignUpView(CreateView):
    model = User
    form_class = CarrierRegistrationForm
    template_name = 'accounts/signup_carrier.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('profile')


# --- Профіль ---

@login_required
def ProfileView(request):
    if request.user.is_carrier:
        routes = Route.objects.filter(carrier=request.user)
        incoming_bookings = Booking.objects.filter(route__carrier=request.user).order_by('-trip_date')
        return render(request, 'accounts/profile_carrier.html', {
            'routes': routes,
            'incoming_bookings': incoming_bookings
        })
    else:
        my_bookings = Booking.objects.filter(passenger=request.user).order_by('-trip_date')
        return render(request, 'accounts/profile_passenger.html', {
            'bookings': my_bookings
        })


# --- Статистика ---

@login_required
def statistics_view(request):
    user = request.user

    if user.is_carrier:
        # 1. Отримуємо дати з GET-запиту
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Базовий фільтр для замовлень цього перевізника
        booking_filter = Q(route__carrier=user)

        if start_date:
            booking_filter &= Q(trip_date__gte=start_date)
        if end_date:
            booking_filter &= Q(trip_date__lte=end_date)

        # 2. Розрахунок загальних показників по всіх маршрутах
        stats = Booking.objects.filter(booking_filter).aggregate(
            rev=Sum('total_price'),
            pax=Sum('seats_count')
        )

        total_revenue = stats['rev'] or 0
        total_pax = stats['pax'] or 0

        # 3. Аналітика по кожному маршруту окремо
        # Використовуємо Subquery для отримання суми грошей та місць для кожного маршруту
        routes_list = Route.objects.filter(carrier=user).annotate(
            # Сума грошей по маршруту
            route_revenue=Subquery(
                Booking.objects.filter(booking_filter, route=OuterRef('pk'))
                .values('route')
                .annotate(total_money=Sum('total_price'))
                .values('total_money')
            ),
            # Сума місць по маршруту
            route_pax=Subquery(
                Booking.objects.filter(booking_filter, route=OuterRef('pk'))
                .values('route')
                .annotate(total_seats=Sum('seats_count'))
                .values('total_seats')
            )
        ).order_by('-route_revenue') # Сортуємо: спочатку найприбутковіші

        context = {
            'total_revenue': total_revenue,
            'active_routes': Route.objects.filter(carrier=user, is_active=True).count(),
            'total_passengers': total_pax,
            'routes_list': routes_list,
            'start_date': start_date,
            'end_date': end_date,
        }
        return render(request, 'accounts/statistics_carrier.html', context)

    else:
        # Статистика для пасажира
        my_bookings = Booking.objects.filter(passenger=user)
        stats = my_bookings.aggregate(
            total_spent=Sum('total_price'),
            total_trips=Count('id')
        )

        context = {
            'trips_count': stats['total_trips'] or 0,
            'spent_money': stats['total_spent'] or 0,
            'bonuses': (stats['total_trips'] or 0) * 10,
        }
        return render(request, 'accounts/statistics_passenger.html', context)


# --- Баланс ---

@login_required
def check_balance(request):
    try:
        profile = request.user.carrier_profile
        return render(request, 'accounts/balance.html', {'balance': profile.balance})
    except:
        return redirect('profile')