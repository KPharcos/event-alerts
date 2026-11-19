# Decision log

Every decision behind the world event alerts app, collected from all project docs:
[`PROMPTS.md`](PROMPTS.md) (the owner's prompts and every question with its options),
[`VALIDATION-LOG.md`](VALIDATION-LOG.md) (Claude's reports), [`PLAN.md`](PLAN.md),
[`CODEBASE_MAP.md`](CODEBASE_MAP.md), the [`README`](../README.md), and the BMAD spec
[`spec-world-event-alerts.md`](../_bmad-output/implementation-artifacts/spec-world-event-alerts.md)
(change log, design notes, review triage logs).

**Decided by:**
- **Owner**: answered by you, usually through an interactive question.
- **Triage**: made by Claude while sorting review findings, under the BMAD workflow rules.
- **Design**: made when the spec or code was written.

**Status:**
- **Accepted**: in force today.
- **Superseded**: replaced by a later decision.
- **Rejected**: considered and deliberately not done.

All dates are 2026-11-19.

## Index

| ID | Decision | By | Status |
|----|----------|----|--------|
| **Product** | | | |
| P1 | Free-text alerts matched by AI | Owner | Accepted |
| P2 | Free public feeds; admins can add events by hand | Owner | Accepted |
| P3 | Admin creates users; no sign-up | Owner | Accepted |
| P4 | Send immediately per matching event; no digest | Owner | Accepted |
| P5 | No market feed (Stooq dead); market events by hand | Owner | Accepted |
| P6 | Add GDACS for non-earthquake disasters | Owner | Accepted |
| P7 | Retry failed sends automatically, at most 3 attempts | Owner | Accepted |
| P8 | Only feed events from the last 24 h notify | Owner | Accepted |
| P9 | Every alert needs at least one channel | Owner | Accepted (supersedes T9) |
| **Architecture** | | | |
| A1 | Django + SQLite, managed with uv | Owner | Accepted |
| A2 | Stock Django admin as the admin view | Owner | Accepted |
| A3 | Claude Haiku 5.5 as the matcher | Owner | Accepted |
| A4 | Slack via an incoming webhook URL per alert | Owner | Accepted |
| A5 | One cron command, no queue; `flock` against overlap | Design | Accepted |
| A6 | Registries as extension points: `SOURCES`, `CHANNELS` | Design | Accepted |
| A7 | One Claude call per event with all active alerts, structured output | Design | Accepted (known limit) |
| A8 | Django 6.1 `MAILERS`; console mail without `EMAIL_HOST` | Design | Accepted |
| A9 | Notification row written after the send | Design | Accepted (known limit) |
| **Matching and polling rules** | | | |
| T1 | A 400 from Claude is permanent: mark done, send nothing | Triage, pass 1 | Superseded by T3 |
| T2 | Retry a 400 only when it says "credit balance" | Triage, pass 2 | Superseded by T3 |
| T3 | Every Claude API error, 400 included, retries next run | Triage, pass 3 | Accepted |
| T4 | Stop matching after 3 failures in a row (circuit breaker) | Triage, pass 3 | Accepted |
| T5 | Refusals and unparseable output: mark done, send nothing | Triage, pass 1 | Accepted |
| T6 | Only `SOURCES` events age out; admin events of any source always match | Triage, pass 4 | Accepted (refines P8) |
| T7 | Match newest first | Triage, pass 4 | Accepted |
| T8 | Retries only for notifications from the last 24 h | Triage, pass 4 | Accepted |
| T9 | Zero-channel alerts are user error, left alone | Triage, pass 1 | Superseded by P9 |
| **Security and robustness** | | | |
| S1 | Random `SECRET_KEY` fallback instead of a public default | Triage, pass 1 | Accepted |
| S2 | Untrusted text: prompt says "data only", XML-escaped | Triage, passes 1–2 | Accepted |
| S3 | Slack: host prefix check, escaping, recheck at send, no redirects | Triage + Owner | Accepted |
| S4 | Alert descriptions capped at 2000 characters (user form and admin) | Triage + Owner | Accepted |
| S5 | Feed summaries stripped of HTML, capped at 2000 characters | Triage, pass 4 | Accepted |
| S6 | Deactivated users and paused alerts get no sends or retries | Triage, pass 2 | Accepted |
| S7 | `DJANGO_CSRF_TRUSTED_ORIGINS` and `STATIC_ROOT` | Owner | Accepted (supersedes "deployment out of scope") |
| S8 | Secure cookies, HSTS, SSL redirect | Claude, scoped with the owner | Rejected |
| S9 | Feed size cap, `defusedxml` | Triage | Rejected |
| S10 | Admin alert form keeps an owner field | Review report | Accepted (bug fix) |
| **Rejected features** | | | |
| R1 | Backoff or an admin "re-send" button | Owner (by choosing P7) | Rejected |
| R2 | Re-evaluate updated events (GDACS escalation, USGS revisions) | Triage | Rejected |
| R3 | Attempt cap for events Claude always rejects | Triage | Rejected |
| R4 | Unique constraint on duplicate channel rows | Triage | Rejected |
| R5 | Cap on matches per event | Triage | Rejected |
| R6 | Email ownership confirmation, unsubscribe header | Triage | Rejected |
| R7 | Pending-state redesign for the crash window | Triage | Rejected |
| **Process and repository** | | | |
| W1 | Install BMAD v6.12.4 (core + bmm, Claude Code) with defaults | Claude, per prompt | Accepted |
| W2 | Build with `bmad-build-auto`, asking the owner interactively | Owner | Accepted |
| W3 | Log every prompt, question, answer and model change | Owner | Accepted |
| W4 | Log every checkable response with its follow-up prompt | Owner | Accepted |
| W5 | GitHub repo `KPharcos/event-alerts`, public | Owner | Accepted |
| W6 | Commit only the BMAD spec, not the framework | Owner | Accepted |
| W7 | Workflow finalize steps commit locally; push only when asked | Claude | Accepted |
| W8 | Apply the BMAD carry rule, but flag weak carried calls | Claude | Accepted |
| W9 | Model and effort changes | Owner | Accepted (log only) |

---

## Product

### P1 — Free-text alerts matched by AI
- **Context:** how a user defines an alert (planning, round 1).
- **Options:**
  - category + keywords + minimum severity (recommended)
  - category only
  - free text matched by AI
- **Chosen:** free text, AI-matched. For example: "tell me if a big quake hits Japan".
- **Consequences:**
  - It needs a Claude API key and costs one call per new event (A7).
  - The intent forbids any keyword or category pre-filter in front of the matcher.

### P2 — Free public feeds; admins can add events by hand
- **Context:** where world events come from (round 1).
- **Options:**
  - free public feeds (recommended)
  - admin entry and webhook ingest only
  - paid APIs with keys
- **Chosen:** free feeds behind a pluggable source interface, plus manual events in admin.
- **Consequences:** USGS earthquakes (the M4.5+ day feed), BBC World RSS, and later GDACS (P6). No API keys needed.

### P3 — Admin creates users; no sign-up
- **Context:** how users get accounts (round 2).
- **Options:** self sign-up and login (recommended), or admin creates users.
- **Chosen:** admin creates users.
- **Consequences:**
  - No public sign-up page.
  - Several later triage calls lean on "accounts are admin-created", e.g. R6.

### P4 — Send immediately per matching event; no digest
- **Context:** when notifications go out (round 2).
- **Options:** immediately (recommended), or an hourly or daily digest.
- **Chosen:** immediately.
- **Consequences:**
  - A broad alert can send many messages.
  - Digests and per-alert caps were later rejected on this basis.

### P5 — No market feed; market events by hand
- **Context:** the planned Stooq market feed turned out dead (404 and a bot check) during implementation (round 3).
- **Options:**
  - Finnhub with a free key (recommended)
  - Yahoo's unofficial endpoint
  - Alpha Vantage with a free key
  - drop the market feed for now
- **Chosen:** drop it.
- **Consequences:**
  - Market events come only from admin entry or as BBC news.
  - The alert form says so in its help text.
  - Open item in `PLAN.md`.

### P6 — Add GDACS for non-earthquake disasters
- **Context:** the intent-alignment reviewer noted that disasters were earthquakes only (round 4).
- **Options:** add GDACS (recommended), or earthquakes only for now.
- **Chosen:** add GDACS: floods, cyclones, volcanoes, droughts and wildfires.
- **Consequences:**
  - GDACS earthquakes (guids starting `EQ`) are dropped because USGS covers them.
  - The live feed was checked: 214 non-earthquake items.

### P7 — Retry failed sends automatically, at most 3 attempts
- **Context:** a failed Slack or SMTP send was logged and never retried, so the alert was lost (round 4).
- **Options:**
  - auto-retry on the next runs, max 3 tries (recommended)
  - an admin "Resend" action only
  - keep as is
- **Chosen:** auto-retry.
- **Consequences:**
  - New `Notification.attempts` field (migration 0002).
  - Retries run every 5 minutes, so a long outage still loses the send. Backoff was later rejected (R1).

### P8 — Only feed events from the last 24 h notify
- **Context:** the first poll stores about 250 existing events, and a new alert would also match events from before it was saved (review pass 3).
- **Options:**
  - last 24 hours only (recommended)
  - send everything unmatched (the behavior at the time)
  - only events after the alert was saved
- **Chosen:** last 24 hours only.
- **Consequences:**
  - Older feed events are marked done without a Claude call or a send.
  - Refined by T6 and T8.

### P9 — Every alert needs at least one channel
- **Context:** an alert without channels costs Claude calls and can never notify. Pass 1 had rejected this as user error (T9), and the carry rule kept that rejection until the owner chose otherwise (prompt 12, "Fix those!").
- **Chosen:** require at least one channel in the user form and the admin inline.
- **Consequences:**
  - The admin inline needed `validate_min` set explicitly (pass 4).
  - The message reads: "Add at least one channel, or the alert can never notify you."

## Architecture

### A1 — Django + SQLite, managed with uv
- **Context:** the project was empty (round 1).
- **Options:**
  - Django + SQLite (recommended)
  - FastAPI + SQLite
  - Node/TypeScript
- **Chosen:** Django + SQLite. User accounts, admin, email and management commands come built in.
- **Consequences:**
  - Python 3.12+ and Django 6.1.
  - Runtime dependencies: `anthropic` and `pydantic` only.

### A2 — Stock Django admin as the admin view
- **Context:** round 2.
- **Options:** Django admin (recommended), or a custom dashboard.
- **Chosen:** Django admin.
- **Consequences:**
  - Admins manage users, alerts, channels and manual events there.
  - The notification log is read-only (add, change and delete disabled).
  - `matched_at` is read-only.

### A3 — Claude Haiku 5.5 as the matcher
- **Context:** round 2.
- **Options:**
  - Haiku 5.5 (recommended)
  - Sonnet 5.5
  - Opus 5.5
- **Chosen:** Haiku 5.5 (`claude-haiku-5-5`), the cheapest and fast enough for yes/no matching.
- **Consequences:** the model is set by `ALERT_MATCH_MODEL`. The code passes no temperature, thinking setting or prefill.

### A4 — Slack via an incoming webhook URL per alert
- **Context:** round 1.
- **Options:** a webhook URL per alert (recommended), or a Slack app with OAuth.
- **Chosen:** webhook.
- **Consequences:**
  - No Slack app or secrets to manage.
  - The URL is user input, which needs the SSRF guard in S3.

### A5 — One cron command, no queue
- **Source:** spec.
- **Choice:** `poll_events` runs every 5 minutes as `flock -n ~/poll_events.lock …`. It logs to `~/poll_events.log`.
- **Why:** the intent rules out Celery and queues.
- **Consequences:**
  - `flock` prevents overlapping runs.
  - Cron doesn't load the shell environment, so the README explains where the env vars go.
  - The lock moved from `/tmp` to `~` in pass 3, after the reviewers raised the shared-`/tmp` risk.

### A6 — Registries as extension points
- **Source:** spec and intent.
- **Choice:**
  - `SOURCES` maps a feed name to a fetcher.
  - `CHANNELS` maps a key to `Channel(label, validate, send)`.
- **Consequences:**
  - A new channel is one registry entry plus a choices-only migration.
  - A new source is one function plus one entry.

### A7 — One Claude call per event with all active alerts, structured output
- **Source:** intent and design notes.
- **Choice:**
  - `messages.parse(output_format=MatchResult)` returns `alert_ids`.
  - Those ids are intersected with the active set.
  - The client times out after 60 s instead of the SDK's 10 minutes.
- **Known limit:** the prompt grows with the number of alerts. This is marked `# shortcut: … batch when alerts exceed a few hundred`. `max_tokens=1024` fits a few hundred ids.

### A8 — Django 6.1 `MAILERS`
- **Source:** design.
- **Choice:** SMTP when `EMAIL_HOST` is set, the console backend otherwise.
- **Consequences:**
  - Console mail still counts as `sent`; the README documents this.
  - `EMAIL_USE_TLS` accepts `1`, `true` or `yes`. That was fixed in pass 2: `true` used to turn TLS off.
  - A blank `EMAIL_PORT` falls back to 587.

### A9 — Notification row written after the send
- **Source:** design. Reconsidered in passes 1–4.
- **Choice:** keep the order. An existence check plus a unique constraint stop duplicates.
- **Known limit:** a crash between the send and the record can resend on the next run. A pending-state redesign was rejected (R7). The README states this.

## Matching and polling rules

### T1 — A 400 from Claude is permanent *(superseded by T3)*
- **Pass 1:** a reviewer found a permanent 400 retried and billed forever.
- **Chosen:** mark the event done and send nothing.

### T2 — Retry a 400 only when it says "credit balance" *(superseded by T3)*
- **Pass 2:** an exhausted API credit returns a 400, so under T1 every event would have been silently lost.
- **Chosen:** a string check, based on web reports rather than official docs.

### T3 — Every Claude API error retries next run
- **Pass 3:** a 400 can come from the shared alert prompt, so T1 would drop every event for every user.
- **Chosen:**
  - Every `anthropic.APIError` leaves the event unmatched.
  - The string check from T2 is removed.
  - This matches the spec's CLAUDE_ERROR row.
- **Cost accepted:** a permanently bad event costs one failed call per run.
- **Flag:** revisit if Anthropic bills rejected requests.
- **Note:** this was made in triage, not by the owner, and recorded in the spec change log.

### T4 — Circuit breaker
- **Pass 3:** a hanging API could keep a run going for hours while `flock` skipped every cron run.
- **Chosen:** stop matching after 3 failures in a row; the rest waits for the next run.
- **Details:**
  - A success resets the count.
  - Unexpected exceptions count as failures.
  - Worst case is about 9 minutes per run.

### T5 — Refusals and unparseable output: mark done, send nothing
- **Pass 1:** `parse` raises `pydantic.ValidationError` on non-JSON text. This was checked in the SDK source.
- **Before:** a refusal or a cut-off reply looped forever.
- **Chosen:** treat it like the spec's REFUSAL row.

### T6 — Only `SOURCES` events age out
- **Pass 4:** the first version exempted only the literal source `manual`. An admin event with any other source and an old date was silently dropped.
- **Chosen:** the 24 h window applies only to sources listed in `SOURCES`. A warning logs the count.

### T7 — Match newest first
- **Pass 4:** three always-failing old events at the head of the queue blocked fresh news on every run.
- **Chosen:** order by `-occurred_at`.

### T8 — Retries only within 24 h
- **Pass 4:** a paused alert switched back on days later would re-send stale failed notifications.
- **Chosen:** retries only for notifications created in the last 24 h.

### T9 — Zero-channel alerts are user error *(superseded by P9)*
- **Pass 1:** rejected as low: "user error only".
- **Later:** carried through passes 2–3 by the carry rule, then overridden by the owner.

## Security and robustness

### S1 — Random `SECRET_KEY` fallback
- **Pass 1:** with no `DJANGO_SECRET_KEY`, the app used a public key, which would let attackers forge logins.
- **Chosen:** use a random key per process.
- **Rejected alternative:** refusing to start. That would also stop the cron poller.
- **Consequences:** sessions reset on restart and differ between workers. The README says to set the key in production.

### S2 — Untrusted text
- **Pass 1:** feed text and alert descriptions are declared untrusted in the system prompt, and alerts sit in `<alert id>` tags.
- **Pass 2:** `xml.sax.saxutils.escape` was added for descriptions and for event title, summary and URL. This stops one user's alert from forging another's tag.

### S3 — Slack hardening
- **Escaping (pass 1):** `& < >` are escaped, so feed text can't ping `<!channel>` or spoof links.
- **Prefix check (from the start):** targets must start with `https://hooks.slack.com/`. The trailing slash defeats look-alike hosts.
- **At send time (owner, prompt 12):** the check is repeated before posting, and redirects are refused.

### S4 — Description cap 2000 characters
- **Pass 3 (triage):**
  - Every description goes into every prompt, so one huge description could make Claude reject all calls.
  - The cap lives in the form only, so no migration is needed.
  - Pass 2 had rejected this on the wrong premise ("users are admin-created"). In fact users write their own alerts.
- **Owner, prompt 12:** admin uses the same form.

### S5 — Feed summaries
- **Pass 4:** `strip_tags` plus a 2000-character cap. Feed HTML no longer reaches prompts, email or Slack, and a huge item can't cause a 400 on every run.

### S6 — Inactive users and alerts
- **Pass 2:** alerts belonging to deactivated users were still notified.
- **Chosen:** the matching query and the retry query both require an active alert and an active user.

### S7 — CSRF trusted origins and `STATIC_ROOT`
- **Before:** passes 1–3 rejected these as "deployment out of scope" via the carry rule. The triage rule only allows that reason when the intent excludes the item, and it didn't, so Claude flagged it.
- **Owner, prompt 12:** add `DJANGO_CSRF_TRUSTED_ORIGINS`, so forms work behind an HTTPS proxy, and `STATIC_ROOT` with a `collectstatic` step.

### S8 — Secure cookies, HSTS, SSL redirect *(rejected)*
- **Reason:** turning them on by default would break plain-HTTP setups.
- **Status:** left as a deployment-specific choice. Open item in `PLAN.md`.

### S9 — Feed size cap and `defusedxml` *(rejected)*
- **Reason:** the feeds are fixed, well-known publishers, and `defusedxml` would add a dependency the intent rules out.
- **Status:** open point in the review report.

### S10 — Admin alert form keeps an owner field
- **Review report, reader pass:** reusing `AlertForm` in admin (S4) dropped the `user` field, so "add alert" crashed.
- **Fix:** `AlertAdmin.fields` includes `user`. The user-facing form still has no owner field, so a user can't move an alert to someone else. Commit `20de65a`.

## Rejected features

| ID | Proposal | Why not |
|----|----------|---------|
| R1 | Backoff, admin "re-send" | The owner chose automatic retries on the next runs (P7) over the "Resend" option |
| R2 | Re-match updated events | A new feature; changing the dedupe key would re-notify existing events |
| R3 | Attempt cap for permanently failing admin events | Needs a migration; newest-first ordering (T7) already stops them blocking fresh news |
| R4 | Unique (alert, channel, target) | User error; the constraint adds surface |
| R5 | Cap matches per event | Would cut legitimate multi-user matches; needs hostile feed text to matter |
| R6 | Email ownership confirmation, unsubscribe | Accounts are admin-created (P3); confirmation is a new flow |
| R7 | Pending state before sending | More than a direct fix; the crash window is rare and documented (A9) |

Other carried rejections:
- A malformed USGS feature drops that source's run.
- Atom and RDF feeds are not supported (a warning is logged).
- A per-event cost cap: the cost is documented as a shortcut.

## Process and repository

### W1 — BMAD install
- **Prompt 2 ("Install BMAD"):** Claude picked the defaults: BMAD v6.12.4, core plus the BMad Method module (`bmm`), and the Claude Code tool.
- **Skipped:** the v7 beta preview, to stay on stable v6.

### W2 — Build with `bmad-build-auto`, interactively
- **Prompt 3:** "If any question arises, ask me interactively!"
- **Recorded deviations from the unattended workflow:**
  - Questions were asked.
  - Subagents ran in the background.
  - Owner scope changes were applied as patches, not by re-deriving code from the spec.
  - In pass 3 the intent question was asked inline instead of halting with "intent gap".
  - The T3 decision was made in triage, not through a spec loopback.
- **Review passes:**

| Pass | Findings | Patched |
|------|----------|---------|
| 1 | 49 | 32 |
| 2 | 54 | 16 |
| 3 | 70 | 32 |
| 4 | 41 | 18 |

Pass 4 found no high-severity issues, so the work converged.

### W3 — Log every prompt, question, answer and model change
- **Prompts 1, 4, 7 and 9:** "Save every prompt", then "…the interactive questions with options and answers!", then "Always log the model and effort changes".
- **Where:** `docs/PROMPTS.md`, kept as a standing memory rule.

### W4 — Validation log
- **Prompt 5:** save every response worth checking, followed by the next prompt, in `docs/VALIDATION-LOG.md`.
- **Rule:** trivial replies are skipped.

### W5 — GitHub repo `KPharcos/event-alerts`, public
- **Prompt 6 options for the name:**
  - `real-world-event-alerts` (recommended)
  - `world-event-alerts`
  - `event-alerts`
- **Prompt 6 options for visibility:** public (recommended) or private.
- **Chosen:** `event-alerts`, public. Only the first commit is pushed so far.

### W6 — Commit only the BMAD spec
- **Options:**
  - commit everything (recommended)
  - only `_bmad-output` (the spec)
  - none
- **Chosen:** only the spec.
- **Consequences:** `.gitignore` excludes `_bmad/` and `.claude/`. Anyone cloning needs `npx bmad-method install`.

### W7 — Commits
- **Rule:** the BMAD finalize step commits locally (passes 2–4), and the owner asks for any other commit ("Commit both!").
- **Nothing is pushed without being asked.** `main` is ahead of GitHub.

### W8 — The carry rule
- **What it says:** findings already triaged keep their earlier verdict while the code still reads the same.
- **How it was applied:** Claude applied it in passes 3–4 and listed weak carried calls for the owner. Zero-channel alerts and deployment settings were both overridden in prompt 12.
- **Exception:** one carried rejection rested on a false premise (S4), and Claude superseded it openly.

### W9 — Model and effort changes

| Prompt | Model | Effort |
|--------|-------|--------|
| 7 | Opus 5.5 → Sonnet 5.5 (default) | xhigh (default) |
| 9 | Sonnet 5.5 → Haiku 5.5 (default) | max (this session only) |
| 11 | Haiku 5.5 → Opus 5.5 (default) | high (default) |

These change who did the work, not the app. Commit co-author lines follow the active model.

## Documentation decisions

- **`docs/CODEBASE_MAP.md` and `CLAUDE.md`:** made with Cartographer (prompt 11). One Sonnet reader covered 34 files.
- **Review report:** made with the review-report skill (prompt 14). It covers the whole project from the empty tree and has 6 chapters. It excludes the README, docs, BMAD spec, migrations and Django boilerplate, each with a reason. Two reader rounds; the generated `reports/review/` folder is gitignored.
- **`docs/PLAN.md`:** made from the spec (prompt 16). The spec stays the source of truth, and this file is the cross-document view.
