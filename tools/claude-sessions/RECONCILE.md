# Reconcile — piece every session back together

**For Claude Code in VS Code, on Brian's laptop.** Brian will open this folder and say
*"follow RECONCILE.md"*. Do the whole thing without asking him technical questions; ask
only when a call is genuinely his (money, a customer, something personal).

## Why this exists

Work has been done in cloud sessions, continued in VS Code, redone in claude.ai, ChatGPT
and Gemini, and saved to Drive in several copies. Nothing says which version is current.
The goal: one page per area that says **where it stands, what is current, what was
superseded, and exactly how to continue** — and everything stale moved out of the way.

## Sources (read all of them)

1. **`Claude Sessions\Session Index.md`** and the transcripts it links (made by
   `Export Claude Sessions.bat`). Run the .bat first if the index is older than today.
   Rows marked *same conversation* are one thread resumed or forked — read them as one;
   the newest activity wins.
2. **Local git clones** on this laptop. Find them (`BHSmobileapp`, `bhs-memory-server`,
   `ai-context`, `CAD-`, and any other folder with a `.git`). For each: `git fetch`, then
   `git status`, `git stash list`, and `git branch -vv`. **Uncommitted changes, stashes and
   unpushed commits are the work most at risk — list every one.**
3. **GitHub**: `main` and `claude/*` branches on each repo. Use the `branch-hygiene` skill's
   `branch_audit.py` in BHSmobileapp for stranded branches.
4. **`ai-context`** (`areas/*.md`) — the shared record every surface reads.
5. **Google Drive** — this folder sits inside it (Drive for Desktop), so `My Drive` is on
   disk. Job paperwork, exports, estimates.
6. **claude.ai chat export**, if Brian has dropped the zip in `Claude Sessions\claude.ai export\`.
   Cloud Claude Code sessions are listed at claude.ai/code; their work shows up as commits.

## Areas (one status page each)

BHS app · BHS customers & jobs (Giles, Johnson, Hedden, …) · Bill / memory server ·
CAD (Draft Studio) · beardsservices.com · Rhythm maker / Rhythm Shop · ComfyUI video ·
Avinley (personal) · Health & research · anything else that turns up.

**Already reconciled — use as the model, don't redo:** Giles. Drive folder
`Giles — BHS20260627 (Jesse & Doree Giles)`, doc `Giles — Job Record (START HERE)`.

## What to write

Into **`My Drive\Where We Stand\`**:

- **`START HERE.md`** — one short table: area, status in one line, the single file or link
  to open, next step. Plain business language; Brian is not technical.
- **`<Area>.md`** for each area:
  - **Where it stands** — what works today, what was last done and when.
  - **Current** — the one file / branch / doc that is the truth, with its path or link.
  - **Superseded** — what it replaced and why (deprecated, truncated, migrated, redone
    elsewhere). Name the session it happened in.
  - **At risk** — uncommitted or unpushed work, half-finished sessions, anything that
    exists only on this laptop.
  - **How to continue** — the exact next step, and a ready-to-paste prompt for the next
    session.

## Moving stale files

- Use **`My Drive\Delete\`** (already created). Move — never delete — anything clearly
  superseded, a duplicate, or junk (build folders like `.venv` / `node_modules`, `-1`/`-2` copies of the
  same file, stray docs whose title is a half-sentence of a prompt).
- Log every move in **`My Drive\Delete\_Why each file is here`**: old path, reason,
  what replaces it. Brian reviews that list and empties the folder himself.
- **When unsure, leave it** and list it under *Unsure* in that log.
- Never move anything under `Where We Stand`, a `START HERE` doc, a customer's current
  paperwork, tax/receipt records, or personal/family material without Brian saying so.

## Rules that do not bend

- **`ai-context` is a PUBLIC repo.** Status pages, customer contact details, money and
  anything personal go in Drive, never there. Only technical pointers go in `ai-context`.
- Do not push to `main` of `BHSmobileapp` or `bhs-memory-server` — that deploys. Stranded
  work goes on a branch, and the status page says so.
- Never discard uncommitted work to tidy up. Commit it to a branch or copy it aside first.
- When done, add a one-line pointer to `Where We Stand\START HERE.md` in
  `ai-context/README.md` (path only, no contents) and push that to `ai-context`.
