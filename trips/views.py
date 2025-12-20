from django.views.generic import UpdateView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RouteForm, RouteStopFormSet
from .models import Route, RouteStop


class RouteBaseView(LoginRequiredMixin):
    model = Route
    form_class = RouteForm
    template_name = 'trips/route_form.html'
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cities_list'] = RouteStop.objects.values_list('city', flat=True).distinct().order_by('city')

        if self.request.POST:
            post_data = self.request.POST.copy()

            # Отримуємо кількість форм
            total_forms_raw = post_data.get('stops-TOTAL_FORMS', '0')
            total_forms = int(total_forms_raw)

            valid_forms_count = 0
            new_post_data = post_data.copy()

            for i in range(total_forms):
                city_key = f'stops-{i}-city'
                order_key = f'stops-{i}-order'

                # Якщо місто порожнє — це пустий рядок, який додали випадково
                city_value = post_data.get(city_key, '').strip()

                if not city_value:
                    # Якщо ми знайдемо порожнє місто в кінці, ми просто зменшимо загальну кількість форм
                    # Django не буде валідувати те, що за межами TOTAL_FORMS
                    pass
                else:
                    # Якщо місто є, гарантуємо, що order заповнений
                    if not post_data.get(order_key):
                        new_post_data[order_key] = str(valid_forms_count)
                    valid_forms_count += 1

            # Оновлюємо TOTAL_FORMS, щоб Django бачив тільки заповнені рядки
            new_post_data['stops-TOTAL_FORMS'] = str(valid_forms_count)

            context['stops'] = RouteStopFormSet(new_post_data, instance=self.object)
        else:
            context['stops'] = RouteStopFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        # Отримуємо контекст, який уже містить оброблені POST-дані
        context = self.get_context_data()
        stops = context['stops']

        if form.is_valid() and stops.is_valid():
            if not self.object:
                form.instance.carrier = self.request.user

            self.object = form.save()
            stops.instance = self.object
            stops.save()
            return redirect(self.success_url)
        else:
            # Виводимо помилки в консоль для відладки, якщо щось не так
            print("Form errors:", form.errors)
            print("Stops errors:", stops.errors)
            return self.render_to_response(self.get_context_data(form=form))


class RouteCreateView(RouteBaseView, CreateView):
    pass


class RouteUpdateView(RouteBaseView, UpdateView):
    pass

