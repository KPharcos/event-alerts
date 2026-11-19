from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .channels import CHANNELS


class Event(models.Model):
    CATEGORIES = [("news", "News"), ("market", "Market"), ("disaster", "Disaster")]

    source = models.CharField(max_length=50)
    external_id = models.CharField(max_length=500)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    url = models.URLField(max_length=1000, blank=True)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source", "external_id"], name="unique_event_per_source")]
        ordering = ["-occurred_at"]

    def __str__(self):
        return self.title


class Alert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    name = models.CharField(max_length=200)
    description = models.TextField(help_text='What should trigger this alert, e.g. "a big earthquake hits Japan".')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AlertChannel(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="channels")
    channel = models.CharField(max_length=30, choices=[(key, c.label) for key, c in CHANNELS.items()])
    target = models.CharField(max_length=500, help_text="Email address or Slack webhook URL.")

    def __str__(self):
        return f"{self.channel}: {self.target}"

    def clean(self):
        if self.channel in CHANNELS and self.target:
            try:
                CHANNELS[self.channel].validate(self.target)
            except ValidationError as e:
                raise ValidationError({"target": e.messages})


class Notification(models.Model):
    STATUSES = [("sent", "Sent"), ("failed", "Failed")]

    alert_channel = models.ForeignKey(AlertChannel, on_delete=models.CASCADE, related_name="notifications")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notifications")
    status = models.CharField(max_length=10, choices=STATUSES)
    attempts = models.PositiveSmallIntegerField(default=1)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["alert_channel", "event"], name="unique_notification")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} -> {self.alert_channel} ({self.status})"
