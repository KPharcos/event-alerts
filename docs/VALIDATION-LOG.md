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
