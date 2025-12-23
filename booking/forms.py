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


class MakeBookingForm(forms.ModelForm):
    # Явно перевизначаємо поля як CharField, щоб вони приймали текст міст
    departure_point = forms.CharField(widget=forms.HiddenInput())
    arrival_point = forms.CharField(widget=forms.HiddenInput())

    # Використовуємо системний віджет дати
    trip_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control bg-transparent border-0 text-white'
        }),
        label="Дата поїздки"
    )

    class Meta:
        model = Booking
        fields = ['trip_date', 'seats_count', 'departure_point', 'arrival_point']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Стилізація поля кількості місць
        self.fields['seats_count'].widget.attrs.update({
            'class': 'form-control glass-input',
            'min': '1'
        })

    def clean(self):
        cleaned_data = super().clean()
        trip_date = cleaned_data.get('trip_date')
        route = self.initial.get('route_obj')

        if trip_date and route:
            # 1. Перевірка на минулу дату
            if trip_date < date.today():
                raise forms.ValidationError("Не можна забронювати рейс на минулу дату.")

            # 2. Перевірка розкладу через RouteStop
            # Python: Mon=0, Sun=6. Ваша модель: Mon=1, Sun=7.
            target_day = trip_date.weekday() + 1

            # Шукаємо, чи є хоча б одна зупинка на цей день для цього маршруту
            exists = route.stops.filter(day_of_week=target_day).exists()

            if not exists:
                ua_days = {
                    1: 'понеділок', 2: 'вівторок', 3: 'середу',
                    4: 'четвер', 5: 'п’ятницю', 6: 'суботу', 7: 'неділю'
                }
                day_name = ua_days.get(target_day)
                raise forms.ValidationError(f"На жаль, за цим маршрутом рейси на {day_name} не заплановані.")

        return cleaned_data