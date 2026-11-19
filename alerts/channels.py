"""Channel registry: the extension point for delivery channels.

Add a channel by writing a send function (and validator) and one CHANNELS entry.
"""
import json
import urllib.request
from typing import Callable, NamedTuple

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email


class Channel(NamedTuple):
    label: str
    validate: Callable[[str], None]  # raises ValidationError
    send: Callable[[str, str, str], None]  # (target, subject, body)


def send_email(target, subject, body):
    send_mail(subject, body, None, [target])


def validate_slack(target):
    # Only Slack's own webhook host, so a user can't make the server POST anywhere (SSRF).
    if not target.startswith("https://hooks.slack.com/"):
        raise ValidationError("Slack target must be an https://hooks.slack.com/ webhook URL.")


def slack_escape(text):
    # Feed text is untrusted: stop <!channel> pings and <url|label> link spoofing.
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_slack(target, subject, body):
    req = urllib.request.Request(
        target,
        data=json.dumps({"text": f"*{slack_escape(subject)}*\n{slack_escape(body)}"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10):
        pass


CHANNELS = {
    "email": Channel("Email", validate_email, send_email),
    "slack": Channel("Slack webhook", validate_slack, send_slack),
}
