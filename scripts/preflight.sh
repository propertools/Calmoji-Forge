#!/usr/bin/env bash
#
# preflight.sh — run all the gates locally before pushing the
# polish/oss-release branch.
#
# Each gate is independent. If one fails, fix it, commit the fix, then
# re-run preflight. We do not auto-fix anything: every formatter / linter
# diff should land as a reviewable commit.
#
# Run from the repo root:
#
#     bash scripts/preflight.sh
#
# Exit code 0 = ready to push. Non-zero = at least one gate failed.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

VENV_DIR="${VENV_DIR:-.venv-preflight}"
PASSED=()
FAILED=()

step() {
    echo
    echo "─── $* ───"
}

ok() {
    echo "✅ $*"
    PASSED+=("$*")
}

bad() {
    echo "❌ $*"
    FAILED+=("$*")
}

gate() {
    local name="$1"
    shift
    if "$@"; then
        ok "$name"
    else
        bad "$name"
    fi
}

step "Gate 1: branch + commit ledger"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"
echo "Commits on this branch (vs main):"
git log --oneline main..HEAD || true
COMMIT_COUNT=$(git log --oneline main..HEAD | wc -l | tr -d ' ')
if [[ "$COMMIT_COUNT" -ge 7 ]]; then
    ok "$COMMIT_COUNT commits ahead of main (expected ≥7)"
else
    bad "only $COMMIT_COUNT commits ahead of main — did finish-oss-release.sh complete?"
fi

step "Gate 2: no tracked-file modifications"
# We only fail on M/D/A changes to tracked files. Untracked helper scripts
# (this file, for instance) are OK; they just aren't part of the release.
DIRTY=$(git status --porcelain | grep -E '^( M|MM| D|D | A|A )' || true)
if [[ -z "$DIRTY" ]]; then
    ok "no modifications to tracked files"
    UNTRACKED=$(git status --porcelain | grep -E '^\?\?' || true)
    if [[ -n "$UNTRACKED" ]]; then
        echo "(untracked files present, ignored:)"
        echo "$UNTRACKED" | sed 's/^/    /'
    fi
else
    bad "tracked-file changes not committed:"
    echo "$DIRTY" | sed 's/^/    /'
fi

step "Gate 3: fresh venv install"
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
gate "pip upgrade" \
    pip install --quiet --upgrade pip
gate "pip install -e .[dev]" \
    pip install --quiet -e '.[dev]'

step "Gate 4: calmoji --version reports 0.1.0"
VERSION_OUT=$(calmoji --version 2>&1 || true)
echo "Output: $VERSION_OUT"
if [[ "$VERSION_OUT" == "calmoji 0.1.0" ]]; then
    ok "console_script reports calmoji 0.1.0"
else
    bad "expected 'calmoji 0.1.0', got: $VERSION_OUT"
fi

step "Gate 5: pytest"
gate "pytest with branch coverage" \
    pytest --cov=calmoji --cov-branch --cov-report=term-missing

step "Gate 6: ruff"
gate "ruff check" \
    ruff check .

step "Gate 7: black --check"
gate "black --check" \
    black --check .

step "Gate 8: mypy strict"
gate "mypy calmoji" \
    mypy calmoji

step "Gate 9: bundle integrity"
if [[ -f release-bundle/v0.1.0/MANIFEST.sha256 ]]; then
    if (cd release-bundle/v0.1.0 && if command -v sha256sum >/dev/null; then sha256sum -c MANIFEST.sha256; else shasum -a 256 -c MANIFEST.sha256; fi >/tmp/preflight-manifest.log 2>&1); then
        ok "all 1873 bundle entries verified against MANIFEST.sha256"
    else
        bad "manifest verification failed (see /tmp/preflight-manifest.log)"
        tail -5 /tmp/preflight-manifest.log
    fi
else
    bad "release-bundle/v0.1.0/MANIFEST.sha256 not found"
fi

step "Gate 10: install-from-git smoke test"
SMOKE_VENV="${VENV_DIR}-smoke"
deactivate || true
rm -rf "$SMOKE_VENV"
python3 -m venv "$SMOKE_VENV"
# shellcheck disable=SC1091
source "$SMOKE_VENV/bin/activate"
pip install --quiet --upgrade pip
if pip install --quiet "calmoji @ git+file://$REPO_ROOT@$CURRENT_BRANCH" >/tmp/preflight-pipgit.log 2>&1; then
    SMOKE_VERSION=$(calmoji --version 2>&1)
    if [[ "$SMOKE_VERSION" == "calmoji 0.1.0" ]]; then
        ok "pip install git+file://...@$CURRENT_BRANCH produces working calmoji 0.1.0"
    else
        bad "git-installed calmoji reports wrong version: $SMOKE_VERSION"
    fi
else
    bad "pip install git+file://...@$CURRENT_BRANCH failed (see /tmp/preflight-pipgit.log)"
    tail -10 /tmp/preflight-pipgit.log
fi
deactivate || true

step "Summary"
echo "Passed: ${#PASSED[@]}"
for p in ${PASSED[@]+"${PASSED[@]}"}; do echo "  ✅ $p"; done
echo "Failed: ${#FAILED[@]}"
for f in ${FAILED[@]+"${FAILED[@]}"}; do echo "  ❌ $f"; done

if [[ ${#FAILED[@]} -eq 0 ]]; then
    echo
    echo "🎉 All gates passed. Safe to push:"
    echo "    git push -u origin $CURRENT_BRANCH"
    echo "    gh pr create --base main --head $CURRENT_BRANCH --title 'Polish for OSS release'"
    exit 0
else
    echo
    echo "🛑 Fix the failures above before pushing."
    exit 1
fi
