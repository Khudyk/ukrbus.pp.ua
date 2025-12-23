import requests
import logging

from trips.models import DistanceCache

logger = logging.getLogger(__name__)

def get_osm_road_distance(city_a, city_b):
    """Отримує реальну відстань по дорогах через OSRM API з обробкою помилок"""
    if not (city_a.latitude and city_a.longitude and city_b.latitude and city_b.longitude):
        return None

    # OSRM використовує формат (longitude, latitude)
    coords = f"{city_a.longitude},{city_a.latitude};{city_b.longitude},{city_b.latitude}"
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=false"

    headers = {'User-Agent': 'UkrBusApp/1.0 (admin@ukrbus.pp.ua)'}

    try:
        response = requests.get(url, timeout=5, headers=headers)
        response.raise_for_status()  # Перевірка на помилки HTTP (4xx, 5xx)
        data = response.json()

        if data.get('code') == 'Ok':
            # Відстань у метрах -> переводимо в км
            distance_km = round(data['routes'][0]['distance'] / 1000, 1)
            return distance_km

    except requests.exceptions.RequestException as e:
        logger.error(f"OSRM API error: {e}")
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error parsing OSRM response: {e}")

    return None


def get_cached_distance(city_a, city_b):
    # Шукаємо в базі
    cached = DistanceCache.objects.filter(city_from=city_a, city_to=city_b).first()
    if cached:
        return cached.distance_km

    # Якщо немає — запитуємо OSRM
    distance = get_osm_road_distance(city_a, city_b)  # Ваша стара функція

    if distance:
        # Зберігаємо в базу для наступного разу
        DistanceCache.objects.create(city_from=city_a, city_to=city_b, distance_km=distance)

    return distance