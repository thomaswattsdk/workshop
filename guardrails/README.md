# Workshop guardrails

The machine-wide rules that sit under every Claude Code session on this computer, kept here so they have history, tests and a repeatable install. The live copies are in `/etc/claude-code`; this folder is the source.

| File | What it is |
|---|---|
| `managed-settings.json` | The sandbox, the permission rules that always ask, and the two hooks below. Written by the owner of the machine; a session cannot change it. |
| `workshop-guard.py` | Before every shell command: refuses deletes that reach outside the workshop or hide in a roundabout form, Docker given too much, and a push that is not a plain push to GitHub. A tripwire, not a wall. |
| `workshop-edit-guard.py` | Before every Edit, Write and NotebookEdit: the "no file change without permission" rule as code. Allows a file git already holds with no uncommitted changes; asks about everything else. Also holds the knowledge zones (ADR-002): in kDrive and `claude-os`, new files only in records, the vault's `Inbox` and Claude's output folders, additions only to living guides in the OS repository (committed, nothing uncommitted), everything else asks; each zone decision is logged to `~/.local/state/workshop/zone-decisions.jsonl` for the Observer. The library holds records, not logic, so it takes new files only and has no history store. |
| `zones.json` | Which folder of kDrive and `claude-os` is in which layer (new files only, additions only, always asks). The edit guard reads it, so changing a zone is a change to this one protected file, not to code. Installed beside the guard. |
| `workshop-push` | The one way to send a project to GitHub from a session: `/etc/claude-code/workshop-push <project>` (a project folder, `workshop` for the platform repository, or `claude-os`). Behind an approval prompt that shows the exact command. A plain `git push` no longer runs in a session: it is not excluded from the sandbox, where the GitHub token is hidden. |
| `workshop-projects` | Read-only: lists every project (most recently committed first) with its phase and the opening of its newest handover. Run as `/etc/claude-code/workshop-projects` at the start of a session, so the project picker needs no improvised shell loop and no approval prompt. |
| `test_workshop_guard.py`, `test_workshop_edit_guard.py`, `test_workshop_push.py`, `test_workshop_projects.py` | The tests. Standard library only. |
| `install.sh`, `verify-install.sh` | Install into `/etc/claude-code` (sudo, tests first, backs up what it replaces); check that the installed copies match. |
| `previous-*` | The files from before 2026-09-25, kept as the way back for that change. Git history now does this job. |

## Run the tests

```
python3 -I test_workshop_guard.py
python3 -I test_workshop_edit_guard.py
```

## Install or update

```
sudo bash /home/thomas/workshop/guardrails/install.sh
```

Then start a new session. To check later whether the installed copies are current: `bash /home/thomas/workshop/guardrails/verify-install.sh`.

## Roll back

`install.sh` copies each file it replaces to `<name>.bak-<date-time>` beside it. Copy that file back over the original.

## What it does not do

- The shell guard reads the command as written; a determined disguise can pass. The sandbox and the permission rules are the walls.
- It does not cover files written by a program the session starts (a script that edits files). The sandbox limits where a shell may write.
- It protects nothing outside this computer. A push is limited by the GitHub token's scope.

## History

Decisions and reasons: Learning to Fly ADR-001 and ADR-002 (kDrive, `Projects/Personal projects/Learning to Fly/`; copies in `claude-os/Workshop/adr/`), and the audit of 2026-10-24 in `claude-os/docs/`.
