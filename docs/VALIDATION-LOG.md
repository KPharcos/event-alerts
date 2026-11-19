# Validation log

Claude responses worth checking (they report results, make claims about what was built or
changed, or carry risks), verbatim, each followed by the user's next prompt. Oldest first.
Prompt numbers match `docs/PROMPTS.md`.

---

## 2026-11-19 — after prompt 2 ("Install BMAD")

### Response

BMAD v6.12.4 now installed in project. I ran `npx bmad-method@latest install --directory . --modules bmm --tools claude-code --yes`, so I picked defaults for you:
- **Modules:** core + BMad Method (`bmm`). Optional modules not added: BMB, CIS, GDS, TEA.
- **Tool:** Claude Code. It installed 29 skills into `.claude/skills`.
- **Files:** framework is in `_bmad/`, and BMAD will write its output to `_bmad-output/`.

Prompt also logged in `docs/PROMPTS.md`.

Next step: restart Claude Code so the new skills load, then run the `bmad-help` skill to start. Installer also offered a v7 beta preview. I skipped it and stayed on stable v6.

Not checked: did not open the installed skill files.

### Follow-up prompt (3)

/bmad-build-auto "We want users to be able to set up alerts so they get notified when
something important happens in the world — like breaking news, market
movements, natural disasters, that kind of thing. Should work for both email
and Slack. Make it flexible enough that we can add more channels later.
We need an admin view too." If any question arises, ask me interactively!

---

## 2026-11-19 — after prompt 3 (bmad-build-auto: world event alerts)

### Response

The alerts app is built and all 28 tests pass. `check` and `makemigrations --check` are clean too. Full record is in `_bmad-output/implementation-artifacts/spec-world-event-alerts.md`.

**What it does**
- **Stack:** Django 6.1 with SQLite, managed by `uv`.
- **Events:** a `poll_events` command, run by cron every 5 minutes, pulls from three free feeds:
  - USGS earthquakes
  - GDACS (floods, cyclones, volcanoes, droughts, fires)
  - BBC World RSS for news
- **Matching:** users write alerts in plain words, like "big quake hits Japan". One Claude Haiku 5.5 call per new event decides which alerts match.
- **Channels:** email and Slack webhook. A new channel is one send function plus one registry entry in `alerts/channels.py`.
- **Admin:** Django admin at `/admin/`. Admin creates users, alerts, channels and manual events, and sees the delivery log.
- **Users:** log in at `/accounts/login/` and manage only their own alerts.
- **Failed sends** are retried on the next runs, 3 attempts in total.

**Your decisions**
- **Stooq market feed:** dead, so dropped. There is no market feed; admin can add market events by hand.
- **More disaster types:** you chose to add GDACS. I checked it live: 214 non-earthquake items.
- **Retries:** auto-retry up to 3 attempts.

**Review:** 4 reviewers raised 49 findings. I fixed 32, including 4 serious ones:
- A Claude refusal or cut-off reply sent the event into an endless retry loop, billed every 5 minutes.
- A permanent 400 error from Claude was also retried forever.
- With no `DJANGO_SECRET_KEY` set, the app fell back to a public key, which lets attackers forge logins.
- Feed text with `<!channel>` would ping a whole Slack channel.

I rejected the other 17: 6 were design choices you made in your answers, 11 were small and unlikely to happen. Reasons are in the spec's triage log.

**Where I departed from the BMAD workflow**
- It is meant to run without questions; I asked you because you told me to.
- The harness ran subagents in the background instead of blocking.
- I applied your scope changes as patches instead of having the code regenerated from the spec.
- The spec recommends a second review, because the retry loop and GDACS were written after the review.

**To run it:** `uv sync`, then `migrate`, then `createsuperuser`. Set `ANTHROPIC_API_KEY` and the SMTP variables (see `README.md`), and add the cron line from the README.

Not checked: the matching prompt has never run against the real Claude API (tests mock it), and SMTP has not been tried against a real server. There is no git repo, so nothing was committed.

Risk: the first poll stores about 250 events, which means about 250 Haiku calls once, if any alerts are active.

### Follow-up prompt (4)

You should save all the prompts, the interactive questions with options and answers!

---

## 2026-11-19 — after prompt 4 (log questions and answers)

### Response

