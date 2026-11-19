# Prompts

Every user prompt, verbatim, oldest first, plus every interactive question Claude asked
(with all options offered) and the answer chosen. Chosen option marked **✔**.

## 2026-11-19 — 1

Save every prompt in docs/PROMPTS.md

## 2026-11-19 — 2

Install BMAD

## 2026-11-19 — 3

/bmad-build-auto "We want users to be able to set up alerts so they get notified when
something important happens in the world — like breaking news, market
movements, natural disasters, that kind of thing. Should work for both email
and Slack. Make it flexible enough that we can add more channels later.
We need an admin view too." If any question arises, ask me interactively!

### Questions — round 1 (planning)

**Project is empty. Which stack should the alerts app use?**
- **✔ Django + SQLite (Recommended)** — Gives you user accounts, admin view, email sending and scheduled jobs (management command) out of the box. Least new code.
- FastAPI + SQLite — Lighter API-first; admin view, auth, templates all hand-built.
- Node/TypeScript (Express or Next.js) — JS stack; auth + admin hand-built or via extra libs.

**Where should 'world events' come from in the first version?**
- **✔ Free public feeds (Recommended)** — Pluggable source interface. Ship with: USGS earthquakes (disasters), RSS feeds (breaking news), Stooq/Yahoo price feed (markets). No API keys. Admin can also add events by hand.
- Admin/manual + webhook ingest only — No external polling. Events enter via admin form or POST endpoint. Sources added later.
- Specific paid APIs — You name them (e.g. NewsAPI, Alpha Vantage). Needs keys.

**How should a user define an alert?**
- Category + keywords + min severity (Recommended) — Pick category (news/market/disaster), optional keywords, optional severity threshold, choose channel(s).
- Category only — Subscribe to whole category. Simplest, noisy.
- **✔ Free-text, AI-matched** — User writes 'tell me if a big quake hits Japan'; LLM decides matches. Needs Claude API key, costs per event.

**How should Slack delivery work?**
- **✔ Incoming webhook URL per alert (Recommended)** — User pastes a Slack webhook URL. No Slack app/OAuth needed.
- Slack app with OAuth + bot token — Proper 'Add to Slack' install, DMs/channel picker. Needs Slack app setup and secrets.

### Questions — round 2 (planning)

**How do users get accounts?**
- Self sign-up + login (Recommended) — Django auth: sign-up, login, logout pages. Each user manages own alerts.
- **✔ Admin creates users** — No public sign-up. Admin adds users in admin view.

**What should the admin view be?**
- **✔ Django admin (Recommended)** — Built-in: manage users, alerts, events, sources, see delivery log with success/failure. Near-zero code.
- Custom admin dashboard — Hand-built pages with stats/charts. More code.

**Which Claude model should decide if an event matches a free-text alert? (One call per new event, checks all active alerts at once.)**
- **✔ Haiku 5.5 (Recommended)** — Cheapest, fastest. Good enough for yes/no matching.
- Sonnet 5.5 — Better judgement on fuzzy alerts, higher cost.
- Opus 5.5 — Best judgement, highest cost.

**When should notifications go out?**
- **✔ Immediately per matching event (Recommended)** — Poll runs every few minutes (cron), each match sent at once. Duplicate events never re-sent.
- Digest — Batch matches into hourly/daily summary.

### Questions — round 3 (after implementation)

**Stooq (planned free market feed) is dead: 404 and a bot check. What should supply market-move events?**
- Finnhub, free API key (Recommended) — Official API, free tier 60 calls/min, quote endpoint gives % change. You sign up for a key and set FINNHUB_API_KEY. Market source skipped when key unset.
- Yahoo Finance chart endpoint — No key. Unofficial, undocumented, can rate-limit or break without notice; terms of use unclear.
- Alpha Vantage, free key — Official, but free tier ~25 requests/day, so market polling must be throttled to a few times a day.
- **✔ Drop market feed for now** — Remove Stooq source. Admin can still add market events by hand; add a real feed later.

### Questions — round 4 (review triage)

**When a Slack/email send fails (e.g. Slack 500, SMTP timeout), it's logged as 'failed' and never retried, so the alert is lost. What should happen?**
- **✔ Auto-retry next runs, max 3 tries (Recommended)** — Poller re-sends failed notifications on following runs (every 5 min) until sent or 3 attempts; attempt count shown in admin.
- Admin 'Resend' action only — Admin selects failed notifications in admin and clicks Resend. No automatic retry.
- Keep as is — Failure logged in admin, no retry.

**Natural disasters currently = earthquakes only (USGS). Add more disaster types?**
- **✔ Add GDACS feed (Recommended)** — UN/EU Global Disaster Alert system, free RSS, no key: floods, cyclones, volcanoes, droughts, wildfires, quakes. One more source function.
- Earthquakes only for now — Keep USGS only; add more later.

## 2026-11-19 — 4

You should save all the prompts, the interactive questions with options and answers!

## 2026-11-19 — 5

Save every worth checking response and the follow up prompt in docs/VALIDATION-LOG.md (like this one: "The alerts app is built and...")

## 2026-11-19 — 6

