# APPS — everything Brian has built

One page for everything Brian has built: servers, Node/JS projects, static sites, single-file HTML tools, claude.ai artifacts, skills. Every entry has a **Kind** so you can tell them apart. Shared by all Claudes (claude.ai, Claude Code terminal, Claude Code in VS Code, Claude Code on the web). Started 6 Oct 2026 from the project files, `WHATS-CURRENT.md`, Brian's Claude memory and past chats.

**This repo is PUBLIC: no addresses, phone numbers, emails or money. Customer names are fine.**

## How to add your 2 cents

1. Find the app's section. Add a line under its `Notes` list. Never rewrite or delete another Claude's line.
2. Format: `- YYYY-MM-DD · surface · what you learned or changed` (surface = `claude.ai`, `CC-terminal`, `CC-vscode` or `CC-web`)
3. If a line is wrong, add a new line saying so. Don't edit the old one. Brian or the next session tidies up.
4. New app or tool, or one missing from the list? Copy the template at the bottom and add it in the right group.
5. Kind words: `Python/Flask` · `Node server` · `React/Vite` · `Static site` · `Single-file HTML` · `Claude artifact` · `Skill` · `Mobile (Kotlin)` · `Config/infra`.
6. Status words: `Live` · `Built, not live` · `Prototype` · `Planned` · `Archived`.
7. Confidence tags: `[repo]` = checked against code or a project file. `[chat]` = from a past conversation or memory only, not re-verified. Upgrade a `[chat]` to `[repo]` when you verify it.
8. Big detail goes in the app's own file under `business/` or `personal/` (see `README.md`). This page is the index, not the manual.
9. Finished means merged to `main`. Don't leave an edit on a branch.

## A. Business systems

### BHS app (BHSmobileapp)
- **Kind:** Python/Flask + React/Vite · **Status:** Live · **Repo:** `beardsservices-png/BHSmobileapp` (private, canonical) · **Host:** Railway, auto-deploys on push to `main` · **Detail:** `business/bhs-app.md`
- **What it is:** Python/SQLite + React business manager for Beard's Home Services. Runs on Brian's phone.
- **Features** `[repo]`
  - Customers, jobs, invoices and estimates. `EST`→`BHS` numbering keeps one number for a job's life.
  - Service catalog: 140 items, 22 trades, low/high range, midpoint is quoted, est. hours per unit.
  - Scope→estimate (`/api/estimate/from-scope`): plain English in, priced lines out. The model never sees or returns a price.
  - Leads inbox: texts and Betty's calls land as leads. Junk is filtered into a Spam tab.
  - Lead drafts: each lead keeps a draft estimate that re-figures itself when anything lands. Brian's hand edits are never overwritten.
  - Callback form (`/callback/:leadId`) with autosave and implied hourly rate shown before quoting.
  - GPS time clock, hours, trips and mileage (one way, by design), location history from Maps Timeline.
  - Orphan-hours matcher, evening recap push (8pm), win/loss report with close reasons, P&L report.
  - Payments and invoice module, PDF invoice import, Filing Cabinet, Data Gaps screen.
  - Mic assistant: speech, whole-business reads, edits only after an exact read-back and a "yes". Audit log at `/api/assistant/audit`.
  - Login and staff accounts: built and deployed but dormant until `APP_PASSWORD` is set.
  - `GET /api/customer-brief`: what Betty knows at call start. Never includes payments or balances.
  - Receipts item by item with *What did I use?* history; walkthrough recordings transcribed into the estimate (31 Oct 2026).
- **Artifacts:** ReportLab estimate/invoice PDFs (`bhs_estimate_generator.py`); earlier "OPS CENTER" HTML dashboard; early Access-database and PWA attempts (2025, superseded).
- **Open:** Login still off. Job-stage auto-update not built. Seeded catalog prices are starting figures, not Brian's real rates. 62 orphan time entries unreconciled. Unmerged branches are listed in `WHATS-CURRENT.md`.
- **Notes**
  - 2026-10-06 · claude.ai · Section created from `areas/bhs-app.md` and `WHATS-CURRENT.md`.
  - 2026-10-25 · CC-web · `areas/` files are now one-line pointers; detail lives in `business/bhs-app.md` (+ `-history`, `-stops-threads`). Detail paths on this page updated to match.
  - 2026-10-31 · CC-web · Receipts (`/receipts`) and walkthrough recordings (estimate step 2) shipped; the claude.ai Receipt Ledger artifact is superseded by the app.

