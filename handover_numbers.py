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


check("obstructed PaCO2 slope 60-300 s", slope(ro), 4.72, 0.10, " mmHg/min")
check("obstructed PACO2 slope", (at(ro, 'paco2_alv', 300) - at(ro, 'paco2_alv', 60)) / 4, 2.61, 0.10)
check("obstructed PvCO2 slope", (at(ro, 'pvco2', 300) - at(ro, 'pvco2', 60)) / 4, 1.80, 0.10)
check("patent PaCO2 slope 60-300 s", slope(rp), 1.68, 0.10, " mmHg/min")
check("patent PvCO2 slope", (at(rp, 'pvco2', 300) - at(rp, 'pvco2', 60)) / 4, 1.74, 0.10)
check("obstructed a-A gap growth", (gap(ro, 300) - gap(ro, 60)) / 4, 2.13, 0.10)
check("patent a-A gap growth", (gap(rp, 300) - gap(rp, 60)) / 4, -0.04, 0.10)
for t, g, sh, sa in ((60, -0.17, 0.0585, 100.0), (180, 1.52, 0.1033, 98.5),
                     (240, 6.48, 0.1406, 93.1), (300, 8.37, 0.1824, 84.9)):
    check(f"obstructed a-A gap at {t:3.0f} s", gap(ro, t), g, 0.4, " mmHg")
    check(f"obstructed shunt at {t:3.0f} s", 100 * at(ro, 'shunt', t), 100 * sh, 1.0, " %")

# ---------------------------------------------------------------------------
print("\nWhat the coupling is NOT")
check("shunt suppressed (max_closed 0.02): slope",
      slope(run(max_closed=0.02)), 4.97, 0.15, " mmHg/min")
check("hb 18, desaturation delayed: slope",
      slope(run(hb=18.0)), 4.24, 0.15, " mmHg/min")
