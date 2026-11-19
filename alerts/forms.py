from django import forms
from django.forms import inlineformset_factory

from .models import Alert, AlertChannel


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["name", "description", "active"]


ChannelFormSet = inlineformset_factory(
    Alert, AlertChannel, fields=["channel", "target"], extra=2, can_delete=True
)
