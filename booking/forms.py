from django import forms
from .models import Booking


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
        # Отримуємо маршрут з kwargs (передається з View)
        route = kwargs.pop('route', None)
        super().__init__(*args, **kwargs)

        # Початковий варіант вибору
        stop_choices = [('', 'Оберіть зупинку...')]

        if route:
            # Отримуємо всі зупинки для цього маршруту, відсортовані за черговістю
            stops = route.stops.all().order_by('order')
            for stop in stops:
                # Формуємо текст: Назва міста (Час)
                label = f"{stop.city.name} ({stop.departure_time.strftime('%H:%M')})"
                stop_choices.append((stop.city.name, label))

        # Оновлюємо списки вибору для полів
        self.fields['departure_point'].choices = stop_choices
        self.fields['arrival_point'].choices = stop_choices

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