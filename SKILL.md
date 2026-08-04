---
name: sync-context
description: Pulls Brian's shared ai-context repo (beardsservices-png/ai-context) before BHS/technical project work, so claude.ai, Claude Code terminal, and Claude Code VS Code sessions all start from the same picture. Trigger whenever work touches the BHS app, beardsservices.com, Rhythm Shop, the ComfyUI video stack, Bill (AI receptionist), or any other item tracked in that repo — or when Brian references "the context repo" / "ai-context" / "what's shared."
---

# sync-context

## On claude.ai (web/mobile)

At the start of relevant work, fetch the current files instead of relying on memory of them:

1. `web_fetch` the relevant raw files, e.g.:
   - `https://raw.githubusercontent.com/beardsservices-png/ai-context/main/profile.md`
   - `https://raw.githubusercontent.com/beardsservices-png/ai-context/main/areas/<project>.md`
2. If deeper access is needed (browsing the whole repo, multiple files at once), use `bash_tool` to `git clone https://github.com/beardsservices-png/ai-context.git` into the scratch workspace — it's public, no auth needed for read.
3. Use what's fetched as ground truth over anything remembered from a prior session.
4. If the conversation produces a durable, cross-cutting decision (new stack choice, new project, status change) — not a one-off detail — propose the specific markdown edit to Brian. On approval, write it via `bash_tool` (clone, edit, `git diff` to show him, then he pushes — or he gives a token for that session if he wants Claude to push directly).

## On Claude Code (terminal + VS Code extension)

1. Keep the repo cloned locally (wherever Brian keeps his repos).
2. In the root `CLAUDE.md` of any project that touches shared context, import the relevant files:
   ```
   @ai-context/profile.md
   @ai-context/areas/bhs-app.md
   ```
3. Before starting work, `git pull` the `ai-context` repo if it hasn't been touched this session — same "pull before trusting it" rule as claude.ai.
4. When a session produces a durable decision worth sharing, edit the relevant file directly in the local clone, then `git commit` and `git push` straight to `main` immediately — don't leave it staged locally waiting on Brian to commit/PR it. GitHub stays the source of truth; the local clone should never sit ahead of it.

## Ground rule (all surfaces)

This repo is PUBLIC — never write customer names/PII, family details, financials, or anything from Brian's non-technical/personal projects into it. Technical/project context only. If unsure whether something belongs, ask Brian rather than writing it.
