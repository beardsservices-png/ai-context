# BHS App

The core Beard's Home Services business management app.

- **Stack:** Python / SQLite, hosted on Railway, source in GitHub org `beardsservices-png`.
- Automation/hosting is Railway — deliberately not n8n.
- **Estimates/invoices:** generated with ReportLab, matching an "Order Summary" style layout. Base script `bhs_estimate_generator.py`, numbering scheme `BHS-YYMM-##`, all line items non-taxable, footer notes owner-operator / no upfront payment.
- **SMS pipeline** (`SMS-Extractor_BHS`): Railway IPv4 fix applied, Pydantic timestamp fields corrected. Body-template tokens on the phone proved unreliable, so the webhook also accepts `from`/`message`/`contact`/timestamps as URL query params and ignores any field that arrives as an unresolved `{{token}}`.
- **SMS outgoing messages:** the phone now forwards Brian's sent texts as well as received ones, so extraction sees both halves of a conversation (a customer's "142 Oak Ridge Rd" only parses as an address next to the question that prompted it). Direction comes from a literal `&direction=sent` in the outbound rule's URL, backed up by matching the sender against `OWNER_PHONE`. Outgoing messages are stored as context but never extracted or notified on. Phone numbers are normalized to 10 digits as the thread key so both rules' formatting lands in one thread.
- **Location/timeline feature:** Google Maps Timeline data integrated with the SQLite DB via Haversine matching (~16 months of location data).
- Includes an invoice/time-tracking database and a task management board built into the app.
- History: built an "OPS CENTER" HTML dashboard as the operational front end.
