# Estimating Rules

Pricing rules behind every BHS estimate. Governs hand-built estimates
(claude.ai + ReportLab) and anything the app generates through
`POST /api/estimate/from-scope`. If the two disagree, this file is the intent and
the code is wrong.

## Hard rules

- **Labor only.** Materials are never bundled into a line item. All materials are
  purchased by the homeowner directly from the supplier. An estimate that quotes a
  material price is wrong even if the number is right.
- **Never quantity 1 for anything that can be measured** (Brian, 2026-10-12). Feet, square
  feet, a count of items: the line carries that quantity and a per-unit price. A drain line
  billed as "1 @ a lump sum" tells you nothing next time; "25 lin.ft. @ a per-foot price" does.
  Quantity 1 is only for a true single thing (one inspection, one service call). When a
  job is priced as a lump sum, divide it by the measured quantity and save the per-unit
  price to the app catalog so the next quote starts from it.
- **Quantity carries the catalog unit** (Brian, 2026-10-08). A fence is `84 lin.ft.` at
  a per-foot price; a one-off item is `1` at a flat amount. Hourly rates and hour counts
  never appear on a customer-facing document; `est_hours_per_unit` stays internal.
- **The page is the lines and the total, nothing else.** No Additional Information, no
  notes, no owner line, no thank-you, no materials, no shopping list.
- **No payment language, anywhere.** Deposit terms, payment timing, "no upfront
  payment required", "due on completion" — none of it appears on any estimate,
  invoice, footer, or cover letter. Brian handles every payment conversation
  directly, in person or by phone. This has been corrected on generated documents
  more than once; check the footer before sending.
- **Round lump-sum lines to the nearest $5.** Per-unit prices may carry cents.

## Pricing philosophy

- **Value-based, not time-based.** Prices reflect what the work is worth in this
  market. They are not back-calculated from a target hourly rate. The implied hourly
  rate is a diagnostic Brian looks at after the fact, not an input.
- **Homewyse is the benchmark** for the Mountain Home market — take the low/high
  range and quote from the midpoint. Same model the `service_catalog` table uses.
  **Use the LABOR row only, at zip 72653.** The catalog was repriced this way on
  2026-10-08 (93 items; homewyse's labor description replaces ours, "Basic" dropped).
  Items with no homewyse page (hourly rates, admin, a few odd services) kept their
  old figures. New services go in the same way: homewyse page → zip 72653 → labor
  low/high → midpoint.
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
`service_catalog` (about 145 items / 22 trades) seeded from `api/service_catalog_seed.py`,
with `service_catalog_aliases` mapping the 168 legacy InvoiceBee category strings
onto them. Edit descriptions there. Do not keep a second copy of that text anywhere
else.

## Materials reimbursements (Brian, 2026-10-09)

- **Cost of business, never billed to a customer:** paint brushes, drill bits, utility
  blades, pickets bought for his own use, ladders and other tools. Record them in the app
  as overhead expenses (`is_overhead=1`, category *Tools & Equipment*).
- **Job materials** on the same receipt are split out, each with its share of the
  receipt's sales tax, and recorded as expenses on the job.
- **The reimbursement sheet** uses the same Order Summary layout as an estimate:
  Date | Home Depot Receipt | Amount, then the total, any materials check received, and
  Amount Due. Only the customer's items are listed.
- **A materials check paid in advance** counts against labor until Brian presents the
  receipts, and **Brian decides where each check lands** (see Giles below). Do not assume
  it goes to receipts first.
- **Only the receipts Brian hands over go on the bill**, not every purchase found in Gmail,
  and an older receipt he says was already paid back stays off.
- **Brian decides where a check lands.** Giles (2026-10-10): the materials check paid off the
  Phase 2 final inspection, the remainder went to the Phase 3 buried downspout drain line, and
  one bill carried both services plus three receipts. Figures are in the app (jobs 111/112),
  not in this public repo.
- **The customer's own check list is the record of check numbers and dates.** Giles texts a
  photo of theirs; use its numbers and dates, and flag any date that differs from the app
  instead of changing the app. A check that reimburses supplies is listed on the Account
  Summary but is not a payment against an invoice (see `business/rules/document-standards.md`).
  Where the customer's sheet files part of a check as labor and the bill applied it to
  materials, the Account Summary shows the split on that check so they can see where it went.
- **Re-quote on a changed request.** When a customer changes the layout after an estimate
  (width, gate size, method), the old estimate is out of date: say so on the job, then
  re-quote from the new scope. Do not leave the old number as the live one.
