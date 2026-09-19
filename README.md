# Apnoeic oxygenation model

A computational model of gas exchange during apnoea after intravenous
induction, built to quantify the effect of buccal oxygen delivery and to
compare a patent airway against a completely obstructed one.

Two implementations that must agree to within 1%: `apnoea_core.py` is the
reference, `model.js` is the browser port. `test_parity.py` holds them to it.

---

## Three ways in

**1. Look at it — no installation.**
Open `airway_scenario.html` in any browser. Two patients side by side, patent
against obstructed, with lungs, trachea and a head that goes blue on
deoxygenated haemoglobin rather than on saturation. Sliders for preoxygenation,
haemoglobin, tilt, buccal oxygen. Nothing is fetched at runtime except the web
fonts, so it works offline with plainer typography.

**2. Run the model.**

```
pip install -r requirements.txt      # numpy, scipy, matplotlib
python3 run.py
```

`run.py` has a PATIENT block and an AIRWAY block at the top. Edit them and
re-run; everything below is plumbing.

**3. Check that it still passes.**

```
python3 test_validation.py           # the benchmarks, pass/fail
python3 test_parity.py               # Python against JavaScript
python3 handover_numbers.py          # every number quoted in HANDOVER.md
python3 protocol/predictions.py      # every number quoted in the study protocol
```

The first two take several minutes. They were green at the commit in
`PROVENANCE.txt`.

---

## What is validated, and what is not

Read this before quoting anything the model produces.

**Benchmarked against clinical measurement**

| source | what it pins |
|---|---|
| Toner 2019 | buccal oxygen, time to desaturation |
| Heard 2017 | apnoeic oxygenation, obstructed |
| O'Loughlin 2020 | desaturation timing |
| Stock 1989 | PaCO2 rise, obstructed |
| Moreault 2021 | the pressure limb |
| Lane / Ramkumar / Altermatt / Dixon | positioning |
| Sci Rep 2023 (n=91) | cardiac output |
| Varat 1972 | the circulation's response to anaemia |

**Compared against another simulator, not against patients**

Laviola 2020 and the 2026 jet paper are the Nottingham model, not measurement.
Every "model comparator" row in the suite traces back to that one simulator —
they are not six independent confirmations, and the suite labels them as such.

**The one open defect**

Arterial CO2 is too sensitive to ventilation/perfusion spread. Tokics 1996
measures log QSD in anaesthetised paralysed adults at 0.80–1.18; the model runs
at 0.70, below measurement, and passes the Stock benchmark only because of
that. The mechanism is the arterial-to-alveolar CO2 gap, whose size depends on
the curvature of the CO2 dissociation curve — and that curve carries a red-cell
correction written from memory rather than from the source paper. **Obstructed
CO2 numbers should be treated as unvalidated** until that is settled.

**A weakness nothing currently tests**

The patent-airway PaCO2 slope between 1 and 5 minutes is 1.70 mmHg/min against
a classical 3–5. No benchmark asserts it, so the suite stays green.

**Not modelled at all**

Jet insufflation. There is no bolus delivery and no outflow path — gas can only
enter the lung. The design decision for it is recorded in HANDOVER but nothing
is built.

`HANDOVER.md` opens with a dated **Current state** section that is authoritative
where the rest of the file disagrees with it, including a table of superseded
claims still present in the older text.

---

## What is in the box

| path | what |
|---|---|
| `airway_scenario.html` | the visualisation. Open it directly |
| `apnoea_core.py` | the model. Reference implementation |
| `bloodgas.py` | O2/CO2 dissociation and acid-base. Read its PROVENANCE header |
| `model.js` | the JavaScript port, embedded into the page by `build_page.py` |
| `run.py` | simplest way to drive the model |
| `test_validation.py` | the benchmarks. The arbiter |
| `test_parity.py` | the two implementations against each other |
| `handover_numbers.py` | regenerates every number quoted in HANDOVER |
| `HANDOVER.md` | the full history: what was tried, what failed, what was retracted |
| `CLAUDE.md` | the working rules, each one written after it was broken |
| `protocol/` | the three-way study, its predictions and its evidence map |
| `patches/` | written but deliberately unapplied changes, with reasons in HANDOVER |
| `LICENSE` | terms of use. All rights reserved |
| `CITATION.cff` | how to cite it, machine readable |
| `editorial.md` | draft prose on the clinical framing. Not peer reviewed |

---

## Two conventions worth knowing

**Numbers in prose rot; numbers in scripts do not.** Anything quoted in
HANDOVER is regenerable by `handover_numbers.py`, which fails if a value has
drifted. Two comparator rows are named there as *not* reproducible because their
configuration was never recorded — that is deliberate, and it is the cautionary
example the script exists to prevent repeating.

**Parameters are not tuned to pass benchmarks.** Several changes that would make
a failing benchmark pass are recorded in HANDOVER as refused, with the
reasoning, because they had no mechanism behind them. A correction that makes a
benchmark worse is recorded as information rather than compensated for
elsewhere.

---

## Provenance and terms

Copyright (c) 2026 A. M. B. Heard. All rights reserved. This is unpublished
research software.

Reading the source, running the model and evaluating it privately need no
permission. **Copying, redistributing, or using its equations, parameters,
calibrations, benchmarks or figures in any publication, thesis, presentation or
product requires the author's prior written permission.** `LICENSE` sets out
the terms in full; `CITATION.cff` says how to cite it once permission is given.

It is a research model, not a medical device. It must not be used to guide the
care of any patient.

`PROVENANCE.txt` carries the commit a package was built from, and any script
can print which model file it actually loaded:

```python
import apnoea_core; print(apnoea_core.provenance())
```
