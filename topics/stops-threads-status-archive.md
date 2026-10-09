# Stops, threads, status and archive (BHS app, Oct 2026)

Decisions and behaviour from the October 2026 dress rehearsals of one full job (call, text,
estimate, work day, payment). Detail and tests live in the app repo (`CLAUDE.md`, section
"Recognising stops, threads and status", and `docs/2026-10_dress-rehearsal-fixes.md`).

## How a stop gets its name (GPS)

In order, after each location ping, for stops that match none of his saved places:

1. **A customer.** He texted that customer "be right there / on my way / I'm here" shortly
   before, or the stop is within ~120 m of a customer's address with no business closer. Named
   "<customer> - visit", counted as work, **never billed** (only a job-site fence writes hours).
2. **The nearest business on the map** (the map's point-of-interest layer, not the address
   layer: the address layer called a Dollar General stop "a house on North Church Street").
3. **Places he always goes.** If that business is already a saved place, or he parked a little
   way from one, the stop belongs to it and the place's circle grows to cover where he parks.
   Otherwise a fuel stop, a supply house or a merchant he has called personal (Dollar General)
   is saved as a place centred on the business.
4. Otherwise the street address, judged by its type only (a street named "Church" is not a
   church).

His texts from 3 hours before to 30 minutes after a stop are attached to it ("headed to get
Sandeep and nailer", "SENT TO GILES"). Hints only: nothing here bills, logs an expense or
overrides a stop he classified by hand. "What was that stop?" is only asked about what the app
could not work out.

Google Takeout "Saved Places.json" can seed his regular places (script in the app repo,
preview first, checked against the real map).

## Threads: nothing a customer says goes unseen

Every customer text or call sends one notification. A customer with an estimate out writing
"go ahead / looks good / when can you start" sends "X said yes" and sets the job's next step.
An estimate changed by their text sends a notification with the old and new total.
**Nothing is accepted automatically**: Accept is his tap, and it locks the estimate against
later rewrites.

## Status path

lead -> estimate (built by itself) -> Looks good -> customer says yes (alert) -> Accept
(pending, EST becomes BHS) -> first hours from the clock (in-progress, automatic) -> payment
covers the total (paid, fence off). "Completed" is manual (finished, not yet settled).

## Numbering

A taken number moves to the next date (see `topics/document-standards.md`).

## Archive (6 months)

Finished and settled work (paid, completed with nothing owed, declined estimates) and customers
with nothing open and nothing new for six months are **flagged**, never deleted, and hidden from
the everyday lists and search unless "Show archived" is ticked. Anything new for that customer
or job brings it back automatically. Reports and the Dashboard still count everything. A job
still owed money is never archived.
