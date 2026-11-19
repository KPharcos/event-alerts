import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from alerts.channels import CHANNELS
from alerts.matching import match_event
from alerts.models import Alert, Event, Notification
from alerts.sources import SOURCES

log = logging.getLogger("alerts.poll")

MAX_ATTEMPTS = 3


def message(alert, event):
    subject = " ".join(f"[{alert.name}] {event.title}".split())  # mail headers can't hold newlines
    body = f"{event.title}\n\n{event.summary}\n\n{event.url}".strip()
    return subject, body


def deliver(ac, subject, body):
    """Send through the channel; return (status, error) instead of raising."""
    try:
        CHANNELS[ac.channel].send(ac.target, subject, body)
        return "sent", ""
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        log.warning("Send via %s for alert %s failed: %s", ac.channel, ac.alert_id, error)
        return "failed", error


class Command(BaseCommand):
    help = "Fetch events from all sources, match them against active alerts and send notifications."

    def handle(self, *args, **options):
        run_started = timezone.now()
        for name, fetch in SOURCES.items():
            try:
                created = 0
                for item in fetch():
                    _, new = Event.objects.get_or_create(
                        source=name, external_id=item.pop("external_id"), defaults=item
                    )
                    created += new
                log.info("Source %s: %d new events", name, created)
            except Exception:
                log.exception("Source %s failed", name)

        alerts = list(Alert.objects.filter(active=True).prefetch_related("channels"))
        for event in Event.objects.filter(matched_at__isnull=True).order_by("occurred_at"):
            try:
                self.process(event, alerts)
            except Exception:
                log.exception("Processing event %s failed", event.pk)

        # Retry sends that failed in earlier runs (not this one), up to MAX_ATTEMPTS in total.
        retry = Notification.objects.filter(
            status="failed", attempts__lt=MAX_ATTEMPTS, created_at__lt=run_started,
            alert_channel__alert__active=True,
        ).select_related("event", "alert_channel__alert")
        for n in retry:
            n.status, n.error = deliver(n.alert_channel, *message(n.alert_channel.alert, n.event))
            n.attempts += 1
            n.save(update_fields=["status", "error", "attempts"])

    def process(self, event, alerts):
        ids = match_event(event, alerts) if alerts else []
        if ids is None:
            return  # matcher failed; leave matched_at null so the next run retries
        by_id = {a.id: a for a in alerts}
        for alert_id in ids:
            alert = by_id[alert_id]
            subject, body = message(alert, event)
            for ac in alert.channels.all():
                if Notification.objects.filter(alert_channel=ac, event=event).exists():
                    continue
                status, error = deliver(ac, subject, body)
                Notification.objects.create(alert_channel=ac, event=event, status=status, error=error)
        event.matched_at = timezone.now()
        event.save(update_fields=["matched_at"])
