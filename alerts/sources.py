"""Free public event feeds. Each fetcher returns a list of dicts of Event fields (minus `source`).

No market feed: market events are added by hand in admin.
"""
import json
import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone

log = logging.getLogger(__name__)

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
GDACS_URL = "https://www.gdacs.org/xml/rss.xml"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "world-event-alerts/0.1"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _rss_items(url, category):
    events = []
    items = list(ET.fromstring(_get(url)).iter("item"))
    if not items:
        log.warning("No RSS <item> elements in %s; Atom and RDF feeds are not supported", url)
    for item in items:
        link = (item.findtext("link") or "").strip()
        ext_id = (item.findtext("guid") or "").strip() or link
        if not ext_id:
            continue
        pub = item.findtext("pubDate")
        try:
            occurred = parsedate_to_datetime(pub) if pub else timezone.now()
        except (TypeError, ValueError):
            occurred = timezone.now()
        if occurred.tzinfo is None:  # "-0000" pubDates parse as naive
            occurred = occurred.replace(tzinfo=UTC)
        events.append({
            "external_id": ext_id[:500],
            "category": category,
            "title": (item.findtext("title") or ext_id).strip()[:500],
            "summary": strip_tags(item.findtext("description") or "").strip()[:2000],
            "url": link[:1000],
            "occurred_at": occurred,
        })
    return events


def fetch_usgs():
    events = []
    for f in json.loads(_get(USGS_URL))["features"]:
        p = f["properties"]
        events.append({
            "external_id": f["id"],
            "category": "disaster",
            "title": (p.get("title") or f"M{p.get('mag')} earthquake - {p.get('place')}")[:500],
            "summary": f"Magnitude {p.get('mag')} earthquake, {p.get('place')}. Tsunami flag: {p.get('tsunami')}.",
            "url": p.get("url") or "",
            "occurred_at": datetime.fromtimestamp(p["time"] / 1000, tz=UTC),
        })
    return events


def fetch_rss():
    events = []
    for feed in settings.EVENT_RSS_FEEDS:
        try:
            events += _rss_items(feed, "news")
        except Exception:
            log.exception("RSS feed %s failed", feed)
    return events


def fetch_gdacs():
    # USGS already covers earthquakes; GDACS adds floods, cyclones, volcanoes, droughts, wildfires.
    return [e for e in _rss_items(GDACS_URL, "disaster") if not e["external_id"].startswith("EQ")]


SOURCES = {"usgs": fetch_usgs, "rss": fetch_rss, "gdacs": fetch_gdacs}
