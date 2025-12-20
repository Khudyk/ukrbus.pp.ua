from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    # Порожні поля, які заповнюються в __init__
    departure_point = forms.ChoiceField(
        label="Місце посадки",
        widget=forms.Select(attrs={'class': 'form-control glass-input'})
    )
    arrival_point = forms.ChoiceField(
        label="Місце висадки",
        widget=forms.Select(attrs={'class': 'form-control glass-input'})
    )

    class Meta:
        model = Booking
        fields = ['trip_date', 'departure_point', 'arrival_point', 'seats_count', 'contact_phone']
        widgets = {
            'trip_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control glass-input'}),
            'seats_count': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': 1}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': '+380...'}),
        }

    def __init__(self, *args, **kwargs):
        # Отримуємо маршрут з аргументів
        route = kwargs.pop('route', None)
        super().__init__(*args, **kwargs)

        # Створюємо початковий варіант "Оберіть зупинку"
        stop_choices = [('', 'Оберіть зупинку...')]

        if route:
            # Додаємо міста з маршруту до списку вибору
            stops = route.stops.all().order_by('order')
            for stop in stops:
                label = f"{stop.city} ({stop.departure_time.strftime('%H:%M')})"
                stop_choices.append((stop.city, label))

        # Призначаємо вибір полям
        self.fields['departure_point'].choices = stop_choices
        self.fields['arrival_point'].choices = stop_choices

    def clean(self):
        cleaned_data = super().clean()
        departure = cleaned_data.get("departure_point")
        arrival = cleaned_data.get("arrival_point")

        # Перевірка, чи не обрав пасажир однакові міста
        if departure and arrival and departure == arrival:
            raise forms.ValidationError("Місце посадки та висадки не можуть збігатися.")

        return cleaned_data