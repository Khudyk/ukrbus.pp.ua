from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView, CreateView

from billing.models import TopPlan
from billing.services import BillingService
from .forms import RouteForm, RouteStopFormSet
from .models import Route, RouteStop


class RouteBaseView(LoginRequiredMixin):
    model = Route
    form_class = RouteForm
    template_name = 'trips/route_form.html'
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        if self.request.POST:
            context['stops'] = RouteStopFormSet(self.request.POST, instance=self.object, prefix='stops')
        else:
            context['stops'] = RouteStopFormSet(instance=self.object, prefix='stops')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        stops = context['stops']

        if form.is_valid() and stops.is_valid():
            try:
                with transaction.atomic():
                    # 1. Зберігаємо маршрут та логіку ТОП (як було)
                    self.object = form.save()

                    # 2. ПРЯМЕ ОНОВЛЕННЯ ПОРЯДКУ З POST-ДАНИХ
                    # Ми просто беремо все, що ви щойно прислали в принті
                    total_forms = int(self.request.POST.get('stops-TOTAL_FORMS', 0))

                    for i in range(total_forms):
                        stop_id = self.request.POST.get(f'stops-{i}-id')
                        new_order = self.request.POST.get(f'stops-{i}-order')
                        is_deleted = self.request.POST.get(f'stops-{i}-DELETE')

                        if stop_id and new_order:
                            if is_deleted == 'on':  # Якщо стоїть галочка видалення
                                RouteStop.objects.filter(id=stop_id).delete()
                                print(f"DEBUG: Видалено ID {stop_id}")
                            else:
                                # ОНОВЛЮЄМО ПРЯМО В БАЗІ
                                RouteStop.objects.filter(id=stop_id).update(order=int(new_order))
                                print(f"DEBUG: ID {stop_id} отримав ORDER {new_order}")

                    # 3. Зберігаємо нові зупинки (якщо вони були додані через "Додати місто")
                    # Нові зупинки не мають ID в POST, тому їх збереже стандартний метод
                    stops.instance = self.object
                    stops.save()

                messages.success(self.request, "Порядок зупинок успішно оновлено!")
                return redirect(self.success_url)
            except Exception as e:
                print(f"ПОМИЛКА: {e}")
                messages.error(self.request, f"Помилка при збереженні: {e}")
                return self.form_invalid(form)
        return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        stops = context['stops']

        # Виводимо загальне повідомлення про помилку
        messages.error(self.request, "Не вдалося зберегти. Перевірте правильність заповнення полів.")

        # Логуємо помилки в консоль сервера для вас
        print(f"DEBUG: Помилки форми: {form.errors}")
        print(f"DEBUG: Помилки зупинок: {stops.errors}")
        return self.render_to_response(self.get_context_data(form=form))


class RouteCreateView(RouteBaseView, CreateView): pass


class RouteUpdateView(RouteBaseView, UpdateView): pass
