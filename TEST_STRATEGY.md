# 🧪 Calmoji Testing & Coverage Doctrine

This document defines coverage targets and testing principles for the **Calmoji** timekeeping engine.

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
| `focus_blocks_writer.py` | 90%+            | Event expansion logic                 |
| CLI layer (when present) | 80%+            | I/O wrapper, lower criticality        |

Core deterministic layers must approach total coverage.
Presentation and CLI layers may tolerate minor gaps.

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

* ICS line folding must respect 75-character limits
* Unfolding must properly reconstruct logical lines
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
* `mypy` (strict mode recommended)
* `ruff`
* `black`
* GitHub Actions CI
* Codecov for trend tracking

CI enforces:

* Full test pass
* Coverage thresholds
* Branch coverage on core logic

---

## 🧱 CI Thresholds

CI fails if:

* Global coverage drops below **90%**
* Any critical deterministic module drops below **95%**
* Branch coverage regresses on core logic
* Deterministic tests begin relying on local timezone behavior

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
