# 🧿 calmoji

## Ritual Calendar Generator — UTC, Deterministic, Glyph-Aligned

[![CI](https://github.com/propertools/Calmoji-Forge/actions/workflows/ci.yml/badge.svg)](https://github.com/propertools/Calmoji-Forge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

> A symbolic scheduling engine built on UTC discipline, exclusive time semantics, and deterministic emoji clocks.

---

## 📖 What is calmoji?

**calmoji** generates structured `.ics` calendar files based on:

* 📅 Academic or fiscal year alignment
* 🧠 Phase-aware focus blocks
* 🌍 Globally humane meeting slots
* 🧿 Deterministic emoji time mapping via EBI48

It is not a SaaS product.
It is not a cloud scheduler.

It is a **semantic calendar compiler**.

You give it a year and alignment.
It produces canonical, UTC-stable calendar artifacts.

---

## 🚀 Quick start — just give me the calendars

Most people don't need to run anything. We pre-generate the calendars and
publish them.

**Get the bundle:**

* 🌐 [ebi48.org](https://ebi48.org) — canonical home of the EBI48 emoji
  time protocol and the calmoji `.ics` artifacts. Pick a year, subscribe
  or download.
* 📦 [GitHub Releases](https://github.com/propertools/Calmoji-Forge/releases)
  — every tagged version ships a `calmoji-artifacts-vX.Y.Z.tar.gz` bundle
  containing all years, both alignments, and a `MANIFEST.sha256` for
  verification.

**What you get for each year:**

```
<year>/
├── academic/
│   ├── semester_phases_<year>.ics       ← season markers
│   ├── meeting_all_<year>.ics           ← meeting slot grid
│   ├── focus_weeks/                     ← weekly focus blocks
│   └── ebi48_layer_<year>.ics           ← EBI48 emoji clock overlay
└── calendar/
    └── … same shape, January-anchored
```

**To import into your calendar:**

* **Apple Calendar:** File → Import → select the `.ics`. For ongoing
  subscription, File → New Calendar Subscription with the ebi48.org URL.
* **Google Calendar:** Settings → Add calendar → From URL (subscription)
  or Import (one-shot).
* **Thunderbird / others:** subscribe to the ebi48.org URL via
  `webcal://`.

The files are deterministic and re-import-safe: re-importing won't create
duplicates, only updates.

If you want the generator itself — to produce calendars for a year we
haven't published, change the alignment, or add new layers — see
[Regenerating the calendars yourself](#-regenerating-the-calendars-yourself)
below.

---

## 🧭 Core Principles

### 1️⃣ UTC Everywhere

All datetimes are timezone-aware and normalized to **UTC**.
No floating times. No silent conversions.

### 2️⃣ Exclusive End Semantics

Phases use:

```
[start, end)
```

End is exclusive.

This guarantees:

* Correct duration math
* No off-by-one errors
* Clean boundary reasoning
* Deterministic testability

### 3️⃣ Deterministic Output

* Stable UID generation
* Stable emoji mappings
* Stable file structure
* Re-import safe `.ics` generation

If you run the same command twice, you get the same structure.

---

## 📅 Academic Phase Engine

The year is divided into symbolic phases:

* Semester A (Seed)
* Winter Break
* Semester A (cont.)
* Downtime A→B
* Semester B (Flame)
* Summer Rest
* Deep Work Phase
* Autumn Drift

Each phase includes:

* Concrete UTC start/end
* Meeting density classification
* Focus block generation
* Weekly ISO segmentation

Phases are aligned via:

```bash
--calendar-alignment=calendar
--calendar-alignment=academic
--calendar-alignment=fiscal_us
--calendar-alignment=fiscal_eu
--calendar-alignment=japanese_school
--calendar-alignment=indian_fiscal
```

---

## 🧠 Focus Blocks

Focus blocks are:

* Defined centrally in `focus_blocks_config.py`
* Generated per ISO week
* Optionally include a weekly **Glyph Key** all-day marker
* Deterministic and sorted

Each ISO week emits:

* N focus blocks × active weekdays
* 1 all-day glyph key event

No clipping. Whole-week coherence > partial-week precision.

---

## 🌍 Meeting Slot Engine

Meeting slots:

* 25 minutes long
* Start at :05 or :35
* Deterministically emoji-tagged
* Region-aware weekday policies (e.g. Mecca Sunday–Thursday)
* Generated per phase with cadence control

Slots are anchored to UTC and filtered by phase range:

```
phase.start <= event.start < phase.end
event.end <= phase.end
```

---

## 🧿 EBI48 — Emoji Time Protocol

Each half-hour UTC segment maps to exactly one emoji + label.

Example:

```
🐶 Dog Face
🦊 Fox Face
⛰️ Mountain Face
```

Mapping is:

* Deterministic
* Complete (48 slots)
* Unique
* Globally consistent

This provides:

* Visual shorthand
* Cross-lingual clarity
* Low-bandwidth coordination
* Memory hooks without ambiguity

---

## 📦 Output Structure

Running:

```bash
python3 calmoji.py --year=2039
```

Produces:

```
output/
├── semester_phases_2039.ics
├── meeting_<phase>_<dates>.ics
├── meeting_all_2039.ics
├── focus_weeks/
│   ├── <phase>__2039-W01.ics
│   ├── <phase>__2039-W02.ics
│   └── ...
└── ebi48_layer_2039.ics
```

Each event includes:

```ics
SUMMARY: Tokyo 🦊 Fox Face Slot (13:30–13:55 JST)
DESCRIPTION: 🌱 — Semester A (Seed)
CLASS: PRIVATE
```

ICS output conforms to RFC 5545 folding rules.

---

## 🛠 Regenerating the calendars yourself

You only need this section if the pre-generated bundle on
[ebi48.org](https://ebi48.org) doesn't cover what you want — a year we
haven't published, a different alignment, or a custom layer toggle.

Clone:

```bash
git clone https://github.com/propertools/Calmoji-Forge.git
cd Calmoji-Forge
```

Generate. Nothing to install, no third-party packages: any Python 3.9
or newer works, including the `python3` that ships with macOS.

```bash
python3 calmoji.py --year=2039
```

Optionally, install it as a package to get a `calmoji` command:

```bash
pip install -e .
calmoji --year=2039
python3 -m calmoji --year=2039
```

Or install directly from GitHub without cloning:

```bash
pip install 'calmoji @ git+https://github.com/propertools/Calmoji-Forge.git'
```

Working on calmoji itself? `pip install -e '.[dev]'` adds the test,
lint and type-check tools.

Preview only:

```bash
calmoji --year=2039 --dry-run
```

Disable layers:

```bash
--no-meetings
--no-focus
--no-ebi48
```

Reproducibility note: the same `--year` and `--calendar-alignment` always
produce byte-identical output. CI verifies this on every commit, across Python versions. So if
you regenerate `2030 / academic` locally, you should get exactly the
files we shipped. If you don't, that's a bug — please open an issue.

---

## 🧪 Test Discipline

Run the suite:

```bash
pytest --cov=calmoji --cov-report=term-missing
```

Coverage includes:

* Exclusive end correctness
* ISO week boundaries across year transitions
* Deterministic UID format
* Emoji uniqueness + completeness
* Slot duration + cadence guarantees
* ICS folding/unfolding compliance
* No stray date imports

This is a calendar system that proves its invariants.

---

## 🧭 Design Philosophy

calmoji is part of the Proper Tools toolchain.

It is designed to:

* Survive infrastructure drift
* Remain interpretable in low-bandwidth environments
* Encode meaning without dependency on platforms
* Preserve coherence over spectacle

If printed on paper, the system still works.

If imported into any standards-compliant calendar, it still works.

If nothing survives but glyphs and dates, it still makes sense.

---

## 🙌 Credits

* Ritual Design: Trey Darley
* Engineering Discipline: Trey Darley
* AI Pair Engineering: ChatGPT, Claude
* Glyph Architecture: [EBI48.org](https://ebi48.org)

---

## 🔐 Security

See [SECURITY.md](SECURITY.md) for the coordinated-disclosure policy and
contact channel. Reports of output non-determinism, RFC 5545 drift, or
malformed-input handling are explicitly in scope.

---

## 📜 License

* Code: [MIT License](LICENSE)
* EBI48 mapping table: CC0 1.0 (public domain where possible)

---

> Calendars should be precise.
> Time should be encoded cleanly.
> Coherence is not optional.

Fox Face, out! 🦊

---

