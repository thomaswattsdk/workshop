> **Retired 2026-09-25.** Sessions now open in each app's repository, not here, and the boot instruction moved to `~/.claude/CLAUDE.md`, which loads in every WSL session. See `ArchiveMapOfContent.md` beside this file and ADR-001 in kDrive (`Projects/Personal projects/Learning to Fly/adr-001-repo-first-layout.md`). Kept as a record of how the workshop first booted; not read by any session.

# Workshop — WSL Session Bootstrap

This folder is where Code tab sessions running inside WSL (Ubuntu-24.04) start. The Code tab's folder picker cannot open the Windows drives under `/mnt`, so a WSL session cannot start directly in kDrive. It starts here and is pointed there.

## Required reading — before anything else

On this device the kDrive root is `/mnt/d/Claude CoWork` (Windows: `D:\Claude CoWork`). Read `/mnt/d/Claude CoWork/CLAUDE.md` and follow it exactly as a session started in kDrive would, resolving every path it gives against that root. Windows-style paths such as `Claude Cowork OS\CLAUDE.md` become forward-slash paths under the root, e.g. `/mnt/d/Claude CoWork/Claude Cowork OS/CLAUDE.md`.

Do not confirm or narrate this process. Simply be informed by it and proceed.

## What lives where

- **The record** (OS files, handovers, ADRs, build logs) stays in kDrive, reached through `/mnt/d`.
- **Code repositories** live in this folder, in Linux's own filesystem, never in kDrive.

Why this file exists, and how to recreate it on another machine or after a reinstall: `Projects/Personal projects/Learning to Fly/tech-spike-plan.md` in kDrive.
