# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import PassengerProfile, CarrierProfile

User = get_user_model()

class PassengerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=True, label="Ім'я")
    email = forms.EmailField(required=True, label="Email")
    phone = forms.CharField(max_length=20, label="Телефон")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "email", "phone", "username")
        labels = {
            'username': "Логін",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_passenger = True
        if commit:
            user.save()
            PassengerProfile.objects.get_or_create(
                user=user,
                defaults={'phone': self.cleaned_data.get('phone')}
            )
        return user

class CarrierRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=255, label="Назва компанії")
    contact_person = forms.CharField(max_length=255, label="Контактна особа")
    phone = forms.CharField(max_length=20, label="Телефон")
    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        # Поле telegram_bot видалено звідси
        fields = ("username","company_name", "contact_person", "email", "phone")
        labels = {
            'username': "Логін для входу",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_carrier = True
        if commit:
            user.save()
            CarrierProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': self.cleaned_data.get('company_name'),
                    'contact_person': self.cleaned_data.get('contact_person'),
                    'phone': self.cleaned_data.get('phone'),
                    # Поле telegram_bot більше не передається при створенні
                }
            )
        return user