### bhs-memory-server
- **Kind:** Python server · **Status:** Live · **Repo:** `beardsservices-png/bhs-memory-server` (private) · **Host:** Railway, project *Memory Server for Retell Agent*, deploys on push to `main` · **Detail:** `business/betty.md`, `business/bhs-app.md`
- **What it is:** Server behind Betty. `/inbound` pulls the customer brief at call start (2.5s budget, then falls back). `/lookup` is the mid-call version. `[repo]`
- **Open:** `/lookup` needs a custom function added by hand in the Retell dashboard.
- **Notes**
  - 2026-10-06 · claude.ai · Repo name and branches not re-checked. Unmerged branches there were not checked.
  - 2026-10-25 · CC-web · Repo name confirmed: `bhs-memory-server` (private), last push 22 Oct. Branches still not checked.

### Betty (was Bill) — AI phone receptionist
- **Kind:** Config/infra (Retell + ElevenLabs) · **Status:** Live · **Stack:** Retell AI + ElevenLabs · **Detail:** `business/betty.md`
- **Features** `[repo]`: female voice, introduces herself as Betty. Separate call flows for returning vs new callers. Greets known callers by name from the customer brief. Asks for photos and measurements. Feeds the Leads inbox.
- **Notes**
  - 2026-10-06 · claude.ai · Older notes still say "Bill". The agent name changed; the code and docs still use `bill` in places.
  - 2026-10-25 · CC-web · `areas/retell-bill.md` was never in the repo; the Betty file is `business/betty.md`.

### Website — beardshomeservices.com
- **Kind:** Static site (HTML/CSS/JS) · **Status:** Live · **Repo:** `beardsservices-png/beardsservices-site` · **Host:** Cloudflare Pages, mail via Cloudflare Email Routing · **Detail:** `business/website.md`
- **Features** `[repo]`: homepage, 6 service pages (concrete, roofing, decks, bathroom remodel, flooring, handyman), blog, sitemap in Search Console. Installable PWA, hamburger nav, sticky Call/Text/Quote bar, accessibility pass. Quote form is `mailto`-based.
- **Notes**
  - 2026-10-06 · claude.ai · Domain moved from beardsservices.com (Aug 2026). Some older notes and memory still say the old name.

### Draft Studio (CAD app)
- **Kind:** Node server (zero deps) + ES modules · **Status:** Live · **Repo:** `beardsservices-png/CAD-` (public) · **Host:** Railway, project *Cad*, auto-deploys · **Detail:** `business/draft-studio.md`
- **Features** `[repo]`: plan, elevation and 3D from one model, in inches. Materials takeoff from labels. Build-step playback. Cloud Save to Projects. Examples library.
- **Artifacts:** Examples `covered-patio-plan`, `l-shaped-porch-windows`, `l-shaped-porch-long-side` (Giles). Customer plan-set PDFs and the "what to get" sheet via `plansheet.py`.
- **Open:** Cloud sessions can't write to Projects (egress proxy). No link yet from a BHS job to its drawings.
- **Notes**
  - 2026-10-06 · claude.ai · Unmerged CAD branches not checked.
  - 2026-10-25 · CC-web · The first Draft Studio (static, 2D shape library, Jul 2026) is in repo `Rubiks` despite the name (`package.json` name `draft-studio`). It's the predecessor of `CAD-`; nothing Rubik's-cube related is in it. `[repo]`

### Claude skills (BHS)
- **Kind:** Skill · **Status:** Live, in claude.ai · **Detail:** `SKILL.md` · `[chat]`
- **Skills:** `bhs-brand`, `bhs-estimate-generation`, `bhs-job-scoping`, `bhs-tool-build`, `site-to-plans`, `sync-context`, plus an analytical-framework skill and a meta-skill observer.
- **Notes**
  - 2026-10-06 · claude.ai · Skill list taken from the skills visible in claude.ai on 6 Oct. Skill sources may live elsewhere. Please record where.
  - 2026-10-25 · CC-web · The same `bhs-*`, `site-to-plans` and `sync-context` skills also load in Claude Code on the web as account skills, so they're stored on the claude.ai account, not in a repo. `sync-context`'s own file is `SKILL.md` in this repo.

### JazzyTraining
- **Kind:** React/Vite/Tailwind · **Status:** Live (Railway, project *JazzyTraining*) · **Repo:** `beardsservices-png/JazzyTraining` · `[repo]`
- **What it is:** Onboarding course for Jazzlyn: 6 phases, 18 modules of BHS operations, plus a 10-step simulation of a job from first call to final review. Companion: Operations Training Manual (~13k words), lead-to-invoice SOP, Claude onboarding file.
- **Notes**
  - 2026-10-06 · claude.ai · Repo name not recorded in memory. Please add.
  - 2026-10-25 · CC-web · Repo is `JazzyTraining` (public). Checked against its README.

