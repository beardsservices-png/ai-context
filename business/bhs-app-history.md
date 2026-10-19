# BHS App: history and session notes

Dated notes moved out of `business/bhs-app.md` so that file stays short. **Read this
when an old decision or incident matters, not by default.** Anything here may be
superseded; `business/bhs-app.md` and the app's `CLAUDE.md` win where they disagree.
The *Document numbering* and *Voice assistant* sections below are kept as history and
are out of date (current numbering: `business/rules/document-standards.md`).

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
  **−3 days**: the invoice usually *precedes* the work. The matcher now surfaces on the Data
  Gaps screen with one-tap linking (see *Orphan hours, location history, and trips* above) —
  but nothing can be matched until the location history is built on the live volume, which is
  a button on that screen and has not been pressed yet.
- 44 jobs from 2023 have billed labor and zero hours (pre-BusyBusy) — unrecoverable, exclude
  from $/hr math.

## Orphan hours, location history, and trips (2026-08-23)

Three things the app knew and kept behind a button. **Merged to `main` and deployed
2026-08-23** (`8ee77bb`).

### The orphan matcher reaches the screen

The matching engine existed but only printed to a terminal, so the 62 unlinked entries kept
being a dropdown of ~109 jobs on Filing Cabinet -> Data Gaps. It now lives in
`api/orphan_matching.py` (the backfill script imports it, so there is one implementation) and
is exposed as `GET /api/data-gaps/orphan-suggestions` and
`POST /api/data-gaps/orphan-suggestions/apply`.

- The browser posts **entry ids only**. Which job each belongs to is re-derived server-side at
  the moment of writing, so a stale screen cannot file hours against the wrong job.
- Linking is an **UPDATE of a row that already exists, never an INSERT**, and carries
  `AND job_id IS NULL`, so re-running links nothing twice.
- Only unambiguous matches apply. `clear_winner` needs both a **25-point margin over the best
  candidate belonging to a different job** and a **score floor of 100** in its own right. The
  floor was added after testing: where only one job site was near that week there is no rival
  to beat, so a stop two days off with hours that disagreed was being called certain.
- Uncertain rows keep the manual dropdown and say why they are uncertain.

Two bugs found in that screen while working on it: the dropdown was built from `/api/jobs`
(which returns `id` / `invoice_id`) but read `job_id` / `invoice_number`, so every option had an
empty value and the Link button could never enable — it had been unusable, which is part of why
the backlog never moved. And a stray separator rendered where a null customer name would be.

Entries older than a year with **no** match fold away behind a "show them" line that names the
count and the hours; anything with a match stays visible however old it is. The clutter is the
part nothing can act on, not the age.

### Building the location history

`api/location_history.py` + `GET/POST /api/admin/build-location-history`, with a button on the
Data Gaps screen. Converts what is already recorded into something usable, in four idempotent
stages: geocode customer addresses and measure road miles from home; materialise
`timeline_visits` as `location_points`; create a job-site fence per past job; run `evaluate()`.

- **It never writes a time entry** — `write_time_entries=False` is hardcoded. The engine's write
  path *inserts* hours derived from visits, which is right for a day not yet recorded and wrong
  across months that already hold their hours.
- Runs on a background thread (a hundred address lookups at one per second is minutes, not a web
  request) and publishes progress to `app_settings`, so **either Gunicorn worker can report it**.
  A run whose heartbeat is 20 minutes stale is treated as dead and can be restarted; a second
  POST while one is live returns 409.
- The phone only started reporting 2026-08-19, so everything before that comes from Google
  Timeline. Backfilled drives still carry no trustworthy mileage — Timeline recorded stops, not
  the trail between them.

### Trips are logged, not suggested

`api/trip_logging.py` writes the drive when the hours are written — `POST /api/time-entries`,
Day Wrap-Up, and when an orphan entry finds its job — under the conditions the old suggestion
used: job on the entry, address with a measured distance, `trip_skip != 1`, no trip already on
that job+date, and exactly one entry for that job that day. `POST /api/suggested-trips/log-all`
clears the backlog in one action.

