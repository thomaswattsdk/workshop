#!/usr/bin/env python3
"""Tests for workshop-push: what it refuses. Run: python3 -I test_workshop_push.py   (standard library only).

It never reaches GitHub here: every case is one the script must stop before it sends anything. The one thing it does
for real (a push) is exercised by using it.
"""
import os
import subprocess
import sys
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workshop-push")


def run(*args):
    out = subprocess.run([sys.executable, "-I", SCRIPT] + list(args), capture_output=True, text=True, timeout=20)
    return out.returncode, out.stderr


class Push(unittest.TestCase):
    def test_it_wants_exactly_one_plain_name(self):
        for args in ([], ["a", "b"], [""], ["../etc"], ["a/b"], [".hidden"], ["-x"], ["a;b"], ["$(x)"]):
            code, err = run(*args)
            self.assertEqual(code, 2, args)
            self.assertIn("usage", err, args)

    def test_a_name_that_is_not_a_project_is_refused(self):
        for name in ("no-such-project", "guardrails", "archive", "docs", "Misc"):
            code, err = run(name)
            self.assertEqual(code, 2, name)
            self.assertIn("not a workshop project", err, name)

    def test_nothing_is_sent_by_a_refusal(self):
        code, err = run("../..")
        self.assertEqual(code, 2)
        self.assertNotIn("Writing objects", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
