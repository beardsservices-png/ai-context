# BHS App

The core Beard's Home Services business management app. **Live on Railway.**

This file is the current picture. Dated session notes and old incidents are in
`business/bhs-app-history.md`; GPS stops, threads, status and archiving in
`business/bhs-app-stops-threads.md`; the phone receptionist in `business/betty.md`.
The app repo's own `CLAUDE.md` is the most detailed and most current source for code.

## Which repo is canonical

**`beardsservices-png/BHSmobileapp` is the live app.** It's what Railway deploys and what runs on the phone. All work goes here.

`beardsservices-png/beard-business-app` is **deprecated and archived** (archived 2026-08-11). Do not commit to it.

- Same git history: `BHSmobileapp` was seeded by pushing the existing local folder to a new remote on 2026-05-03, so both share every commit from `4381393` (initial, 2026-02-28) through `374a745` (2026-04-05).
- The split was the move to Railway/mobile — first divergent commit is the Railway deployment config.
- `beard-business-app` is a strict subset: zero files exist there that aren't in `BHSmobileapp`. Nothing to migrate.
- Everything after the split — Railway deploy, GPS time clock, the in-app payment/invoice module, SMS leads inbox, Retell/Betty webhook, Settings page, PDF invoice import — exists only in `BHSmobileapp`.
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

## Importing an estimate that already exists as a PDF (2026-10-18)

The New Estimate screen opens with **Import a PDF estimate**. For an estimate written in chat (e.g. from a Messenger
conversation) and already sent to the customer: pick the PDF and the customer, number and lines fill in; *Save estimate* files
it as an **estimate** (not a paid invoice, which is what the old Filing Cabinet cleanup import did), keeps the printed number
as `EST` + digits, and files the PDF itself on the job under *Files & drawings*.

- The customer is matched by phone, then by the same words in the name. A near name is offered, never assumed. No match = a
  new customer is filled in from the PDF and saved with the estimate.
- A number already in the app for that customer is not imported twice (the screen offers Open it / File this PDF on it).
- The printed line total decides each line's unit price, so the app shows exactly what the customer holds.
- Code: `api/estimate_pdf.py`, `frontend/src/pages/Estimate.jsx`, test `scripts/tests/test_estimate_pdf.py`. PDF only (no photos of
  a printout). Not yet seen on a real PDF: check the first one by eye.

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

### Leads keep a draft estimate current (2026-10)

**Status: live.** Merged to `main` 5 Oct (`3c0d1da`); Railway reported the build successful at 11:38 UTC.

Every customer lead carries a draft estimate that **re-figures itself from the whole lead record
whenever something lands on it**: a customer text, Betty's call summary, a reply Brian sends, or a
note from Brian (typed, dictated, or relayed by any Claude session). The draft is derived from the
record each time, never patched, so a customer changing the job is just one more line in the record
and the latest word wins. It starts by itself once the lead has a name, an address and a request, and
until then the lead says what it is waiting on. Each refresh records what changed and why.

Decisions worth keeping:

- **One way in and out for any session:** `GET /api/leads/<id>/file` and `POST /api/leads/<id>/notes`.
- **Drafts live in `lead_drafts` / `lead_notes`, never in `lead_callbacks`.** A `lead_callbacks` row is
  what the customer brief reads as "callback in progress", and Betty tells the caller so. A draft the app
  wrote itself must not change what the receptionist says.
- **His hand edits are never overwritten.** If he edited the lines, new information is held as a
  proposal (*Use the new estimate* / *Keep mine*). An untouched copy follows the draft.
- **It stops at the lead.** A lead that became a job is not touched: the document there may be in the
  customer's hands. Changes to a job underway should be one-tap-apply, not automatic. Not built yet.
- **It cannot break intake.** It runs after the lead is committed, on its own thread, debounced per
  lead, and swallows and logs every failure. Off switch: `POST /api/leads/auto-draft`.
- **Labor only**: materials lines are dropped and reported, per `business/rules/estimating-rules.md`.
  What the catalog could not price stays visible.
- The pricing prompt that reads a whole conversation was tested with a stub, not the live model.
- Open: the rules file says flat rate / Qty 1 / round to $5; the app prices unit x quantity.
  Drafts follow the app.

### The mic assistant: the whole business, edits only after a read-back (2026-10)

**Status: live.** Merged 6 Oct (`b76e20b`). Brian's brief: *not scoped to an open invoice, the full brain, and able to edit anything as long as it repeats back exactly what the edit will be.*

