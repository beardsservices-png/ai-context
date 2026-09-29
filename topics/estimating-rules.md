# Estimating Rules

Pricing rules behind every BHS estimate. Governs hand-built estimates
(claude.ai + ReportLab) and anything the app generates through
`POST /api/estimate/from-scope`. If the two disagree, this file is the intent and
the code is wrong.

## Hard rules

- **Labor only.** Materials are never bundled into a line item. All materials are
  purchased by the homeowner directly from the supplier. An estimate that quotes a
  material price is wrong even if the number is right.
- **Flat rate, Qty always 1.** Every line item is `Qty 1` with a flat amount. Hourly
  rates and hour counts never appear on a customer-facing document. The app computes
  hours internally (`est_hours_per_unit`) for profitability — that stays internal.
- **No payment language, anywhere.** Deposit terms, payment timing, "no upfront
  payment required", "due on completion" — none of it appears on any estimate,
  invoice, footer, or cover letter. Brian handles every payment conversation
  directly, in person or by phone. This has been corrected on generated documents
  more than once; check the footer before sending.
- **Round to the nearest $5.**

## Pricing philosophy

- **Value-based, not time-based.** Prices reflect what the work is worth in this
  market. They are not back-calculated from a target hourly rate. The implied hourly
  rate is a diagnostic Brian looks at after the fact, not an input.
- **Homewyse is the benchmark** for the Mountain Home market — take the low/high
  range and quote from the midpoint. Same model the `service_catalog` table uses.
- **Prices run lean.** Low overhead, solo operator, high efficiency. Deliberately
  below market. Do not "correct" a price upward toward a national average.
- **Collection rate is not a pricing input.** 99%+ collection is a fact about the
  customer base, not a signal to raise prices.

## Structural conventions

- **Installation and plumbing connections are separate line items.** A complication
  in the connection must not inflate the cost of the install, and vice versa. Same
  logic anywhere one task can go sideways independently of another.
- **Baseboard removal is inherent to flooring work** — part of the flooring line,
  discounted accordingly, not billed separately.
- **Touch-ups are rare and narrow** (corners, edges). Not a catch-all line.
- **Optional items** render in `Helvetica-BoldOblique` and are excluded from the
  subtotal. Use the `amount` field directly rather than `price × qty` when totaling,
  or optionals will silently land in the total.
- **Large jobs split into phase estimates**, sequenced around practical constraints —
  what the customer can live with, what has to dry before the next thing starts,
  dependency order. Phases take letter suffixes.

## Where the line-item copy lives

Standardized service titles and descriptions are **in the app**, not in this repo:
`service_catalog` (140 items / 22 trades) seeded from `api/service_catalog_seed.py`,
with `service_catalog_aliases` mapping the 168 legacy InvoiceBee category strings
onto them. Edit descriptions there. Do not keep a second copy of that text anywhere
else.
