# ai-context

Shared technical/project context for Brian Beard's Claude "trinity" — claude.ai, Claude Code (terminal), and Claude Code in VS Code — so all three surfaces work from the same picture instead of three separate memories.

**This repo is PUBLIC. Keep it that way on purpose:**
- ✅ Technical architecture, stack decisions, project status, tool/skill definitions
- ✅ Customer names (e.g. "Jesse & Doree Giles") where they help tie work to a job
- ❌ Customer addresses, phone numbers, emails or other contact details; family details; financial specifics; anything from the civic-project investigation

If it wouldn't be fine on a public GitHub profile, it doesn't go in this repo.

## Start here: what is where

Read this table, then only the file for the work at hand. Business work also needs
`profile.md`, and anything that makes a customer document needs `business/rules/`.

### Business (Beard's Home Services)

| Project | File | Repo | Runs on | State |
|---|---|---|---|---|
| BHS app (jobs, estimates, leads, time clock) | `business/bhs-app.md` (+ `-history`, `-stops-threads`) | `BHSmobileapp` (private) | Railway, project *BHS APP*, deploys on push to `main` | **Live** |
| Betty, the phone receptionist | `business/betty.md` | `bhs-memory-server` (private) + Retell agent | Railway, project *Memory Server for Retell Agent*, deploys on push to `main` | **Live** |
| Website beardshomeservices.com | `business/website.md` | `beardsservices-site` | Cloudflare Pages | **Live** |
| Draft Studio (CAD drawings of jobs) | `business/draft-studio.md` | `CAD-` (public) | Railway, project *Cad*, deploys on push to `main` | **Live** |
| Marketing video (ComfyUI / RunPod) | `business/comfyui-video.md` | probably `RunpodComfy` | RunPod GPU pod, started when needed | On demand |
| Estimating and document rules | `business/rules/estimating-rules.md`, `business/rules/document-standards.md` | -- | -- | Rules every estimate/invoice follows |

### Personal

| Project | File | Repo | Runs on | State |
|---|---|---|---|---|
| Rhythm Shop (music practice) | `personal/rhythm-shop.md` | `Rhythm-Maker` | Railway, project *Rhythm Maker* | **Live** |
| Couch build | `personal/couch-build.md` | -- (drawings in Draft Studio) | -- | Build notes |
| Minecraft tools (Tacoma build planner, track plotter, command guide) | `personal/minecraft-tacoma.md` | `vrlike` (`tools/mc-builder`, `tools/mc-track-plotter`, `tools/mc-commands`) | claude.ai artifacts *Lifted Tacoma Build*, *Bedrock Command Guide* | Building the Tacoma (1 block = 2 in) |

### Other repos (no notes written yet)

Business or personal is a guess from the name where marked; correct it here when known.

| Repo | Railway project | Notes |
|---|---|---|
| `JazzyTraining` | *JazzyTraining* | Business (guess): training for Jazzy, his helper |
| `Task-Board-Apps` | *Taskboard* | Business (guess) |
| `Training-Business-Template` | *Business Training Template* | Business (guess) |
| `Fashion-Design` | *Fashion Design Studio* | Personal (guess) |
| `Mobile-Mechanic-app`, `PureMechanicsite` | *Mobile Mechanic App* | Not his trade; whose is unknown |
| `vrlike` (Handspace; also the Minecraft tools), `Gemini_Prototype`, `Short-story`, `virtual-board-games`, `Rubiks`, `Flipbook`, `musicinspiration` | none | Personal (guess), not deployed |
| `claude-code-business-starter-kit` (+ the `Beardsservices-` copy) | none | Claude Code starter kit (fork) |
| Railway project *victorious-appreciation* | -- | Unnamed; repo not identified |

**Retired, do not use:** `beard-business-app` (archived, replaced by `BHSmobileapp`),
`SMS-Extractor_BHS` (archived; the app receives texts itself; Railway project *sms* is the
stopped copy), `medical` (archived).

### Other files

- `APPS.md`: index of everything Brian has built (apps, sites, HTML tools, artifacts, skills), with a Kind and Status for each. Any Claude adds notes there.
- `profile.md`: who Brian is, the stack, how he wants to work.
- `WHATS-CURRENT.md`: what is live, what is built but not live, what each customer was last sent.
- `areas/` and `topics/`: **old paths, now one-line pointers** to the files above. They stay
  until every Claude surface reads the new paths (claude.ai preferences, the laptop's
  `~/.claude/CLAUDE.md`, the installed sync-context skill); then delete them.

## How each surface uses this

**Claude Code (terminal + VS Code extension):** add this to your root `CLAUDE.md`:
```
@ai-context/profile.md
@ai-context/business/bhs-app.md
```
(import whichever area files are relevant to the repo you're in). Since both terminal and VS Code sessions read `CLAUDE.md` off disk, this covers every local session automatically once the repo is cloned/pulled — no separate setup per surface.

**claude.ai (web/mobile):** covered by the `sync-context` skill in this repo (see `SKILL.md`). At the start of relevant work, Claude fetches the current files via the public raw GitHub URLs (no auth needed since this repo is public) and reads them before proceeding. After a session produces a durable decision worth sharing across surfaces, Claude proposes an update to the relevant file — Brian approves, Claude writes it and merges it to `main` itself.

## Sync convention (manual, not automatic)

There's no real-time sync — GitHub isn't a live channel. The convention is:
1. Whoever (which surface) learns something durable and cross-cutting proposes an edit to the relevant `.md` file here.
2. Brian reviews/commits.
3. Next session on any surface pulls the latest before relying on it.

"Knowable, not real-time" — which is the actual goal.

## Where things stand right now

Plain-language status pages, one per area, live in Drive at `My Drive\Where We Stand\START HERE.md` (path only - contents stay out of this public repo). Rebuilt by following `tools/claude-sessions/RECONCILE.md`.
