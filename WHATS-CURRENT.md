# What's current

**Last updated 5 October 2026 (evening).** One page: what is live, what is built but not live, what Brian asked for, and what each customer was last sent.

This repo is public, so there are no addresses, phone numbers, emails or money in here. The plain-language version with those details lives in Brian's Drive under *Where We Stand*.

**Keep it current:** whoever changes what is live, or what a customer was sent, updates the matching line below and its date. A line with no date is not to be trusted.

**Checked on 5 Oct:** the BHSmobileapp code on GitHub, Brian's personal Gmail Sent folder (last 60 days), and the Where We Stand files of 29 Sep.
**Not checked:** Brian's texts, the live app's data, the business Gmail account, and the unmerged branches of the other repos (CAD, ai-context, bhs-memory-server).

## 1. Live in the app (`BHSmobileapp` `main`)

- **5 Oct, `c68c481`: other people can sign in, limited to the sections Brian picks** (Settings -> People). **Live, but the login itself is OFF**, so nothing has changed for anyone yet. Details in `areas/bhs-app.md`.
- **5 Oct, `fdaad3c`: the login, safer print links, and a database-download hole closed.** **Live, login OFF.** The admin routes used to accept an empty key when `ADMIN_KEY` was unset; they now refuse everything in that case.
- **5 Oct, `3c0d1da`: leads keep a draft estimate current.** See `areas/bhs-app.md`. Railway reported the build **successful** at 11:38 UTC on 5 Oct, so it is live.
- **5 Oct, `f6b77de`:** clock double-billing fix, and the screen that counted silence as driving.
- **4 Oct:** two text-forwarding fixes (the webhook accepts its secret from wherever the forwarder puts it; forwarded texts are stamped with a timezone so the Leads screen stops showing wrong times).

## 2. Built, but NOT live (sitting on branches)

| What it does | Branch, date | Status |
|---|---|---|
| A customer texts "put the invoice in my husband's name" and the app changes who or where the document is addressed, with Undo. Prices and line items are deliberately not touched. | `claude/sms-order-updates-akhp2q`, 1 Oct | Does not merge cleanly into `main`, and now also overlaps the 5 Oct lead-drafts work (both edit `api/app.py` and `CLAUDE.md`). Needs a hand merge. |
| Show the text conversation on a lead instead of a count | `claude/determined-sagan-ra9rfp`, 18 Sep | Unmerged. |
| Invoice preview matches the Order Summary layout | `claude/callback-form-estimate-flow-elhdaw`, 14 Aug | Unmerged. Check it is still wanted. |

`claude/claude-md-docs-lojo8m` (June) is a separate history with a different root commit. Never merge it.

## 3. What Brian asked for most recently

An estimate that is created by itself on a lead once it has a name, an address and what the customer wants, and that updates by itself when a text arrives, when Betty's summary arrives, or when Brian speaks or types a change. Every Claude session should see the same thing. If a customer such as Giles texts "change this, this and this", the scope and estimate change.

- **Lead stage: built, merged to `main` and deployed 5 Oct.** The draft re-figures from the whole lead record whenever a text, a call summary, a reply or a note lands. It starts once there is a name, an address and a request. It says what changed and why. If Brian has hand-edited the estimate, new information waits for one tap (*Use the new estimate* / *Keep mine*) instead of overwriting his numbers. Brian first said "change everything automatically", then asked Claude to work out the best way; this is that answer.
- **One way in and out for any session:** `GET /api/leads/<id>/file` reads everything on a lead, `POST /api/leads/<id>/notes` adds what was learned. A session can only use them if it can reach the live app. Cloud sessions cannot unless the environment's network setting allows it; a session on Brian's laptop can.
- **Job stage: NOT built.** A lead that has become a job (Giles) is not touched, because the estimate or invoice there is a document the customer may be holding. The recommended next step is a proposed change with one-tap apply, not an automatic edit. The 1 Oct branch covers only who or where a document is addressed.
- **Untested against the live model.** The tests stub the pricing call, so watch the first real drafts.

## 4. Customers: what was sent, and how

As of the dates shown. Texts are not visible to Claude.

| Customer | Last thing seen | How | Waiting on |
|---|---|---|---|
| Jane Shuberidge (door widening) | Called Betty 24 Sep. Betty said Brian would estimate and asked for pictures and measurements. | Phone | Brian's callback. None recorded as of 29 Sep. |
| Horseshoe Bend slab (about 1,600 sq ft) | Called Betty 24 Sep. | Phone | Brian's callback. None recorded as of 29 Sep. |
| Giles | 25 Sep: Brian emailed a Home Depot list for the punch list and said he would rather pick the items up with a check. | Email | Phase 3 section 3.1 is complete and due. Section 3.2 was about to start on 28 Sep. The materials check of 28 Sep counts against labour until the receipt is shown. |
| An estimate emailed 5 Sep to a Hotmail address (customer not identified here) | The customer replied the same day: no attachment arrived. | Email | A resend. None appears in the personal Sent folder since. It may have gone by text or from the business Gmail, which Claude cannot read. |

## 5. What nobody can see

- **Texts Brian sends and receives.** They live on his phone. The app only sees incoming texts when SMS Forwarder is on. On 29 Sep it was not installed on the new phone (nothing since 20 Sep). The 4 Oct fixes suggest it was being worked on. Test: send a text and see whether it shows on the Leads screen.
- **Anything sent from the business Gmail account.**
- **What was sent to whom.** The app records none of it: it sends nothing, and Brian shares PDFs from Drive on his phone. This page is the only list.

## 6. Do these first

0. **Decide when to switch the login on.** It is built, tested and deployed but dormant. Switching it on means setting `APP_PASSWORD` (and `APP_SECRET`, `APP_API_TOKEN`) in Railway. Effects: Brian signs in once per phone; print links copied before then stop working (copy new ones); the text forwarder, location tracker and Betty keep working on their own tokens (tested). Remove `APP_PASSWORD` to switch it off again. Staff accounts can only be added once it is on.

1. Confirm a text reaches the Leads screen.
2. Call Jane Shuberidge and the Horseshoe Bend slab caller, if not already done.
3. Resend the 5 Sep estimate, if not already done.
4. Watch the first real lead drafts; the pricing prompt has not met the live model.
5. Decide what happens to the 1 Oct and 18 Sep branches (merge or drop) before building the job stage.
