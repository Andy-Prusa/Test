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
from scipy.optimize import brentq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apnoea_core as ac  # noqa: E402
from apnoea_core import (AirwayEpoch, Patient, simulate,  # noqa: E402
                         time_to)

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
print("\nTHE RECOIL FLOOR: WAS INCOHERENT, NOW INERT BY RULING")
print("  The argument that found it: if the patient still has a cardiac")
print("  output, gas is still being absorbed, and in a sealed lung that gas")
print("  must come out of volume or out of pressure. _recoil returns")
print("  max(p, floor): at p_collapse = -50 the PRESSURE was clamped and the")
print("  VOLUME was not, so from 361 s the model reported a pressure its own")
print("  recoil function contradicted by up to 21 cmH2O.")
print("  RULING (A.H., 2026-09-20): there is no data below about -20 cmH2O")
print("  and there never will be, so put the floor at minus the systolic")
print("  pressure and move on. That is a convention, not a derivation.")
_cl = Patient(weight=70, height=1.75, age=45, hb=14.0)
_clr = simulate(_cl, [AirwayEpoch(900, resistance=OBS, fgo2=0.21)],
                dt=0.1, stop_sao2=0.0)
check("floor = -SBP_SUPINE * 1.35951", ac.P_COLLAPSE, -149.5461, 0.001,
      " cmH2O")
check("shipped Patient carries it", _cl.p_collapse, -149.5461, 0.001, " cmH2O")


def _recoil_unclamped(v):
    """What _recoil returns WITHOUT the max(p, floor), in cmH2O."""
    _p = (v - _cl.frc_anaes()) / (_cl.crs * 1.35951)
    if v < _cl.rv:
        _p += (v - _cl.rv) / (_cl.crs * 1.35951 * _cl.stiff_below_rv)
    return _p * 1.35951


print("    The contradiction is gone: reported pressure IS the recoil now.")
for _t, _v, _pw in ((300, 845.4, -33.69), (420, 529.9, -62.15),
                    (540, 439.1, -70.35), (590, 438.1, -70.44)):
    check(f"volume at {_t} s", at(_clr, 'va', _t), _v, 3.0, " mL")
    check(f"pressure REPORTED at {_t} s", at(_clr, 'palv_cmh2o', _t), _pw,
          0.6, " cmH2O")
    check(f"pressure its own RECOIL implies at {_t} s",
          _recoil_unclamped(at(_clr, 'va', _t)), _pw, 0.6, " cmH2O")

# The floor is INERT. Not "small" -- bit-identical to having no floor at all.
_nof = simulate(Patient(weight=70, height=1.75, age=45, hb=14.0,
                        p_collapse=-1e6),
                [AirwayEpoch(900, resistance=OBS, fgo2=0.21)],
                dt=0.1, stop_sao2=0.0)
print("    Against a run with NO floor at all (p_collapse -1e6), the largest")
print("    difference in any output over the whole 900 s:")
for _k in ('va', 'palv_cmh2o', 'pao2', 'paco2', 'sao2', 'ph', 'co', 'map'):
    check(f"max |shipped - no floor|, {_k}",
          float(np.abs(_clr[_k] - _nof[_k]).max()), 0.0, 1e-9, "")

print("    And nothing comes near it. Minimum pressure reached, floor set to")
print("    -1e6 so it cannot bind, across the configurations that push the")
print("    lung hardest:")
for _name, _kw, _fg, _want in (
        ("default air seal", {}, 0.21, -70.44),
        ("preoxygenated seal", {}, 1.0, -70.44),
        ("obese 120 kg / 1.70 m", dict(weight=120, height=1.70), 0.21, -68.60),
        ("vo2_ref 400", dict(vo2_ref=400.0), 0.21, -70.65),
        ("no terminal bradycardia", dict(hr_term_sao2=0.0), 0.21, -71.51),
        ("no bradycardia + vo2_ref 400",
         dict(hr_term_sao2=0.0, vo2_ref=400.0), 0.21, -73.31)):
    _k2 = dict(_kw)
    _p2 = Patient(weight=_k2.pop('weight', 70), height=_k2.pop('height', 1.75),
                  age=45, hb=14.0, p_collapse=-1e6, **_k2)
    _r2 = simulate(_p2, [AirwayEpoch(900, resistance=OBS, fgo2=_fg)],
                   dt=0.1, stop_sao2=0.0)
    check(f"min P, {_name}", float(_r2['palv_cmh2o'].min()), _want, 0.6,
          " cmH2O")
print("    Every one asymptotes near -70, roughly 78 cmH2O clear of the")
print("    floor. THE RUNAWAY p_collapse WAS GUARDING AGAINST DOES NOT")
print("    EXIST. The model already had its own terminator and nobody had")
print("    looked: the absorption gradient closes. Alveolar PO2 falls to")
print("    mixed venous PO2 and there is nothing left to take up, while CO2")
print("    coming out of blood holds the residual volume. Below, with the")
print("    heart forced to keep beating for 1800 s so nothing else can stop")
print("    it:")
_pz = Patient(weight=70, height=1.75, age=45, hb=14.0, p_collapse=-1e6,
              hr_term_sao2=0.0)
_rz = simulate(_pz, [AirwayEpoch(1800, resistance=OBS, fgo2=0.21)],
               dt=0.1, stop_sao2=0.0)
for _t, _pa, _pv in ((300, 375.50, 40.72), (540, 21.03, 12.84),
                     (900, 1.43, 0.0), (1790, 0.0, 0.0)):
    check(f"alveolar PO2 at {_t} s", at(_rz, 'pao2_alv', _t), _pa, 1.5,
          " mmHg")
    check(f"mixed venous PO2 at {_t} s", at(_rz, 'pvo2', _t), _pv, 1.5,
          " mmHg")
check("alveolar PCO2 at 1790 s, holding the volume up",
      at(_rz, 'paco2_alv', 1790), 74.59, 1.5, " mmHg")
check("min pressure over 1800 s, unclamped", float(_rz['palv_cmh2o'].min()),
      -71.62, 0.6, " cmH2O")
check("min volume over 1800 s, unclamped", float(_rz['va'].min()), 425.0,
      4.0, " mL")
print("    What the move COSTS, since it is not free: the ITP stroke-volume")
print("    term is now charged over the whole fall instead of being frozen")
print("    at the old clamp. At the -70.4 asymptote the factor is 0.892")
print("    against 0.925 at -50 -- the 3.2 points the clamp was not")
print("    charging. Gas tensions move by about 2% of dry pressure, which is")
print("    NOT the oxygen defect: that is at 300 s, before the old clamp")
print("    ever bound, and is unchanged to 0.01 mmHg by this.")
_G2, _F2 = _cl.sv_itp_gain, _cl.itp_fraction
check("sv factor at the -70.4 asymptote",
      max(0.15, 1.0 + _G2 * -70.44 * _F2), 0.8943, 0.002, "")
check("sv factor at the old -50 clamp",
      max(0.15, 1.0 + _G2 * -50.0 * _F2), 0.925, 0.002, "")
