# ADR-001: One environment, projects and tools on one platform

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Thomas, Claude
**Amends:** Learning to Fly ADR-001, change 2 (sessions open in the repository itself). Its other changes stand.

## Decision

**There is one kind of session: a Linux (WSL) Code session opened in `/home/thomas/workshop`.** Projects (repositories) and tools are made and used from there. Projects stay separate in git and readable across; tools are exposed once at user level and available to every project.

**A session starts by asking what to work on** (added the same day): the choice of an existing project or a new one sets the session's focus, and the project's own record sets it up. All projects are open to every session; git is the only separation (Thomas: "this is my work-plane").

## Context

Learning to Fly ADR-001 opened sessions inside each repository because the first workshop kept every record in kDrive and a bootstrap folder had to reach across to it. Rules now load from `~/.claude/CLAUDE.md`, so that reason is gone, while the rule it left behind (open in the repository) created many entry points. On 2026-10-22 two Windows-native sessions opened on `work-ecosystem` through its `\\wsl.localhost` path and split its history and broke its environment.

## Consequences

- **Gains:** one place to start; the side panel and file cards see every project; cross-project reading needs no hop; the Workbench's view across work matches where the session lives.
- **Cost:** session history is keyed by folder, so older per-project histories stay under their own names and are not carried into the platform's; one session can write in every project, so separation rests on git (commit per step, per repository) and on the rules in `CLAUDE.md`, not on the sandbox.
- **Not guarded by a file:** which environment the Claude app offers or defaults to is an app setting. The guard in `CLAUDE.md` makes a wrong-door session stop; it cannot close the door.

## Test

Open a session at `/home/thomas/workshop`. It passes when the rules load, a question that names a project triggers that project's Session Reset, a file card from any project opens, and a tool from one project is used on another by name.
