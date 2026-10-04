# Security Policy

## Reporting a vulnerability

If you believe you have found a security-relevant issue in **calmoji**, please
report it privately rather than opening a public GitHub issue.

**Preferred channel:** email `security@propertools.be`.

**Backup channel:** GitHub's *Report a vulnerability* button on the repository's
**Security** tab (private vulnerability reporting).

If your report includes anything you would not want to send in cleartext —
exploit code, sensitive logs, identifying details — please request a PGP key
in the first message and we will send one. We do not publish a long-lived
project key in this repository because the contributor set is small enough
that key rotation is best handled out-of-band.

We aim to acknowledge any report within **3 working days (Brussels time)**.
A substantive triage response will follow within **10 working days** in most
cases. If you do not hear back, please re-send: mail filtering occasionally
swallows threads.

## Disclosure model

We follow coordinated disclosure. The default sequence is:

1. You report privately.
2. We acknowledge, reproduce, and triage.
3. We agree on a fix and a target disclosure date with you.
4. We ship the fix in a tagged release.
5. We publish a brief advisory crediting the reporter (unless anonymity is
   requested).

We will not threaten legal action against good-faith security researchers
operating within the scope below. We will not pay bounties — this is a
small public-interest project — but we will credit you publicly and we will
take the issue seriously.

## Supported versions

calmoji is pre-1.0 and uses a single rolling line of support. Only the
latest tagged release on `main` receives security fixes. There are no
backports to earlier tags.

| Version       | Supported          |
| ------------- | ------------------ |
| latest tag    | :white_check_mark: |
| earlier tags  | :x:                |
| `main` branch | best effort        |

## In scope

- The Python package `calmoji` and its CLI.
- The pre-generated `.ics` artifact bundle distributed alongside tagged
  releases (e.g. on GitHub Releases or via [ebi48.org](https://ebi48.org)).
- The EBI48 emoji-to-time mapping table in `calmoji/ebi48.py`.

## Out of scope

- Third-party calendar clients (Apple Calendar, Google Calendar, Outlook,
  Thunderbird, etc.). Bugs in how those clients render or import our `.ics`
  files belong to those vendors. We are happy to help diagnose, but we
  cannot fix them.
- Issues caused by user-modified output files.
- Denial-of-service against the generator from adversarial CLI input that
  is not also exploitable as a privilege escalation.
- Anything depending on a development environment that already has
  arbitrary code execution by the user.

## What we care most about

calmoji is a deterministic time engine. The properties most likely to
matter to a security reporter are:

- **Output integrity.** A malformed input must never produce a *valid-looking
  but silently wrong* `.ics` file (e.g. wrong UTC offset, swapped phase
  boundaries, duplicate UIDs masquerading as updates).
- **Determinism.** A regression that makes outputs depend on locale, system
  clock, or environment is treated as a correctness bug *and* a supply-chain
  hazard, because downstream consumers rely on the property to verify
  artifact provenance.
- **RFC 5545 conformance.** Folding, escaping, or UID generation that drifts
  from the spec in ways an attacker could weaponize against a calendar
  client.

These are bugs to us regardless of exploitability. If you find one, we
want to know.