print("    STILL NOT MODELLED, and the floor is now the only thing standing")
print("    in for them: units closing and ceasing to absorb, a chest-wall or")
print("    mediastinal hard limit, and flow stopping. The difference is that")
print("    the floor no longer touches any result, so those absences are now")
print("    visible instead of being absorbed into a clamped number.")

print("\nIS THERE A NEGATIVE PRESSURE THAT PREVENTS CARDIAC OUTPUT? No.")
print("  Condos 1987, n=10 at cardiac catheterisation, Mueller: mean RIGHT")
print("  ATRIAL pressure 7 -> -17 mmHg and cardiac output fell only 6.0 ->")
print("  5.3 L/min (12%), stroke volume 83 -> 74 mL. Their mechanism, echo-")
print("  confirmed: COLLAPSE OF THE GREAT VENOUS TRUNKS AT THE THORACIC")
print("  INLETS, which LIMITS venous return without abolishing it and raises")
print("  the driving pressure downstream of itself. The venous return curve")
print("  plateaus; it does not fall to zero.")
_pt_itp = Patient(weight=70, height=1.75, age=45, hb=14.0)
_G, _F = _pt_itp.sv_itp_gain, _pt_itp.itp_fraction
check("sv factor at our -50 clamp (pleural -30)",
      max(0.15, 1.0 + _G * -50.0 * _F), 0.925, 0.002, "")
check("alveolar cmH2O needed for the max(0.15) floor to bind",
      (0.15 - 1.0) / _G / _F, -566.7, 1.0, " cmH2O")
print("    So OUR model also says no -- but with no venous-return curve and")
print("    nothing representing caval collapse. The term is pure afterload,")
print("    fitted at -30 cmH2O and extrapolated as a straight line. The floor")
print("    needs -567 cmH2O to bind, about where Hardman & Wills' NPS goes.")
_itpr = simulate(_pt_itp, [AirwayEpoch(900, resistance=OBS, fgo2=0.21)],
                 dt=0.1, stop_sao2=0.0)
check("CO at 240 s (baseline 3.75) -- it RISES", at(_itpr, 'co', 240),
      4.51, 0.08, " L/min")
check("pleural pressure at 240 s", at(_itpr, 'palv_cmh2o', 240) * _F,
      -9.1, 0.4, " cmH2O")
print("    CO climbs 20% to 240 s while pleural pressure falls to -9:")
print("    hypercapnic inotropy and tachycardia outrun the ITP penalty, and")
print("    the eventual collapse is hypoxic bradycardia, not mechanics.")
print("    CONDOS'S SUBJECTS WERE NORMOCAPNIC, so their 12% is the ITP effect")
print("    clean. We have NO comparator anywhere for negative ITP PLUS")
print("    hypercapnia -- the actual apnoea case, and exactly the combination")
print("    our model resolves in favour of the inotropy. Unvalidated.")

# ---------------------------------------------------------------------------
print("\nWHY PaO2 DOES NOT FOLLOW STOCK: the alveolus is fine, the step to")
print("the artery is not")


def _o2run(**kw):
    q = Patient(weight=70, height=1.75, age=45, hb=15.0, **kw)
    return simulate(q, [AirwayEpoch(360, resistance=OBS, fgo2=0.21)],
                    dt=DT, feo2_start=0.87, paco2_start=39.0, stop_sao2=0.0)


_o2 = _o2run()
check("PAO2 at 300 s (ALVEOLAR; Stock's ARTERIAL is 314)",
      at(_o2, 'pao2_alv', 300), 379.0, 4.0, " mmHg")
check("PaO2 at 300 s (arterial; Stock 314 +- 87)",
      at(_o2, 'pao2', 300), 60.5, 1.5, " mmHg")
print("    The alveolar value sits ABOVE Stock's arterial, which is where an")
print("    alveolar value belongs. Everything is lost after the alveolus.")
print("    Four levers, PaO2 at 300 s: p_collapse -200 gives 60.5 (+0%),")
print("    max_closed 0.02 gives 62.2 (+3%), co_drop_frac 0 gives 67.4")
print("    (+11%), both circulation levers 67.5 (+12%). Together they buy")
print("    12% of a gap that needs 400%.")
print("    AND IT IS NOT THE SAME DEFECT AS THE CO2 GAP. Hypothesis tested")
print("    and refuted: at the dispersion that ZEROES the CO2 gap, a large")
print("    oxygen gap remains.")
for _sd, _wpo2, _wgap in ((0.30, 96.0, 224.0), (0.70, 61.0, 319.0)):
    _r = _o2run(vq_log_sd=_sd)
    check(f"vq_log_sd {_sd:.2f}: PaO2 at 300 s", at(_r, 'pao2', 300),
          _wpo2, 2.0, " mmHg")
    check(f"vq_log_sd {_sd:.2f}: a-A OXYGEN gap at 300 s",
          at(_r, 'pao2_alv', 300) - at(_r, 'pao2', 300), _wgap, 4.0, " mmHg")
print("    CO2 gap is dispersion-driven; the OXYGEN gap has a large")
print("    dispersion-INDEPENDENT floor. Two different defects.")
print("    Surviving candidate: the FLATNESS of the oxygen dissociation curve")
print("    at high PO2 -- end-capillary blood is saturated, so mixing in a")
print("    little venous blood costs little CONTENT and enormous TENSION.")
print("    NEXT TEST: sweep shunt_base, not max_closed. max_closed suppresses")
print("    CLOSURE-driven shunt and was nearly inert, which is consistent.")

# ---------------------------------------------------------------------------
print("\nWHAT THE DEFECTS DO TO THE ANSWERS -- the obstructed SpO2 milestones")
print("  Stock measured every one of 14 patients above 92% at all times, with")
print("  7 completing 300 s. Hardman & Wills put SaO2 90->40% at 1.56 min.")
print("  The two anchors pull OPPOSITE ways and we sit wrong against both.")
_ms = simulate(Patient(weight=70, height=1.75, age=45, hb=15.0),
               [AirwayEpoch(1600.0, resistance=OBS, fgo2=0.21)],
               dt=DT, feo2_start=0.87, stop_sao2=0.0)
for _s, _w in ((95, 257.6), (92, 284.6), (90, 300.4), (80, 364.6), (40, 543.8)):
    check(f"obstructed: SpO2 reaches {_s}%", float(time_to(_ms, 'spo2', _s)),
          _w, 4.0, " s")
_t90 = float(time_to(_ms, 'spo2', 90))
_t40 = float(time_to(_ms, 'spo2', 40))
check("obstructed: SaO2 90->40% rate (H&W say 33)",
      50 * 60.0 / (_t40 - _t90), 12.3, 0.3, " %/min")
