from django import forms
from django.forms import inlineformset_factory
from .models import Route, RouteStop
from billing.models import TopPlan

class RouteForm(forms.ModelForm):
    boost_days = forms.ChoiceField(
        required=False,
        label="Просування",
        widget=forms.Select(attrs={'class': 'form-select glass-input'})
    )

    class Meta:
        model = Route
        fields = [
            'title', 'is_active', 'boost_days',
            'is_passenger', 'is_parcel',
            'min_trip_price', 'price_per_km',
            'min_parcel_price', 'price_per_kg'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control glass-input text-white'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'is_passenger': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'is_parcel': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'min_trip_price': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
            'price_per_km': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
            'min_parcel_price': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
            'price_per_kg': forms.NumberInput(attrs={'class': 'form-control glass-input text-white', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plans = TopPlan.objects.filter(is_active=True).order_by('days')
        choices = [('0', '--- Без просування ---')]
        for p in plans:
            choices.append((str(p.days), f"{p.days} дн. — {p.price} грн"))
        self.fields['boost_days'].choices = choices

RouteStopFormSet = inlineformset_factory(
    Route, RouteStop,
    fields=('city', 'day_of_week', 'departure_time', 'order'),
    extra=0,
    can_delete=True,
    widgets={
        'city': forms.Select(attrs={'class': 'form-select glass-input text-white'}),
        'day_of_week': forms.Select(attrs={'class': 'form-select glass-input text-white'}),
        'departure_time': forms.TimeInput(attrs={'class': 'form-control glass-input text-white', 'type': 'time'}),
        # Додаємо клас для легкого пошуку в JS та початкове значення
        'order': forms.HiddenInput(attrs={'class': 'order-input', 'value': '1'}),
    }
)