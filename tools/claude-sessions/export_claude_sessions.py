"""
Export every local Claude Code conversation (terminal, VS Code extension, and cloud
sessions continued locally) into readable Markdown in Google Drive.

Where Claude Code keeps them:   %USERPROFILE%\\.claude\\projects\\<project>\\<session>.jsonl
Where this writes them:         <My Drive>\\Claude Sessions\\
                                  Session Index.md      - every session, newest first
                                  Transcripts\\<project>\\<date>_<title>_<id>.md
                                  Raw\\<project>\\<session>.jsonl   (untouched backup)

Safe to run again: only new or changed sessions are rewritten. Never deletes anything.
Prints ASCII only (Windows consoles choke on anything else).
"""
import hashlib
import json
import os
import re
import shutil
import string
import sys
from datetime import datetime
from pathlib import Path

SOURCE = Path.home() / ".claude" / "projects"
TOOL_RESULT_CHARS = 400      # keep a taste of each tool result, not the whole dump
TOOL_INPUT_CHARS = 200


def find_drive_root():
    """Google Drive for Desktop mounts 'My Drive' on a drive letter (usually G:)."""
    candidates = []
    if os.name == "nt":
        for letter in string.ascii_uppercase[3:]:
            candidates.append(Path(f"{letter}:/My Drive"))
    home = Path.home()
    candidates += [home / "Google Drive" / "My Drive", home / "My Drive", home / "Google Drive"]
    for c in candidates:
        try:
            if c.is_dir():
                return c, True
        except OSError:
            pass
    return home / "Desktop", False


def text_of(content):
    """Flatten a message's content into readable Markdown."""
    if isinstance(content, str):
        return content.strip()
    out = []
    for block in content or []:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text":
            out.append(block.get("text", "").strip())
        elif kind == "tool_use":
            inp = block.get("input") or {}
            hint = (inp.get("command") or inp.get("file_path") or inp.get("path")
                    or inp.get("pattern") or inp.get("query") or inp.get("description") or "")
            hint = str(hint).replace("\n", " ")[:TOOL_INPUT_CHARS]
            out.append(f"> *tool: {block.get('name', '?')}* `{hint}`")
        elif kind == "tool_result":
            res = block.get("content")
            if isinstance(res, list):
                res = " ".join(b.get("text", "") for b in res if isinstance(b, dict))
            res = str(res or "").strip().replace("\n", " ")
            if res:
                cut = "..." if len(res) > TOOL_RESULT_CHARS else ""
                out.append(f"> *result:* {res[:TOOL_RESULT_CHARS]}{cut}")
        elif kind == "image":
            out.append("> *[image]*")
    return "\n\n".join(p for p in out if p)


def read_session(path):
    s = {"id": path.stem, "title": None, "cwd": None, "branch": None,
         "first": None, "last": None, "turns": [], "first_user": None}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "summary" and e.get("summary"):
                s["title"] = s["title"] or e["summary"]
                continue
            if e.get("type") not in ("user", "assistant") or e.get("isSidechain"):
                continue
            ts = e.get("timestamp")
            if ts:
                s["first"] = s["first"] or ts
                s["last"] = ts
            s["cwd"] = s["cwd"] or e.get("cwd")
            s["branch"] = s["branch"] or e.get("gitBranch")
            msg = e.get("message") or {}
            body = text_of(msg.get("content"))
            if not body or e.get("isMeta"):
                continue
            role = msg.get("role") or e["type"]
            is_human = role == "user" and not body.startswith("> *result:*")
            if is_human and s["first_user"] is None:
                s["first_user"] = body
            who = "Brian" if is_human else "Claude"
            if s["turns"] and s["turns"][-1][1] == who:
                prev = s["turns"][-1]
                s["turns"][-1] = (prev[0], who, prev[2] + "\n\n" + body)
            else:
                s["turns"].append((ts, who, body))
    if not s["title"] and s["first_user"]:
        s["title"] = s["first_user"].splitlines()[0][:80]
    s["title"] = s["title"] or "(untitled)"
    return s