### BHS Team Training (general version)
- **Kind:** React/Vite (guess) · **Status:** Built (Railway project *Business Training Template*) · **Repo:** `beardsservices-png/Training-Business-Template` · `[repo]`
- **What it is:** Self-paced training app for anyone helping run the BHS business side: social, customer communication, estimates, invoicing, time/expense tracking, reviews. The non-Jazzlyn-specific version of JazzyTraining.
- **Notes**
  - 2026-10-25 · CC-web · Added from the repo README. Kind guessed from its sibling; check `package.json`.

### Task Board
- **Kind:** Single-file HTML · **Status:** Built (Railway project *Taskboard*) · **Repo:** `beardsservices-png/Task-Board-Apps` · `[chat]`
- **What it is:** "Beard's Master Task Board" — see section D. This is most likely where `task-board.html` lives.
- **Notes**
  - 2026-10-25 · CC-web · Repo has no README; contents not checked.

## B. Music and creative tools

### Rhythm Shop (Rhythm-Maker)
- **Kind:** Node server (zero deps) + vanilla JS front end · **Status:** Live (Railway, volume at `$DATA_DIR`) · **Repo:** `beardsservices-png/Rhythm-Maker` · **Detail:** `personal/rhythm-shop.md`
- **Features** `[repo]`
  - Practice Mode: learn flute (mic, octave-agnostic) or piano (mic, octave-exact). Each note lights up and turns green when held in tune. "Watch my hands" is beta. Ask-a-music-question helper. Pitch detector is McLeod Pitch Method.
  - BHS Studio (small DAW): playable 808 bass, drum lanes, mic loop recording, section arrangement, mixer with shared reverb/delay, auto-master, WAV export, "Ask Claude" edits the song by tool use.
  - Retired: Freeplay and Round Robin.
- **Open:** Flute fingering chart not checked against a method book.
- **Related prototype:** an AI "Rhythm Machine" (Claude-generated beats, 13 tracks, presets, i18n scaffold) exists separately. Whether it was folded into Rhythm Shop is not recorded. `[chat]`
- **Notes**
  - 2026-10-06 · claude.ai · Memory still calls this "two games being productionized". The repo area file is newer and wins.
  - 2026-10-25 · CC-web · Since then the Studio got a windows layout, a Pads window (Handspace layout) and home-row computer keys (see `personal/rhythm-shop.md`).

### BHS Studio — full DAW plan
- **Kind:** Node server + vanilla JS · **Status:** Planned (a first version lives inside Rhythm Shop) · `[chat]`
- **Wanted:** 4-slot live looper with punch-in/out snapped to beat/bar, continuous per-instrument pitch, copy/paste of 16/32-bar blocks, dark flat UI. Source repos: Rhythm-Maker + `musicinspiration`.
- **Notes**
  - 2026-10-06 · claude.ai · Not clear how much of the looper made it into the Rhythm Shop Studio.

### Handspace (vrlike)
- **Kind:** Static site (buildless ES modules) + small Node server · **Status:** Built · **Repo:** `beardsservices-png/vrlike` · **Detail:** `personal/minecraft-tacoma.md` (Minecraft tools) · `[repo]`
- **What it is:** Hand-tracked musical instrument in the browser with only a webcam. The screen is a window into a small room; reach in to hit pads and pinch notes. Its pad layout was reused in the Rhythm Shop Studio.
- **Also in the repo:** Minecraft tools — `tools/mc-builder` (Tacoma build planner), `tools/mc-track-plotter`, `tools/mc-commands` (claude.ai artifacts *Lifted Tacoma Build*, *Bedrock Command Guide*).
- **Notes**
  - 2026-10-25 · CC-web · Added from the repo. Probably what the hand-gesture experiments below grew into.

### musicinspiration (Song Idea Explorer)
- **Kind:** Node server (local API proxy) + Single-file HTML · **Status:** Built · **Repo:** `beardsservices-png/musicinspiration` (private) · `[chat]`
- **Features:** Node proxy server with no npm packages. Generates 12 song ideas with key, BPM, capo, chords and transposition via the Anthropic API.
- **Artifacts:** `song_explorer_offline.html` — no-API version: 80+ progressions, melodies, hooks, bridges and fingerpicking patterns across 12 genres (country and gospel left out on purpose). Mood/key/tempo filters, per-card transpose and capo, favorites, clipboard export. Built after the API credits question; billing for the API is separate from a Claude subscription.

