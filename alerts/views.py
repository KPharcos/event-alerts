from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AlertForm, ChannelFormSet
from .models import Alert


@login_required
def alert_list(request):
    alerts = request.user.alerts.prefetch_related("channels")
    return render(request, "alerts/alert_list.html", {"alerts": alerts})


@login_required
def alert_edit(request, pk=None):
    alert = get_object_or_404(Alert, pk=pk, user=request.user) if pk is not None else Alert(user=request.user)
    data = request.POST if request.method == "POST" else None
    form = AlertForm(data, instance=alert)
    formset = ChannelFormSet(data, instance=alert)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            alert = form.save()
            formset.instance = alert
            formset.save()
        return redirect("alert_list")
    return render(request, "alerts/alert_form.html", {"form": form, "formset": formset, "alert": alert})


@login_required
def alert_delete(request, pk):
    alert = get_object_or_404(Alert, pk=pk, user=request.user)
    if request.method == "POST":
        alert.delete()
        return redirect("alert_list")
    return render(request, "alerts/alert_confirm_delete.html", {"alert": alert})
