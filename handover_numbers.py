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


check("obstructed PaCO2 slope 60-300 s", slope(ro), 4.35, 0.10, " mmHg/min")
check("obstructed PACO2 slope", (at(ro, 'paco2_alv', 300) - at(ro, 'paco2_alv', 60)) / 4, 2.63, 0.10)
check("obstructed PvCO2 slope", (at(ro, 'pvco2', 300) - at(ro, 'pvco2', 60)) / 4, 2.01, 0.10)
check("patent PaCO2 slope 60-300 s", slope(rp), 1.70, 0.10, " mmHg/min")
check("patent PvCO2 slope", (at(rp, 'pvco2', 300) - at(rp, 'pvco2', 60)) / 4, 1.80, 0.10)
check("obstructed a-A gap growth", (gap(ro, 300) - gap(ro, 60)) / 4, 1.72, 0.10)
check("patent a-A gap growth", (gap(rp, 300) - gap(rp, 60)) / 4, -0.04, 0.10)
for t, g, sh, sa in ((60, -0.2, 0.058, 100.0), (180, 1.3, 0.103, 98.5),
                     (240, 6.3, 0.140, 93.1), (300, 6.7, 0.181, 84.9)):
    check(f"obstructed a-A gap at {t:3.0f} s", gap(ro, t), g, 0.4, " mmHg")
    check(f"obstructed shunt at {t:3.0f} s", 100 * at(ro, 'shunt', t), 100 * sh, 1.0, " %")

# ---------------------------------------------------------------------------
print("\nWhat the coupling is NOT")
check("shunt suppressed (max_closed 0.02): slope",
      slope(run(max_closed=0.02)), 4.50, 0.15, " mmHg/min")
check("hb 18, desaturation delayed: slope",
      slope(run(hb=18.0)), 3.91, 0.15, " mmHg/min")
check("p_collapse floor removed (-200): slope",
      slope(run(p_collapse=-200.0)), 4.29, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\ntau_mix -- the lever that acts on the a-A gap")
for tm, want in ((25.0, 5.77), (45.0, 4.35), (60.0, 3.85), (90.0, 2.99)):
    check(f"tau_mix {tm:5.1f}: Stock 1-5 min slope",
          slope(run(tau_mix=tm)), want, 0.12, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nvq_log_sd against Tokics 1996 (measured 0.80 isotope / 1.18 inert gas)")
for sd, want in ((0.50, 3.07), (0.70, 4.35), (0.80, 5.02), (1.18, 7.44)):
    check(f"vq_log_sd {sd:4.2f}: Stock 1-5 min slope",
          slope(run(vq_log_sd=sd)), want, 0.15, " mmHg/min")
check("baseline shunt (Tokics measured 7.0 +- 1.3%)",
      100 * ro['shunt'][0], 5.0, 0.5, " %")

# ---------------------------------------------------------------------------
print("\nsv_itp_gain -- nearly inert on the knot (human data give 0.0033-0.00476)")
for g_, want in ((0.0025, 4.35), (0.00476, 4.24)):
    check(f"sv_itp_gain {g_:.5f}: Stock slope",
          slope(run(sv_itp_gain=g_)), want, 0.12, " mmHg/min")
check("stiff_below_rv 2.00: Stock slope",
      slope(run(stiff_below_rv=2.0)), 5.15, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nThe CO2 dissociation curve -- its CURVATURE drives the a-A gap")
import bloodgas as bg  # noqa: E402
for pco2, want in ((40, 50.96), (60, 59.15), (80, 65.43), (100, 70.63)):
    ph = bg.ph_from_pco2_be(pco2, 0.0, 15.0, so2=0.97, temp=37.0)
    check(f"CCO2 at PCO2 {pco2:3d}, SO2 0.97, Hb 15",
          bg.co2_content(pco2, ph, 0.97, 15.0, 37.0), want, 0.15, " mL/dL")
print("    (textbook arterial anchor is about 48 mL/dL at PCO2 40; we read high,")
print("     which bloodgas.py records. The CURVATURE has never been checked --")
print("     that needs Kelman 1967.)")

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
