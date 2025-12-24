from django.db.models import Q
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import City

def city_autocomplete(request):
    term = request.GET.get('term', '').strip().lower()

    if not term:
        return JsonResponse({'results': []})

    all_cities = City.objects.all()

    # Фільтрація засобами Python (працює з кирилицею)
    filtered = [
        c for c in all_cities
        if term in c.name.lower()
    ][:10]

    results = [{'id': c.id, 'text': c.name} for c in filtered]
    return JsonResponse({'results': results})

def city_list_view(request):
    q = request.GET.get('q', '').strip().lower()
    # Отримуємо QuerySet (ще не список)
    city_qs = City.objects.select_related('country').all()

    if q:
        # ПЕРЕТВОРЮЄМО НА СПИСОК І ФІЛЬТРУЄМО ЧЕРЕЗ PYTHON
        # Це єдиний спосіб для SQLite обійти проблему кириличного регістру
        city_list = [
            c for c in city_qs
            if q in c.name.lower() or q in c.country.name.lower()
        ]
        # Сортуємо список за назвою міста
        city_list.sort(key=lambda x: x.name.lower())
    else:
        # Якщо пошуку немає, просто сортуємо QuerySet за допомогою БД (це вона вміє)
        city_list = city_qs.order_by('name')

    # Paginator в Django чудово працює і зі списками []
    paginator = Paginator(city_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'city/city_list.html', {
        'page_obj': page_obj,
        'search_query': q,
    })


def city_detail_view(request, slug):  # Аргумент має називатися точно 'slug'
    city = get_object_or_404(City, slug=slug)  # Шукаємо по полю slug

    # Решта твого коду...
    return render(request, 'city/city_detail.html', {'city': city})