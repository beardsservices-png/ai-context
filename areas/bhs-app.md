# BHS App

The core Beard's Home Services business management app.

## Which repo is canonical

**`beardsservices-png/BHSmobileapp` is the live app.** It's what Railway deploys and what runs on the phone. All work goes here.

`beardsservices-png/beard-business-app` is **deprecated and archived** (archived 2026-08-11). Do not commit to it.

- Same git history: `BHSmobileapp` was seeded by pushing the existing local folder to a new remote on 2026-05-03, so both share every commit from `4381393` (initial, 2026-02-28) through `374a745` (2026-04-05).
- The split was the move to Railway/mobile — first divergent commit is the Railway deployment config.
- `beard-business-app` is a strict subset: zero files exist there that aren't in `BHSmobileapp`. Nothing to migrate.
- Everything after the split — Railway deploy, GPS time clock, the in-app payment/invoice module, SMS leads inbox, Retell/Bill webhook, Settings page, PDF invoice import — exists only in `BHSmobileapp`.
- The `CLAUDE.md` in `beard-business-app` is stale (February version, describes a smaller app). The one in `BHSmobileapp` is current.

## Deploying

**Pushing to `main` auto-deploys.** Both `BHSmobileapp` and `bhs-memory-server` are connected
to their GitHub repos and have been for a long time. Deployment history confirms
GitHub-triggered builds back through July using the **Dockerfile** builder.

The Dockerfile is essential: it installs Node and builds the React frontend into `dist/`.
Railpack auto-detection would ship a Python API with no frontend. The builder is now pinned in
`railway.json` (`build.builder = DOCKERFILE`) so it lives in version control.

> **Warning, learned the hard way (2026-08-11).** `railway status` reports the source of the
> *last deployment*, not the service's GitHub link. After a manual `railway up` it shows
> `repo: None`, which looks exactly like "GitHub is not connected". It is not. Do not conclude
> auto-deploy is missing from that field, and do not run `railway service source connect` to
> "fix" it -- doing so reset the builder to Railpack and introduced a deployment-approval gate
> on a setup that was already working correctly.

`railway up` still works for a manual deploy but should not be needed, and it creates
CLI-upload deployments that muddy the history.

- Project **BHS APP** -> service **BHSmobileapp** -> `bhsmobileapp-production.up.railway.app`
- `ANTHROPIC_API_KEY` is set on Railway, **not** in the local `.env`. Anything calling Claude
  cannot be tested locally.

### The local clone is not a clone

The local `BHSmobileapp` folder has an **unrelated git history** from `origin/main` -- different
root commit, no merge base. Work committed locally cannot be merged or fast-forwarded to
`origin`; it has to be ported onto a branch cut from `origin/main`. Check
`git merge-base HEAD origin/main` before assuming a push will work, and never force-push to
resolve it -- that would destroy the real history.

## Data — where it actually lives

- Live data is on a **Railway volume** (`beard-business-data`, `DB_PATH=/data/beard_business.db`).
  It is not in the repo and never was.
- `data/beard_business.db` is **not tracked** and must never be committed — real customer
  names, addresses, phone numbers. The only tracked DB is `data/schema_seed.db`: schema plus
  service catalog, verified zero rows in every customer-bearing table. It exists so a fresh
  volume comes up empty and correct rather than quietly restoring a stale snapshot.
- The local DB file is a personal working copy and is **always behind** live. Never quote
  figures from it.

## Service catalog (the toolbox)

The pricing model is modelled on homewyse: every item has a low/high range and the
**midpoint is what gets quoted**.

- `service_catalog`: **trade → subcategory → item**, 140 items across 22 trades. Each carries
  a standardized title and description, a unit, low/high/mid price, and
  **`est_hours_per_unit`**.
- `service_catalog_aliases` maps all 168 legacy InvoiceBee category strings onto items, so
  historical invoices still resolve. Verified zero unresolved both directions.
- Seeded prices are **starting figures** (`price_verified = 0`) for the Mountain Home market
  at roughly $55–85/hr — not yet Brian's real numbers. Editing a price recomputes the
  midpoint and marks it verified. Seeding is idempotent; redeploying never overwrites an edit.
- Taxonomy and seed data live in `api/service_catalog_seed.py`.

## Scope → estimate

`POST /api/estimate/from-scope` turns a plain-English scope into priced, categorized lines.

**The model never sees or returns a price.** It maps language to structure only — which
catalog item, how many units — and every dollar figure is looked up server-side from the
catalog, so a hallucinated price is not possible. Unstated quantities come back flagged
`assumed_quantity`; scope text with no catalog fit is returned in `unmatched` rather than
forced onto an unrelated item. Uses `claude-sonnet-5`.

