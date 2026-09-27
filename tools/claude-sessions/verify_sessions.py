"""
Check every code change a Claude session made against what is actually on GitHub,
so work that was overlooked, split between phone and laptop, or never pushed is not lost.

Reads the raw session backups written by export_claude_sessions.py
(<My Drive>\\Claude Sessions\\Raw\\...) and, for each session:

  - every file edit (Edit / Write / MultiEdit): is that text on main today?
  - every commit it made:                     is that commit on main today?

Answers, per item:
  ON MAIN          - landed, nothing to do
  BRANCH ONLY      - pushed to a branch that was never merged (named)
  LAPTOP ONLY      - found in a folder on this computer but never pushed
  REMOVED FROM MAIN- it DID land on main, and a later change took it out again. Names
                     the change that removed it, when, which session made it, and
                     whether that looks deliberate or like an accidental overwrite
  REPLACED LATER   - never landed as written; the file was revised before or after
  NOT FOUND        - on no branch and not on this computer: lost work (the transcript
                     still has the text). A commit that is NOT FOUND was usually wiped
                     out by a force-push

Writes <My Drive>\\Claude Sessions\\Verification Report.md. Read-only towards every repo:
it downloads its own copies into a cache folder and never changes yours.
Prints ASCII only.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_claude_sessions import find_drive_root  # noqa: E402

OWNER = "beardsservices-png"
CACHE = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".cache") / "claude-session-verify"
COMMIT_RE = re.compile(r"\[([^\]\s]+)(?: \(root-commit\))? ([0-9a-f]{7,40})\] (.+)")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip()


# ---------- reading sessions ----------

def distinctive_line(text):
    """The longest meaningful line of an edit - specific enough to find again."""
    # Drop list numbers and bullets: "6. foo" renumbered to "7. foo" is not lost work.
    lines = [re.sub(r"^(?:[-*+>]|\d+[.)])\s+", "", l.strip()) for l in (text or "").splitlines()]
    lines = [l for l in lines if len(l) >= 20 and not l.startswith(("#", "//", "import ", "from "))] or \
            [l for l in lines if len(l) >= 12]
    return max(lines, key=len)[:200] if lines else None


def split_repo_path(file_path, repo_names):
    """'/home/user/BHSmobileapp/api/app.py' or 'C:\\x\\BHSmobileapp\\api\\app.py' -> ('BHSmobileapp', 'api/app.py')"""
    parts = re.split(r"[\\/]+", file_path)
    for i in range(len(parts) - 2, -1, -1):
        if parts[i].lower() in repo_names:
            return repo_names[parts[i].lower()], "/".join(parts[i + 1:])
    return None, None


def read_session(path):
    s = {"id": path.stem, "title": None, "last": None, "edits": [], "commits": [], "cwd": None}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") == "summary":
                s["title"] = s["title"] or e.get("summary")
                continue
            if e.get("isSidechain"):
                continue
            s["last"] = e.get("timestamp") or s["last"]
            s["cwd"] = s["cwd"] or e.get("cwd")
            content = (e.get("message") or {}).get("content")
            if isinstance(content, str):
                if e.get("type") == "user" and not s["title"]:
                    s["title"] = content.strip().splitlines()[0][:80] if content.strip() else None
                continue
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and e.get("type") == "user" and not s["title"]:
                    s["title"] = (b.get("text") or "").strip().splitlines()[0][:80] or None
                if b.get("type") == "tool_use" and b.get("name") in EDIT_TOOLS:
                    inp = b.get("input") or {}
                    fp = inp.get("file_path") or inp.get("notebook_path")
                    texts = [inp.get("new_string"), inp.get("content"), inp.get("new_source")]
                    texts += [x.get("new_string") for x in inp.get("edits") or [] if isinstance(x, dict)]
                    probe = distinctive_line("\n".join(t for t in texts if t))
                    if fp and probe:
                        s["edits"].append({"file": fp, "probe": probe, "ts": e.get("timestamp")})
                if b.get("type") == "tool_result":
                    res = b.get("content")
                    if isinstance(res, list):
                        res = " ".join(x.get("text", "") for x in res if isinstance(x, dict))
                    for m in COMMIT_RE.finditer(str(res or "")):
                        s["commits"].append({"branch": m.group(1), "sha": m.group(2),
                                             "msg": m.group(3)[:90]})
    s["title"] = s["title"] or "(untitled)"
    return s


# ---------- repos ----------

def find_local_clones():
    """Folders on this computer that are git repos, by folder name (shallow search)."""
    roots = [Path.home()]
    if os.name == "nt":
        roots += [Path(f"{d}:/") for d in "CDEF" if Path(f"{d}:/").exists()]
    found = {}
    for root in roots:
        for depth in range(0, 4):
            pattern = "/".join(["*"] * depth) + ("/" if depth else "") + ".git"
            try:
                for g in root.glob(pattern):
                    if g.is_dir() and "node_modules" not in g.parts and "AppData" not in g.parts:
                        found.setdefault(g.parent.name.lower(), g.parent)
            except (OSError, PermissionError):
                pass
    return found


def ensure_cache(name):
    """A fresh copy of the GitHub repo with every branch, kept outside Drive."""
    dest = CACHE / name
    if (dest / ".git").is_dir():
        git(dest, "fetch", "--quiet", "--prune", "origin", "+refs/heads/*:refs/remotes/origin/*")
        return dest
    CACHE.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--filter=blob:none",
                        f"https://github.com/{OWNER}/{name}.git", str(dest)],
                       capture_output=True, text=True)
    return dest if r.returncode == 0 else None


def remote_branches(repo):
    _, out = git(repo, "for-each-ref", "--format=%(refname)", "refs/remotes/origin")
    return [r for r in out.splitlines() if not r.endswith("/HEAD")]


def main_ref(repo):
    code, _ = git(repo, "rev-parse", "--verify", "-q", "refs/remotes/origin/main")
    return "refs/remotes/origin/main" if code == 0 else "refs/remotes/origin/master"


def check_edit(repo, local, rel, probe):
    code, _ = git(repo, "grep", "-q", "-F", "-e", probe, main_ref(repo), "--", rel)
    if code == 0:
        return "ON MAIN", ""
    refs = remote_branches(repo)
    if refs:
        _, out = git(repo, "grep", "-l", "-F", "-e", probe, *refs, "--", rel)
        hits = sorted({line.split(":", 1)[0].replace("refs/remotes/origin/", "") for line in out.splitlines()})
        if hits:
            return "BRANCH ONLY", ", ".join(hits[:3]) + (" ..." if len(hits) > 3 else "")
    if local is not None:
        f = local / rel
        try:
            if f.is_file() and probe in f.read_text(encoding="utf-8", errors="replace"):
                return "LAPTOP ONLY", str(local)
        except OSError:
            pass
    return "NOT FOUND", ""


def check_commit(repo, local, sha):
    if git(repo, "cat-file", "-e", f"{sha}^{{commit}}")[0] == 0:
        if git(repo, "merge-base", "--is-ancestor", sha, main_ref(repo))[0] == 0:
            return "ON MAIN", ""
        _, out = git(repo, "branch", "-r", "--contains", sha)
        names = [b.strip().replace("origin/", "") for b in out.splitlines() if "HEAD" not in b]
        return ("BRANCH ONLY", ", ".join(names[:3])) if names else \
               ("NOT FOUND", "commit is on no branch any more - likely overwritten by a force-push")
    if local is not None and git(local, "cat-file", "-e", f"{sha}^{{commit}}")[0] == 0:
        return "LAPTOP ONLY", str(local)
    return "NOT FOUND", "commit is not on GitHub - never pushed from a machine that's gone, or force-pushed over"


DELIBERATE = re.compile(r"\b(revert|remove|drop|delete|replace|rewrite|rename|refactor|"
                        r"supersede|deprecate|move|undo|simplif|clean)", re.I)


def removed_from_main(repo, rel, probe, session_by_sha):
    """If this text was on main once and is gone now, who took it out and how."""
    _, out = git(repo, "log", "--format=%H%x09%ct%x09%s", "-S", probe, main_ref(repo), "--", rel)
    hits = [l.split("\t", 2) for l in out.splitlines() if l.count("\t") == 2]
    if not hits:
        return None
    sha, ct, subject = hits[0]                     # newest change to this text = its removal
    when = datetime.fromtimestamp(int(ct)).strftime("%Y-%m-%d")
    _, stat = git(repo, "show", "--numstat", "--format=", sha, "--", rel)
    try:
        added, deleted = (int(x) for x in stat.split()[:2])
    except ValueError:
        added = deleted = 0
    if DELIBERATE.search(subject):
        verdict = "looks deliberate"
    elif deleted >= 40 and deleted >= added * 0.6:
        verdict = f"CHECK - bulk rewrite of the file (-{deleted}/+{added}), the usual way work gets overwritten"
    else:
        verdict = "CHECK - the change that removed it doesn't say why"
    who = session_by_sha.get(sha[:7])
    by = f" in session \"{who}\"" if who else ""
    return (f"removed {when} by {sha[:7]} \"{subject[:70]}\"{by} - {verdict} - "
            f"https://github.com/{OWNER}/{repo.name}/commit/{sha[:12]}")


def epoch(ts):
    """Transcript timestamps are UTC ('...Z'); git's are unix seconds. Compare as numbers."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return float("inf")


