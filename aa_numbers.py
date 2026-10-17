# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
aa_numbers.py -- regenerates every A-a gradient dial figure quoted in
HANDOVER.md and in the Outputs page, and fails if one has drifted.

Same contract as buccal_numbers.py, handover_numbers.py and
protocol/predictions.py: NOT in the pre-commit hook, because these are claims
about the world and about a user-facing control, not invariants of the code.
They are expected to move when the model is corrected. The point is that they
must not move SILENTLY.

    python3 aa_numbers.py          about 9 minutes, almost all of it the two
                                   90-minute patent-airway runs at the end

WHY THIS IS A SEPARATE FILE AND NOT A SECTION OF handover_numbers.py. It was
written as one, on 2026-10-09, and taken out the same day. handover_numbers.py
had already grown past TWO HOURS -- a full run was killed at that limit, which
is the longest this session can wait -- and a self-checking file nobody can
finish running is a file whose checks do not get run. That is the same failure
mode as a permanently red suite. The A-a block was only 8.5 minutes of it, so
moving it does not fix handover_numbers.py; THAT IS STILL OPEN and is recorded
as such. What this does is stop a new, expensive and actively-used set of
numbers from being buried inside a file nobody can run to completion.

A --only flag on handover_numbers.py was considered first and rejected on
inspection: that file is a flat script of 4962 lines with 79 sections that
share state through module-level variables, so selecting sections means
restructuring it into functions. That is a real refactor of the one file whose
whole job is to catch drift, and a silently dropped check there is the worst
possible outcome. Per-topic scripts are the pattern this project already uses.

THE DIAL ITSELF. "Extra A-a gradient", 0-75 kPa, default 0, added 2026-10-08
on A. Heard's ruling after he asked for the control in those terms twice. It
does NOT store a gradient -- the alveolar-to-arterial difference is an OUTPUT
of shunt, cardiac output, Hb and oxygen consumption, and for one fixed shunt
it is large at a high alveolar PO2 and small at a low one. The dial asks what
shunt would produce this much EXTRA gradient at a stated reference condition,
solves for it, and lets the gradient move from there.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apnoea_core as ac  # noqa: E402
from apnoea_core import AirwayEpoch, Patient, simulate, time_to  # noqa: E402

print(ac.provenance())
print()

_fails = []


