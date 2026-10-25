#!/usr/bin/env python3
"""Tests for workshop-projects: what it lists, in what order, and that it changes nothing.
Run: python3 -I test_workshop_projects.py   (standard library only).
"""
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workshop-projects")


def run(root):
    out = subprocess.run([sys.executable, "-I", SCRIPT, root], capture_output=True, text=True, timeout=30)
    return out.returncode, out.stdout


def make_project(root, name, when, claude="", handovers=()):
    path = os.path.join(root, name)
    os.makedirs(os.path.join(path, "docs"))
    env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    subprocess.run(["git", "init", "-q", path], check=True)
    with open(os.path.join(path, "CLAUDE.md"), "w", encoding="utf-8") as f:
        f.write(claude)
    for fname, body in handovers:
        with open(os.path.join(path, "docs", fname), "w", encoding="utf-8") as f:
            f.write(body)
    subprocess.run(["git", "-C", path, "add", "-A"], check=True)
    subprocess.run(["git", "-C", path, "commit", "-q", "-m", "x"], check=True, env=env)


def snapshot(root):
    seen = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for fname in files:
            p = os.path.join(base, fname)
            with open(p, "rb") as f:
                seen[p] = (os.path.getmtime(p), f.read())
    return seen


class Projects(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        make_project(self.root, "older", "2026-01-01T10:00:00", "# Older\n- **Phase:** Discovery.\n")
        make_project(self.root, "newer", "2026-02-01T10:00:00", "# Newer\n- **Phase:** Development.\n", [
            ("HANDOVER-2026-01-01-a.md", "---\nstatus: consumed\n---\n\n> Old opening.\n"),
            ("HANDOVER-2026-02-01-b.md", "---\nstatus: open\n---\n\n# Title\n\n> **Where we are.** Newest opening.\n"),
        ])
        os.makedirs(os.path.join(self.root, "not-a-project"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_most_recently_committed_first_and_only_repositories(self):
        code, out = run(self.root)
        self.assertEqual(code, 0)
        self.assertLess(out.index("== newer"), out.index("== older"))
        self.assertNotIn("not-a-project", out)

    def test_phase_and_the_newest_handovers_opening(self):
        _, out = run(self.root)
        self.assertIn("phase: Phase: Development.", out)
        self.assertIn("HANDOVER-2026-02-01-b.md [open]", out)
        self.assertIn("Newest opening.", out)
        self.assertNotIn("Old opening", out)

    def test_a_project_without_a_handover_or_phase_says_so(self):
        _, out = run(self.root)
        self.assertIn("handover: none", out)
        make_project(self.root, "bare", "2026-03-01T10:00:00", "# Bare\n")
        _, out = run(self.root)
        self.assertIn("not stated in CLAUDE.md", out)

    def test_nothing_is_changed(self):
        before = snapshot(self.root)
        run(self.root)
        self.assertEqual(before, snapshot(self.root))

    def test_an_empty_workshop_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as empty:
            code, out = run(empty)
            self.assertEqual(code, 0)
            self.assertIn("Nothing here right now", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
