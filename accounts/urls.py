from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .forms import CustomPasswordResetForm
from .views import PassengerSignUpView, CarrierSignUpView, ProfileView
from . import views

urlpatterns = [
    # Реєстрація та Профіль
    path('signup/passenger/', PassengerSignUpView.as_view(), name='passenger_signup'),
    path('signup/carrier/', CarrierSignUpView.as_view(), name='carrier_signup'),
    path('profile/', ProfileView, name='profile'),

    # Авторизація
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- ВІДНОВЛЕННЯ ПАРОЛЯ (ПОВНИЙ ЦИКЛ) ---

    # 1. Сторінка введення Email
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             form_class=CustomPasswordResetForm,
             success_url=reverse_lazy('password_reset_done')
         ),
         name='password_reset'),

    # 2. Лист надіслано
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    # 3. Введення нового пароля (посилання з пошти)
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ),
         name='password_reset_confirm'),

    # 4. Пароль успішно змінено
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    path('statistics/', views.statistics_view, name='statistics'),
]
