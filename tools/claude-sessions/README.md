# Claude Sessions — export and reconcile

Claude Code keeps every conversation (terminal, VS Code, and cloud sessions continued
locally) only on the machine, in `%USERPROFILE%\.claude\projects\`. Continuing a cloud
session locally makes a local copy that never syncs back. These tools get all of it into
Google Drive and then piece it together.

1. **`Export Claude Sessions.bat`** — double-click on the laptop. Writes
   `My Drive\Claude Sessions\` (index + readable transcripts + raw backup). Re-run any time;
   it only adds what is new. Needs Python (already installed for the BHS app) and Google
   Drive for Desktop; without Drive it saves to the Desktop.
2. **`RECONCILE.md`** — open `My Drive\Claude Sessions` in VS Code and tell Claude
   *"follow RECONCILE.md"*. It writes `My Drive\Where We Stand\` (START HERE + one page per
   area) and moves stale files to `My Drive\Delete\` with a reason for each.

No transcript or status page is ever written into this repo — it is public.