print("    We cross 92% at 285 s, where Stock had every patient above it at")
print("    300 s: TOO EARLY. Then 90->40% takes 4.06 min against their 1.56:")
print("    THREE TIMES TOO SLOW. The total, 544 s, agrees with Laviola's ~510")
print("    BY CANCELLATION. So 'when does desaturation start' is pessimistic,")
print("    'time to critical' is right by luck, and 'once they start dropping,")
print("    how long have I got' is DANGEROUSLY OPTIMISTIC -- four minutes")
print("    against the only other model's ninety seconds.")
print("    The buccal work is NOT contaminated: all four Toner and Heard")
print("    benchmarks run patent(), and buccal oxygen buys nothing once")
print("    occluded anyway. Our patent-regime oxygen is +13% and +22%.")
print("    BEYOND 300 s OF COMPLETE OBSTRUCTION THERE IS NO HUMAN")
print("    MEASUREMENT AT ALL. Stock's table stops there.")

# ---------------------------------------------------------------------------
print("\nStock's pH column is a BUFFER MEASUREMENT, and we never used it")
print("  Table 1 pairs pH with PaCO2 at eight times, in humans, under")
print("  COMPLETE OBSTRUCTION. Paired, they are the CO2 titration line")
print("  dpH/dlog10(PCO2) -- a direct measurement of effective in-vivo buffer")
print("  capacity in our own regime. We had only ever checked pH at 300 s.")
_ST_T = np.array([0, 20, 40, 60, 120, 180, 240, 300], float)
_ST_P = np.array([39, 44, 48, 50, 53, 56, 59, 63], float)
_ST_H = np.array([7.42, 7.38, 7.35, 7.34, 7.32, 7.31, 7.28, 7.26])
_titr = lambda pc, ph: float(np.polyfit(np.log10(pc), ph, 1)[0])
check("Stock's measured titration line (8 points)", _titr(_ST_P, _ST_H),
      -0.758, 0.004, " per decade")
_stock_titr = simulate(Patient(weight=70, height=1.75, age=45, hb=15.0),
               [AirwayEpoch(360, resistance=OBS, fgo2=0.21)],
               dt=DT, feo2_start=0.87, paco2_start=39.0, stop_sao2=0.0)
_mp = np.array([at(_stock_titr, 'paco2', t) for t in _ST_T])
_mh = np.array([at(_stock_titr, 'ph', t) for t in _ST_T])
check("our titration line at the same points", _titr(_mp, _mh),
      -0.669, 0.006, " per decade")
print("    In vitro whole blood titrates near -0.55 per decade; whole-body /")
print("    extracellular fluid near -0.75 to -0.80. Stock measures -0.758 and")
print("    Ebata -0.837, so BOTH human datasets land on the in-vivo value and")
print("    we sit between the two, closer to in-vitro. Our buffering is")
print("    measurably too strong, in the direction of Hardman 1998's ECF 11.6")
print("    -- the region the Douglas pole blocks. Sourced, and NOT the cause")
print("    of the failing slope: the sweep moves it 7% over a 2.5-fold span,")
print("    and steepening toward -0.76 pushes the first-minute rise to 13.29.")
print("  AND THE CO2 DEFECT SWITCHES ON AT ABOUT 200 s")
print("      t    Stock    ours")
for _i, _t in enumerate(_ST_T):
    print(f"    {_t:4.0f}    {_ST_P[_i]:5.0f}   {_mp[_i]:6.1f}")
check("we track Stock to within ~1 mmHg at 180 s", _mp[5] - _ST_P[5],
      0.4, 0.5, " mmHg")
check("and are +6.4 out by 300 s", _mp[7] - _ST_P[7], 6.4, 0.5, " mmHg")
print("    That kills any explanation acting uniformly in time -- the")
print("    buffering, the dissociation curve and the stores all act from t=0.")
print("    What starts at 200 s is the lung having shrunk far enough for the")
print("    shunt to climb, which is where the perfusion-weighted-content")
print("    against volume-weighted-fraction asymmetry lives.")

# ---------------------------------------------------------------------------
import bloodgas as _bg  # noqa: E402
print("\nThe Douglas red-cell pole sits ON the inverse's lower bracket")
print("  co2_content's RBC correction has a pole at pH 8.142. bloodgas.py's")
print("  own note says it is reached by 'any PCO2 below about 2.4 mmHg'.")
print("  Measured at BE 0 / Hb 15 the content is already NEGATIVE at 3.0 --")
print("  and 3.0 is exactly where pco2_from_co2_content sets its lower")
print("  bracket. Content rises monotonically from there in the shipped")
print("  configuration so brentq still finds the right root, which is why")
print("  this has never bitten. It is one sign change away from biting: at")
print("  the ECF buffer capacity Hardman 1998 uses, pH at PCO2 3 goes PAST")
print("  the pole and content wraps to +74.86, the inverse clamps PaCO2 to")
print("  3.0 for the whole run, and every CO2 result becomes 0.00.")
_zf = (lambda pp: _bg.co2_content(
    pp, _bg.ph_from_pco2_be(pp, 0.0, 15.0, so2=0.97, temp=37.0),
    0.97, 15.0, 37.0))
check("CO2 content at PCO2 3.0, BE 0, Hb 15", _zf(3.0), -11.46, 0.30, " mL/dL")
check("PCO2 where CO2 content crosses ZERO",
      float(brentq(_zf, 2.0, 8.0, xtol=1e-9)), 3.935, 0.02, " mmHg")
print("    Recorded as a defect, not fixed: fixing it changes no benchmark in")
print("    the accessible range and should be done deliberately.")

# ---------------------------------------------------------------------------
print("\nThe acid-base lever is REFUTED")
print("  Hardman 1998 made the strength of the acid-base response the")
print("  untested lever on the CO2 limb. Swept it; it is not the answer.")
print("  Lever: the Siggaard-Andersen non-bicarbonate buffer capacity in")
print("  ph_from_pco2_be, (9.5 + 1.63*cHb), which is 24.7 at Hb 15 -- the")
print("  IN VITRO whole-blood value. Hardman 1998 uses 11.6 flat, the")
print("  EXTRACELLULAR FLUID value, a factor of 2.13 apart.")
print("    buffer   beta   Stock   patent    a-A   1st min")
print("      x0.8   19.7    4.68     1.91    6.82    13.29")
print("      x1.0   24.7    4.72     1.68    8.35    12.02   <- shipped")
print("      x1.5   37.0    4.85     1.35   10.27    10.04")
print("      x2.0   49.3    5.02     1.17   11.77     8.89")
print("    Over a 2.5-fold span the Stock slope moves 7% while the")
print("    first-minute rise swings 50% -- and the rise is the quantity that")
print("    currently matches Stock's measured 12 almost exactly. Weak lever")
print("    on what fails, strong lever on what works, and the direction that")
print("    helps the slope is the direction that breaks the rise.")
print("    Moreault stays -17.7 at every level, so separability holds here")
print("    too. Below beta 19.7 the sweep is INVALID -- see the pole above.")

