#!/usr/bin/env bash
# Report whether the installed guardrails in /etc/claude-code match the source in this folder. Needs no sudo.
src="$(cd "$(dirname "$0")" && pwd)"
dst=/etc/claude-code
status=0
for f in workshop-guard.py workshop-edit-guard.py workshop-push workshop-projects managed-settings.json; do
  if [ ! -e "$dst/$f" ]; then echo "MISSING   $f"; status=1
  elif cmp -s "$src/$f" "$dst/$f"; then echo "identical $f"
  else echo "DIFFERS   $f"; status=1; fi
done
exit $status
