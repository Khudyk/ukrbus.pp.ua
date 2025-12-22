from django import forms
from django.forms import inlineformset_factory
from .models import Route, RouteStop
from billing.models import TopPlan


class RouteForm(forms.ModelForm):
    """
    Основна форма маршруту.
    Включає логіку вибору тарифів просування (TopPlan) та налаштування цін.
    """
    # Додаткове поле, якого немає в моделі Route прямо, але ми використовуємо його для білінгу
    boost_days = forms.ChoiceField(
        required=False,
        label="Просування",
        widget=forms.Select(attrs={'class': 'form-select glass-input'})
    )

    class Meta:
        model = Route
        # Поля, які користувач заповнює в адмінці або на сайті
        fields = [
            'title', 'is_active', 'boost_days',
            'is_passenger', 'is_parcel',
            'min_trip_price', 'price_per_km',
            'min_parcel_price', 'price_per_kg'
        ]
        # Стилізація віджетів під Bootstrap/Glassmorphism дизайн
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control glass-input text-white', 'placeholder': 'Напр: Київ - Варшава'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'is_passenger': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'is_parcel': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            # step='0.01' дозволяє вводити копійки в числові поля
            'min_trip_price': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
            'price_per_km': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
            'min_parcel_price': forms.NumberInput(
                attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Динамічно завантажуємо доступні тарифні плани з бази даних billing.TopPlan
        """
        super().__init__(*args, **kwargs)
        # Отримуємо тільки активні плани просування
        plans = TopPlan.objects.filter(is_active=True).order_by('days')
        choices = [('0', '--- Без просування ---')]
        for p in plans:
            choices.append((str(p.days), f"{p.days} дн. — {p.price} грн"))

        # Оновлюємо список варіантів для поля вибору
        self.fields['boost_days'].choices = choices


# inlineformset_factory створює зв'язку "Маршрут -> Зупинки"
# Це дозволяє редагувати багато зупинок на одній сторінці з маршрутом
RouteStopFormSet = inlineformset_factory(
    Route,
    RouteStop,
    fields=('city', 'day_of_week', 'departure_time', 'order'),
    extra=0,
    can_delete=True,
    widgets={
        'city': forms.Select(attrs={'class': 'form-select glass-input text-white'}),
        'day_of_week': forms.Select(attrs={'class': 'form-select glass-input text-white'}),
        'departure_time': forms.TimeInput(attrs={'class': 'form-control glass-input text-white', 'type': 'time'}),
        # Використовуємо клас 'order-input' для зв'язку з вашим JS
        'order': forms.HiddenInput(attrs={'class': 'order-input'}),
    }
)