# ---------------------------------------------------------------------------
print("\nThe CO2 curve's CURVATURE IS the acid-base response, and the a-A")
print("gap scales with it BACKWARDS")
print("  Hardman 1998 Appendix 2 gives the NPS CO2 content equation as")
print("    CaCO2 (ml/litre) = PaCO2 x 50.76 / 10^(0.019 x (temp - 37))")
print("  Linear in PaCO2: no bicarbonate curve, no pH term, no haemoglobin,")
print("  no saturation, so no Haldane. At FIXED pH our own law is already")
print("  exactly that form -- strictly proportional -- so the entire curvature")
print("  of the physiological curve is the acid-base response.")
_c40 = _bg.co2_content(40.0, 7.40, 0.97, 15.0, 37.0)
check("at pH 7.40 FIXED, dC/dP over 40-50", 
      (_bg.co2_content(50.0, 7.40, 0.97, 15.0, 37.0) - _c40) / 10.0,
      1.168, 0.004, " mL/dL/mmHg")
check("at pH 7.40 FIXED, dC/dP over 50-60",
      (_bg.co2_content(60.0, 7.40, 0.97, 15.0, 37.0)
       - _bg.co2_content(50.0, 7.40, 0.97, 15.0, 37.0)) / 10.0,
      1.168, 0.004, " mL/dL/mmHg")
check("the same law is PROPORTIONAL: C(40)/40", _c40 / 40.0, 1.168, 0.004, "")
_cs = {}
for _p in (40.0, 50.0, 60.0):
    _ph = _bg.ph_from_pco2_be(_p, 0.0, 15.0, so2=0.97, temp=37.0)
    _cs[_p] = _bg.co2_content(_p, _ph, 0.97, 15.0, 37.0)
check("with pH SOLVED from BE 0, dC/dP over 40-50",
      (_cs[50.0] - _cs[40.0]) / 10.0, 0.450, 0.006, " mL/dL/mmHg")
check("with pH SOLVED from BE 0, dC/dP over 50-60",
      (_cs[60.0] - _cs[50.0]) / 10.0, 0.381, 0.006, " mL/dL/mmHg")
print("    Flat 1.168 at frozen pH against 0.45 falling to 0.38 with pH")
print("    responding. The plasma algebra contributes NO curvature at all.")
print("    Substituting the NPS form into our 80-compartment lung (anchored")
print("    at PCO2 40, which is the same line either way because the fixed-pH")
print("    law passes through the origin):")
print("      Stock obstructed slope   4.72 -> 10.38   (measured 3.4)")
print("      patent slope             1.68 ->  0.55")
print("      a-A gap at 300 s         8.35 -> 32.81")
print("      first-minute rise       12.02 ->  4.59   (measured 12)")
print("    THIS FILE SAID THE a-A GAP 'SCALES WITH THE CURVATURE'. The sign is")
print("    backwards: removing the curvature QUADRUPLES the gap. Curvature")
print("    SUPPRESSES it. And it explains why Kelman looked exonerating -- the")
print("    [Hb] fix changed the curve's LEVEL and never varied the acid-base")
print("    coupling that generates the curvature, so that hypothesis was")
print("    untested until now. The untested lever is the STRENGTH of the")
print("    acid-base response, not the curve's calibration.")

# ---------------------------------------------------------------------------
print("\nHardman & Wills 2006 -- the obstruction effect has the WRONG SIGN")
print("  BJA 2006;97:564-70. MODEL, not measurement. Nottingham Physiology")
print("  Simulator, the lineage ICSM is built on. The first comparator we")
print("  hold that runs BOTH open and closed airway. Their 18-yr-old: 170 cm,")
print("  54 kg, Hb 140 g/L, Crs 144 mL/cmH2O, CO 5100, VO2 250, FRC 1769.")
print("  feo2_start is matched to their stated post-preoxygenation PaO2 (81")
print("  kPa at 3 min), so this compares apnoea dynamics and not how each")
print("  model preoxygenates.")
_hw = Patient(weight=54.0, height=1.70, age=18, hb=14.0)


def _hw_run(obstructed):
    ep = AirwayEpoch(1800.0, resistance=OBS if obstructed else 2.0, fgo2=0.21)
    return simulate(_hw, [ep], dt=DT, feo2_start=0.98, stop_sao2=0.0)


for _obst, _lab, _we, _wl, _rate in ((True, "closed", 5.60, 5.07, 32.1),
                                   (False, "open", 9.25, 3.22, 22.7)):
    _r = _hw_run(_obst)
    _t90, _t40 = time_to(_r, 'sao2', 90), time_to(_r, 'sao2', 40)
    _e, _tot = _t90 / 60.0, _t40 / 60.0
    check(f"H&W 3min preO2 {_lab}: to SaO2 90% (theirs "
          f"{6.54 if _obst else 8.40})", _e, _we, 0.15, " min")
    check(f"H&W 3min preO2 {_lab}: SaO2 90->40% (theirs "
          f"{1.56 if _obst else 2.20})", _tot - _e, _wl, 0.15, " min")
    print(f"      terminal rate: ours {50.0/(_tot-_e):5.1f} %/min, "
          f"theirs {_rate:4.1f}")
print("    Closing the airway makes THEIR patient desaturate FASTER (33 vs 26")
print("    %/min) and makes OURS desaturate SLOWER (9.9 vs 15.5). That is a")
print("    DIRECTION disagreement, the first this project has found.")
print("    Their mechanism is explicit: alveolar PO2 is the product of")
print("    intra-alveolar PRESSURE and oxygen fraction. Their Table 4 has the")
print("    3-min-preoxygenated 18-yr-old at 44.34 kPa absolute when SaO2")
print("    reaches 40% -- about -57 kPa gauge, roughly -580 cmH2O. Ours")
print("    asymptotes near -70 cmH2O, EIGHT TIMES LESS. That number is the")
print("    model's own mechanics now, not a clamp: the recoil floor sits at")
print("    -149.5 and is never reached (see the recoil-floor section above,")
print("    where removing it entirely changes nothing at all). This used to")
print("    read 'ours cannot pass p_collapse = -50', which credited the")
print("    disagreement to a parameter. It was never the parameter.")
print("    MOREAULT 2021 MEASURED -20 (5) and -31 (10) cmH2O IN HUMANS, and")
print("    we give -17.7. So their desaturation is driven by a pressure")
print("    excursion human measurement forbids, and our pressure is the one")
print("    near the measurement while our terminal desaturation is 3x slow.")
print("    Both cannot be right. The well-posed question is what makes a")
print("    sealed lung desaturate fast WITHOUT that pressure excursion.")

# ---------------------------------------------------------------------------
print("\nEvery paper we hold, every channel it records")
print("  All 15 uploaded PDFs screened for SaO2, PaO2, PaCO2, pH, CO, HR, MAP.")
print("  Four record >=2 AND can be configured. Three more record >=2 but")
print("  cannot: Chen & Scharf 1998 (pigs), Condos 1987 and Wright 2023")
print("  (voluntary Mueller, seconds long). The rest record fewer than two.")

# Tokics 1996 Table 2, anaesthetised column: VENTILATED steady state, so this
# is the model's t = 0 and not an apnoea. n=10, 48.7 yr, 175.6 cm, 77.4 kg,
# FiO2 0.40-0.43. Their +- is SE; the bands below are 1 SD = SE*sqrt(10).
_tk = simulate(Patient(weight=77.4, height=1.756, age=49, hb=14.0),
               [AirwayEpoch(60, resistance=2.0, fgo2=0.40)],
               dt=DT, feo2_start=0.40, paco2_start=35.7, stop_sao2=0.0)