Done. `docs/PROMPTS.md` now has all 4 prompts, plus all 11 questions I asked across 4 rounds. Each question lists every option with its description, and the one you picked is marked ✔. This message is logged as prompt 4.

Memory rule updated too, so from now on every question and your answer gets logged right after you answer.

Wording of the questions and options is copied from the calls I made this session.

### Follow-up prompt (5)

Save every worth checking response and the follow up prompt in docs/VALIDATION-LOG.md (like this one: "The alerts app is built and...")

---

## 2026-11-19 — after prompt 6 (first commit + push)

### Response

I pushed the project to https://github.com/KPharcos/event-alerts. It's a public repo on branch `main` with one commit, `f798f17`.

- **What's in it:** 35 files: the app code, tests, migrations, README, `uv.lock`, the spec in `_bmad-output/`, and both log files in `docs/`.
- **Left out by the new `.gitignore`:** the BMAD framework (`_bmad/`, `.claude/`), `.venv/`, `db.sqlite3` and any `.env` files.
- **Secrets check:** I searched the committed files for API keys, tokens and your email. Nothing real turned up; the only match was the fake Slack URL in `alerts/tests.py`.
- **Logs:** this prompt and your three answers are in `docs/PROMPTS.md`, which made it into the commit.

The new entry for this reply in `docs/VALIDATION-LOG.md` was written after the push, so it isn't in the commit yet. Say if you want me to commit and push it. I haven't looked at the repo page on GitHub. Anyone who clones it has to run `npx bmad-method install` to get the BMAD skills back.

### Follow-up prompt (7)

/model (run directly in Claude Code) — set model to Sonnet 5.5, effort xhigh, saved as default.

Please log the model and effort changes into docs/PROMPTS.md

---

## 2026-11-19 — after prompt 7 (log model and effort change)

### Response

Logged the model and effort change in `docs/PROMPTS.md` as prompt 7. It's under a `### Settings changes` heading:
- **Model:** Opus 5.5 → Sonnet 5.5, saved as default.
- **Effort:** xhigh, saved as default. The old effort level wasn't shown in the session, so I didn't record one.

I also fixed the prompt 6 entry in `docs/VALIDATION-LOG.md`. It now has my actual last reply word for word, and your prompt 7 as the follow-up. And I saved a memory rule so later `/model` changes get logged the same way.

Nothing is committed yet: the two doc edits and the earlier log entry are still local. Say if you want a second commit and push.

### Follow-up prompt (8)

/bmad-build-auto _bmad-output/implementation-artifacts/spec-world-event-alerts.md

---

## 2026-11-19 — after prompt 8 (bmad-build-auto: follow-up review pass)

### Response

Review pass done. Spec `done`. 34 tests pass (was 28). `check` and `makemigrations --check` clean.

54 findings, 4 reviewers: high 2, medium 9, low 34, false 9. Fixed 16 (5 real bugs + test gaps). Rejected 38. Reasons in spec triage log.

**Fixed**
- **Credit out = events lost (high).** No API credit gives HTTP 400. My old fix called all 400s permanent, so events were marked matched and gone. Now a "credit balance" 400 retries next run.
- **Prompt break-out (medium).** Alert text could close its tag and steer other users' matches. Alert and feed text now XML-escaped.
- **Deactivated users still got alerts (medium).** Poll and retry now skip them.
- **`EMAIL_USE_TLS=true` meant TLS off (medium).** SMTP login was sent in clear. Now `1`, `true`, `yes` all mean on.
- **Claude call timeout 60s (low).** SDK default is 10 min, which could stall cron.
- **6 new tests**, 3 extended, for gaps the reviewers showed: inactive alert retry, Slack lookalike URLs, one bad event not stopping the run, event text in prompt, bad RSS dates, read-only notification log.

**Rejected:** user decisions (retry design, no market feed, GDACS), unlikely cases, new features (event updates, backoff, feed hardening).

**Workflow notes**
- Reviewers ran in background again, not blocking as the workflow wants.
- Finalize step says commit. I committed locally, not pushed. Commit also holds earlier doc edits.

Not checked: new tests not mutation-checked. Credit fix matches the text "credit balance", from web reports, not official docs. Escaping changes what Haiku sees; nothing ran against the real API.
Risk: spec again recommends a follow-up review, because a high was patched.

### Follow-up prompt (9)

/model (run directly in Claude Code) — set model Haiku 5.5, saved as default; effort max, this session only.

