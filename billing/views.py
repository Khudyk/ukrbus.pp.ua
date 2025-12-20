from datetime import timezone

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from pyexpat.errors import messages

from billing.models import TopPlan
from billing.services import BillingService
from trips.models import Route


@login_required
def boost_route(request, pk):
    route = get_object_or_404(Route, pk=pk, carrier=request.user)
    cost = 50.00

    # Викликаємо наш новий сервіс
    success, message = BillingService.process_payment(
        user=request.user,
        amount=cost,
        description=f"ТОП для маршруту {route.title}"
    )

    if success:
        # Логіка додавання часу ТОП (яку ми писали раніше)
        route.activate_top(days=7)  # Можна винести в метод моделі Route
        messages.success(request, "Послугу активовано!")
    else:
        messages.error(request, message)

    return redirect('profile')


@login_required
def boost_route_select(request, pk):
    """Сторінка вибору тарифу"""
    route = get_object_or_404(Route, pk=pk, carrier=request.user)
    plans = TopPlan.objects.filter(is_active=True)
    return render(request, 'billing/boost_select.html', {
        'route': route,
        'plans': plans
    })


@login_required
def boost_route_confirm(request, pk, plan_id):
    """Обробка оплати обраного тарифу"""
    route = get_object_or_404(Route, pk=pk, carrier=request.user)
    plan = get_object_or_404(TopPlan, pk=plan_id, is_active=True)

    success, message = BillingService.process_payment(
        user=request.user,
        amount=plan.price,
        description=f"ТОП на {plan.days} днів для {route.title}"
    )

    if success:
        now = timezone.now()
        start_point = route.top_until if (route.top_until and route.top_until > now) else now
        route.top_until = start_point + timezone.timedelta(days=plan.days)
        route.save()
        messages.success(request, f"Успішно активовано на {plan.days} днів!")
    else:
        messages.error(request, message)

    return redirect('profile')