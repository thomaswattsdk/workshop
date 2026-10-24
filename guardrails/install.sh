#!/usr/bin/env bash
# Install the workshop guardrails into /etc/claude-code. Thomas runs this, with sudo: it changes machine-wide settings.
#   sudo bash /home/thomas/workshop/guardrails/install.sh
# It runs the tests first and stops if any fail. It backs up each installed file that differs, copies the scripts, and
# installs the settings last, so the settings never name a script that is not there yet. Nothing is deleted.
set -euo pipefail

src="$(cd "$(dirname "$0")" && pwd)"
dst=/etc/claude-code
stamp="$(date +%Y-%m-%d-%H%M)"

echo "Running the tests ..."
python3 -I "$src/test_workshop_guard.py" > /dev/null
python3 -I "$src/test_workshop_edit_guard.py" > /dev/null
echo "Tests pass."

mkdir -p "$dst"
for f in workshop-guard.py workshop-edit-guard.py workshop-push managed-settings.json; do
  if [ -e "$dst/$f" ] && ! cmp -s "$src/$f" "$dst/$f"; then
    cp -p "$dst/$f" "$dst/$f.bak-$stamp"
    echo "Backed up $f as $f.bak-$stamp"
  fi
done

install -m 755 "$src/workshop-guard.py" "$dst/workshop-guard.py"
install -m 755 "$src/workshop-edit-guard.py" "$dst/workshop-edit-guard.py"
install -m 755 "$src/workshop-push" "$dst/workshop-push"
install -m 644 "$src/managed-settings.json" "$dst/managed-settings.json"
echo "Installed. Start a new session for the settings to load."
bash "$src/verify-install.sh"
