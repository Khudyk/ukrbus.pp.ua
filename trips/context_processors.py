from django.utils import timezone
from trips.models import Route

def popular_directions(request):
    # Отримуємо поточний момент (дата + час)
    full_now = timezone.now()
    # Отримуємо тільки сьогоднішню дату для порівняння з DateField
    today = full_now.date()

    # 1. Вибираємо ТОП-маршрути
    # Використовуємо today, якщо top_until - це DateField
    top_routes = Route.objects.filter(
        is_active=True,
        top_until__gt=today
    ).order_by('?')[:7]

    # 2. Якщо ТОПів мало, добираємо звичайні
    count = top_routes.count()
    if count < 6:
        additional = Route.objects.filter(is_active=True).exclude(
            id__in=top_routes.values_list('id', flat=True)
        ).order_by('?')[:6 - count]
        popular_list = list(top_routes) + list(additional)
    else:
        popular_list = top_routes

    prepared_directions = []
    for route in popular_list:
        first_stop = route.stops.order_by('order').first()
        last_stop = route.stops.order_by('order').last()

        if first_stop and last_stop:
            # ТУТ ВИПРАВЛЕННЯ: порівнюємо top_until з today
            is_boosted = False
            if route.top_until:
                is_boosted = route.top_until > today

            prepared_directions.append({
                'start_city': first_stop.city.name,
                'end_city': last_stop.city.name,
                'min_price': route.min_trip_price,
                'is_boosted': is_boosted,
                'route_id': route.id,
            })

    return {
        'popular_directions_list': prepared_directions
    }