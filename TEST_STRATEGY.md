# 🧪 Calmoji Testing & Coverage Doctrine

This document defines coverage targets and testing principles for the **Calmoji** timekeeping engine.

The per-module numbers below are **targets**, not gates. The only coverage gate CI
enforces is the 90% total (see "What CI enforces").

Our goal is not vanity metrics.

We do not chase 100% coverage for optics.

We test for:

* Determinism
* Temporal correctness
* Symbolic coherence
* RFC compliance
* Reproducibility

The engine must remain mathematically stable across time.

---

## 🎯 Coverage Targets by Layer

| Layer                    | Coverage Target | Rationale                             |
| ------------------------ | --------------- | ------------------------------------- |
| `types.py`               | 100%            | Pure data structures                  |
| `ebi48.py`               | 100%            | Canonical fixed mapping               |
| `utils.py`               | 95–100%         | Core time + UID logic                 |
| `ics_writer.py`          | 100%            | RFC 5545 correctness                  |
| `calendar_config.py`     | 95%+            | Anchor logic integrity                |
| `calendar_phases.py`     | 95%+            | Offset + enrichment correctness       |
| `slot_generator.py`      | 95%+            | Boundary & weekday policy correctness |
| `monthly.py`             | 90%+            | Month bucketing and file naming       |
| CLI layer (when present) | 80%+            | I/O wrapper, lower criticality        |

Core deterministic layers should approach total coverage.
Presentation and CLI layers may tolerate minor gaps.

Some modules are below their target today (for example, the helper functions in
`ebi48.py` beyond the mapping lookups, and a few branches in `utils.py`). Run
`pytest --cov=calmoji --cov-branch --cov-report=term-missing` to see the current
numbers.

---

## 🛡️ Testing Principles

### 1️⃣ Determinism First

* EBI48 mapping must be fully covered
* UID generation must be deterministic and unique
* Phase offsets must produce stable, predictable boundaries
* UTC behavior must never depend on system locale

---

### 2️⃣ Temporal Correctness

* `Phase.end` is **exclusive** — always
* Durations must be mathematically derived
* Events must remain within phase boundaries
* ISO week grouping must behave correctly across year boundaries
* Leap years must not break slot generation

---

### 3️⃣ RFC 5545 Compliance

* ICS line folding must respect the 75-octet limit (octets, not characters)
* Unfolding must properly reconstruct logical lines
* TEXT values (summaries, descriptions, comments, calendar names) must be escaped, so no value can inject a property
* UID format must be stable and parseable
* All timestamps must be UTC-normalized

If an `.ics` file imports inconsistently across calendar clients,
the test suite must catch it first.

---

### 4️⃣ Edge Case Discipline

We test:

* Invalid weekday inputs
* Negative offsets
* Out-of-range integers
* Malformed fold continuations
* Emoji mapping bounds

Failing safely is as important as succeeding correctly.

---

### 5️⃣ Symbolic Integrity

Symbolic systems require strict validation:

* All 48 emoji slots must be unique
* No duplicate glyphs
* No missing half-hour segment
* All labels must be strings
* All mappings must round-trip cleanly

We test the glyph layer because it encodes meaning.

---

## 🧰 Tooling

* `pytest`
* `pytest-cov` (branch coverage enabled)
* `mypy` (strict mode)
* `ruff`
* `black`
* GitHub Actions CI (it uploads `coverage.xml` as a build artifact)

---

## 🧱 What CI enforces

CI fails if:

* Any test fails (on Python 3.9 through 3.13)
* Total coverage, measured with branch coverage, drops below **90%**
  (`fail_under` in `pyproject.toml`)
* `ruff`, `black --check` or `mypy calmoji` fail
* A sample year generated twice, and on Python 3.9 and 3.13, isn't byte-identical
* The package can't generate a year, or its test suite fails, on macOS's `/usr/bin/python3`

Nothing else is gated. In particular there is no per-module coverage floor and no
automatic check that tests avoid local-timezone behaviour; those are targets and
review practice.

---

## 🧭 Philosophy

Calmoji is a time engine.

Time engines must be:

* Stable
* Verifiable
* Deterministic
* Portable

We write tests not only for correctness,
but for **coherence across time**.

If someone runs this engine in 2039,
the fox should still land in the same half-hour.

🦊

---
