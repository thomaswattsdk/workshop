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
                             env=dict(os.environ, WORKSHOP_GUARD_ROOT=self.root))
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