Always log the model and effort changes into docs/PROMPTS.md

---

## 2026-11-19 — after prompt 9 (log model and effort change)

### Response

Logged as prompt 9 in `docs/PROMPTS.md`:
- **Model:** Sonnet 5.5 → Haiku 5.5, saved as default.
- **Effort:** max, this session only. Default still xhigh.

I also made the rule explicit in memory: every `/model` change gets logged, session-only ones too. The follow-up is in `docs/VALIDATION-LOG.md` under the prompt 8 entry.

Not committed. Skipped: nothing else changed. Risk: none for the logs.

### Follow-up prompt (10)

/bmad-build-auto _bmad-output/implementation-artifacts/spec-world-event-alerts.md

---

## 2026-11-19 — after prompt 10 (bmad-build-auto: follow-up review pass 3)

### Response

Pass 3 done. Spec `done`. 42 tests pass (was 34). Committed local, not pushed.

Your call applied: old events notify only last 24 h. Admin events exempt (intent: manual events match next run).

70 findings: high 5, medium 11, low 46, false 8. Patched 32 rows. Rejected 38.

Fixed:
- Every Claude API error retries, 400s too. Shared prompt rejected = all events dropped before.
- Descriptions capped 2000 chars.
- Stop matching after 3 fails in a row. Hung API no longer stalls runs for hours.
- Small: ALLOWED_HOSTS spaces, blank EMAIL_PORT, README cron env/log/lock path, legends, admin read-only matched_at.

Need your call:
- Zero-channel alerts save silent. Earlier pass said user error, carry rule kept that. I think it's a trap. Say go, I patch.
- Deployment: CSRF origins behind HTTPS proxy, STATIC_ROOT. Still rejected under carry. Matters if you deploy behind HTTPS. Say go.

Skipped: new tests not mutation-checked; matcher never run on real Claude. Risk: 400 retry — if Anthropic bills rejected requests, revisit. Follow-up review recommended again (high patched).

### Follow-up prompt (11)

/model (run directly in Claude Code) — set model Opus 5.5, effort high, both saved as default.

/cartographer

---

## 2026-11-19 — after prompt 11 (cartographer)

### Response

Map done: `docs/CODEBASE_MAP.md`. New `CLAUDE.md` points to it.

- 34 files, ~31k tokens. One Sonnet reader, I wrote the map from its report.
- Map has: architecture diagram, directory tree, module guide (models, channels, sources, matcher, poller, web, admin, config + env table), poll-run and user-flow sequence diagrams, conventions, gotchas, navigation guide (add channel, add source, change matching, etc).
- Gotchas worth knowing: retries ignore the circuit breaker; Slack guard is validation-only (ORM writes bypass it); 2000-char cap is form-only (admin can exceed); a feed source named `manual` would skip the 24 h window.

Reader found spec vs code drift: spec cron says `/tmp/poll_events.lock` (README now `~/`); spec says retries skip when matcher returned None, code retries always. Not fixed.

Not committed. Skipped: did not re-run tests (no code change). Risk: map is a snapshot; goes stale on next code change.

If cartographer helped you, consider starring: https://github.com/kingbootoshi/cartographer - please!

### Follow-up prompt (12)

Fix those!

---

## 2026-11-19 — after prompt 12 (fix spec drift, Slack/admin gotchas, zero-channel, deployment)

### Response

All four fixed. 46 tests pass (was 42). `check` and `makemigrations --check` clean. Not committed.

- **Spec drift:** spec now says `~/poll_events.lock` + log redirect, and failed sends retry every run whatever matching did. Matches code.
- **Slack:** `send_slack` rechecks `https://hooks.slack.com/` before posting and refuses redirects. ORM-written bad target now fails as `failed`, never posts.
- **Admin cap:** admin alert form = `AlertForm`, so 2000-char limit holds there too.
- **Zero-channel:** alert needs ≥1 channel, user form ("Add at least one channel, or the alert can never notify you.") and admin inline.
- **Deployment:** `DJANGO_CSRF_TRUSTED_ORIGINS` env var; `STATIC_ROOT = staticfiles/` (gitignored); README says run `collectstatic` in production.
- Spec Change Log + `docs/CODEBASE_MAP.md` updated.