# ---------- report ----------

def main():
    root, _ = find_drive_root()
    base = root / "Claude Sessions"
    raw = base / "Raw"
    if not raw.is_dir():
        print("Run Export Claude Sessions first - no Raw folder yet.")
        return 1
    print("Reading sessions...")
    sessions = [read_session(p) for p in sorted(raw.glob("*/*.jsonl"))]
    sessions = [s for s in sessions if s["edits"] or s["commits"]]

    local = find_local_clones()
    names = {}
    for s in sessions:
        for e in s["edits"]:
            for part in re.split(r"[\\/]+", e["file"]):
                if part:
                    names.setdefault(part.lower(), part)
    print("Downloading repo copies to compare against (first run takes a minute)...")
    repos, known = {}, {}
    for key, name in names.items():
        if key in local or key in ("bhsmobileapp", "bhs-memory-server", "ai-context", "cad-",
                                   "claude-code-business-starter-kit", "beardsservices-site"):
            path = ensure_cache(local[key].name if key in local else name)
            if path:
                repos[key] = path
                known[key] = local[key].name if key in local else name

    rows, tally, touched_later = [], {}, {}
    session_by_sha = {c["sha"][:7]: s["title"] for s in sessions for c in s["commits"]}
    ordered = sorted(sessions, key=lambda s: s["last"] or "")
    for s in ordered:                      # oldest first, so "later" is known
        for e in s["edits"]:
            repo_key, rel = split_repo_path(e["file"], {k: k for k in repos})
            e["repo"], e["rel"] = repo_key, rel
    # An edit is "replaced later" if any later edit - in this session or another - touched the same file.
    all_edits = [(x["ts"] or "", x) for t in ordered for x in t["edits"] if x["repo"]]
    for s in ordered:
        for e in s["edits"]:
            if e["repo"]:
                later = any(ts > (e["ts"] or "") and x["repo"] == e["repo"] and x["rel"] == e["rel"]
                            for ts, x in all_edits)
                touched_later[(s["id"], e["file"], e["probe"])] = later

    for s in sorted(sessions, key=lambda s: s["last"] or "", reverse=True):
        items = []
        for e in s["edits"]:
            if not e["repo"]:
                continue                   # a file outside any repo (Drive, Desktop, temp)
            status, where = check_edit(repos[e["repo"]], local.get(e["repo"]), e["rel"], e["probe"])
            if status == "NOT FOUND":
                repo = repos[e["repo"]]
                gone = removed_from_main(repo, e["rel"], e["probe"], session_by_sha)
                _, was = git(repo, "log", "--all", "-1", "--format=%h", "-S", e["probe"], "--", e["rel"])
                _, changed = git(repo, "log", "-1", "--format=%ct", main_ref(repo), "--", e["rel"])
                if gone:
                    status, where = "REMOVED FROM MAIN", gone
                elif was:
                    status, where = "REPLACED LATER", f"committed on a branch ({was}), revised before it reached main"
                elif touched_later.get((s["id"], e["file"], e["probe"])):
                    status, where = "REPLACED LATER", "a later edit changed this file"
                elif changed and e["ts"] and int(changed) > epoch(e["ts"]):
                    when = datetime.fromtimestamp(int(changed)).strftime("%Y-%m-%d")
                    status, where = "REPLACED LATER", f"file changed on main after this edit ({when})"
            items.append((status, f"{known[e['repo']]}/{e['rel']}", where, e["probe"]))
        for c in s["commits"]:
            key = next((k for k in repos if s["cwd"] and k in s["cwd"].lower()), None)
            if not key:
                continue
            status, where = check_commit(repos[key], local.get(key), c["sha"])
            items.append((status, f"{known[key]} commit {c['sha'][:7]}", where or f"branch {c['branch']}", c["msg"]))
        seen, uniq = set(), []
        for it in items:
            if (it[0], it[1], it[3]) not in seen:
                seen.add((it[0], it[1], it[3]))
                uniq.append(it)
        for it in uniq:
            tally[it[0]] = tally.get(it[0], 0) + 1
        if uniq:
            rows.append((s, uniq))

    order = ["LAPTOP ONLY", "NOT FOUND", "REMOVED FROM MAIN", "BRANCH ONLY", "REPLACED LATER", "ON MAIN"]
    out = ["# Verification Report", "",
           f"Checked {datetime.now():%Y-%m-%d %H:%M} against GitHub. "
           + ", ".join(f"**{k}** {tally.get(k, 0)}" for k in order), "",
           "- **LAPTOP ONLY** - exists only on this computer. Push it or it can be lost.",
           "- **NOT FOUND** - on no branch and not on this computer. Likely lost; the session transcript has the text.",
           "- **REMOVED FROM MAIN** - it landed, then a later change took it out. Each line names that change "
           "and says whether it looks deliberate; **CHECK** means it may have been overwritten by accident.",
           "- **BRANCH ONLY** - pushed, never merged to main.",
           "- **REPLACED LATER** - never landed as written; revised in the same or a later session. Usually fine.",
           "- **ON MAIN** - landed.", "",
           "## Needs a look", ""]
    for s, items in rows:
        bad = [it for it in items if it[0] in ("LAPTOP ONLY", "NOT FOUND", "BRANCH ONLY")
               or (it[0] == "REMOVED FROM MAIN" and "CHECK" in it[2])]
        if bad:
            out.append(f"### {s['title']}  <sub>{(s['last'] or '')[:10]} - {s['id'][:8]}</sub>")
            for status, what, where, probe in sorted(bad, key=lambda x: order.index(x[0])):
                out.append(f"- **{status}** `{what}` {('- ' + where) if where else ''}  ")
                out.append(f"  <sub>{probe.replace('|', '/')[:140]}</sub>")
            out.append("")
    out += ["## Everything, by session", ""]
    for s, items in rows:
        counts = {}
        for it in items:
            counts[it[0]] = counts.get(it[0], 0) + 1
        out.append(f"- {(s['last'] or '')[:10]} **{s['title']}** - "
                   + ", ".join(f"{k.lower()} {counts[k]}" for k in order if k in counts))
    (base / "Verification Report.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("Done. " + ", ".join(f"{k}: {tally.get(k, 0)}" for k in order))
    print(f"Open: {base / 'Verification Report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
