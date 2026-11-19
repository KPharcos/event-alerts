from django import forms
from django.forms import inlineformset_factory

from .models import Alert, AlertChannel


class AlertForm(forms.ModelForm):
    # Capped: the description goes into every match prompt, so a huge one would make Claude reject all of them.
    description = forms.CharField(
        max_length=2000,
        widget=forms.Textarea,
        help_text='What should trigger this alert, e.g. "a big earthquake hits Japan". '
                  "There is no automatic market feed, so market moves reach you only through news.",
    )

    class Meta:
        model = Alert
        fields = ["name", "description", "active"]


ChannelFormSet = inlineformset_factory(
    Alert, AlertChannel, fields=["channel", "target"], extra=2, can_delete=True
)
