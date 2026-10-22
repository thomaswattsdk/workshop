# Workshop

**The one working environment: a Linux (WSL) Code session opened in `/home/thomas/workshop`. Projects and tools are made here; nowhere else is a session started.** Thomas's rules load from `~/.claude/CLAUDE.md` in every session; this file adds only what is true of the platform. Decision and reasons: `docs/adr/adr-001-one-environment.md`.

## The one entry point

If the platform is Windows, or the working directory is a `\\wsl...` or drive-letter path (a Windows session reaching in through the network path), **stop**: edit, run and commit nothing, and say in one sentence that this is the wrong door and the right one is a WSL Code session opened in `/home/thomas/workshop`. Why: a Windows session has its own history, paths and line endings and splits the record of the work. Thomas is never the one who guards this; the session is.

## Projects: separate, readable across

- **A project is a folder here with its own `.git`.** It holds its own code and its own record (`CLAUDE.md`, `docs/`: ADRs, build log, handovers). The list of projects is never typed here: look at the folders, and at the MapOfContent Path Registry for what each is. Folders without a `.git` are not projects.
- **Separate:** a project's decisions, rules and history live in its repository and are committed there. A change to a project's files is committed in that project's repository, never in the platform's.
- **Readable across:** any session may read any project's `CLAUDE.md`, `docs/` and newest handover to answer a question or to build on its work. Work items are read and written through the Work Ecosystem core (`work-ecosystem-core`, its `docs/command-line.md`), never by opening the files. Write in a project only when the work in hand is about that project; a binding or fix that must land in another project is committed there, saying which project it came from.
- **No project is assumed at session start.** Do not pre-read anything. When the conversation turns to a named project, run that project's Session Reset (newest handover, glossary, ADRs) before advising.

## Tools: available to every project

A tool is built in its own project and **exposed at user level, never copied**: skills are linked into `~/.claude/skills`, mods live under `~/.claude/dev-mods`, command-line tools are run by their path. Each project's own record says what its tool does. A project uses a tool by name; it does not carry its own copy. When a tool is built or moved, expose it in the same step, or say it is not yet exposed.

## Making a project

A new folder here, `git init`, a `CLAUDE.md` in the pattern of the existing projects (what it is and its phase; the record; *Starting a session*; the rules any session must keep), and a first commit. Project Framework phases apply: no code before the Definition gate. Commit after each completed step; ask before pushing.
