#!/usr/bin/env bash
# Run every check the workshop has, from one place: tests, type checks, dependency audit, a secret scan, the guardrail tests.
#   bash /home/thomas/workshop/tools/check-all.sh            everything
#   bash /home/thomas/workshop/tools/check-all.sh --quick    skip the browser tests and the audit (they need a browser and the network)
# Prints one line per check and the last lines of any that fail. Exit code 0 only if everything passed.
# Needs no network for --quick. Writes nothing but a temporary log.
set -u
W="$(cd "$(dirname "$0")/.." && pwd)"
quick=0
[ "${1:-}" = "--quick" ] && quick=1
fail=0
log="${TMPDIR:-/tmp}/workshop-check-$$.log"

run() { # run <name> <folder under the workshop> <command...>
  local name="$1" dir="$2"
  shift 2
  if (cd "$W/$dir" && "$@" > "$log" 2>&1); then
    printf '  ok    %s\n' "$name"
  else
    printf '  FAIL  %s\n' "$name"
    tail -12 "$log" | sed 's/^/          /'
    fail=1
  fi
}

TSC_CORE="node node_modules/typescript/bin/tsc"
SECRETS='sk-ant-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|xox[baprs]-[A-Za-z0-9-]{10,}'

echo "Tests and type checks"
run "work-ecosystem-core: tests"        work-ecosystem-core node --test core/*.test.ts
run "work-ecosystem-core: type check"   work-ecosystem-core $TSC_CORE -p core/tsconfig.json
run "workbench: tests"                  workbench           node --test core/*.test.ts
run "workbench: type check"             workbench           node ../work-ecosystem-core/node_modules/typescript/bin/tsc -p tsconfig.check.json --noEmit
run "work-ecosystem server: tests"      work-ecosystem/server node --test *.test.ts
run "work-ecosystem server: type check" work-ecosystem/server $TSC_CORE -p tsconfig.json
run "visual-grill-board: tests"         visual-grill-board  node --test "tests/**/*.test.mjs"
if [ "$quick" = 0 ]; then
  run "work-ecosystem: browser tests"   work-ecosystem      node --test --test-concurrency=1 tests/*.test.ts
fi

echo "Formatting (Prettier)"
run "work-ecosystem-core: format"       work-ecosystem-core   node node_modules/prettier/bin/prettier.cjs --check "core/*.ts"
run "work-ecosystem: format"            work-ecosystem/server node node_modules/prettier/bin/prettier.cjs --check "*.ts" "../tests/*.ts" "../web/js/*.js"
run "visual-grill-board: format"        visual-grill-board    npm run --silent format:check

echo "Guardrails"
run "guardrails: shell guard tests"     guardrails python3 -I test_workshop_guard.py
run "guardrails: edit guard tests"      guardrails python3 -I test_workshop_edit_guard.py
run "guardrails: push script tests"     guardrails python3 -I test_workshop_push.py

echo "Secret scan (tracked files)"
for r in workbench work-ecosystem work-ecosystem-core retro visual-grill-board hello-app grill-copies; do
  if git -C "$W/$r" grep -IlE "$SECRETS" > "$log" 2>&1; then
    printf '  FAIL  %s: a key-shaped string is tracked\n' "$r"; sed 's/^/          /' "$log"; fail=1
  else
    printf '  ok    %s\n' "$r"
  fi
done

if [ "$quick" = 0 ]; then
  echo "Dependency audit"
  for d in work-ecosystem-core visual-grill-board work-ecosystem/server; do
    run "$d: npm audit" "$d" npm audit --audit-level=high
  done
fi

echo
[ "$fail" = 0 ] && echo "All checks passed." || echo "Some checks failed."
exit "$fail"
