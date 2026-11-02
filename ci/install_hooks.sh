#!/bin/bash
# Enable the repository's git hooks for this checkout.
#
# Git does not version hooks: it reads them from core.hooksPath or .git/hooks
# only. The scripts live in ci/hooks so they can be reviewed and diffed like
# any other code, and this points git at that directory. Idempotent, so it can
# be re-run safely after a pull.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! git -C "$ROOT" rev-parse --git-dir > /dev/null 2>&1; then
  echo "install_hooks: $ROOT is not a git checkout" >&2
  exit 1
fi

cd "$ROOT"

current=$(git config --get core.hooksPath || true)
if [ "$current" = "ci/hooks" ]; then
  echo "install_hooks: already enabled (core.hooksPath=ci/hooks)"
  exit 0
fi
if [ -n "$current" ]; then
  echo "install_hooks: replacing core.hooksPath '$current' with 'ci/hooks'"
fi

git config core.hooksPath ci/hooks
echo "install_hooks: pre-commit gate enabled (core.hooksPath=ci/hooks)"
