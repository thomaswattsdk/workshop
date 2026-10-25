#!/usr/bin/env python3
"""Tests for workshop-edit-guard.py. Run: python3 -I test_workshop_edit_guard.py   (standard library only).

Builds a throwaway workshop: a platform repository and one project repository, then asks the hook about files in each state.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "workshop-edit-guard.py")


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))


def put(path, text=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


class EditGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = os.path.realpath(cls.tmp.name)  # the stand-in workshop
        cls.proj = os.path.join(cls.root, "proj")
        sh(cls.root, "git", "init", "-q")
        sh(cls.root, "git", "config", "commit.gpgsign", "false")
        put(os.path.join(cls.root, "CLAUDE.md"), "rules\n")
        put(os.path.join(cls.root, "guardrails", "g.py"), "x\n")
        put(os.path.join(cls.root, ".gitignore"), "/*\n!/.gitignore\n!/CLAUDE.md\n!/guardrails/\n")
        sh(cls.root, "git", "add", ".gitignore", "CLAUDE.md", "guardrails")
        sh(cls.root, "git", "commit", "-q", "-m", "platform")
        os.makedirs(cls.proj)
        sh(cls.proj, "git", "init", "-q")
        sh(cls.proj, "git", "config", "commit.gpgsign", "false")
        put(os.path.join(cls.proj, "a.md"), "clean\n")
        put(os.path.join(cls.proj, "b.md"), "will change\n")
        put(os.path.join(cls.proj, "item.md"), "---\ntype: work-item\nid: wi-1\n---\nbody\n")
        put(os.path.join(cls.proj, ".gitignore"), "ignored/\n")
        sh(cls.proj, "git", "add", ".")
        sh(cls.proj, "git", "commit", "-q", "-m", "project")
        put(os.path.join(cls.proj, "b.md"), "changed after the commit\n")
        put(os.path.join(cls.proj, "untracked.md"), "not in git\n")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ask(self, path, tool="Edit", cwd=None):
        payload = {"tool_name": tool, "cwd": cwd or self.proj, "tool_input": {"file_path": path}}
        out = subprocess.run([sys.executable, "-I", HOOK], input=json.dumps(payload), capture_output=True, text=True, timeout=20,
                             env=dict(os.environ, WORKSHOP_GUARD_ROOT=self.root, ZONE_LOG=os.devnull))
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] if out.stdout.strip() else "silent"

    def test_a_clean_tracked_file_may_be_edited(self):
        self.assertEqual(self.ask(os.path.join(self.proj, "a.md")), "allow")
        self.assertEqual(self.ask(os.path.join(self.proj, "a.md"), "Write"), "allow")

    def test_a_file_with_uncommitted_changes_asks(self):
        self.assertEqual(self.ask(os.path.join(self.proj, "b.md")), "ask")

    def test_an_untracked_file_asks(self):
        self.assertEqual(self.ask(os.path.join(self.proj, "untracked.md")), "ask")

    def test_a_new_file_in_a_repository_is_allowed_unless_git_ignores_it(self):
        self.assertEqual(self.ask(os.path.join(self.proj, "docs", "new.md"), "Write"), "allow")
        self.assertEqual(self.ask(os.path.join(self.proj, "ignored", "x.md"), "Write"), "ask")

    def test_files_outside_the_workshop_repositories_ask(self):
        self.assertEqual(self.ask("/etc/hosts"), "ask")
        self.assertEqual(self.ask("/home/thomas/claude-os/CLAUDE.md"), "ask")
        self.assertEqual(self.ask("/mnt/d/x.md"), "ask")

    def test_the_files_that_govern_every_session_always_ask(self):
        self.assertEqual(self.ask(os.path.join(self.root, "CLAUDE.md"), cwd=self.root), "ask")
        self.assertEqual(self.ask(os.path.join(self.root, "guardrails", "g.py"), cwd=self.root), "ask")
        self.assertEqual(self.ask(os.path.join(self.proj, ".git", "config")), "ask")
        self.assertEqual(self.ask(os.path.join(self.proj, ".claude", "settings.json"), "Write"), "ask")

    def test_a_work_item_record_asks_even_when_clean(self):
        self.assertEqual(self.ask(os.path.join(self.proj, "item.md")), "ask")

    def test_the_scratch_folder_is_allowed(self):
        self.assertEqual(self.ask("/tmp/claude-1000/anything/scratch.txt", "Write"), "allow")

    def test_a_path_that_climbs_out_does_not_fool_it(self):
        self.assertEqual(self.ask(self.proj + "/.." * 20 + "/etc/hosts"), "ask")
    def test_other_tools_and_bad_input_are_ignored(self):
        self.assertEqual(self.ask(os.path.join(self.proj, "a.md"), "Read"), "silent")
        out = subprocess.run([sys.executable, "-I", HOOK], input="not json", capture_output=True, text=True)
        self.assertEqual((out.returncode, out.stdout), (0, ""))


class ZoneGuard(unittest.TestCase):
    """ADR-002: the knowledge zones in kDrive and the OS repository (layers of the Difference Engine)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = os.path.realpath(cls.tmp.name)
        cls.kd = os.path.join(base, "kdrive")
        cls.os_root = os.path.join(base, "claude-os")
        cls.log = os.path.join(base, "state", "zone-decisions.jsonl")
        cls.ci = os.path.join(cls.kd, "Knowledge base", "Code Intelligence.md")
        put(cls.ci, "line1\nline2\n")
        put(os.path.join(cls.kd, "Knowledge base", "Finances", "payslip.pdf"), "pdf\n")
        put(os.path.join(cls.kd, "Knowledge base", "Project Framework", "framework.html"), "<html>\n")
        put(os.path.join(cls.kd, "Obsidian", "Watts Obsidian", "Inbox", "old.md"), "old\n")
        put(os.path.join(cls.kd, "Obsidian", "Watts Obsidian", "Areas", "note.md"), "note\n")
        put(os.path.join(cls.kd, "Claude outputs", "report.md"), "report\n")
        put(os.path.join(cls.kd, "Claude Cowork OS", "instructions.md"), "frozen\n")
        os.makedirs(cls.os_root)
        sh(cls.os_root, "git", "init", "-q")
        sh(cls.os_root, "git", "config", "commit.gpgsign", "false")
        for rel in ("CLAUDE.md", "instructions.md", "Memory.md", "Skills/s/SKILL.md", "Workshop/backlog.md", "Workshop/adr/a.md",
                    "Handovers/old.md"):
            put(os.path.join(cls.os_root, rel), "a\nb\n")
        sh(cls.os_root, "git", "add", ".")
        sh(cls.os_root, "git", "commit", "-q", "-m", "os")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def env(self, **extra):
        env = dict(os.environ, WORKSHOP_GUARD_ROOT=os.path.join(self.tmp.name, "workshop"), KDRIVE_GUARD_ROOT=self.kd,
                   OS_GUARD_ROOT=self.os_root, ZONE_LOG=self.log)
        env.update(extra)
        return env

    def ask(self, path, tool="Write", env=None, **tool_input):
        payload = {"tool_name": tool, "cwd": self.kd, "tool_input": dict(tool_input, file_path=path)}
        out = subprocess.run([sys.executable, "-I", HOOK], input=json.dumps(payload), capture_output=True, text=True, timeout=20,
                             env=env or self.env())
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] if out.stdout.strip() else "silent"

    def vault(self, *parts):
        return os.path.join(self.kd, "Obsidian", "Watts Obsidian", *parts)

    # New files only: records, the vault's Inbox, Claude's own output folders.
    def test_a_new_note_in_the_vault_inbox_is_allowed(self):
        self.assertEqual(self.ask(self.vault("Inbox", "new.md"), content="x\n"), "allow")

    def test_an_existing_vault_note_is_never_edited_without_asking(self):
        self.assertEqual(self.ask(self.vault("Inbox", "old.md"), "Edit", old_string="old", new_string="old more"), "ask")
        self.assertEqual(self.ask(self.vault("Areas", "note.md"), content="x"), "ask")

    def test_a_new_note_outside_the_inbox_asks(self):
        self.assertEqual(self.ask(self.vault("Areas", "new.md"), content="x"), "ask")

    def test_a_new_record_file_is_allowed_but_an_existing_one_is_never_overwritten(self):
        self.assertEqual(self.ask(os.path.join(self.kd, "Knowledge base", "Finances", "new.pdf"), content="x"), "allow")
        self.assertEqual(self.ask(os.path.join(self.kd, "Knowledge base", "Finances", "payslip.pdf"), content="x"), "ask")
        self.assertEqual(self.ask(os.path.join(self.kd, "Knowledge base", "Project Framework", "framework.html"), content="x"), "ask")

    def test_claude_output_folders_take_new_files_only(self):
        self.assertEqual(self.ask(os.path.join(self.kd, "Claude outputs", "new.md"), content="x"), "allow")
        self.assertEqual(self.ask(os.path.join(self.kd, "Claude outputs", "report.md"), content="x"), "ask")

    def test_the_frozen_cowork_copy_and_unlisted_kdrive_paths_ask(self):
        self.assertEqual(self.ask(os.path.join(self.kd, "Claude Cowork OS", "new.md"), content="x"), "ask")
        self.assertEqual(self.ask(os.path.join(self.kd, "Projects", "p", "new.md"), content="x"), "ask")
        self.assertEqual(self.ask(self.kd + "/.." * 30 + "/etc/outside.md", content="x"), "ask")

    # Living guides in the OS repository: additions only, git holds the file, nothing uncommitted.
    def mem(self):
        return os.path.join(self.os_root, "Memory.md")

    def test_adding_an_entry_to_a_living_guide_is_allowed(self):
        self.assertEqual(self.ask(self.mem(), "Edit", old_string="b\n", new_string="b\nnew entry\n"), "allow")
        self.assertEqual(self.ask(self.mem(), "Write", content="a\nb\nappended\n"), "allow")

    def test_revising_or_removing_existing_guide_text_asks(self):
        self.assertEqual(self.ask(self.mem(), "Edit", old_string="a", new_string="z"), "ask")
        self.assertEqual(self.ask(self.mem(), "Edit", old_string="a\n", new_string=""), "ask")
        self.assertEqual(self.ask(self.mem(), "Write", content="something else\n"), "ask")

    def test_a_multi_edit_is_allowed_only_if_every_edit_adds(self):
        add = {"old_string": "b\n", "new_string": "b\nmore\n"}
        revise = {"old_string": "a", "new_string": "X"}
        self.assertEqual(self.ask(self.mem(), "MultiEdit", edits=[add]), "allow")
        self.assertEqual(self.ask(self.mem(), "MultiEdit", edits=[add, revise]), "ask")

    def test_a_guide_with_uncommitted_changes_asks(self):
        original = open(self.mem()).read()
        try:
            put(self.mem(), original + "uncommitted\n")
            self.assertEqual(self.ask(self.mem(), "Edit", old_string="b\n", new_string="b\nx\n"), "ask")
        finally:
            put(self.mem(), original)

    def test_the_library_takes_no_edits_to_existing_files_not_even_additions(self):
        self.assertEqual(self.ask(self.ci, "Edit", old_string="line2\n", new_string="line2\nnew entry\n"), "ask")
        self.assertEqual(self.ask(self.ci, "Write", content="line1\nline2\nappended\n"), "ask")

    # The OS repository: hard rules and core guides ask; living guides take additions.
    def test_the_hard_rules_and_core_guides_in_the_os_repository_ask(self):
        for rel in ("CLAUDE.md", "instructions.md", "Workshop/adr/a.md"):
            self.assertEqual(self.ask(os.path.join(self.os_root, rel), "Edit", old_string="a\n", new_string="a\nmore\n"), "ask", rel)

    def test_living_guides_in_the_os_repository_take_additions_only(self):
        for rel in ("Memory.md", "Skills/s/SKILL.md", "Workshop/backlog.md"):
            path = os.path.join(self.os_root, rel)
            self.assertEqual(self.ask(path, "Edit", old_string="b\n", new_string="b\nadded\n"), "allow", rel)
            self.assertEqual(self.ask(path, "Edit", old_string="a\n", new_string="z\n"), "ask", rel)

    def test_a_new_handover_is_allowed_but_an_existing_one_asks(self):
        self.assertEqual(self.ask(os.path.join(self.os_root, "Handovers", "2026-10-25 new.md"), content="x"), "allow")
        self.assertEqual(self.ask(os.path.join(self.os_root, "Handovers", "old.md"), "Edit", old_string="a", new_string="a b"), "ask")

    # The log the Observer reads (Difference Engine, tenet 7).
    def test_every_zone_decision_is_logged_and_a_broken_log_changes_nothing(self):
        before = open(self.log).read().count("\n") if os.path.exists(self.log) else 0
        self.ask(self.vault("Inbox", "logged.md"), content="x")
        self.ask(self.vault("Areas", "note.md"), content="x")
        lines = [json.loads(line) for line in open(self.log).read().splitlines()][before:]
        self.assertEqual([entry["decision"] for entry in lines], ["allow", "ask"])
        self.assertTrue(all({"time", "path", "tool", "zone", "reason"} <= set(entry) for entry in lines))
        env = self.env(ZONE_LOG="/proc/no-such-place/log.jsonl")
        self.assertEqual(self.ask(self.vault("Inbox", "logged2.md"), env=env, content="x"), "allow")

    def test_paths_in_no_zone_are_not_logged(self):
        before = open(self.log).read() if os.path.exists(self.log) else ""
        self.ask("/etc/hosts", "Edit", old_string="a", new_string="b")
        after = open(self.log).read() if os.path.exists(self.log) else ""
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
