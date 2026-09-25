# CLAUDE.md

Read `HANDOVER.md` next. It is long; start with **Current state** at the top,
which is the only part guaranteed to reflect what is true now.

## What this is

A computational model of gas exchange during apnoea. Two implementations that
MUST agree to within 1%: `apnoea_core.py` (reference) and `model.js` (browser).
Change one, change the other, then run `python3 build_page.py`.

## Rules that exist because they were broken

**Never trust a number you did not just compute.** Every retraction in this
project's history came from asserting a value from memory or from an abstract.
If a paper is not in the repository or uploaded to the session, say so and treat
the number as unverified. Reasoning from what a document does NOT say has been
wrong every time it was tried.

**Always check which model file you loaded.** A whole afternoon's results were
once computed against a stale copy of `apnoea_core.py` in a scratch directory.
Any throwaway script must print its provenance:

```python
import apnoea_core; print(apnoea_core.provenance())
```

Run from the repository root. If you deliberately want a modified copy — for a
parameter sweep outside the repo — that is fine, but print the provenance so
the output says so.

**Numbers in markdown rot. Numbers in scripts do not.** So do FACTS in
markdown: on 2026-09-25 five separate claims about which papers had been read
were found wrong across four documents, because the same fact was written in
four places with no link between them. `sources_registry.py` now holds that
fact once and `check_sources.py` regenerates README from it. If you find
yourself about to state in prose something another file also states, ask
whether it can be generated instead. Anything quoted in
HANDOVER should be regenerable by `python3 handover_numbers.py`, which fails if
a value has drifted. If you add a table to HANDOVER, add it there too. The
Ellis comparator rows are the cautionary example: recorded, never scripted, and
now unreproducible.

**Only published data goes in this repository.** Not unpublished trial results,
not a collaborator's spreadsheet, not numbers derived from either — including
derived numbers in prose, in a commit message, or as the value of a parameter.
`make_package.sh` builds from `git archive HEAD`, so everything tracked here
travels in every package. This rule exists because trial figures reached
HANDOVER.md and protocol/evidence.md before anyone had decided they could be
used, and had to be redacted. If unpublished data suggests a finding, the
finding can only be recorded once it stands on a published source, or on
something internal to this code.

**One authorised exception to the rule above, granted 2026-09-21.** A. Heard,
who owns the data, authorised use of `Glottic01_analysed.xlsx` — a
transcutaneous monitor export from the Toner study. The rule is not repealed:
everything else unpublished stays out. The terms that make this safe are in
`SOURCES.md`, and the important one is that a finding which rests on this trace
alone is reported as resting on it, by name, and not laundered into a parameter
or a benchmark band.

**Do not tune a parameter to pass a benchmark.** This has been proposed and
refused four times, each recorded in HANDOVER with the reasoning. A change
needs a mechanism, not a fit. If a correction makes a benchmark WORSE, that is
information — record it, do not reach for a compensating parameter.

## How to report back

These are about the reply, not the physics, and they were asked for because the
default was wrong in both directions.

**End every reply with a list of what the reader has to do.** Split it: what
only they can decide, what needs something fetched from outside, and what you
can do next on a word from them. Specific and ordered, not "let me know how
you'd like to proceed".

**Gloss every code reference in plain language.** `crs = 85.0` means nothing on
its own — say "respiratory compliance, how stiff the lungs are". Same for file
names, parameter names and equations. The reader is an anaesthetist, not a
Python programmer, and a term that is obvious to whoever wrote the line is
often opaque to whoever has to judge it.

**Lead with the finding, not the method.** What changed, what it means, what is
still wrong. The working — sweeps, intermediate numbers, what was ruled out —
belongs in `HANDOVER.md` and `handover_numbers.py`, where it is checkable, not
in the reply, where it is just volume.

## Commits

`.githooks/pre-commit` runs `build_page.py --check`, `check_sources.py
--check`, `test_parity.py` and `test_validation.py`, and blocks on failure. It takes 5-15 minutes; run commits in the background and
wait. `./setup-hooks.sh` once per clone. `git commit --no-verify` exists but
say in the message which benchmark is broken and why.

`protocol/predictions.py`, `handover_numbers.py` and `buccal_numbers.py` are
deliberately NOT in the hook. They check claims about the world, not invariants of the code, and are
expected to move when the model is corrected — the point is that they must not
move silently.

## Where things are

| path | what |
|---|---|
| `apnoea_core.py` | the model. Reference implementation |
| `bloodgas.py` | O2/CO2 dissociation, acid-base. Read its PROVENANCE header |
| `model.js` | JavaScript port. Must track the Python |
| `test_validation.py` | benchmarks as pass/fail. The arbiter |
| `test_parity.py` | the two implementations against each other |
| `handover_numbers.py` | regenerates the numbers quoted in HANDOVER |
| `buccal_numbers.py` | regenerates the buccal-oxygen numbers, and the audit of `editorial.md` |
| `protocol/` | the three-way study, its predictions and its evidence map |
| `sources_registry.py` | WHICH PAPERS HAVE BEEN READ. The only place that fact is written |
| `check_sources.py` | regenerates README's read-status table from it; `--check` in the hook |
| `variant_cost.py` | runs the suite against an experimental lung-volume form |
| `patches/` | written but unapplied changes, with the reason in HANDOVER |
