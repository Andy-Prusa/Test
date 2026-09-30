# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
buccal_numbers.py -- regenerates every buccal-oxygen figure quoted in
HANDOVER.md and editorial.md, and fails if one has drifted.

Same contract as handover_numbers.py and protocol/predictions.py: NOT in the
pre-commit hook, because these are claims about the world rather than
invariants of the code. They are expected to move when the model is
corrected. The point is that they must not move SILENTLY.

Published configurations only. Toner 2019 (lean) and Heard 2017 (obese) are
the two benchmarked populations; nothing here uses unpublished data.

    python3 buccal_numbers.py
"""
import numpy as np
import apnoea_core as A
from apnoea_core import Patient, AirwayEpoch, simulate

print(A.provenance())
print()

OBS = np.inf
LEAN = dict(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)     # Toner 2019
# Heard 2017, READ FROM THE PAPER 2026-09-22: 105 +- 13 kg, 174 +- 9 cm,
# 42 +- 14 y, 30 degrees reverse Trendelenburg. Was 107/1.75/45/tilt 25,
# which was a guess at a cohort we had not read.
OBESE = dict(weight=105, height=1.74, age=42, hb=14, tilt_deg=30)  # Heard 2017
FAILED = []


def check(name, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    if not ok:
        FAILED.append(name)
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<46}{got:>8.1f}{unit}"
          f"   recorded {want}{unit}")


# PREOXYGENATION IS PER COHORT, not a single default. Heard 2017 was read on
# 2026-09-22 and states its endpoint explicitly: "At the first reading of
# end-tidal oxygen (EtO2) >= 80%, buccal oxygenation was started". Before that
# reading, every obese number in this file started from 0.87 -- seven points of
# alveolar oxygen the trial never gave its patients.
#
# The lean value is STILL AN ASSUMPTION. Toner 2019 has been read for its
# outcomes but not for a preoxygenation endpoint, so 0.87 stays there and is
# labelled as the assumption it is rather than being quietly matched to Heard.
FEO2_OBESE = 0.80    # Heard 2017, read from the paper
FEO2_LEAN = 0.87     # Toner 2019, ASSUMED -- not read from the paper


def sim(kw, epochs, dt=0.05, feo2=FEO2_LEAN):
    return simulate(Patient(**kw), epochs, dt=dt, feo2_start=feo2,
                    stop_sao2=0.0)


def t95(kw, fg, feo2=FEO2_LEAN):
    """Time to SpO2 < 95% with a patent airway. 9999 = past the trials' ceiling.

    feo2 is the COHORT's preoxygenation endpoint and must be passed for the
    obese arm: Heard 2017 preoxygenated to EtO2 >= 80%, not to the 0.87 this
    file assumes for Toner's lean cohort.
    """
    r = sim(kw, [AirwayEpoch(1200, resistance=2, fgo2=fg)], feo2=feo2)
    s = np.asarray(r['spo2'])
    below = np.where(s < 95.0)[0]
    return float(np.asarray(r['t'])[below[0]]) if len(below) else 9999.0


def at(r, key, t):
    return float(np.interp(t, np.asarray(r['t']), np.asarray(r[key])))


# ---------------------------------------------------------------------------
print("Pharyngeal oxygen fraction -- a SENSITIVITY, not a dose-response.")
print("The pharyngeal fraction is a model INPUT. Toner measured TRACHEAL")
print("oxygen; nobody has measured the pharynx. Until they do, these say")
print("what follows IF the fraction is x, not what a device delivers.\n")
# NOTE on "holds": the trials stopped at 750 s, so an earlier version of this
# table recorded anything past 750 as "holds". That flattened a real gradation,
# and the gradation is still there -- the lean patient at FO2 0.70 desaturates
# at 933 s, past the trials' ceiling but nothing like indefinitely.
#
# RENUMBERED 2026-09-23, and the ceiling MOVED. Every row here is longer than
# it was, by 40-110 s, and the obese patient at FO2 0.90 now runs past 20
# minutes where it used to fail at 1062 s. The earlier note said "only FO2
# 1.00 runs past 20 min"; that is no longer true and the line is struck.
#
# WHY THEY ALL MOVED. Three changes, in order: the V/Q category-error fix
# (gas volume is no longer allocated by a ratio of flows, which had been
# acting as a fake shunt on every patient including lean ones), residual
# volume becoming BMI-dependent, and the low-V/Q mechanism. The first
# LENGTHENS everything and the third SHORTENS the obese, and on these rows
# the first dominates.
#
# AND THIS FILE WAS STALE BEFORE THE RE-KEY OF 2026-09-24, which is the more
# important finding. Run against the previous commit (1288632, Pelosi's curve)
# it failed SIX rows, every one of them obese:
#     obese FO2 0.21   recorded 310.2   actual 302.2
#     obese FO2 0.60   recorded 500.3   actual 484.1
#     obese FO2 0.70   recorded 619.4   actual 597.6
#     BMI 45.1 room air recorded 196.8  actual 185.7
#     obese opened at 300 s, FO2 0.21   recorded 52.5   actual 46.6
#     obese 0.6 mm aperture at 30 min   recorded 88.9   actual 86.6
# The recorded values predate the tilt -> cardiac-output term and the Pelosi
# curve, both committed the same day, and the file was not re-run after
# either. The PR body's claim that it was "complete and clean" was wrong.
#
# THE RE-KEY THEN MOVED THE OBESE ROWS BACK TOWARD THE RECORDED VALUES, so
# only three now drift. This patient is tilted 30 degrees head-up, and the
# re-key is the first change that lets tilt reduce the shunt: hers falls
# 7.53% -> 4.72%. In an identical harness, forcing 7.53% gives 597.6 s and
# forcing 4.72% gives 612.9 s, so within this change lower shunt means longer
# time, as it should. The recorded 619.4 is NOT on that line, which is what
# identifies it as predating the cardiac-output term rather than the shunt.
for fg, lean, obese in ((0.21, 444.5, 310.2), (0.60, 744.2, 500.3),
                        (0.70, 938.9, 612.9), (0.90, 9999.0, 9999.0)):
    check(f"lean, pharyngeal FO2 {fg:.2f}", t95(LEAN, fg), lean, 6.0, " s")
    check(f"obese, pharyngeal FO2 {fg:.2f}", t95(OBESE, fg, FEO2_OBESE),
          obese, 6.0, " s")
check("lean, pharyngeal FO2 1.00 (runs past 20 min)", t95(LEAN, 1.00),
      9999.0, 1.0, " s")

# ---------------------------------------------------------------------------
print("\nWho benefits most: the gain grows with BMI, room air vs buccal")
for w, want in ((67, 642.5), (138, 196.8)):
    kw = dict(weight=w, height=1.74, age=42, hb=14, tilt_deg=30)
    check(f"BMI {w/1.75**2:.1f}, room air", t95(kw, 0.21), want, 8.0, " s")

print("\nAnaemia does NOT shorten it -- SpO2 is a saturation, not a content")
for hb, want in ((8.0, 450.5), (15.0, 444.5)):
    kw = dict(LEAN); kw['hb'] = hb
    check(f"lean, Hb {hb:.0f}, room air", t95(kw, 0.21), want, 6.0, " s")

# ---------------------------------------------------------------------------
print("\nThe mechanism: same flow, different gas. Cumulative O2 drawn in at 300 s")
for fg, want in ((0.21, 298.0), (1.00, 1011.0)):
    r = sim(LEAN, [AirwayEpoch(400, resistance=2, fgo2=fg)])
    check(f"lean, O2 entrained by 300 s at FO2 {fg:.2f}",
          at(r, 'cum_o2_in', 300), want, 25.0, " mL")

# ---------------------------------------------------------------------------
print("\nComplete occlusion: buccal oxygen can do NOTHING without a conduit")
for name, kw, fe, want in (('lean', LEAN, FEO2_LEAN, 385.7),
                           ('obese', OBESE, FEO2_OBESE, 266.4)):
    for fg in (0.21, 1.00):
        r = sim(kw, [AirwayEpoch(600, resistance=OBS, fgo2=fg)], feo2=fe)
        s = np.asarray(r['spo2']); b = np.where(s < 95.0)[0]
        got = float(np.asarray(r['t'])[b[0]]) if len(b) else 9999.0
        check(f"{name}, occluded, pharynx {fg:.2f}", got, want, 6.0, " s")

print("\nRelieved at laryngoscopy: room air gives a bump, buccal gives a rescue")
# The room-air row is recorded at 52.5%, was already 46.6% at the previous
# commit, and is 47.5% now -- so most of this drift predates the shunt re-key
# and belongs to the tilt -> cardiac-output term (this patient is tilted 30
# degrees). The re-key moved it back by 0.9 of a point. The rescue on 100%
# oxygen is unchanged at 99.8% throughout: it has saturation in hand, and the
# room-air bump is the one a shunt or a lower cardiac output eats into.
for fg, want in ((0.21, 47.5), (1.00, 99.8)):
    r = sim(OBESE, feo2=FEO2_OBESE, epochs=[AirwayEpoch(300, resistance=OBS, fgo2=fg),
                    AirwayEpoch(600, resistance=2, fgo2=fg)])
    check(f"obese, opened at 300 s, SpO2 120 s later, FO2 {fg:.2f}",
          at(r, 'spo2', 420), want, 2.0, " %")

# ---------------------------------------------------------------------------
print("\nHow narrow a channel will do? R = 394*(1/d mm)^4, anchored on the")
print("1 mm <-> 1.3 cmH2O at 3.3 mL/s in AirwayEpoch's docstring.")
R1MM = 1.3 / 0.0033
for d, lean, obese in ((0.8, 99.7, 98.6), (0.6, 96.5, 88.9)):
    R = R1MM * (1.0 / d) ** 4
    for name, kw, fe, want in (('lean', LEAN, FEO2_LEAN, lean),
                               ('obese', OBESE, FEO2_OBESE, obese)):
        r = sim(kw, [AirwayEpoch(1860, resistance=R, fgo2=1.00)], feo2=fe)
        check(f"{name}, {d} mm aperture, SpO2 at 30 min",
              at(r, 'spo2', 1800), want, 2.0, " %")
print("    THIS CONCLUSION IS REVERSED, 2026-09-23. It read: 'a 0.2 mm change")
print("    takes the lean patient from 83% to 36%, patency is effectively")
print("    binary, and the threshold is SUB-MILLIMETRE'. It is now 99.7% to")
print("    96.5% -- three points, not forty-seven. The obese patient goes 98.6")
print("    to 88.9 where it went 37.3 to 34.2. A sub-millimetre channel now")
print("    SUFFICES, at both body habitus, for thirty minutes on 100% oxygen.")
print("    THE HISTORY OF THIS ROW, because it has now moved twice and in")
print("    opposite directions:")
print("        lean 0.8mm  lean 0.6mm  obese 0.8mm  obese 0.6mm")
print("            90.0        64.2        69.1        34.4   before 2026-09-17")
print("            83.4        35.8        37.3        34.2   after the crs fix")
print("            99.7        96.5        98.6        88.9   now")
print("    The last step is the V/Q category-error fix: the artefact it")
print("    removed was acting as a shunt that no aperture could overcome, so")
print("    the old numbers were measuring the artefact and not the aperture.")
print("    WHAT SURVIVES is only that the relationship is steep in d: R goes")
print("    as 1/d^4, so the transition is still sharp. WHERE it sits is now")
print("    BELOW 0.6 mm and has not been bracketed. Do not quote a threshold")
print("    from this table until the sweep is run again at finer spacing.")

r = sim(OBESE, [AirwayEpoch(1860, resistance=2.0, fgo2=1.00)], feo2=FEO2_OBESE)
check("obese, airway WIDE OPEN, SpO2 at 30 min", at(r, 'spo2', 1800), 99.4, 2.0, " %")
print("    THERE IS NO LONGER AN OBESE 30-MINUTE CEILING. This read: 'wide")
print("    open, with alveolar PO2 above 350 mmHg, saturation is still 86%,")
print("    that is SHUNT'. Wide open now holds 99.4%, which is what a 7.5%")
print("    shunt on 100% oxygen should give. The 86.5% was the V/Q volume")
print("    artefact behaving as extra shunt, not the shunt the model reports.")
print("    THE CLAIM THAT IT WAS SHUNT WAS WRONG, and it was wrong in the")
print("    informative direction: the model HAS always reported ~7.5% here.")
print("    Reading 86% as evidence of shunt meant trusting a saturation over")
print("    the model\'s own shunt output when the two disagreed by a factor")
print("    of three. The output was right.")
print("    editorial.md's claim that 0.8 mm holds >90% for 30 min NO LONGER")
print("    REPRODUCES FOR EITHER PATIENT. Until the compliance unit fix of")
print("    2026-09-17 the lean figure was 90.0 and matched the claim exactly;")
print("    it is now 83.4. The audit entry in HANDOVER that recorded the claim")
print("    as reproducing is superseded by this line.")

# ---------------------------------------------------------------------------
print()
print("NOT REPRODUCIBLE, and recorded as such")
print("    editorial.md's '50-70 seconds' of buccal benefit in a CICO")
print("    progression: no progression is specified, so there is no path back")
print("    to a calculation. Buccal buys exactly ZERO once occluded, so the")
print("    figure must come from benefit banked beforehand -- but from what")
print("    timeline is not recorded.")
print("    editorial.md's alveolar PN2 of 395 mmHg in 'the morbidly obese':")
print("    no weight or BMI is given. At the Heard configuration it is 246.")
print()
if FAILED:
    print(f"{len(FAILED)} value(s) have drifted:")
    for f in FAILED:
        print(f"  - {f}")
    raise SystemExit(1)
print("Every buccal number still reproduces from this commit.")
