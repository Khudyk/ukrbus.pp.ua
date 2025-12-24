from django import forms
from .models import Booking
from datetime import datetime

class BookingForm(forms.ModelForm):
    # Поля вибору зупинок
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
        # Видалили contact_phone з переліку полів
        fields = ['trip_date', 'departure_point', 'arrival_point', 'seats_count']
        widgets = {
            'trip_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control glass-input'}),
            'seats_count': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': 1, 'value': 1}),
        }

    def __init__(self, *args, **kwargs):
        route = kwargs.pop('route', None)
        super().__init__(*args, **kwargs)

        stop_choices = [('', 'Оберіть зупинку...')]

        if route:
            stops = route.stops.all().order_by('order')
            for stop in stops:
                label = f"{stop.city.name} ({stop.departure_time.strftime('%H:%M')})"
                # Використовуємо назву міста як значення (як у вашому другому циклі)
                stop_choices.append((stop.city.name, label))

        self.fields['departure_point'].choices = stop_choices
        self.fields['arrival_point'].choices = stop_choices

        # ЗАБОРОНА РЕДАГУВАННЯ:
        # Додаємо атрибут disabled через віджети
        self.fields['departure_point'].widget.attrs['disabled'] = 'disabled'
        self.fields['arrival_point'].widget.attrs['disabled'] = 'disabled'

        # Також можна встановити параметр disabled для самого поля (Django 1.9+)
        # Це автоматично ігнорує будь-які POST-зміни від користувача для безпеки
        self.fields['departure_point'].disabled = True
        self.fields['arrival_point'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        departure = cleaned_data.get("departure_point")
        arrival = cleaned_data.get("arrival_point")

        # 1. Перевірка на однакові міста
        if departure and arrival and departure == arrival:
            raise forms.ValidationError("Місце посадки та висадки не можуть збігатися.")

        # 2. Логічна перевірка черговості (опціонально)
        # Якщо потрібно переконатися, що зупинка висадки йде ПІСЛЯ зупинки посадки
        return cleaned_data


from django import forms
from datetime import date  # Імпортуємо тільки date для порівняння
from .models import Booking


from django import forms

class MakeBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['trip_date', 'seats_count', 'departure_point', 'arrival_point']
        widgets = {
            'trip_date': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Оберіть дату',
                'readonly': 'readonly' # Користувач не пише руками, а вибирає в календарі
            }),
            'seats_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
        }