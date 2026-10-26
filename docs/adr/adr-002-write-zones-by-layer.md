# ADR-002: Logic lives in git; the library holds records; write rules follow the Difference Engine's layers

**Status:** Accepted (2026-10-26, Thomas). Proposed 2026-10-25 and revised the same day. The hook enforces it and the amended rule text is in place. Tests 1 to 4 pass; Test 5 (the Observer, W-18) is deferred. Still to do: Thomas retires the library originals in Windows; removal of `guardrails/setup-kdrive-history.sh` awaits his permission.
**Date:** 2026-10-25
**Deciders:** Thomas, Claude
**Governing spec:** `Difference Engine - Concept Seed.md` (now in `Projects\Collaboration Framework`, to move into `claude-os/docs/`), tenets 1, 2, 3, 4, 5, 6, 7. Treated as the foundational design for working with the knowledge structure (Thomas, 2026-10-25).
**Amends (when accepted):** the hard rules in `claude-os/CLAUDE.md` (the file-modification exception widens from "workshop repositories" to the zones below); `instructions.md` → *Files and records* (snapshots are records) and every path that points at logic in the library.

## Decision

1. **All logic for Claude Code lives in git, none in the Knowledge base** (Thomas, 2026-10-25). Logic means anything a session loads, follows or is checked against: instructions, skills, guides, templates, specs. The Cowork habit of keeping them in the library, so a limited session could reach them, ends. To move: `Code Intelligence.md` becomes a skill in the OS repository (a skill is evoked by its description, which is the router of tenet 3; moved whole, split later); `Project Framework\framework.html` and its templates join the `project-framework` skill; the Difference Engine seed moves to `claude-os/docs/`. Each is copied into git and checked byte for byte; the originals are then retired by Thomas in Windows (the shell cannot write there), following the retirement rule for files outside git.
2. **The Knowledge base is a library and an archive of dated artefacts written out of Code.** It holds records: the life folders, Falck deliverables, and time-stamped `.md` snapshots of rules, instructions, ADRs, handovers and retrospectives as a backup and as general knowledge. **A snapshot is a record, not a copy** (Thomas, 2026-10-25): it opens with a header (what it is a snapshot of, the date, the git commit, and "not authority; the live version is in git"), is never loaded as an instruction, and never competes with the live file. `instructions.md` gets one sentence saying so, so the single-authority rule is not read as forbidding it.
3. **The hard tier is narrowed to what cannot be recovered** (tenet 2): deleting or truncating, any external action, secrets, and the files that enforce the rules (hard-rule text, hooks, managed settings, `.git/config`). These ask every time. Everything recoverable is a soft tier governed by the layer rules.
4. **Each part sits in one layer, and the layer sets how I may write to it** (tenet 6):

