from django import forms
from django.forms import inlineformset_factory
from .models import Route, RouteStop

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['title', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Наприклад: Київ — Львів'}),
        }

RouteStopFormSet = inlineformset_factory(
    Route, RouteStop,
    fields=('city', 'day_of_week', 'departure_time', 'order'),
    extra=3,
    widgets={
        'city': forms.Select(attrs={'class': 'form-select glass-input'}),
        'day_of_week': forms.Select(attrs={'class': 'form-select glass-input'}),
        'departure_time': forms.TimeInput(attrs={'class': 'form-control glass-input', 'type': 'time'}),
        'order': forms.NumberInput(attrs={'class': 'form-control glass-input', 'style': 'width: 70px;'}),

    }
)