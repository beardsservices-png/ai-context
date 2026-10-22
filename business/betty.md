# Betty (AI phone receptionist)

**Live.** Retell AI agent + ElevenLabs voice (`11labs-Grace`, female). Renamed from Bill
on 2026-09-06 when the voice changed; older notes and some code still say "Bill".

- Repo: `beardsservices-png/bhs-memory-server` (Node, **Railway, auto-deploys from `main`**).
  Remembers callers, feeds Betty context at call start (`/inbound`), pushes callback reminders.
- When a call ends, Retell posts the call (summary, caller details, `recording_url`) to the BHS
  app's `/api/webhook/call`, which files a lead and forwards the same body to the memory server.
  No n8n or other middleman, deliberately.
- Since 2026-10-19 the app keeps the recording link and the lead has a *Hear the call* player.

- Built on Retell AI + ElevenLabs.
- Prompt restructured into separate call flows for returning vs. new callers, after debugging behavioral failures.
- Pre-call webhook spec drafted for injecting customer context before the call starts.


### Betty greets by name, then asks for the name (2026-09-06)

Two independent causes, both found by reading the live Retell API rather than any local file.

**1. `caller_name_on_file` was blank on every returning call.** The memory server's `/inbound`
read the name only from its **own** `callers` record, whose name field is written by the
post-call webhook and is usually empty — while the BHS app knew exactly who was ringing. The
name reached Betty only as a sentence inside `caller_context`. Enough to greet with, not solid
enough to satisfy the prompt's "you already have their name" test.

Fixed in `bhs-memory-server` (`ed76ba2`): the name falls back to `brief.customer_name`, the
`caller_context` line is built from the same value so prose and variable cannot disagree, and
**`callback_number_on_file` defaults to `from_number`** — they are calling from it, so it never
needed a lookup. `test-inbound.mjs` seeds the exact failing shape (a nameless caller record for
a number the business knows) and checks all of it.

**2. The bigger one: live calls run agent version 15.** Not the newest, not the newest
published.

| | |
|---|---|
| Serving every recent call | **agent v15**, llm v15, prompt **4,966 chars** |
| Newest published | agent v20 / llm v20 |
| Newest of all | agent v21 / llm v21, prompt 9,508 chars — **unpublished** |

v15 predates the returning-caller work entirely — no Flow A/B split, just
`- "Can I get your name?"` unconditionally. v21 is the careful one that says *"Nowhere in this
flow do you ask for either one"* three separate ways. **The greeting comes from the memory
server's `agent_override.begin_message`, which works regardless of prompt version** — which is
exactly why Betty greets by name and then asks for it.

This is the second time a corrected prompt sat in a file and never reached the running agent:
`VoiceAgent/william-preprompt-updated.txt` (March) had the same fix and was never pasted in.
**A prompt is not live until the agent version serving the phone number uses it.**

`+18707063071` shows `inbound_agent_id: None` in Retell — calls arrive over Twilio
(`twilio-callsid`, `diversion` headers present), forwarded from `+18703211072` on no-answer, so
the agent version is pinned somewhere in that routing, not on the Retell number record.

**3. The phone number was pinned to a version.** This is the one that mattered most:

```
+18707063071  inbound_agents = [{agent_version: 15, ...}]
              last modified   = May 2026
```

Retell lets a number pin an exact agent version, and this one had. **Publishing does nothing
when the number names a version** — so every prompt improvement from v16 to v21 had been
invisible since May. Editing a prompt in the dashboard and never seeing a behaviour change is
the symptom of exactly this.

> **When a prompt change seems to have no effect, check the phone number's `inbound_agents`
> pin before touching the prompt again.** Three separate corrected prompts had piled up unused
> behind this: the March file, the unpublished v21 draft, and everything in between.

### Now live (2026-09-06)

- Agent **v21 published** and `+18707063071` repointed to it, inbound and outbound.
- Renamed **Bill -> Betty**, voice changed to **`11labs-Grace`** (ElevenLabs, American,
  middle-aged female) at `voice_speed 1.0`. The old voice was `custom_voice_4e5a...`.
  Renaming was forced by the voice change: the prompt had her say "this is Bill" in three
  places.
- Flow now decided by `{{caller_name_on_file}}`, not by reading a name out of prose.
- Latency/quality: `begin_message_delay_ms` **800 -> 400**, `enable_backchannel` **on**,
  `max_call_duration_ms` **211s -> 480s** (3.5 minutes could cut off a caller mid-description).
  `stt_mode` was already `fast`; `responsiveness` 0.64 and `interruption_sensitivity` 0.3 left
  alone deliberately — changing several conversational dials at once makes a regression
  impossible to attribute.
- Verified live: `/inbound` returns `caller_name_on_file: 'Heath Johnson'`,
  `callback_number_on_file: '<their number>'`, greeting *"Hey Heath..."*.

Backup of the pre-change prompt: `~/Backups/retell-llm-v21-backup-2026-09-06.json`.

> `NTFY_TOPIC` is **hardcoded** at `server.js:8` in the memory server
> (same topic; name not repeated here). That is why Betty's call notifications always worked while the BHS
> app's lead alerts never did — the app read an env var nobody had set.

The stale local clone at `VoiceAgent/bhs-memory-server` was 12 commits behind and has been
deleted; work from a fresh clone of `beardsservices-png/bhs-memory-server`.


## Betty's live knowledge

`GET /api/customer-brief?phone=` on the BHS app returns current state as structured fields plus
a **speakable prose block** (Retell injects dynamic variables as text). ~220ms live.

- `bhs-memory-server` `/inbound` calls it at call start, budgeted 2.5s with an AbortController;
  any failure degrades to the old thin context rather than costing the greeting. It also now
  handles a caller the memory server has never seen but the business has — a customer who has
  only ever texted gets greeted by name.
- `POST /lookup` on the memory server is the mid-call version. **Requires a custom function
  pointing at it to be added in the Retell dashboard** — not configurable from code. Everything
  else works without it.

**Financial boundary, deliberate and structural.** Betty gets the invoice *including the agreed
amount* — it exists the moment the customer approves the work, so it is the record of the job
and its terms, and the customer already knows that number. Betty never gets payment history or
balances: the endpoint **never queries the `payments` table**, so there is no balance to leak
because none is computed. Nothing financial is written into the memory server's `callers`
record either. Brian's rule: *"the other homeowners won't like an AI knowing financial
records."*

## Memory server pages need the key (22 Oct 2026)
`/callers`, `/callback/:phone`, `/dashboard` and `/test-notify` were open to anyone with the address and returned the whole caller list. They now require `WEBHOOK_SECRET` (`X-Webhook-Token` header or `?token=`); the BHS app's `callbacks.py` sends it. `/inbound` and `/lookup` stay open for Retell, but now log whether Retell's signature is present. Enforce the signature once the logs show it arrives (found during the Railway env-var breach, 21 Oct).
