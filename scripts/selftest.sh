#!/usr/bin/env bash
# End-to-end self test: run the whole pipeline over both shipped samples and
# assert that every gate passes. Use it after installing the skill, after
# changing a renderer, and in CI.
#
#   scripts/selftest.sh
#
# Exit 0 = everything passed. Exit 1 = something regressed, with the failing
# step named.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0

step() {
  local name="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    printf '  \033[32m✓\033[0m %s\n' "$name"
    PASS=$((PASS + 1))
  else
    printf '  \033[31m✗\033[0m %s\n' "$name"
    printf '%s\n' "$out" | sed 's/^/      /'
    FAIL=$((FAIL + 1))
  fi
}

# A gate that is expected to fail — proves the check actually catches things.
step_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '  \033[31m✗\033[0m %s (gate did not fire)\n' "$name"
    FAIL=$((FAIL + 1))
  else
    printf '  \033[32m✓\033[0m %s\n' "$name"
    PASS=$((PASS + 1))
  fi
}

echo "crosspost-design self test"
echo "  root: $ROOT"
echo

echo "syntax"
for f in "$ROOT"/scripts/*.py "$ROOT"/docs/*.py; do
  [ -e "$f" ] || continue
  step "compiles $(basename "$f")" python3 -m py_compile "$f"
done

echo
echo "manifests"
step "plugin.json is valid JSON" python3 -c \
  "import json;json.load(open('$ROOT/.claude-plugin/plugin.json'))"
step "marketplace.json is valid JSON" python3 -c \
  "import json;json.load(open('$ROOT/.claude-plugin/marketplace.json'))"
step "SKILL.md has name + description" python3 -c "
import re,sys
t=open('$ROOT/SKILL.md',encoding='utf-8').read()
assert t.startswith('---'), 'no front matter'
head=t.split('---')[1]
for k in ('name:','description:'):
    assert k in head, 'missing '+k
"

echo
echo "pipeline"
for lang in ru en; do
  SRC="$ROOT/assets/sample-article.$lang.md"
  OUT="$WORK/$lang"
  step "[$lang] source_lint"      python3 "$ROOT/scripts/source_lint.py" "$SRC"
  step "[$lang] typography_lint"  python3 "$ROOT/scripts/typography_lint.py" "$SRC"
  step "[$lang] build_targets"    python3 "$ROOT/scripts/build_targets.py" "$SRC" -o "$OUT"
  step "[$lang] validate_post"    python3 "$ROOT/scripts/validate_post.py" --auto "$OUT/"'*'
  step "[$lang] report exists"    test -s "$(echo "$OUT"/*.report.md)"
done

echo
echo "gates actually fire"
BAD="$WORK/bad.vk.html"
printf '<div class="x" style="color:red"><table><tr><td>a</td></tr></table></div>' > "$BAD"
step_expect_fail "validate_post rejects forbidden VK markup" \
  python3 "$ROOT/scripts/validate_post.py" --platform vk "$BAD"

BADSRC="$WORK/bad.md"
printf -- '---\nlang: ru\n---\n\n:::tldr\n- x\n\ntext[^1]\n' > "$BADSRC"
step_expect_fail "source_lint rejects unbalanced ::: and missing footnote" \
  python3 "$ROOT/scripts/source_lint.py" "$BADSRC"

TYPO="$WORK/typo.md"
printf -- '---\nlang: ru\n---\n\n"текст" - и 5-7 дней...\n' > "$TYPO"
step_expect_fail "typography_lint flags straight quotes and hyphen dashes" \
  python3 "$ROOT/scripts/typography_lint.py" "$TYPO"

echo
if [ "$FAIL" -eq 0 ]; then
  printf '\033[32m✓ %d checks passed\033[0m\n' "$PASS"
  exit 0
fi
printf '\033[31m✗ %d of %d checks failed\033[0m\n' "$FAIL" "$((PASS + FAIL))"
exit 1