def slug(text, n=50):
    return (re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")[:n] or "session")


def project_name(folder, cwd):
    if cwd:
        return Path(cwd).name or folder
    return folder.split("-")[-1] or folder


def day(ts):
    return (ts or "")[:10] or "unknown-date"


def main():
    if not SOURCE.is_dir():
        print(f"No Claude Code sessions found at {SOURCE}")
        return 1
    root, on_drive = find_drive_root()
    out = root / "Claude Sessions"
    (out / "Transcripts").mkdir(parents=True, exist_ok=True)
    (out / "Raw").mkdir(parents=True, exist_ok=True)
    print(f"Reading   {SOURCE}")
    print(f"Writing   {out}" + ("" if on_drive else "   (Google Drive not found - saved to Desktop)"))

    sessions, written = [], 0
    for jsonl in sorted(SOURCE.glob("*/*.jsonl")):
        s = read_session(jsonl)
        if not s["turns"]:
            continue
        proj = project_name(jsonl.parent.name, s["cwd"])
        s["project"] = proj
        s["opening"] = hashlib.sha1((s["first_user"] or "").encode("utf-8")).hexdigest()[:10]
        rel = Path("Transcripts") / slug(proj, 40) / f"{day(s['first'])}_{slug(s['title'])}_{s['id'][:8]}.md"
        s["file"] = rel.as_posix()
        dest = out / rel
        raw = out / "Raw" / slug(proj, 40) / jsonl.name
        if not dest.exists() or dest.stat().st_mtime < jsonl.stat().st_mtime:
            dest.parent.mkdir(parents=True, exist_ok=True)
            lines = [f"# {s['title']}", "",
                     f"- **Project:** {proj}  ",
                     f"- **Folder:** {s['cwd'] or '?'}  ",
                     f"- **Branch:** {s['branch'] or '-'}  ",
                     f"- **Started:** {s['first'] or '?'}  ",
                     f"- **Last activity:** {s['last'] or '?'}  ",
                     f"- **Session id:** {s['id']}  ", "", "---", ""]
            for ts, who, body in s["turns"]:
                lines += [f"### {who}  <sub>{ts or ''}</sub>", "", body, ""]
            dest.write_text("\n".join(lines), encoding="utf-8")
            written += 1
        if not raw.exists() or raw.stat().st_size != jsonl.stat().st_size:
            raw.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(jsonl, raw)
        sessions.append(s)

    # Sessions that open with the same first message are one conversation that was
    # resumed, forked, or carried over from the cloud - flag them so they are read together.
    groups = {}
    for s in sessions:
        groups.setdefault(s["opening"], []).append(s)

    sessions.sort(key=lambda s: s["last"] or "", reverse=True)
    idx = ["# Claude Sessions - Index", "",
           f"Updated {datetime.now():%Y-%m-%d %H:%M}. {len(sessions)} sessions, newest activity first.",
           "Rows marked **same conversation** started from the same first message - a resume,",
           "a fork, or a cloud session continued here. Read them together; the newest one wins.", "",
           "| Last activity | Started | Project | Title | Turns | Branch | Notes |",
           "|---|---|---|---|---|---|---|"]
    for s in sessions:
        kin = [k for k in groups[s["opening"]] if k is not s]
        note = f"same conversation as {len(kin)} other(s)" if kin and s["first_user"] else ""
        title = s["title"].replace("|", "/")
        link = s["file"].replace(" ", "%20")
        idx.append(f"| {day(s['last'])} | {day(s['first'])} | {s['project']} | [{title}]({link}) "
                   f"| {len(s['turns'])} | {s['branch'] or '-'} | {note} |")
    (out / "Session Index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    print(f"Done. {len(sessions)} sessions found, {written} new or updated.")
    print(f"Open: {out / 'Session Index.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
