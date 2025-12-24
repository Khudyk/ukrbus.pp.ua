import random
from datetime import time
from django.contrib.auth import get_user_model
from trips.models import Route, RouteStop
from city.models import City

User = get_user_model()
try:
    carrier = User.objects.get(id=3)
    cities = list(City.objects.all())

    if len(cities) < 6:
        print("Помилка: Треба хоча б 6 міст у базі.")
    else:
        for i in range(10):
            # 1. Вибираємо випадкові міста (від 6 до 10)
            num = random.randint(6, min(len(cities), 10))
            sel_cities = random.sample(cities, num)

            # 2. Створюємо маршрут
            r = Route.objects.create(
                title=f"{sel_cities[0].name} — {sel_cities[-1].name}",
                carrier=carrier,
                is_active=True,
                min_trip_price=random.randint(500, 1000)
            )

            # 3. Створюємо зупинки (RouteStop)
            # Виберемо випадковий день для всього маршруту (наприклад, понеділок = 1)
            route_day = random.randint(1, 7)

            for idx, city in enumerate(sel_cities):
                RouteStop.objects.create(
                    route=r,
                    city=city,
                    order=idx + 1,
                    day_of_week=route_day,
                    # Час відправлення збільшується з кожною зупинкою
                    departure_time=time(hour=(8 + idx) % 24, minute=0)
                )
            print(f"Створено: {r.title} (Зупинок: {num})")
except User.DoesNotExist:
    print("Помилка: Користувач (перевізник) з ID=3 не знайдений!")