- **Reads everything.** The old six canned lookups stay; on top of them it can run one read-only SELECT over the live database. The read-only rule is enforced by SQLite's own authorizer, not a text filter, and the tables for logins, settings and its own queue cannot be read at all.
- **Edits through one tool that writes nothing.** The model proposes; the server validates the change, dry-runs it inside a transaction that is rolled back, and **builds the read-back itself from the rows** (names, before and after, and what it does to the job's total, paid and balance). The model's own words never decide what Brian is shown.
- **A yes applies it, once.** Tap or say "yes". The proposal expires in 20 minutes and is re-checked against the data as it is *now*; if it would read back differently, nothing is applied and he is shown the new read-back. All or nothing, and every proposal and applied change is logged.
- **Guard rails.** Customers, jobs and invoices cannot be deleted by voice (they take records with them). The price book, logins and creating a brand-new estimate stay in the app. Hours written by the GPS clock cannot be deleted from here.
- **Side effects match the screens.** Changing a line recalculates the invoice; payments move a job to and from paid; removing a payment no longer drops an in-progress job back to pending (the old payment screen did that).
- **Untested against the live model.** The tests stub it. Watch the first real conversations.
- **Exposure while the login is off:** the assistant is owner-only once the login is on. Until `APP_PASSWORD` is set, the whole app is open, and that now includes this.

### Login and people (2026-10)

**Status: live, and on as of 6 Oct** (merged 5 Oct as `fdaad3c`, `c68c481`; `APP_PASSWORD` was set on the server by someone else on 6 Oct, evidenced in Railway's request log). It is dormant whenever `APP_PASSWORD` is empty or unset.

- **Why:** the app had no login at all. Anyone who found the address could read and change every customer, job and
  figure, `/print/<id>` handed the whole job file to anyone who counted job numbers, and the admin backup route matched
  an empty key when `ADMIN_KEY` was unset (it returned the whole database).
- **One owner password** (`APP_PASSWORD`), a signed HttpOnly SameSite=Lax cookie for 60 days, and a Bearer token
  (`APP_API_TOKEN`) for Claude sessions and scripts. Guessing is rate limited.
- **Machines keep their own tokens and are an explicit allowlist**, never put behind the password: health check,
  location ingest, SMS Forwarder and Retell webhooks, the memory server's customer brief, the admin routes. A test walks
  every route and fails if one outside the allowlist is left open. Putting a login in front of those would silently stop
  texts and tracking, which already cost five days of leads.
- **Print links carry a code** (`?k=`): it opens that one job, and a dedicated endpoint returns only what the printed
  document shows. Links copied before the login is switched on stop working.
- **Other people can sign in with limited access** (Settings -> People): eight sections (time, customers, leads,
  estimates, jobs, money, trips, location). Enforced on the server: every route belongs to a section or to the owner
  alone, and an unclassified route is the owner's. A person with no price-bearing section is never *sent* prices or
  payments; Brian's private notes on difficult customers are sent to no one else. Settings, the voice assistant,
  backups, price-book edits and deleting a customer, job or payment are owner only. Access ends on the next tap.
- **People cannot be added while the login is off**, because a stranger could plant an account that would be waiting
  the day the login is switched on.


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

**Picture messages do not forward (found 2026-10-08).** The handset forwarder sends plain SMS
only. A text with a PDF or photo attached (MMS/RCS) never reaches `/sms` — Charlotte Collins'
estimate PDF and her original fence request are both missing from Railway logs, while plain
texts that day forwarded fine. Until the forwarder handles MMS, record a document send by hand:
`POST /api/leads/<id>/notes` (and the job's next step).

**Texts land on the customer's open lead** (status new/read/converted, matched by phone), and the
customer file shows them via `leads.customer_id`. Set `leads.job_id` (`PUT /api/leads/<id>`) to
tie that thread to the job — done for Collins (lead 330 → job 114, EST20261007).

**Cloud sessions can reach the live app** (2026-10-08): `bhsmobileapp-production.up.railway.app`
answers from here; send `Authorization: Bearer $APP_API_TOKEN`. The old note that the egress
proxy blocks Railway is out of date.


## Job records — one per job, and it wins (2026-09-26)

The Giles paperwork had spread across three AI tools and Drive: a ChatGPT redo of
Phase 3 that put back a door the customer had already dropped, a Gemini draft
that got the split right but still said "Door Rough Opening", five copies of a
July materials list, and design notes nobody else linked to. Nothing said which
one was true.

The fix is a rule, not a file: **every multi-document job gets one Drive folder
with a `<Customer> — Job Record (START HERE)` doc in it.** That doc lists the
phases, what has been billed, the scope decisions that override older paperwork,
and which file is current. Anything replaced moves to a `Superseded — do not
send` subfolder, renamed `SUPERSEDED — …`, never deleted. The app, this repo and
the CAD drawings point *at* the record; none of them restate its numbers (this
repo is public anyway, so amounts stay out of it).

- **Giles** — Drive folder `Giles — BHS20260627 (Jesse & Doree Giles)`. Phase 3 is
  now billed in two draws; the current sheet is `BHS20260627D_Giles_Phase3_Draw1.pdf`.
  Scope settled: **no exterior door, no sidelite** (the walkway stays open), three
  double-hung windows, the triangle above the long side glazed rather than sided.
- **The app is not caught up.** Job 111 still carries whatever was keyed in June
  and invoice `BHS20260627` still reads `paid` (see *Receivable $0* in
  `docs/2026-09_tier1-live-findings.md`). Cloud sessions cannot reach Railway, so
  the job record lists the target state; the next session with app access applies
  it. Careful with `PUT /api/filing-cabinet/<id>`: it **replaces** services and
  **deletes any time entry not in the payload**, so read the job first and send
  everything back.


## Estimate outcomes — why one closed

`jobs.close_reason` records *why* an estimate left the live set; `jobs.closed_at`
when; `jobs.superseded_by` points at the estimate that replaced it. Before this
the trash endpoint appended `[Rejected] <text>` onto `notes`, so the reason was
unqueryable and no win/loss number existed.

- Vocabulary lives in **`api/job_status.py`** — the one definition of statuses
  and reasons. Add reasons there, not as literals in `app.py`.
- Reasons: `accepted`, `declined_price`, `lost_competitor`, `no_response`,
  `declined_timing`, `withdrawn`, `superseded`, `duplicate`.
- **`superseded` and `duplicate` count as neither win nor loss.** A re-quote
  would otherwise read as a lost job and revising an estimate would drag the
  win rate down every time.
- `GET /api/reports/win-loss` returns rate, dollars, and loss reasons ranked by
  **dollars rather than count** — the costliest reason is rarely the commonest.
- `GET /api/estimates/close-reasons` feeds the picker.
- Unrecognised free-text reasons are kept verbatim under `unspecified` rather
  than rejected, so older screens keep working.

Status sets are defined once in `job_status.py` and rendered into queries. The
exclusion `NOT IN ('estimate', 'rejected')` used to be hand-written at six call
sites; a missed one produced a wrong number rather than an error.


## Stack

- Python / SQLite, hosted on Railway, source in GitHub org `beardsservices-png`.
- Automation/hosting is Railway — deliberately not n8n.
- **Estimates/invoices:** generated with ReportLab, matching an "Order Summary" style layout. Base script `bhs_estimate_generator.py`, all line items non-taxable, footer notes owner-operator only. **No payment language on any customer-facing document** — the "no upfront payment required" line older generated documents carry is not wanted; strip it wherever it survives. See `business/rules/estimating-rules.md`. Numbering: `business/rules/document-standards.md`.
- **SMS pipeline** (`SMS-Extractor_BHS`): Railway IPv4 fix applied, Pydantic timestamp fields corrected. Body-template tokens on the phone proved unreliable, so the webhook also accepts `from`/`message`/`contact`/timestamps as URL query params and ignores any field that arrives as an unresolved `{{token}}`.
- **SMS outgoing messages — LIVE (2026-08-11).** Brian's sent texts forward to the BHS app's `/sms` with `&direction=sent`, and thread alongside incoming ones so a customer's short answer sits under the question that prompted it. Direction resolves from the URL param first, `OWNER_PHONE` as fallback. Outbound is stored but never extracted and never notified. Threads key on the normalized 10-digit number.
- **Location/timeline feature:** Google Maps Timeline data integrated with the SQLite DB via Haversine matching (~16 months of location data).
- Includes an invoice/time-tracking database and a task management board built into the app.
- History: built an "OPS CENTER" HTML dashboard as the operational front end.


## Decisions, Oct 2026 (BHSmobileapp)

- **Helpers** are set up like the owner (the *Full helper* preset opens all sections). Four switches say what they may do: change existing records, change prices/settings, delete, use the mic assistant. Adding is always allowed. Passwords have no minimum length and no lockout, by Brian's instruction; password boxes have an eye.
- **Estimate screen**: one screen, three steps (who, what you saw, what it comes to). Walk the Job was folded into it. One shared line list (`LineList`) is used by the estimate, Callback and Filing Cabinet screens.
- **Filing Cabinet = customer files**: top is *Needs you* (what is waiting and for how many days), then *What your work really pays* vs his hourly target, then each customer. Emphasis is actions and not dropping the ball, not owed/paid. Each open job has a one-line next step.
- **App opens on Leads**, each card showing when it arrived and the next action.
- **Drive settings are two toggles**: the drive TO the job counts as business (default on); the drive BACK is separate (default off).
- **Pushes**: a notice when he leaves a job site with the hours logged (tap to fix times); prompts to name unrecognised stops (supplier, fuel) so expenses can be verified.
- **Automatic estimates**: once a lead has name, address and request, the customer, job and priced estimate are created automatically and kept current from new texts until he taps *Looks good*. His own line edits are never overwritten (he gets a next step instead). Setting: *Build estimates for me*. After review the estimate is the customer's document and is not changed automatically.
- **Your Day (`/timeline`) looks like Google Maps Timeline** (2026-10-28): a map with numbered stops and the roads driven, then stops and drives in order. Every drive is driving (no travel-mode question). Stops ask *Was this work?* Yes/No; stops named by an address get *Name this place* so places read like "24 hr fuel", "Lowes", "Chens", "Home".
- **Gas stops always ask "Did you get fuel?"** (2026-10-28, Brian: even a 4-minute stop at 24 hr fuel or Shell). A place counts as a gas station by its saved kind or by its name; the question shows on Your Day and as a push unless a bank alert, an earlier answer or an expense he typed in already covers it. Yes saves a fuel expense dated the day of the stop; No is remembered. A parked 3-minute stop is now recorded even at a place the app has never saved.
- Not built yet: one-tap apply of text-driven changes on jobs already underway.

## Location record = OwnTracks, read like Google Timeline (decided 30 Oct 2026)
- Reverses the 29 Oct decision: a weekly manual Google export is NOT acceptable. Everything must be automatic (no export, no confirming, no hand logging).
- The phone's pings were fine; the logic was wrong. Fixed in the logic: one circle per driveway (several open jobs = one stop), a quiet phone at home is still home, a saved non-job place counts as a stop at 3 minutes, every stop gets a name.
- Likelihood decides close calls: a job with no hours/texts/calls/payments in 45 days, stopped at after 4 pm or under 90 min, is a drive-by and is not billed. A long morning there still is.
- Nightly, Claude reads the close calls with the whole day for context (only among stops it was shown; cannot invent stops or hours). No API key = rules alone.
- Your Day looks like Google's Day view (totals line, glyph per place, "Left at 6:54 AM").
- Past days were re-read once (old stops hidden, never deleted; hours only for the last 21 days).
- Anything the app cannot settle (rules and Claude both stuck, no API key, a silent stretch) becomes a popup asking Brian; it is never left guessed.
- OwnTracks is the primary source. Google Timeline is the backup truth Brian checks himself (phone only, no remote read); the app links to it for the day in question.
- A text months after a job closed becomes a new lead (old converted lead only absorbs texts while its job is open or within 14 days).

## Receipts and walkthrough recordings (31 Oct 2026)
- **Receipts** (`/receipts`, `api/receipts.py`): photo or PDF -> every line read -> each item Job (customer's materials) /
  Mine (cost of business: brushes, blades, bits, tools) / Personal / Not sure -> saved. Expenses are derived from the receipt
  (one per job + one overhead, tax shared), rewritten on edit. A Chime-alert expense for the same total within 2 days is
  replaced; an alert after the receipt is linked, not logged again. Lines that do not add up are marked "check this", never fixed.
- **What did I use?** (`GET /api/receipts/history?q=`): the work words find past real jobs (not unaccepted estimates) and list
  receipt items, invoice materials lines and hand-typed expenses for each. The mic assistant can read it too.
- The claude.ai Receipt Ledger artifact (Jul-Oct 2026) was imported once (`owner_fixes.receipt_ledger`); new receipts go in the app.
- **Walkthrough recordings** (`api/walkthrough.py`): estimate step 2 *Add a walkthrough recording*, or Share -> BHS. faster-whisper
  `small.en` on the server (own process, one at a time, model on the volume under `models/`); Claude extracts work + follow-ups
  (no prices; small talk and personal matters left out); saving the estimate files the audio + transcript on the job.
  `av` must stay at 16.0.1 with faster-whisper 1.2.1.