## Callback form

Lives **in the BHS app** at `/callback/:leadId`, reached from the Leads inbox. It replaces
the print-only form that used to live on the memory server — that one had no `<form>`, no
`name` attributes and no save, so everything captured on a call became pixels in a PDF and
had to be retyped.

- Service-matched qualifying checklist, scope → priced lines, running total, expected hours
  and implied hourly rate shown before the number is quoted.
- Autosaves while typing (plus a `pagehide` beacon) — he is mid-call and will not press save.
- Drafts live in their own `lead_callbacks` table, **not** `leads.metadata`, because metadata
  is rewritten by the SMS and call webhooks and a later text would wipe out pricing.
- `POST /api/leads/<id>/create-job` creates the job and populates **`leads.job_id`** — a
  column that existed since the table was created with nothing ever writing to it. That
  single missing link is why a lead could reach a customer but never the job it became, and
  why texts during a job had nowhere to land. It also claims the SMS thread onto the job.

## Profitability — the open thread

The point of tying hours to services: *"if we don't assign time to service being performed,
how do we know if I'm making money?"*

- `time_entries.service_id` and `services_performed.catalog_id` / `est_hours` now exist, so
  estimate-vs-actual is answerable **per service** rather than per job. Historical rows are
  not yet populated.
- Only **12 jobs** have both logged hours and billed labor. Their effective rates run
  **$28/hr to $122/hr** — a 4x spread.
- **62 orphan time entries / 209.8 hours** have no `job_id`. They cluster into **15 blocks**
  (top 5 = 86% of hours). Date alone cannot resolve them — every block has 2–4 candidates
  within days. `timeline_visits` (GPS, customer already resolved, `job_id` empty) is the
  strongest tiebreaker. Calibrated on 358 known-good links, median lag work→invoice is
  **−3 days**: the invoice usually *precedes* the work.
- 44 jobs from 2023 have billed labor and zero hours (pre-BusyBusy) — unrecoverable, exclude
  from $/hr math.

## SMS — one receiver, and machine traffic

`BHSmobileapp` is the **only** SMS receiver. `SMS-Extractor_BHS` was a complete duplicate that
received nothing but Railway health checks; archived and stopped 2026-08-11. Do not merge its
`claude/callback-form-estimate-flow-elhdaw` branch — that logic is already in the app.

Brian cannot filter marketing/OTP at the handset (the forwarder has no idea what a business
text looks like), so the app decides. Short codes (3–6 digits), alphanumeric sender IDs and
OTP/marketing patterns get `status='spam'` with a reason, visible under the **Spam** tab with a
"Not spam" button. A known customer always beats the heuristic. Nothing is dropped — a
wrongly-filtered customer must stay findable.

Watch out: `POST /sms` previously had **two** handlers registered. Flask matched the earlier
rule, so the entire threading/ntfy block was unreachable and `sms_leads` was never written to.
Fixed; the dead handler now lives at `/sms/legacy-thread`.

## Bill's live knowledge

`GET /api/customer-brief?phone=` on the BHS app returns current state as structured fields plus
a **speakable prose block** (Retell injects dynamic variables as text). ~220ms live.

- `bhs-memory-server` `/inbound` calls it at call start, budgeted 2.5s with an AbortController;
  any failure degrades to the old thin context rather than costing the greeting. It also now
  handles a caller the memory server has never seen but the business has — a customer who has
  only ever texted gets greeted by name.
- `POST /lookup` on the memory server is the mid-call version. **Requires a custom function
  pointing at it to be added in the Retell dashboard** — not configurable from code. Everything
  else works without it.

**Financial boundary, deliberate and structural.** Bill gets the invoice *including the agreed
amount* — it exists the moment the customer approves the work, so it is the record of the job
and its terms, and the customer already knows that number. Bill never gets payment history or
balances: the endpoint **never queries the `payments` table**, so there is no balance to leak
because none is computed. Nothing financial is written into the memory server's `callers`
record either. Brian's rule: *"the other homeowners won't like an AI knowing financial
records."*

## Stack

