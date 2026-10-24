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

It answers with a decision only for those cases. On any error it says nothing, so the normal permission rules apply.
Deletion by overwriting is covered the same way: only a clean, tracked file can be replaced without asking, and git has it.
Tests: test_workshop_edit_guard.py in this folder. WORKSHOP_GUARD_ROOT overrides the workshop folder for those tests only.
"""
import json
import os
import subprocess
import sys

WORKSHOP = os.environ.get("WORKSHOP_GUARD_ROOT") or "/home/thomas/workshop"
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
