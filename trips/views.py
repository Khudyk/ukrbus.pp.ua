from django.views.generic import ListView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Case, When, Value, BooleanField
from django.contrib import messages
from django.db import transaction

from .forms import RouteForm, RouteStopFormSet
from .models import Route, RouteStop
from billing.models import TopPlan
from billing.services import BillingService


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
            # Для CreateView self.object спочатку None — це нормально
            context['stops'] = RouteStopFormSet(instance=self.object, prefix='stops')
        return context

    def form_valid(self, form):
        # 1. Створюємо формсет прямо тут, щоб контролювати його стан
        stops = RouteStopFormSet(self.request.POST, instance=self.object, prefix='stops')

        # 2. Перевіряємо обидві форми
        if form.is_valid() and stops.is_valid():
            try:
                with transaction.atomic():
                    # Зберігаємо маршрут
                    self.object = form.save(commit=False)

                    if not self.object.pk:
                        self.object.carrier = self.request.user
                        # Стартовий бонус 1 день
                        if not self.object.top_until:
                            self.object.top_until = timezone.now() + timezone.timedelta(days=1)

                    # Логіка оплати ТОП
                    boost_days_raw = form.cleaned_data.get('boost_days')
                    boost_days = int(boost_days_raw) if boost_days_raw else 0

                    if boost_days > 0:
                        plan = TopPlan.objects.filter(days=boost_days, is_active=True).first()
                        carrier_profile = self.request.user.carrier_profile

                        if plan and carrier_profile.balance >= plan.price:
                            success, msg = BillingService.process_payment(
                                user=self.request.user,
                                amount=plan.price,
                                description=f"ТОП {plan.days} дн. для {self.object.title}"
                            )
                            if success:
                                now = timezone.now()
                                start = self.object.top_until if (
                                            self.object.top_until and self.object.top_until > now) else now
                                self.object.top_until = start + timezone.timedelta(days=plan.days)
                                messages.success(self.request, f"ТОП активовано!")
                            else:
                                messages.error(self.request, msg)
                        else:
                            messages.error(self.request, "Недостатньо коштів.")

                    self.object.save()

                    # 3. Зберігаємо зупинки
                    stops.instance = self.object
                    stops.save()

                return redirect(self.success_url)
            except Exception as e:
                messages.error(self.request, f"Помилка: {str(e)}")
                return self.form_invalid(form)
        else:
            # Якщо формсет невалідний, виводимо помилки
            return self.render_to_response(self.get_context_data(form=form, stops=stops))

    def form_invalid(self, form):
        # Додаємо stops у контекст, щоб помилки відобразилися
        return self.render_to_response(self.get_context_data(form=form))


class RouteCreateView(RouteBaseView, CreateView): pass


class RouteUpdateView(RouteBaseView, UpdateView): pass