# Workshop

**The one working environment: a Linux (WSL) Code session opened in `/home/thomas/workshop`. Projects and tools are made here; nowhere else is a session started.** Thomas's rules load from `~/.claude/CLAUDE.md` in every session; this file adds only what is true of the platform. Decision and reasons: `docs/adr/adr-001-one-environment.md`.

## The one entry point

If the platform is Windows, or the working directory is a `\\wsl...` or drive-letter path (a Windows session reaching in through the network path), **stop**: edit, run and commit nothing, and say in one sentence that this is the wrong door and the right one is a WSL Code session opened in `/home/thomas/workshop`. Why: a Windows session has its own history, paths and line endings and splits the record of the work. Thomas is never the one who guards this; the session is.

## Projects: separate, readable across

- **A project is a folder here with its own `.git`.** It holds its own code and its own record (`CLAUDE.md`, `docs/`: ADRs, build log, handovers). The list of projects is never typed here: look at the folders, and at the MapOfContent Path Registry for what each is. Folders without a `.git` are not projects.
- **Separate:** a project's decisions, rules and history live in its repository and are committed there. A change to a project's files is committed in that project's repository, never in the platform's.
- **Readable across:** any session may read any project's `CLAUDE.md`, `docs/` and newest handover to answer a question or to build on its work. Work items are read and written through the Work Ecosystem core (`work-ecosystem-core`, its `docs/command-line.md`), never by opening the files. Write in a project only when the work in hand is about that project; a binding or fix that must land in another project is committed there, saying which project it came from.
- **Every session has access to every project.** This is Thomas's work-plane; git does the separating (a commit per step, in the repository of the project worked on). No sandbox or permission walls between projects.

## Starting a session

Thomas does not carry resume prompts between sessions; the record does. After the entry-point check and before anything else, ask **"What would you like to work on today?"** in a **selection box** (the one place a picker is wanted, by Thomas's choice; every other question stays in prose). Read the projects live, never from memory, by running `/etc/claude-code/workshop-projects` (it lists them most recently committed first, with phase and newest handover; it is the one fixed command allowed to run without a prompt, so never improvise a shell loop for this; if it is missing, `guardrails/README.md` says how to install it). Each option is a project's name, with its phase (from its `CLAUDE.md`) and where it stands (the opening of its newest handover) in the description. A box holds four options, so the full list is paged: the first box shows the two most recent projects, **"More projects…"** and **"Start a new project"**; "More projects…" opens a further box with the next three projects and another "More projects…" until the list is exhausted. "Other" takes free text. No project is assumed and nothing else is pre-read; the conflict sweep and the open-handover read run right after the choice (`instructions.md` → *Session start* holds the one order). Whatever Thomas answers is enough to begin: a project's name, a description, "the last one".

- **A project chosen:** that choice sets the session up. Read the project's `CLAUDE.md`, run its Session Reset from the record (newest handover, glossary, ADRs, decision map, `git status`), then say in two or three sentences where the work stands and what its next step is, and offer to start it. From then on the project is the **focus**: work, commits and rules are its own. Other projects stay readable, and a change that must land in another project is committed there, saying where it came from.
- **A new project:** follow *Making a project* below, beginning with the MVP Pitch.
- **Work that spans projects, or no project:** say so and proceed with the platform as the focus.
- **The focus can change mid-session** when Thomas names another project: run that project's Session Reset before advising on it.

## Tools: available to every project

A tool is built in its own project and **exposed at user level, never copied**: skills are linked into `~/.claude/skills`, mods live under `~/.claude/dev-mods`, command-line tools are run by their path. Each project's own record says what its tool does. A project uses a tool by name; it does not carry its own copy. When a tool is built or moved, expose it in the same step, or say it is not yet exposed.

## Making a project

A new folder here, `git init`, a `CLAUDE.md` in the pattern of the existing projects (what it is and its phase; the record; *Starting a session*; the rules any session must keep), and a first commit. Project Framework phases apply: no code before the Definition gate. Commit after each completed step; ask before pushing.
