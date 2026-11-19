import json
import urllib.error
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import anthropic
import httpx2
import pydantic
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import sources
from .channels import send_slack
from .matching import MatchResult
from .models import Alert, AlertChannel, Event, Notification

SLACK_URL = "https://hooks.slack.com/services/T000/B000/XXX"


def quake(ext_id="us7000abcd"):
    return {
        "external_id": ext_id,
        "category": "disaster",
        "title": "M 7.1 - 50 km E of Tokyo, Japan",
        "summary": "Magnitude 7.1 earthquake",
        "url": "https://earthquake.usgs.gov/x",
        "occurred_at": datetime(2026, 11, 19, 9, 0, tzinfo=UTC),
    }


def claude_returning(ids=(), stop_reason="end_turn"):
    """Patch the Anthropic client so messages.parse returns the given ids."""
    client = MagicMock()
    client.messages.parse.return_value = SimpleNamespace(
        stop_reason=stop_reason, parsed_output=MatchResult(alert_ids=list(ids))
    )
    return patch("alerts.matching.anthropic.Anthropic", return_value=client), client


def claude_raising(exc):
    client = MagicMock()
    client.messages.parse.side_effect = exc
    return patch("alerts.matching.anthropic.Anthropic", return_value=client), client


class PollTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pw-123456")
        self.alert = Alert.objects.create(user=self.user, name="Japan quake", description="big quake hits Japan")
        self.email = AlertChannel.objects.create(alert=self.alert, channel="email", target="alice@example.com")
        self.slack = AlertChannel.objects.create(alert=self.alert, channel="slack", target=SLACK_URL)
        self.urlopen = patch("alerts.channels.urllib.request.urlopen").start()
        self.addCleanup(patch.stopall)

    def poll(self, sources_map=None):
        with patch.dict("alerts.sources.SOURCES", {"usgs": lambda: [quake()]} if sources_map is None else sources_map, clear=True):
            call_command("poll_events")


