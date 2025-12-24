from .models import Route


def popular_directions(request):
    # Отримуємо всі активні маршрути з попереднім завантаженням зупинок та міст для швидкості
    routes = Route.objects.filter(is_active=True).prefetch_related('stops__city')[:10]

    dynamic_directions = []

    for route in routes:
        # Використовуємо метод order_by('order'), щоб точно знати, де початок і кінець
        all_stops = route.stops.all().order_by('order')
        if all_stops.exists():
            start_stop = all_stops.first()
            end_stop = all_stops.last()

            if start_stop.city and end_stop.city:
                dynamic_directions.append({
                    'start_name': start_stop.city.name,
                    'end_name': end_stop.city.name,
                })

    return {
        'popular_directions_list': dynamic_directions
    }