check("p_collapse floor removed (-200): slope",
      slope(run(p_collapse=-200.0)), 4.72, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\ntau_mix -- the lever that acts on the a-A gap")
for tm, want in ((25.0, 6.24), (45.0, 4.72), (60.0, 4.00), (90.0, 3.09)):
    check(f"tau_mix {tm:5.1f}: Stock 1-5 min slope",
          slope(run(tau_mix=tm)), want, 0.12, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nvq_log_sd against Tokics 1996 (measured 0.80 isotope / 1.18 inert gas)")
for sd, want in ((0.50, 3.16), (0.70, 4.72), (0.80, 5.41), (1.18, 7.56)):
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
for g_, want in ((0.0025, 4.72), (0.00476, 4.66)):
    check(f"sv_itp_gain {g_:.5f}: Stock slope",
          slope(run(sv_itp_gain=g_)), want, 0.12, " mmHg/min")
check("stiff_below_rv 2.00: Stock slope",
      slope(run(stiff_below_rv=2.0)), 5.20, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nn_vq convergence -- arterial CO2 went the WRONG WAY below n_vq 80")
print("  CO2 cannot leave a clamped lung, so PaCO2 must rise monotonically.")
print("  Below 80 compartments it did not. The default was raised 20 -> 80 on")
print("  2026-09-18 for exactly that reason. These rows keep the evidence.")
for n_, want_slope, want_falls in ((20, 4.75, 24), (40, 4.74, 8),
                                   (80, 4.72, 0), (160, 4.71, 0)):
    r_ = run(n_vq=n_)
    falls = int((np.diff(r_['paco2']) < -1e-9).sum())
    check(f"n_vq {n_:3d}: Stock 1-5 min slope", slope(r_), want_slope, 0.15,
          " mmHg/min")
    check(f"n_vq {n_:3d}: steps where PaCO2 FALLS", float(falls),
          float(want_falls), 2.0, " steps")
print("    Raising the default bought CORRECTNESS, not accuracy. The slope")
print("    moves 4.75 -> 4.72 against a measured 3.4, and the a-A gap is")
print("    converged at ~8.4 mmHg from n_vq 60 upward. The disagreement is a")
print("    property of the model physics, not of its discretisation, and no")
print("    refinement will remove it. test_validation.py checks timestep")
print("    convergence and has never checked compartment-count convergence.")

# ---------------------------------------------------------------------------
print("\nvq_log_sd is a VOLUME dispersion, not a V/Q dispersion")
print("  It appears exactly once in apnoea_core.py, and its only product is")
print("  the gas-VOLUME share. Inflow follows volume, so specific ventilation")
print("  is uniform by construction and a PATENT run does have VA/Q dispersion")
print("  equal to vq_log_sd -- which is what makes the Tokics comparison look")
print("  legitimate. Under obstruction there is no ventilation, so all that is")
print("  left is VOLUME per perfusion. We calibrate a volume distribution")
print("  against a ventilation measurement. See HANDOVER, 'Where to look next'.")


def first_min(r_):
    return at(r_, 'paco2', 60) - at(r_, 'paco2', 0)


for sd, w_obs, w_pat, w_gap, w_r1 in ((0.30, 1.89, 1.65, -0.91, 12.13),
                                      (0.40, 2.42, 1.66, 1.03, 12.11),
                                      (0.50, 3.16, 1.66, 3.60, 12.08),
                                      (0.70, 4.72, 1.68, 8.35, 12.02)):
    r_o = run(vq_log_sd=sd)
    r_p = run(vq_log_sd=sd, obstructed=False)
    check(f"vq_log_sd {sd:4.2f}: obstructed slope (Stock 3.4)", slope(r_o),
          w_obs, 0.15, " mmHg/min")
    check(f"vq_log_sd {sd:4.2f}: PATENT slope", slope(r_p), w_pat, 0.15,
          " mmHg/min")
    check(f"vq_log_sd {sd:4.2f}: a-A gap at 300 s", gap(r_o, 300), w_gap, 0.40,
          " mmHg")
    check(f"vq_log_sd {sd:4.2f}: first-minute rise (Stock 12)", first_min(r_o),
          w_r1, 0.25, " mmHg")
print("    The PATENT arm is inert across the whole range, 1.65 to 1.72, which")
print("    is why no patent-airway dataset could ever have caught this. The")
print("    first-minute rise is inert too, 11.8 to 12.1 against a measured 12,")
print("    so the bulk CO2 bookkeeping is right at every value and only the")
print("    gap moves. And the a-A gap CHANGES SIGN between 0.30 and 0.40: a")
print("    hard bracket, not a fitted one. Below it the model has arterial CO2")
print("    running BELOW alveolar inside a sealed lung.")
print("    Stock's 3.4 wants a volume dispersion near 0.50. That is NOT")
print("    permission to set it there. What is needed is a measurement of")
print("    regional gas volume per unit perfusion, which is not in this")
print("    repository and is not what Tokics measured.")

# ---------------------------------------------------------------------------
print("\nvq_log_sd is NOT the log QSD it is compared against")
print("  The z grid is linspace(-2.2, 2.2, n). Truncating a Gaussian at 2.2")
print("  sigma discards the tails, so the discrete distribution has SD 0.9206")
print("  and model log QSD = 0.9206 * vq_log_sd. Tokics Table 3 also reports")
print("  log VSD, which this file used to ignore; the model forces the two")
print("  equal, so it can represent the ISOTOPE lung (0.80 / 0.78) and cannot")
print("  represent the MIGET lung (1.18 / 0.62) at all.")


def log_moments(sd, n=None):
    """Perfusion- and ventilation-weighted SD of ln(VA/Q) over the grid."""
    q = Patient(weight=70, height=1.75, age=45, hb=15.0, vq_log_sd=sd,
                **({'n_vq': n} if n else {}))
    w, vol = q.vq_distribution()
    zz = np.linspace(-2.2, 2.2, q.n_vq)
    lr = sd * zz

    def lsd(wt):
        wt = wt / wt.sum()
        return float(np.sqrt(wt @ (lr - float(wt @ lr)) ** 2))

    return lsd(w), lsd(vol)


_z = np.linspace(-2.2, 2.2, 80)
_w = _z * 0 + np.exp(-0.5 * _z * _z)
_w = _w / _w.sum()
check("truncation factor at n_vq 80 (would be 1.0 untruncated)",
      float(np.sqrt(_w @ (_z - float(_w @ _z)) ** 2)), 0.9206, 0.002, "")
for sd, w_q, w_v in ((0.50, 0.460, 0.448), (0.70, 0.644, 0.612),
                     (0.869, 0.800, 0.739), (1.282, 1.180, 1.002)):
    q_, v_ = log_moments(sd)
    check(f"vq_log_sd {sd:5.3f}: model log QSD", q_, w_q, 0.006, "")
    check(f"vq_log_sd {sd:5.3f}: model log VSD", v_, w_v, 0.006, "")
print("    Tokics 1996 Table 3, read from the page 2026-09-18:")
print("      awake, inert gas          log QSD 0.67 +- 0.07  log VSD 0.54 +- 0.06")
print("      anaesthetised, inert gas  log QSD 1.18 +- 0.12  log VSD 0.62 +- 0.05")
print("      anaesthetised, isotope    log QSD 0.80 +- 0.04  log VSD 0.78 +- 0.04")
print("    The shipped 0.70 DELIVERS 0.644 -- below even the awake 0.67. This")
print("    file used to say we pass because 0.70 is 'below measurement'. It is")
print("    further below it than that.")
for sd, want, lab in ((0.869, 5.85, "isotope log QSD 0.80"),
                      (1.282, 8.25, "inert-gas log QSD 1.18")):
    check(f"at the TRUE {lab}: Stock slope", slope(run(vq_log_sd=sd)), want,
          0.15, " mmHg/min")
print("    Correcting the comparison makes the benchmark WORSE: 5.41 -> 5.85")
print("    and 7.56 -> 8.25 against a measured 3.4. Recorded, not compensated.")
print("    The grid was NOT widened. Truncating at 2.2 sigma is a legitimate")
print("    discretisation; comparing the PARAMETER to a measured log QSD was")
print("    the error. Widening to 3 or 4 sigma would move every benchmark in")
print("    the suite, so it is a decision and it is left open.")
print("    Neither Tokics nor Rothen measures regional gas VOLUME against")
print("    regional perfusion, which is what would settle the block above.")
print("    Tokics' only volume figure is whole-lung: 'the calculated mean gas")
print("    volume (FRC) approximates 2.0 liters', against our 2012 mL.")

# ---------------------------------------------------------------------------
print("\nSeparability -- the CO2 limb and the mechanics limb are NOT coupled")
print("  HANDOVER said the compliance fix exposed a trade-off that 'every lung")
print("  volume lever produces'. That was asserted, not tested. These rows are")
print("  the test: the Moreault pressure against the Stock slope, one lever at")
print("  a time. Mixing and dispersion move the slope by a factor of two and")
print("  the pressure by a tenth of a percent.")
from apnoea_core import PB, PH2O  # noqa: E402


def moreault_p(ml=1008.0, **kw):
    """Airway pressure once `ml` of gas, measured at atmospheric, has gone.

    The same construction as test_validation.test_moreault_2021: their
    volumes were read at atmospheric pressure, and the lung shrinks by less
    than the gas that leaves it because the remainder rarefies.
    """
    q = Patient(weight=70, height=1.75, age=45, hb=14.0, **kw)
    r_ = simulate(q, [AirwayEpoch(420.0, resistance=OBS, fgo2=0.21)],
                  dt=0.1, stop_sao2=0.0)
    n_atm = r_['va'] * (PB + r_['palv_cmh2o'] / 1.35951 - PH2O) / (PB - PH2O)
    lost = n_atm[0] - n_atm
    assert lost[-1] >= ml, f"only {lost[-1]:.0f} mL absorbed in 420 s"
    return float(r_['palv_cmh2o'][int(np.argmax(lost >= ml))])


_base_p = moreault_p()
check("baseline Moreault P at 1008 mL", _base_p, -17.7, 0.4, " cmH2O")
for lab, kw, want_s, want_p in (
        ("tau_mix 25", dict(tau_mix=25.0), 6.24, -17.7),
        ("tau_mix 90", dict(tau_mix=90.0), 3.09, -17.7),
        ("vq_log_sd 0.50", dict(vq_log_sd=0.50), 3.16, -17.7),
        ("vq_log_sd 1.18", dict(vq_log_sd=1.18), 7.56, -17.7),
        ("crs 60", dict(crs=60.0), 4.37, -24.2),
        ("crs 110", dict(crs=110.0), 4.92, -14.0),
        ("stiff_below_rv 0.05", dict(stiff_below_rv=0.05), 4.11, -27.3),
        ("rv 900", dict(rv=900.0), 5.17, -11.7),
        ("rv 1300", dict(rv=1300.0), 4.27, -32.0)):
    check(f"{lab}: Stock slope", slope(run(**kw)), want_s, 0.15, " mmHg/min")
    check(f"{lab}: Moreault P at 1008 mL", moreault_p(**kw), want_p, 0.5,
          " cmH2O")
print("    Neither CO2 lever moves the pressure at all. The mechanics levers")
print("    move the slope by about 10%, so the coupling runs ONE WAY and")
print("    weakly. The two red limbs are separable and can be worked apart.")
print("    tau_mix 90 and vq_log_sd 0.50 each put the Stock slope back inside")
print("    its 2.4-4.4 band on their own, with the mechanics untouched, which")
print("    is exactly why neither may be set there. A fit is not a mechanism.")

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
