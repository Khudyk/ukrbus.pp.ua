from django.contrib.auth import views as auth_views
from django.urls import path

from .views import PassengerSignUpView, CarrierSignUpView ,ProfileView

urlpatterns = [
    # Реєстрація (наші кастомні View)
    path('signup/passenger/', PassengerSignUpView.as_view(), name='passenger_signup'),
    path('signup/carrier/', CarrierSignUpView.as_view(), name='carrier_signup'),

    # Авторизація (використовуємо вбудовані класи Django)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Відновлення пароля (опціонально, але корисно)
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('profile/', ProfileView, name='profile'),

]
