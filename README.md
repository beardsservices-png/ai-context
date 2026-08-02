# ai-context

Shared technical/project context for Brian Beard's Claude "trinity" — claude.ai, Claude Code (terminal), and Claude Code in VS Code — so all three surfaces work from the same picture instead of three separate memories.

**This repo is PUBLIC. Keep it that way on purpose:**
- ✅ Technical architecture, stack decisions, project status, tool/skill definitions
- ❌ Customer names/PII, family details, financial specifics, anything from the civic-project investigation

If it wouldn't be fine on a public GitHub profile, it doesn't go in this repo.

## Structure

- `profile.md` — durable facts about the business/stack (mirrors what Claude Code's CLAUDE.md should already know)
- `areas/*.md` — one file per active project (BHS app, website, Rhythm Shop, etc.) — status, stack, decisions, open threads
- `topics/*.md` — cross-cutting technical topics (deployment conventions, coding preferences, etc.)

## How each surface uses this

**Claude Code (terminal + VS Code extension):** add this to your root `CLAUDE.md`:
```
@ai-context/profile.md
@ai-context/areas/bhs-app.md
```
(import whichever area files are relevant to the repo you're in). Since both terminal and VS Code sessions read `CLAUDE.md` off disk, this covers every local session automatically once the repo is cloned/pulled — no separate setup per surface.

**claude.ai (web/mobile):** covered by the `sync-context` skill in this repo (see `SKILL.md`). At the start of relevant work, Claude fetches the current files via the public raw GitHub URLs (no auth needed since this repo is public) and reads them before proceeding. After a session produces a durable decision worth sharing across surfaces, Claude proposes an update to the relevant file — Brian approves, Claude writes it, Brian commits/pushes.

## Sync convention (manual, not automatic)

There's no real-time sync — GitHub isn't a live channel. The convention is:
1. Whoever (which surface) learns something durable and cross-cutting proposes an edit to the relevant `.md` file here.
2. Brian reviews/commits.
3. Next session on any surface pulls the latest before relying on it.

"Knowable, not real-time" — which is the actual goal.