| Layer | What is in it | How I may write |
|---|---|---|
| **Hard guardrail** | `claude-os/CLAUDE.md` hard rules; `workshop/guardrails/`; `/etc/claude-code`; each project's `.git/config`, `.git/hooks`, `.claude`, `.mcp.json` | Ask, with the four-part description. |
| **Guide, core** (near-frozen) | `instructions.md`, `AboutMe.md`, ADRs, design documents, the Difference Engine seed | Proposed first (file, change, why, consequence), applied on approval. |
| **Guide, boundary** (living), in git | skills (including Code Intelligence and Project Framework once moved), glossaries, `Memory.md`, `Workshop/backlog.md` | **Additive entries** are applied at once, committed, and listed as "captured, not yet ticked" for Thomas. **Revising or removing existing text** is proposed first. Each addition states which feedback outcome it is (tenet 4): core wrong, router mis-fired, or boundary extended. |
| **Project records, in git** | workshop repositories | As now: edit committed files, create files in the step that commits them. |
| **Library records and archive** | `Knowledge base\` (life folders, `Work\`, the Code archive of snapshots); Claude's output folders (`Claude outputs\`, `Sweeps\`, `Inbox for Claude\`) | **New files only.** Never overwrite, edit, rename or move an existing file without asking. |
| **Thinking** (the sketchbook) | `Obsidian\Watts Obsidian\` | **New notes in `Inbox` only.** Existing notes are Thomas's. Reads are unrestricted. |
| **Not yet in git** | `Projects\` in kDrive (until backlog W-13) | Ask. |

5. **The library gets no history store.** Nothing in it needs one: logic is in git, which keeps its history; library records are only added to, never edited; backups of the library are Thomas's, made in Windows. (A first draft proposed a git history kept in WSL for `Code Intelligence.md`; it falls away because that file moves into git.)
6. **An independent check, not my own read-back, confirms a write** (tenet 7). A small rule-based Observer reads the edit hook's log and git, lists every write to a zone with its layer, and flags any outside its zone or unticked. A dynamic (AI) observer is a later question. Tracked as W-18.
7. **Skills that no longer work in Code but are still wanted are rebuilt** (self-refresh and observer roles; W-19), one by one as Thomas marks them.
8. **The Map of Content splits by job, and each half lives with what it serves** (Thomas, 2026-10-25). The **Path Registry** (logical key to location; sessions and skills resolve through it) is logic, so it moves into `claude-os`; projects already in git need no rows, because the picker finds them live. The **library map** (what is in the Knowledge base and the vault) stays in the library, hand-edited, reduced to contents; its edits ask, which is cheap because it changes rarely. The registry says *where* and the library map says *what is in it*; no row text lives in both. **Dated index snapshots** of the library (path, size, modified date for the Knowledge base and the vault, written as records in the Code archive) are taken before and after structural changes such as the migration, so that a later listing can be compared against them to see exactly what changed or went missing. This is the library's delta baseline now that it has no history store.

## Context

The hard rules were written for a setting with no history, and the library was where a limited Cowork session found its guides. Now the OS and the workshop are in git, most edits can be undone, and a prompt on every edit weakens the prompts that matter. The Engine keeps the hard tier narrow (tenet 2), ties pace of change to blast radius (tenet 6), and wants guides evoked rather than always loaded (tenet 3). Its tenet 5 ("never auto-applied") is kept for cores and revisions and relaxed for additions to living guides, which are additive and reversible; Thomas agreed to watch whether that creates friction.

## Consequences

- **Gains:** Code Intelligence captures stop queueing in a batch file (the batch file's reason ends with the move); revert is a commit; fewer prompts; the pending/captured gap becomes a visible list; the library is simple (read, add, never edit).
- **Costs and risks:** ticking can become a rubber stamp; the zone table lives in `guardrails/zones.json` and the hook must enforce it; the Observer must be built; several files must change with approval (hard-rule text, `instructions.md`, four skills, the Cowork map, the Path Registry); the originals in the library are retired by hand.
- **Not covered:** the Engine's role table is Cowork-shaped and needs updating (observer, router, sensor now map to `retro`, hooks, the Workbench block, ADR links). Snapshots need a layout (proposed: `Knowledge base\Code archive\<kind>\YYYY-MM-DD-name.md`, written by me with the file editor at moments that matter).

## Test

1. A new note in the vault `Inbox` is written with no prompt; an edit to an existing vault note asks.
2. A new snapshot in the Code archive is written with no prompt and carries its header; an attempt to overwrite an existing file (a PDF, say) in the Knowledge base asks first, and the hook logs the "ask" (tested 2026-10-25).
3. A new entry in the Code Intelligence skill is committed, appears on the "not yet ticked" list, and is reverted from git on request; a revision of an existing entry asks first.
4. No instruction, skill or template is loaded from the Knowledge base: a search of `claude-os` and `workshop` for "Knowledge base" finds only records and snapshots.
5. The Observer lists all of the above after the session and flags a deliberate out-of-zone write.

**Open before acceptance:** the migration (step 1 copies, then the reference changes, then the retirements); simplifying the hook and `zones.json` (the Code Intelligence entry and the history check go); removing `guardrails/setup-kdrive-history.sh` (a deletion, needs Thomas's explicit permission); the amended text in `claude-os/CLAUDE.md` and `instructions.md`.