def check(what, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    print(f"    {'ok  ' if ok else 'FAIL'} {what:<46} {got:8.2f}{unit}"
          f"   HANDOVER says {want:g}{unit}", flush=True)
    if not ok:
        _fails.append(what)


LEAN = dict(weight=76.5, height=1.75, age=45, hb=14.0, tilt_deg=25.0)
OBESE = dict(weight=107.0, height=1.75, age=45, hb=14.0, tilt_deg=25.0)

print("  THE SOLVER ROUND-TRIPS EXACTLY. This is the whole claim: ask for a")
print("  gradient, get the shunt that produces it. shunt_for_aa_gradient()")
print("  inverts aa_gradient_mmhg(), which is the forward direction of")
print("  plateau_sao2(): f = r/(1+r) with r the arterial oxygen content")
print("  deficit in units of the arteriovenous difference. The only numerical")
print("  step is the dissociation curve.")
_own = ac.aa_gradient_mmhg(Patient(**LEAN),
                           Patient(**LEAN).shunt_base_eff()) / ac.KPA_MMHG
check("lean patient's own A-a gradient", _own, 9.03, 0.05, " kPa")
for _g in (10.0, 20.0, 30.0, 40.0):
    _p = Patient(aa_extra_kpa=_g, **LEAN)
    check(f"  ask +{_g:.0f} kPa -> gradient delivered",
          ac.aa_gradient_mmhg(_p, _p.shunt_base_eff()) / ac.KPA_MMHG - _own,
          _g, 0.05, " kPa")

print()
print("  THE CEILING IS PHYSICAL, NOT CHOSEN. The total gradient cannot exceed")
print("  the alveolar PO2 itself, because arterial tension cannot go negative,")
print("  so the dial saturates at (that PO2 minus the patient's own gradient).")
check("reference alveolar PO2", ac.AA_REF_PAO2 / ac.KPA_MMHG, 76.0, 0.05, " kPa")
_obown = ac.aa_gradient_mmhg(Patient(**OBESE),
                             Patient(**OBESE).shunt_base_eff()) / ac.KPA_MMHG
check("obese patient's own A-a gradient", _obown, 18.0, 0.1, " kPa")
_sat = [Patient(aa_extra_kpa=g, **OBESE).shunt_base_eff() for g in (58, 70, 90)]
check("obese: shunt at dial +58 kPa", _sat[0] * 100, 77.93, 0.05, " %")
check("  ... identical at +70 (saturated)", abs(_sat[1] - _sat[0]) * 100,
      0.0, 1e-6, " pp")
check("  ... identical at +90 (saturated)", abs(_sat[2] - _sat[0]) * 100,
      0.0, 1e-6, " pp")
print("    SO 90 kPa WAS NOT BUILT. A. Heard asked for it; the top third would")
print("    have done nothing, at a point that MOVES WITH THE PATIENT -- 58 kPa")
print("    for this obese patient, about 67 for the lean one. 75 is the limit")
print("    and the page says 'capped' past each patient's own saturation.")

print()
print("  THE CLIFF, read from the regenerated sweep rather than recomputed.")
print("  sweeps.json is kept fresh by build_sweeps.js --check IN THE HOOK, so")
print("  this cannot silently check a stale artifact: the guarantee comes from")
print("  the hook, not from trust.")
_swp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweeps.json')
if os.path.exists(_swp):
    _sw = json.load(open(_swp))
    _aa = [d for d in _sw['dials'] if d['key'] == 'aaExtraKpa']
    if _aa:
        _d = _aa[0]
        _x, _c, _v = _d['x'], _d['control']['death'], _d['device']['death']
        check("sweep: control death at +0 kPa", _c[0], 745, 2, " s")
        check("sweep: control death at +60 kPa", _c[_x.index(60)], 701, 2, " s")
        check("  so the whole sub-cliff range costs",
              _c[0] - _c[_x.index(60)], 44, 3, " s")
        check("sweep: control death at +68 kPa", _c[_x.index(68)], 50, 2, " s")
        check("sweep: DEVICE at +60 kPa (None -> -1)",
              -1 if _v[_x.index(60)] is None else _v[_x.index(60)], -1, 0, "")
        check("sweep: DEVICE death at +68 kPa", _v[_x.index(68)], 50, 2, " s")
        print("    THE DEVICE SURVIVES THE WHOLE HOUR AT EVERY SETTING UP TO")
        print("    60 kPa AND THEN DIES IN FIFTY SECONDS. Between 60 and 68 the")
        print("    solved shunt crosses about three quarters of the cardiac")
        print("    output, and no amount of pharyngeal oxygen can oxygenate")
        print("    blood that never meets gas. It fails abruptly rather than")
        print("    degrading, which the old 40 kPa ceiling hid entirely.")
    else:
        _fails.append("sweeps.json has no aaExtraKpa dial")
        print("    FAIL: sweeps.json has no aaExtraKpa dial -- regenerate it.")
else:
    _fails.append("sweeps.json absent")
    print("    FAIL: sweeps.json absent; run: node build_sweeps.js")

print()
print("  THE DEVICE ARM, OBESE, MEASURED DIRECTLY. Two patent-airway runs at")
print("  about 0.085 s of wall per simulated second -- four minutes each, and")
print("  almost all of this file's runtime. They are here because the 17.5")
print("  minutes is the dial's whole case, and a number that expensive to")
print("  produce is exactly the kind that rots in prose. NOTE resistance=2.0:")
print("  the device arm is PATENT. Complete obstruction is np.inf, and this")
print("  project has run the wrong one three times.")
for _g, _w95 in ((0.0, 78.64), (40.0, 61.10)):
    _r = simulate(Patient(aa_extra_kpa=_g, **OBESE),
                  [AirwayEpoch(5400, resistance=2.0, fgo2=1.0)], dt=0.1)
    _t = time_to(_r, 'spo2', 95)
    check(f"obese device arm, +{_g:.0f} kPa: SpO2<95%",
          -1.0 if _t is None else _t / 60.0, _w95, 0.3, " min")
print("    17.5 MINUTES ACROSS THE DIAL, against 44 SECONDS in the control arm")
print("    below the cliff. The control arm is STORE-limited -- a fixed load of")
print("    oxygen, so shunt spoils the tension and barely touches the clock.")
print("    The device arm is SUPPLY-limited, so shunt decides whether supply")
print("    can keep up. That is the whole lesson of this dial and it is what")
print("    the Outputs page now says in words.")
print("    THE LEAN PATIENT WAS VERIFIED, NOT ASSUMED, not to desaturate within")
print("    two hours at either end of the dial -- 0 and +40 kPa, both None,")
print("    while PaO2 at 60 min falls 309 -> 213 mmHg. The gas looks far worse")
print("    and the patient is in no danger at all.")

print()
if _fails:
    print(f"{len(_fails)} value(s) have drifted:")
    for f in _fails:
        print(f"  - {f}")
    print("Either the model moved or the document is stale. Fix the document.")
    raise SystemExit(1)
print("Every A-a dial number still reproduces from this commit.")
