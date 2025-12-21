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
        fields = ['title', 'is_active', 'boost_days']

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
    extra=0, # Встановлюємо 0, щоб порожні рядки не з'являлися самі собою
    can_delete=True
)