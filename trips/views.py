from django.views.generic import ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField, ExpressionWrapper

from .forms import RouteForm, RouteStopFormSet
from .models import Route, RouteStop


# ==========================================================
# 1. СПИСОК МАРШРУТІВ (ВИПРАВЛЕНЕ СОРТУВАННЯ)
# ==========================================================
class RouteListView(ListView):
    model = Route
    template_name = 'trips/route_list.html'
    context_object_name = 'routes'

    def get_queryset(self):
        now = timezone.now()
        # annotate створює віртуальне поле, яке ми використовуємо для сортування
        return Route.objects.filter(is_active=True).annotate(
            is_active_top=Case(
                When(top_until__gt=now, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        ).order_by(
            '-is_active_top',  # ПЕРШИМИ йдуть ті, де ТОП діє прямо зараз (True > False)
            '-top_until',  # Далі — за терміном дії (довші ТОПи вище)
            '-id'  # Всі інші — за новизною
        )


# ==========================================================
# 2. БАЗОВИЙ КЛАС ДЛЯ ФОРМ
# ==========================================================
class RouteBaseView(LoginRequiredMixin):
    model = Route
    form_class = RouteForm
    template_name = 'trips/route_form.html'
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Міста для datalist - суто алфавітний порядок
        context['cities_list'] = RouteStop.objects.values_list(
            'city__name', flat=True
        ).distinct().order_by('city__name')

        if self.request.POST:
            context['stops'] = RouteStopFormSet(self.request.POST, instance=self.object)
        else:
            context['stops'] = RouteStopFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        stops = context['stops']

        if form.is_valid() and stops.is_valid():
            if not self.object or not self.object.pk:
                form.instance.carrier = self.request.user
                # Бонус на 1 добу при створенні
                form.instance.top_until = timezone.now() + timezone.timedelta(days=1)

            self.object = form.save()
            stops.instance = self.object
            stops.save()
            return redirect(self.success_url)

        return self.render_to_response(self.get_context_data(form=form))


class RouteCreateView(RouteBaseView, CreateView):
    pass


class RouteUpdateView(RouteBaseView, UpdateView):
    pass


# ==========================================================
# 3. КНОПКА ПІДНЯТТЯ
# ==========================================================
@login_required
def boost_route(request, pk):
    route = get_object_or_404(Route, pk=pk, carrier=request.user)
    now = timezone.now()

    # Визначаємо точку старту для нарахування +7 днів
    if route.top_until and route.top_until > now:
        start_point = route.top_until
    else:
        start_point = now

    route.top_until = start_point + timezone.timedelta(days=7)
    route.save()
    return redirect('profile')