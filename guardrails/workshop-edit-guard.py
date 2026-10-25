#!/usr/bin/env python3
"""Pre-action check for the file tools (Edit, Write, NotebookEdit): the "no file change without permission" rule, as code.

The hard rule (Claude Cowork OS CLAUDE.md) says Claude never edits or creates a file without asking, with one
exception: in a workshop repository, in a WSL session, a file that git already holds with no uncommitted changes may be
edited without asking, and a new file may be created if it is committed in the step that creates it. Git keeps the last
version, which is the reason the rule exists (Learning to Fly ADR-001). This hook makes that exception mechanical:

  allow  a tracked file with no uncommitted changes, inside a workshop repository
  allow  a new file in a workshop repository that git would not ignore
  allow  a file in the session's own scratch folder under /tmp/claude*
  ask    everything else: untracked or modified files, ignored files, anything outside the workshop repositories
         (kDrive, home dotfiles, claude-os), and the protected files below, even where git holds them
  ask    a work-item record (type: work-item): those change through the core's command line, never by editing

Knowledge zones (ADR-002, after the Difference Engine's layers). Two more roots have their own rules, checked first, and every
decision in them is appended to a log that the Observer reads (tenet 7: a check outside the loop that made the change):

  new    a file that does not exist yet is allowed, an existing one asks  (records, the vault's Inbox, Claude's output folders)
  add    a living guide in a git repository (the OS repository): allowed when the edit only adds text (the old text stays
         whole inside the new), git holds the file and it has no uncommitted changes; a new file is allowed; revising or
         removing existing text asks
  ask    everything else in the root (hard rules, core guides, the frozen Cowork copy, the rest of kDrive)

The library (kDrive root) holds records, not logic, so it has no "add" zone and no history store (ADR-002).

It answers with a decision only for those cases. On any error it says nothing, so the normal permission rules apply.
Deletion by overwriting is covered the same way: only a clean, tracked file can be replaced without asking, and git has it.
Tests: test_workshop_edit_guard.py in this folder. WORKSHOP_GUARD_ROOT overrides the workshop folder for those tests only.
"""
import datetime
import json
import os
import subprocess
import sys

WORKSHOP = os.environ.get("WORKSHOP_GUARD_ROOT") or "/home/thomas/workshop"
# The knowledge zones. The environment variables override the places for the tests only.
HOME = os.path.expanduser("~")
KDRIVE = os.environ.get("KDRIVE_GUARD_ROOT") or "/mnt/d/Claude CoWork"
OS_ROOT = os.environ.get("OS_GUARD_ROOT") or "/home/thomas/claude-os"
ZONE_LOG = os.environ.get("ZONE_LOG") or os.path.join(HOME, ".local/state/workshop/zone-decisions.jsonl")
# Rules per root, read from zones.json beside this file (first match wins; a path that matches none asks).
# If the file cannot be read, no rule matches and everything in the roots asks.
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "zones.json"), encoding="utf-8") as _fh:
        _zones = json.load(_fh)
except Exception:
    _zones = {}
KDRIVE_RULES = tuple(tuple(r) for r in _zones.get("kdrive", ()))
OS_RULES = tuple(tuple(r) for r in _zones.get("os", ()))
SCRATCH = ("/tmp/claude",)
# Files that govern every session: never changed without asking, even though git holds them.
PROTECTED = ("guardrails", "CLAUDE.md")  # relative to the workshop folder
PROTECTED_PARTS = (".git", ".claude", ".mcp.json")


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                              "permissionDecisionReason": "Workshop edit guard: " + reason}}))
    sys.exit(0)


def git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True, timeout=5)


def repo_root(path):
    """The nearest folder above path that holds a .git, but only inside the workshop."""
    cur = os.path.dirname(path)
    while cur.startswith(WORKSHOP + "/") or cur == WORKSHOP:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        if cur == WORKSHOP:
            break
        cur = os.path.dirname(cur)
    return None


