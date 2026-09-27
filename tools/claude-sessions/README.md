# Claude Sessions — export and reconcile

Claude Code keeps every conversation (terminal, VS Code, and cloud sessions continued
locally) only on the machine, in `%USERPROFILE%\.claude\projects\`. Continuing a cloud
session locally makes a local copy that never syncs back. These tools get all of it into
Google Drive and then piece it together.

1. **`Export Claude Sessions.bat`** — double-click on the laptop. Writes
   `My Drive\Claude Sessions\` (index + readable transcripts + raw backup). Re-run any time;
   it only adds what is new. Needs Python (already installed for the BHS app) and Google
   Drive for Desktop; without Drive it saves to the Desktop.
   The same double-click then runs **`verify_sessions.py`**: every edit and commit from
   every session is checked against GitHub and written to `Verification Report.md` —
   ON MAIN, BRANCH ONLY (never merged), LAPTOP ONLY (never pushed), REPLACED LATER, or
   NOT FOUND (lost; the transcript still has the text). Needs Git, which VS Code uses.
   It downloads its own copies of the repos into `%LOCALAPPDATA%` and never touches yours.
2. **`RECONCILE.md`** — open `My Drive\Claude Sessions` in VS Code and tell Claude
   *"follow RECONCILE.md"*. It writes `My Drive\Where We Stand\` (START HERE + one page per
   area) and moves stale files to `My Drive\Delete\` with a reason for each.

No transcript or status page is ever written into this repo — it is public.

## "Different repository" when continuing a session in VS Code

The session was made in a GitHub repo, and VS Code needs a copy of it on this computer to
open. One-time fix: in VS Code press `Ctrl+Shift+P`, type **Git: Clone**, paste
`https://github.com/beardsservices-png/BHSmobileapp`, and pick `C:\BHS` as the place to
put it. From then on choose **Open folder** and pick `C:\BHS\BHSmobileapp`. Choosing
*Continue here* instead runs the session in whatever folder is open, which is how work
ends up in the wrong place.