Skipped: secure cookies / HSTS (would break plain-HTTP dev); not checked against a real proxy or Slack redirect. Risk: user form now shows 2 channel rows (1 required + 1 extra), was 2 optional.

### Follow-up prompt (13)

/bmad-build-auto _bmad-output/implementation-artifacts/spec-world-event-alerts.md

---

## 2026-11-19 — after prompt 13 (bmad-build-auto: follow-up review pass 4)

### Response

Pass 4 done. Spec `done`, follow-up review **not** recommended anymore (no high found) — review converged. 53 tests pass (was 46). Committed local `282839f`, not pushed. Commit also holds your prompt-12 fixes + map + CLAUDE.md.

41 findings: high 0, medium 14, low 20, false 7. Patched 18 rows, rejected 23.

Fixed:
- Admin could delete alert's only channel (Django admin sets `min_num` but not `validate_min`). Now blocked.
- Admin event with source other than exact `manual` + old date got silently dropped. Now only feed sources age out; any admin source matches.
- Always-failing event at head of queue blocked fresh news every run. Now newest first + feed summaries capped 2000 chars (likely 400 cause).
- Feed HTML stripped from summaries.
- Paused alert turned back on days later no longer re-sends stale failed notifications (retries last 24 h only).
- Old events aged out now log a count.
- Tests: `_opener` really has no-redirect handler, breaker resets after success, SMTP settings from env, + the above.

Rejected mostly carried calls: random SECRET_KEY fallback, secure cookies/HSTS (break plain HTTP), USGS bad feature, event updates, duplicate channel rows.

Skipped: nothing run against real Claude/SMTP/Slack. Risk: a permanently rejected admin event costs 1 Claude call per run forever (no attempt cap; needs migration).

### Follow-up prompt (14)

/review-report the whole project

---

## 2026-11-19 — after prompt 14 (review-report: whole project)

### Response

Report done: `reports/review/2026-11-19-world-event-alerts-the-whole-project/index.html` (open in browser). 6 chapters following one poll run → feeds → Claude matching → delivery → user pages → admin. 1401 of 1401 changed code lines shown (100%); README, docs, BMAD spec, migrations, Django boilerplate excluded with reasons.

Reader pass, 2 rounds: 15 questions answered as notes, 2 left open (no feed size cap / stdlib XML parser; GDACS fixture weekday).

Reader pass found a real bug: admin "add alert" had no user field (`AlertForm.Meta.fields` dropped it when admin reused the form in prompt 12) → saving crashed on NOT NULL. Fixed: `AlertAdmin.fields` includes `user`; new admin-add test. 54 tests pass. Fix is uncommitted; the report covers HEAD and says so in the admin note.

Skipped: did not commit. Renderer added `reports/review/` to `.gitignore` (uncommitted too). Risk: report is a snapshot of HEAD, misses the admin fix diff.

### Follow-up prompt (15)

Commit both!

---

## 2026-11-19 — after prompt 15 (commit admin fix + gitignore)

### Response

Committed `20de65a`: admin user-field fix + its test, `.gitignore` gets `reports/review/`, and the two log files. Tree clean.

Not pushed. `main` is 4 commits ahead of GitHub (pass 3, pass 4 + prompt-12 fixes, this one, and the earlier pass-2 commit). Say "push" to send them.

### Follow-up prompt (16)

Make a docs/PLAN.md from _bmad-output/implementation-artifacts/spec-world-event-alerts.md

---

## 2026-11-19 — after prompt 16 (docs/PLAN.md)

### Response

Wrote `docs/PLAN.md` from the spec. Not committed.

It merges the original plan with every later decision, so it shows the app as it is now:
- Goal, approach, scope in/out.
- Decisions table: 15 rows, who made each (owner vs triage) and when.
- Architecture diagram (mermaid), links to `CODEBASE_MAP.md` and `PROMPTS.md`.
- Work items (all done), acceptance criteria with status, edge-case matrix with the test for each row (13 rows; I added OLD_EVENT and CLAUDE_DOWN from later decisions).
- Configuration table, cron line, verification commands, review history (4 passes + review report).
- Open items: never run against real Claude/SMTP/Slack, no market feed, 4 commits unpushed, production hardening left out, accepted limits.

Triage logs not copied (they stay in the spec). Test names in the plan checked against `alerts/tests.py`.

Skipped: did not commit. Risk: plan is a snapshot; the spec stays the source of truth.

