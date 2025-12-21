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
            # Використовуємо prefix='stops', щоб JS точно знаходив інпути
            context['stops'] = RouteStopFormSet(self.request.POST, instance=self.object, prefix='stops')
        else:
            context['stops'] = RouteStopFormSet(instance=self.object, prefix='stops')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        stops = context['stops']

        # Отримуємо вибір ТОП
        boost_days = int(form.cleaned_data.get('boost_days', 0))

        if form.is_valid() and stops.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save(commit=False)

                    if not self.object.pk:
                        self.object.carrier = self.request.user
                        # Стартовий бонус 1 день
                        self.object.top_until = timezone.now() + timezone.timedelta(days=1)

                    # Логіка оплати
                    if boost_days > 0:
                        plan = TopPlan.objects.filter(days=boost_days, is_active=True).first()
                        carrier = self.request.user.carrier_profile

                        if plan and carrier.balance >= plan.price:
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
                                messages.success(self.request, f"ТОП активовано на {plan.days} днів!")
                            else:
                                messages.error(self.request, msg)
                        else:
                            messages.error(self.request, "Недостатньо коштів на балансі.")

                    self.object.save()
                    stops.instance = self.object
                    stops.save()  # Django сам проігнорує абсолютно порожні форми

                return redirect(self.success_url)
            except Exception as e:
                messages.error(self.request, f"Помилка збереження: {str(e)}")

        return self.render_to_response(self.get_context_data(form=form))


class RouteCreateView(RouteBaseView, CreateView): pass


class RouteUpdateView(RouteBaseView, UpdateView): pass