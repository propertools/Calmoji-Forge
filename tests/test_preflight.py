# tests/test_preflight.py
"""scripts/preflight.sh: the closing hint suggests the right next step for the branch it ran on."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "scripts" / "preflight.sh").read_text(encoding="utf-8")


def closing_output(branch: str, failed: bool = False) -> str:
    """Run only the script's summary section, as if every gate had (or hadn't) passed."""
    summary = SCRIPT[SCRIPT.index('step "Summary"') :]
    harness = (
        "set -uo pipefail\n"
        'step() { echo "─── $* ───"; }\n'
        "PASSED=(gate-a gate-b)\n"
        f"FAILED=({'gate-c' if failed else ''})\n"
        f"CURRENT_BRANCH={branch}\n" + summary
    )
    done = subprocess.run(["bash", "-c", harness], capture_output=True, text=True)
    assert done.returncode == (1 if failed else 0), done.stderr
    return done.stdout


def test_on_main_it_suggests_the_release_steps_not_a_pull_request():
    out = closing_output("main")
    assert "git tag vX.Y.Z" in out
    assert "git push origin vX.Y.Z" in out
    assert "python3 scripts/build_bundle.py --out dist" in out
    assert "gh pr create" not in out
    assert "--head main" not in out
    assert out.index("git tag") < out.index("git push origin vX.Y.Z") < out.index("build_bundle.py")


@pytest.mark.parametrize("branch", ["fix/v0.1.2", "feat/x"])
def test_on_any_other_branch_it_suggests_pushing_and_a_pull_request(branch):
    out = closing_output(branch)
    assert f"git push -u origin {branch}" in out
    assert f"gh pr create --base main --head {branch} --fill" in out
    assert "git tag" not in out


def test_a_failure_suggests_neither():
    out = closing_output("main", failed=True)
    assert "Fix the failures above" in out
    assert "git tag" not in out and "gh pr create" not in out