check("Tokics ventilated t=0: CO    (meas 5.7)", _tk['co'][0], 4.04, 0.10,
      " L/min")
check("Tokics ventilated t=0: HR    (meas 79)", _tk['hr'][0], 70.0, 1.0, " bpm")
check("Tokics ventilated t=0: MAP   (meas 81)", _tk['map'][0], 72.8, 1.0,
      " mmHg")
check("Tokics ventilated t=0: PaO2  (meas 159)", _tk['pao2'][0], 194.0, 3.0,
      " mmHg")
# NOT a check of anything: the run SETS paco2_start=35.7 from Tokics' own
# table, so reading 35.8 back is an input echoed to an output. Printed so the
# circularity is visible, never tabled as agreement.
print(f"    --   Tokics t=0 PaCO2 is CIRCULAR "
      f"(set 35.7, read {_tk['paco2'][0]:.1f}) -- not evidence")
# And CO/HR/MAP at t=0 come straight from the Patient allometry, not from any
# dynamics. This asserts that, so that if simulate() ever starts moving them
# the assumption behind the bracketed row in HANDOVER is caught.
_tkp = Patient(weight=77.4, height=1.756, age=49, hb=14.0)
check("Tokics t=0 CO is the ALLOMETRY, not the sim",
      _tk['co'][0] - _tkp.co_anaes(), 0.0, 1e-9, " L/min")

# Ebata 1991 Table II. Ten-minute apnoea test, PATENT airway, O2 insufflated
# 6 L/min via a 2.1 mm catheter above the carina. NINE BRAIN-DEAD patients,
# 53.4 yr, mean body temp 36.0 C, ALL on dopamine (two also dobutamine) --
# so their HR of 100 is pharmacologically driven and our shortfall there is
# expected rather than a defect.
_eb = simulate(Patient(weight=70, height=1.75, age=53, hb=14.0, temp=36.0),
               [AirwayEpoch(600, resistance=2.0, fgo2=1.0)],
               dt=DT, feo2_start=0.90, paco2_start=45.0, stop_sao2=0.0)
# The patent configuration is genuinely patent: gas flows in at about VO2 and
# the lung holds its volume. Checked here because the whole Ebata comparison
# is meaningless if resistance=2.0 were behaving like an obstruction.
check("Ebata run is PATENT: O2 drawn in over 600 s",
      float(_eb['cum_o2_in'][-1]), 2098.0, 25.0, " mL")
check("Ebata run is PATENT: alveolar volume held",
      float(_eb['va'][-1] - _eb['va'][0]), 0.0, 5.0, " mL")
check("Ebata 10 min apnoeic ox: PaCO2 (meas 78 +- 3)", at(_eb, 'paco2', 600),
      75.3, 0.5, " mmHg")
check("Ebata 10 min apnoeic ox: pH    (meas 7.17)", at(_eb, 'ph', 600),
      7.20, 0.02, "")
check("Ebata 10 min apnoeic ox: PaO2  (meas 332 +- 38)", at(_eb, 'pao2', 600),
      375.3, 4.0, " mmHg")
check("Ebata 10 min apnoeic ox: CO    (meas 5.7 +- 0.8)", at(_eb, 'co', 600),
      5.03, 0.10, " L/min")
check("Ebata 10 min apnoeic ox: MAP   (meas 81 +- 7)", at(_eb, 'map', 600),
      76.2, 1.0, " mmHg")
check("Ebata 10 min apnoeic ox: HR    (meas 100 +- 7)", at(_eb, 'hr', 600),
      81.1, 1.0, " bpm")
print(f"    Ebata's PaCO2 rate is (78-45)/10 = 3.30 mmHg/min on a PATENT")
print(f"    airway. Ours is {(at(_eb,'paco2',600)-45)/10:.2f}. Stock's")
print("    OBSTRUCTED rate is 3.4, so the two measurements put patent and")
print("    obstructed almost on top of each other, where we separate them.")

# Laviola 2026 Table S5, end of apnoea = the cricothyroidotomy moment, defined
# as SaO2 40% after complete upper airway obstruction. MODEL comparator.
_lv = simulate(Patient(weight=70, height=1.75, age=45, hb=14.0),
               [AirwayEpoch(1400, resistance=OBS, fgo2=0.21)],
               dt=DT, stop_sao2=0.0)
_t40 = time_to(_lv, 'sao2', 40)
_i = int(np.searchsorted(_lv['t'], _t40))
check("Laviola CICO: time to SaO2 40% (theirs ~510)", float(_t40), 504.0, 6.0,
      " s")
check("Laviola CICO: PaO2 (theirs 28.3 +- 0.4)", float(_lv['pao2'][_i]),
      27.65, 0.6, " mmHg")
check("Laviola CICO: PaCO2 (theirs 84.6 +- 4.4)", float(_lv['paco2'][_i]),
      73.35, 1.2, " mmHg")
check("Laviola CICO: CO  (theirs 2.7 +- 0.1)", float(_lv['co'][_i]), 1.79,
      0.08, " L/min")
check("Laviola CICO: MAP (theirs 57.4 +- 2.4)", float(_lv['map'][_i]), 27.4,
      1.0, " mmHg")
print("    These four MOVED on 2026-09-20 when the recoil floor went to minus")
print("    systolic, and one of them BROKE A BENCHMARK. PaCO2 was 77.36 on")
print("    the old -50 floor, inside test_validation's 75.8-93.4 band by 1.6")
print("    mmHg; unclamped it is 73.35 and FAILS by 2.4. The floor sweep, at")
print("    the cricothyroidotomy moment: -50 gives 77.36, -60 gives 75.25,")
print("    -70 gives 73.35, and everything below -70 gives 73.35 because the")
print("    lung never gets there. The mechanism is not subtle -- a deeper")
print("    vacuum is a lower alveolar PCO2 for the same quantity of gas, so")
print("    more CO2 leaves the blood and arterial PCO2 falls.")
print("    RECORDED, NOT COMPENSATED, per CLAUDE.md. The band is not moving")
print("    and no parameter is being reached for. Two things make this an")
print("    acceptable loss: it is a MODEL comparator, not a measurement, and")
print("    HANDOVER already records that ICSM's obstructed numbers are an")
print("    extrapolation from patent-airway validation just as ours are; and")
print("    the correction it came from is one the model's own mechanics")
print("    demanded. A benchmark that only passed because a reported pressure")
print("    contradicted its own recoil function was not passing for a reason.")
print("    THE CO2 LIMB IS THE BEST-AGREEING CHANNEL IN THE WHOLE SET: PaCO2")
print("    within 10% of all four, pH within hundredths. The red check in")
print("    test_validation.py is a SLOPE error, not broken bookkeeping.")
print("    THE OXYGEN ERROR APPEARS ONLY UNDER COMPLETE OBSTRUCTION: PaO2 is")
print("    +22%, +13% and -1% on the other three and -81% on Stock. Laviola's")
print("    -1% is near-automatic -- their endpoint IS SaO2 40%, so we sample")
print("    at matched saturation and the curve forces PaO2 to agree. But the")
print("    TIMING agrees too, 502 s against ~510. So two independently built")
print("    models agree with each other on the desaturation rate under")
print("    obstruction and BOTH disagree with the one human measurement.")
print("    THE HAEMODYNAMICS RUN LOW EVERYWHERE: CO -29/-12/-30%, MAP")
print("    -10/-6/-50%, HR -11/-19%. Never high, at any condition.")

