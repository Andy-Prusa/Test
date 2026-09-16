# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""Regenerate every number quoted in HANDOVER.md, and fail if any has drifted.

HANDOVER.md carries several numeric tables that were computed once and typed in.
Numbers in markdown rot. This script recomputes them and checks them, so that
when the model changes the tables are known to be stale instead of quietly
becoming fiction. The Ellis comparator rows are the cautionary case: recorded
in 2026, never scripted, and now unreproducible because the configuration
behind them was not written down.

    python3 handover_numbers.py

Deliberately NOT in the pre-commit hook, for the same reason as
`protocol/predictions.py`: these describe claims and investigations, not
invariants of the code, and they are expected to move when the model is
corrected. The point is that they must not move SILENTLY.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apnoea_core as ac  # noqa: E402
from apnoea_core import AirwayEpoch, Patient, simulate  # noqa: E402

OBS = np.inf
DT = 0.05
_fails = []


def check(what, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    print(f"    {'ok  ' if ok else 'FAIL'} {what:<46} {got:8.2f}{unit}"
          f"   HANDOVER says {want:g}{unit}")
    if not ok:
        _fails.append(what)


def run(duration=360.0, obstructed=True, **kw):
    """One sealed (or patent) run at the Stock reference patient."""
    fgo2 = kw.pop('fgo2', 0.21 if obstructed else 1.0)
    p = Patient(weight=kw.pop('weight', 70), height=kw.pop('height', 1.75),
                age=kw.pop('age', 45), hb=kw.pop('hb', 15.0), **kw)
    ep = AirwayEpoch(duration, resistance=OBS if obstructed else 2.0, fgo2=fgo2)
    return simulate(p, [ep], dt=DT, stop_sao2=0.0)


def at(r, key, t):
    return float(np.interp(t, r['t'], r[key]))


def slope(r, a=60.0, b=300.0):
    return (at(r, 'paco2', b) - at(r, 'paco2', a)) / ((b - a) / 60.0)


print(ac.provenance())
print()

# ---------------------------------------------------------------------------
print("Known disagreement / the a-A decomposition")
print("  The venous slopes agree between obstructed and patent, which is what")
print("  exonerates the CO2 stores. If that stops being true, the whole")
print("  localisation in HANDOVER is void.")
ro, rp = run(), run(obstructed=False)


def gap(r, t):
    return at(r, 'paco2', t) - at(r, 'paco2_alv', t)


check("obstructed PaCO2 slope 60-300 s", slope(ro), 4.03, 0.10, " mmHg/min")
check("obstructed PACO2 slope", (at(ro, 'paco2_alv', 300) - at(ro, 'paco2_alv', 60)) / 4, 2.53, 0.10)
check("obstructed PvCO2 slope", (at(ro, 'pvco2', 300) - at(ro, 'pvco2', 60)) / 4, 1.70, 0.10)
check("patent PaCO2 slope 60-300 s", slope(rp), 1.70, 0.10, " mmHg/min")
check("patent PvCO2 slope", (at(rp, 'pvco2', 300) - at(rp, 'pvco2', 60)) / 4, 1.74, 0.10)
check("obstructed a-A gap growth", (gap(ro, 300) - gap(ro, 60)) / 4, 1.50, 0.10)
check("patent a-A gap growth", (gap(rp, 300) - gap(rp, 60)) / 4, -0.04, 0.10)
for t, g, sh, sa in ((60, -0.2, 0.058, 100.0), (180, 1.3, 0.103, 98.5),
                     (240, 5.9, 0.140, 93.1), (300, 5.8, 0.181, 84.9)):
    check(f"obstructed a-A gap at {t:3.0f} s", gap(ro, t), g, 0.4, " mmHg")
    check(f"obstructed shunt at {t:3.0f} s", 100 * at(ro, 'shunt', t), 100 * sh, 1.0, " %")

# ---------------------------------------------------------------------------
print("\nWhat the coupling is NOT")
check("shunt suppressed (max_closed 0.02): slope",
      slope(run(max_closed=0.02)), 4.21, 0.15, " mmHg/min")
check("hb 18, desaturation delayed: slope",
      slope(run(hb=18.0)), 3.64, 0.15, " mmHg/min")
check("p_collapse floor removed (-200): slope",
      slope(run(p_collapse=-200.0)), 3.98, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\ntau_mix -- the lever that acts on the a-A gap")
for tm, want in ((25.0, 5.44), (45.0, 4.03), (60.0, 3.56), (90.0, 2.70)):
    check(f"tau_mix {tm:5.1f}: Stock 1-5 min slope",
          slope(run(tau_mix=tm)), want, 0.12, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nvq_log_sd against Tokics 1996 (measured 0.80 isotope / 1.18 inert gas)")
for sd, want in ((0.50, 2.89), (0.70, 4.03), (0.80, 4.67), (1.18, 6.74)):
    check(f"vq_log_sd {sd:4.2f}: Stock 1-5 min slope",
          slope(run(vq_log_sd=sd)), want, 0.15, " mmHg/min")
check("baseline shunt (Tokics Table 3 measured 5.0 +- 1.3%)",
      100 * ro['shunt'][0], 5.0, 0.5, " %")
print("    Tokics' inert-gas shunt under anaesthesia is 5.0 +- 1.3% (Table 3,")
print("    read from the page 2026-09-16). HANDOVER used to record it as 7.0,")
print("    one of nine values transposed 5-for-7. We LAND on the measurement,")
print("    we do not sit under it.")

# ---------------------------------------------------------------------------
print("\nsv_itp_gain -- nearly inert on the knot (human data give 0.0033-0.00476)")
for g_, want in ((0.0025, 4.03), (0.00476, 3.93)):
    check(f"sv_itp_gain {g_:.5f}: Stock slope",
          slope(run(sv_itp_gain=g_)), want, 0.12, " mmHg/min")
check("stiff_below_rv 2.00: Stock slope",
      slope(run(stiff_below_rv=2.0)), 4.77, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nn_vq convergence -- and arterial CO2 going the WRONG WAY at n_vq 20")
print("  CO2 cannot leave a clamped lung, so PaCO2 must rise monotonically.")
print("  At the default n_vq it does not. This is a discretisation artefact")
print("  and it is the reason the benchmarked slope is below the converged one.")
for n_, want_slope, want_falls in ((20, 4.03, 19), (40, 4.13, 0),
                                   (80, 4.11, 0), (160, 4.10, 0)):
    r_ = run(n_vq=n_)
    falls = int((np.diff(r_['paco2']) < -1e-9).sum())
    check(f"n_vq {n_:3d}: Stock 1-5 min slope", slope(r_), want_slope, 0.15,
          " mmHg/min")
    check(f"n_vq {n_:3d}: steps where PaCO2 FALLS", float(falls),
          float(want_falls), 2.0, " steps")
print("    The 20 -> 160 slope move is 1.7%, inside the working tolerance.")
print("    The SIGN error is not a tolerance question. test_validation.py")
print("    checks timestep convergence and has never checked this one.")

# ---------------------------------------------------------------------------
print("\nThe CO2 dissociation curve -- its CURVATURE drives the a-A gap")
import bloodgas as bg  # noqa: E402
for pco2, want in ((40, 46.59), (60, 54.90), (80, 61.22), (100, 66.44)):
    ph = bg.ph_from_pco2_be(pco2, 0.0, 15.0, so2=0.97, temp=37.0)
    check(f"CCO2 at PCO2 {pco2:3d}, SO2 0.97, Hb 15",
          bg.co2_content(pco2, ph, 0.97, 15.0, 37.0), want, 0.15, " mL/dL")
check("arterial anchor Hb 14, pH 7.40, PCO2 40, SO2 0.97",
      bg.co2_content(40, 7.40, 0.97, 14.0, 37.0), 47.50, 0.15, " mL/dL")
print("    Kelman 1967 and Douglas 1988 were obtained on 2026-09-14 and both")
print("    limbs are now VERIFIED against the papers. A real error was found:")
print("    Douglas takes [Hb] in g/100 mL and we were passing mmol/L, which put")
print("    content 8.7% high. These four values moved by about 4.3 mL/dL each.")
print("    The arterial anchor checked above sits against a textbook ~48;")
print("    before the [Hb] fix it was 51.65. Its configuration is the one")
print("    bloodgas.py's NOTE_DOUGLAS states -- Hb 14, pH 7.40, PCO2 40,")
print("    SO2 0.97 -- and both figures reproduce there exactly, 47.4984 now")
print("    and 51.6544 at 1713715^. It is now checked rather than printed,")
print("    because it was printed prose before and prose does not fail.")
print("    The pH is GIVEN here, not solved from base excess. That matters:")
print("    at BE 0 the same anchor is 47.36, and an earlier attempt to")
print("    regenerate 47.50 searched base-excess space, failed to find it,")
print("    and wrongly recorded it as unreproducible.")
print("    The CURVATURE was the reason Kelman was called the critical path.")
print("    Correcting the curve moved every CO2 SLOPE by under 0.05 mmHg/min,")
print("    so the curve is NOT the cause of the a-A over-sensitivity.")

# ---------------------------------------------------------------------------
print("\nPharyngeal FO2 -- what Toner's tracheal traces would settle")
from apnoea_core import time_to  # noqa: E402

_pt = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)


def t95(fg, dur):
    r = simulate(_pt, [AirwayEpoch(dur, resistance=2, fgo2=fg)],
                 dt=DT, feo2_start=0.87, stop_sao2=0.0)
    t = time_to(r, 'spo2', 95)
    return 9999.0 if t is None else t


check("sham arm at FO2 0.21 (shipped; Toner IQR 405-525)", t95(0.21, 700), 402.0, 4.0, " s")
check("sham arm at FO2 0.30 (Toner median is 447)", t95(0.30, 700), 439.7, 5.0, " s")
check("buccal arm at FO2 0.60 (below this it fails)", t95(0.60, 900), 668.4, 8.0, " s")
print("    The SHAM assumption is the sensitive one: 0.21 is the only value")
print("    tested that falls BELOW Toner's IQR. The buccal arm holds to 750 s")
print("    anywhere at or above 0.70, so its traces would settle nothing.")

# ---------------------------------------------------------------------------
print("\nNOT REPRODUCIBLE, and recorded as such")
print("    Ellis 2022 pregnancy comparator: HANDOVER quotes 18.1 and 5.8 min")
print("    against their 25.4 and 9.9. The configuration behind those two")
print("    numbers was never written down. Regenerate them before using them.")
print("    Laviola 2020 airway rescue (38.7 vs 42.3 kPa) likewise.")

print()
if _fails:
    print(f"{len(_fails)} value(s) in HANDOVER.md have drifted:")
    for f in _fails:
        print(f"  - {f}")
    print("Either the model moved or the document is stale. Fix the document.")
    sys.exit(1)
print("Every number checked here still matches HANDOVER.md.")
