from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required

from .forms import PassengerRegistrationForm, CarrierRegistrationForm
from trips.models import Route
from booking.models import Booking  # Імпортуємо бронювання

User = get_user_model()


# --- Реєстрація (залишаємо як є) ---

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


# --- Профіль з виводом бронювань ---

@login_required
def ProfileView(request):
    if request.user.is_carrier:
        # Для перевізника: його маршрути + замовлення від пасажирів на ці маршрути
        routes = Route.objects.filter(carrier=request.user)
        # Отримуємо всі замовлення, де маршрут належить цьому перевізнику
        incoming_bookings = Booking.objects.filter(route__carrier=request.user).order_by('-trip_date')

        return render(request, 'accounts/profile_carrier.html', {
            'routes': routes,
            'incoming_bookings': incoming_bookings
        })
    else:
        # Для пасажира: тільки його замовлення
        my_bookings = Booking.objects.filter(passenger=request.user).order_by('-trip_date')

        return render(request, 'accounts/profile_passenger.html', {
            'bookings': my_bookings
        })


@login_required
def check_balance(request):
    # Отримуємо профіль перевізника поточного користувача
    profile = request.user.carrier_profile
    current_balance = profile.balance

    if current_balance > 0:
        return f"Ваш баланс: {current_balance} грн"
    else:
        return "На рахунку немає коштів"