Make the first commit + push to https://github.com/KPharcos

### Questions — round 1 (commit + push)

**https://github.com/KPharcos is your account, and the alerts project has no repo there yet. What should the new repo be called?**
- real-world-event-alerts (Recommended) — Matches the folder name, with dashes instead of underscores.
- world-event-alerts — Shorter name.
- **✔ event-alerts** — Shortest name.

**Should the new alerts repo be public or private?**
- **✔ Public (Recommended)** — Matches your other repo (helpdesk-rag). Anyone can see the code, docs/PROMPTS.md and docs/VALIDATION-LOG.md.
- Private — Only you can see it, and you can make it public later.

**Should the BMAD files (_bmad/, .claude/skills/, _bmad-output/) go into the alerts repo too?**
- Commit all (Recommended) — Includes the framework (about 2 MB of skills) and the spec, so anyone who clones the repo gets the same workflow.
- **✔ Only _bmad-output (spec)** — Keeps the spec and leaves out the installed framework (_bmad/, .claude/) with a .gitignore entry.
- None — App code and docs only.

## 2026-11-19 — 7

/model (run directly in Claude Code, not sent to Claude) — output: "Set model to `Sonnet 5.5` and saved as your default for new sessions with `xhigh` effort"

Please log the model and effort changes into docs/PROMPTS.md

### Settings changes

- **Model:** Opus 5.5 (`claude-opus-5-5`) → **Sonnet 5.5** (`claude-sonnet-5-5`). Saved as default for new sessions.
- **Effort:** **xhigh**, saved as default for new sessions. The previous effort level was not shown in the session.

## 2026-11-19 — 8

/bmad-build-auto _bmad-output/implementation-artifacts/spec-world-event-alerts.md

## 2026-11-19 — 9

/model (run directly in Claude Code, not sent to Claude) — output: "Set model to `Haiku 5.5` and saved as your default for new sessions · `max` effort for this session only"

Always log the model and effort changes into docs/PROMPTS.md

### Settings changes

- **Model:** Sonnet 5.5 (`claude-sonnet-5-5`) → **Haiku 5.5** (`claude-haiku-5-5`). Saved as default for new sessions.
- **Effort:** **max**, this session only. Not saved as default. Default effort unchanged (still xhigh from prompt 7).

## 2026-11-19 — 10

/bmad-build-auto _bmad-output/implementation-artifacts/spec-world-event-alerts.md

### Questions — round 1 (review triage, pass 3)

**Which old events may notify an alert? First poll stores about 250 existing events, and a new alert would also match events from before it was saved. Which rule should apply?**
- **✔ Last 24 hours only (Recommended)** — Events older than 24 h are marked done without sending. Fixes the first-deploy flood, outage backlogs and new alerts matching old news.
- Send everything unmatched (current) — Keeps today's behavior: first deploy sends matches for the whole backlog at once; alerts match any old unmatched event.
- Only events after the alert was saved — Each alert ignores events that happened before it existed. Needs a per-alert time check, so more code.

## 2026-11-19 — 11

/model (run directly in Claude Code, not sent to Claude) — output: "Set model to `Opus 5.5` and saved as your default for new sessions with `high` effort"

/cartographer

### Settings changes

- **Model:** Haiku 5.5 (`claude-haiku-5-5`) → **Opus 5.5** (`claude-opus-5-5`). Saved as default for new sessions.
- **Effort:** max (session only) → **high**, saved as default for new sessions.

## 2026-11-19 — 12

Fix those!

### Questions — round 1 (what to fix)

**"Fix those" could mean several open items from the map and the review. Which should I fix?** (multi-select)
- **✔ Spec drift (Recommended)** — Update the spec to match the code: cron lock path ~/poll_events.lock, and failed sends retry every run regardless of matching. Docs only, no code change.
- **✔ Slack + admin gotchas** — send_slack rechecks the hooks.slack.com prefix and refuses redirects (ORM writes can't bypass the SSRF guard); admin also caps alert descriptions at 2000 chars.
- **✔ Zero-channel alerts** — Alert form requires at least one channel, so an alert can't silently never notify. Overrides the earlier carried 'user error' reject.
- **✔ Deployment hardening** — DJANGO_CSRF_TRUSTED_ORIGINS env var (forms work behind an HTTPS proxy) and STATIC_ROOT + collectstatic in README (styled admin with DEBUG off).

## 2026-11-19 — 13

/bmad-build-auto _bmad-output/implementation-artifacts/spec-world-event-alerts.md

## 2026-11-19 — 14

/review-report the whole project

## 2026-11-19 — 15

Commit both!

## 2026-11-19 — 16

Make a docs/PLAN.md from _bmad-output/implementation-artifacts/spec-world-event-alerts.md

## 2026-11-19 — 17

Make a docs/DECISIONS.md based on every doc!

## 2026-11-19 — 18

Do not ignore reports/review/, it will be commited!

## 2026-11-19 — 19

Yes, and make some screenshots about the running app!

## 2026-11-19 — 20

Extend README with more info based on docs! Add MIT license to the repo! Log before commit this time! Last thing, push everything!
