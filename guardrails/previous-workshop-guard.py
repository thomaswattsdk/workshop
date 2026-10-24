#!/usr/bin/env python3
"""Pre-action check for the workshop (Learning to Fly, spike step 6).

Runs before every shell command Claude Code issues. It refuses two things
outright, and stays silent otherwise so the normal permission rules apply:

1. Deletions that reach outside the workshop, or that are written in a
   roundabout form (find -delete, xargs rm, sh -c "rm ...", a script
   one-liner). Plain rm/rmdir/unlink/shred/truncate/git clean inside the
   workshop are left to the "ask" rules, so Thomas is asked each time.
2. Docker commands that would give a container kDrive, the Windows drives,
   the whole filesystem or the Docker engine itself. Docker runs outside
   the sandbox, so this check is the only thing watching it.

It reads the command as written, so a disguised command can still slip
past. It is a tripwire, not a wall; the sandbox is the wall for kDrive.
"""
import json
import os
import re
import shlex
import sys

WORKSHOP = "/home/thomas/workshop"
SAFE_ROOTS = (WORKSHOP, "/tmp")

DELETE_PROGRAMS = {"rm", "rmdir", "unlink", "shred", "truncate", "srm", "wipe"}
PROTECTED_HINTS = ("/mnt/", "/mnt\"", "/mnt'", "/mnt ", "\\\\wsl", "d:\\", "c:\\", "d:/", "c:/")
ROUNDABOUT_DELETE = [
    r"-delete\b",
    r"\bxargs\b[^|;&]*\b(rm|rmdir|unlink|shred)\b",
    r"-exec(dir)?\s+(rm|rmdir|unlink|shred)\b",
    r"\b(sh|bash|zsh|dash)\s+-c\s+.*\b(rm|rmdir|unlink|shred)\b",
    r"\b(os\.remove|os\.unlink|os\.rmdir|shutil\.rmtree|unlinkSync|rmSync|rmdirSync|fs\.rm|File\.delete)\b",
    r"\bgit\s+clean\b.*-[a-zA-Z]*x",
    r"\b(powershell|pwsh|cmd|wsl)\.exe\b",
    r"(^|[\s;&|(])(powershell|pwsh)(\s|$)",
    r"/mnt/[a-z]/\S*\.(exe|bat|cmd|ps1)\b",
]
DOCKER_DANGER = [
    r"(^|\s)-v\s*/?:",                 # mounting the filesystem root
    r"(^|\s)(-v|--volume)[ =]/(\s|:)",
    r"source=/(,|\s|$)",
    r"--privileged\b",
    r"docker\.sock",
    r"--pid[ =]host\b",
    r"--cap-add\b",
]


def refuse(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Workshop guard: " + reason,
        }
    }))
    sys.exit(0)


def mentions_protected(text):
    t = text.lower()
    return any(h in t for h in PROTECTED_HINTS) or t.rstrip().endswith("/mnt")


def paths_outside_workshop(args, cwd):
    outside = []
    for a in args:
        if a.startswith("-"):
            continue
        p = os.path.expanduser(a)
        if not os.path.isabs(p):
            p = os.path.join(cwd, p)
        p = os.path.normpath(p)
        if not any(p == r or p.startswith(r + "/") for r in SAFE_ROOTS):
            outside.append(a)
    return outside


def split_commands(command):
    return [c for c in re.split(r"&&|\|\||;|\||\n|\$\(|`", command) if c.strip()]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = (data.get("tool_input") or {}).get("command", "")
    cwd = data.get("cwd") or WORKSHOP

    # Docker: refuse anything that hands a container kDrive, Windows or the host.
    if re.search(r"\bdocker\b", command):
        if mentions_protected(command):
            refuse("Docker may not be given kDrive or the Windows drives.")
        for pat in DOCKER_DANGER:
            if re.search(pat, command):
                refuse("Docker may not be given the whole filesystem, the engine itself, or extra host powers.")
        if re.search(r"\bdocker\s+compose\b|\bdocker-compose\b", command):
            for name in ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"):
                path = os.path.join(cwd, name)
                if os.path.isfile(path):
                    with open(path, encoding="utf-8", errors="replace") as fh:
                        body = fh.read()
                    if mentions_protected(body) or re.search(r"docker\.sock|privileged:\s*true|^\s*-\s*/:", body, re.M):
                        refuse(name + " gives a container kDrive, Windows or host access.")

    # Windows programs run outside the sandbox and can reach kDrive directly.
    for pat in ROUNDABOUT_DELETE:
        if re.search(pat, command, re.IGNORECASE):
            refuse("roundabout deletes and Windows programs are not allowed. "
                   "Use rm/rmdir directly so Thomas is asked.")

    # Plain delete programs: refused when they reach outside the workshop.
    for part in split_commands(command):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        while words and re.match(r"^\w+=", words[0]):
            words = words[1:]
        if words and words[0] == "sudo":
            refuse("sudo is Thomas's to run, not Claude's.")
        while words and words[0] in ("env", "nice", "nohup", "time", "command", "exec"):
            words = words[1:]
        if not words:
            continue
        prog = os.path.basename(words[0])
        if prog in DELETE_PROGRAMS or (prog == "mv" and mentions_protected(part)):
            if mentions_protected(part):
                refuse("nothing in kDrive or on the Windows drives may be deleted or moved.")
            outside = paths_outside_workshop(words[1:], cwd)
            if outside:
                refuse("deletes are only possible inside the workshop folder (" + ", ".join(outside) + ").")

    sys.exit(0)


if __name__ == "__main__":
    main()