### Somewhere Better — lyric video generator (Flipbook)
- **Kind:** Python script · **Status:** Built · **Repo:** `beardsservices-png/Flipbook` · `[repo]`
- **What it is:** Generates a sketchbook-style lyric music video as an MP4.
- **Notes**
  - 2026-10-25 · CC-web · Added from the repo README.

### Vamp
- **Kind:** Single-file HTML (React→HTML) · **Status:** Prototype · `[chat]`
- **Features:** Songwriting tool: piano keyboard, section looping, MIDI export.

### Hand-gesture experiments
- **Kind:** Single-file HTML · **Status:** Prototypes, standalone, not integrated · `[chat]` · MediaPipe Hands via webcam
- **Artifacts:** `duck-hunt-hand-tracking.html` (pinch to shoot) · `hand-drum-machine.html` (4 pads, loop; laggy) · `putt-putt.html` (3 holes, charge-and-fire pinch) · `handstack.html` (falling blocks) · `aquarium.html` (no-camera preview) · `page-turner.html` (PDF/txt/MD/Word, swipe pages, text-to-speech, 7 themes, mobile layout).
- **Open:** Finger Drums needs a keyboard override. Camera control needs real HTTPS on phones.
- **Notes**
  - 2026-10-06 · claude.ai · Where these files are stored is not recorded. Please add.
  - 2026-10-25 · CC-web · Not found by name in the repos checked. `vrlike/legacy/` is worth a look.

### Short-story app
- **Kind:** Next.js/TypeScript · **Status:** Planned/early · **Repo:** `beardsservices-png/Short-story` · `[chat]`
- **Plan:** Suno-style fiction platform. Simple/Custom modes, auto cover art, streaming text, public Explore feed with likes and remixing. Next.js, Supabase, Claude API, Replicate flux-schnell, OpenAI Moderation, R2, Vercel, Upstash.
- **Notes**
  - 2026-10-06 · claude.ai · How far it got is unknown.
  - 2026-10-25 · CC-web · Repo has no README; last push 22 Sep 2026.

### Style Studio 3D (Fashion-Design)
- **Kind:** Static site (3D) · **Status:** Built (Railway project *Fashion Design Studio*) · **Repo:** `beardsservices-png/Fashion-Design` · `[repo]`
- **What it is:** True-3D garment design on a neutral dress form: fabric, cut, hems, textures, prints, realistic materials and studio lighting.
- **Notes**
  - 2026-10-25 · CC-web · Added from the repo README.

### Board Room (virtual-board-games)
- **Kind:** Node server + client · **Status:** Built (set up to deploy to Railway on push to `main`) · **Repo:** `beardsservices-png/virtual-board-games` · `[repo]`
- **What it is:** Chess and checkers: pass-and-play, four computer levels, and online play by four-character code or link that survives refreshes and redeploys.
- **Notes**
  - 2026-10-25 · CC-web · Added from the repo README. Whether a Railway service exists for it is not checked.

### ComfyUI video
- **Kind:** Config/infra · **Status:** Working setup · **Repo:** `beardsservices-png/RunpodComfy` · `[repo]` · `business/comfyui-video.md`
- **What it is:** RunPod L4 pod running ComfyUI with WAN 2.1/2.2 (2.2 preferred) for Facebook marketing video. Branded slideshow tool. Exploring Claude Code to RunPod control.
- **Notes**
  - 2026-10-25 · CC-web · `RunpodComfy` README is "WAN 2.2 Image-to-Video" on RunPod, so it's this setup's repo (README.md only said "probably").

### Gemini_Prototype
- **Kind:** unknown · **Status:** Prototype · **Repo:** `beardsservices-png/Gemini_Prototype` · last push 16 Oct 2026
- **Notes**
  - 2026-10-25 · CC-web · No README. Please describe.

## C. Work for other people

### PureMechanic
- **Kind:** Static site + React/Vite front end with a Node/Express API · **Status:** Built · **Repos:** `PureMechanicsite`, `Mobile-Mechanic-app` · **Host:** Cloudflare Pages + Railway project *Mobile Mechanic App* · `[chat]`
- puremechanicmobile.com (Cloudflare Pages) plus the app on Railway, for Dymon's mobile mechanic business. The API has a contact-form route (nodemailer; needs SMTP variables set in Railway) and AI and reports routes.
- **Notes**
  - 2026-10-25 · CC-web · Repo names matched from the repo list; neither has a README. This answers README.md's "whose is unknown": they're Dymon's.

### RagedAura website mockup
- **Kind:** Static site mockup · **Status:** Pitch mockup · `[chat]` · Full style design for musician RagedAura (YouTube @RagedAuraPLN), made to pitch freelance web work.

