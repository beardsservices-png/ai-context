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

## Deploying — read before you push

**Railway does not auto-deploy from GitHub.** The service has no repo source
(`source: {repo: None}`), so pushing to `main` deploys nothing. Deploys happen only via
`railway up` from the local folder. Two commits sat undeployed for ~2 weeks because of this.

The local folder must be linked to the right project first — it was linked to project
**"sms"**, not "BHS APP", so a `railway up` would have deployed the business app into the
SMS project:

```
railway link --project "BHS APP" --environment production --service BHSmobileapp
railway up --service BHSmobileapp
```

- Project **BHS APP** → service **BHSmobileapp** → `bhsmobileapp-production.up.railway.app`
- `ANTHROPIC_API_KEY` is set on Railway, **not** in the local `.env`. Anything calling
  Claude cannot be tested locally.

### The local clone is not a clone

`C:\Users\bbria\BHSmobileapp` has an **unrelated git history** from `origin/main` — different
root commit, no merge base. Work committed locally cannot be merged or fast-forwarded to
`origin`; it has to be ported onto a branch cut from `origin/main`. Check
`git merge-base HEAD origin/main` before assuming a push will work, and never force-push
to resolve it — that would destroy the real history.

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

## Stack

- Python / SQLite, hosted on Railway, source in GitHub org `beardsservices-png`.
- Automation/hosting is Railway — deliberately not n8n.
- **Estimates/invoices:** generated with ReportLab, matching an "Order Summary" style layout. Base script `bhs_estimate_generator.py`, numbering scheme `BHS-YYMM-##`, all line items non-taxable, footer notes owner-operator / no upfront payment.
- **SMS pipeline:** Railway IPv4 fix applied, Pydantic timestamp fields corrected. SMS Forwarder body template on phone still needs updating to `{"from":"{{from}}","contact":"{{contact}}","message":"{{message}}"}` — not yet live.
- **Location/timeline feature:** Google Maps Timeline data integrated with the SQLite DB via Haversine matching (~16 months of location data).
- Includes an invoice/time-tracking database and a task management board built into the app.
- History: built an "OPS CENTER" HTML dashboard as the operational front end.
