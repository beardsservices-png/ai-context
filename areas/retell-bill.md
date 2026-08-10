# Bill (AI Phone Receptionist)

- Built on Retell AI + ElevenLabs.
- Prompt restructured into separate call flows for returning vs. new callers, after debugging behavioral failures.
- Pre-call webhook spec drafted for injecting customer context before the call starts.
- Backed by `bhs-memory-server` (Node/Express + `node:sqlite` on Railway): caller memory, dashboard, callback form, estimates.

## Callback → estimate flow

Call comes in → push notification links to `/callback/:phone` → Brian calls back with the
form open → **Create Estimate** renders a customer-facing document he can print or save as
PDF from his phone.

- The form autosaves as he types (debounced, plus a `pagehide` beacon) — he's mid-call and
  won't press a save button. Drafts live in their own `callbacks` table so a later call from
  the same customer can't overwrite pricing already worked out.
- Service-specific qualifying checklists come from `checklists.js`, matched on keywords in
  the caller's stated service.
- Pricing is editable line items, not fixed labor/materials fields; the total is computed
  from the rows so it can't drift.
- Estimate numbers: `BHS-YYMM-##`, sequential within the month, assigned on first open and
  frozen thereafter so reprints match what the customer was quoted.
- Estimate documents are print-styled HTML rendered by the server, not ReportLab — the BHS
  app's `bhs_estimate_generator.py` remains separate.
