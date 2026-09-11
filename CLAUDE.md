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

**Numbers in markdown rot. Numbers in scripts do not.** Anything quoted in
HANDOVER should be regenerable by `python3 handover_numbers.py`, which fails if
a value has drifted. If you add a table to HANDOVER, add it there too. The
Ellis comparator rows are the cautionary example: recorded, never scripted, and
now unreproducible.

**Do not tune a parameter to pass a benchmark.** This has been proposed and
refused four times, each recorded in HANDOVER with the reasoning. A change
needs a mechanism, not a fit. If a correction makes a benchmark WORSE, that is
information — record it, do not reach for a compensating parameter.

## Commits

`.githooks/pre-commit` runs `test_validation.py` and `test_parity.py` and
blocks on failure. It takes 5-15 minutes; run commits in the background and
wait. `./setup-hooks.sh` once per clone. `git commit --no-verify` exists but
say in the message which benchmark is broken and why.

`protocol/predictions.py` and `handover_numbers.py` are deliberately NOT in the
hook. They check claims about the world, not invariants of the code, and are
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
| `protocol/` | the three-way study, its predictions and its evidence map |
| `patches/` | written but unapplied changes, with the reason in HANDOVER |
