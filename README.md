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

Download the ready-made calendars for **2026–2036** from the
[latest release](https://github.com/propertools/Calmoji-Forge/releases/latest):
grab **`calmoji-artifacts-vX.Y.Z.zip`** (X.Y.Z is the release's version
number) and unzip it.

Inside, pick an alignment and stick with it:

* **`academic`**: each year runs September → August (school, university,
  research, or anyone whose year turns in autumn)
* **`calendar`**: each year runs January → December

Then open the folder for the year you want, for example `2026/academic/`:

```
2026/academic/
├── seasons_2026.ics             ← 🌗 Seasons: the seasons of your year
├── emoji_clock_2026.ics         ← 🧿 Emoji Clock
├── focus/
│   └── focus_2026-09.ics …      ← 🧠 Focus — Open, one file per month
└── meetings/
    └── meetings_2026-09.ics …   ← 🕒 Meetings — Open, one file per month
```

### Importing

Create one calendar per layer in your calendar app (for example
"🧠 Focus — Open", "🕒 Meetings — Open"), then import each file into its own
calendar. That's what lets you colour each layer and switch it on and off
on its own; the [playbook](docs/PLAYBOOK.md) explains why it matters. Give
each layer its own colour; the playbook suggests a
[calm starting palette](docs/PLAYBOOK.md#colours). In apps that create a
calendar when you import, the file already names it for you.

* **Apple Calendar:** File → Import → choose the file → choose the calendar.
* **Google Calendar:** Settings → Import & export → choose the file and the
  destination calendar.
* **Outlook, Fastmail, Thunderbird and others:** use your app's "Import"
  option.

Tips for v0.1:

* **Start with this month and next.** Focus blocks and meeting slots come
  one file per month; add more months as you go. It's a gentler start
  anyway.
* **Months are in UTC.** If you're west of UTC, an event late in the
  evening on the last day of a month may be in the next month's file.
* **Every file is kept under 600 events and 512 KB**, so it fits the
  import limits reported for Google, Outlook and Proton. The ready-made
  calendars cover 2026–2036 because Proton accepts events only up to 2037;
  any other year you can
  [generate yourself](#-regenerating-the-calendars-yourself).
* To refresh a layer later, delete that calendar, recreate it and import
  again. Your own plans live in your own calendars and are untouched.

### Upgrading from v0.1.0

Delete the old calmoji calendars and import fresh. Event times and
identifiers changed (see the [changelog](CHANGELOG.md)), so importing over
the old ones would leave you with duplicates.

Subscribable feeds that update themselves, and a website to browse and
download individual files, are coming in v0.2. See the
[roadmap](#-roadmap).

Calendar apps differ in small ways. If something doesn't work in yours,
please [open an issue](https://github.com/propertools/Calmoji-Forge/issues);
we'll fold what we learn into these docs.

---

## 🧭 How to use it

The short version:

1. **The Map is read-only.** calmoji's layers (🌗 Seasons,
   🧠 Focus — Open, 🕒 Meetings — Open and 🧿 Emoji Clock) show what's
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

### 🌗 Seasons

The year is divided into eight phases, each an all-day marker so you always
know which mode you're in. Names come from the academic year; in the
`calendar` alignment the same arc starts on 1 January.

| Phase | Length | Open meetings? |
|---|---|---|
| 🌱 Semester A (Seed) | 14 weeks | yes |
| ❄️ Winter Break | 2 weeks | no |
| 🌾 Semester A (cont.) | 25 days | yes |
| 🪷 Downtime A→B | 2 weeks | yes |
| 🔥 Semester B (Flame) | 19 weeks | yes |
| 🐚 Summer Rest | 15 days | no |
| 🧠 Deep Work Phase | 6 weeks | yes |
| 🍂 Autumn Drift | until the year turns | no |

### 🧠 Focus — Open

Twelve 96-minute blocks a day, starting every two hours on the hour (UTC),
every day of the week, with a 24-minute breather between them. Each has a
theme glyph: 🧠 deep thinking, ✍️ writing, 📚 reading, 🔧 technical,
🧾 admin, 📞 comms, 🪞 reflection, 📈 analysis, 🎨 creative,
🛠️ maintenance, ⚖️ decisions, ⛩️ closure. You'll only ever use the few
that fall in your waking hours. Each week also gets an all-day 🗝️ Glyph
Key marker. They come one file per month.

### 🕒 Meetings — Open

25-minute windows starting at :05 or :35 past the hour, two per city,
placed around early afternoon local time in Tokyo, Delhi, Mecca, Brussels,
Havana and Seattle (Auckland is available when you generate them
yourself). Slots run Monday–Friday (Sunday–Thursday for Mecca) and pause
during breaks. Each slot carries the EBI48 emoji for its half-hour, and they
come one file per month.

Like everything in calmoji, slots are fixed in UTC all year, and your
calendar app shows them in your local time. Each slot's description says
exactly when it falls locally.

### 🧿 Emoji Clock

I designed EBI48 after years of watching global technical standards
calls spend their last ten minutes on time-zone arithmetic: which
city, which day, has London changed its clocks yet, does that clash with
Jane's carpool next Thursday. Everyone was doing mental maths, juggling
guilt and triage, just to find a time.

EBI48 gives each of the day's 48 half-hours an emoji that means the same
moment everywhere, anchored at :05 and :35 UTC. Your calendar shows each
one at your local time, so nobody converts anything out loud. Instead of
doing sums, you **pick a day and look for free animals at acceptable
times**. See [EBI48-README.md](EBI48-README.md).

### ⚠️ Known limitations

* **Daylight saving time moves meeting slots in local time.** A slot keeps
  the same UTC time all year, so in cities with daylight saving time
  (Brussels, Havana, Seattle) its local time is an hour earlier in winter
  than in summer. Each slot's description says exactly when it falls,
  summer and winter.
* **Months are in UTC.** An event late in the evening on the last day of a
  month, for someone west of UTC, may be in the next month's file.

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
Python version. CI checks this on every commit: it generates a sample year
twice, and on Python 3.9 and 3.13, and compares the files byte for byte.

Even `DTSTAMP`, which RFC 5545 requires on every event, is a fixed,
documented constant rather than "now", so that files stay reproducible.

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

By default the files go to `output/<year>/<alignment>/`, so different years
and alignments never mix. calmoji only writes into a folder that is empty or
that it made itself (it leaves a `.calmoji-output` file there), and re-running
replaces its own files in that folder. Any other non-empty folder is refused,
untouched.

Alignments: `academic`, `calendar`, `fiscal_us`, `fiscal_eu`,
`japanese_school`, `indian_fiscal`.

Options:

```bash
--year=YYYY          # required
--output-dir=DIR     # default: output/<year>/<alignment>/
--dry-run            # preview what would be written, month by month
--no-meetings        # skip meeting slots
--no-focus           # skip focus blocks
--no-ebi48           # skip the EBI48 layer
--include-oceania    # add Auckland meeting slots
```

Output for one year (the files are in `output/2027/academic/` here):

```
output/2027/academic/
├── .calmoji-output                     ← marks the folder as calmoji's
├── seasons_2027.ics
├── emoji_clock_2027.ics
├── focus/
│   └── focus_<YYYY-MM>.ics …           ← one file per month
└── meetings/
    └── meetings_<YYYY-MM>.ics …        ← one file per month
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
test, lint and type-check tools, and `bash scripts/preflight.sh` runs CI's
main checks on your machine (tests with coverage, ruff, black, mypy) plus a
reproducible release-bundle build. CI also tests Python 3.9 through 3.13,
compares output across Python versions, and runs on stock macOS.

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
