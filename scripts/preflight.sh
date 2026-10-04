#!/usr/bin/env bash
#
# preflight.sh — run all the gates locally before pushing a branch.
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
if [[ "$CURRENT_BRANCH" == "main" ]]; then
    ok "on main (release check)"
elif [[ "$COMMIT_COUNT" -ge 1 ]]; then
    ok "$COMMIT_COUNT commits ahead of main"
else
    bad "no commits ahead of main — are you on the branch you meant to check?"
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

# The expected version is whatever pyproject.toml says: the first top-level
# `version = "..."` line, which is the one under [project].
EXPECTED_VERSION=$(sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' pyproject.toml | head -n 1)

step "Gate 4: calmoji --version matches pyproject.toml (${EXPECTED_VERSION:-unreadable})"
VERSION_OUT=$(calmoji --version 2>&1 || true)
echo "Output: $VERSION_OUT"
if [[ -z "$EXPECTED_VERSION" ]]; then
    bad "could not read the version from pyproject.toml"
elif [[ "$VERSION_OUT" == "calmoji $EXPECTED_VERSION" ]]; then
    ok "console_script reports calmoji $EXPECTED_VERSION"
else
    bad "expected 'calmoji $EXPECTED_VERSION', got: $VERSION_OUT"
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

step "Gate 9: release bundle is reproducible"
# Build the bundle twice, for two years only (the release itself builds
# 2026-2036), into two temporary directories. The archives must match byte
# for byte, and the manifest must verify.
verify_manifest() {
    # Run from inside the bundle folder, as the bundle's own README tells users to.
    local dir="$1"
    if command -v shasum >/dev/null 2>&1; then
        (cd "$dir" && shasum -a 256 -c MANIFEST.sha256)
    elif command -v sha256sum >/dev/null 2>&1; then
        (cd "$dir" && sha256sum -c MANIFEST.sha256)
    else
        echo "neither shasum nor sha256sum is installed"
        return 1
    fi
}

BUNDLE_TMP_BASE="${TMPDIR:-/tmp}"
BUNDLE_TMP=$(mktemp -d "${BUNDLE_TMP_BASE%/}/calmoji-preflight-bundle.XXXXXX")
BUNDLE_YEARS="2026-2027"
BUNDLE_ZIP="calmoji-artifacts-v${EXPECTED_VERSION}.zip"
BUNDLE_TAR="calmoji-artifacts-v${EXPECTED_VERSION}.tar.gz"

if python3 scripts/build_bundle.py --out "$BUNDLE_TMP/a" --years "$BUNDLE_YEARS" >"$BUNDLE_TMP/build-a.log" 2>&1 \
    && python3 scripts/build_bundle.py --out "$BUNDLE_TMP/b" --years "$BUNDLE_YEARS" >"$BUNDLE_TMP/build-b.log" 2>&1; then
    ok "build_bundle.py built $BUNDLE_YEARS twice"

    if cmp "$BUNDLE_TMP/a/$BUNDLE_ZIP" "$BUNDLE_TMP/b/$BUNDLE_ZIP" \
        && cmp "$BUNDLE_TMP/a/$BUNDLE_TAR" "$BUNDLE_TMP/b/$BUNDLE_TAR"; then
        ok "zip and tar.gz are byte-identical across the two builds"
    else
        bad "archives differ between two builds of the same bundle"
    fi

    MANIFEST_ENTRIES=$(wc -l <"$BUNDLE_TMP/a/v${EXPECTED_VERSION}/MANIFEST.sha256" | tr -d ' ')
    if verify_manifest "$BUNDLE_TMP/a/v${EXPECTED_VERSION}" >"$BUNDLE_TMP/verify.log" 2>&1; then
        VERIFIED=$(grep -c ': OK$' "$BUNDLE_TMP/verify.log" || true)
        if [[ "$MANIFEST_ENTRIES" -gt 0 && "$VERIFIED" -eq "$MANIFEST_ENTRIES" ]]; then
            ok "all $VERIFIED manifest entries verified"
        else
            bad "manifest check passed but verified $VERIFIED of $MANIFEST_ENTRIES entries"
        fi
    else
        bad "manifest verification failed"
        grep -v ': OK$' "$BUNDLE_TMP/verify.log" | head -10
    fi
else
    bad "build_bundle.py failed"
    tail -10 "$BUNDLE_TMP/build-a.log" "$BUNDLE_TMP/build-b.log" 2>/dev/null
fi
rm -rf "$BUNDLE_TMP"

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
    if [[ "$SMOKE_VERSION" == "calmoji $EXPECTED_VERSION" ]]; then
        ok "pip install git+file://...@$CURRENT_BRANCH produces working calmoji $EXPECTED_VERSION"
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
    if [[ "$CURRENT_BRANCH" == "main" ]]; then
        echo "🎉 All gates passed on main. To release, tag it, push the tag, build the archives:"
        echo "    git tag vX.Y.Z"
        echo "    git push origin vX.Y.Z"
        echo "    python3 scripts/build_bundle.py --out dist"
    else
        echo "🎉 All gates passed. Safe to push:"
        echo "    git push -u origin $CURRENT_BRANCH"
        echo "    gh pr create --base main --head $CURRENT_BRANCH --fill"
    fi
    exit 0
else
    echo
    echo "🛑 Fix the failures above before pushing."
    exit 1
fi
