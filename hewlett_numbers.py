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

PART I (same authors with Minty, Br J Anaesth 1974;46:479-85) was read in full
from upload the same day. It carries NO patient data -- it is the helium-dilution
apparatus and its accuracy -- but its Table I is what lets section 5 below decide
how much weight part III's scatter can bear, and it changes the answer in part
III's favour.

WHY IT MATTERS. It is the FIRST source this project holds with PAIRED awake and
anaesthetised FRC in the SAME patients, and its BMI range 19.1-32.5 is the lean
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

# Hewlett 1974 part III, TABLE II.
# CORRECTED 2026-10-13, SAME DAY, BY AN ADVERSARIAL RE-READ. The first
# transcription of this table, made by eye from the rotated page, had SEVEN
# cells wrong -- five weights and two heights, including a one-row slip of the
# weight column across patients 4-7 and a value (84.5 kg) that is not in the
# table at all. Every other cell, both FRC columns included, was right.
# The error was CAUGHT BY THE PAPER'S OWN INTERNAL CHECK: Hewlett prints a
# weight/height correlation of 0.415, the first transcription gave 0.327, and
# the corrected one gives 0.410. That discrepancy was recorded as "unresolved"
# for several hours when it was in fact the signal that the table was misread.
# Verified against the PDF text layer with `pdftotext -layout -f 3 -l 3`.
# pt, age y, height cm, weight kg, FRC awake l, FRC anaes l, % fall,
# (A-a)PO2 awake mmHg, (A-a)PO2 anaesthetised mmHg.  Volumes BTPS.
T2 = [
    (1,  54, 160, 74.5, 1.860, 1.893,  -1.8,  54.7,  83.9),
    (2,  64, 165, 71.5, 1.618, 1.129,  30.2,  75.0, 126.9),
    (3,  22, 169, 82.0, 1.241, 0.944,  23.9,  50.5, 104.4),
    (4,  35, 169, 54.5, 2.138, 2.118,   3.4,  42.0,  42.1),
    (5,  62, 154, 77.0, 1.206, 0.994,  17.6, 106.5, 134.7),
    (6,  43, 175, 75.5, 2.079, 1.529,  26.5,  38.0,  85.4),
    (7,  34, 160, 53.5, 2.271, 1.882,  17.1,  34.5,  30.9),
    (8,  59, 164, 77.5, 3.827, 2.952,  22.9,  71.5, 127.3),
    (9,  41, 174, 74.5, 2.259, 2.092,   7.4,  44.3,  75.1),
    (10, 51, 161, 55.0, 2.318, 1.704,  26.5,  62.2,  98.5),
    (11, 26, 172, 61.0, 1.925, 1.943,  -0.9,  25.6,  37.2),
    (12, 23, 156, 56.0, 2.189, 2.354,  -7.5,  21.4,   9.2),
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
print("   THE CHECK THAT CAUGHT A MISREADING. He prints a correlation of the")
print("   FRC change with weight/height ratio of 0.415. The FIRST transcription")
print("   of this table gave 0.327 and that was logged as an unresolved")
print("   discrepancy -- when it was in fact the signal that seven height and")
print("   weight cells had been misread. Corrected, it reproduces:")
WH = np.array([r[3] / (r[2] / 100.0) for r in T2])
check("   wt/ht vs PERCENTAGE change [paper: 0.415]",
      np.corrcoef(WH, PCT)[0, 1], 0.410, 0.001)
check("   wt/ht vs ABSOLUTE change [paper: 0.415]",
      np.corrcoef(WH, AW - AN)[0, 1], 0.282, 0.001)
check("   BMI vs percentage change (nearest candidate)",
      np.corrcoef(BMI, PCT)[0, 1], 0.385, 0.001)
print("   0.410 against his printed 0.415, on the same definition of 'change in")
print("   FRC' that his age figure pins. NOTHING IS NOW UNRESOLVED IN THIS TABLE,")
print("   and the lesson is that a paper's own internal statistic is a better")
print("   transcription check than re-reading the page.")
print()

print("2. THE LOAD-BEARING FINDING: WHAT PREDICTS THE ANAESTHETISED LUNG VOLUME")
print("   IN HIS PAIRED DATA. This is the first direct evidence the project has")
print("   on whether the anaesthetised level should come from the awake lung.")
for _lbl, _x, _rec in (("the patient's own AWAKE FRC", AW, 0.894),
                       ("BMI", BMI, -0.434),
                       ("height", np.array([r[2] / 100.0 for r in T2]), 0.163),
                       ("age", AGE, 0.029)):
    check(f"anaesthetised FRC vs {_lbl}", np.corrcoef(_x, AN)[0, 1], _rec, 0.002)
print("   The awake volume explains about 80% of the variance; BMI about 19%.")
print("   (Before the transcription fix BMI appeared to explain 3%. The")
print("   correction QUADRUPLES BMI's share and narrows the gap, but does not")
print("   close it: awake FRC remains far the stronger predictor, and the")
print("   headline r = +0.894 is untouched because both FRC columns were right.)")
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
print("   THE HONEST REBUTTAL, and it is a real one: his BMI range is 19.1-32.5,")
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
check("awake: model - measured, mean bias", float(np.mean(_e_aw)), 510.0, 1.0, " mL")
check("anaes SHIPPED: mean bias", float(np.mean(_e_sh)), 62.0, 1.0, " mL")
check("anaes DE-COUPLED: mean bias", float(np.mean(_e_dc)), -129.0, 1.0, " mL")
check("anaes SHIPPED: mean absolute error", float(np.mean(np.abs(_e_sh))), 467.0, 1.0, " mL")
check("anaes DE-COUPLED: mean absolute error", float(np.mean(np.abs(_e_dc))), 430.0, 1.0, " mL")
print("   The model's AWAKE volume runs 510 mL high, which is what a male model")
print("   measured against a 10/13 female cohort should do. The two anaesthetised")
print("   forms differ by 37 mL of mean absolute error -- FAR inside that")
print("   confound. ON ABSOLUTE LEVEL THIS COHORT CANNOT DISCRIMINATE THEM, and")
print("   section 2 above, which is a correlation, is the part that can.")
print()

print("4. THE MODEL'S EFFECTIVE INDUCTION DROP vs BMI (1.70 m, age 40, supine).")
print("   frc_drop is 400 mL flat, but Pelosi's BMI shape is applied after it:")
print(f"   {'BMI':>5}{'awake':>9}{'anaes':>9}{'drop mL':>10}{'drop %':>9}")
for _b, _rec in ((19, 14.1), (22, 14.6), (25, 28.5), (28, 39.2), (31, 47.2)):
    _p = Patient(weight=_b * 1.70 ** 2, height=1.70, age=40, tilt_deg=0)
    _a, _n = _p.frc_awake(), _p.frc_anaes()
    _pc = 100.0 * (_a - _n) / _a
    if abs(_pc - _rec) > 0.1:
        FAILED.append(f"effective drop at BMI {_b}")
    print(f"   {_b:>5}{_a:>9.0f}{_n:>9.0f}{_a - _n:>10.0f}{_pc:>8.1f}%")
print("   THOSE FIGURES STEEPENED AT THE OFFSET RULING OF 2026-10-15 -- at the")
print("   retired 0.6882 average they were 26.7, 35.9 and 42.8%. Lowering the")
print("   curve made the model's effective drop LARGER, so the ruling moved this")
print("   disagreement in the wrong direction. Recorded, not compensated.")
print()
print("   HEWLETT MEASURED 15.4% as the mean of a cohort whose mean BMI is 25.4,")
print("   where the model gives about 27%. The model's drop is right at the lean")
print("   end and roughly doubles his by BMI 28. That is NOT frc_drop -- a flat")
print("   400 mL is only 103 mL biased against him -- it is Pelosi's shape")
print("   steepening the fall after it. Pelosi and Hewlett disagree here and")
print("   BOTH are published. That is a conflict to record, not an error to")
print("   patch, and NOTHING here licenses moving a parameter to split them.")
print()

print("5. HOW MUCH OF PART III'S SCATTER IS THE INSTRUMENT? Part I measured a")
print("   MODEL LUNG of known volume 4.528 l by water displacement, through the")
print("   same rig, in both of its modes. Its Table I:")
print("                        n   mean l   SD(indiv)   mean error l")
for _lbl, _n, _m, _sd, _e in (("spontaneous 1", 10, 4.563, 0.046, -0.035),
                              ("spontaneous 2",  9, 4.559, 0.060, -0.031),
                              ("artificial 1",  10, 4.511, 0.159, -0.017),
                              ("artificial 2",  10, 4.529, 0.107, -0.001)):
    print(f"     {_lbl:<16}{_n:>3}{_m:>9.3f}{_sd:>12.3f}{_e:>15.3f}")
# CORRECTED 2026-10-13 BY AN ADVERSARIAL VERIFIER. Part I's SDs are for a
# SINGLE measurement. Table II's cells are MEANS OF DUPLICATES -- the Methods
# say "a duplicate pre-induction FRC measurement was made" and "A duplicate FRC
# measurement was made 9-22 min after the first", and the table itself prints
# "FRC first", "FRC second", "FRC mean". The error on a mean of two is SD/sqrt2.
# The first version of this section fed in the single-measurement SDs, which
# OVERSTATED the instrument's noise and so overstated the attenuation it causes.
SD1_SPONT = (0.046 + 0.060) / 2.0     # part I, ONE measurement, spontaneous
SD1_ARTIF = (0.159 + 0.107) / 2.0     # part I, ONE measurement, ventilated
SD_SPONT = SD1_SPONT / np.sqrt(2.0)   # part III's AWAKE cells, means of two
SD_ARTIF = SD1_ARTIF / np.sqrt(2.0)   # part III's ANAESTHETISED cells
check("single-measurement SD, spontaneous mode", SD1_SPONT, 0.053, 0.0005, " l")
check("single-measurement SD, ventilated mode", SD1_ARTIF, 0.133, 0.0005, " l")
check("SD of a MEAN OF TWO, spontaneous", SD_SPONT, 0.0375, 0.0005, " l")
check("SD of a MEAN OF TWO, ventilated", SD_ARTIF, 0.0940, 0.0005, " l")
print("   The anaesthetised numbers are 2.5x NOISIER than the awake ones, which")
print("   part I attributes to about 1.5 l of extra apparatus in the ventilated")
print("   circuit. That asymmetry matters three times over:")
print()
_SD_D = float(np.hypot(SD_SPONT, SD_ARTIF))
check("   SD of the awake-to-anaesthetised DIFFERENCE", _SD_D, 0.101, 0.001, " l")
print("   (a) THE THREE PATIENTS WHOSE FRC DID NOT FALL are patients 1, 11 and 12.")
for _pt, _a, _n in ((1, 1.860, 1.893), (11, 1.925, 1.943), (12, 2.189, 2.354)):
    print(f"       pt {_pt:>2}: {1000 * (_n - _a):+6.0f} mL = {(_n - _a) / _SD_D:+.2f} SD of method noise")
print("       All three are inside about one SD of the instrument. They are")
print("       consistent with NO CHANGE mismeasured, NOT with anaesthesia adding")
print("       gas -- which is the reading a mandatory induction drop would need")
print("       to explain away, and now does not have to.")
print()
print("   (b) THE FACTOR-3.4 SPREAD AT BMI 28-31 IS NOT THE INSTRUMENT:")
check("       spread in units of measurement SD", (2.952 - 0.880) / SD_ARTIF, 22.03, 0.02, " SD")
print("       Fifteen measurement SDs wide. The biological spread at one BMI is")
print("       real, and section 2's conclusion rests on something the rig could")
print("       not have manufactured.")
print()
print("   (c) ATTENUATION, AND IT RUNS THE HELPFUL WAY. Measurement noise biases")
print("       a correlation TOWARD ZERO, so r = +0.894 UNDERSTATES the awake")
print("       lung's hold on the anaesthetised one. Correcting with Spearman's")
print("       formula, using part I's SDs as the error term:")
_rel_aw = 1 - SD_SPONT ** 2 / AW.std(ddof=1) ** 2
_rel_an = 1 - SD_ARTIF ** 2 / AN.std(ddof=1) ** 2
check("       reliability, awake column", _rel_aw, 0.9969, 0.0005)
check("       reliability, anaesthetised column", _rel_an, 0.9766, 0.0005)
check("       awake vs anaes, DISATTENUATED r",
      np.corrcoef(AW, AN)[0, 1] / np.sqrt(_rel_aw * _rel_an), 0.906, 0.002)
check("       BMI   vs anaes, DISATTENUATED r",
      np.corrcoef(BMI, AN)[0, 1] / np.sqrt(_rel_an), -0.439, 0.002)
print("       Correcting for the instrument moves both only slightly, 0.894 ->")
print("       0.906 and -0.434 -> -0.439, because a mean of two duplicates is")
print("       quieter than a single run. The awake lung keeps its lead.")
print()

print("6. HOW MUCH WEIGHT n = 13 ACTUALLY BEARS. Added 2026-10-13 after an")
print("   adversarial verifier pointed out that section 2 reported correlations")
print("   with no interval and no significance, which is how a 3%-vs-80% contrast")
print("   can look more decisive than the data allow.")
print()


def _fisher(r, n):
    z, se = np.arctanh(r), 1.0 / np.sqrt(n - 3)
    return np.tanh(z - 1.959963985 * se), np.tanh(z + 1.959963985 * se)


def _perm_p(x, y, iters=50000, seed=0):
    rng = np.random.default_rng(seed)
    r0, yy, hits = abs(np.corrcoef(x, y)[0, 1]), y.copy(), 0
    for _ in range(iters):
        rng.shuffle(yy)
        if abs(np.corrcoef(x, yy)[0, 1]) >= r0:
            hits += 1
    return (hits + 1) / (iters + 1)


for _lbl, _x, _r, _lo, _hi, _p in (
        ("awake FRC", AW, 0.894, 0.676, 0.968, 0.0001),
        ("BMI", BMI, -0.434, -0.795, 0.154, 0.1378)):
    _rr = np.corrcoef(_x, AN)[0, 1]
    _l, _h = _fisher(_rr, 13)
    check(f"   anaes FRC vs {_lbl}: r", _rr, _r, 0.002)
    check(f"   anaes FRC vs {_lbl}: 95% CI low", _l, _lo, 0.002)
    check(f"   anaes FRC vs {_lbl}: 95% CI high", _h, _hi, 0.002)
    check(f"   anaes FRC vs {_lbl}: permutation p", _perm_p(_x, AN), _p, 0.004)
print()
print("   SO THE TWO HALVES OF THE CONTRAST ARE NOT EQUALLY SOLID. The awake")
print("   correlation is strong and significant (p = 0.0001). THE BMI ONE IS NOT")
print("   DISTINGUISHABLE FROM ZERO (p = 0.14, interval crossing zero). Reporting")
print("   'BMI explains 19%' as a quantity overstates what 13 patients can say.")
print()
print("   AND IT TURNS ON ONE PATIENT. Patient 8's awake FRC is 3.827 l, far the")
print("   largest in the table. Dropping him alone:")
_m = np.array([r[0] != 8 for r in T2])
for _lbl, _x, _rec in (("awake FRC", AW, 0.867), ("BMI", BMI, -0.741)):
    check(f"   without pt 8: anaes FRC vs {_lbl}", np.corrcoef(_x[_m], AN[_m])[0, 1], _rec, 0.002)
print("   The awake correlation barely moves (+0.894 -> +0.867). BMI's goes from")
print("   -0.434 to -0.741, i.e. from 19% of the variance to 55%, and becomes")
print("   significant. SO THE HONEST STATEMENT IS NARROWER THAN SECTION 2's:")
print("   the awake volume is robustly the better predictor in this cohort, by")
print("   both readings; but 'BMI explains almost nothing' does NOT survive, and")
print("   how much BMI explains is unstable between 19% and 55% on one patient.")
print("   The argument against keying the anaesthetised level on BMI ALONE holds.")
print("   The argument that BMI carries little information does not.")
print()

# Hewlett 1974 PART II (Br J Anaesth 46:486-94), TABLE II. 26 MALES,
# SPONTANEOUSLY breathing, thiopentone + halothane, supine, read in full from
# upload 2026-10-14. Volumes litres BTPS. Transcribed from the PDF text layer.
# pt, age, ht cm, wt kg, FRC pre-induction, FRC anaesthetised, % reduction
P2 = [
    (1, 39, 171, 66.5, 2.184, 1.934, 11.45), (2, 47, 168, 64.2, 2.733, 2.300, 15.84),
    (3, 42, 174, 79.0, 1.846, 1.535, 16.85), (4, 54, 165, 71.5, 1.755, 1.535, 12.54),
    (5, 44, 179, 68.5, 2.606, 1.960, 24.79), (6, 34, 190, 80.0, 1.551, 1.611, -3.87),
    (7, 26, 173, 74.5, 1.934, 1.772, 8.38), (8, 27, 170, 66.6, 2.647, 2.640, 0.26),
    (9, 37, 167, 56.0, 1.347, 1.118, 17.00), (10, 25, 176, 92.0, 2.188, 1.872, 14.44),
    (11, 24, 194, 85.0, 3.096, 2.830, 8.59), (12, 58, 154, 64.0, 1.808, 1.519, 15.98),
    (13, 31, 177, 85.0, 1.443, 1.381, 4.30), (14, 36, 181, 74.0, 2.571, 1.527, 40.61),
    (15, 31, 170, 61.0, 1.571, 1.123, 28.52), (16, 45, 171, 69.8, 2.251, 1.886, 16.22),
    (17, 43, 172, 90.0, 2.093, 1.435, 31.44), (18, 43, 179, 53.0, 4.771, 3.290, 31.04),
    (19, 34, 171, 76.7, 2.206, 1.251, 43.29), (20, 32, 175, 75.0, 2.527, 2.931, -15.99),
    (21, 24, 182, 73.5, 1.732, 1.656, 4.39), (22, 37, 175, 80.0, 2.553, 2.271, 11.05),
    (23, 68, 174, 68.2, 2.651, 2.245, 15.31), (24, 38, 176, 75.0, 3.625, 2.473, 31.78),
    (25, 40, 179, 93.0, 1.061, 0.822, 22.53), (26, 19, 169, 56.5, 2.611, 2.301, 11.87),
]
PRE = np.array([r[4] for r in P2])
PAN = np.array([r[5] for r in P2])
PPCT = np.array([r[6] for r in P2])
PBMI = np.array([r[3] / (r[2] / 100.0) ** 2 for r in P2])

print("7. PART II, AND IT IS THE PAPER THAT BREAKS THE SEX CONFOUND: 26 MALES,")
print("   SPONTANEOUSLY BREATHING. Part III was 10/13 female and paralysed and")
print("   ventilated; this is the same group's independent cohort in the sex the")
print("   model is configured for and the breathing state closer to apnoea.")
print()
print("   TRANSCRIPTION, checked against FIVE printed statistics:")
check("   mean pre-induction FRC [table: 2.283]", float(PRE.mean()), 2.283, 0.001, " l")
check("   mean anaesthetised FRC [table: 1.893]", float(PAN.mean()), 1.893, 0.001, " l")
check("   mean reduction [text: 390 mL]", 1000 * float((PRE - PAN).mean()), 390.0, 0.6, " mL")
check("   mean % reduction [text: 16.1, SD 13.4]", float(PPCT.mean()), 16.10, 0.02, " %")
check("   SD of the % reduction [text: 13.4]", float(PPCT.std(ddof=1)), 13.37, 0.02, " %")
check("   patients whose FRC fell [text: 24 of 26]", float((PPCT > 0).sum()), 24.0, 0.5)
print("   Every printed statistic reproduces. This transcription is sound.")
print()
print("   AND A TRAP IN ITS OWN SUMMARY. The abstract gives the fall correlating")
print("   with age at r = 0.41 and with weight/height at r = 0.30. BOTH ARE THE")
print("   POOLED FIGURES over 54 patients (his 26 plus Don's two series), as the")
print("   figure captions state. THIS STUDY'S OWN 26 GIVE:")
_page = np.array([float(r[1]) for r in P2])
_pwh = np.array([r[3] / r[2] for r in P2])
check("   % reduction vs age, THIS COHORT ONLY", np.corrcoef(_page, PPCT)[0, 1], 0.235, 0.002)
check("   % reduction vs wt/ht, THIS COHORT ONLY", np.corrcoef(_pwh, PPCT)[0, 1], -0.033, 0.002)
print("   Neither of the abstract's figures belongs to these 26 patients. Do not")
print("   quote 0.41 or 0.30 as properties of this cohort.")
print()
print("   THE REPLICATION, and it is why the de-coupling question is closed:")
for _lbl, _x, _rec in (("pre-induction FRC", PRE, 0.855), ("BMI", PBMI, -0.439),
                       ("height", np.array([r[2] / 100.0 for r in P2]), 0.230),
                       ("age", _page, -0.081)):
    check(f"   anaesthetised FRC vs {_lbl}", np.corrcoef(_x, PAN)[0, 1], _rec, 0.002)
print("   Part III gave +0.894 against -0.434 in 13 mostly-female paralysed")
print("   patients. Part II gives +0.855 against -0.439 in 26 males breathing")
print("   spontaneously. DIFFERENT PATIENTS, DIFFERENT SEX MIX, DIFFERENT")
print("   VENTILATION, SAME ANSWER. That is a replication, not a repetition.")
print()
print("   AND IT CORRECTS SOMETHING THIS FILE SAID. Section 3 explained the")
print("   model's +510 mL awake bias against part III as what a male model")
print("   should do against a 10/13 female cohort. AGAINST 26 MALES THE BIAS IS")
print("   ESSENTIALLY THE SAME:")
_eaw, _ean, _edr = [], [], []
for _pt, _ag, _ht, _wt, _fp, _fa, _ in P2:
    _g = dict(weight=_wt, height=_ht / 100.0, age=_ag, tilt_deg=0)
    _p = Patient(**_g)
    _eaw.append(_p.frc_awake() - _fp * 1000)
    _ean.append(_p.frc_anaes() - _fa * 1000)
    _edr.append((_p.frc_awake() - _p.frc_anaes()) - (_fp - _fa) * 1000)
check("   awake bias against 26 MALES", float(np.mean(_eaw)), 503.0, 1.0, " mL")
check("   anaesthetised bias against 26 MALES", float(np.mean(_ean)), 221.0, 1.0, " mL")
check("   the DROP, model minus measured", float(np.mean(_edr)), 281.0, 1.0, " mL")
print("   +503 mL in males against +510 mL in the mostly-female cohort. THE SEX")
print("   CONFOUND DOES NOT EXPLAIN THE AWAKE BIAS -- it is the model's, and it")
print("   is a real conflict with Hewlett that sex was being used to excuse.")
print()
print("   THE DROP, ONCE MORE SEPARATING THE PARAMETER FROM THE SHAPE:")
_md = float(np.mean([Patient(weight=r[3], height=r[2] / 100.0, age=r[1],
                             tilt_deg=0).frc_awake()
                     - Patient(weight=r[3], height=r[2] / 100.0, age=r[1],
                               tilt_deg=0).frc_anaes() for r in P2]))
check("   model's mean effective drop", _md, 671.0, 1.0, " mL")
check("   frc_drop, the PARAMETER", Patient().frc_drop, 400.0, 0.5, " mL")
print("   Measured 390 mL. The PARAMETER is within 10 mL of it; the EFFECTIVE")
print("   drop is 671 mL because Pelosi's BMI shape steepens the fall after it")
print("   -- and it grew from 635 mL when the offset ruling of 2026-10-15")
print("   lowered the curve, so the ruling made THIS disagreement worse.")
print("   Exactly the split part III showed, now confirmed in the right sex.")
print()

if FAILED:
    print(f"{len(FAILED)} value(s) have drifted:")
    for f in FAILED:
        print(f"  - {f}")
    raise SystemExit(1)
print("Every Hewlett number still reproduces from this commit.")