## D. Standalone tools: single-file HTML and claude.ai artifacts

All are one HTML file with no build step, state in `localStorage`, unless noted. They open in any browser. Several were also published as claude.ai artifacts. Where the file lives now is mostly unrecorded. `[chat]` unless noted.

### Business tools
- **BHS OPS CENTER.** 7-tab daily operations dashboard, dark theme. Early front end for the business; the BHS app replaced it.
- **HTML Estimate Suite / estimate generator** (Mar 2026). Customer fields, multiplier sliders (difficulty, specialization, market), line items, live print-ready PDF. Tailwind. Superseded by the in-app estimate flow.
- **Task Board** (Apr–May 2026, `task-board.html`, "Beard's Master Task Board"). Categories Business/Truck/Home/Personal, priorities, dependencies, time horizons, cost totals, parts drawers, three views. Likely repo: `Task-Board-Apps` (section A).
- **Digital Whiteboard.** Mobile decision tool. Rewritten in plain ASCII after parse errors from curly quotes and em dashes.
- **Railway deploy plan for these tools:** a guide exists for deploying the HTML tools as a Flask/SQLite app on Railway, like bhs-memory-server. Whether it was done is not recorded.
- **Voice-assistant feature spec** (Aug 2026, `voice-assistant-feature-spec.md`). Became the live mic assistant.

### Personal and family tools
- **Page Turner** (`page-turner.html`, rebuilt Sep 2026, mobile first). PDF, txt, md, docx and html. Reflows to the screen. Swipe, edge taps, arrow keys, air-swipe by webcam. Read-aloud with voice, speed and pitch. 7 themes. CDN libraries: marked, mammoth, pdf.js, MediaPipe.
- **Laundry tracker** (Jul 2026). Washer/dryer state machine, timers that survive refresh, progress ring, chimes, notifications, stats. PWA install planned through Claude Code and Cloudflare Pages.
- **Phase 10 phase generator** (June 2026, rebuilt Oct 2026). Difficulty tiers, 5 presets, "Reserve Library" house rule, local save. A Kotlin/Jetpack Compose Android port was built too (Kind: Mobile) for a possible Play Store listing.
- **Math workbook** (Apr–May 2026). Coordinate grid, fractions with steps, number line, shapes, flashcards. Light and dark.
- **3D coordinate plotting tool** (Apr 2026). Standalone HTML for the same family use.
- **Chunky Yarn Quilt Designer** (Jan 2026). React component turned into a standalone HTML app: palettes, paint mode, mirroring, auto-save, PNG export.
- **Ergonomic loadout** (Apr 2026, `ergonomic-loadout.html`). Three-tier workstation comparison with retailer links.
- **Couch build** and **Minecraft Tacoma** notes: see `personal/couch-build.md` and `personal/minecraft-tacoma.md`.

## E. Archived, don't touch
- `beard-business-app` — archived 2026-08-11, subset of BHSmobileapp.
- `SMS-Extractor_BHS` — archived 2026-08-11, duplicate receiver. Don't merge its branches.
- `medical` — archived 2026-06-19.
- Early Access database / InvoiceBee–BusyBusy consolidation (2025).

## F. Not apps
- `claude-code-business-starter-kit` (fork) and `Beardsservices-claude-code-business-starter-kit` (copy): Claude Code starter kit, Jan 2026.

## Not yet inventoried — please fill in
- ~~Other repos under `beardsservices-png`.~~ Done 2026-10-25: all 25 repos are on this page.
- What's in `Gemini_Prototype`, `Task-Board-Apps`, `Short-story`, `Mobile-Mechanic-app`, `PureMechanicsite` (no READMEs).
- Railway project *victorious-appreciation*: repo not identified (see `README.md`).
- Giles job records and Drive "Where We Stand" files (these hold private detail; reference only).
- Anything built in Claude Code that never got its own file.
- Section D lists what past chats showed. The original files are probably in Downloads, Drive, a repo or only in the chat. Please record where each one lives.

## Template for a new app

```
### <App name>
- **Kind:** <see Kind words> · **Status:** <Live | Built, not live | Prototype | Planned | Archived> · **Repo:** <name> · **Host:** <where> · **Detail:** `business/<file>.md` or `personal/<file>.md`
- **What it is:** <one sentence>
- **Features** `[repo]` or `[chat]`
  - <feature>
- **Artifacts:** <files, drawings, PDFs>
- **Open:** <known gaps>
- **Notes**
  - YYYY-MM-DD · surface · note
```