- **Every leg starts wherever he actually was.** Home is not a special case — it is one of the
  places he can be leaving from. He leaves a job, stops at ACE, carries on to the next job:
  that drive starts at ACE. Origin comes from the last stop in the location record before the
  arrival, routed by road; falls back to the previous job-site trip of that day when there is
  no location record, then to the distance from home. A leg that did begin at home uses the
  stored `mileage_from_home` so a hand-corrected figure is never re-routed over. Nothing older
  than 18 hours counts as the previous place.
- **A hole in the record is not a route.** A stop only counts as the origin if he left it
  within 3 hours of arriving (`MAX_ORIGIN_GAP_HOURS`). A dead battery from 10:30 to 16:30
  leaves a stop that is technically most recent and says nothing about the drive. Past the gap
  the trip is still logged, at the distance from home, with a note saying the record has a
  hole — amber on the Trips page with a *Re-measure this day* action. A day with no tracking at
  all is the normal historical case and is not flagged. Nothing ever blocks or asks him where
  he was.
- `POST /api/trips/recalculate-day` re-measures one day's automatic trips under current rules,
  for after a distance is corrected or the location history is built. Only touches trips whose
  notes begin `Auto-logged from time entry`; never runs on its own.
- **A typed distance wins.** `customers.mileage_verified = 1` marks a figure Brian entered
  himself and nothing recomputes over it — a rural address geocodes to the nearest road
  centroid, up to a couple of miles off the driveway, and re-measuring reproduces the same
  wrong answer. One customer read 10.1 where the map said 8.0; that is the cause. Editable on
  the Customers screen, badged *your figure* vs *measured*.
- **Miles are one way, and that is deliberate.** Brian's rule: the drive out is to the job, the
  drive back usually takes in the lumber yard, the gas station and the school run, and he will
  not charge a customer for a leg spent on his own errands — the same way you are paid for the
  ride to a site and not the ride home. A round trip was tried and reverted at his instruction.
  Do not "fix" the missing `* 2`; if the return leg is ever counted, that is his call with his
  accountant.
- Day Wrap-Up skips the automatic trip when he entered his own miles on the same form — his
  number wins, and two trips for one job on one day is a double deduction.
- `customer_lat/lon` and `mileage_from_home` are now worked out automatically when a customer is
  saved with an address (in the background, so the save does not wait on two web services) and
  cleared when the address changes. `POST /api/customers/<id>/calculate-mileage` still exists and
  now goes through `geo.py`'s cached, rate-limited path instead of its own uncached copy of
  Nominatim — the duplication `geo.py` was written to end had grown back.
- `geo.road_miles()` is the OSRM call, returning `None` rather than a straight-line guess: a
  missing mileage is visibly missing, a Haversine standing in for a route is wrong in a way
  nothing downstream can detect.

### The evening recap

`api/day_digest.py` pushes one notification a day (default 8pm `BHS_TIMEZONE`) listing the
hours and miles recorded, through the same ntfy topic the SMS lead alerts use — nothing new to
set up on the handset. Toggle, hour and a *send today's now* button are on Settings.

- **A prompt, not an approval gate.** Trips are logged as they happen and count whether or not
  he reads it. Gating on approval would mean a missed evening is a missing mileage record.
- **A quiet day sends nothing.** A "you did nothing today" buzz teaches a person to swipe
  notifications away unread, and then the ones that matter go the same way.
- **Doubt leads.** Trips measured across a hole in the location record are listed first — those
  are the ones only he can correct.
- Scheduling is a thread per Gunicorn worker polling every 5 minutes; the send is claimed by a
  conditional UPDATE on `app_settings.day_digest_last_sent`, so two workers waking at eight
  produce one notification rather than two.

### Worth knowing before the next session

