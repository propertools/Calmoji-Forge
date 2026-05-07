---
title: EBI48 — The Canonical Emoji Clock
description: A deterministic emoji-based time overlay for UTC coordination.
layout: default
---

# 🧿 EBI48 — The Canonical Emoji Clock

> Time is precise.  
> EBI48 makes it legible.

EBI48 is a deterministic symbolic overlay for UTC time.  
It divides every day into **48 half-hour segments** and assigns each segment a **unique emoji + label pair**.

No randomness.  
No timezone drift.  
No ambiguity.

---

## 🌍 What Is EBI48?

EBI48 is a canonical mapping:

- 48 slots per UTC day  
- Each slot = 30 minutes  
- Each slot = one emoji + one label  
- Mapping is globally stable and versioned  

Example:

```

🐶 Dog Face
🦊 Fox Face
⛰️ Mountain Face

```

Every slot has exactly one symbol.  
Every symbol corresponds to exactly one half-hour.

---

## 🧭 Why It Exists

UTC is globally consistent but cognitively abstract.

EBI48 adds a symbolic layer:

- 👁 Visual shorthand
- 🌐 Cross-lingual coordination
- 📞 Voice-friendly scheduling
- 🧠 Improved mnemonic recall

Instead of:

> “Let’s meet at 05:35 UTC.”

You can say:

> “Let’s meet during Fox Face.”

The timestamp remains canonical.  
The glyph becomes memorable.

---

## 🕒 How It Works

- Day divided into 48 × 30-minute slots
- Anchored strictly to UTC
- No DST adjustments
- No locale variance
- Deterministic mapping table (`EBI48_CLOCK`)

The mapping is:

- Complete (all 48 slots covered)
- Unique (no duplicate glyphs)
- Stable across implementations
- Machine-verifiable

---

## 📅 Distribution

EBI48 is distributed as a standards-compliant `.ics` layer:

- RFC 5545 compliant
- Proper line folding
- Deterministic UID generation
- UTC timestamps only

Compatible with:

- Google Calendar
- Apple Calendar
- Outlook
- CalDAV servers
- Automation scripts
- Embedded systems

---

## 🔁 Deterministic Properties

EBI48 guarantees:

- The same UTC timestamp always maps to the same emoji
- The same emoji never maps to multiple slots
- Mapping does not depend on geography
- Mapping does not depend on user settings

This makes it safe for:

- Incident response
- AI-human interfaces
- Voice scheduling
- Low-bandwidth coordination
- Distributed system logging overlays

---

## 🧠 Design Constraints

The glyph set was curated to ensure:

- High visual distinctiveness
- Low semantic collision
- Minimal cultural ambiguity
- Clear Unicode support across major platforms

Avoided:

- Skin-tone modifiers
- Flag sequences
- Politicized symbols
- Lookalike duplicates

---

## 🛠 Developer Notes

EBI48 is:

- UTC-only
- Pure mapping (no side effects)
- Embeddable in other systems
- Independent of calmoji (but used by it)

In Python:

```python
from calmoji.ebi48 import get_emoji_for_time

emoji, label = get_emoji_for_time(dt_utc)
```

The mapping table is exposed as:

```python
EBI48_CLOCK
```

---

## 🦊 Relationship to calmoji

EBI48 powers:

* Meeting slot tagging
* Symbolic focus cycles
* Cross-team coordination layers
* Ritual scheduling experiments

calmoji uses EBI48 as a stable time primitive.

EBI48 can also be used independently.

---

## ⚖️ License

* Code: MIT License
* Mapping tables: CC0 1.0 (public domain where possible)

---

## 🧭 Philosophy

EBI48 is not an aesthetic flourish.

It is a cognitive compression layer.

If only printed calendars and emoji glyphs survive,
Fox Face will still mean something precise.

---

EBI48 v2025
UTC-only.
Deterministic.
Canonical.

---

