# Document Standards

How BHS customer-facing documents are built and named. Applies to the ReportLab
generator and to anything the app renders — a document produced by the app should be
indistinguishable from one produced in a claude.ai session.

## Numbering

Canonical scheme (supersedes the older `BHS-YYMM-##` note in earlier context files):

- An estimate is `EST` + date: **`EST20260907`**
- On conversion to an invoice **the number does not change** — only the prefix:
  `EST20260907` → **`BHS20260907`**. Same job, same identity, start to finish.
- Two on the same day take a suffix: `EST20260907-2` → `BHS20260907-2`
- Multi-phase estimates take a letter suffix per phase: `BHS20260627A`, `B`, `C`, `D`
- Once converted, **the estimate is archived or hidden** — never left live alongside
  the invoice. A customer must never hold an estimate that contradicts an invoice.
- **The prefix is not stored.** `api/app.py` derives it from status at display time
  (`'EST' if status == 'estimate' else 'BHS'`). Status carries the meaning; the
  number is only identity. Do not encode state into the number.
- Jazzy's pay invoices are a separate series: `JBHS-YYYYMM-##`

## Filenames

- Estimates: `EST[YYYYMMDD]_[ClientName]_Estimate.pdf`
- Invoices: `BHS[YYYYMMDD]_[LastNameFirstName]_Invoice.pdf`

## Rendering

Python / ReportLab, **canvas-based** — not platypus/flowables. Base script
`bhs_estimate_generator.py`.

- Logo fetched from its GitHub-hosted URL, cached at `/tmp/bhs_logo.png`
- Output to `/mnt/user-data/outputs/`
- All line items non-taxable (`*`)

### Visual

| Element | Value |
|---|---|
| Header | teal `#3a9abf` |
| Added items | green `#1a6b2a` |
| Revised items | amber `#8b4500` |
| Table rows | light gray, alternating |
| Price/amount columns | `drawRightString` |
| Optional items | `Helvetica-BoldOblique`, excluded from subtotal |

### Layout

```python
rowh    = (len(wrapped)) * 0.126 * inch + 0.26 * inch
col_qty = W - MARGIN - 2.55 * inch
col_prc = W - MARGIN - 1.05 * inch
```

Row heights are dynamic via `textwrap.wrap()`.

## Header block

- Phone: strip `+1`, display as `(XXX) XXX-XXXX`
- Business block: Beard's Home Services / 870-321-1072 /
  `brianb@beardshomeservices.com` / Mountain Home, Arkansas 72653 /
  `https://beardshomeservices.com/`

> **The old `beardsservices.com` address is dead and must not be used.** The domain
> moved to `beardshomeservices.com` in August 2026 (see `areas/website.md`).
> `brianb@beardsservices.com` **bounced on a live customer send** — the Giles
> materials reimbursement on 2026-07-28, "domain not found" — because it was still
> sitting on the estimate letterhead. Any generator, template or saved document
> still carrying the old domain wants correcting before it is sent again.

## Footer

Owner-operator note only. **No payment, deposit, or timing language** — see
`topics/estimating-rules.md`. Older generated documents carry a "no upfront payment
required" line in the footer; that line is not wanted and should be stripped wherever
it survives, including in `bhs_estimate_generator.py` itself.
