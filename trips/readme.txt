import random
from datetime import time
from django.contrib.auth import get_user_model
from trips.models import Route, RouteStop
from city.models import City
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

try:
    # Отримуємо перевізника
    carrier = User.objects.get(id=3)
    cities = list(City.objects.all())

    if len(cities) < 6:
        print("Помилка: Треба хоча б 6 міст у базі.")
    else:
        for i in range(10):
            # 1. Вибираємо випадкову кількість міст
            num = random.randint(6, min(len(cities), 10))
            sel_cities = random.sample(cities, num)

            # 2. Генеруємо ціни
            # Пасажирські ціни
            min_trip = random.randint(300, 600)      # Мінімалка за квиток
            price_km = random.uniform(1.5, 3.5)      # Ціна за 1 км (наприклад, 2.50 грн)

            # Ціни на посилки
            min_parcel = random.randint(50, 150)     # Мінімалка за посилку
            price_kg = random.uniform(5.0, 15.0)     # Ціна за 1 кг

            # Випадково робимо деякі маршрути "ТОП" (на 7 днів вперед)
            is_top = random.choice([True, False, False]) # 33% шанс бути в топі
            top_date = timezone.now() + timedelta(days=7) if is_top else None

            # 3. Створюємо маршрут з усіма полями
            r = Route.objects.create(
                title=f"{sel_cities[0].name} — {sel_cities[-1].name}",
                carrier=carrier,
                is_active=True,
                top_until=top_date,
                is_passenger=True,
                is_parcel=random.choice([True, True, False]), # Більшість возить посилки

                # Заповнюємо ціни
                min_trip_price=min_trip,
                price_per_km=round(price_km, 2),
                min_parcel_price=min_parcel,
                price_per_kg=round(price_kg, 2)
            )

            # 4. Створюємо зупинки (RouteStop)
            route_day = random.randint(1, 7)
            for idx, city in enumerate(sel_cities):
                RouteStop.objects.create(
                    route=r,
                    city=city,
                    order=idx + 1,
                    day_of_week=route_day,
                    # Час збільшується: 08:00, 09:00, 10:00...
                    departure_time=time(hour=(8 + idx) % 24, minute=0)
                )

            status = " [ТОП]" if is_top else ""
            print(f"Створено: {r.title}{status}. Ціна км: {r.price_per_km} грн. Зупинок: {num}")

except User.DoesNotExist:
    print("Помилка: Користувач (перевізник) з ID=3 не знайдений!")