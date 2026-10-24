#!/usr/bin/env python3
"""Pre-action check for the workshop (Learning to Fly, spike step 6).

Runs before every shell command Claude Code issues. It refuses three things
outright, and stays silent otherwise so the normal permission rules apply:

1. Deletions that reach outside the workshop, or that are written in a
   roundabout form (find -delete, xargs rm, sh -c "rm ...", a script
   one-liner). Plain rm/rmdir/unlink/shred/truncate/git clean inside the
   workshop are left to the "ask" rules, so Thomas is asked each time.
2. Docker commands that would give a container kDrive, the Windows drives,
   the whole filesystem or the Docker engine itself. Docker runs outside
   the sandbox, so this check is the only thing watching it.
3. A git push that is not a plain push to GitHub. git push also runs
   outside the sandbox (ADR-002), so it must stand alone, with no command
   chained to it, no config overrides, and only GitHub remotes. The one
   other way to push is the fixed script /etc/claude-code/workshop-push,
   followed by exactly one plain project name.

It reads the command as written, so a disguised command can still slip
past. It is a tripwire, not a wall; the sandbox is the wall for kDrive.

What it does not scan: text that only a read-only program prints or searches
for (grep, echo, cat ...), and the body of a plain `cat <<EOF` heredoc, since
that text is data, not a command. A word such as "unlink" or "git push" in a
search, an echo or a commit message is therefore harmless. Anything that
could run what it is given (a shell, xargs, find, a substitution, a heredoc
that is piped or redirected) is still scanned in full.
Tests: test_workshop_guard.py in this folder.
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

# Programs that only read or print. What they are given in quotes is data, so it is not scanned. Left out on
# purpose, because an option can make them run another program: rg (--pre), sort (--compress-program), sed, awk,
# find, xargs, env, any shell or interpreter, and git.
READ_ONLY = {"grep", "egrep", "fgrep", "cat", "head", "tail", "wc", "ls", "echo", "printf", "diff", "cmp", "stat",
             "file", "cut", "tr", "uniq", "basename", "dirname", "realpath", "readlink", "pwd", "true", "false"}
SUBSTITUTION = re.compile(r"\$\(|`|<\(|>\(")
# A heredoc that only displays text: `cat <<'EOF'` alone on its line, or the same inside $( ... ) at the end of a line
# (the usual way to write a commit message). Piped or redirected heredocs do not match, so they are scanned.
DISPLAY_HEREDOC = re.compile(r"^\s*cat\s+<<-?\s*(['\"]?)(\w+)\1\s*$|\$\(\s*cat\s+<<-?\s*(['\"]?)(\w+)\3\s*$")


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


def strip_display_heredocs(command):
    """Drop the body of a heredoc that only displays text; keep its first line and its terminator."""
    lines = command.split("\n")
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        m = DISPLAY_HEREDOC.search(lines[i])
        if m:
            delimiter = m.group(2) or m.group(4)
            end = next((j for j in range(i + 1, len(lines)) if lines[j].strip() == delimiter), None)
            if end is not None:
                out.append(lines[end])
                i = end + 1
                continue
        i += 1
    return "\n".join(out)


def top_level_segments(command):
    """Cut a command at ; & | and newlines that sit outside quotes. Returns [text, separator, text, ...]."""
    parts, cur, quote, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if ch == "\\" and quote != "'" and i + 1 < len(command):
            cur.append(ch)
            cur.append(command[i + 1])
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
            cur.append(ch)
        elif ch in "'\"":
            quote = ch
            cur.append(ch)
        elif ch in ";&|\n":
            parts.append("".join(cur))
            parts.append(ch)
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def mask_read_only(command):
    """Replace each read-only segment that holds no substitution by its program name alone."""
    parts = top_level_segments(command)
    for k in range(0, len(parts), 2):
        seg = parts[k]
        if SUBSTITUTION.search(seg):
            continue
        try:
            words = shlex.split(seg)
        except ValueError:
            continue
        if words and os.path.basename(words[0]) in READ_ONLY:
            parts[k] = " " + words[0] + " "
    return "".join(parts)


def scannable(command):
    """The text the delete, Docker and push checks look at: the command without its harmless data."""
    return mask_read_only(strip_display_heredocs(command))


GITHUB_URL = re.compile(r"^(https://github\.com/|git@github\.com:|ssh://git@github\.com/)[\w.-]+/[\w.-]+?(\.git)?/?$")
PUSH_OPTIONS_REFUSED = ("--repo", "--receive-pack", "--exec")


def git_output(args, cwd):
    import subprocess
    try:
        out = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    return out.stdout.split() if out.returncode == 0 else []


def check_git_push(command, cwd):
    """git push runs outside the sandbox, so only a plain push to GitHub may pass."""
    mentions_push = False
    for part in split_commands(command):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        if "git" in (os.path.basename(w) for w in words) and "push" in words:
            mentions_push = True
    if not mentions_push:
        return

    try:
        words = shlex.split(command)
    except ValueError:
        refuse("a git push must be a plain, single command.")
    chained = re.search(r"&&|\|\||[;|&<>\n`]|\$\(", command)
    if chained or len(words) < 2 or words[0] != "git" or words[1] != "push":
        refuse("a git push must stand alone and start with 'git push': "
               "no chained commands, redirections, settings or git options before it.")
    for w in words[2:]:
        if w.startswith(PUSH_OPTIONS_REFUSED):
            refuse("git push may not name its own remote program or target with " + w + ".")

    rewrites = git_output(["config", "--get-regexp", r"^url\..*\.(pushinsteadof|insteadof)$"], cwd)
    if rewrites is None or rewrites:
        refuse("git is set to rewrite remote addresses, so the push target cannot be trusted.")

    positional = [w for w in words[2:] if not w.startswith("-")]
    if positional:
        target = positional[0]
        if "/" in target or ":" in target:
            urls = [target]
        else:
            urls = git_output(["remote", "get-url", "--push", "--all", target], cwd)
    else:
        urls = []
        for remote in git_output(["remote"], cwd) or []:
            urls += git_output(["remote", "get-url", "--push", "--all", remote], cwd) or []
    if not urls:
        refuse("the push target could not be found, so it cannot be checked.")
    for url in urls:
        if not GITHUB_URL.match(url):
            refuse("git push may only go to GitHub (" + url + ").")


PUSH_SCRIPT = "/etc/claude-code/workshop-push"
PUSH_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def check_push_script(command):
    """The sanctioned push: the fixed script, one plain project name, nothing else."""
    if PUSH_SCRIPT not in command:
        return False
    try:
        words = shlex.split(command)
    except ValueError:
        refuse("the push script must be a plain, single command.")
    chained = re.search(r"&&|\|\||[;|&<>\n`]|\$\(", command)
    if chained or len(words) != 2 or words[0] != PUSH_SCRIPT or not PUSH_NAME.match(words[1]):
        refuse("the push script must stand alone: " + PUSH_SCRIPT + " <project name>, "
               "with nothing before or after it.")
    return True


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = (data.get("tool_input") or {}).get("command", "")
    cwd = data.get("cwd") or WORKSHOP

    # The fixed push script is the one sanctioned way to push any project. It is judged on the command as written.
    if check_push_script(command):
        sys.exit(0)

    # Everything below looks at the command without its harmless data (see the header).
    scan = scannable(command)

    # git push runs outside the sandbox: only a plain push to GitHub.
    check_git_push(scan, cwd)

    # Docker: refuse anything that hands a container kDrive, Windows or the host.
    if re.search(r"\bdocker\b", scan):
        if mentions_protected(scan):
            refuse("Docker may not be given kDrive or the Windows drives.")
        for pat in DOCKER_DANGER:
            if re.search(pat, scan):
                refuse("Docker may not be given the whole filesystem, the engine itself, or extra host powers.")
        if re.search(r"\bdocker\s+compose\b|\bdocker-compose\b", scan):
            for name in ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"):
                path = os.path.join(cwd, name)
                if os.path.isfile(path):
                    with open(path, encoding="utf-8", errors="replace") as fh:
                        body = fh.read()
                    if mentions_protected(body) or re.search(r"docker\.sock|privileged:\s*true|^\s*-\s*/:", body, re.M):
                        refuse(name + " gives a container kDrive, Windows or host access.")

    # Windows programs run outside the sandbox and can reach kDrive directly.
    for pat in ROUNDABOUT_DELETE:
        if re.search(pat, scan, re.IGNORECASE):
            refuse("roundabout deletes and Windows programs are not allowed. "
                   "Use rm/rmdir directly so Thomas is asked.")

    # Plain delete programs: refused when they reach outside the workshop.
    for part in split_commands(scan):
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
