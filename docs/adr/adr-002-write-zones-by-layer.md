# ADR-002: Write rules follow the Difference Engine's layers, not the folder or the file

**Status:** Proposed (2026-10-25; becomes Accepted when Thomas approves, and takes effect only when the hook enforces it and the hard-rule text is amended)
**Date:** 2026-10-25
**Deciders:** Thomas, Claude
**Governing spec:** `Projects\Collaboration Framework\Difference Engine - Concept Seed.md` (kDrive), tenets 2, 4, 5, 6, 7. Treated as the foundational design for working with the knowledge structure (Thomas, 2026-10-25).
**Amends (when accepted):** the three hard rules in `claude-os/CLAUDE.md` (the file-modification rule's exception widens from "workshop repositories" to the zones below); `instructions.md` → *Files and records*.

## Decision

1. **The hard tier is narrowed to what cannot be recovered** (tenet 2). It keeps: deleting or truncating, any external action, secrets, and the files that enforce the rules (hard-rule text, hooks, managed settings, `.git/config`). These ask every time, as now. Everything recoverable moves to a soft tier governed by the layer rules below.
2. **Each part of the knowledge setup sits in one layer, and the layer sets how I may write to it** (tenet 6: the more a mistake can break, the slower and more deliberate the change):

| Layer | What is in it | How I may write |
|---|---|---|
| **Hard guardrail** | `claude-os/CLAUDE.md` hard rules; `workshop/guardrails/`; `/etc/claude-code`; each project's `.git/config`, `.git/hooks`, `.claude`, `.mcp.json` | Ask, with the four-part description. Never covered by any zone. |
| **Guide, core** (near-frozen) | `instructions.md`, `AboutMe.md`, ADRs, design documents, the Difference Engine seed, `Knowledge base\Project Framework\` (framework, templates) | Proposed first (file, change, why, consequence), applied on approval. |
| **Guide, boundary** (living, changes through use) | `Knowledge base\Code Intelligence.md`, skills (`claude-os/Skills/`), glossaries, `Memory.md`, `Workshop/backlog.md` | **Additive entries** (a new pattern, a new row) are applied at once, committed, and listed on a "captured, not yet ticked" list for Thomas. **Revising or removing existing text** is proposed first. Each addition states which feedback outcome it is (tenet 4): core wrong, router mis-fired, or boundary extended. |
| **Records** (instances; read on demand, never modelled, tenet 1) | `Knowledge base\` Car, Family, Finances, Garden, House, Insurance, Legal, Stevns Information; `Work\Falck Knowledge`, `Work\Old work templates and knowledge`, `Work\Thomas work ai tests` | **New files only.** Never overwrite, edit, rename or move an existing file without asking. |
| **Thinking** (the sketchbook) | `Obsidian\Watts Obsidian\` | **New notes in `Inbox` only.** Existing notes are Thomas's; Obsidian edits them live. Reads are unrestricted. |
| **Project records, in git** | workshop repositories | As now: edit committed files, create files in the step that commits them. |
| **Project records, not yet in git** | `Projects\Personal projects\`, `Projects\Work Projects\` | Ask, until the project moves into git (backlog W-13). |
| **Claude's own output** | `Claude outputs\`, `Sweeps\`, `Inbox for Claude\` | New files only. |

3. **Recoverability is the condition for any soft write.** A text file may be edited under the boundary rule only when its history is kept (git, with the history held in WSL, outside the folder kDrive watches). Where no history is kept, the file stays at "ask". This is untested (see Test).
4. **An independent check, not my own read-back, confirms a write** (tenet 7). A small observer reads the hook's log and git, lists every write to a knowledge zone with its layer, and flags any outside its zone or unticked. It is static and rule-based first (the Engine matches a static observer to a near-frozen layer); a dynamic one is a later question. Tracked as W-18.

## Context

Everything under the hard rules asks, because the rules were written for a setting with no history. Now the OS and the workshop are in git, so most edits can be undone, and a prompt on every edit weakens the prompts that matter. The Engine itself keeps the hard tier narrow (tenet 2) and ties pace of change to blast radius (tenet 6). Its tenet 5 ("never auto-applied") is kept for cores and for revisions, and relaxed for additions to living guides because those are additive and reversible; Thomas agreed to watch whether this creates friction.

## Consequences

- **Gains:** Code Intelligence captures no longer queue in a batch file; a capture is committed, listed and reviewable; revert is a commit; fewer prompts; the pending/captured gap becomes a visible list.
- **Costs and risks:** ticking can become a rubber stamp; the zone check must be coded in the edit hook (a path-and-layer table) and tested; the observer must be built; the hard-rule text in `claude-os/CLAUDE.md` and the Engine seed's role table must be edited (each asks first).
- **Not covered:** non-text files with no history stay at "new files only". The Engine's role table is Cowork-shaped and needs updating (observer, router, sensor now map to `retro`, hooks, the Workbench block, ADR links).

## Test

1. A new note in the vault `Inbox` is written with no prompt; an edit to an existing vault note asks.
2. A new Code Intelligence entry is committed, appears on the "not yet ticked" list, and is reverted from git on request.
3. A revision of an existing Code Intelligence entry asks first.
4. An attempt to overwrite a PDF in the Knowledge base is refused.
5. The observer lists all of the above after the session and flags a deliberate out-of-zone write.

**Open before acceptance:** the spike that proves git can keep the history of files on the Windows drive from WSL (on a throwaway copy), and whether the edit hook can resolve `/mnt/d` paths to layers.
