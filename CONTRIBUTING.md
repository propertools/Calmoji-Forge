# 🧿 Contributing to Calmoji

Welcome to **Calmoji** — a deterministic symbolic calendar engine built on:

* UTC-only time
* Exclusive-end phase semantics
* RFC 5545–compliant `.ics` generation
* Canonical EBI48 emoji mapping
* Full test coverage across core logic

Calmoji is not a toy scheduler.
It is a **time engine**.

If you are contributing, you are modifying a deterministic system.
Precision matters.

---

# 🛠 Contribution Philosophy

We value:

* Determinism over cleverness
* Explicitness over magic
* UTC over locale
* Tests before features
* Symbolic clarity without mysticism

Before opening a PR, ask:

> Does this preserve temporal invariance?

---

# 🔧 Roadmap: Near-Term Improvements

## 🎛 CLI & Configuration

The engine works. The CLI layer is evolving.

Planned:

* [ ] `--calendar-mode` (academic / gregorian)
* [ ] `--output-dir` override
* [ ] `--dry-run` enforcement tests
* [ ] `--version` flag (wired to package metadata)
* [ ] Optional config file (`calmoji.yml`)
* [ ] Combined vs per-phase export toggle

CLI changes must not alter core deterministic logic.

---

## 🧼 Code Quality & Structure

* [ ] Replace residual `print()` calls with structured logging
* [ ] Add docstrings to all public APIs
* [ ] Ensure full type coverage (strict `mypy`)
* [ ] Confirm no hidden local-time usage
* [ ] Remove any hardcoded year constants
* [ ] Expand module-level `__all__` clarity

Core modules must remain import-safe and side-effect-free.

---

## 🛡 Robustness & Safety

* [ ] Atomic file writes (temp + rename)
* [ ] Explicit output directory validation
* [ ] Harden malformed config parsing
* [ ] Guard against malformed phase definitions
* [ ] Validate user-supplied year bounds

Calmoji should fail loudly and clearly — never silently drift.

---

# 🧪 Testing Standards

Before contributing:

```bash
pytest -v --cov --cov-branch
```

Core deterministic modules should not regress in coverage.

We test for:

* Phase exclusivity correctness
* ISO week rollover
* Leap year handling
* UID determinism
* Emoji mapping completeness
* RFC 5545 folding integrity
* Slot weekday policy correctness
* Cross-year boundary grouping

If a change alters time math, you must add tests.

---

# 🧠 Current Test Status

The following are already covered:

* [x] `slugify()`
* [x] `generate_uid()` uniqueness + format
* [x] `get_emoji_for_time()` bounds + determinism
* [x] EBI48 mapping uniqueness + completeness
* [x] Phase duration correctness
* [x] Exclusive `Phase.end`
* [x] ISO week grouping across year boundaries
* [x] RFC folding / unfolding
* [x] Slot generation boundary enforcement

Future expansion:

* [ ] Simulated file write failures
* [ ] CLI argument validation tests
* [ ] Config parsing edge cases
* [ ] Large-year performance sanity checks

---

# 🧰 Tooling

Required:

* `pytest`
* `pytest-cov`
* `ruff`
* `black`
* `mypy`

CI enforces:

* Full test pass
* Coverage threshold ≥ 90%
* Branch coverage on core logic

---

# 📊 Future Direction: Declarative Planning Mode

Calmoji may evolve beyond static slot generation toward declarative planning.

Potential expansion:

## 🛠 Planner Infrastructure

* [ ] Add `X-CALMOJI-*` ICS headers
* [ ] YAML-based weekly intent declarations
* [ ] `calmoji plan --mode=declarative`
* [ ] Slot budgeting by percentage or count
* [ ] Project-to-emoji mapping layer

## 📈 Weekly Summary Output

Example:

```
Week W30 Summary:
  - Research:     6 slots
  - Engineering:  4 slots
  - Family:       5 slots
  - Unassigned:   9 slots
```

## 🔄 Long-Term Feedback Loop

* Planned vs actual slot comparison
* Symbolic drift detection
* Intent vs execution coherence analysis

These are aspirational.
Core deterministic logic remains the foundation.

---

# 🧭 Contribution Workflow

1. Fork the repo
2. Install dev requirements
3. Run full test suite
4. Make change
5. Add or update tests
6. Confirm coverage
7. Open PR with clear description

PRs that modify:

* Time math
* Phase boundaries
* UID generation
* EBI48 mapping
* RFC folding

…will receive stricter review.

---

# 🦊 Final Note

Calmoji encodes meaning in time.

That means:

* No hidden timezone conversions
* No implicit magic
* No casual symbolic changes
* No “almost correct”

If someone runs this in 2039,
the fox must still land in the same half-hour.

Let’s build something worthy of coherence.

🦊