# ---------------------------------------------------------------------------
print("\nStock 1989 measured OXYGEN too -- and the model fails it badly")
print("  Table 1 has a PaO2 column and the Results text says, verbatim:")
print("  'Pulse oximeter and laboratory SaO2 remained above 0.92 at all")
print("  times.' Nothing in test_validation.py has ever tested oxygen under")
print("  OBSTRUCTION -- Toner, Heard, O'Loughlin and ICSM are all patent")
print("  airway or rescue -- and the first time it is tested we are wrong.")
print("  Read from the page 2026-09-18. N falls 14 -> 7 across the table and")
print("  one stopping rule WAS SaO2 0.93, so the late rows are conditioned on")
print("  not having desaturated. That bias flatters Stock and cannot carry it.")
_stock_o2 = simulate(Patient(weight=70, height=1.75, age=45, hb=15.0),
                     [AirwayEpoch(360, resistance=OBS, fgo2=0.21)],
                     dt=DT, feo2_start=0.87, stop_sao2=0.0)
print(f"    {'t':>5}{'model PaO2':>12}{'Stock PaO2':>16}{'model SaO2':>12}")
for t_, po2, sd_ in ((0, 412, 108), (20, 423, 136), (40, 452, 69),
                     (60, 402, 16), (120, 385, 163), (180, 383, 84),
                     (240, 332, 93), (300, 314, 87)):
    print(f"    {t_:5d}{at(_stock_o2,'pao2',t_):12.0f}"
          f"{po2:11d} +-{sd_:<3d}{at(_stock_o2,'sao2',t_):12.1f}")
check("Stock oxygen: model PaO2 at   0 s (Stock 412 +- 108)",
      at(_stock_o2, 'pao2', 0), 512.0, 3.0, " mmHg")
check("Stock oxygen: model PaO2 at 180 s (Stock 383 +-  84)",
      at(_stock_o2, 'pao2', 180), 135.0, 3.0, " mmHg")
check("Stock oxygen: model PaO2 at 300 s (Stock 314 +-  87)",
      at(_stock_o2, 'pao2', 300), 61.0, 3.0, " mmHg")
check("Stock oxygen: model SaO2 at 300 s (Stock: NEVER below 92)",
      at(_stock_o2, 'sao2', 300), 85.3, 0.6, " %")
# The haemodynamic error SCALES WITH SEVERITY, which the by-study tables hide.
# Ebata's patients are mildly stressed and Laviola's are at SaO2 40%.
print("    THE HAEMODYNAMIC ERROR SCALES WITH SEVERITY. Ebata (PaCO2 78,")
print("    PaO2 332, saturation normal): CO -12%, MAP -6%. Laviola (SaO2")
print("    40%): CO -30%, MAP -50%. A gradient, not a constant offset -- the")
print("    sicker the patient, the worse we get. That points at the")
print("    cardiovascular RESPONSE to extreme hypoxia, hypercapnia and")
print("    negative intrathoracic pressure, not at the baseline allometry,")
print("    which the circular Tokics row shows we have never tested.")
# _stock_titr, not _stock_o2: it carries paco2_start=39.0, Stock's own measured
# baseline, where _stock_o2 takes the 40.0 default. The pH differs between
# them, which is exactly what this check caught on first writing.
check("Stock: pH at 300 s (measured 7.26 +- 0.06)",
      at(_stock_titr, 'ph', 300), 7.238, 0.006, "")
print("    The model tracks to 120 s and then COLLAPSES. Not a preoxygenation")
print("    artefact: at feo2_start 0.80 and 0.70, where the baseline matches")
print("    Stock better, SaO2 at 300 s is 82.9 and 77.1 -- the same or worse.")
print("    It loses oxygen too fast under obstruction wherever it starts,")
print("    because the sealed lung is shrinking and the shunt is rising.")
print("    Their fitted CO2 equation, also from the page, for anyone testing")
print("    the SHAPE rather than the slope:")
print("      PaCO2 = (PaCO2)0 + 0.044(t) + 2.72[ln(t)],  t in seconds")
print("    Two unmodelled design differences: their patients had NO")
print("    neuromuscular blockade, and were 36 +- 14 yr where we run 45.")

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
        ("stiff_below_rv 0.05", dict(stiff_below_rv=0.05), 3.94, -27.3),
        ("rv 900", dict(rv=900.0), 5.17, -11.7),
        ("rv 1300", dict(rv=1300.0), 4.27, -32.0)):
    check(f"{lab}: Stock slope", slope(run(**kw)), want_s, 0.15, " mmHg/min")
    check(f"{lab}: Moreault P at 1008 mL", moreault_p(**kw), want_p, 0.5,
          " cmH2O")
print("    Neither CO2 lever moves the pressure at all. The mechanics levers")
print("    move the slope by 4-17%, so the coupling runs ONE WAY and weakly.")
print("    The two red limbs are separable and can be worked apart.")
print("    stiff_below_rv 0.05 moved 4.11 -> 3.94 on 2026-09-20 with the")
print("    recoil floor. It is the ONLY row that moved, and for a reason: it")
print("    was the one setting soft enough to drive the pressure onto the old")
print("    -50 floor, so its lever was being clipped. That was flagged when")
print("    the sweep was first run -- it was comparing two mechanical regimes")
print("    -- and is now gone. The conclusion is unchanged and slightly")
print("    stronger: the strongest mechanics lever moves the slope 17% where")
print("    the WEAKEST CO2 lever moves it 32%.")
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
print("\nTHE OXYGEN DEFECT AND THE CO2 DEFECT ARE ONE DEFECT -- 2026-09-21")
print("  HANDOVER once recorded this hypothesis as REFUTED. That test left the")
print("  SHUNT ON, so what it called a dispersion-independent floor was the")
print("  shunt. These rows are the re-test with no blood allowed to bypass gas")
print("  exchange by any route.")
_NS = dict(inflow_mech_frac=0.0, perfusion_gain=0.0, shunt_base=0.0,
           max_closed=0.0)


def _obs(**kw):
    """Stock's reference patient, sealed airway, preoxygenated."""
    _p = Patient(weight=70, height=1.75, age=45, hb=15.0, **kw)
    return simulate(_p, [AirwayEpoch(360, resistance=OBS, fgo2=0.21)],
                    dt=DT, feo2_start=0.87, paco2_start=39.0, stop_sao2=0.0)


print("    First: the long-promised shunt_base sweep. It is NOT the actor.")
for _sb, _w in ((0.00, 64.1), (0.05, 60.5), (0.20, 50.6)):
    check(f"shunt_base {_sb:.2f}: PaO2 at 300 s", at(_obs(shunt_base=_sb),
          'pao2', 300), _w, 1.0, " mmHg")
