from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from .models import City


# Create your views here.


def city_autocomplete(request):
    term = request.GET.get('term', '')
    term = term.capitalize()
    cities = City.objects.select_related('country').filter(name__startswith=term).order_by('name')[:10]
    results = [{'id': city.id, 'text': f"{city.name}, {city.country.name if city.country else ''}"} for city in cities]
    return JsonResponse({'results': results})

def city_list_view(request):
    q = request.GET.get('q', '')
    city_name = q.split(',')[0].strip()

    city_list = City.objects.all() # <-- Початковий QuerySet

    if city_name:
        city_list = city_list.filter(name__icontains=city_name)

 #   city_list = city_list.order_by('name') # <-- Тут відбувається сортування

    city_list = City.objects.all().order_by(Lower('name'))

    paginator = Paginator(city_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': q,
        'debug_city_names': [city.name for city in page_obj.object_list],  # Це покаже порядок, що передається в шаблон
    }
    return render(request, 'city/city_list.html', context)

def city_detail_view(request, city_id):
    city = get_object_or_404(City, id=city_id)
    return render(request, 'city/city_detail.html', {'city': city})