- Verification against live data is not possible from a container: `data/beard_business.db` is
  absent by design, Nominatim and OSRM are blocked by the sandbox proxy. The pattern that works
  is `cp data/schema_seed.db /tmp/x.db`, `DB_PATH=/tmp/x.db python3 -c "import app"` from `api/`
  to run migrations, seed a fixture, then drive the Flask test client. Flask is not installed in
  a fresh container (`pip install --ignore-installed blinker flask flask-cors`), and Chromium is
  at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` for a real browser pass.
- Do not name a scratch file `click.py` next to a test that imports Flask. It shadows Flask's
  own `click` dependency and the traceback makes no sense.


## Leads intake — the five-day blackout (2026-08-31 → 2026-09-06)

Fixed and deployed 2026-09-06 (`361f2b7`). Worth knowing because four separate faults
stacked into one symptom: *"I have texted a new person and not a single piece of data
shows in the app."*

**Every lead created after 31 Aug was invisible.** `3e430c7` gave leads a `lead_type` and
rebuilt the screen around four tabs derived from it — but all four intake paths inserted
without one. `tab_where('needs_me')` requires `lead_type = 'customer'`, so every new row was
typed NULL, matched no tab's WHERE clause, and appeared nowhere. The rows were in the
database and returned by `/api/leads` the whole time; only the screen could not see them.
"Needs me" read **0** for five days while real enquiries arrived.

- Lead creation now goes through one **`_lead_insert`** that stamps `lead_type` *and*
  `phone_norm`, so neither can be dropped again by a new caller.
- `needs_me` and `working` count a NULL type as a customer. **A row on no tab is worse than
  a row on the wrong tab** — that is the whole failure in one line, and the guard is there so
  the screen cannot go blank again if some future path forgets.

**A text from an existing customer only became a note.** The webhook appended it to
`customers.notes` and returned — no lead, no notification, nothing on any screen. Heath
Johnson's *"did you happen to get those quotes together?"* was filed perfectly into a field
nobody opens while waiting on a callback. Being on the books is a reason to answer faster,
not to go quiet. The note is still written; a lead is now raised alongside it.

**Threading was a scan of the twenty newest rows**, normalising numbers in Python. A busy
evening of family texts pushed a real lead out of the window and split her conversation into
two leads — and personal/junk traffic inserted a *fresh row per message*, 60 from one number.
Leads now carry **`phone_norm`** (indexed); every sender threads onto one lead, family
included.

**The handset flattens the notification.** The SMS Forwarder rule sends the whole thing as
the message body instead of filling the `%ct%` / `%mb%` macros, so every lead opened with the
sender's own name and number, carried a blank `contact_name`, and was stamped with the moment
the webhook fired rather than when the text was sent:

```
Amanda Shirley
+1870XXXXXXX
09/03, 4:41 PM
<what she actually wrote>
```

`api/sms_parsing.py` takes that header back apart. **It only strips when it finds a real
timestamp line**, so a genuine message that merely opens with a name is left exactly as
written. Fixing the rule on the phone is still worth doing, but the app no longer depends on
a phone setting being right to know who texted.

`api/leads_hygiene.py` (`leads_hygiene_v1`) repaired the stored rows — on live: **4 typed,
213 numbers normalised, 227 headers unpacked, 145 duplicate rows folded into 12 threads**,
229 leads → 84 with no content lost. Converted and dismissed leads, and any lead a job or a
callback draft points at, are left exactly where they are.

Regression test: `scripts/tests/test_leads_intake.py` — seeds a fixture in the broken shape,
runs the migration, then drives all four intake paths through the Flask test client and
asserts **no lead exists that no tab can show**.

### ntfy: two services, one topic

The topic is a single ntfy topic (its name is deliberately **not** written in this public repo: anyone who knows it can read the alerts, which carry customer names) and Brian is subscribed to it in the ntfy app. Betty's call-back
alerts were arriving from `bhs-memory-server`, which had it configured — **the BHS app
service never did**, so `push_configured` was `false` and the app's SMS lead alerts and the
8pm day-digest silently sent nothing for their whole life. `NTFY_TOPIC` is now set on the
BHS app too, pointing at the same topic, which is what was always intended. Don't read "Betty's
notifications work" as "notifications work" — they are separate services with separate config.

### A text during a live job is not a callback (2026-09-06)

Jesse and Doree Giles have had **job 111 in progress since 27 June**. Four messages about
that job sat in *Needs me* as a stranger's first enquiry. Being in the queue beat the
vanishing act it replaced, but a customer Brian has been on site for since June is not
someone he failed to ring back — it is the same fault pointing the other way.

Three things kept the app from knowing (`f68fe33`):

- **They text from a number one digit off the one on their record.** The number matched
  nothing. The **contact name is now a fallback** — it comes out of Brian's own phone book,
  so an exact match is his filing, not a guess. Exact only, single match only, and only after
  the number has failed; a fuzzy match here would staple a stranger's text to a real
  customer's job. The number is then written to **`contact_directory.customer_id`**, so the
  next text is a plain lookup and it is never inferred twice.
- **Nothing consulted the jobs table.** A matched customer with a job at `IN_PROGRESS` gets
  the lead filed onto that job and marked `converted`, so it reads under **Working**.
- **The boundary is deliberately narrow — `IN_PROGRESS` only.** A customer sitting on an
  estimate is *chasing a quote*, and that is precisely the message class that went missing to
  begin with. Under-filing leaves a text visible; over-filing hides one. Verified in both
  directions in the test: the job in progress leaves the queue, Heath Johnson chasing his
  quote stays in it.

Live result: `{'phones_cleaned': 1, 'phones_blanked': 2, 'linked_by_name': 5,
'filed_onto_jobs': 1, 'numbers_remembered': 3}`. Exactly one lead moved.

### Junk in the customers table, from converting an unparsed lead

Three customer records held a **name, or a whole undelivered-MMS notification, in the phone
column** — left behind by converting a lead whose message was still an unparsed forwarder
blob, using that blob as the customer name. `api/lead_job_links.py` recovers a number where
one is buried in the text and empties the field where there is none, so it reads as missing
rather than as data.

One junk record survives and wants deleting by hand: **customer 102, name *"Message from
Heath Johnson not downloaded"***, no jobs, no time entries, notes `Created from SMS lead: …`.
The real Heath Johnson is customer 103.

The junk lead (83) and customer (102) were deleted 2026-09-06 after confirming nothing else
pointed at them.

### Saves used to blank every field they did not carry — fixed

`PUT /api/customers`, `/api/expenses`, `/api/trips` and `/api/categories` each wrote their
**whole column list out of `data.get()`**. A save carrying only the field that changed erased
every other one and returned **200**. Correcting a phone number took the address, the notes
and the cya_notes with it. An expense edit set `cost` to **zero** — the coercion was
`float(data.get('cost', 0))` — and turned `is_overhead` off, because a missing key is falsey.

**`partial_update()` in `api/app.py` is now the one place a row is edited.** Absent means
unchanged; **present-but-empty still means clear it**, because a wrong address has to stay
deletable. Numeric fields go through a converter that raises rather than storing a zero, so a
cost of `"a lot"` is a 400 and the old cost stands.

Two bugs fell out of centralising it:

- An address only counts as **moved** when the save actually contained one. Before, *every*
  save without an address looked like a move, threw away the cached coordinates, and cleared
  any mileage Brian had confirmed by hand (`mileage_verified`) — the figure the trip logging
  is explicitly built to never recompute over.
- Saving a customer with no name, or one that does not exist, now fails cleanly rather than
  writing a nameless row or silently doing nothing.

Covered by `scripts/tests/test_partial_saves.py`: all four endpoints, the deliberate clear,
and the refusals. **When adding an edit endpoint, use `partial_update` — do not write a
column list from `data.get()`.**


### Deploy approval is not a setting you can turn off

Railway puts a deployment in **NEEDS_APPROVAL** when the pushing GitHub account is not linked
to a Railway account with access to the workspace. Railway have stated this **cannot be
disabled** — it is their boundary between repo access and infrastructure access. So a push to
`main` builds but waits for someone to click Approve in the dashboard. Either approve each
one, or link the pushing GitHub account to Brian's Railway account. Do not go hunting for a
toggle, and do not "fix" it by reconnecting the service source — that is what reset the
builder to Railpack in August.

### Verified correct on Railway (2026-09-06)

Builder **DOCKERFILE** and healthcheck `/api/health`, both pinned in `railway.json` and shown
in the dashboard as "The value is set in /railway.json". GitHub `beardsservices-png/BHSmobileapp`
→ branch `main`, auto-deploy on. Port 8080, US West, 1 replica (replicas are unavailable with
an attached volume, which is correct — the digest scheduler and location-history threads assume
few workers). `DB_PATH=/data/beard_business.db` on volume `beard-business-data`.

### The sent-message rule (2026-09-06)

The rule existed all along. It was issuing a **GET**, both webhook routes were registered
`methods=['POST']`, and so every sent text was answered **405 before a line of the handler
ran**. The outbound handling was written, deployed and correct the whole time and nothing
could reach it. Routes now accept GET as well as POST (`26b43d0`).

That was not the only fault in the rule. It also sends **no body and no query parameters** —
only `?token=` — so there is nothing to file even once the method is right; it answers
`400 Missing from or message`. The rule needs, at minimum, the other party's number and the
message text, plus **`&direction=sent`** in the URL. `direction` is a literal string in the
URL and always resolves, which is why it beats matching against `OWNER_PHONE`.

Both shapes are verified live: a GET carrying `&direction=sent&to=…&message=…`, and a POST
reusing the inbound JSON body with `&direction=sent` appended. Field values are read from the
query string as well as the body, so a rule built entirely out of URL parameters works.

The recipient is looked for under `to`, `recipient`, `destination`, `address`, `number`,
`in-number`/`in_number`, `out-number`/`out_number`, `contact_number`, `msisdn`, `sim` and
finally `from` — whichever the handset's sent-rule template offers. Brian's own number and
unexpanded macros like `{out-number}` are skipped rather than treated as a value.

A sent message whose rule reported no recipient used to return a silent `200` and be stored
nowhere. It now returns **422 naming which fields arrived and which are missing**, so a broken
rule is visible in the forwarder app instead of green. A text Brian sent can carry a price he
quoted; it must never look like a success when it was dropped.

**The forwarder's macro syntax is `{in-number}` / `{msg}`** (curly braces, not the `%from%`
style some versions use). The working inbound rule is `POST` with body
`{"from":"{in-number}","message":"{msg}"}`.

### What the sent rule actually sends (2026-09-06, from a live test)

Fixing the method was not enough. A live test put the real payload in the logs and it matched
nothing the webhook looked for:

```json
{"time":"09/06, 12:35 AM",
 "key":"Outgoing : 
+1870XXXXXXX
09/06, 12:35 AM
Test reply from my phone
"}
```

Three separate mismatches in one payload, all now handled (`94bf471`):

- The message is under **`key`**, not `message`/`text`/`body`. Accepted, but **last in the
  alias list** — a name that generic must never outrank a real `message` field.
- **There is no recipient field.** The other number is a line *inside* the blob. The number
  parsed out of the payload now stands in as the recipient when no explicit field carries one,
  which is right for this rule because it reports the other party's number in both directions.
- **There is no `?direction=`.** The only thing saying which way it went is the literal words
  **`Outgoing :`** at the front. That label now sets the direction.

Direction is resolved in trust order: explicit `?direction=` in the URL (a literal that always
resolves) → the `Outgoing :` / `Incoming :` label the phone wrote → sender matching
`OWNER_PHONE`. `OWNER_PHONE` is last because it needs the rule to put a number in a field, and
this rule puts no number in any field.

The label only counts when what follows is a forwarder payload with a real timestamp header,
so a customer opening with *"Sent: the photos you asked for"* keeps their first word.

Verified live: the exact payload above returns
`{"ok":true,"direction":"outbound","threaded_to":"8707245506"}` and both halves of the
conversation now sit on one lead, role-tagged `customer` and `brian`.

Also seen and worth watching: a rule was issuing an **empty GET every 1–3 minutes** — token
only, no body, no params — answered `400 Missing from or message`. It stopped after the sent
rule was reconfigured. If it returns, it is a rule firing on a timer rather than on a message.


## Document numbering

- An estimate is `EST` + the date: **`EST20260816`**.
- When it becomes an invoice **the number does not change** — only the prefix
  does, `EST20260816` → **`BHS20260816`**. Same job, same number, start to finish.
- Two on the same day take a suffix: `EST20260816-2` → `BHS20260816-2`.
- Once converted **the estimate goes away** — archived or hidden, never left
  live alongside the invoice. A customer must never hold an estimate that
  contradicts their invoice.
- The prefix is not stored. `api/app.py` derives it from status at display time
  (`prefix = 'EST' if status == 'estimate' else 'BHS'`), so the underlying
  record keeps one identity for its whole life. Status carries the meaning; the
  number is only identity. Do not encode state into the number.
- Jazzy's own pay invoices are a separate series, `JBHS-YYYYMM-##`.
- **A multi-phase job keeps one number and adds a letter per phase document**:
  Giles is `20260627`, with `20260627C` = Phase 2 and `20260627D` = Phase 3. A
  phase billed in parts stays on its own number and says **"Draw 1 of 2"** on the
  sheet, with a *what is billed now / what is still to come* table at the top, so
  the customer can see the phase total never moved.


## Voice assistant

A floating mic on every screen. With an invoice open, speech edits it directly:
"make the install line nineteen hundred". Lives in **`api/assistant.py`**.

- `POST /api/assistant/command` takes a transcript plus which record is on
  screen. **The client sends only the record's identity** — the record is read
  from the database, so a stale screen cannot cause a wrong write.
- Five tools: `update_line_item`, `add_line_item`, `remove_line_item`,
  `update_customer_field`, `set_invoice_status`. **The model proposes, the
  backend decides.** Negative prices, unknown fields, bad statuses and line
  items belonging to another invoice are refused whatever was proposed. No raw
  SQL is ever exposed.
- **Destructive calls come back for a one-tap confirm** and are re-validated on
  confirm, with `invoice_id` re-pinned from the request so a tampered payload
  cannot retarget another invoice.
- Totals recompute after every line change by the same rule as a normal save
  (`amount * quantity`, `reimbursed` excluded from both buckets).
- `assistant_audit` records transcript, tool, arguments and before/after for
  every attempt — this path skips the normal screens, so it is the only trace.
  Read it at `GET /api/assistant/audit`.
- Speech is the browser's own `SpeechRecognition` — no third-party
  transcription. Browsers without it fall back to typing. Chrome on Android has
  it; iOS Safari does not.
- Invoices only so far. Other record types return `available: false`.
- Frontend: `components/VoiceAssistant.jsx` plus `context/ScreenRecord.jsx`,
  where a page publishes the record it has open via `usePublishRecord`. Only
  FilingCabinet publishes today — that is what makes the assistant available on
  a screen.
- Needs `ANTHROPIC_API_KEY`, which is set on Railway and not locally, so **this
  cannot be tested end to end on a dev machine.** Stub `assistant._call_claude`
  to exercise everything downstream of the model.


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
- **`GET /api/customer-brief`** + memory-server `/inbound` and `/lookup`: Betty now speaks from
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
- 62 orphan time entries / 209.8 hours across 15 blocks still unreconciled. The screen to
  clear them is live as of 2026-08-23, but the location history it reads has not been built on
  the live volume yet — until Brian presses *Match up my location history* on Data Gaps, the
  suggestion box is empty by design and says so.
- A full QC audit prompt is at `C:\Users\bbria\bhs-qc-audit-prompt.md` for an independent
  review of the whole ecosystem.

## The week the numbers were wrong (2026-09-27 → 29)

Several figures the app reported were wrong, in ways that all looked like separate
problems and turned out to share causes. Full write-up in the app repo at
`docs/2026-09_timeline-crossref.md`; plain-language version in Drive under
`Where We Stand`.

### The home fence was 1.6 miles from home

`BRIAN_HOME_LAT/LON` is hardcoded at `app.py:54-55`, `geofence_engine.py:290-291`
and `location_history.py:104-105`, and `_init_home_coords()` geocodes
`'360 County Road 35, Clarkridge, AR'` at import. **The address is right; the
geocode is not** — it resolves 2,542 m from where Brian actually parks. The seeded
`kind='home'` fence had therefore never matched a point in five weeks, and a
hand-dropped fence named "Saved place" (`kind='other'`, 75 m) was catching them all.

Consequence chain, and it is worth following because the fix is not where it looks:
`classify_drive()` only fires its commute branch on `from_kind == 'home'`. With home
typed `other`, that branch was unreachable, execution fell through to
`'Mixed trip - one end is personal, so not billable'`, and **`business_miles` read 0
every single day**. Setting `commute_policy` would have changed nothing — the policy
was never consulted.

Fixed by moving fence 1 to `36.4795240, -92.3387018`, widening it to **500 m** (the
driveway and the school-bus run spread 300–500 m; nearest other named place is
4,249 m, so nothing is swallowed) and deactivating the duplicate.
`location_history.home_coords()` prefers the `kind='home'` fence over the constant,
so that one change propagated to mileage without a deploy. The constants are still
wrong and would seed a fresh database wrong.

### Trips were never derived — they were imported

Every trip on file carried a `timeline-import:` note. **Not one was ever produced
automatically.** They stop on 2026-09-04 because that is where the last manual
Google Timeline import stopped, not because anything broke. September went
**8.2 mi → 186.6** and **17.62 h → 48.54** once the gap was backfilled.

### The 0.42 h entries were real work, badly measured

Four Giles visits logged exactly 25 minutes — `MIN_BILLABLE_JOB_SITE_MIN`, the floor
showing through. **The Giles site has no cell signal**; OwnTracks only posts when it
catches their guest wifi, so the point trail covers a fraction of each visit and
`duration_min` (last point inside − arrival) is honest about a trail that is not.
Days of 2+ hours logged as 25 minutes. Google's own Timeline is unaffected — 96% of
Giles time lands inside the 120 m fence, because it backfills after the fact.

Do not widen the Giles fence to compensate: David Isham, Allison and two other sites
sit within 3.2 km and would have their hours stolen.

### A gap in the trail was being sold as a drive

`_rebuild_drives()` derives a drive from each pair of consecutive visits **with no
bound on how far apart they are**. Days with no ingest were stitched into single
drives and every point between them summed as distance — a 137-mile "drive" spanning
71 hours, a 402-mile one spanning 41. Harmless as `unclassified`; the moment
`commute_policy` was set to `business`, **362.5 miles of fabricated business
mileage went live**. `MAX_DRIVE_MIN` (8 h) and `MAX_DRIVE_MPH` (100) now reject them
with a reason naming the bound broken.

### Tolerance alarms

Brian: *"any driving over 25 miles gets flagged. not to approve, but to at least be
made aware."* `ALERT_LONG_DRIVE_MI` 25, `ALERT_LONG_DAY_HOURS` 8,
`ALERT_SHORT_JOB_SITE_MIN` 30 — deliberately separate from the hard limits that
decide what gets *written*, because a figure can be writable and still worth a look.
Plus an arrival push naming the job, the service and the one-way mileage. All go out
through the same ntfy topic, injected via `set_notifier()` the way `day_digest`
takes one.

### `database is locked`

`fill_customer_coordinates()` held a write transaction open across every Nominatim
and OSRM call and committed once at the end. A throttled run of 31 recalculations
left a background thread holding the lock and **every write in the app returned 500
while reads looked perfectly healthy**. It now commits before each outbound call,
and `get_db()` sets `busy_timeout` so a blocked writer waits instead of failing.

### Still open

- The hardcoded home coordinates in all three files.
- `app.py` does not read `BRIAN_HOME_LAT/LON` from the environment at all.
- Re-evaluation **adds** visits rather than replacing them when a fence changes
  (`_find_existing_visit` keys on `geofence_id`), so the review queue inflates.
- **No MMS capture anywhere** (Oct 2026: still true of the forwarder, but there is now a
  hand-off: hold the picture in Messages, Share, BHS, and the app reads it into notes on the
  right customer). The lead model has no media field and SMS Forwarder
  reads notifications rather than the SMS database, so every photo a customer has
  ever texted has been dropped. Also why some messages arrive as
  "Sensitive notification content hidden" (12 of 787 archived).


## Session notes, 12 Oct 2026 (data and rules, no app code changed)

No dollar amounts here; this repo is public. Figures are in the app and Brian's Drive.

- **The live app is reachable from a cloud session** (`bhsmobileapp-production.up.railway.app`),
  with `Authorization: Bearer $APP_API_TOKEN`. Anything done through the same routes the
  screens use writes the same rows. This session used it to correct estimates, record payments
  and expenses, add notes and next steps, and edit the catalog.
- **The service catalog was repriced from homewyse**: labor row only, zip 72653, low/high
  midpoint, homewyse's labor wording as the description (the word "Basic" dropped). 93 existing
  items changed; items with no homewyse page (hourly rates, admin, a few odd services) kept
  their old figures. New items added to the live database (not the seed file): *Picket Fence
  Installation Labor*, *Remove Fencing*, *Buried Downspout Drain Line* (each per linear foot). A
  fresh database seeded from `service_catalog_seed.py` will not have them. Rule in
  `business/rules/estimating-rules.md`.
- **Quantity carries the unit, never 1 for measurable work** (feet, square feet, counts), with a
  per-unit price, so the price per foot is known next time. Covered in the rules file.
- **Estimate pages carry only the lines and the total.** No notes, no owner line, no footer
  (`business/rules/document-standards.md`). An **Account Summary** document (all phases, checks beside
  each service line, unfinished work separate) now exists as a hand-made PDF; the app does not
  generate it. Document layouts are built in claude.ai/Claude Code sessions, not by the app.
- **Gotcha: deleting a payment can flip a job from `in_progress` to `pending`.** To move a
  payment from one job to another, POST the new one, DELETE the old one, then
  `POST /api/jobs/<id>/start-work` if the job was in progress. (The mic assistant deliberately
  avoids this; the plain payment delete does it.)
- **Gotcha: `PUT /api/filing-cabinet/<id>` is a whole-job save.** Send back everything
  (`customer_id`, `notes`, `photos_album_url`, every line with its `id`, the time entries with
  their `id`) with only the intended line changed. Lines and time entries you leave out are
  **deleted**, and `notes` and the photo link are blanked. Line ids are kept for the ones you
  send, so their hours stay attached.
- **Known false alarm: the "said yes by text" alert.** A customer wrote that they would look at
  a re-quote ("if it's not too much trouble to refigure it ... we can look at it") and the app
  pushed *Said yes by text: tap Accept* and set that next step. Nothing was accepted. The alert
  matches soft wording; treat it as a prompt to read the thread, and correct the next step by
  hand (`POST /api/jobs/<id>/next-step`). Worth tightening the matcher before it trains Brian
  to ignore it.
- **Pictures and PDFs that Brian or a customer texts do not forward** (the forwarder passes
  text only, and a photo shows up as the word "Image"). A customer's check list, an estimate
  PDF Brian sends: none of it reaches the app. Record what was sent as a job note
  (`POST /api/jobs/<id>/notes`) and keep the file in Drive.
- **A customer's thread joins their job** when the customer's lead has `job_id` set
  (`PUT /api/leads/<id>` `{job_id}`): done for Collins. Then their texts show under the job.
- **Materials receipts**: cost-of-business items (brushes, bits, blades, pickets for his own use,
  ladders) are overhead expenses; job materials are expenses on the job with the receipt's tax
  share. The customer's reimbursement sheet lists only their items.

## Session notes, 13 Oct 2026 (the assistant, and work still to come)

No dollar amounts here; this repo is public.

- **The mic assistant is now Claude, on every screen, with hands in the app** (`8412c06`, live). It
  used to know only an open invoice, described its own limits from memory (and got them wrong),
  and answered like a form. Now: the page sends its full address and the server reads whatever is
  open (a job, a customer's file, a lead, a printed document) fresh; its list of powers is
  *generated from the code* so it cannot misstate them; it answers anything in or out of the app
  at the length the question needs; model `claude-sonnet-5-5` (`ASSISTANT_MODEL` overrides, falls
  back to the old model if the API rejects the id). Details in the BHSmobileapp `CLAUDE.md`.
- **Two write tools, both read back first and run only after a yes.** `propose_changes` edits
  records (payments, lines, hours, expenses, trips, customer and job fields). `propose_app_actions`
  does what the screens do by calling the app's own routes as the person asking (start, accept or
  decline an estimate, add a customer, notes, next step, archive, price-book changes, settings,
  stop and drive classification). Because the real route runs, a helper's switches apply.
- **Decision: the assistant does not delete a customer, job or invoice.** It offers archive (one tap
  undoes it) or, for an estimate, decline. Deleting stays in the app. Open it up only by deliberate
  choice, with a count of what goes with it in the read-back.
- **New line type: "still to come"** (`service_type = to_come`). Work quoted and not done. It stays
  on the job, prints in its own section marked "Not yet billed", is left out of the invoice total
  and so of every balance, and a job with any of it is never marked paid. This is how a
  multi-phase invoice (Giles phase D) shows only the finished work as the balance due. Marking
  existing lines this way is one assistant request ("the unstarted lines are still to come"), the
  line sheet's *Still to come* button, or the Filing Cabinet line select.
- **Giles phase D data: not changed by this session.** The code is live; Brian says (16 Oct) the six
  unstarted Phase 3 items are already marked still to come, not verified by a session. This session had no app token. Expected
  result once done: billed = finished work only, paid as recorded, balance due = the 10/12
  account update's owed figure (the $50 of check 7163 applied to the drain line stays as decided).
- Gotcha for any session: a request inside a request shares Flask's `g`, and the inner request's
  teardown closes the outer one's database connection. Nested calls go in their own thread
  (`assistant_app._call`).
