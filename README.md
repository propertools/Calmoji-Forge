# 🧿 calmoji

**Calendar rituals for people who drift off task.**

[![CI](https://github.com/propertools/Calmoji-Forge/actions/workflows/ci.yml/badge.svg)](https://github.com/propertools/Calmoji-Forge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

If time slides away from you, if a blank week feels like a wall, or if you
lose the thread between "I should work on that" and actually doing it,
calmoji gives your calendar a shape before you have to make any decisions.

It produces ready-made calendar layers: the seasons of your year, a daily
palette of focus blocks, and humane meeting windows across time zones. You
toggle them on to plan and off to work. When you want to use a block, you
**claim** it by copying it into your own calendar. You never build a
schedule from scratch, and you never break the structure underneath.

No app, no account, no subscription fee. Just `.ics` files that work in
Apple Calendar, Google Calendar, Outlook, Fastmail, Thunderbird, and
anything else that speaks the iCalendar standard.

---

## 🚀 Get the calendars

Download the ready-made calendars for **2026–2039** from the
[latest release](https://github.com/propertools/Calmoji-Forge/releases/latest):
grab **`calmoji-artifacts-v0.1.1.zip`** and unzip it.

Inside, pick an alignment and stick with it:

* **`academic`**: each year runs September → August (school, university,
  research, or anyone whose year turns in autumn)
* **`calendar`**: each year runs January → December

Then open the folder for the year you want, for example `2026/academic/`:

```
2026/academic/
├── semester_phases_2026.ics     ← the seasons of your year
├── meeting_all_2026.ics         ← every meeting slot for the year
├── meeting_<phase>_….ics        ← the same slots, one file per phase
├── focus_all_2026.ics           ← every focus block for the year
├── focus_<phase>_….ics          ← the same blocks, one file per phase
└── ebi48_layer_2026.ics         ← the EBI48 emoji clock
```

### Importing

Create one calendar per layer in your calendar app (for example
"🧠 Focus Blocks", "🕒 Meeting Slots"), then import each file into its own
calendar. That's what lets you colour each layer and switch it on and off
on its own; the [playbook](docs/PLAYBOOK.md) explains why it matters.

* **Apple Calendar:** File → Import → choose the file → choose the calendar.
* **Google Calendar:** Settings → Import & export → choose the file and the
  destination calendar.
* **Outlook, Fastmail, Thunderbird and others:** use your app's "Import"
  option.

Tips for v0.1:

* **Focus blocks come one file per phase.** Start with the phase you're
  in rather than the whole year; it's a gentler start anyway. Each phase
  file holds only that phase's own days, so the files never overlap.
* Use **either** `meeting_all_<year>.ics` **or** the per-phase meeting
  files, not both. The same goes for `focus_all_<year>.ics` and the
  per-phase focus files.
* To refresh a layer later, delete that calendar, recreate it and import
  again. Your own plans live in your own calendars and are untouched.

Subscribable feeds that update themselves, and a website to browse and
download individual files, are coming in v0.2. See the
[roadmap](#-roadmap).

Calendar apps differ in small ways. If something doesn't work in yours,
please [open an issue](https://github.com/propertools/Calmoji-Forge/issues);
we'll fold what we learn into these docs.

---

## 🧭 How to use it

The short version:

1. **Reference layers are read-only.** calmoji's layers show what's
   *available*. Don't edit them.
2. **Claim, don't edit.** To use a focus block or meeting slot, duplicate
   it into one of your own calendars (for example "🎯 Focus — Claimed").
3. **Mark progress in the title.** 🎯 means planned, ✅ means done. Search
   for 🎯 to find what slipped; search for ✅ for your weekly review.
4. **Regenerate without fear.** Because your plans live in your own
   calendars, you can delete and re-import calmoji's layers any time.
   Nothing you've claimed is lost.
5. **Layers are privacy controls.** When scheduling with someone, show only
   the layers they should see.

The full pattern, with a suggested set of calendars and the weekly loop,
is in **[docs/PLAYBOOK.md](docs/PLAYBOOK.md)**. It's a starting point, not a
rulebook: start small and adapt it.

---

## 🗂 What's in each layer

Every event is marked **private** and **free** (it won't make you look
busy). All times are fixed in **UTC**; your calendar app shows them in your
local time.

### 📅 Semester phases

The year is divided into eight phases, each an all-day marker so you always
know which mode you're in. Names come from the academic year; in the
`calendar` alignment the same arc starts on 1 January.

| Phase | Length | Meeting slots? |
|---|---|---|
| 🌱 Semester A (Seed) | 14 weeks | yes |
| ❄️ Winter Break | 2 weeks | no |
| 🌾 Semester A (cont.) | 25 days | yes |
| 🪷 Downtime A→B | 2 weeks | yes |
| 🔥 Semester B (Flame) | 19 weeks | yes |
| 🐚 Summer Rest | 15 days | no |
| 🧠 Deep Work Phase | 6 weeks | yes |
| 🍂 Autumn Drift | until the year turns | no |

### 🧠 Focus blocks

Twelve 96-minute blocks a day, starting every two hours on the hour (UTC),
every day of the week, with a 24-minute breather between them. Each has a
theme glyph: 🧠 deep thinking, ✍️ writing, 📚 reading, 🔧 technical,
🧾 admin, 📞 comms, 🪞 reflection, 📈 analysis, 🎨 creative,
🛠️ maintenance, ⚖️ decisions, ⛩️ closure. You'll only ever use the few
that fall in your waking hours. Each week also gets an all-day 🗝️ Glyph
Key marker.

### 🕒 Meeting slots

25-minute windows starting at :05 or :35 past the hour, two per city,
placed around early afternoon local time in Tokyo, Delhi, Mecca, Brussels,
Havana and Seattle (Auckland is available when you generate them
yourself). Slots run Monday–Friday (Sunday–Thursday for Mecca) and pause
during breaks. Each slot carries the EBI48 emoji for its half-hour.

### 🧿 EBI48 clock

A deterministic emoji for each of the day's 48 half-hours, anchored at :05
and :35 UTC, so "let's meet at 🦊" means the same moment everywhere. See
[EBI48-README.md](EBI48-README.md).

### ⚠️ Known limitations

* **Meeting slot labels assume summer time.** Slots are fixed in UTC, and
  their local-time labels (CEST, EDT, PDT) are correct for summer. In
  winter, Brussels, Havana and Seattle slots fall an hour earlier in local
  time than the label says. The UTC time is always correct.
* **The EBI48 layer appears one day a week**, and each entry shows its
  emoji twice. Its event descriptions also link to ebi48.org, which isn't
  live yet.
* **Leap years:** the last day of a leap year (for example 31 August 2028
  in `academic`, 31 December 2028 in `calendar`) belongs to no year's
  files.

All of these are on the [roadmap](#-roadmap) for v0.2.

---

## 🧭 Core principles

### 1️⃣ UTC everywhere

All datetimes are timezone-aware and normalized to **UTC**. No floating
times. No silent conversions.

### 2️⃣ Exclusive end semantics

Phases use `[start, end)`. End is exclusive. That means correct duration
math, no off-by-one errors, clean boundaries, and deterministic tests.

### 3️⃣ Deterministic output

Stable UIDs, stable emoji mappings, stable file structure. The same inputs
always produce byte-identical files, on any machine and any supported
Python version. CI checks this on every commit.

---

## 🛠 Regenerating the calendars yourself

You only need this if the published calendars don't cover what you want:
another year, another alignment, or different layers.

```bash
git clone https://github.com/propertools/Calmoji-Forge.git
cd Calmoji-Forge
```

Generate. Nothing to install, no third-party packages: any Python 3.9 or
newer works, including the `python3` that ships with macOS.

```bash
python3 calmoji.py --year=2027 --calendar-alignment=academic
```

Alignments: `academic`, `calendar`, `fiscal_us`, `fiscal_eu`,
`japanese_school`, `indian_fiscal` (plus `chinese_lunar` and
`islamic_hijri`, which currently use placeholder anchor dates).

Options:

```bash
--output-dir=DIR     # default: output/
--dry-run            # preview, write nothing
--no-meetings        # skip meeting slots
--no-focus           # skip focus blocks
--no-ebi48           # skip the EBI48 layer
--include-oceania    # add Auckland meeting slots
```

Output for one year:

```
output/
├── semester_phases_2027.ics
├── focus_all_2027.ics              ← all focus blocks for the year
├── focus_<phase>_<dates>.ics       ← the same, one file per phase
├── meeting_all_2027.ics            ← all meeting slots for the year
├── meeting_<phase>_<dates>.ics     ← the same, one file per phase
└── ebi48_layer_2027.ics
```

Optionally, install it as a package to get a `calmoji` command. Use a
virtual environment, and upgrade pip first (macOS ships an old one):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
calmoji --year=2027
```

Working on calmoji itself? `python3 -m pip install -e '.[dev]'` adds the
test, lint and type-check tools, and `bash scripts/preflight.sh` runs every
check CI runs.

If you regenerate a year we publish and get a different file, that's a
bug. Please open an issue.

---

## 📍 Roadmap

v0.1 is deliberately small: it works today, and it's what I use myself. Planned
for v0.2, in no promised order:

* **Subscribable calendars that update themselves**: rolling feeds that
  always cover this year and next, so there's nothing to re-import each
  year.
* **A website, calmoji.propertools.be,** to browse the calendars and
  download single files or a zip per year, without unpacking the whole
  archive.
* **Meeting-slot labels that stay correct** through daylight saving time
  changes.
* **An EBI48 clock that appears every day**, with its emoji shown once.
* **The leap-year gap closed**, so consecutive years fit together
  exactly.
* **Releases built automatically** from a git tag, with byte-identical
  output checked in CI.

Ideas and calendar-app quirks are very welcome in
[issues](https://github.com/propertools/Calmoji-Forge/issues).

---

## 🧪 Test discipline

```bash
pytest --cov=calmoji --cov-report=term-missing
```

Coverage includes exclusive-end correctness, ISO week boundaries across
year transitions, deterministic UID format, emoji uniqueness and
completeness, slot duration and cadence guarantees, ICS folding and
unfolding, and a guard against stray `date` imports.

This is a calendar system that proves its invariants.

---

## 🧭 Design philosophy

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

* Ritual design: Trey Darley
* Engineering discipline: Trey Darley
* AI pair engineering: ChatGPT, Claude
* Glyph architecture: [EBI48](EBI48-README.md)

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