class PollTests(PollTestBase):
    def test_happy_path(self):
        p, client = claude_returning([self.alert.id])
        with p:
            self.poll()
        event = Event.objects.get()
        self.assertIsNotNone(event.matched_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])
        self.assertEqual(self.urlopen.call_count, 1)
        req = self.urlopen.call_args.args[0]
        self.assertEqual(req.full_url, SLACK_URL)
        self.assertIn("Tokyo", json.loads(req.data)["text"])
        self.assertEqual(self.urlopen.call_args.kwargs["timeout"], 10)
        self.assertEqual(Notification.objects.filter(status="sent").count(), 2)
        kwargs = client.messages.parse.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-haiku-5-5")
        self.assertIn("untrusted", kwargs["system"])
        self.assertIn("alert descriptions", kwargs["system"])
        self.assertIn(f'<alert id="{self.alert.id}">big quake hits Japan</alert>', kwargs["messages"][0]["content"])

    def test_duplicate_fetch(self):
        p, client = claude_returning([self.alert.id])
        with p:
            self.poll()
            self.poll()
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(client.messages.parse.call_count, 1)

    def test_foreign_ids_ignored(self):
        inactive = Alert.objects.create(user=self.user, name="off", description="x", active=False)
        AlertChannel.objects.create(alert=inactive, channel="email", target="off@example.com")
        p, client = claude_returning([inactive.id, 99999])
        with p:
            self.poll()
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIsNotNone(Event.objects.get().matched_at)
        self.assertNotIn(f'<alert id="{inactive.id}">', client.messages.parse.call_args.kwargs["messages"][0]["content"])

    def test_channel_fail(self):
        self.urlopen.side_effect = urllib.error.HTTPError(SLACK_URL, 500, "Server Error", {}, None)
        p, _ = claude_returning([self.alert.id])
        with p:
            self.poll()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Notification.objects.get(alert_channel=self.email).status, "sent")
        failed = Notification.objects.get(alert_channel=self.slack)
        self.assertEqual(failed.status, "failed")
        self.assertIn("500", failed.error)
        self.assertIsNotNone(Event.objects.get().matched_at)

    def test_claude_error_retries_next_run(self):
        req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
        for exc in (
            anthropic.APIConnectionError(request=req),
            anthropic.InternalServerError("boom", response=httpx2.Response(500, request=req), body=None),
        ):
            with self.subTest(exc=type(exc).__name__):
                p, _ = claude_raising(exc)
                with p:
                    self.poll()
                self.assertIsNone(Event.objects.get().matched_at)
                self.assertEqual(Notification.objects.count(), 0)
        # next run succeeds -> delivered
        p, _ = claude_returning([self.alert.id])
        with p:
            self.poll()
        self.assertIsNotNone(Event.objects.get().matched_at)
        self.assertEqual(Notification.objects.count(), 2)

    def test_bad_request_not_retried(self):
        req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
        p, _ = claude_raising(anthropic.BadRequestError("too big", response=httpx2.Response(400, request=req), body=None))
        with p:
            self.poll()
        self.assertIsNotNone(Event.objects.get().matched_at)
        self.assertEqual(Notification.objects.count(), 0)

    def test_unparseable_output_not_retried(self):
        try:
            MatchResult.model_validate_json("I can't help with that.")
        except pydantic.ValidationError as e:
            exc = e
        p, _ = claude_raising(exc)
        with p:
            self.poll()
        self.assertIsNotNone(Event.objects.get().matched_at)
        self.assertEqual(Notification.objects.count(), 0)

    def test_parsed_output_none(self):
        client = MagicMock()
        client.messages.parse.return_value = SimpleNamespace(stop_reason="max_tokens", parsed_output=None)
        with patch("alerts.matching.anthropic.Anthropic", return_value=client):
            self.poll()
        self.assertIsNotNone(Event.objects.get().matched_at)
        self.assertEqual(Notification.objects.count(), 0)

    def test_newline_in_title_kept_out_of_subject(self):
        Event.objects.create(source="manual", external_id="1", **{k: v for k, v in quake().items() if k != "external_id"} | {"title": "Big\nquake"})
        p, _ = claude_returning([self.alert.id])
        with p:
            self.poll({})
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("\n", mail.outbox[0].subject)

    def test_existing_notification_not_resent(self):
        event = Event.objects.create(source="manual", external_id="1", **{k: v for k, v in quake().items() if k != "external_id"})
        Notification.objects.create(alert_channel=self.email, event=event, status="sent")
        p, _ = claude_returning([self.alert.id])
        with p:
            self.poll({})
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.urlopen.call_count, 1)
        self.assertEqual(Notification.objects.count(), 2)

    def test_failed_send_retried_next_run(self):
        self.urlopen.side_effect = urllib.error.HTTPError(SLACK_URL, 500, "Server Error", {}, None)
        p, client = claude_returning([self.alert.id])
        with p:
            self.poll()
            self.assertEqual(Notification.objects.get(alert_channel=self.slack).attempts, 1)
            self.urlopen.side_effect = None
            self.poll()
        n = Notification.objects.get(alert_channel=self.slack)
        self.assertEqual((n.status, n.attempts, n.error), ("sent", 2, ""))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(client.messages.parse.call_count, 1)

    def test_failed_send_gives_up_after_3_attempts(self):
        self.urlopen.side_effect = urllib.error.HTTPError(SLACK_URL, 500, "Server Error", {}, None)
        p, _ = claude_returning([self.alert.id])
        with p:
            for _ in range(4):
                self.poll()
        n = Notification.objects.get(alert_channel=self.slack)
        self.assertEqual((n.status, n.attempts), ("failed", 3))
        self.assertEqual(self.urlopen.call_count, 3)

    def test_refusal(self):
        p, _ = claude_returning([self.alert.id], stop_reason="refusal")
        with p:
            self.poll()
        self.assertIsNotNone(Event.objects.get().matched_at)
        self.assertEqual(Notification.objects.count(), 0)

    def test_source_fail(self):
        def broken():
            raise urllib.error.URLError("down")

        p, _ = claude_returning([self.alert.id])
        with p:
            self.poll({"rss": broken, "usgs": lambda: [quake()]})
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 2)

    def test_no_alerts_no_claude_call(self):
        Alert.objects.update(active=False)
        p, client = claude_returning([self.alert.id])
        with p:
            self.poll()
        client.messages.parse.assert_not_called()
        self.assertIsNotNone(Event.objects.get().matched_at)

    def test_manual_event(self):
        Event.objects.create(source="manual", external_id="1", **{k: v for k, v in quake().items() if k != "external_id"})
        p, _ = claude_returning([self.alert.id])
        with p:
            self.poll({})
        self.assertEqual(Notification.objects.filter(status="sent").count(), 2)
        self.assertIsNotNone(Event.objects.get().matched_at)