check("shunt_base 0.00 still leaves total shunt at",
      at(_obs(shunt_base=0.0), 'shunt', 300), 0.132, 0.01, "")
print("    Zeroing it moves PaO2 3.6 mmHg against a 254 mmHg gap, and the")
print("    shunt is still 0.13 because the per-unit absorption collapse")
print("    supplies it. max_closed was already shown inert. So neither named")
print("    suspect is the actor.")
_allof = _obs(**_NS)
check("every collapse lever off: total shunt", at(_allof, 'shunt', 300), 0.0,
      1e-9, "")
check("every collapse lever off: alveolar PO2", at(_allof, 'pao2_alv', 300),
      365.5, 3.0, " mmHg")
check("every collapse lever off: arterial PaO2", at(_allof, 'pao2', 300),
      70.1, 2.0, " mmHg")
print("    A 295 mmHg gap with the shunt at EXACTLY zero. Now sweep the V/Q")
print("    spread with the shunt still off -- the gap tracks it, and goes")
print("    slightly NEGATIVE at a near-uniform lung:")
for _sd, _wg, _wp in ((0.01, -38.7, 327.5), (0.20, 42.4, 252.9),
                      (0.50, 253.6, 86.1), (0.70, 295.4, 70.1)):
    _r = _obs(vq_log_sd=_sd, **_NS)
    check(f"vq_log_sd {_sd:.2f}, no shunt: a-A O2 gap",
          at(_r, 'pao2_alv', 300) - at(_r, 'pao2', 300), _wg, 3.0, " mmHg")
    check(f"vq_log_sd {_sd:.2f}, no shunt: PaO2 (Stock measured 314 +- 87)",
          at(_r, 'pao2', 300), _wp, 3.0, " mmHg")
print("    At a near-uniform lung PaO2 is 327.5 against Stock's measured 314,")
print("    INSIDE the measurement. So both defects are one mechanism: blood")
print("    mixes by CONTENT, which is linear, and is reported as PARTIAL")
print("    PRESSURE, which is curved, so a perfusion-weighted content average")
print("    lands low on the curve.")
print("    THIS DOES NOT LICENSE SETTING vq_log_sd LOW. Tokics measures the")
print("    spread WIDER than we use. The question is no longer 'what is the")
print("    extra oxygen defect' but 'is the shared mechanism implemented")
print("    correctly'. Against it: V/Q inequality is classically CORRECTABLE")
print("    by high inspired oxygen where true shunt is not, yet a zero-shunt")
print("    lung with alveolar PO2 above 360 still shows a 295 mmHg gap.")

# ---------------------------------------------------------------------------
print("\nTHE MECHANISM TRACED, AND WHY 'PaO2 81% LOW' OVERSTATES IT")
print("  Faster cardiogenic stirring between lung units does NOT close the gap.")
print("  tau_mix is that stirring's time constant; HANDOVER has always called")
print("  it 'not well characterised'. Swept 180x with the shunt at zero:")
for _tm, _wa, _wp in ((1.0, 282.8, 99.6), (45.0, 365.5, 70.1),
                      (180.0, 390.6, 60.9)):
    _r = _obs(tau_mix=_tm, **_NS)
    check(f"tau_mix {_tm:5.1f} s: alveolar PO2", at(_r, 'pao2_alv', 300), _wa,
          3.0, " mmHg")
    check(f"tau_mix {_tm:5.1f} s: arterial PaO2", at(_r, 'pao2', 300), _wp,
          2.0, " mmHg")
print("    A 183 mmHg gap survives NEAR-INSTANT stirring, so the gap is not")
print("    just units that have not had time to equilibrate with each other.")
print("    Looking inside the 80 units at 300 s (instrumented copy, shunt 0)")
print("    they are BIMODAL: 41% of the BLOOD FLOW goes to units sitting at")
print("    mixed-venous PO2 (38-44 mmHg, 38% saturated) which have had their")
print("    oxygen taken and can give none back -- a shunt in all but name,")
print("    which is why turning the named shunt off changed nothing.")
print("    NOW THE PART THAT MATTERS. PaO2 is a hypersensitive readout above")
print("    ~150 mmHg because the dissociation curve is FLAT there. The same")
print("    disagreement with Stock, stated three ways:")
_S_PO2, _O_PO2, _PH, _PC = 314.0, 60.5, 7.24, 70.0
_s_st = bg.so2_from_po2(_S_PO2, _PH, _PC, 37.0)
_s_us = bg.so2_from_po2(_O_PO2, _PH, _PC, 37.0)
_c_st = bg.HUFNER * 15.0 * _s_st + bg.O2_SOL * _S_PO2
_c_us = bg.HUFNER * 15.0 * _s_us + bg.O2_SOL * _O_PO2
check("Stock PaO2 314 implies arterial O2 content", _c_st, 21.02, 0.05,
      " mL/dL")
check("our PaO2 60.5 implies arterial O2 content", _c_us, 17.34, 0.05,
      " mL/dL")
check("disagreement stated as PaO2", 100 * (_O_PO2 - _S_PO2) / _S_PO2, -80.7,
      0.3, " %")
check("disagreement stated as SATURATION", 100 * (_s_us - _s_st) / _s_st,
      -14.5, 0.3, " %")
check("disagreement stated as OXYGEN CONTENT", 100 * (_c_us - _c_st) / _c_st,
      -17.5, 0.3, " %")
check("PaO2 needed for SaO2 99% -- the flatness, quantified",
      brentq(lambda x: bg.so2_from_po2(x, _PH, _PC, 37.0) - 0.99, 10, 700),
      158.1, 1.0, " mmHg")
print("    Going 99% -> 100% saturation costs 0.20 mL/dL of content and takes")
print("    PaO2 from 158 mmHg to unbounded. So the model is 17.5% LOW ON")
print("    ARTERIAL OXYGEN CONTENT -- serious, still the largest disagreement")
print("    in the project, but an ORDINARY one, not the 81% catastrophe the")
print("    PaO2 framing implies. Three consequences: judge this limb on")
print("    CONTENT or SATURATION, never PaO2 above 150; it puts oxygen (17.5%)")
print("    and CO2 (~10%) on the same scale, one mechanism; and the '81%'")
print("    entries elsewhere in HANDOVER are the wrong denominator and should")
print("    not be quoted alone again.")

# ---------------------------------------------------------------------------
print("\nTHE STOP-ABSORBING RULE IS ALREADY IN THE MODEL -- verified 2026-09-21")
print("  On 2026-09-20 this file's author proposed 'giving closed units a")
print("  stop-absorbing rule' as the proper fix for the recoil floor. That was")
print("  wrong: it is already there. apnoea_core.py weights each unit's")
print("  perfusion by (1 - coll_c), so a fully collapsed unit gets ZERO share")
print("  of blood flow and takes up no gas at all.")
_sa = simulate(Patient(weight=70, height=1.75, age=45, hb=14.0,
                       hr_term_sao2=0.0),
               [AirwayEpoch(1800, resistance=OBS, fgo2=0.21)],
               dt=0.1, stop_sao2=0.0)
