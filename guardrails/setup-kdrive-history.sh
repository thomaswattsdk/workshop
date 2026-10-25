#!/usr/bin/env bash
# One-time setup (ADR-002): the history store for the Knowledge base's living guides, kept in WSL and outside the folder
# kDrive watches. Thomas runs this; it only READS kDrive and creates one git directory under ~/.local/share/workshop.
# It never overwrites: if the store exists it says so and changes nothing.
#   bash /home/thomas/workshop/guardrails/setup-kdrive-history.sh
set -euo pipefail

H="${KDRIVE_GUARD_HISTORY:-$HOME/.local/share/workshop/kdrive-history.git}"
KD="${KDRIVE_GUARD_ROOT:-/mnt/d/Claude CoWork}"

if [ -e "$H" ]; then
  echo "Already exists: $H (nothing changed)"
  exit 0
fi

mkdir -p "$(dirname "$H")"
git init -q --bare "$H"
g() { git --git-dir="$H" --work-tree="$KD" "$@"; }
g config core.fileMode false
g config core.autocrlf false
g config commit.gpgsign false
g config user.name "Workshop history"
g config user.email "history@localhost"
g add "Knowledge base/Code Intelligence.md"
g commit -q -m "Baseline: Code Intelligence"
echo "Created $H"
g log --oneline