### Follow-up prompt (17)

Make a docs/DECISIONS.md based on every doc!

---

## 2026-11-19 — after prompt 17 (docs/DECISIONS.md)

### Response

Wrote `docs/DECISIONS.md`, built from PROMPTS, VALIDATION-LOG, PLAN, CODEBASE_MAP, README and the BMAD spec (change log, design notes, all 4 triage logs). Not committed.

- Index table, then one entry per decision: context, options offered, choice, consequences, who decided (owner / triage / design), status (accepted / superseded / rejected).
- 50 decisions in 7 groups: product (P1–P9), architecture (A1–A9), matching rules (T1–T9), security (S1–S10), rejected features (R1–R7), process & repo (W1–W9), docs.
- Superseded chains made explicit: 400 handling T1 → T2 → T3; zero-channel T9 → P9; "deployment out of scope" → S7.
- Flags what was decided by triage, not by you (T3 400-retry, T4 breaker, T6–T8), and the one carried rejection with a false premise (S4).

Skipped: did not commit. Risk: hand-merged from many docs; spec stays the source of truth if they disagree.

### Follow-up prompt (18)

Do not ignore reports/review/, it will be commited!

---

## 2026-11-19 — after prompt 18 (stop ignoring reports/review/)

### Response

`reports/review/` is no longer ignored. `git check-ignore` confirms it, and `reports/` now shows as untracked.

The review-report renderer re-adds `reports/review/` to `.gitignore` on every render unless that line already exists. So `.gitignore` keeps the line and un-ignores the folder right after it with `!reports/review/`, plus a comment explaining why. Saved as a memory rule.

Not committed. Pending: `.gitignore`, `docs/PLAN.md`, `docs/DECISIONS.md`, the report folder, log updates.

Risk: the report was rendered before `20de65a`, so it shows the old admin code. It needs a re-render to show the admin fix in the diff.

### Follow-up prompt (19)

Yes, and make some screenshots about the running app!

---

## 2026-11-19 — after prompt 19 (re-render report + app screenshots)

### Response

Done and committed locally (not pushed).

- **Report re-rendered** against HEAD, so the admin fix (`fields` with `user`, `admin.py` line 29) is now in the diff with its own note and test. `reports/review/` stays tracked.
- **9 screenshots** in `docs/screenshots/`, linked from a new README "Screenshots" section:
  - user side: login, a user's alert list, new alert form, Slack URL rejected
  - admin side: home, events, read-only notification log, alerts, alert with its channels (owner field visible, which proves the fix)
- **How they were made:**
  - Dev server on a scratch database, so the repo's `db.sqlite3` is untouched.
  - 36 real events from the live USGS, BBC and GDACS feeds, plus one manual market event.
  - Demo users and alerts use `example.com` addresses.
  - Headless Chrome driven from a small Node script.
  - The notifications were staged with matching alerts (Chile quake, Australian fire, Brent oil); Claude was not called, and the README says so.

Skipped: no live Claude/SMTP/Slack. Risk: user pages are plain unstyled HTML, which the screenshots show as-is; GitHub is now 5 commits behind.

### Follow-up prompt (20)

Extend README with more info based on docs! Add MIT license to the repo! Log before commit this time! Last thing, push everything!

---

## 2026-11-19 — after prompt 20 (README, MIT license, push)

### Response

Done. README extended, MIT license added, everything committed and pushed to https://github.com/KPharcos/event-alerts. This log entry was written before the commit, so the tree is clean.

- **README** (from PLAN, DECISIONS, CODEBASE_MAP, spec), new sections:
  - How it works (mermaid diagram plus the 5 steps)
  - Features
  - Status (54 tests, 4 review passes, never run against real Claude/SMTP/Slack)
  - Security notes
  - Known limits
  - Project docs (index of every doc and the review report)
  - How this was built (BMAD + Claude Code)
  - License
- **LICENSE:** MIT, `Copyright (c) 2026 KPharcos`. I used your GitHub handle, not your real name; change it if you want. `pyproject.toml` declares `license = "MIT"`, and `uv lock --check` still passes.
- **Push:** `main` was 5 commits behind GitHub; now 6 commits are pushed (5 + this one).

Skipped: did not re-run screenshots or the report (no code change). Risk: GitHub shows the review report as raw HTML; download it to view it.
