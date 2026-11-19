# World event alerts

Users describe what they care about in plain text ("tell me if a big quake hits Japan").
A cron job pulls events from free public feeds, Claude Haiku decides which alerts each
new event matches, and matches are delivered by email and/or Slack. Admins manage
users, alerts, events and the notification log in Django admin.

## Setup

```sh
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

- Admin: `/admin/` — create users here (there is no public sign-up), plus alerts, channels, manual events, and the notification log.
- Users: log in at `/accounts/login/` to manage their own alerts.

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | Django secret key. **Set it in production**; without it a random key is used and sessions reset on every restart | random per process |
| `DJANGO_DEBUG` | `1` enables debug | off |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `EMAIL_HOST` | SMTP host; when unset, emails are printed to the console | unset |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials | empty |
| `EMAIL_USE_TLS` | `1` or `true` for STARTTLS | `1` |
| `DEFAULT_FROM_EMAIL` | Sender address | `alerts@localhost` |
| `ANTHROPIC_API_KEY` | Claude API key (read by the `anthropic` SDK) | — |

Feed and matching settings live in `config/settings.py`: `EVENT_RSS_FEEDS`, `ALERT_MATCH_MODEL`.

## Sources

- `usgs`: USGS earthquakes of magnitude 4.5+ from the last day (category `disaster`).
- `rss`: each feed in `EVENT_RSS_FEEDS`, BBC World by default (category `news`). One failing feed doesn't skip the others.
- `gdacs`: GDACS global disaster alerts — floods, cyclones, volcanoes, droughts, wildfires (category `disaster`).
  GDACS earthquakes are skipped because USGS already covers them.

There is no market feed. Market events (category `market`) are added by hand in admin
(`/admin/alerts/event/add/`) and are matched and delivered on the next poll run.

## Polling

Run the poller from cron every 5 minutes:

```
*/5 * * * * cd <dir> && flock -n /tmp/poll_events.lock uv run python manage.py poll_events
```

`flock -n` skips a run while the previous one is still going (a slow Claude call can take
minutes), so overlapping runs can't send the same notification twice.

Each run fetches every source, stores new events (deduplicated by source + external id),
asks Claude once per unmatched event which active alerts it satisfies, sends to each matched
alert's channels and records a `Notification` per channel. If the Claude call fails, the
event stays unmatched and is retried on the next run. A failing source or channel is logged
and does not stop the run. Events added by hand in admin are picked up the same way.

Failed sends are retried automatically: each run re-sends every `failed` notification from an
earlier run, up to 3 attempts in total (`attempts` column in the admin notification log).
After the third failure it stays `failed`.

The first run after setup stores everything currently in the feeds (a few hundred events) and
makes one Claude call per event that has active alerts to check.

## Adding a channel

In `alerts/channels.py`, write a `send(target, subject, body)` function and a
`validate(target)` function that raises `ValidationError`, then add one entry:

```python
CHANNELS["teams"] = Channel("Microsoft Teams", validate_teams, send_teams)
```

The channel appears in the alert form and admin. Run `uv run python manage.py makemigrations`
once to record the new choice (no schema change).

## Adding a source

In `alerts/sources.py`, write a function that returns a list of dicts with the `Event` fields
`external_id`, `category` (`news`, `market` or `disaster`), `title`, `summary`, `url`,
`occurred_at`, and add it to `SOURCES` under a unique key.

## Tests

```sh
uv run python manage.py test alerts
```

All network access (Claude, feeds, Slack) is mocked.