class SourceParsingTests(TestCase):
    def test_usgs(self):
        body = json.dumps({"features": [{"id": "us1", "properties": {
            "mag": 5.2, "place": "Chile", "time": 1763542800000, "url": "https://u", "title": "M 5.2 - Chile", "tsunami": 0,
        }}]}).encode()
        with patch("alerts.sources._get", return_value=body):
            [e] = sources.fetch_usgs()
        self.assertEqual((e["external_id"], e["category"], e["title"]), ("us1", "disaster", "M 5.2 - Chile"))
        self.assertEqual(e["occurred_at"], datetime(2025, 11, 19, 9, 0, tzinfo=UTC))

    @override_settings(EVENT_RSS_FEEDS=["https://bad", "https://feed"])
    def test_rss(self):
        body = b"""<rss><channel>
          <item><title>A</title><link>https://a</link><guid>g1</guid><pubDate>Wed, 19 Nov 2026 08:00:00 GMT</pubDate></item>
          <item><title>B</title><link>https://b</link></item>
          <item><title>C</title><link>https://c</link><guid>  </guid><pubDate>Thu, 19 Nov 2026 08:00:00 -0000</pubDate></item>
        </channel></rss>"""

        def get(url):
            if url == "https://bad":
                raise urllib.error.URLError("down")
            return body

        with patch("alerts.sources._get", side_effect=get):
            events = sources.fetch_rss()
        self.assertEqual([e["external_id"] for e in events], ["g1", "https://b", "https://c"])
        self.assertEqual(events[0]["category"], "news")
        self.assertEqual(events[0]["occurred_at"], datetime(2026, 11, 19, 8, 0, tzinfo=UTC))
        self.assertEqual(events[2]["occurred_at"], datetime(2026, 11, 19, 8, 0, tzinfo=UTC))
        self.assertIsNotNone(events[2]["occurred_at"].tzinfo)

    def test_gdacs_skips_earthquakes(self):
        body = """\ufeff<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
          <item><title>Green earthquake in Peru</title><link>https://g/eq</link><guid>EQ1578046</guid>
            <pubDate>Wed, 19 Nov 2026 06:00:00 GMT</pubDate></item>
          <item><title>Red flood alert in Bangladesh</title><description>Flood</description><link>https://g/fl</link>
            <guid>FL1103456</guid><pubDate>Wed, 19 Nov 2026 07:00:00 GMT</pubDate></item>
        </channel></rss>""".encode()
        with patch("alerts.sources._get", return_value=body):
            [e] = sources.fetch_gdacs()
        self.assertEqual((e["external_id"], e["category"], e["title"]), ("FL1103456", "disaster", "Red flood alert in Bangladesh"))
        self.assertEqual(e["occurred_at"], datetime(2026, 11, 19, 7, 0, tzinfo=UTC))


class SlackTests(TestCase):
    def test_slack_text_escaped(self):
        with patch("alerts.channels.urllib.request.urlopen") as urlopen:
            send_slack(SLACK_URL, "<!channel> & co", "see <http://evil|bank>")
        text = json.loads(urlopen.call_args.args[0].data)["text"]
        self.assertEqual(text, "*&lt;!channel&gt; &amp; co*\nsee &lt;http://evil|bank&gt;")


class AlertViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pw-123456")
        self.other = User.objects.create_user("bob", password="pw-123456")
        self.bobs = Alert.objects.create(user=self.other, name="bob's", description="x")

    def form_data(self, slack=SLACK_URL):
        return {
            "name": "Quake", "description": "big quake in Japan", "active": "on",
            "channels-TOTAL_FORMS": "2", "channels-INITIAL_FORMS": "0",
            "channels-MIN_NUM_FORMS": "0", "channels-MAX_NUM_FORMS": "1000",
            "channels-0-channel": "email", "channels-0-target": "alice@example.com",
            "channels-1-channel": "slack", "channels-1-target": slack,
        }

    def test_login_lands_on_list_and_create_alert(self):
        resp = self.client.post(reverse("login"), {"username": "alice", "password": "pw-123456"})
        self.assertRedirects(resp, reverse("alert_list"))
        resp = self.client.post(reverse("alert_create"), self.form_data())
        self.assertRedirects(resp, reverse("alert_list"))
        alert = Alert.objects.get(user=self.user)
        self.assertEqual(sorted(alert.channels.values_list("channel", flat=True)), ["email", "slack"])
        self.assertContains(self.client.get(reverse("alert_list")), "Quake")
        self.assertNotContains(self.client.get(reverse("alert_list")), "bob&#x27;s")

    def test_bad_email_rejected(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse("alert_create"), self.form_data() | {"channels-0-target": "not-an-email"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Alert.objects.filter(user=self.user).exists())
        self.assertEqual(AlertChannel.objects.count(), 0)

    def test_update_own_alert_and_delete_channel(self):
        alert = Alert.objects.create(user=self.user, name="Old", description="x")
        ch = AlertChannel.objects.create(alert=alert, channel="email", target="alice@example.com")
        self.client.force_login(self.user)
        resp = self.client.post(reverse("alert_update", args=[alert.pk]), {
            "name": "New", "description": "x", "active": "on",
            "channels-TOTAL_FORMS": "1", "channels-INITIAL_FORMS": "1",
            "channels-MIN_NUM_FORMS": "0", "channels-MAX_NUM_FORMS": "1000",
            "channels-0-id": str(ch.pk), "channels-0-channel": "email",
            "channels-0-target": "alice@example.com", "channels-0-DELETE": "on",
        })
        self.assertRedirects(resp, reverse("alert_list"))
        alert.refresh_from_db()
        self.assertEqual(alert.name, "New")
        self.assertEqual(Alert.objects.filter(user=self.user).count(), 1)
        self.assertFalse(alert.channels.exists())

    def test_bad_slack_url_rejected(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse("alert_create"), self.form_data(slack="http://evil.example/x"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "hooks.slack.com")
        self.assertFalse(Alert.objects.filter(user=self.user).exists())
        self.assertEqual(AlertChannel.objects.count(), 0)

    def test_other_users_alert_404(self):
        self.client.force_login(self.user)
        for name in ("alert_update", "alert_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[self.bobs.pk])).status_code, 404)
            self.assertEqual(self.client.post(reverse(name, args=[self.bobs.pk])).status_code, 404)
        self.assertTrue(Alert.objects.filter(pk=self.bobs.pk).exists())

    def test_delete_own_alert(self):
        self.client.force_login(self.other)
        self.client.post(reverse("alert_delete", args=[self.bobs.pk]))
        self.assertFalse(Alert.objects.exists())

    def test_login_required(self):
        resp = self.client.get(reverse("alert_list"))
        self.assertRedirects(resp, f"{reverse('login')}?next=/")


class AdminTests(TestCase):
    def test_admin_pages_render(self):
        admin = User.objects.create_superuser("root", "root@example.com", "pw-123456")
        self.client.force_login(admin)
        for url in (
            "/admin/auth/user/add/", "/admin/alerts/alert/add/", "/admin/alerts/event/add/",
            "/admin/alerts/event/", "/admin/alerts/notification/?status__exact=failed",
        ):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get("/admin/alerts/notification/add/").status_code, 403)
