# CLAUDE.md

## Codebase Overview

Django app where users write free-text alerts about world events. A cron command (`poll_events`)
pulls events from free feeds (USGS, GDACS, BBC RSS), one Claude Haiku call per new event decides
which alerts match, and matches are sent by email or Slack webhook through a channel registry,
with every send logged as a `Notification`.

**Stack**: Python 3.12+, Django 6.1, SQLite, `anthropic` SDK (structured output via `pydantic`), uv.
**Structure**: `config/` (settings, URLs), `alerts/` (models, `channels.py` registry, `sources.py` feeds, `matching.py` Claude matcher, `management/commands/poll_events.py`, views, admin, tests).

Run tests: `uv run python manage.py test alerts` (all network mocked).

For detailed architecture, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).