check("sealed lung volume at 1390 s", at(_sa, 'va', 1390), 425.2, 3.0, " mL")
check("sealed lung volume at 1790 s", at(_sa, 'va', 1790), 425.0, 3.0, " mL")
check("volume LOST over those 400 s", at(_sa, 'va', 1390) - at(_sa, 'va', 1790),
      0.21, 0.3, " mL")
check("alveolar PO2 at 1790 s", at(_sa, 'pao2_alv', 1790), 0.0, 0.5, " mmHg")
check("mixed venous PO2 at 1790 s", at(_sa, 'pvo2', 1790), 0.0, 0.5, " mmHg")
print("    0.2 mL lost in the last 400 s, with the heart forced to keep")
print("    beating. A lung that kept absorbing would go to zero volume. The")
print("    terminator is real and already modelled.")

# ---------------------------------------------------------------------------
print("\nEBATA TABLE II, re-read off the page 2026-09-21")
print("  protocol/evidence.md proposed PVR +63% as one of 'two candidate")
print("  benchmarks that ARE clean'. Ebata's own Results say otherwise: 'The")
print("  SVR was slightly decreased and PVR increased, but the changes were")
print("  not statistically significant.' Only MPAP and CO reach significance.")
print("      pH    7.37 (0.01) -> 7.17 (0.02)   P<0.001")
print("      PaCO2 45 (1)      -> 78 (3)        P<0.001")
print("      MPAP  11 (1)      -> 17 (2)        P<0.01    <- usable")
print("      CO    4.8 (0.7)   -> 5.7 (0.8)     P<0.05    <- usable")
print("      PaO2, MAP, HR, PCWP, RAP, SVR, PVR           all NS")
_eb = simulate(Patient(weight=70, height=1.75, age=45, hb=14.0),
               [AirwayEpoch(600, resistance=2, fgo2=1.0)],
               dt=DT, feo2_start=1.0, stop_sao2=0.0)
check("ours: mean PAP at 600 s (Ebata 17 +- 2, P<0.01)", at(_eb, 'pap', 600),
      19.3, 1.5, " mmHg")
check("ours: cardiac output at 600 s (Ebata 5.7 +- 0.8, P<0.05)",
      at(_eb, 'co', 600), 5.03, 0.3, " L/min")
print("    NOT ADDED TO test_validation.py AS A BAND. The pulmonary limb is")
print("    wholly set by Marshall 1994, which nobody here has read, and PAP")
print("    swings 54% across that paper's plausible range. Banding a limb")
print("    whose only parameter is unsourced would be grading noise. Read")
print("    Marshall first -- see SOURCES.md.")

# ---------------------------------------------------------------------------
print("\nTHE FRC REGRESSION -- the largest UNCITED lever in the model")
print("  Flagged 2026-09-21 by the pre-release source audit (SOURCES.md). The")
print("  regression apnoea_core.py anchors FRC to --")
print("      FRC(L) = 2.34*height(m) + 0.009*age - 1.09")
print("  -- has NO author, NO journal and NO year anywhere in this repository,")
print("  and it appears in none of HANDOVER's three provenance tiers, so it was")
print("  never triaged. These rows exist so the sensitivity cannot rot, and are")
print("  run at the EXACT test_validation.py configurations.")


def _t95(**kw):
    """time to SpO2 < 95% on a patent airway, room air."""
    _p = Patient(**kw)
    _r = simulate(_p, [AirwayEpoch(900, resistance=2, fgo2=0.21)],
                  dt=DT, stop_sao2=0.0)
    return time_to(_r, 'spo2', 95)


def _heard(**kw):      # test_validation.py test_heard_2017
    return _t95(weight=107, height=1.75, age=45, hb=14, tilt_deg=25, **kw)


def _toner(**kw):      # test_validation.py test_toner_2018
    return _t95(weight=70, height=1.75, age=45, hb=15, tilt_deg=0, **kw)


for _v, _wh, _wt in ((2200.0, 249.5, 346.9), (2500.0, 289.2, 403.4),
                     (2800.0, 329.8, 460.5)):
    check(f"frc_ref {_v:.0f}: Heard control [band 244-314]",
          _heard(frc_ref=_v), _wh, 3.0, " s")
    check(f"frc_ref {_v:.0f}: Toner sham   [band 380-525]",
          _toner(frc_ref=_v), _wt, 3.0, " s")
for _v, _wh in ((0.0300, 344.6), (0.0417, 289.2), (0.0550, 237.1)):
    check(f"k_frc_bmi {_v:.4f}: Heard control [band 244-314]",
          _heard(k_frc_bmi=_v), _wh, 3.0, " s")
check("the quoted age term is NOT implemented: height_factor at age 45",
      Patient(weight=70, height=1.75, age=45, hb=14).height_factor(), 1.0,
      1e-9, "")
check("  ... and identically at age 80",
      Patient(weight=70, height=1.75, age=80, hb=14).height_factor(), 1.0,
      1e-9, "")
print("    A +-12% error in frc_ref (2200 / 2800) takes one or other HEADLINE")
print("    CLINICAL benchmark out of band, and +-30% in k_frc_bmi walks the")
print("    obese one out in BOTH directions. For scale, the same audit measured")
print("    Hufner 1.34->1.39 at under 1% on desaturation. The largest lever in")
print("    the model is the one with no source. See SOURCES.md section 3.")

# ---------------------------------------------------------------------------
print("\nMOREAULT'S SPREAD IS SEM, NOT SD -- the sample size was wrong by 10x")
print("  Read off the paper 2026-09-21: 'The mean (SEM) Pairway became")
print("  progressively negative ... reaching [-20 (5) and -31 (10) cmH2O]'.")
print("  39 patients across FOUR groups (two devices x two measurements), so")
print("  the pressure groups are n ~ 10. protocol/study.html read the 5 as a")
print("  STANDARD DEVIATION. This block is pure arithmetic and is here so the")
print("  correction cannot rot back.")
_SD = 5.0 * np.sqrt(10.0)
check("implied SD from SEM 5 at n=10", _SD, 15.81, 0.01, " cmH2O")
check("the giveaway: 5/sqrt(20), quoted as 'standard error of 1.12'",
      5.0 / np.sqrt(20.0), 1.118, 0.001, "")
_se20 = _SD / np.sqrt(20.0)
check("true SE at n=20", _se20, 3.536, 0.005, " cmH2O")
check("true 95% CI at n=20 (t19 = 2.093)", 2.093 * _se20, 7.40, 0.02,
      " cmH2O")
print("    +-7.40 does NOT separate two predictions 5 cmH2O apart. n for 90%")
print("    power at alpha 0.05 by one-sample t test is 108, not the 11 the")
print("    protocol claimed. Whether Moreault's between-subject spread even")
print("    transfers to a clamped tube in BMI<30 patients is a separate")
print("    judgement and is NOT settled -- see protocol/study.html 3.3.")

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
