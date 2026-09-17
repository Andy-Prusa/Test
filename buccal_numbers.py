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
OBESE = dict(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)  # Heard 2017
FAILED = []


def check(name, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    if not ok:
        FAILED.append(name)
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<46}{got:>8.1f}{unit}"
          f"   recorded {want}{unit}")


def sim(kw, epochs, dt=0.05, feo2=0.87):
    return simulate(Patient(**kw), epochs, dt=dt, feo2_start=feo2,
                    stop_sao2=0.0)


def t95(kw, fg):
    """Time to SpO2 < 95% with a patent airway. 9999 = past the trials' ceiling."""
    r = sim(kw, [AirwayEpoch(1200, resistance=2, fgo2=fg)])
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
# table recorded anything past 750 as "holds". That flattened a real gradation.
# The lean patient at FO2 0.70 desaturates at 824 s -- past the ceiling, but
# only by 74 s, and nothing like indefinitely. Only FO2 1.00 runs past 20 min.
for fg, lean, obese in ((0.21, 402.3, 288.4), (0.60, 669.0, 462.2),
                        (0.70, 823.7, 562.4), (0.90, 9999.0, 1030.2)):
    check(f"lean, pharyngeal FO2 {fg:.2f}", t95(LEAN, fg), lean, 6.0, " s")
    check(f"obese, pharyngeal FO2 {fg:.2f}", t95(OBESE, fg), obese, 6.0, " s")
check("lean, pharyngeal FO2 1.00 (runs past 20 min)", t95(LEAN, 1.00),
      9999.0, 1.0, " s")

# ---------------------------------------------------------------------------
print("\nWho benefits most: the gain grows with BMI, room air vs buccal")
for w, want in ((67, 570.0), (138, 181.0)):
    kw = dict(weight=w, height=1.75, age=45, hb=14, tilt_deg=25)
    check(f"BMI {w/1.75**2:.1f}, room air", t95(kw, 0.21), want, 8.0, " s")

print("\nAnaemia does NOT shorten it -- SpO2 is a saturation, not a content")
for hb, want in ((8.0, 394.0), (15.0, 402.3)):
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
for name, kw, want in (('lean', LEAN, 256.0), ('obese', OBESE, 198.0)):
    for fg in (0.21, 1.00):
        r = sim(kw, [AirwayEpoch(600, resistance=OBS, fgo2=fg)])
        s = np.asarray(r['spo2']); b = np.where(s < 95.0)[0]
        got = float(np.asarray(r['t'])[b[0]]) if len(b) else 9999.0
        check(f"{name}, occluded, pharynx {fg:.2f}", got, want, 6.0, " s")

print("\nRelieved at laryngoscopy: room air gives a bump, buccal gives a rescue")
for fg, want in ((0.21, 56.8), (1.00, 99.8)):
    r = sim(OBESE, [AirwayEpoch(300, resistance=OBS, fgo2=fg),
                    AirwayEpoch(600, resistance=2, fgo2=fg)])
    check(f"obese, opened at 300 s, SpO2 120 s later, FO2 {fg:.2f}",
          at(r, 'spo2', 420), want, 2.0, " %")

# ---------------------------------------------------------------------------
print("\nHow narrow a channel will do? R = 394*(1/d mm)^4, anchored on the")
print("1 mm <-> 1.3 cmH2O at 3.3 mL/s in AirwayEpoch's docstring.")
R1MM = 1.3 / 0.0033
for d, lean, obese in ((0.8, 83.4, 35.0), (0.6, 35.8, 34.2)):
    R = R1MM * (1.0 / d) ** 4
    for name, kw, want in (('lean', LEAN, lean), ('obese', OBESE, obese)):
        r = sim(kw, [AirwayEpoch(1860, resistance=R, fgo2=1.00)])
        check(f"{name}, {d} mm aperture, SpO2 at 30 min",
              at(r, 'spo2', 1800), want, 2.0, " %")
print("    A 0.2 mm change takes the lean patient from 83% to 36%. Patency is")
print("    effectively binary, and the threshold is SUB-MILLIMETRE -- far below")
print("    anything POGO or Cormack-Lehane resolves. That conclusion survives")
print("    the compliance unit fix of 2026-09-17; the numbers it rests on do")
print("    not. Before the fix these were 90.0 / 69.1 at 0.8 mm and 64.2 /")
print("    34.4 at 0.6 mm. Sub-millimetre apertures are now WORSE, not better.")

r = sim(OBESE, [AirwayEpoch(1860, resistance=2.0, fgo2=1.00)])
check("obese, airway WIDE OPEN, SpO2 at 30 min", at(r, 'spo2', 1800), 86.5, 2.0, " %")
print("    The obese 30-minute ceiling is NOT an aperture limit. Wide open, with")
print("    alveolar PO2 above 350 mmHg, saturation is still 86%. That is SHUNT.")
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
