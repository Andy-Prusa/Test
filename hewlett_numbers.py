# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
hewlett_numbers.py -- regenerates every number quoted from Hewlett 1974 part
III, and fails if one has drifted.

Same contract as handover_numbers.py, buccal_numbers.py, aa_numbers.py and
frc_level_numbers.py: NOT in the pre-commit hook, because these are claims
about the world rather than invariants of the code. Fast -- a few seconds,
nothing is simulated.

    python3 hewlett_numbers.py

THE SOURCE. Hewlett AM, Hulands GH, Nunn JF, Milledge JS. "Functional residual
capacity during anaesthesia III: Artificial ventilation." Br J Anaesth
1974;46:495-502. Read in full from upload 2026-10-13. Published data only.

WHY IT MATTERS. It is the FIRST source this project holds with PAIRED awake and
anaesthetised FRC in the SAME patients, and its BMI range 18.6-30.8 is the lean
gap that Pelosi (from BMI 20) and Damia (morbidly obese) both leave as
extrapolation. It therefore speaks directly to the open question of whether the
anaesthetised lung volume should be derived from the awake one.

AND ITS LIMIT, WHICH IS NOT SMALL. By the Table II footnote only patients 2, 8
and 9 were male. Ten of thirteen were FEMALE and this model is male by ruling,
so ABSOLUTE volumes are confounded. The correlation structure is not confounded
the same way, and that is what the load-bearing findings below rest on.
"""
import dataclasses

import numpy as np

import apnoea_core as A
from apnoea_core import Patient

print(A.provenance())
print()

# Hewlett 1974 part III, TABLE II, transcribed from the page.
# pt, age y, height cm, weight kg, FRC awake l, FRC anaes l, % fall,
# (A-a)PO2 awake mmHg, (A-a)PO2 anaesthetised mmHg.  Volumes BTPS.
T2 = [
    (1,  54, 160, 74.5, 1.860, 1.893,  -1.8,  54.7,  83.9),
    (2,  64, 165, 71.5, 1.618, 1.129,  30.2,  75.0, 126.9),
    (3,  22, 169, 82.0, 1.241, 0.944,  23.9,  50.5, 104.4),
    (4,  35, 169, 84.5, 2.138, 2.118,   3.4,  42.0,  42.1),
    (5,  62, 154, 54.5, 1.206, 0.994,  17.6, 106.5, 134.7),
    (6,  43, 175, 77.0, 2.079, 1.529,  26.5,  38.0,  85.4),
    (7,  34, 173, 75.5, 2.271, 1.882,  17.1,  34.5,  30.9),
    (8,  59, 164, 77.5, 3.827, 2.952,  22.9,  71.5, 127.3),
    (9,  41, 174, 74.5, 2.259, 2.092,   7.4,  44.3,  75.1),
    (10, 51, 161, 55.0, 2.318, 1.704,  26.5,  62.2,  98.5),
    (11, 26, 172, 55.0, 1.925, 1.943,  -0.9,  25.6,  37.2),
    (12, 23, 170, 56.0, 2.189, 2.354,  -7.5,  21.4,   9.2),
    (13, 27, 156, 75.0, 1.343, 0.880,  34.4,  11.5,  81.1),
]
MALE = {2, 8, 9}        # Table II footnote

AW = np.array([r[4] for r in T2])
AN = np.array([r[5] for r in T2])
BMI = np.array([r[3] / (r[2] / 100.0) ** 2 for r in T2])
AGE = np.array([float(r[1]) for r in T2])
PCT = np.array([r[6] for r in T2])
DAA = np.array([r[8] - r[7] for r in T2])
FAILED = []


def check(name, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    if not ok:
        FAILED.append(name)
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<50}{got:>9.3f}{unit}"
          f"   recorded {want}{unit}")


def absolute():
    @dataclasses.dataclass
    class V(Patient):
        frc_anaes_absolute = True
    return V


print("1. THE TRANSCRIPTION, VALIDATED TWO INDEPENDENT WAYS. Table II is printed")
print("   ROTATED and was transcribed by eye, so it is checked by whether the")
print("   paper's OWN published statistics fall out of it.")
check("mean awake supine FRC [paper: 2.021]", AW.mean(), 2.021, 0.001, " l")
check("mean anaesthetised FRC [paper: 1.724]", AN.mean(), 1.724, 0.001, " l")
check("mean fall [paper: 297 mL]", 1000 * (AW - AN).mean(), 297.0, 0.6, " mL")
check("mean % fall [paper: 15.4]", PCT.mean(), 15.4, 0.05, " %")
_sl, _ic = np.polyfit(PCT, DAA, 1)
check("A-a regression SLOPE [paper: 1.47]", _sl, 1.466, 0.002)
check("A-a regression INTERCEPT [paper: 8.2]", _ic, 8.17, 0.02, " mmHg")
check("A-a regression r [paper: 0.790]", np.corrcoef(PCT, DAA)[0, 1], 0.790, 0.002)
check("% fall vs age, r [paper: 0.289]", np.corrcoef(AGE, PCT)[0, 1], 0.289, 0.001)
print("   Four printed statistics AND his published regression recovered from")
print("   the transcribed cells. The table is read correctly.")
print()
print("   ONE THING THAT DOES NOT REPRODUCE, recorded rather than explained")
print("   away. He prints a correlation of the FRC change with weight/height")
print("   ratio of 0.415. Refitting gives:")
WH = np.array([r[3] / (r[2] / 100.0) for r in T2])
check("   wt/ht vs PERCENTAGE change [paper: 0.415]",
      np.corrcoef(WH, PCT)[0, 1], 0.327, 0.001)
check("   wt/ht vs ABSOLUTE change [paper: 0.415]",
      np.corrcoef(WH, AW - AN)[0, 1], 0.284, 0.001)
check("   BMI vs percentage change (nearest candidate)",
      np.corrcoef(BMI, PCT)[0, 1], 0.390, 0.001)
print("   Using his PRINTED percentage column the age figure reproduces EXACTLY,")
print("   which fixes what 'change in FRC' means; on that same definition his wt/ht")
print("   figure does not. BMI gives 0.390, the nearest candidate, and is still")
print("   not 0.415. UNRESOLVED -- his 0.415 is not to be quoted.")
print()

print("2. THE LOAD-BEARING FINDING: WHAT PREDICTS THE ANAESTHETISED LUNG VOLUME")
print("   IN HIS PAIRED DATA. This is the first direct evidence the project has")
print("   on whether the anaesthetised level should come from the awake lung.")
for _lbl, _x, _rec in (("the patient's own AWAKE FRC", AW, 0.894),
                       ("BMI", BMI, -0.167),
                       ("height", np.array([r[2] / 100.0 for r in T2]), 0.380),
                       ("age", AGE, 0.029)):
    check(f"anaesthetised FRC vs {_lbl}", np.corrcoef(_x, AN)[0, 1], _rec, 0.002)
print("   The awake volume explains about 80% of the variance; BMI about 3%.")
print()
print("   WHY, visible in the raw table -- his five patients between BMI 28")
print("   and 31, anaesthetised FRC in litres:")
_band = sorted([(r[0], r[3] / (r[2] / 100.0) ** 2, r[5]) for r in T2
                if 28 <= r[3] / (r[2] / 100.0) ** 2 <= 31], key=lambda t: t[2])
for _pt, _b, _v in _band:
    print(f"       pt {_pt:>2}   BMI {_b:.1f}   {_v:.3f} l")
_vs = [v for _, _, v in _band]
check("   spread at essentially one BMI, as a ratio", max(_vs) / min(_vs), 3.355, 0.005, " x")
print("   A curve keyed on BMI alone cannot produce that spread. The awake")
print("   volume can, because it already contains whatever makes them differ.")
print()
print("   THE HONEST REBUTTAL, and it is a real one: his BMI range is 18.6-30.8,")
print("   so BMI has little room to show what it can do. Over Pelosi's 20-66 it")
print("   would explain far more. This result bears on the LEAN end, which is")
print("   where Toner, Berthoud and Frumin sit, and not on the obese end.")
print()

print("3. THE MODEL AGAINST HIM, and the sex confound in plain numbers.")
_e_aw, _e_sh, _e_dc = [], [], []
for _pt, _age, _ht, _wt, _fa, _fn, *_ in T2:
    _g = dict(weight=_wt, height=_ht / 100.0, age=_age, tilt_deg=0)
    _e_aw.append(Patient(**_g).frc_awake() - _fa * 1000)
    _e_sh.append(Patient(**_g).frc_anaes() - _fn * 1000)
    _e_dc.append(absolute()(**_g).frc_anaes() - _fn * 1000)
check("awake: model - measured, mean bias", float(np.mean(_e_aw)), 553.0, 1.0, " mL")
check("anaes SHIPPED: mean bias", float(np.mean(_e_sh)), 123.0, 1.0, " mL")
check("anaes DE-COUPLED: mean bias", float(np.mean(_e_dc)), 73.0, 1.0, " mL")
check("anaes SHIPPED: mean absolute error", float(np.mean(np.abs(_e_sh))), 518.0, 1.0, " mL")
check("anaes DE-COUPLED: mean absolute error", float(np.mean(np.abs(_e_dc))), 508.0, 1.0, " mL")
print("   The model's AWAKE volume runs 553 mL high, which is what a male model")
print("   measured against a 10/13 female cohort should do. The two anaesthetised")
print("   forms differ by 10 mL of mean absolute error -- FAR inside that")
print("   confound. ON ABSOLUTE LEVEL THIS COHORT CANNOT DISCRIMINATE THEM, and")
print("   section 2 above, which is a correlation, is the part that can.")
print()

print("4. THE MODEL'S EFFECTIVE INDUCTION DROP vs BMI (1.70 m, age 40, supine).")
print("   frc_drop is 400 mL flat, but Pelosi's BMI shape is applied after it:")
print(f"   {'BMI':>5}{'awake':>9}{'anaes':>9}{'drop mL':>10}{'drop %':>9}")
for _b, _rec in ((19, 14.1), (22, 14.6), (25, 26.7), (28, 35.9), (31, 42.8)):
    _p = Patient(weight=_b * 1.70 ** 2, height=1.70, age=40, tilt_deg=0)
    _a, _n = _p.frc_awake(), _p.frc_anaes()
    _pc = 100.0 * (_a - _n) / _a
    if abs(_pc - _rec) > 0.1:
        FAILED.append(f"effective drop at BMI {_b}")
    print(f"   {_b:>5}{_a:>9.0f}{_n:>9.0f}{_a - _n:>10.0f}{_pc:>8.1f}%")
print("   HEWLETT MEASURED 15.4% as the mean of a cohort whose mean BMI is 25.4,")
print("   where the model gives about 27%. The model's drop is right at the lean")
print("   end and roughly doubles his by BMI 28. That is NOT frc_drop -- a flat")
print("   400 mL is only 103 mL biased against him -- it is Pelosi's shape")
print("   steepening the fall after it. Pelosi and Hewlett disagree here and")
print("   BOTH are published. That is a conflict to record, not an error to")
print("   patch, and NOTHING here licenses moving a parameter to split them.")
print()

if FAILED:
    print(f"{len(FAILED)} value(s) have drifted:")
    for f in FAILED:
        print(f"  - {f}")
    raise SystemExit(1)
print("Every Hewlett number still reproduces from this commit.")