def is_work_item(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = [fh.readline() for _ in range(12)]
    except OSError:
        return False
    return head and head[0].strip() == "---" and any(line.strip() == "type: work-item" for line in head[1:])


def under(path, root):
    return path == root or path.startswith(root + "/")


def adds_only(tool, tool_input, path):
    """True when the edit only adds text: the old text stays whole inside the new text."""
    def one(old, new):
        return bool(old) and isinstance(new, str) and old in new
    if tool == "Edit":
        return one(tool_input.get("old_string"), tool_input.get("new_string"))
    if tool == "MultiEdit":
        edits = tool_input.get("edits") or []
        return bool(edits) and all(one(e.get("old_string"), e.get("new_string")) for e in edits)
    if tool == "Write":
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read() in (tool_input.get("content") or "")
    return False


def zone_decision(path, tool, tool_input):
    """(decision, reason, kind) when path is inside a knowledge zone, otherwise None."""
    for root, rules in ((KDRIVE, KDRIVE_RULES), (OS_ROOT, OS_RULES)):
        if not under(path, root) or path == root:
            continue
        rel = os.path.relpath(path, root)
        if any(p in PROTECTED_PARTS for p in rel.split(os.sep)):
            return "ask", "this is a protected path (" + rel + ").", "ask"
        kind = next((k for prefix, k in rules if rel == prefix or rel.startswith(prefix + "/")), "ask")
        if kind == "ask":
            return "ask", "this layer changes only when Thomas has approved the change (" + rel + ").", "ask"
        if not os.path.exists(path):
            return "allow", "a new file in a zone that takes new files; nothing existing is lost.", kind
        if kind == "new":
            return "ask", "this file already exists, and this zone takes new files only.", kind
        # kind == "add": a living guide, which must sit in a git repository (a root without one always asks)
        git_args = ["git", "-C", root]
        if subprocess.run(git_args + ["ls-files", "--error-unmatch", "--", rel], capture_output=True, timeout=5).returncode != 0:
            return "ask", "git does not hold this file yet, so a change could not be undone.", kind
        if subprocess.run(git_args + ["status", "--porcelain", "--", rel], capture_output=True, text=True, timeout=5).stdout.strip():
            return "ask", "this guide has uncommitted changes, which an edit could not separate from the last version.", kind
        if not adds_only(tool, tool_input, path):
            return "ask", "this edit revises or removes existing text; a revision is proposed first.", kind
        return "allow", "this edit only adds to a living guide, and git holds the last version.", kind
    return None


def log_decision(path, tool, kind, decision, reason):
    """One JSON line per zone decision, for the Observer. A failure here changes nothing."""
    try:
        os.makedirs(os.path.dirname(ZONE_LOG), exist_ok=True)
        entry = {"time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "path": path,
                 "tool": tool, "zone": kind, "decision": decision, "reason": reason}
        with open(ZONE_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
        tool = data.get("tool_name")
        if tool not in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            sys.exit(0)
        given = (data.get("tool_input") or {}).get("file_path") or (data.get("tool_input") or {}).get("notebook_path")
        if not given:
            sys.exit(0)
        path = os.path.realpath(os.path.join(data.get("cwd") or WORKSHOP, os.path.expanduser(given)))
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)

    try:
        zone = zone_decision(path, tool, data.get("tool_input") or {})
        if zone:
            log_decision(path, tool, zone[2], zone[0], zone[1])
            decide(zone[0], zone[1])
        inside_workshop = path == WORKSHOP or path.startswith(WORKSHOP + "/")
        if not inside_workshop and any(path == s or path.startswith(s) for s in SCRATCH):
            decide("allow", "the session's own scratch folder.")
        if is_work_item(path):
            decide("ask", "this is a work-item record; it changes through the core's command line, not by editing the file.")
        root = repo_root(path)
        if root is None:
            decide("ask", "this file is outside the workshop repositories, so git does not hold it.")
        rel = os.path.relpath(path, root)
        parts = rel.split(os.sep)
        if any(p in PROTECTED_PARTS for p in parts):
            decide("ask", "this is a protected path (" + rel + ").")
        from_workshop = os.path.relpath(path, WORKSHOP)
        if any(from_workshop == p or from_workshop.startswith(p + os.sep) for p in PROTECTED):
            decide("ask", "this file governs every session, so it is never changed without asking.")

        if os.path.exists(path):
            tracked = git(root, "ls-files", "--error-unmatch", "--", rel).returncode == 0
            if not tracked:
                decide("ask", "git does not hold this file yet, so a change could not be undone.")
            if git(root, "status", "--porcelain", "--", rel).stdout.strip():
                decide("ask", "this file has uncommitted changes, which an edit could not separate from the last version.")
            decide("allow", "git holds this file with no uncommitted changes, so the last version is safe.")
        if git(root, "check-ignore", "-q", "--", rel).returncode == 0:
            decide("ask", "git ignores this path, so a new file there would not be kept.")
        decide("allow", "a new file in a workshop repository; it is committed in the step that creates it.")
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