- Python / SQLite, hosted on Railway, source in GitHub org `beardsservices-png`.
- Automation/hosting is Railway — deliberately not n8n.
- **Estimates/invoices:** generated with ReportLab, matching an "Order Summary" style layout. Base script `bhs_estimate_generator.py`, numbering scheme `BHS-YYMM-##`, all line items non-taxable, footer notes owner-operator / no upfront payment.
- **SMS pipeline** (`SMS-Extractor_BHS`): Railway IPv4 fix applied, Pydantic timestamp fields corrected. Body-template tokens on the phone proved unreliable, so the webhook also accepts `from`/`message`/`contact`/timestamps as URL query params and ignores any field that arrives as an unresolved `{{token}}`.
- **SMS outgoing messages — LIVE (2026-08-11).** Brian's sent texts forward to the BHS app's `/sms` with `&direction=sent`, and thread alongside incoming ones so a customer's short answer sits under the question that prompted it. Direction resolves from the URL param first, `OWNER_PHONE` as fallback. Outbound is stored but never extracted and never notified. Threads key on the normalized 10-digit number.
- **Location/timeline feature:** Google Maps Timeline data integrated with the SQLite DB via Haversine matching (~16 months of location data).
- Includes an invoice/time-tracking database and a task management board built into the app.
- History: built an "OPS CENTER" HTML dashboard as the operational front end.

## Session log — 2026-08-11/12

**Shipped and verified live:**

- **Service catalog** (`service_catalog`): 140 items, 22 trades, trade > subcategory > item.
  Low/high range with the midpoint quoted (homewyse method), plus `est_hours_per_unit`. All 168
  legacy InvoiceBee category strings preserved as aliases; zero unresolved either direction.
- **`POST /api/estimate/from-scope`**: plain-English scope -> priced, categorized lines. The
  model maps language to structure only; every price is looked up server-side, so a
  hallucinated price is impossible. Unstated quantities come back flagged `assumed_quantity`.
- **Callback form moved into the app** at `/callback/:leadId`, replacing a print-only form that
  had no save at all. Autosaves, service-matched checklist, scope -> priced lines, shows the
  implied hourly rate before a number is quoted. Drafts live in `lead_callbacks`, not
  `leads.metadata`, which the webhooks overwrite.
- **`leads.job_id` is populated for the first time.** The column existed since the table was
  created with nothing ever writing to it. `POST /api/leads/<id>/create-job` fills it and claims
  the SMS thread onto the job.
- **Outgoing SMS captured.** Direction from `?direction=sent` first, `OWNER_PHONE` fallback.
  Threads key on the normalized 10-digit number. Outbound is never notified but IS recorded and
  extracted -- an unanswered text can carry a price quoted or a day committed to, and those are
  captured as `quoted_price` / `committed_date` / `awaiting_reply`. Extraction is role-aware.
- **Machine-traffic filtering**: short codes, sender IDs, OTP/marketing get `status='spam'` with
  a reason, visible under a new Spam tab with a "Not spam" button. Nothing is dropped.
- **`GET /api/customer-brief`** + memory-server `/inbound` and `/lookup`: Bill now speaks from
  current state, including for callers who have no customer record yet. ~220ms live.
- **Bugs fixed:** `/api/reports/pl` returned 500 on every request (`te.date` vs `entry_date`);
  fresh-volume seeding pointed at a deleted file; a roof scope double-billed tear-off; `POST
  /sms` had two handlers so the app's threading code was unreachable and `sms_leads` was never
  written to.
- **Repo hygiene:** `beard-business-app` and `SMS-Extractor_BHS` archived (both were duplicates
  receiving nothing); customer database untracked from git; stranded branches resolved.

**Mistakes made this session, recorded so they are not repeated:**

1. **Misread `railway status` and "fixed" working infrastructure.** It reports the last
   deployment's source, not the service's GitHub link. Concluded auto-deploy did not exist,
   documented that falsely, then ran `railway service source connect` -- which reset the builder
   to Railpack and added a deployment-approval gate to a setup that had been working since July.
   See the Deploying section above.
2. **Claimed outgoing SMS was live when it was not**, by merging a branch description as fact.
3. **Printed `ANTHROPIC_API_KEY` in plaintext** by running `railway environment config --json`,
   which returns all variables. That key should be rotated. Never dump that command's raw output.

**Open / needs attention:**

- Two deployments sitting at `NEEDS_APPROVAL` with the Railpack builder. **Do not approve them
  as-is.** The service-level builder needs setting back to DOCKERFILE in the Railway dashboard;
  `railway environment edit --service-config` did not take effect. `railway.json` now pins it,
  but the service setting still overrides.
- The approval gate itself is new and unwanted -- also a dashboard setting.
- Retell dashboard: a custom function pointing at the memory server's `POST /lookup` must be
  added by hand for mid-call lookups. Call-start context works without it.
- The phone's SMS Forwarder template still emits unresolved `{Placeholder}` tokens on at least
  one rule. Rejected safely in code; the rule itself wants fixing on the handset.
- Seeded catalog prices are starting figures (`price_verified = 0`), not Brian's real numbers.
- 62 orphan time entries / 209.8 hours across 15 blocks still unreconciled.
- A full QC audit prompt is at `C:\Users\bbria\bhs-qc-audit-prompt.md` for an independent
  review of the whole ecosystem.
