#!/usr/bin/env python3
"""Tests for workshop-guard.py: what it must refuse, and what it must leave alone.

Run: python3 -I test_workshop_guard.py        (standard library only; creates two throwaway git repositories)

The guard is a tripwire for three things (see its header): deletes that reach outside the workshop or hide in a
roundabout form, Docker given too much, and a push that is not a plain push to GitHub. These tests pin both sides:
every refusal that protects, and every harmless command that used to be refused only because its text contained a
watched word (searching for the word, echoing it, a commit message that mentions it).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "workshop-guard.py")
WORKSHOP = "/home/thomas/workshop"
SCRIPT = "/etc/claude-code/workshop-push"


def git(path, *args):
    subprocess.run(["git", "-C", path] + list(args), check=True, capture_output=True)


class Guard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.good = os.path.join(cls.tmp.name, "good")
        cls.evil = os.path.join(cls.tmp.name, "evil")
        for path, url in ((cls.good, "https://github.com/thomaswattsdk/x.git"), (cls.evil, "https://example.com/a/b.git")):
            os.makedirs(path)
            git(path, "init", "-q")
            git(path, "remote", "add", "origin", url)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def verdict(self, command, cwd=None):
        payload = {"tool_name": "Bash", "cwd": cwd or WORKSHOP, "tool_input": {"command": command}}
        out = subprocess.run([sys.executable, "-I", GUARD], input=json.dumps(payload), capture_output=True, text=True, timeout=20)
        self.assertEqual(out.returncode, 0, out.stderr)
        if not out.stdout.strip():
            return "allow"
        return "deny" if json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny" else "other"

    def refused(self, command, cwd=None):
        self.assertEqual(self.verdict(command, cwd), "deny", command)

    def left_alone(self, command, cwd=None):
        self.assertEqual(self.verdict(command, cwd), "allow", command)

    # ---- what must stay refused -------------------------------------------------------------------------------
    def test_push_must_stand_alone(self):
        self.refused("cd /home/thomas/workshop/x && git push", self.good)
        self.refused("git push; ls", self.good)
        self.refused("git -c core.sshCommand=evil push", self.good)
        self.refused("git push origin main > /tmp/out", self.good)
        self.refused("git push --repo=https://github.com/a/b", self.good)

    def test_push_only_to_github(self):
        self.refused("git push", self.evil)
        self.refused("git push https://example.com/a/b.git", self.good)

    def test_a_plain_push_to_github_passes_the_guard(self):
        self.left_alone("git push", self.good)
        self.left_alone("git push origin main", self.good)

    def test_the_push_script_stands_alone_with_one_plain_name(self):
        self.left_alone(SCRIPT + " claude-os")
        self.refused(SCRIPT + " claude-os && ls")
        self.refused(SCRIPT + " ../etc")
        self.refused(SCRIPT + " retro hello-app")
        self.refused("cd /tmp && " + SCRIPT + " retro")
        self.refused(SCRIPT)

    def test_roundabout_deletes_are_refused(self):
        self.refused("find . -name x -delete")
        self.refused("grep -rl foo . | xargs rm")
        self.refused("find . -exec rm {} +")
        self.refused('bash -c "rm /tmp/x"')
        self.refused("python3 -c \"import os; os.remove('/tmp/x')\"")
        self.refused("git clean -fdx")
        self.refused("powershell.exe -c Get-Date")

    def test_deletes_outside_the_workshop_are_refused(self):
        self.refused("rm /etc/hosts")
        self.refused("rm -r /home/thomas/.claude")
        self.refused("rm /mnt/d/x")
        self.refused("mv a /mnt/d/")
        self.refused("sudo ls")

    def test_docker_is_not_given_the_machine(self):
        self.refused("docker run -v /:/host alpine")
        self.refused("docker run --privileged alpine")
        self.refused("docker run -v /mnt/d:/d alpine")

    def test_a_substitution_hides_nothing(self):
        self.refused('grep "$(rm -rf /home/thomas/x)" file')
        self.refused('echo `find . -delete`')

    def test_text_fed_to_a_shell_still_counts(self):
        self.refused("cat <<'EOF' | bash\nrm -rf /home/thomas/x\nEOF")
        self.refused("cat > /tmp/s.sh <<'EOF'\nrm -rf /home/thomas/x\nEOF")

    def test_masking_a_read_only_command_does_not_hide_its_neighbours(self):
        self.refused("echo hi; rm /etc/hosts")
        self.refused('grep -rn "x" core && find . -delete')
        self.refused('echo "a;b" | xargs rm')
        self.refused("echo $(find . -delete)")

    # ---- what must be left alone (these used to be refused only for the words they contain) -------------------
    def test_searching_for_a_watched_word_is_harmless(self):
        self.left_alone('grep -rn "unlink" core')
        self.left_alone('grep -rn "os.remove" .')
        self.left_alone("grep -rn 'git push' docs")
        self.left_alone('grep -rn "rm -rf" docs | head -5')

    def test_printing_a_watched_word_is_harmless(self):
        self.left_alone('echo "rm -rf x"')
        self.left_alone("echo 'git push origin main'")
        self.left_alone("printf '%s' \"bash -c 'rm x'\"")

    def test_a_message_that_mentions_a_watched_word_is_harmless(self):
        self.left_alone("cat <<'EOF'\nthe notes say: git push, rm -rf, find -delete\nEOF")
        self.left_alone("git commit -m \"$(cat <<'EOF'\nNotes: mention git push and rm in the text\nEOF\n)\"")

    def test_ordinary_commands_pass(self):
        for c in ("ls /tmp", "ls /mnt/d", "git log --oneline", "git status", "node --test core/*.test.ts", "head -5 file"):
            self.left_alone(c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
