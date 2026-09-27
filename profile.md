# Profile

Brian Beard — owner-operator of Beard's Home Services (BHS), a solo home services/contracting business based in Mountain Home, Arkansas (Twin Lakes/Baxter County area).

- 20+ years trade experience across 14+ service divisions (concrete, metal roofing, decks, flooring, bathroom remodeling, electrical, plumbing, fencing).
- Prior career: continuous improvement facilitator, lean manufacturing / Kaizen background. Thinks in systems.
- Non-coder who built BHS's business management app from scratch using Claude Code.

## Digital stack (source of truth)

- **BHS app:** Python / SQLite, hosted on Railway. See `areas/bhs-app.md`.
- **Website:** beardshomeservices.com (migrated from beardsservices.com), hosted on Cloudflare Pages. Installable PWA + mobile nav. See `areas/website.md`.
- **Source control:** GitHub, org `beardsservices-png`.
- **AI phone receptionist:** "Bill" — Retell AI + ElevenLabs. See `areas/retell-bill.md`.
- **Dev tools:** Claude / Claude Code as primary dev tooling, across claude.ai (web/mobile), Claude Code (terminal), and Claude Code in VS Code.

## Working style

- Prefers Claude to make technical decisions (framework, DB, hosting, format) rather than asking — reserve questions for genuine tradeoffs, not arbitrary ones.
- Wants consistency once a technical approach is chosen — don't switch methods mid-stream on a snag.
- Casual, direct communication, often voice-to-text.
- **Finished means on `main`.** Brian expects work to be pushed and merged without being asked each time; a session ending with work only on a `claude/*` branch is how things got abandoned. Merge to `main` as the last step. The one exception is a repo where `main` deploys (`BHSmobileapp`, `bhs-memory-server`): merge there too once it is tested, unless something is genuinely risky. **Two outcomes only: push it, or ask with a clickable question box** (the multiple-choice prompt, e.g. "Merge to main now?") so it cannot be missed. Never end on a sentence saying it's on a branch.
