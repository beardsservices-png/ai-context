# Wiring the shared context into Claude Code

## Already done on Brian's laptop — check before adding another

`C:\Users\bbria\.claude\CLAUDE.md` exists and loads `profile.md` + `areas/bhs-app.md`
into **every** local session, terminal and VS Code alike. It was added 2026-09-29,
after the local clone turned out to be 23 days stale and a session re-derived a
correction Brian had already given another Claude.

A user-level file loads on every session, so it deliberately imports only the two
files that are nearly always relevant. `areas/bhs-app.md` alone is 750+ lines — a
full import list belongs in a repo's own `CLAUDE.md`, not the global one.

## Per-repo snippet

Paste into the root `CLAUDE.md` of a repo where the wider context is relevant:

```
## Shared context (all Claude surfaces)
@~/Projects/ai-context/profile.md
@~/Projects/ai-context/areas/bhs-app.md
@~/Projects/ai-context/areas/website.md
@~/Projects/ai-context/areas/rhythm-shop.md
@~/Projects/ai-context/areas/comfyui-video.md
@~/Projects/ai-context/areas/retell-bill.md
@~/Projects/ai-context/areas/cad-app.md
@~/Projects/ai-context/topics/estimating-rules.md
@~/Projects/ai-context/topics/document-standards.md
```

### Mind the path

On Brian's laptop the clone is at **`C:\Users\bbria\Projects\ai-context`**, but the
repos are not all siblings of it:

| Repo | `../ai-context/` resolves? |
|---|---|
| `Projects\handspace`, `Projects\bhs-taskboard`, other `Projects\*` | yes |
| **`C:\Users\bbria\BHSmobileapp`** — the main one | **no** |
| `CAD-` | not cloned locally at all |

A relative `../ai-context/` path fails **silently** in `BHSmobileapp` — no error, the
context simply never loads. Use `~/Projects/ai-context/` as above, or an absolute
path, unless the repo really is a sibling.

## Pull before trusting it

These files are a clone. They are only current if someone pulled. Early in any
session touching BHS work:

```
git -C ~/Projects/ai-context pull --ff-only
```

If it moves, read what changed before proceeding — another surface has learned
something this session does not know yet.

## Ground rule

This repo is **public**. Customer names are fine. Never write customer addresses,
phone numbers, emails, family details or financials into it — those belong in Drive.
