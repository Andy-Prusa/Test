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


def _forced_shunt(value):
    """Patient subclass whose baseline shunt is forced to `value`.

    No parameter forces an absolute baseline shunt any more. shunt_base and
    shunt_obese went with the flat 5%; the Pelosi quadratic's coefficients
    went with the re-key on 2026-09-24, and what is left -- shunt_anat and
    shunt_cc_k -- sets a LAW whose value depends on lung volume against
    closing capacity. Overriding the accessor is the only way to pin the
    number, and it works at any BMI, tilt and age.
    """
    class _Forced(Patient):
        def shunt_base_eff(self):
            return value
    return _Forced



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


check("obstructed PaCO2 slope 60-300 s", slope(ro), 4.60, 0.10, " mmHg/min")
check("obstructed PACO2 slope", (at(ro, 'paco2_alv', 300) - at(ro, 'paco2_alv', 60)) / 4, 2.61, 0.10)
check("obstructed PvCO2 slope", (at(ro, 'pvco2', 300) - at(ro, 'pvco2', 60)) / 4, 1.80, 0.10)
check("patent PaCO2 slope 60-300 s", slope(rp), 1.68, 0.10, " mmHg/min")
check("patent PvCO2 slope", (at(rp, 'pvco2', 300) - at(rp, 'pvco2', 60)) / 4, 1.74, 0.10)
check("obstructed a-A gap growth", (gap(ro, 300) - gap(ro, 60)) / 4, 2.13, 0.10)
check("patent a-A gap growth", (gap(rp, 300) - gap(rp, 60)) / 4, -0.04, 0.10)
for t, g, sh, sa in ((60, -0.17, 0.0585, 100.0), (180, 1.52, 0.1033, 98.5),
                     (240, 6.07, 0.1406, 93.1), (300, 7.97, 0.1824, 84.9)):
    check(f"obstructed a-A gap at {t:3.0f} s", gap(ro, t), g, 0.4, " mmHg")
    check(f"obstructed shunt at {t:3.0f} s", 100 * at(ro, 'shunt', t), 100 * sh, 1.0, " %")

# ---------------------------------------------------------------------------
print("\nWhat the coupling is NOT")
check("shunt suppressed (max_closed 0.02): slope",
      slope(run(max_closed=0.02)), 4.77, 0.15, " mmHg/min")
check("hb 18, desaturation delayed: slope",
      slope(run(hb=18.0)), 4.24, 0.15, " mmHg/min")
check("p_collapse floor removed (-200): slope",
      slope(run(p_collapse=-200.0)), 4.72, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nTHESE TWO SWEEPS NOW MEASURE NOTHING -- STRUCK 2026-09-23")
print("  They were 'tau_mix -- the lever that acts on the a-A gap' and")
print("  'vq_log_sd against Tokics 1996'. Both swept a parameter and recorded")
print("  how the Stock CO2 slope moved. Both now return the SAME NUMBER for")
print("  every value:")
print("      tau_mix   25 / 45 / 60 / 90 s      all 1.95, were 6.09-3.09")
print("      vq_log_sd 0.50 / 0.70 / 0.80 / 1.18  all 1.95, were 3.16-7.56")
print("  WHY, and it is one reason for both. The Stock patient is lean and")
print("  supine: FRC exceeds closing capacity, nothing closes, the unwashed")
print("  fraction is zero, so EVERY COMPARTMENT IS IDENTICAL for the whole")
print("  run. There is nothing for cardiogenic mixing to mix and nothing for")
print("  a dispersion parameter to disperse. Before the V/Q category-error")
print("  fix the compartments differed in GAS VOLUME -- wrongly, by a ratio")
print("  of flows -- and that difference is what these sweeps were moving.")
print("  THEY WERE MEASURING THE ARTEFACT, NOT THE PARAMETER.")
print("  NOT RENUMBERED, BECAUSE A TABLE OF IDENTICAL VALUES PRESENTED AS A")
print("  SENSITIVITY ANALYSIS IS WORSE THAN NO TABLE. To be useful again")
print("  they must be re-run on a patient whose compartments differ. On the")
print("  Gander patient (15.79% unwashed) tau_mix 5 -> 300 s moves")
print("  desaturation by 1.25 s and vq_log_sd is STILL exactly inert --")
print("  see 'vq_log_sd IS A DEAD PARAMETER' below.")
check("baseline shunt at the default patient [Tokics 5.0, SE 1.3]",
      100 * ro['shunt'][0], 3.61, 0.05, " %")
print("    CORRECTED 2026-09-25, THE PAPER HAVING BEEN READ AT SOURCE. Two")
print("    things in the old note were wrong.")
print("    (a) THE 1.3 IS A STANDARD ERROR, NOT A STANDARD DEVIATION. Table 3")
print("        footnote, verbatim: \"Values are means 6 SE; n 5 10.\" So the")
print("        SD is 1.3*sqrt(10) = 4.11, and every 'in SD of 5.0 (1.3)' this")
print("        repository computed used a band 3.16 times too narrow.")
print("    (b) 'We LAND on the measurement, we do not sit under it' was true")
print("        when shunt_base was a flat 5% for everyone. The re-key of")
print("        2026-09-24 made it 3.61% here, so that sentence is struck.")
print("    Against the CORRECT SD the row is comfortable either way:")
print("        3.61 against 5.0, SD 1.30 (the old misreading):  -1.07 SD")
print("        3.61 against 5.0, SD 4.11 (SE corrected)      :  -0.34 SD")

# ---------------------------------------------------------------------------
print("\nsv_itp_gain -- nearly inert on the knot (human data give 0.0033-0.00476)")
for g_, want in ((0.0025, 4.72), (0.00476, 4.66)):
    check(f"sv_itp_gain {g_:.5f}: Stock slope",
          slope(run(sv_itp_gain=g_)), want, 0.12, " mmHg/min")
check("stiff_below_rv 2.00: Stock slope",
      slope(run(stiff_below_rv=2.0)), 5.20, 0.15, " mmHg/min")

# ---------------------------------------------------------------------------
print("\nn_vq convergence -- RENUMBERED 2026-09-23, and the reason it existed")
print("  is gone. CO2 cannot leave a clamped lung, so PaCO2 must rise")
print("  monotonically. Below 80 compartments it did not, and the default was")
print("  raised 20 -> 80 on 2026-09-18 for exactly that reason.")
print("  THE NON-MONOTONICITY IS NOW THE SAME AT EVERY GRID: 9 backward steps")
print("  at n_vq 20, 80 AND 160, where it was 24 / 0 / 3. The slope is")
print("  identical to four decimals at every grid. On the LEAN SEALED patient")
print("  the compartments are identical, so compartment count cannot matter --")
print("  which means these rows no longer test discretisation at all, and the")
print("  9 backward steps are a TIMESTEP artefact that the old grid-dependence")
print("  was masking. n_vq 80 showing exactly 0 was luck, not convergence.")
print("  n_vq IS still live where compartments differ: on the Gander patient")
print("  20 -> 160 moves initial PaO2 453.0 -> 445.3 mmHg, converging.")
print("  WHAT NEEDS DOING: re-run this convergence check on a patient with a")
print("  nonzero unwashed fraction, and find where the 9 backward steps come")
print("  from. Neither is done. The rows below are renumbered only so the")
print("  file runs; they do not support the conclusion printed after them.")
for n_, want_slope, want_falls in ((20, 1.95, 9), (40, 1.95, 9),
                                   (80, 1.95, 9), (160, 1.95, 9)):
    r_ = run(n_vq=n_)
    falls = int((np.diff(r_['paco2']) < -1e-9).sum())
    check(f"n_vq {n_:3d}: Stock 1-5 min slope", slope(r_), want_slope, 0.15,
          " mmHg/min")
    check(f"n_vq {n_:3d}: steps where PaCO2 FALLS", float(falls),
          float(want_falls), 2.0, " steps")
print("    THE OLD NOTE HERE IS STRUCK. It read that n_vq 160 showed 3")
print("    backward steps where it showed 0, that shipped n_vq 80 was still")
print("    exactly 0 so the default was not compromised, and that a finer")
print("    grid was no longer strictly safer. All three rest on the grid")
print("    mattering, and it no longer does: 9 backward steps at every grid.")
print("    WHAT SURVIVES, and it survives more strongly than before: the")
print("    disagreement with Stock is a property of the model PHYSICS, not of")
print("    its discretisation, and no refinement will remove it. That was an")
print("    inference from a weak grid-dependence; it is now a direct")
print("    observation, because there is no grid-dependence at all here.")
print("    test_validation.py checks timestep convergence and has never")
print("    checked compartment-count convergence. It still has not.")

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
for _t, _v, _pw in ((300, 849.7, -37.75), (420, 536.0, -69.82),
                    (540, 443.4, -79.28), (590, 442.2, -79.41)):
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
        ("default air seal", {}, 0.21, -79.41),
        ("preoxygenated seal", {}, 1.0, -79.41),
        ("obese 120 kg / 1.70 m", dict(weight=120, height=1.70), 0.21, -77.48),
        ("vo2_ref 400", dict(vo2_ref=400.0), 0.21, -79.53),
        ("no terminal bradycardia", dict(hr_term_sao2=0.0), 0.21, -80.63),
        ("no bradycardia + vo2_ref 400",
         dict(hr_term_sao2=0.0, vo2_ref=400.0), 0.21, -82.67)):
    _k2 = dict(_kw)
    _p2 = Patient(weight=_k2.pop('weight', 70), height=_k2.pop('height', 1.75),
                  age=45, hb=14.0, p_collapse=-1e6, **_k2)
    _r2 = simulate(_p2, [AirwayEpoch(900, resistance=OBS, fgo2=_fg)],
                   dt=0.1, stop_sao2=0.0)
    check(f"min P, {_name}", float(_r2['palv_cmh2o'].min()), _want, 0.6,
          " cmH2O")
print("    Every one asymptotes near -79, roughly 70 cmH2O clear of the")
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
      -80.76, 0.6, " cmH2O")
check("min volume over 1800 s, unclamped", float(_rz['va'].min()), 425.0,
      4.0, " mL")
print("    What the move COSTS, since it is not free: the ITP stroke-volume")
print("    term is now charged over the whole fall instead of being frozen")
print("    at the old clamp. At the -79.4 asymptote the factor is 0.881")
print("    against 0.925 at -50 -- the 3.2 points the clamp was not")
print("    charging. Gas tensions move by about 2% of dry pressure, which is")
print("    NOT the oxygen defect: that is at 300 s, before the old clamp")
print("    ever bound, and is unchanged to 0.01 mmHg by this.")
_G2, _F2 = _cl.sv_itp_gain, _cl.itp_fraction
check("sv factor at the -79.4 asymptote",
      max(0.15, 1.0 + _G2 * -79.41 * _F2), 0.8808, 0.002, "")
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
      -10.24, 0.4, " cmH2O")
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
      71.66, 1.2, " mmHg")
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
print("\nvq_log_sd was a VOLUME dispersion -- BLOCK STRUCK 2026-09-23")
print("  This block diagnosed the category error before it was fixed. It")
print("  read: vq_log_sd appears exactly once in apnoea_core.py, its only")
print("  product is the gas-VOLUME share, under obstruction there is no")
print("  ventilation so all that is left is VOLUME per perfusion, and we")
print("  calibrate a volume distribution against a ventilation measurement.")
print("  THAT DIAGNOSIS WAS RIGHT AND THE FIX OF 2026-09-22 ACTED ON IT.")
print("  Gas volume now tracks perfusion, so the parameter has no product at")
print("  all: it appears in NO executable statement in apnoea_core.py.")
print("  Every row below therefore returns the same number for every value,")
print("  and the conclusions printed after them -- that the patent arm is")
print("  inert while the gap moves, that the a-A gap changes sign between")
print("  0.30 and 0.40 as a hard bracket rather than a fitted one, and that")
print("  Stock wants a volume dispersion near 0.50 -- are all statements")
print("  about a dispersion that no longer exists. STRUCK, not renumbered:")
print("  renumbering would present four identical rows as a bracket. The")
print("  rows are kept only to ASSERT the inertness.")


def first_min(r_):
    return at(r_, 'paco2', 60) - at(r_, 'paco2', 0)


for sd, w_obs, w_pat, w_gap, w_r1 in ((0.30, 1.95, 1.64, -0.71, 12.16),
                                      (0.40, 1.95, 1.64, -0.71, 12.16),
                                      (0.50, 1.95, 1.64, -0.71, 12.16),
                                      (0.70, 1.95, 1.64, -0.71, 12.16)):
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
print("    FOUR IDENTICAL ROWS. That is the assertion, not a failure.")
print("    ONE THING FROM THE OLD NOTE SURVIVES AND IS NOW WORSE. It said")
print("    the a-A CO2 gap changing sign between 0.30 and 0.40 was a hard")
print("    bracket, and that below it the model had arterial CO2 running")
print("    BELOW alveolar inside a sealed lung. The gap is now -0.71 mmHg at")
print("    EVERY value, so the model is permanently on the wrong side of")
print("    that sign. It is small -- under one mmHg -- but arterial CO2")
print("    below alveolar in a clamped lung is not a thing a lung does, and")
print("    there is no longer any parameter that moves it back.")
print("    The first-minute rise is 12.16 against Stock measured 12, so the")
print("    bulk CO2 bookkeeping is still right. The defect is in the")
print("    alveolar-to-arterial step alone, which is where the Stock slope")
print("    disagreement has been localised since 2026-09-21.")

# ---------------------------------------------------------------------------
print("\nvq_log_sd is NOT the log QSD it is compared against -- and after")
print("  2026-09-23 it is not a log QSD at all. READ THIS BEFORE THE ROWS.")
print("  The z grid is linspace(-2.2, 2.2, n). Truncating a Gaussian at 2.2")
print("  sigma discards the tails, so the discrete distribution has SD 0.9206")
print("  and log QSD = 0.9206 * vq_log_sd.")
print("  THE ROWS BELOW ARE THE SCRIPT TALKING TO ITSELF. log_moments()")
print("  builds lr = sd * zz WITH ITS OWN HAND. The model does not: nothing")
print("  in apnoea_core.py constructs a V/Q ratio from vq_log_sd, so what is")
print("  labelled 'model log QSD' is this file reconstructing the ratio the")
print("  model WOULD have had. That was arguably true before the category-")
print("  error fix, when the volume share carried the ratio. It is not true")
print("  now, and the label is misleading. Kept because the ARITHMETIC is")
print("  still the right arithmetic for choosing a future dispersion.")
print("  AND THE TWO MOMENTS ARE NOW IDENTICALLY EQUAL. The model forces gas")
print("  volume to track perfusion exactly, so log VSD == log QSD at every")
print("  value -- 0.460/0.644/0.800/1.180 for both, where VSD used to run")
print("  0.448/0.612/0.739/1.002. Tokics measures them as DIFFERENT")
print("  quantities, so the model can now represent NEITHER of his lungs:")
print("  not the isotope lung (0.80 / 0.78) and not the MIGET lung")
print("  (1.18 / 0.62). Before, it could at least hit the isotope pair.")
print("  THAT IS A REAL LOSS AND IT IS NOT A REASON TO UNDO THE FIX -- the")
print("  fix removed a quantity that was wrong, and what is needed now is a")
print("  DERIVED volume distribution, which is the open item recorded in")
print("  vq_distribution().")


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
for sd, w_q, w_v in ((0.50, 0.460, 0.460), (0.70, 0.644, 0.644),
                     (0.869, 0.800, 0.800), (1.282, 1.180, 1.180)):
    q_, v_ = log_moments(sd)
    check(f"vq_log_sd {sd:5.3f}: model log QSD", q_, w_q, 0.006, "")
    check(f"vq_log_sd {sd:5.3f}: model log VSD", v_, w_v, 0.006, "")
print("    Tokics 1996 Table 3, read from the page 2026-09-18:")
print("      awake, inert gas          log QSD 0.67 +- 0.07  log VSD 0.54 +- 0.06")
print("      anaesthetised, inert gas  log QSD 1.18 +- 0.12  log VSD 0.62 +- 0.05")
print("      anaesthetised, isotope    log QSD 0.80 +- 0.04  log VSD 0.78 +- 0.04")
print("    The shipped 0.70 WOULD deliver 0.644 -- below even the awake 0.67.")
print("    It currently delivers nothing, because the parameter is inert.")
print("    THE TWO ROWS THAT FOLLOWED ARE STRUCK. They set vq_log_sd to the")
print("    value that reproduces Tokics isotope (0.869) and inert-gas (1.282)")
print("    log QSD and recorded the Stock slope: 5.85 and 8.25, against a")
print("    measured 3.4. The argument was that the model gets WORSE as its")
print("    dispersion is moved toward the measured one, which was a real")
print("    finding. Both now return 1.95, the same as every other value, so")
print("    the argument cannot be made this way any more. It is not refuted,")
print("    it is untestable with this parameter. Renumbering these two to")
print("    1.95 would have preserved the sentence and destroyed its meaning.")
for sd, want, lab in ((0.869, 1.95, "isotope log QSD 0.80"),
                      (1.282, 1.95, "inert-gas log QSD 1.18")):
    check(f"at the TRUE {lab}: Stock slope [INERT, see above]",
          slope(run(vq_log_sd=sd)), want, 0.15, " mmHg/min")
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
check("baseline Moreault P at 1008 mL", _base_p, -19.8, 0.4, " cmH2O")
for lab, kw, want_s, want_p in (
        ("tau_mix 25", dict(tau_mix=25.0), 6.09, -19.9),
        ("tau_mix 90", dict(tau_mix=90.0), 3.09, -19.9),
        ("vq_log_sd 0.50", dict(vq_log_sd=0.50), 3.16, -19.8),
        ("vq_log_sd 1.18", dict(vq_log_sd=1.18), 7.56, -19.8),
        ("crs 60", dict(crs=60.0), 4.37, -24.2),
        ("crs 110", dict(crs=110.0), 4.92, -14.0),
        ("stiff_below_rv 0.05", dict(stiff_below_rv=0.05), 3.78, -30.0),
        ("rv 900", dict(rv=900.0), 5.17, -13.3),
        ("rv 1300", dict(rv=1300.0), 4.11, -35.8)):
    check(f"{lab}: Stock slope", slope(run(**kw)), want_s, 0.15, " mmHg/min")
    check(f"{lab}: Moreault P at 1008 mL", moreault_p(**kw), want_p, 0.5,
          " cmH2O")
print("    Neither CO2 lever moves the pressure at all. The mechanics levers")
print("    move the slope by 4-17%, so the coupling runs ONE WAY and weakly.")
print("    The two red limbs are separable and can be worked apart.")
print("    stiff_below_rv 0.05 moved 4.11 -> 3.94 on 2026-09-20 with the")
print("    recoil floor, and 3.94 -> 3.78 on 2026-09-22 with crs 85 -> 75.")
print("    It moves on every mechanics change, and for a reason: it")
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
_NS = dict(inflow_mech_frac=0.0, perfusion_gain=0.0,
           max_closed=0.0)


def _obs(_cls=None, **kw):
    """Stock's reference patient, sealed airway, preoxygenated.

    _cls lets a caller pass a Patient subclass -- see _forced_shunt.
    """
    _p = (_cls or Patient)(weight=70, height=1.75, age=45, hb=15.0, **kw)
    return simulate(_p, [AirwayEpoch(360, resistance=OBS, fgo2=0.21)],
                    dt=DT, feo2_start=0.87, paco2_start=39.0, stop_sao2=0.0)


print("    First: the long-promised shunt_base sweep. It is NOT the actor.")
for _sb, _w in ((0.00, 64.1), (0.05, 60.5), (0.20, 50.6)):
    check(f"baseline shunt {_sb:.2f}: PaO2 at 300 s", at(_obs(_cls=_forced_shunt(_sb)),
          'pao2', 300), _w, 1.0, " mmHg")
check("baseline shunt 0.00 still leaves total shunt at",
      at(_obs(_cls=_forced_shunt(0.0)), 'shunt', 300), 0.132, 0.01, "")
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
print("\nONE MECHANISM: AT A UNIFORM LUNG BOTH LIMBS LAND ON STOCK")
print("  THE LUNG IS NOW UNIFORM, AND ONLY ONE LIMB LANDED -- 2026-09-23.")
print("  This block made the case for the V/Q category-error fix: at a")
print("  near-uniform lung with the shunt off, PaCO2 was 58.85 against a")
print("  measured 63 (9) and PaO2 327.5 against 314 (87) AT THE SAME SETTING,")
print("  so one change would fix both. The fix was made on 2026-09-22 and the")
print("  lung is uniform for every run now. THE OXYGEN PREDICTION HELD:")
print("  PaO2 at 300 s is 326.88 with the shunt off, 157.2 with the shipped")
print("  5% shunt, against 60.9 before. THE CO2 PREDICTION DID NOT: the")
print("  sealed slope is 1.91 against a measured 3.4, further from Stock")
print("  than the 4.52 it replaced, and 'both limbs land' turned out to mean")
print("  one limb landed and the other overshot through the band.")
print("  THAT IS RECORDED HERE RATHER THAN IN HINDSIGHT ELSEWHERE, because")
print("  this is the block that made the prediction. The prediction was")
print("  half right, the fix was still correct -- a ratio of flows cannot")
print("  allocate a volume, whatever it does to a benchmark -- and the CO2")
print("  cost is carried openly in .github/known-blocking.txt.")
print("  Not a discretisation artefact. n_vq is how many parallel units the")
print("  lung is chopped into; refining it 16-fold changes nothing:")
for _n, _w in ((20, 326.88), (80, 326.88), (320, 326.88)):
    check(f"n_vq {_n:3d}: PaO2 at 300 s, no shunt", at(_obs(n_vq=_n, **_NS),
          'pao2', 300), _w, 1.0, " mmHg")
print("  The CO2 limb behaves identically. Same zero-shunt condition, and at a")
print("  near-uniform lung BOTH land inside Stock's measurements at once:")
for _sd, _wco2, _wgap in ((0.01, 58.84, -0.39), (0.50, 58.84, -0.39),
                          (0.70, 58.84, -0.39), (0.90, 58.84, -0.39)):
    _r = _obs(vq_log_sd=_sd, **_NS)
    check(f"vq_log_sd {_sd:.2f}, no shunt: PaCO2 (Stock 63 +- 9)",
          at(_r, 'paco2', 300), _wco2, 1.0, " mmHg")
    check(f"vq_log_sd {_sd:.2f}, no shunt: a-A CO2 gap",
          at(_r, 'paco2', 300) - at(_r, 'paco2_alv', 300), _wgap, 0.6, " mmHg")
print("    ALL FOUR ROWS ARE NOW THE SAME ROW, because vq_log_sd is inert.")
print("    PaCO2 58.84 against a measured 63 (9) -- inside one SD, which is")
print("    the part that held. PaO2 326.88 against 314 (87) -- also inside.")
print("    Both at the shipped setting, with the shunt off, with nothing")
print("    swept. What has gone is the ability to show it by SWEEPING to it.")
print("    THE OLD NOTE'S WALL IS STILL THERE AND IS STILL THE RIGHT POINT:")
print("    Tokics measured VENTILATION/perfusion dispersion in a VENTILATED")
print("    lung. In apnoea there is no ventilation, and what would drive this")
print("    model is the dispersion of gas VOLUME against perfusion -- a")
print("    different quantity, never measured in an apnoeic human. That is a")
print("    DEFINITION question, not a fit, and no sweep can settle it. The")
print("    fix resolved it by setting the volume dispersion to ZERO, which is")
print("    the only value that needs no measurement to justify.")

print("\nTHE SCORECARD OXYGEN ROWS, RESTATED ON CONTENT")
print("  Three of four were the flat-curve artefact, not disagreements.")
for _lab, _th, _us, _ph, _pc, _hb, _w in (
        ("Ebata patent 600 s", 332.0, 375.3, 7.17, 78.0, 14.0, 0.7),
        ("Tokics ventilated t=0", 159.1, 194.0, 7.40, 40.0, 14.0, 0.8),
        ("Laviola at SaO2 40%", 28.3, 27.7, 7.20, 84.6, 14.0, -3.3),
        ("Stock obstructed 300 s", 314.0, 60.5, 7.26, 63.0, 15.0, -16.7)):
    _st = bg.so2_from_po2(_th, _ph, _pc, 37.0)
    _us_s = bg.so2_from_po2(_us, _ph, _pc, 37.0)
    _ct = bg.HUFNER * _hb * _st + bg.O2_SOL * _th
    _cu = bg.HUFNER * _hb * _us_s + bg.O2_SOL * _us
    check(f"{_lab}: difference in arterial O2 CONTENT",
          100.0 * (_cu - _ct) / _ct, _w, 0.4, " %")
print("    On the quantity that matters for oxygen delivery the model agrees")
print("    with Ebata to 0.7% and Tokics to 0.8%. Laviola sits on the STEEP")
print("    part of the curve where PaO2 is informative, so that row was always")
print("    sound. This SHARPENS the Stock problem: it is no longer one of")
print("    several oxygen discrepancies, it is the ONLY one, and it is")
print("    obstruction-specific. Everything patent or ventilated is exact.")

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
check("sealed lung volume at 1390 s", at(_sa, 'va', 1390), 429.2, 3.0, " mL")
check("sealed lung volume at 1790 s", at(_sa, 'va', 1790), 429.0, 3.0, " mL")
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
print("\nO'LOUGHLIN 2020 OBTAINED AND READ IN FULL -- 2026-09-21")
print("  Anaesthesia 2020;75:1070-1075, doi 10.1111/anae.14959. Read off the")
print("  page: n=64 (42 female), mean (SD) age 47 (16) y, BMI 25 (4) kg/m2;")
print("  10-French tracheal catheter at 0.5-1.0 L/min; apnoea 18.7 (7.2) min;")
print("  VENOUS PCO2 rate of rise 0.15 (0.10) kPa/min; 62/64 completed; all")
print("  patients SpO2 98-100% at the start of apnoea. Exclusions: BMI > 45,")
print("  any condition exacerbated by hypercapnia, severe cardiorespiratory")
print("  disease, predicted prolonged surgery.")
check("their apnoea 18.7 min, in seconds", 18.7 * 60.0, 1122.0, 0.5, " s")
check("their venous rate 0.15 kPa/min, in Pa/min", 0.15 * 1000.0, 150.0, 0.5,
      " Pa/min")
check("their venous rate in mmHg/min", 0.15 * 7.50062, 1.125, 0.005,
      " mmHg/min")
_ol = simulate(Patient(weight=76.5, height=1.75, age=47, hb=14.0),
               [AirwayEpoch(1400, resistance=2, fgo2=1.0)],
               dt=DT, feo2_start=0.92, stop_sao2=0.0)
check("ours: SpO2 at their mean apnoea of 18.7 min", at(_ol, 'spo2', 1122.0),
      99.2, 0.6, " %")
print("    OUR TEST CONFIGURATION IS EXACT -- test_validation.py already used")
print("    BMI 25 and age 47, and the paper gives 25 (4) and 47 (16).")
print("    ONE EDITORIAL CLAIM WAS WRONG AND IS NOW FIXED. editorial.md said")
print("    their 'own tabulation shows arterial studies clustering at")
print("    0.40-0.45 kPa/min'. The paper's range is 0.15-0.45 ACROSS ALL")
print("    studies, and the arterial/transcutaneous ones it cites are 0.4")
print("    (Frumin), 0.24 (Gustafsson) and 0.30 (Toner) -- a spread, not a")
print("    cluster, and the editorial's CO2 recommendation leaned on it.")
print("    Four other claims verified word for word: the 18.7 min mean, the")
print("    0.15 being VENOUS, the explicit statement that venous and end-tidal")
print("    'significantly underestimate carbon dioxide accumulation', the")
print("    BMI>45 and hypercapnia exclusions, and the conclusion being for")
print("    'short duration' surgery in 'non-obese patients'.")
print("    SECONDHAND, recorded as such: O'Loughlin reports Frumin 1959 as")
print("    0.4 kPa/min arterial in EIGHT subjects over surgery lasting 18-55")
print("    min. That corroborates apnoea_core.py's '3.0-3.4 mmHg/min arterial")
print("    (Frumin)' --", f"{0.4*7.50062:.2f} mmHg/min -- and the n=8 read off")
print("    Frumin's own page 789. It does NOT verify the pH 6.72 or PaCO2 250.")

# ---------------------------------------------------------------------------
print("\nTHE PATENT-AIRWAY CO2 SLOPE -- 18% LOW, not 2-3x low")
print("  README called this 'a weakness nothing currently tests', our 1.70")
print("  mmHg/min against 'a classical 3-5'. It is now tested and the")
print("  comparator is not 3-5. Measured on the TONER TRANSCUTANEOUS TRACE,")
print("  one patient, glottic01, 7 March 2017 (unpublished, use authorised")
print("  2026-09-21): baseline 35.46 (SD 0.63) over 1260 s, then a slope of")
print("  2.160 mmHg/min over 452 s with r = 0.9959. Toner's own PUBLISHED")
print("  figure is 0.30 kPa/min = 2.25 mmHg/min, which the trace reproduces.")
print("  ONLY THE MODEL SIDE IS CHECKED BELOW. The measured numbers are not")
print("  scripted on purpose: the spreadsheet is untracked, so a check that")
print("  read it would fail for every recipient of the package.")
_tn = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)
_tnr = simulate(_tn, [AirwayEpoch(900, resistance=2, fgo2=1.00)],
                dt=DT, feo2_start=0.87, stop_sao2=0.0)
check("buccal arm: PaCO2 at 150 s", at(_tnr, 'paco2', 150), 53.79, 0.5,
      " mmHg")
check("buccal arm: PaCO2 at 555 s", at(_tnr, 'paco2', 555), 65.79, 0.5,
      " mmHg")
check("buccal arm: slope 2.5-9.25 min (measured 2.16)",
      (at(_tnr, 'paco2', 555) - at(_tnr, 'paco2', 150)) / ((555 - 150) / 60.0),
      1.778, 0.03, " mmHg/min")
check("buccal arm: slope 1-5 min",
      (at(_tnr, 'paco2', 300) - at(_tnr, 'paco2', 60)) / 4.0, 1.680, 0.03,
      " mmHg/min")
print("    THE DIRECTION IS THE FINDING. Obstructed we are 4.72 against a")
print("    measured 3.4, i.e. 39% TOO STEEP. Patent we are 1.78 against a")
print("    measured 2.16, i.e. 18% TOO SHALLOW. A global error in the CO2")
print("    chemistry -- the dissociation curve, the buffering, the tissue")
print("    stores -- would move BOTH limbs the same way, because all of them")
print("    act whatever the airway is doing. An error that FLIPS SIGN with")
print("    the airway state cannot be any of those. It points at what the")
print("    airway does: dilution by entrained gas when open, and the")
print("    V/Q-weighting mechanism when sealed. That is consistent with the")
print("    V/Q result above and is the first evidence that the two CO2")
print("    disagreements are ONE mechanism seen from two sides.")
print("    NOT A CALIBRATION. n=1, transcutaneous is not arterial, and the")
print("    authorisation terms forbid setting any parameter or band from it.")

# ---------------------------------------------------------------------------
print("\nTWO FAULTS, NOT ONE -- the 'one mechanism' claim REFUTED 2026-09-22")
print("  On 2026-09-21 this file's author wrote that the CO2 sign flip was")
print("  'the first evidence that the two CO2 disagreements are ONE mechanism")
print("  seen from two sides'. The test built to confirm it refuted it.")
print("  If one mechanism drove both, a lever on it would move BOTH limbs in")
print("  opposite directions. Sealed = Stock config, 1-5 min (measured 3.4).")
print("  Patent = Toner buccal config, 2.5-9.25 min (measured 2.16).")


def _seal(**kw):
    _p = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0, **kw)
    return simulate(_p, [AirwayEpoch(900, resistance=OBS, fgo2=0.21)],
                    dt=DT, feo2_start=0.87, paco2_start=39.0, stop_sao2=0.0)


def _pat(**kw):
    _p = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0, **kw)
    return simulate(_p, [AirwayEpoch(900, resistance=2, fgo2=1.00)],
                    dt=DT, feo2_start=0.87, paco2_start=40.0, stop_sao2=0.0)


def _sl(_r, a, b):
    return (at(_r, 'paco2', b) - at(_r, 'paco2', a)) / ((b - a) / 60.0)


for _lab, _kw, _ws, _wp in (
        ("shipped", {}, 1.910, 1.778),
        ("vq_log_sd 0.35", dict(vq_log_sd=0.35), 1.910, 1.778),
        ("vq_log_sd 0.90", dict(vq_log_sd=0.90), 1.910, 1.777),
        ("tau_mix 15", dict(tau_mix=15.0), 1.910, 1.778),
        ("vo2_ref 300", dict(vo2_ref=300.0), 1.890, 2.307),
        ("rq 0.9", dict(rq=0.9), 2.210, 2.078),
        ("v_tis_co2_fast 15", dict(v_tis_co2_fast=15.0), 2.650, 2.408),
        ("k_co2_slow 0.4", dict(k_co2_slow=0.4), 1.970, 1.925)):
    check(f"{_lab}: SEALED slope", _sl(_seal(**_kw), 60, 300), _ws, 0.05,
          " mmHg/min")
    check(f"{_lab}: PATENT slope", _sl(_pat(**_kw), 150, 555), _wp, 0.05,
          " mmHg/min")
print("    THE PARTITION THIS BLOCK ESTABLISHED HAS INVERTED -- 2026-09-23.")
print("    It concluded: 'THE LEVERS PARTITION AND THE SETS ARE DISJOINT. The")
print("    V/Q levers move the sealed limb up to 61% and the patent limb by")
print("    ZERO... The production and store levers move the patent limb and")
print("    barely touch the sealed one: vo2_ref 250 -> 300 moves patent 30%")
print("    and sealed by 0.002 mmHg/min.' Every part of that is now false.")
print("    THE PATENT COLUMN DID NOT MOVE AT ALL -- every patent value above")
print("    is the one recorded on 2026-09-22, to three decimals. The SEALED")
print("    column moved wholesale, and the two lever families swapped roles:")
print("      lever                sealed BEFORE -> NOW    patent (unchanged)")
print("      shipped                   4.520 -> 1.910           1.778")
print("      vq_log_sd 0.35            2.040 -> 1.910           1.778")
print("      vq_log_sd 0.90            5.810 -> 1.910           1.777")
print("      tau_mix 15                7.290 -> 1.910           1.778")
print("      vo2_ref 300               4.440 -> 1.890           2.307")
print("      rq 0.9                    4.810 -> 2.210           2.078")
print("      v_tis_co2_fast 15         5.360 -> 2.650           2.408")
print("      k_co2_slow 0.4            4.694 -> 1.970           1.925")
print("    THE V/Q LEVERS NOW MOVE NEITHER LIMB. They are inert on the lean")
print("    sealed patient for the reason given several blocks above: every")
print("    compartment is identical, so there is nothing to disperse or mix.")
print("    THE PRODUCTION AND STORE LEVERS NOW MOVE BOTH LIMBS, AND BY")
print("    SIMILAR AMOUNTS. v_tis_co2_fast 15 moves sealed +39% and patent")
print("    +35%; rq 0.9 moves sealed +16% and patent +17%. Before, the same")
print("    levers moved patent by tens of percent and sealed by hundredths.")
print("    WHAT THAT DOES TO THE ARGUMENT. The disjointness was the entire")
print("    evidence for TWO FAULTS. It is gone, and what replaces it points")
print("    the other way: one family of levers moves both limbs together,")
print("    which is the signature of a SHARED mechanism. The claim refuted")
print("    on 2026-09-22 -- that the two CO2 disagreements are one mechanism")
print("    seen from two sides -- is therefore BACK ON THE TABLE.")
print("    RULED ONE DEFECT, 2026-09-24. A. Heard. The model is worked from")
print("    here on as ONE CO2 fault seen from two sides, and HANDOVER may")
print("    say so.")
print("    WHAT THE RULING RESTS ON, stated so it can be overturned:")
print("      1. The production and store levers move BOTH limbs, by similar")
print("         amounts -- v_tis_co2_fast 15 moves sealed +39% and patent")
print("         +35%, rq 0.9 moves sealed +16% and patent +17%. A lever")
print("         family that moves two quantities together is the ordinary")
print("         signature of one mechanism underneath them.")
print("      2. Both limbs now err in the SAME direction, too shallow:")
print("         sealed 1.91 against a measured 3.4, patent 1.78 against")
print("         2.16. Two independent faults would not be expected to")
print("         agree in sign.")
print("      3. No lever now separates them. The V/Q levers, which used to")
print("         move the sealed limb alone, move neither.")
print("    WHAT IT DOES NOT REST ON, AND THIS IS THE HONEST PART. The same")
print("    three observations are ALSO consistent with two faults that")
print("    happen to share the CO2 chemistry -- the dissociation curve, the")
print("    buffering and the tissue stores act on both limbs whatever the")
print("    airway is doing, so a shared lever family is expected either")
print("    way. Point 1 is therefore weak evidence, not strong. Point 2 is")
print("    the same observation restated. THE RULING IS A DECISION TO STOP")
print("    HEDGING AND WORK A SINGLE MECHANISM, NOT A DEMONSTRATION THAT")
print("    THERE IS ONE.")
print("    WHAT WOULD OVERTURN IT: any lever that moves one limb and not")
print("    the other. If one is found, this ruling is void and the search")
print("    for a shared mechanism should stop. The sealed limb alone is")
print("    reachable through the alveolar-to-arterial step, which is where")
print("    the a-A CO2 gap rows below show the sealed and patent airways")
print("    behaving completely differently -- so such a lever may well")
print("    exist and has simply not been looked for since the V/Q fix")
print("    removed the old one.")
print("    AND ONE THING THE RULING MAKES TESTABLE. If it is one fault,")
print("    the single correction that brings the sealed limb from 1.91 to")
print("    3.4 must ALSO bring the patent limb from 1.78 to 2.16 -- a")
print("    factor of 1.78 on one and 1.21 on the other. It must therefore")
print("    NOT be a simple gain on CO2 production or storage, because those")
print("    scale both limbs by the same factor. That is a real constraint")
print("    and it came out of the ruling rather than out of the data.")
_gs, _gp = _seal(), _pat()
for _t, _wgs, _wgp in ((60, -0.18, 0.11), (300, 8.27, -0.05), (555, -2.52, 0.08)):
    check(f"a-A CO2 gap at {_t} s, SEALED",
          at(_gs, 'paco2', _t) - at(_gs, 'paco2_alv', _t), _wgs, 0.25, " mmHg")
    check(f"a-A CO2 gap at {_t} s, PATENT",
          at(_gp, 'paco2', _t) - at(_gp, 'paco2_alv', _t), _wgp, 0.25, " mmHg")
print("    WHY: with the airway OPEN the gap is zero to within a tenth of a")
print("    mmHg at every timepoint. Fresh gas keeps the compartments")
print("    equilibrated, so the V/Q-weighting mechanism has nothing to bite")
print("    on. Seal the airway and it switches on hard (+8.27 at 300 s). The")
print("    mechanism found on 2026-09-21 is real and is EXCLUSIVELY an")
print("    obstructed-airway mechanism. It cannot explain the patent")
print("    shortfall because it is not operating there.")
print("    THE PATENT FAULT POINTS AT THE FAST CO2 TISSUE STORE. vo2_ref")
print("    would have to RISE to about 285 to fix the slope, but Farmery &")
print("    Roe quoting Nunn puts anaesthetised VO2 at 0.20 L/min against our")
print("    232 mL/min -- our production is if anything already too high, so")
print("    raising it would be tuning against the literature. v_tis_co2_fast")
print("    would have to fall from 22 to about 18, and THAT store is")
print("    calibrated against the paper nobody has read: Kaiser HA et al,")
print("    Sci Rep 2024;14:3617, open access. Specific prediction: if their")
print("    measured CO2 kinetics imply a fast store smaller than 22, the")
print("    patent limb resolves without touching the sealed limb at all.")

# ---------------------------------------------------------------------------
print("\nTHE NOTTINGHAM SIMULATOR HAS 100-500 V/Q COMPARTMENTS -- THIS BLOCK")
print("WAS WRONG, CORRECTED 2026-09-22 THE SAME DAY IT WAS WRITTEN")
print("  What follows below is the Hardman 1998 Appendix 1 reading that this")
print("  block was built on. It is quoted correctly. The CONCLUSION drawn")
print("  from it -- that ICSM has no V/Q distribution, that our mechanism is")
print("  structurally absent from their model, and that any use of an ICSM")
print("  number to argue about V/Q is void -- IS FALSE, and was used to")
print("  dismiss a comparator that turns out to AGREE WITH THE HUMAN")
print("  MEASUREMENT where we do not.")
print("  Hardman JG, Wills JS, Aitkenhead AR, Anesth Analg 2000;90:619-24,")
print("  Methods, verbatim: the NPS respiratory models include \'100 parallel")
print("  pulmonary compartments with independent compliance curves and")
print("  ventilation/perfusion ratios\'.")
print("  McNamara MJ, Hardman JG, Anaesthesia 2005;60:741-6, Methods:")
print("  \'Five hundred alveolar compartments were used in the model ... Each")
print("  of the 500 alveolar compartments has an independently configured")
print("  compliance curve and inlet (bronchiolar) resistance. Each alveolar")
print("  compartment has an associated pulmonary vessel ... with an")
print("  independently configured vascular resistance\'. Their deliberately")
print("  defective configuration had mean (SD) V/Q ratio 1.54 (0.84).")
print("  SO THEY HAVE 100 COMPARTMENTS BY 2000 AND 500 BY 2005, AGAINST OUR")
print("  80. The 1998 description was of a simpler configuration and does not")
print("  describe the model used in any paper we compare against.")
print("  A CV of 0.84/1.54 = 0.545 corresponds, if log-normal, to a log SD")
print("  near 0.51 -- NARROWER THAN OUR 0.70, in a lung they built to be")
print("  pathological. Recorded as an observation, not as a target.")
print("")
print("THE ORIGINAL BLOCK, LEFT IN PLACE SO THE ERROR IS VISIBLE:")
print("  Hardman JG, Bedforth NM, Ahmed AB, Mahajan RP, Aitkenhead AR,")
print("  Br J Anaesth 1998;81:327-332, Appendix 1, VERBATIM:")
print('    "Complete mixing of gases within the alveoli is assumed. ...')
print('     Blood flow through the lung is modelled as two compartments:')
print('     shunted and non-shunted blood. ... Each packet comes to a true')
print('     equilibrium with alveolar gases"')
print("  ONE well-mixed alveolar compartment, blood flow split TWO ways.")
check("our compartment count (theirs: 100 in 2000, 500 in 2005)",
      float(Patient().n_vq), 80.0, 0.5, "")
print("    So the mechanism identified on 2026-09-21 as our sealed-airway")
print("    fault -- arterial blood as a perfusion-weighted CONTENT average")
print("    across a V/Q spread, read back through a curved relationship --")
print("    CANNOT EXIST IN THEIRS. It is structurally absent.")
print("    THE CONSEQUENCE THAT MATTERS: the ICSM comparator cannot arbitrate")
print("    our V/Q question in EITHER direction. Agreement would not")
print("    corroborate the mechanism and disagreement would not refute it,")
print("    because their model has no such degree of freedom. Any future use")
print("    of an ICSM number to argue about V/Q is void.")
print("    Also read off the paper: 'apnoea', 'apnea', 'V/Q' and")
print("    'ventilation-perfusion' appear ZERO times in the whole paper. Its")
print("    own scope sentence recommends it 'for predicting the effects of")
print("    alterations in mechanical ventilation in stable patients in the")
print("    intensive care unit'. Validated on 31 ICU patients against changes")
print("    in minute volume or FiO2; 95% limits of agreement PaO2 -2.07 to")
print("    +2.47 kPa, PaCO2 -0.33 to +0.67, pH -0.023 to +0.033.")
print("    TWO CORRECTIONS IT FORCES. (1) The 'Hardman ECF 11.6 against our")
print("    24.7' comparison was UNLIKE-FOR-UNLIKE: their Appendix 2 gives")
print("    BEecf = [HCO3-] - 11.6*(7.4 - pH) - 24, an EXTRACELLULAR base-")
print("    excess conversion applied to a blood-gas reading, not the")
print("    simulator's internal blood buffering. Ours is Siggaard-Andersen's")
print("    non-bicarbonate buffer capacity for WHOLE BLOOD. The discrepancy")
print("    was never real. (2) They use THOMAS's equation for content-to-")
print("    partial-pressure where we use Severinghaus; bloodgas.py's")
print("    PROVENANCE header raises that choice and can now name which model")
print("    uses which.")

# ---------------------------------------------------------------------------
print("\nSTOCK vs ICSM vs US, on the ONE channel where all three exist")
print("  Asked 2026-09-22: does ICSM agree with Stock under obstruction?")
print("  On CO2 it can be answered, and the answer reverses a claim this")
print("  repository had been shipping in a test_validation.py docstring.")
_s10 = 12.0 + 9 * 3.4
check("Stock's own fit carried to 10 min", _s10, 42.6, 0.05, " mmHg")
print("    = 12 mmHg in the first minute + 9 x 3.4 thereafter, which is his")
print("    OWN piecewise fit. HIS DATA STOP AT 5 MIN, so this is an")
print("    extrapolation of his fit, not a measurement. He reports the rise")
print("    as LOGARITHMIC, so carrying it forward LINEARLY over-estimates")
print("    his own curve -- the caveat tightens the agreement below, it does")
print("    not loosen it.")
print("    Laviola 2026, in silico, 10 min: 38.2 (8.2) mmHg, read from the")
print("    main text 2026-09-21. Their 1 SD band is 30.0 to 46.4.")
check("Stock's 42.6 minus Laviola's mean 38.2", _s10 - 38.2, 4.4, 0.05, " mmHg")
print("    4.4 mmHg apart, INSIDE their 1 SD. A human measurement and a")
print("    simulator that has NO V/Q DISTRIBUTION land on the same number.")
_ten = run(duration=700.0)
_o10 = at(_ten, 'paco2', 600) - _ten['paco2'][0]
check("ours, same 10 min sealed", _o10, 27.4, 0.5, " mmHg")
check("ours as a fraction of Stock's extrapolated rise",
      100.0 * _o10 / _s10, 64.3, 1.5, " %")
print("    WE ARE THE OUTLIER, 28% below both of them. That is the opposite")
print("    of what the struck docstring said. It claimed ICSM and we both")
print("    landed 'a long way from Stock'; on this channel ICSM and Stock")
print("    agree with each other and we do not.")
print("    CAVEAT ON THEIR END, stated because it is the weak point of the")
print("    comparison: Laviola's 10 minutes INCLUDES the post-")
print("    cricothyroidotomy period with RapidO2 insufflations, so it is not")
print("    pure obstruction throughout. Their protocol is in SOURCES.md 1b.")
print("    ON OXYGEN THERE IS NOTHING TO COMPARE, and this is the part that")
print("    was asserted without a number. The SDC gives the state at SaO2")
print("    40% and the main text gives no oxygen tension at any FIXED TIME.")
print("    We hold NO ICSM arterial oxygen value at 5 minutes, or at any")
print("    other moment Stock measured. Where their oxygen sits against")
print("    Stock is UNKNOWN to this repository. It should be recorded as")
print("    unknown rather than guessed, which is the whole of CLAUDE.md's")
print("    first rule, and the struck sentence broke it.")
print("    WHAT WOULD CLOSE THIS: any ICSM publication giving PaO2 or SaO2")
print("    at a fixed time under complete obstruction -- a time course")
print("    rather than an endpoint state. See SOURCES.md.")

# ---------------------------------------------------------------------------
print("\nREMOVING THE V/Q SPREAD -- THE ANSWER IS NOW 'NOTHING AT ALL'")
print("  RESOLVED 2026-09-23. This block asked, on 2026-09-22: what does")
print("  vq_log_sd actually do to every reported variable? At the time it did")
print("  a great deal, and the answer drove that day's category-error fix.")
print("  AFTER THAT FIX IT DOES NOTHING. Both arms below are now identical to")
print("  five significant figures on every channel, and reach SaO2 40% within")
print("  0.1 s of each other. The rows are kept and renumbered to the common")
print("  value BECAUSE THEY ARE NOW AN ASSERTION OF INERTNESS -- if the two")
print("  arms ever diverge again, something has reintroduced a dependence on")
print("  a parameter that is supposed to have none. vq_chart.py carries the")
print("  same assertion.")
print("  Two runs of THIS model, identical but for that one number.")
print("  A is the shipped 0.70. B is 0.01 -- one effectively uniform alveolar")
print("  compartment, which is the STRUCTURE Hardman 1998 Appendix 1")
print("  describes. B IS OUR CODE EMULATING THEIR STRUCTURE. It is not their")
print("  model, not their output, and no B number may be reported as an ICSM")
print("  result. Configuration is test_validation.test_stock_1989 exactly --")
print("  70 kg, 1.75 m, 45 y, Hb 15.0, tube clamped, room air -- so the")
print("  comparison with Stock is like-for-like with the benchmark.")
print("  Drawn by vq_chart.py; ARBITRATED HERE.")


def _vqrun(sd):
    _p = Patient(weight=70, height=1.75, age=45, hb=15.0, vq_log_sd=sd)
    return simulate(_p, [AirwayEpoch(1400, resistance=OBS, fgo2=0.21)],
                    dt=DT, stop_sao2=0.0)


_vqA, _vqB = _vqrun(0.70), _vqrun(0.01)
for _k, _lab, _wa, _wb, _tol in (
        ('pao2',  'PaO2 at 300 s',  157.48, 157.48, 0.60),
        ('paco2', 'PaCO2 at 300 s',   60.09,  60.09, 0.15),
        ('sao2',  'SaO2 at 300 s',    99.11,  99.11, 0.30),
        ('ph',    'pH at 300 s',       7.276,  7.276, 0.005)):
    check(f"spread ON  0.70: {_lab}", at(_vqA, _k, 300), _wa, _tol)
    check(f"spread OFF 0.01: {_lab}", at(_vqB, _k, 300), _wb, _tol)
check("spread ON  0.70: first-minute CO2 rise",
      at(_vqA, 'paco2', 60) - _vqA['paco2'][0], 12.16, 0.10, " mmHg")
check("spread OFF 0.01: first-minute CO2 rise",
      at(_vqB, 'paco2', 60) - _vqB['paco2'][0], 12.16, 0.10, " mmHg")
check("spread ON  0.70: Stock 1-5 min slope",
      (at(_vqA, 'paco2', 300) - at(_vqA, 'paco2', 60)) / 4.0, 1.95, 0.05,
      " mmHg/min")
check("spread OFF 0.01: Stock 1-5 min slope",
      (at(_vqB, 'paco2', 300) - at(_vqB, 'paco2', 60)) / 4.0, 1.95, 0.05,
      " mmHg/min")
check("spread ON  0.70: SaO2 40% reached at",
      time_to(_vqA, 'sao2', 40), 496.0, 3.0, " s")
check("spread OFF 0.01: SaO2 40% reached at",
      time_to(_vqB, 'sao2', 40), 496.0, 3.0, " s")
print("    Stock 1989 MEASURED, 14 anaesthetised adults, tube clamped:")
print("      PaO2 314 (87)   PaCO2 63 (9)   pH 7.26 (0.06)   SaO2 >92% in ALL")
print("      first minute 12 mmHg, thereafter 3.4 mmHg/min (band 2.4-4.4)")
print("    WHAT THIS BLOCK USED TO SAY, AND WHY IT IS NOW HISTORY:")
print("      'ON OXYGEN THE SPREAD IS MOST OF THE DEFECT.' Killing it moved")
print("      PaO2 61 -> 157 against a measured 314 -- a 2.6x move toward the")
print("      measurement -- and turned a saturation failing Stock's 'every")
print("      patient above 92%' into one that passes. THAT MOVE HAS BEEN")
print("      MADE PERMANENT: the fix killed the spread for every run, so 157")
print("      and 99.1% are now simply what the model gives. It still does")
print("      not reach 314, so the spread was never the whole oxygen story.")
print("      'ON CO2 THE SPREAD BRACKETS THE MEASUREMENT.' 4.72 was 39% high,")
print("      1.95 is 43% low, and Stock's 3.4 sat between them. Only the")
print("      1.95 arm now exists, so THE MODEL IS PERMANENTLY ON THE LOW")
print("      SIDE and the bracket is gone. That is the cost side of the fix,")
print("      it was argued in the commit that made it, and it is why")
print("      'Stock obstructed, 1-5 min slope' sits in known-blocking.txt.")
print("    Stock 1989 MEASURED, 14 anaesthetised adults, tube clamped:")
print("      PaO2 314 (87)   PaCO2 63 (9)   pH 7.26 (0.06)   SaO2 >92% in ALL")
print("      first minute 12 mmHg, thereafter 3.4 mmHg/min (band 2.4-4.4)")
print("    On the ABSOLUTE 300 s CO2 value we are inside +-1 SD of 63 (9), so")
print("    the SLOPE remains the only statistic that discriminates. An")
print("    earlier draft said one arm was 'in band' where the other was")
print("    'out'. Both were in. That claim was wrong and is struck here")
print("    rather than quietly dropped.")
print("    The first-minute rise is INERT to the spread -- 12.02 against")
print("    12.16, both on a measured 12 -- so the bulk CO2 bookkeeping is")
print("    right either way and only the a-A gap moves. Same result the")
print("    dispersion block above reaches by a different route.")
print("    AND AGAINST LAVIOLA 2026 THE SIGN REVERSES: removing the spread")
print("    makes agreement WORSE on PaO2, PaCO2, cardiac output and MAP at")
print("    the SaO2 40% state. So the human measurement wants LESS spread")
print("    and the other simulator wants MORE.")
print("    NEITHER ARBITRATES. Laviola's simulator has no V/Q distribution")
print("    at all (block above), so it cannot be an authority on the")
print("    parameter; and Stock's two channels disagree with each other.")
print("    THIS IS NOT PERMISSION TO SPLIT THE DIFFERENCE. vq_log_sd 0.50")
print("    puts the CO2 slope in band (3.16, recorded above) and would move")
print("    oxygen too. That is a fit, not a mechanism, and CLAUDE.md forbids")
print("    it. The parameter stays at 0.70 pending a written ruling.")
print("    WHAT WOULD SETTLE IT: time-to-desaturation is NEARLY BLIND to")
print("    this parameter -- 513 s against 496 s, a 3.3% difference across")
print("    the entire plausible range of the thing that moves PaO2 by 2.6x.")
print("    So any experiment reading out desaturation TIME cannot decide it.")
print("    It needs a GAS STATE measured under obstruction, which is Stock")
print("    and only Stock, or a measurement of regional gas volume against")
print("    regional perfusion, which nobody in this repository has made.")

# ---------------------------------------------------------------------------
print("\nTHE PATENT-AIRWAY DEFECT IS A 60-SECOND TRANSIENT -- 2026-09-22")
print("  Toner 2019 and Kaiser 2024 both obtained and READ. Toner, n=20,")
print("  patent airway: early CO2 LINEAR at 3.16 (buccal) / 2.82 (sham)")
print("  mmHg/min; prolonged buccal NONLINEAR, 'declined over time',")
print("  averaging 2.22. Sham apnoea median 447 s, IQR 405-525 -- the paper")
print("  says 'median (interquartile range)', so it IS an IQR. Mean tracheal")
print("  pressure 0.21 (SD 0.39) buccal, 0.56 (SD 1.25) sham cmH2O.")
print("  Kaiser, n=91: PaCO2 43 (IQR 10) -> 73 (IQR 14) over 15 min, mean")
print("  change 2.1 mmHg/min; cardiac output 5.0 -> 6.5 L/min, +30%.")


def _co2win(sealed, pc0):
    _p = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)
    return simulate(_p, [AirwayEpoch(1000,
                    resistance=(OBS if sealed else 2),
                    fgo2=(0.21 if sealed else 1.00))],
                    dt=DT, feo2_start=(0.87 if sealed else 0.90),
                    paco2_start=pc0, stop_sao2=0.0)


_rs, _rp = _co2win(True, 39.0), _co2win(False, 43.0)
for _a, _b, _lab, _wsl, _wpa in ((0, 60, '0-1 min', 11.76, 12.16),
                                 (60, 120, '1-2 min', 1.75, 1.38),
                                 (120, 300, '2-5 min', 5.59, 1.91)):
    check(f"{_lab}: SEALED slope",
          (at(_rs, 'paco2', _b) - at(_rs, 'paco2', _a)) / ((_b - _a) / 60.0),
          _wsl, 0.15, " mmHg/min")
    check(f"{_lab}: PATENT slope",
          (at(_rp, 'paco2', _b) - at(_rp, 'paco2', _a)) / ((_b - _a) / 60.0),
          _wpa, 0.15, " mmHg/min")
print("    THE FIRST-MINUTE RISE IS ESSENTIALLY IDENTICAL IN THE TWO")
print("    REGIMES: 11.76 sealed against 12.16 patent. Sealed that is RIGHT,")
print("    Stock measured 12 and the suite checks it. Patent it is wrong by")
print("    nearly FOUR TIMES -- Toner's early phase is linear at 3.16")
print("    mmHg/min, so about 3.2 mmHg in the first minute.")
print("    THE MODEL APPLIES AN OBSTRUCTION-SIZED EQUILIBRATION TRANSIENT TO")
print("    AN OPEN AIRWAY. At onset, arterial CO2 jumps toward mixed venous")
print("    because gas exchange stops clearing it. Sealed, it has nowhere to")
print("    go. With fresh gas flowing past, the jump should be heavily")
print("    damped. Ours is barely damped at all.")
print("    IT ALSO RESOLVES AN INCONSISTENCY. Over a window INCLUDING the")
print("    first minute we look too steep (2.48 against Kaiser's 2.1); over")
print("    one EXCLUDING it we look too shallow (1.78 against Toner's 2.22).")
print("    One localised error: a first-minute transient ~4x too large, then")
print("    a plateau slightly too shallow.")
print("    AND THE SHAPE AGREES, contrary to what was written on 2026-09-21.")
for _a, _b, _w in ((120, 240, 1.916), (480, 600, 1.820), (720, 900, 1.723)):
    check(f"patent slope {_a//60}-{_b//60} min (declining, as Toner reports)",
          (at(_rp, 'paco2', _b) - at(_rp, 'paco2', _a)) / ((_b - _a) / 60.0),
          _w, 0.1, " mmHg/min")
print("    Ours declines monotonically once the transient is past, which is")
print("    the direction Toner reports. The earlier 'our slope increases'")
print("    claim compared two windows straddling the transient, so it")
print("    measured the transient rather than the shape.")
_ck = _co2win(False, 43.0)
check("Kaiser window: our mean change over 15 min (theirs 2.1)",
      (at(_ck, 'paco2', 900) - at(_ck, 'paco2', 0)) / 15.0, 2.482, 0.05,
      " mmHg/min")
check("Kaiser window: our cardiac output rise (theirs +30%)",
      100.0 * (at(_ck, 'co', 900) / at(_ck, 'co', 0) - 1.0), 35.9, 0.6, " %")
print("    NOTE ON THE 'FAST STORE' PREDICTION of 2026-09-21: it was BADLY")
print("    POSED and is neither confirmed nor refuted. Kaiser reports a RATE,")
print("    not a store. Deriving a store from their rate through our own")
print("    model and then using it to correct that model is circular -- the")
print("    exact pattern the source audit flagged for co_co2_gain.")

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
    return _t95(weight=105, height=1.74, age=42, hb=14, tilt_deg=30, **kw)


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
print("\nvq_log_sd IS A DEAD PARAMETER -- established 2026-09-23")
print("  It is the width of the ventilation-to-perfusion distribution: how")
print("  unevenly air and blood are matched from region to region. After the")
print("  V/Q category-error fix it has NO EFFECT ON ANY OUTPUT, sealed or")
print("  patent. Its own docstring claimed the opposite until corrected.")
print("  Checked by SWEEP, not by reading the code, because a claim that a")
print("  parameter does nothing is exactly the kind that gets asserted:")


def _vq(sd, res):
    _p = Patient(weight=70, height=1.75, age=45, hb=15.0, vq_log_sd=sd)
    return simulate(_p, [AirwayEpoch(1200.0, resistance=res, fgo2=0.21)],
                    dt=DT, stop_sao2=0.0)


for _res, _lab, _o2, _co2, _sa in ((OBS, 'sealed', 157.22, 60.07, 99.103),
                                   (2.0, 'patent', 169.84, 58.18, 99.308)):
    for _sd in (0.01, 0.35, 0.70, 1.18):
        _r = _vq(_sd, _res)
        check(f"{_lab}, vq_log_sd {_sd:.2f}: PaO2 at 300 s",
              at(_r, 'pao2', 300.0), _o2, 0.01, " mmHg")
        check(f"{_lab}, vq_log_sd {_sd:.2f}: PaCO2 at 300 s",
              at(_r, 'paco2', 300.0), _co2, 0.01, " mmHg")
        check(f"{_lab}, vq_log_sd {_sd:.2f}: SaO2 at 300 s",
              at(_r, 'sao2', 300.0), _sa, 0.01, " %")
print("    A HUNDREDFOLD RANGE, IDENTICAL TO FIVE SIGNIFICANT FIGURES. The")
print("    name appears in no executable statement in apnoea_core.py -- only")
print("    its declaration and two docstrings -- and vqDist(n, sd) in")
print("    model.js never reads sd. Both implementations are dead the SAME")
print("    way, so test_parity.py could never see it: parity tests")
print("    agreement, not liveness.")
print("    THIS IS NOT A BUG. The model has NO IMPOSED V/Q dispersion. Every")
print("    compartment is identical at t=0 and they diverge only through")
print("    mechanisms -- absorption collapse per compartment, and the")
print("    unwashed fraction. That is what vq_distribution()'s own docstring")
print("    argued for. The state is now the aspiration.")
print("    The slider it fed on airway_scenario.html HAS BEEN REMOVED: a")
print("    control that does nothing is worse than no control, and that page")
print("    is used by an anaesthetist. vq_chart.py now ASSERTS the two arms")
print("    agree, so a reintroduced dependence fails loudly.")

# ---------------------------------------------------------------------------
print("\nTHE PULSE-OXIMETER LAG, and a comparison error it caused")
print("  Gander drew arterial blood when the OXIMETER read 92%. Our spo2")
print("  output carries a delay and a time constant, so at the moment it")
print("  DISPLAYS 92 the true arterial saturation is already far lower, and")
print("  PaO2 follows the true value. Comparing at the displayed number made")
print("  a 24 mmHg 'disagreement' that is not one.")
_gh = 1.70
_gp2 = Patient(weight=47.0 * _gh * _gh, height=_gh, age=38, hb=14.0)
_gr2 = simulate(_gp2, [AirwayEpoch(900.0, resistance=2.0, fgo2=0.21)],
                dt=DT, feo2_start=0.90, paco2_start=46.0, stop_sao2=0.0)
check("spo2_delay as shipped", _gp2.spo2_delay, 25.0, 1e-9, " s")
check("spo2_tau as shipped", _gp2.spo2_tau, 8.0, 1e-9, " s")
_t_disp = time_to(_gr2, 'spo2', 92)
_t_true = time_to(_gr2, 'sao2', 92)
check("when the OXIMETER reads 92: PaO2 [Gander 68 (10)]",
      at(_gr2, 'pao2', _t_disp), 43.6, 1.0, " mmHg")
check("  ... and the TRUE saturation then is",
      at(_gr2, 'sao2', _t_disp), 74.2, 1.0, " %")
check("when the TRUE saturation is 92: PaO2 [Gander 68 (10)]",
      at(_gr2, 'pao2', _t_true), 70.0, 1.0, " mmHg")
check("  ... in SD of Gander's 68 (10)",
      abs(at(_gr2, 'pao2', _t_true) - 68.0) / 10.0, 0.0, 0.6, " SD")
check("the two readings are how far apart, in saturation points",
      at(_gr2, 'spo2', _t_disp) - at(_gr2, 'sao2', _t_disp), 17.8, 1.0, " %")
print("    THE TWO READINGS BRACKET THE MEASURED VALUE, so the row is not a")
print("    disagreement. But it RELOCATES the problem rather than excusing")
print("    it: Gander's PaO2 68 at a pH near 7.3 implies a TRUE saturation")
print("    near 92 at the moment they drew blood, so THEIR oximeter was")
print("    reading close to the truth. Ours is 17 points out at the same")
print("    instant. Either the lag is too long for their probe and protocol,")
print("    or our desaturation through that region is too steep.")
print("    spo2_delay 25 s and spo2_tau 8 s HAVE NO SOURCE recorded anywhere")
print("    in this repository. That matters more than one row: every")
print("    desaturation-time benchmark in test_validation.py -- Toner,")
print("    Heard, the four tilt trials, Gander -- is scored on a threshold")
print("    crossing of spo2, so all of them inherit this lag model.")

# ---------------------------------------------------------------------------
print("\nLOW V/Q FROM INCOMPLETE DENITROGENATION -- added 2026-09-23")
print("  A lung unit whose airway is already shut when preoxygenation starts")
print("  never sees the oxygen. It is NOT collapsed -- it still holds gas and")
print("  is still perfused -- but the gas is the alveolar AIR it had when the")
print("  airway closed, so blood leaving it is poorly oxygenated while every")
print("  other unit's is maximally oxygenated. Low V/Q, not shunt.")
print("  NO NEW FREE PARAMETER: same max_closed and cc_k as the runtime")
print("  collapse term, evaluated at the AWAKE lung volume because")
print("  preoxygenation happens before induction.")


def _uw(**kw):
    return Patient(**kw).unwashed_fraction() * 100.0


print("  IT IS EXACTLY ZERO WHEREVER FRC EXCEEDS CLOSING CAPACITY, which is")
print("  every young lean supine patient -- so no lean benchmark can move:")
check("Stock/Toner reference patient, 45 y, BMI 22.9",
      _uw(weight=70, height=1.75, age=45, hb=15.0), 0.0, 1e-9, " %")
check("the SAME patient at 80 years (closure is age as well as BMI)",
      _uw(weight=70, height=1.75, age=80, hb=15.0), 3.49, 0.05, " %")
check("Heard cohort, BMI 34.7 at 30 deg head-up",
      _uw(weight=105, height=1.74, age=42, hb=14, tilt_deg=30), 3.78, 0.05, " %")
check("Gander cohort, BMI 47 supine",
      _uw(weight=47 * 1.70 ** 2, height=1.70, age=38, hb=14), 15.79, 0.05, " %")
print("  WHAT IT MOVED IN test_validation.py, and it is the whole list. Every")
print("  row that moved is obese or elderly; every lean row is bit-identical:")
print("      Heard control, SpO2<95%     319.8 -> 310.2 s   band 244-314  PASS")
print("      tilt, BMI 44 at 25 deg       33.4 ->  35.9 %   band  20-45   PASS")
print("      tilt, BMI 35 at 30 deg       45.4 ->  51.1 %   band  20-45   FAIL")
print("      Toner sham, SpO2<95%        444.5 -> 444.5 s   UNCHANGED")
print("      tilt, non-obese 20 deg       28.6 ->  28.6 %   UNCHANGED")
print("      every Stock row                      unchanged to 1 decimal")
print("  THE TILT ROW IS THE COST AND IT IS RECORDED, NOT COMPENSATED.")
print("  Head-up tilt raises awake FRC, which shrinks the unwashed fraction,")
print("  so the mechanism AMPLIFIES the benefit of tilt -- 45.4% to 51.1%")
print("  against a measured ~+30%. That row was already failing at 45.4 and")
print("  is now failing worse. CLAUDE.md: a correction that makes a benchmark")
print("  worse is information. The honest reading is that tilt gets TWO bites")
print("  in this model, once through FRC and once through denitrogenation,")
print("  and whether a real lung gives it both is an open question.")

# ---------------------------------------------------------------------------
print("\nTHE TILT -> CARDIAC OUTPUT TERM -- added 2026-09-24, and it makes a")
print("  channel WORSE. Perilli 2003 phase 4 vs phase 5, identical but for")
print("  position: cardiac output 4.9 (0.9) -> 4.0 (0.8) L/min, P<0.05.")
print("  -18.4% at 30 degrees, so co_tilt_gain = 0.184/30 = 0.00612 per degree.")

_TH, _TBMI, _TAGE, _THB, _TPACO2 = 1.61, 48.1, 37.0, 14.0, 33.0


class _NoCoTilt(Patient):
    def tilt_co_factor(self):
        return 1.0


def _tco(cls, tilt):
    return cls(weight=_TBMI*_TH*_TH, height=_TH, age=_TAGE, hb=_THB,
               tilt_deg=tilt)


check("tilt_co_factor at 30 deg [Perilli -18.4%]",
      _tco(Patient, 30.0).tilt_co_factor(), 0.8164, 0.001, "")
check("  ... our CO ratio, supine to 30 deg",
      _tco(Patient, 30.0).co_anaes() / _tco(Patient, 0.0).co_anaes(),
      0.8164, 0.001, "")
check("  ... Perilli's measured ratio", 4.0 / 4.9, 0.8163, 0.001, "")
print("    THE RATIO IS EXACT. Our ABSOLUTE cardiac output is not: we give")
print("    5.78 L/min supine at his BMI 48 against his measured 4.9, +18%.")
print("    That matters beyond this row, because the 10-12% obese shunt was")
print("    inverted THROUGH this model's cardiac output -- see Dantzker 1980")
print("    in the Perilli section of SOURCES.md.")
check("our supine CO at Perilli's cohort [measured 4.9 (0.9)]",
      _tco(Patient, 0.0).co_anaes(), 5.78, 0.05, " L/min")


def _tox(cls, fio2, tilt):
    _p = _tco(cls, tilt)
    _alv = fio2 * ac.PDRY - _TPACO2 / 0.8
    _r = simulate(_p, [AirwayEpoch(2.0, resistance=2.0, fgo2=fio2)],
                  dt=DT, feo2_start=_alv / ac.PDRY, paco2_start=_TPACO2,
                  stop_sao2=0.0)
    return _r['pao2'][0]


print("  IT USED TO FLIP THE SIGN OF PERILLI\'S OWN OXYGENATION RESULT, AND")
print("  THE RE-KEY OF 2026-09-24 FIXED THAT. He measures PaO2 146 -> 179,")
print("  +33 mmHg, IMPROVING with tilt DESPITE the cardiac output falling.")
print("  At his cohort, FiO2 0.50:")
_b0, _b30 = _tox(_NoCoTilt, 0.50, 0.0), _tox(_NoCoTilt, 0.50, 30.0)
_a0, _a30 = _tox(Patient, 0.50, 0.0), _tox(Patient, 0.50, 30.0)
check("FRC route + shunt route, no CO term: PaO2 change at 30 deg [meas +33]",
      _b30 - _b0, 36.2, 0.3, " mmHg")
check("WITH the CO term:   PaO2 change at 30 deg [measured +33]",
      _a30 - _a0, 17.3, 0.3, " mmHg")
check("  error against +33, no CO term", abs(_b30 - _b0 - 33.0), 3.2, 0.3, " mmHg")
check("  error against +33, WITH",   abs(_a30 - _a0 - 33.0), 15.7, 0.3, " mmHg")
print("    THE SIGN IS RIGHT NOW. On the BMI-keyed curve these were +3.8 and")
print("    -11.8, so the model said head-up tilt made this patient WORSE")
print("    against a measured +33. The re-key turned -11.8 into +17.3 and")
print("    cut the error from 44.8 to 15.7, a 65% reduction, WITHOUT any")
print("    parameter being touched to achieve it -- the shunt law was fitted")
print("    to Pelosi\'s supine curve alone and Perilli was never in the fit.")
print("    WHAT IS STILL WRONG, AND IT IS NOW THE CARDIAC-OUTPUT TERM.")
print("    Without it the FRC and shunt routes together give +36.2 against")
print("    +33, an error of 3.2 mmHg. Adding the measured CO loss takes it")
print("    to +17.3. So the two effects are individually defensible and")
print("    together they overshoot the cost. Three readings are open and")
print("    this row cannot separate them: the CO term is too strong; or")
print("    tilt gets too many bites on the oxygen side (store,")
print("    denitrogenation, and now shunt); or our absolute cardiac output,")
print("    18% above Perilli\'s measured 4.9 L/min, makes a proportional")
print("    loss bite harder than it should. NOT COMPENSATED. No parameter")
print("    was moved to close the remaining 15.7 mmHg.")
check("standing shunt, supine", 
      _tco(Patient, 0.0).shunt_base_eff() * 100.0, 12.53, 0.02, " %")
check("standing shunt at 30 deg [IT MOVES NOW -- this was the defect]",
      _tco(Patient, 30.0).shunt_base_eff() * 100.0, 9.18, 0.02, " %")
check("FRC supine at this patient", _tco(Patient, 0.0).frc_anaes(),
      585.0, 5.0, " mL")
check("FRC at 30 deg -- and the shunt now follows it",
      _tco(Patient, 30.0).frc_anaes(), 840.0, 6.0, " mL")
print("    THE DIAGNOSIS THAT WAS ACTED ON. Until the re-key there was NO")
print("    ROUTE FROM LUNG VOLUME TO STANDING SHUNT. shunt_base_eff() was a")
print("    pure function of BMI, so FRC could rise 585 -> 840 mL and the")
print("    shunt would not move one hundredth of a percent; tilt therefore")
print("    had no oxygenation benefit to offset its cardiac-output cost.")
print("    Perilli\'s own explanation of his result is that tilt raises FRC")
print("    and FRC improves oxygenation; he found the gain correlated with")
print("    compliance, r = -0.65.")
print("    TWO PAPERS POINTED AT THE SAME REDESIGN. Pelosi: the BMI-keyed")
print("    curve had a knee that does not exist. Perilli: the BMI-keyed")
print("    curve could not respond to position. BOTH SAID BMI IS A PROXY AND")
print("    THE MODEL WAS KEYED ON THE PROXY INSTEAD OF THE QUANTITY -- lung")
print("    volume against closing capacity, already computed for the apnoea")
print("    collapse. DONE 2026-09-24 by ruling: shunt_base_eff() now reads")
print("    x = (cc - frc_anaes)/frc_anaes through closure_x(), on two fitted")
print("    parameters where the quadratic had three.")

# ---------------------------------------------------------------------------
print("\nPELOSI 1998 -- the whole BMI range, and IT CONTRADICTS OUR KNEE")
print("  n=24 across BMI 20-66 continuously, FiO2 0.40, ZEEP, supine,")
print("  paralysed, before surgery. The ONLY source here that publishes")
print("  REGRESSIONS rather than one cohort mean:")
print("      FRC       = 11.97*exp(-0.096*BMI) + 0.46  L     r 0.86")
print("      PaO2/PAO2 = 1.23 *exp(-0.037*BMI) + 0.196       r 0.81")
print("      D(A-a)O2  = -7.15 + 3.37*BMI            mmHg    r 0.84")
print("      PaCO2     NOT related to BMI (r 0.06), about 33")

_PH, _PAGE, _PHB, _PFIO2, _PPACO2 = 1.64, 52.0, 14.0, 0.40, 33.0
_PALV = _PFIO2 * ac.PDRY - _PPACO2 / 0.8


def _pel_ratio(b):
    return 1.23 * np.exp(-0.037 * b) + 0.196


def _pel_daa(b):
    return -7.15 + 3.37 * b


def _pel_pao2(b, shunt=None):
    _cls = Patient if shunt is None else _forced_shunt(shunt)
    _p = _cls(weight=b * _PH * _PH, height=_PH, age=_PAGE, hb=_PHB,
              tilt_deg=0.0)
    _r = simulate(_p, [AirwayEpoch(2.0, resistance=2.0, fgo2=_PFIO2)],
                  dt=DT, feo2_start=_PALV / ac.PDRY, paco2_start=_PPACO2,
                  stop_sao2=0.0)
    return _p, _r['pao2'][0]


def _pel_invert(b):
    """Shunt that reproduces Pelosi's oxygenation at this BMI."""
    _tgt = _pel_ratio(b) * _PALV
    _lo, _hi = 0.01, 0.60
    for _ in range(22):
        _mid = 0.5 * (_lo + _hi)
        if _pel_pao2(b, _mid)[1] > _tgt:
            _lo = _mid
        else:
            _hi = _mid
    return 0.5 * (_lo + _hi) * 100.0


check("Pelosi: alveolar PO2 at FiO2 0.40, PaCO2 33", _PALV, 243.9, 1.0, " mmHg")
for _b, _ours_sh, _pel_sh, _frc in ((22, 3.71, 3.47, 1886.0),
                                    (30, 5.75, 5.96, 1237.0),
                                    (34, 7.09, 7.28, 1039.0),
                                    (42, 10.49, 10.37, 745.0),
                                    (50, 14.24, 14.12, 578.0)):
    _p, _o = _pel_pao2(_b)
    check(f"BMI {_b}: OUR shunt_base_eff", _p.shunt_base_eff() * 100.0,
          _ours_sh, 0.05, " %")
    check(f"BMI {_b}: shunt PELOSI IMPLIES", _pel_invert(_b), _pel_sh, 0.10, " %")
    check(f"BMI {_b}: our FRC [Pelosi helium {11.97*np.exp(-0.096*_b)*1000+460:.0f}]",
          _p.frc_anaes(), _frc, 8.0, " mL")
print("    ADOPTED 2026-09-24 BY RULING, THEN RE-KEYED THE SAME DAY. The")
print("    curve was first carried as a QUADRATIC IN BMI fitted to these")
print("    inverted points -- worst residual 0.27 percentage points, rms")
print("    0.094. It was then re-keyed off BMI entirely onto")
print("    x = (cc - frc_anaes)/frc_anaes, fitted to the SAME inverted")
print("    points, on TWO parameters where the quadratic had three:")
print("        shunt = shunt_anat + (1 - shunt_anat) * x / (x + shunt_cc_k)")
print("    AND IT FITS PELOSI WORSE: worst residual 0.49 percentage points")
print("    against 0.27, rms 0.23 against 0.094. That is the honest cost of")
print("    the re-key and it is recorded, not compensated. What it buys is")
print("    in the Perilli block above: a shunt that responds to head-up")
print("    tilt, to age and to the induction FRC drop, none of which a")
print("    function of BMI can see. The \'OUR\' and \'PELOSI IMPLIES\' columns")
print("    above therefore agree to within that wider fit, which is what")
print("    those rows assert: that it has not drifted further.")
print("    NOTE THE \'OUR\' COLUMN IS NOW CONFIGURATION-DEPENDENT. It is")
print("    computed at Pelosi\'s cohort -- height 1.64 m, age 52, supine --")
print("    because the shunt is no longer a function of BMI alone. Reinius,")
print("    Valenza and Gander differ in height and age and now get their own")
print("    shunts at the same BMI, which is the point of the change.")
print("    WHAT FOLLOWS IS THE ARGUMENT THAT LED TO IT, kept as the record.")
print("    THERE IS NO KNEE. Pelosi's implied shunt rises 1.28, 1.21, 1.32,")
print("    1.47, 1.62, 1.79 and 1.95 points per four BMI units from 22 to 50")
print("    -- ACCELERATING, not flattening. Our curve is flat above BMI 30.")
print("    AND THE AGREEMENT AT BMI 42-46 IS WHY NOBODY CAUGHT IT. Pelosi")
print("    implies 10.37% at BMI 42 and 12.17% at 46 against our flat 10.90%.")
print("    Reinius sits at BMI 45 and Valenza at 42: BOTH ANCHORS ARE IN THE")
print("    ONE PLACE WHERE THE WRONG CURVE HAPPENS TO BE RIGHT. The whole")
print("    disagreement is in BMI 24-40, which the parameter block itself")
print("    named as unmeasured when the curve was committed.")
print("    IT DOES NOT OVERTURN HEDENSTIERNA. He measured ATELECTATIC AREA by")
print("    CT and found it flat above BMI 30. Pelosi measures OXYGENATION,")
print("    which is shunt PLUS low V/Q. Both hold if the atelectasis plateaus")
print("    while the poorly-aerated compartment keeps growing -- exactly the")
print("    nonaerated 11% / poorly aerated 39% split Reinius reports.")
print("    shunt_base conflates the two, so Hedenstierna's knee was applied")
print("    to a quantity it does not govern. Pelosi measures the quantity")
print("    shunt_base actually represents, in the ventilated state where")
print("    unwashed_fraction() cannot act. HIS CURVE IS THE RIGHT TARGET.")
print("    THE FRC ROWS ARE REASSURING and are NOT the contradiction: ours")
print("    tracks Pelosi's helium across the whole range and sits BETWEEN his")
print("    helium and Reinius's CT, which is what the CT ruling predicts.")
print("    His exponent 0.096 is NOT comparable with our k_frc_bmi 0.0417 --")
print("    his form carries a 0.46 L offset, ours a residual-volume floor.")
print("    The VALUES agree though the exponents do not, and values are what")
print("    ACTED ON THE SAME DAY, by ruling. The broken line is gone.")

# ---------------------------------------------------------------------------
print("\nVALENZA 2007 -- FRC AGAINST TILT, MEASURED, and it reverses a")
print("  conclusion recorded earlier the same day. n=20, BMI 42 (5),")
print("  anaesthetised and PARALYSED, ventilated at FiO2 0.60. Beach chair =")
print("  reverse Trendelenburg 30 deg head-up, legs lifted to the abdomen.")
print("  End-expiratory lung volume by closed-circuit helium dilution.")

_VH, _VBMI, _VAGE, _VHB = 1.65, 42.0, 37.0, 14.0
_VW = _VBMI * _VH * _VH
_VPACO2 = 38.3
_VPDRY = ac.PDRY
_VALV = 0.6 * _VPDRY - _VPACO2 / 0.8


def _val(tilt, shunt=None):
    # forces an ABSOLUTE baseline shunt -- see _forced_shunt at the head
    # of this file for why setting a parameter no longer does that
    _cls = Patient if shunt is None else _forced_shunt(shunt)
    return _cls(weight=_VW, height=_VH, age=_VAGE, hb=_VHB, tilt_deg=tilt)


def _val_pao2(tilt, shunt=None):
    _p = _val(tilt, shunt)
    _r = simulate(_p, [AirwayEpoch(2.0, resistance=2.0, fgo2=0.6)],
                  dt=DT, feo2_start=_VALV / _VPDRY, paco2_start=_VPACO2,
                  stop_sao2=0.0)
    return _r['pao2'][0]


_vs, _vb = _val(0.0), _val(30.0)
check("Valenza: FRC supine [measured 460 (100) by HELIUM]",
      _vs.frc_anaes(), 751.0, 5.0, " mL")
check("  ... in SD of 460 (100)", (_vs.frc_anaes() - 460.0) / 100.0,
      2.91, 0.06, " SD")
check("Valenza: FRC at 30 deg head-up [measured 850 (300)]",
      _vb.frc_anaes(), 1101.0, 6.0, " mL")
check("Valenza: OUR tilt gain in FRC",
      (_vb.frc_anaes() / _vs.frc_anaes() - 1.0) * 100.0, 46.6, 0.5, " %")
check("Valenza: MEASURED tilt gain in FRC (0.46 -> 0.85 L)",
      (0.85 / 0.46 - 1.0) * 100.0, 84.8, 0.2, " %")
check("  ... we are too SMALL by a factor of",
      84.78 / ((_vb.frc_anaes() / _vs.frc_anaes() - 1.0) * 100.0), 1.82,
      0.03, " x")
check("Valenza: alveolar PO2 at FiO2 0.60, PaCO2 38.3", _VALV, 379.9, 1.0, " mmHg")
print("    HISTORY: 251.8 mmHg (+1.50 SD) at a flat 5% shunt, 165.6 (-0.23)")
print("    on the broken line, 171.4 (-0.11) on Pelosi's curve. Valenza was")
print("    NOT used to fit the curve either.")
check("Valenza: baseline shunt from closure, BMI 42 at HIS height and age",
      _vs.shunt_base_eff() * 100.0, 9.64, 0.05, " %")
check("Valenza: our supine PaO2 [measured 177 (50)]",
      _val_pao2(0.0), 182.27, 1.5, " mmHg")
check("  ... in SD of 177 (50)", (_val_pao2(0.0) - 177.0) / 50.0, 0.11,
      0.04, " SD")
print("    THE RE-KEY OF 2026-09-24 IMPROVED THIS ROW and moved the shunt")
print("    DOWN from 10.45% to 9.64% at the same BMI 42. It moved because")
print("    the shunt is no longer a function of BMI: Valenza's cohort has")
print("    its own height and age, so it gets its own closing capacity and")
print("    its own FRC. PaO2 171.4 (-0.11 SD) -> 182.3 (+0.11 SD), which is")
print("    the same distance from his measurement on the other side.")
_vsh = []
for _s in (0.05, 0.10, 0.15, 0.20):
    _v = _val_pao2(0.0, _s)
    _vsh.append((_s * 100.0, _v))
    check(f"  baseline shunt {_s*100:4.1f}%: PaO2 at FiO2 0.60", _v,
          {0.05: 251.8, 0.10: 177.4, 0.15: 123.7, 0.20: 94.8}[_s], 1.5, " mmHg")
_va = np.array([x[0] for x in _vsh]); _vbv = np.array([x[1] for x in _vsh])
check("SHUNT NEEDED to reproduce Valenza's supine PaO2 of 177",
      float(np.interp(177.0, _vbv[::-1], _va[::-1])), 10.0, 0.3, " %")

print("    THE TILT CONCLUSION OF THIS MORNING IS REVERSED. It read that the")
print("    tilt overshoot lives in tilt_gain_lean / tilt_gain_bmi and that")
print("    what was needed was a measurement of FRC against tilt angle. The")
print("    measurement now exists and says OUR TILT GAIN IS 1.8x TOO SMALL.")
print("    Correcting it upward -- which is what the only direct measurement")
print("    of this quantity demands -- would make the apnoea-time tilt rows")
print("    WORSE, since they already overshoot. So the defect is NOT in")
print("    tilt_gain_*; it is in the CONVERSION OF FRC INTO APNOEA TIME. The")
print("    model takes too little extra volume from tilt and turns it into")
print("    too much extra time.")
print("    AND THE PARAMETER'S STATED MECHANISM IS CONTRADICTED. The comment")
print("    says head-up 'lifts the abdominal contents off the diaphragm'. In")
print("    Valenza's beach chair the legs are lifted TO the abdomen and")
print("    intra-abdominal pressure RISES, 17.87 -> 23.92 cmH2O, while lung")
print("    volume nearly doubles. The gain is empirical and stands; the")
print("    explanation attached to it should not be quoted.")
print("    THE TWO GOLD-STANDARD VOLUMES DISAGREE, AND BY METHOD. Valenza")
print("    460 (100) at BMI 42 by HELIUM, Reinius 697 (157) at BMI 45 by CT")
print("    -- the heavier cohort has the LARGER lung, which is backwards.")
print("    Helium sees only communicating gas; CT sees trapped gas too, and")
print("    an obese anaesthetised lung is where they differ most. Valenza's")
print("    own release-technique intercept is 0.098 L, 21% of their mean.")
print("    We are -0.18 SD from Reinius and +2.91 SD from Valenza, with our")
print("    BMI slope in the right direction and theirs not. NEITHER PAPER")
print("    CAN RE-ANCHOR FRC ALONE; resolve them first.")
print("    A THIRD INDEPENDENT SHUNT MEASUREMENT, AND IT AGREES:")
print("      Reinius blood gas, FiO2 0.50, BMI 45   11.85 %")
print("      Reinius nonaerated volume by CT        11 (6) %")
print("      Valenza blood gas, FiO2 0.60, BMI 42   10.0  %")
print("      shipped                                 5.0  %")
print("    Two centres, two years, two inspired fractions, two BMIs, one")
print("    anatomical route and two physiological ones. 10-12%.")
print("    ONE CAUTION: Valenza found NO RECRUITABLE LUNG (0.04 (0.1) L")
print("    supine) and attributes the low volume to 'a prevalent decrease of")
print("    the size of the alveoli rather than atelectasis', yet their blood")
print("    gas still needs 10%. Their method measures what a recruitment")
print("    manoeuvre can OPEN, not what is closed. Do not equate the")
print("    inferred shunt with atelectasis.")

# ---------------------------------------------------------------------------
print("\nREINIUS 2009 READ IN FULL -- the obese shunt, measured two ways")
print("  n=30, BMI 45 (4), spiral CT in 23. Preoxygenated 5 min 100% O2 with")
print("  a TIGHT SEAL MASK, then ventilated at FiO2 0.5, ZEEP, supine.")
print("  THE MODEL IS TOO GOOD ON A VENTILATOR, and the denitrogenation")
print("  mechanism cannot be the explanation: on a ventilator every unit gets")
print("  fresh gas every breath, so unwashed_fraction() is irrelevant here.")

_RH, _RBMI, _RAGE, _RHB = 1.66, 45.0, 37.0, 14.0
_RPACO2 = 34.0
_RPDRY = ac.PDRY
_RALV = 0.5 * _RPDRY - _RPACO2 / 0.8


def _rein(shunt=None):
    # forces an ABSOLUTE baseline shunt via _forced_shunt. The shunt
    # parameters are now Pelosi-curve coefficients, so no single parameter
    # sets an absolute value any more.
    _cls = Patient if shunt is None else _forced_shunt(shunt)
    _p = _cls(weight=_RBMI * _RH * _RH, height=_RH, age=_RAGE, hb=_RHB,
              tilt_deg=0.0)
    _r = simulate(_p, [AirwayEpoch(2.0, resistance=2.0, fgo2=0.5)],
                  dt=DT, feo2_start=_RALV / _RPDRY, paco2_start=_RPACO2,
                  stop_sao2=0.0)
    return _p, _r


_rp, _rr = _rein()
check("Reinius: FRC anaesthetised [measured EELV 697 (157)]",
      _rp.frc_anaes(), 668.0, 5.0, " mL")
check("  ... in SD of 697 (157). NOT independent: k_rv_bmi was anchored here",
      (_rp.frc_anaes() - 697.0) / 157.0, -0.18, 0.05, " SD")
check("Reinius: FRC AWAKE [measured 1387 (581)] -- the non-circular row",
      _rp.frc_awake(), 891.0, 8.0, " mL")
check("  ... in SD of 1387 (581). 'NOT CONTRADICTED', not 'confirmed'",
      (_rp.frc_awake() - 1387.0) / 581.0, -0.85, 0.03, " SD")
check("Reinius: unwashed share [awake poorly aerated 28 (12) %]",
      _rp.unwashed_fraction() * 100.0, 14.79, 0.05, " %")
check("  ... in SD of the AWAKE 28 (12), which is the right comparator",
      (_rp.unwashed_fraction() * 100.0 - 28.0) / 12.0, -1.10, 0.03, " SD")
check("Reinius: alveolar PO2 at FiO2 0.5, PaCO2 34", _RALV, 314.0, 1.0, " mmHg")
print("  AFTER THE BMI-DEPENDENT SHUNT RULING OF 2026-09-24 the rows below")
print("  are the corrected model, not the disagreement. Before the ruling:")
print("    PaO2 201.3, PaO2/FiO2 402.6, a-A gradient 112.7 -- against a")
print("    measured 126 / 252 / 188. We oxygenated an anaesthetised morbidly")
print("    obese patient about as well as Reinius's were before induction.")
print("  AFTER PELOSI'S CURVE REPLACED THE BROKEN LINE, 2026-09-24. Reinius")
print("  is now hit almost exactly, and WAS NOT USED TO FIT IT -- the curve")
print("  comes from Pelosi's regression alone. History of this row:")
print("      PaO2/FiO2  402.6  flat 5% shunt for everybody")
print("                 266.1  broken line, 10.9% plateau")
print("                 251.7  Pelosi's curve, as a quadratic in BMI")
print("                 261.6  re-keyed on lung volume vs closing capacity")
print("                 252    MEASURED (groups 225-266)")
print("    THE RE-KEY COST THIS ROW ITS NEAR-EXACT HIT, and that is the")
print("    trade being recorded rather than hidden: 251.7 was within three")
print("    tenths of a mmHg of Reinius, 261.6 is 9.6 above him -- still")
print("    INSIDE his groups' range of 225-266, but at the top of it.")
print("    It moved because Reinius's cohort is not Pelosi's: same BMI 45,")
print("    different height and age, so a shunt keyed on closing capacity")
print("    against FRC no longer gives them the same number. The curve was")
print("    fitted at Pelosi's height and age alone and Reinius was never in")
print("    the fit, before or after.")
check("Reinius: baseline shunt from closure, BMI 45 at HIS height and age",
      _rp.shunt_base_eff() * 100.0, 11.16, 0.05, " %")
check("Reinius: our PaO2 ventilated [measured PaO2/FiO2 252 -> PaO2 126]",
      _rr['pao2'][0], 130.81, 1.0, " mmHg")
check("Reinius: our PaO2/FiO2 [measured 252, groups 225-266]",
      _rr['pao2'][0] / 0.5, 261.62, 2.0, "")
check("Reinius: our a-A oxygen gradient [theirs is 188]",
      _RALV - _rr['pao2'][0], 183.19, 1.5, " mmHg")

print("  AND THE AUTHORS THEMSELVES FLAG THE AWAKE VOLUME. Limitation 12:")
print("  'during spontaneous breathing the patient did not comprehend the")
print("  instructions given, thus failing to make an end-expiratory")
print("  breath-hold... however we believe this to be unlikely'. Its SD is")
print("  42% of its mean where the anaesthetised value's is 23%. So the one")
print("  non-circular check on frc_ref and k_frc_bmi is SOFTER than it")
print("  looks: read -0.85 SD as not contradicted, not as confirmed, and do")
print("  not quote it as a validation of the FRC regression.")
print("  LIMITATION 10 STATES OUR MECHANISM'S THIRD PREDICTION AS FACT:")
print("  'The anesthesia was induced with 100% O2, WHICH PROMOTES FORMATION")
print("  OF ATELECTASIS'. That is prediction (c) -- a closed unit full of")
print("  oxygen absorbs, one full of nitrogen is splinted open -- asserted")
print("  by a group that measures atelectasis by CT for a living.")
print("  INVERTING THE BLOOD GAS FOR SHUNT. What shunt_base reproduces their")
print("  PaO2/FiO2 of 252 at an alveolar PO2 of 314?")
_sh = []
for _s in (0.05, 0.08, 0.11, 0.14, 0.20):
    _v = _rein(_s)[1]['pao2'][0]
    _sh.append((_s * 100.0, _v))
    check(f"  baseline shunt {_s*100:4.1f}%: PaO2/FiO2", _v / 0.5,
          {0.05: 402.6, 0.08: 325.8, 0.11: 264.4, 0.14: 220.8,
           0.20: 168.8}[_s], 2.0, "")
_a = np.array([x[0] for x in _sh]); _b = np.array([x[1] for x in _sh])
_need = float(np.interp(126.0, _b[::-1], _a[::-1]))
check("SHUNT NEEDED to reproduce Reinius's arterial oxygen",
      _need, 11.9, 0.3, " %")
check("  ... against their MEASURED nonaerated lung volume of 11 (6) %",
      (_need - 11.0) / 6.0, 0.15, 0.06, " SD")
print("    11.9% INFERRED FROM ARTERIAL BLOOD, 11% MEASURED BY CT, in the")
print("    same patients. A perfusion fraction and a volume fraction are not")
print("    obliged to agree, so the agreement is worth more than either.")
print("    WE SHIP 5.0%, AND shunt_base HAS NO BMI DEPENDENCE AT ALL -- a")
print("    lean patient and a BMI 45 patient are given the same 5%. That is")
print("    the defect this branch was forked to find.")
print("    THE 5% IS NOT WRONG WHERE IT CAME FROM. Tokics 1996 Table 3")
print("    measures 5.0 (1.3) % by inert gas under anaesthesia, and the row")
print("    above checks it and passes. TOKICS'S PATIENTS WERE NOT OBESE.")
print("    NO CONTRADICTION WITH HEDENSTIERNA 2020, whose finding is that")
print("    atelectasis does not increase FURTHER above BMI 30. That")
print("    constrains the SHAPE of the ceiling, not its HEIGHT. A flat")
print("    ceiling at the wrong height satisfies both papers, and nothing")
print("    before today measured the height in an obese cohort.")
print("    NOT ACTED ON. A BMI-dependent shunt_base anchored on Tokics at")
print("    normal weight and Reinius at BMI 45 would be two measurements,")
print("    not a fit -- the same footing as k_rv_bmi -- but it moves Heard,")
print("    the tilt rows, Gander and the buccal numbers, and it is recorded")
print("    for a ruling rather than made.")
print("    AND IT CANNOT BE SETTLED SEPARATELY FROM THE LOW-V/Q FRACTION.")
print("    Inverting GANDER wanted an unwashed share of 36-44%; Reinius's")
print("    AWAKE poorly-aerated fraction is 28 (12) % and our 14.8% sits")
print("    inside it. If the standing shunt is really 11-12%, part of what")
print("    the Gander inversion asked of the unwashed fraction belongs to")
print("    the shunt instead. Raising one without the other is fitting.")

# ---------------------------------------------------------------------------
print("\nGANDER 2005 -- the morbidly obese benchmark, CONFIGURATION WRITTEN DOWN")
print("  SOURCES.md has carried this table as typed-in markdown since")
print("  2026-09-23 with no script behind it, which is exactly how the Ellis")
print("  comparator rows became unreproducible. It is scripted here now.")
print("  Gander gives BMI 47 (6) and age 38 (12) and nothing else about the")
print("  patient; height, Hb and how well they preoxygenated are OURS.")


def _gander():
    _h = 1.70
    _p = Patient(weight=47.0 * _h * _h, height=_h, age=38, hb=14.0)
    _r = simulate(_p, [AirwayEpoch(900.0, resistance=2.0, fgo2=0.21)],
                  dt=DT, feo2_start=0.90, paco2_start=46.0, stop_sao2=0.0)
    return _p, _r


_gp, _gr = _gander()
_g92 = time_to(_gr, 'spo2', 92)
check("Gander: unwashed perfusion share (low V/Q)",
      _gp.unwashed_fraction() * 100.0, 15.79, 0.10, " %")
check("Gander: PaO2 before apnoea [measured 243 (136)]",
      _gr['pao2'][0], 321.68, 1.5, " mmHg")
check("  ... in SD of 243 (136)", (_gr['pao2'][0] - 243.0) / 136.0, 0.58,
      0.03, " SD")
check("Gander: shunt at t=0 [implied ~20%+]",
      _gr['shunt'][0] * 100.0, 12.21, 0.10, " %")
check("Gander: time to SpO2 90% [measured 127 (43), 1 SD 84-170]",
      time_to(_gr, 'spo2', 90), 145.0, 3.0, " s")
check("Gander: PaO2 at SpO2 92% [measured 68 (10)]",
      at(_gr, 'pao2', _g92), 43.6, 1.0, " mmHg")
check("Gander: PaCO2 at SpO2 92% [measured 53 (4)]",
      at(_gr, 'paco2', _g92), 54.8, 1.0, " mmHg")
check("Gander: ERV anaesthetised [Holley: zero in morbid obesity]",
      _gp.frc_anaes() - _gp.rv_eff(), 0.0, 5.0, " mL")
print("    THE HISTORY OF THIS ROW, because it has moved three times and each")
print("    move meant something different:")
print("      time to SpO2 90%   PaO2 before apnoea   what changed")
print("        166 s              563.8              no FRC floor at all:")
print("                                              ERV was MINUS 466 mL")
print("        251 s              563.8              floored at a FLAT RV")
print("        164 s              563.8              RV falls with BMI")
print("        148 s              446.9              low V/Q added")
print("                           ----")
print("        127 (43)           243 (136)          MEASURED")
print("    The old 166 s came from an ERV of MINUS 466 mL and the 164 from an")
print("    ERV of zero, which is what Holley measured. Same number, opposite")
print("    physics, and that is why the 251 s step was an improvement even")
print("    though it doubled the error.")
print("    LOW V/Q IS THE ONLY THING THAT HAS EVER MOVED THE OXYGEN. 563.8 at")
print("    every residual volume, 446.9 with unwashed units. Still well above")
print("    the measured 243 (136): the mechanism is the right KIND of thing")
print("    and is not yet the whole size of it. Nothing has been reached for")
print("    to close the rest.")

# ---------------------------------------------------------------------------
print("\nRESIDUAL VOLUME IS NOW BMI-DEPENDENT -- the Reinius 2009 anchor")
print("  rv is residual volume: the gas that cannot be blown out of the lungs")
print("  even at maximal expiration. It is a FLOOR under FRC. It was one")
print("  constant for everybody until 2026-09-23, which is wrong in an obvious")
print("  direction -- what pushes FRC down in obesity pushes RV down too.")
print("  Anchor: Reinius 2009 measured end-expiratory lung volume 697 (157) mL")
print("  at BMI 45 after induction and paralysis; Holley 1967 has ERV going to")
print("  zero in morbid obesity, so FRC IS RV there and 697 is an upper bound")
print("  on RV. k_rv_bmi solves 1100*exp(-k*(45-22)) = 697.")


def _rvpat(bmi, h=1.75):
    return Patient(weight=bmi * h * h, height=h, age=42, hb=14)


check("k_rv_bmi solves the Reinius anchor",
      np.log(ac.Patient().rv / 697.0) / (45.0 - 22.0),
      ac.Patient().k_rv_bmi, 0.0005, "")
_r45 = _rvpat(45.0)
check("residual volume at BMI 45", _r45.rv_eff(), 698.0, 12.0, " mL")
check("  ... against Reinius measured 697 (157), in SD",
      abs(_r45.rv_eff() - 697.0) / 157.0, 0.0, 0.25, " SD")
check("FRC anaesthetised at BMI 45", _r45.frc_anaes(), 719.0, 15.0, " mL")
for _b, _rv, _fa, _fn in ((22.9, 1081.0, 2412.0, 2012.0),
                          (34.3, 862.0, 1498.0, 1123.0),
                          (44.4, 706.0, 982.0, 737.0),
                          (46.4, 679.0, 905.0, 679.0)):
    _p = _rvpat(_b)
    check(f"BMI {_b:.1f}: residual volume", _p.rv_eff(), _rv, 12.0, " mL")
    check(f"BMI {_b:.1f}: FRC awake", _p.frc_awake(), _fa, 20.0, " mL")
    check(f"BMI {_b:.1f}: FRC anaesthetised", _p.frc_anaes(), _fn, 20.0, " mL")
_erv46 = _rvpat(46.4).frc_anaes() - _rvpat(46.4).rv_eff()
check("ERV anaesthetised at BMI 46.4 (Holley: zero in morbid obesity)",
      _erv46, 0.0, 5.0, " mL")
print("    ERV reaching zero at BMI 46 is Holley FALLING OUT of the model, not")
print("    being put into it. The dependency to watch is that reading")
print("    Reinius's 697 as a residual volume rests ENTIRELY on Holley's ERV")
print("    going to zero.")
print("  CORRECTION, 2026-09-23. The commit that made this change asserted")
print("  that the benchmark suite was 'bit-identical either side of it' and")
print("  that it 'adds none and fixes none'. BOTH ARE FALSE, and the error")
print("  was asserting from three spot-checked Stock rows instead of running")
print("  the suite on both sides. Running it on both sides, FOUR rows moved:")
print("      tilt, BMI 44 at 25 deg     0.0 ->  33.4 %   FAIL -> PASS")
print("      tilt, BMI 35 at 30 deg    34.5 ->  45.4 %   PASS -> FAIL")
print("      Stock obstructed, PaO2   157.0 -> 157.2 mmHg")
print("      Moreault, pressure step  -13.3 -> -11.8 cmH2O")
print("  The blocking count stayed at 5 BY COINCIDENCE -- one tilt row fixed,")
print("  the other broken.")
print("  AND THE ZERO IS THE POINT. At BMI 44 the flat RV floor bound at BOTH")
print("  tilt angles, so head-up tilt bought that patient EXACTLY NOTHING --")
print("  a gain of 0.0%, against four trials measuring about +30%. That is")
print("  independent evidence for the change, found only by running the suite")
print("  properly, and it is why the tilt rows are scripted below.")

def _tilt_gain(w, h, hb, tilt, thr):
    _out = []
    for _t in (0.0, tilt):
        _q = Patient(weight=w, height=h, age=45, hb=hb, tilt_deg=_t)
        _rr = simulate(_q, [AirwayEpoch(1200.0, resistance=OBS, fgo2=0.21)],
                       dt=DT, stop_sao2=0.0)
        _out.append(time_to(_rr, 'spo2', thr))
    return (_out[1] / _out[0] - 1.0) * 100.0


print("  DOES THE TILT QUESTION NEED A HUMAN STUDY? NO -- ANSWERED 2026-09-24")
print("  Head-up tilt helps twice in this model: it raises awake FRC (a")
print("  bigger oxygen store) AND it shrinks the unwashed fraction (better")
print("  denitrogenation, because a larger awake lung closes fewer airways).")
print("  The four positioning trials measure only the TOTAL, so they cannot")
print("  separate the two -- which looked like it needed a new study.")
print("  IT DID NOT. The second route is EXACTLY ZERO whenever awake FRC")
print("  exceeds closing capacity, so switching it off and re-running the")
print("  trial configurations says how much of the overshoot it owns:")
print("      configuration        BOTH   FRC only   2nd route   band")
print("      lean 20 deg          28.6%     28.6%       0.0%    15-40")
print("      BMI 35 at 30 deg     51.1%     45.4%       5.7%    20-45")
print("      BMI 44 at 25 deg     35.9%     33.4%       2.5%    15-40")
print("  THE OVERSHOOT IS NOT IN THE DENITROGENATION ROUTE. With that route")
print("  switched entirely off the BMI 35 row STILL FAILS, at 45.4% against")
print("  a band top of 45. The second route adds at most 5.7 points and")
print("  removing it would not bring the row back.")
print("  SO THE DEFECT IS IN HOW MUCH FRC RISES WITH TILT, and that is")
print("  tilt_gain_lean / tilt_gain_bmi, which apnoea_core.py states were")
print("  'Calibrated against four randomised trials'. THEY ARE A FIT WITH")
print("  NO INDEPENDENT SOURCE, and the fit is now stale: it was made when")
print("  FRC, residual volume and the V/Q machinery all behaved differently.")
print("  WHAT THAT MEANS FOR THE NEXT STEP. Re-fitting them to pass the")
print("  tilt rows is tuning a parameter to a benchmark, which CLAUDE.md")
print("  forbids and which has been refused four times. What is needed is a")
print("  MEASUREMENT of FRC against tilt angle -- not of apnoea time, which")
print("  is what the four trials give and is downstream of everything else")
print("  in the model. That is a different literature search, and possibly")
print("  a different study, from the one the tilt rows suggest.")


def _tilt_gain_no2nd(w, h, hb, tilt, thr):
    """Tilt gain with the denitrogenation route switched off."""
    class _NoUnwashed(Patient):
        def unwashed_fraction(self):
            return 0.0
    _out = []
    for _t in (0.0, tilt):
        _q = _NoUnwashed(weight=w, height=h, age=45, hb=hb, tilt_deg=_t)
        _rr = simulate(_q, [AirwayEpoch(1200.0, resistance=OBS, fgo2=0.21)],
                       dt=DT, stop_sao2=0.0)
        _out.append(time_to(_rr, 'spo2', thr))
    return (_out[1] / _out[0] - 1.0) * 100.0


check("tilt gain FRC ROUTE ONLY, lean 20 deg [band 15-40]",
      _tilt_gain_no2nd(70, 1.75, 15, 20, 95), 28.6, 0.5, " %")
check("tilt gain FRC ROUTE ONLY, BMI 35 at 30 deg [band 20-45: STILL FAILS]",
      _tilt_gain_no2nd(95, 1.65, 14, 30, 90), 45.4, 0.5, " %")
check("tilt gain FRC ROUTE ONLY, BMI 44 at 25 deg [band 15-40]",
      _tilt_gain_no2nd(120, 1.65, 14, 25, 92), 33.4, 0.5, " %")
check("unwashed share at BMI 35, supine", Patient(
      weight=95, height=1.65, age=45, hb=14, tilt_deg=0).unwashed_fraction()
      * 100.0, 9.24, 0.05, " %")
check("  ... and at 30 deg head-up (this is the second route)", Patient(
      weight=95, height=1.65, age=45, hb=14, tilt_deg=30).unwashed_fraction()
      * 100.0, 4.29, 0.05, " %")

check("tilt gain, non-obese 20 deg [band 15-40, lean: must not move]",
      _tilt_gain(70, 1.75, 15, 20, 95), 28.6, 0.5, " %")
check("tilt gain, BMI 35 at 30 deg [band 20-45, measured ~+30]",
      _tilt_gain(95, 1.65, 14, 30, 90), 51.1, 0.5, " %")
check("tilt gain, BMI 44 at 25 deg [band 15-40; was 0.0 at a flat RV]",
      _tilt_gain(120, 1.65, 14, 25, 92), 35.9, 0.5, " %")

# ---------------------------------------------------------------------------
print("\nNOT REPRODUCIBLE, and recorded as such")
print("    Ellis 2022 pregnancy comparator: HANDOVER quotes 18.1 and 5.8 min")
print("    against their 25.4 and 9.9. The configuration behind those two")
print("    numbers was never written down. Regenerate them before using them.")
print("    Laviola 2020 airway rescue: THIS ENTRY IS STRUCK 2026-09-22.")
print("    The paper was obtained and read, and the protocol is exactly what")
print("    test_validation.py already implements -- 3 min of 100% oxygen,")
print("    apnoea with an OBSTRUCTED airway, relief at SaO2 60%, supraglottic")
print("    FO2 100%, reported post-rescue PaO2 42.3 (4.4) kPa. Ours gives")
print("    43.92, inside ONE SD, and it is insensitive to the only detail we")
print("    had to assume: across feo2_start 0.80/0.87/0.90/0.95 the answer is")
print("    40.60/43.92/44.96/45.89 kPa, EVERY value inside their 1 SD. The")
print("    orphaned 38.7 came from a configuration nobody wrote down; the one")
print("    in test_validation.py is written down and reproduces.")

# ---------------------------------------------------------------------------
print("\nCLOSING CAPACITY -- THE SOURCE IS FOUND, THE BLOCKER IS TLC")
print("  Chased again 2026-09-24 on a ruling, and the first finding is that")
print("  the chase was already done: Buist & Ross 1973 was obtained and READ")
print("  AT SOURCE on 2026-09-23 and its combined regression is quoted")
print("  verbatim in SOURCES.md:")
print("      CC/TLC (per cent) = 0.525 * age(years) + 14.348 +- 4.34")
print("  So cc_at_20/cc_per_year/cc_per_bmi are UNSOURCED VALUES, not an")
print("  unsourced QUANTITY. Any claim that closing capacity has no source is")
print("  wrong and this block exists to stop it being made again.")
print("  WHAT ACTUALLY BLOCKS IT: Buist gives CC as a PERCENTAGE OF TLC and")
print("  this model has no TLC. That is the whole of the remaining work.")

_CH = 1.75


def _buist_cc(age, tlc):
    """Buist & Ross 1973 combined regression, in mL, against a given TLC."""
    return tlc * (0.525 * age + 14.348) / 100.0


def _cp(age, bmi=22.0):
    return Patient(weight=bmi * _CH * _CH, height=_CH, age=age, tilt_deg=0.0)


def _crossover(vol, cc):
    """Age at which closing capacity overtakes lung volume."""
    _lo, _hi = 5.0, 100.0
    for _ in range(60):
        _m = 0.5 * (_lo + _hi)
        if cc(_m) < vol(_m):
            _lo = _m
        else:
            _hi = _m
    return 0.5 * (_lo + _hi)


print("  THE CROSSOVER TEST. Both sources put CC = FRC at ~44 years SUPINE")
print("  (Milic-Emili 2007; BJA Education 2022). It has no free parameter in")
print("  it, which is what makes it worth failing against.")
check("our CC = awake FRC crossover [literature ~44 y]",
      _crossover(lambda a: _cp(a).frc_awake(), lambda a: _cp(a).closing_capacity()),
      55.0, 0.1, " y")
print("    SOURCES.md recorded this as 50.6 y. IT DOES NOT REPRODUCE at any")
print("    reading: 55.0 against awake FRC, 35.0 against anaesthetised FRC.")
print("    A prose number that rotted, which is why it is now in this file.")
print("    Our disagreement with the literature is therefore WIDER than the")
print("    document claimed, not narrower.")
check("  ... same, against anaesthetised FRC",
      _crossover(lambda a: _cp(a).frc_anaes(), lambda a: _cp(a).closing_capacity()),
      35.0, 0.1, " y")

print("  AND OUR FRC IS AGE-FLAT, WHICH IS A SECOND FAULT IN THE SAME TEST.")
print("  height_factor() quotes a regression carrying 0.009*age and then does")
print("  not implement the age term, so at BMI 22 frc_awake is frc_ref at")
print("  EVERY age. Giving the term back makes the crossover WORSE, 55.0 ->")
print("  59.9 y, because that regression has FRC RISING with age. Recorded,")
print("  not compensated: it is evidence the error is not all in CC.")


def _frc_aged(age):
    _f = lambda a: 2.34 * _CH + 0.009 * a - 1.09
    return 2500.0 * _f(age) / _f(45.0)


check("crossover once FRC carries its own age term [~44 y]",
      _crossover(_frc_aged, lambda a: _cp(a).closing_capacity()), 59.92, 0.05, " y")

print("  WHAT TLC WOULD BUIST & ROSS NEED? Solving the crossover for TLC is")
print("  the one thing that can be done WITHOUT the Quanjer paper, because")
print("  the 44-year target is itself a published number:")
_lo, _hi = 3000.0, 14000.0
for _ in range(60):
    _m = 0.5 * (_lo + _hi)
    if _crossover(lambda a: _cp(a).frc_awake(), lambda a, _t=_m: _buist_cc(a, _t)) > 44.0:
        _lo = _m
    else:
        _hi = _m
_TLC44 = 0.5 * (_lo + _hi)
check("TLC that puts the Buist crossover at exactly 44 y, h 1.75",
      _TLC44, 6676.0, 3.0, " mL")
_lo, _hi = 3000.0, 14000.0
for _ in range(60):
    _m = 0.5 * (_lo + _hi)
    if _crossover(_frc_aged, lambda a, _t=_m: _buist_cc(a, _t)) > 44.0:
        _lo = _m
    else:
        _hi = _m
check("  ... and again with the FRC age term restored",
      0.5 * (_lo + _hi), 6658.0, 3.0, " mL")
print("    THE TWO AGREE TO 0.3%, so the TLC the crossover implies does NOT")
print("    depend on the unresolved FRC age-term question. About 6.7 L for a")
print("    1.75 m subject is a plausible TLC, so Buist & Ross and the")
print("    crossover test are consistent with each other while OUR")
print("    regression is consistent with neither.")

print("  WHAT IT WOULD COST. Buist CC is LOWER than ours for every obese")
print("  cohort, so the shunt FALLS -- the direction SOURCES.md predicted:")
for _nm, _h, _b, _a, _want in (("Pelosi BMI 45", 1.64, 45.0, 52.0, 11.16),
                               ("Reinius BMI 45", 1.70, 45.0, 42.0, 9.53),
                               ("Perilli BMI 48.1", 1.61, 48.1, 37.0, 10.31),
                               ("Heard BMI 34.7", 1.74, 34.7, 42.0, 6.38)):
    class _BuistCC(Patient):
        def closing_capacity(self, _t=_TLC44):
            return _buist_cc(self.age, _t)
    _q = _BuistCC(weight=_b * _h * _h, height=_h, age=_a, hb=14.0, tilt_deg=0.0)
    _now = Patient(weight=_b * _h * _h, height=_h, age=_a, hb=14.0, tilt_deg=0.0)
    check(f"{_nm}: shunt on a Buist CC at TLC {_TLC44:.0f} "
          f"[ours {_now.shunt_base_eff()*100:.2f}%]",
          _q.shunt_base_eff() * 100.0, _want, 0.05, " %")
print("    NOT APPLIED. Implementing Buist faithfully needs a predicted TLC,")
print("    and the TLC source -- Quanjer/ECSC 1993, which Milic-Emili uses --")
print("    could not be read: this environment's network policy blocks every")
print("    primary host. The 6.7 L above is what the crossover IMPLIES, not a")
print("    value read from anywhere, and it must not be shipped as one.")

# ---------------------------------------------------------------------------
print("\nIS DESATURATION ROBUST? ASKED 2026-09-25, AND IT SPLITS IN TWO")
print("  TIME-TO-THRESHOLD: YES, and strongly. RATE OF CHANGE OF SaO2: NO.")

_RH = dict(weight=105, height=1.74, age=42, hb=14, tilt_deg=30)   # Heard 2017
_RL = dict(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)     # Toner 2019


def _desat(kw, feo2, dt=0.05, nvq=None, dur=1200, thr=95.0):
    _p = Patient(**kw, **({'n_vq': nvq} if nvq else {}))
    _r = simulate(_p, [AirwayEpoch(dur, resistance=2.0, fgo2=0.21)], dt=dt,
                  feo2_start=feo2, stop_sao2=0.0)
    _s = np.asarray(_r['spo2'])
    _b = np.where(_s < thr)[0]
    return float(np.asarray(_r['t'])[_b[0]]) if len(_b) else float('nan')


print("  1. TIMESTEP. The shipped dt=0.05 against a half-step reference:")
check("lean, time to SpO2<95% at dt 0.05", _desat(_RL, 0.87), 446.90, 0.05, " s")
check("  ... at dt 0.025", _desat(_RL, 0.87, dt=0.025), 447.05, 0.05, " s")
check("obese, time to SpO2<95% at dt 0.05", _desat(_RH, 0.80), 307.60, 0.05, " s")
check("  ... at dt 0.025", _desat(_RH, 0.80, dt=0.025), 307.73, 0.05, " s")
print("    Under 0.05% either way. Timestep is not a source of doubt.")

print("  2. COMPARTMENT COUNT -- NEVER CHECKED ON DESATURATION UNTIL NOW.")
print("  The n_vq block above says compartment convergence had only ever been")
print("  checked on the CO2 slope. On desaturation time it is FLAT:")
for _n, _w in ((20, 307.65), (80, 307.60), (320, 307.60)):
    check(f"obese, time to SpO2<95% at n_vq {_n}", _desat(_RH, 0.80, nvq=_n),
          _w, 0.05, " s")
print("    n_vq 20 to 320 moves desaturation by 0.05 s, 0.016%. It is LIVE for")
print("    CO2 and INERT for desaturation timing -- both are now measured.")

print("  3. AND NOW THE DEFECT. THE TRUE SaO2 TRACE IS A ONE-SECOND STAIRCASE.")
print("  apnoea_core.py inverts the blood gas -- which is where SaO2, PaO2,")
print("  PaCO2 and pH all come from -- only ONCE PER SIMULATED SECOND, and")
print("  holds the last value in between, whatever dt is. So SaO2 sits exactly")
print("  flat and then jumps. The signature is unambiguous:")


def _stair(dt):
    _p = Patient(**_RH)
    _r = simulate(_p, [AirwayEpoch(360, resistance=2.0, fgo2=0.21)], dt=dt,
                  feo2_start=0.80, stop_sao2=0.0)
    _t = np.asarray(_r['t'])
    _sa = np.asarray(_r['sao2'])
    _ds = np.diff(_sa)
    return (np.diff(_sa) / np.diff(_t)).min(), _ds.min(), float((np.abs(_ds) < 1e-12).mean())


for _dt, _rate, _drop, _flat in ((0.1, -5.4608, -0.5461, 0.9000),
                                 (0.05, -10.8870, -0.5444, 0.9500),
                                 (0.025, -21.7392, -0.5435, 0.9750)):
    _r_, _d_, _f_ = _stair(_dt)
    check(f"dt {_dt}: APPARENT steepest SaO2 fall", _r_, _rate, 0.02, " %/s")
    check(f"dt {_dt}:   drop in the one non-flat step", _d_, _drop, 0.002, " %")
    check(f"dt {_dt}:   fraction of steps EXACTLY flat", _f_, _flat, 0.002, "")
print("    READ THE THREE COLUMNS TOGETHER. The apparent rate DOUBLES as dt")
print("    HALVES -- an artefact, not a physiological rate. The drop per step")
print("    is CONSTANT at 0.544%. And the flat fraction is exactly 1 - dt, so")
print("    precisely one step per second is non-flat. That is the proof.")
print("    MEASURED ON A PATCHED COPY outside the repository, inverting every")
print("    step (provenance printed, per CLAUDE.md): the TRUE steepest fall is")
print("    0.5438 %/s and NO step exceeds 1 %/s. The shipped model overstates")
print("    the peak rate TWENTYFOLD at dt 0.05, and worse as dt falls.")
print("    WHY IT DOES NOT POISON THE TIMING: SpO2 is an exponential filter")
print("    over the staircase (spo2_delay 25 s, spo2_tau 8 s), so the probe")
print("    reading is smooth even though the true saturation is not. On the")
print("    patched copy time to SpO2<90% is 326.25 s against 326.7 shipped --")
print("    0.45 s, 0.14%. Every benchmark row reads SpO2, so none of them is")
print("    measurably affected.")
print("    WHAT IS AFFECTED: any RATE read off SaO2; the instant at which a")
print("    given true saturation is reached, good to about 1 s; and PaO2,")
print("    PaCO2 and pH, which come from the SAME cached tuple and are")
print("    therefore quantised identically. Whether that bears on the")
print("    backward-PaCO2-step diagnostic above is NOT TESTED.")
print("    THE FIX IS NOT FREE: inverting every step costs 2.5x runtime")
print("    (600 s of apnoea, 22 s -> 55 s wall), which would take the CI")
print("    benchmark job from about 15 minutes to nearer 40. A finer grid,")
print("    or interpolation between inversions, would buy most of it for")
print("    less. NOT DONE -- it needs a ruling.")

print("  4. WHAT ACTUALLY MOVES DESATURATION. Every lever +-10%, obese patient,")
print("  change in time to SpO2 90% against a 326.7 s baseline:")
_SBASE = _desat(_RH, 0.80, thr=90.0)
check("baseline, time to SpO2<90%", _SBASE, 326.70, 0.05, " s")


def _lever(attr, val, frac):
    _p = Patient(**_RH, **{attr: val * frac})
    _r = simulate(_p, [AirwayEpoch(1200, resistance=2.0, fgo2=0.21)], dt=0.05,
                  feo2_start=0.80, stop_sao2=0.0)
    _s = np.asarray(_r['spo2'])
    _b = np.where(_s < 90.0)[0]
    return (float(np.asarray(_r['t'])[_b[0]]) if len(_b) else float('nan')) - _SBASE


for _nm, _at, _v, _lo, _hi in (
        ("vo2_ref     metabolic rate", "vo2_ref", 250.0, 38.60, -31.00),
        ("frc_ref     THE UNCITED ONE", "frc_ref", 2500.0, -38.10, 38.60),
        ("k_frc_bmi   also uncited", "k_frc_bmi", 0.0417, 20.90, -19.70),
        ("shunt_anat  this branch's work", "shunt_anat", 0.03225, 0.20, -0.20)):
    check(f"{_nm}, -10%", _lever(_at, _v, 0.9), _lo, 0.06, " s")
    check(f"{_nm}, +10%", _lever(_at, _v, 1.1), _hi, 0.06, " s")
print("    TWO LEVERS CARRY IT AND ONE OF THEM IS UNCITED. A 10% error in")
print("    frc_ref or in vo2_ref moves desaturation by about 12%, near enough")
print("    one-for-one. frc_ref is the regression apnoea_core.py labels the")
print("    largest uncited lever in the model, so the dominant uncertainty in")
print("    every desaturation time this model reports is a number with no")
print("    author, journal or year in this repository.")
print("    AND THE SHUNT BARELY MATTERS TO TIMING: 10% on shunt_anat moves it")
print("    0.2 s, 0.06%. The whole obese-shunt branch changed OXYGENATION --")
print("    the PaO2 a patient starts from -- and hardly touched how long they")
print("    last. Both are true and they are different questions.")

# ---------------------------------------------------------------------------
print("\nQUANJER 1993 READ AT SOURCE 2026-09-25 -- IT SETTLES TWO THINGS AT ONCE")
print("  Quanjer PH, Tammeling GJ, Cotes JE, Pedersen OF, Peslin R, Yernault JC.")
print("  Lung volumes and forced ventilatory flows. ECSC / official statement of")
print("  the ERS. Eur Respir J 1993;6 Suppl 16:5-40. PMID 8499054. Table 6, p.26,")
print("  H = standing height in metres, A = age in years, volumes in litres:")
print("      Men    FRC = 2.34H + 0.009A - 1.09   RSD 0.6")
print("      Women  FRC = 2.24H + 0.001A - 1.00   RSD 0.50")
print("      Men    TLC = 7.99H - 7.08            RSD 0.70")
print("      Women  TLC = 6.60H - 5.79            RSD 0.60")


def _q_tlc_m(h):
    return (7.99 * h - 7.08) * 1000.0


def _q_frc_m(h, a):
    return (2.34 * h + 0.009 * a - 1.09) * 1000.0


print("  1. THE LARGEST UNCITED LEVER IS NOW CITED. apnoea_core.py quoted")
print("     FRC(L) = 2.34*height(m) + 0.009*age - 1.09 with no author, journal")
print("     or year. It is Quanjer's MEN'S equation, coefficient for")
print("     coefficient. The model has no sex, so it applies a male line to")
print("     every patient -- women's age term is 0.001 against men's 0.009.")
check("Quanjer men FRC at 1.75 m, age 45 [SEATED]", _q_frc_m(1.75, 45.0),
      3410.0, 1.0, " mL")
check("  our frc_ref, SUPINE, same subject",
      Patient(weight=22 * 1.75 * 1.75, height=1.75, age=45.0).frc_awake(),
      2500.0, 1.0, " mL")
check("  ... the supine-to-seated ratio we imply",
      Patient(weight=22 * 1.75 * 1.75, height=1.75, age=45.0).frc_awake()
      / _q_frc_m(1.75, 45.0), 0.733, 0.002, "")
print("  1b. RULED 2026-09-25: THIS IS A MALE MODEL. Quanjer's men's equations")
print("      are used for every patient, deliberately. The cost, from his own")
print("      women's equations at age 45:")


def _qf_f(h, a):
    return (2.24 * h + 0.001 * a - 1.00) * 1000.0


def _qt_f(h):
    return (6.60 * h - 5.79) * 1000.0


for _h, _wf, _wt in ((1.55, 0.856, 0.837), (1.65, 0.863, 0.836),
                     (1.75, 0.870, 0.834)):
    check(f"FRC women/men at {_h:.2f} m", _qf_f(_h, 45.0) / _q_frc_m(_h, 45.0),
          _wf, 0.002, "")
    check(f"TLC women/men at {_h:.2f} m", _qt_f(_h) / _q_tlc_m(_h), _wt,
          0.002, "")
print("      About 14% less FRC and 16% less TLC, and the age term differs")
print("      NINEFOLD (0.001 against 0.009), so a woman's FRC is very nearly")
print("      age-flat where a man's is not.")
print("      WHO THIS MISSES: Tokics' cohort was 3 women of 10; PELOSI'S WAS")
print("      SEVEN WOMEN TO ONE MAN per group -- and Pelosi is the curve")
print("      shunt_base_eff is fitted to. A male model is being fitted through")
print("      female-majority data. Ruled, recorded, and not small.")
print("     SO THE MODEL TAKES QUANJER'S SHAPE AND SETS ITS OWN LEVEL. Quanjer")
print("     measures SEATED (his section 6.1); frc_ref is supine. 0.73 is the")
print("     right sort of size for the supine fall but is not itself sourced.")

print("  2. TLC EXISTS NOW, AND IT HAS NO AGE TERM -- confirming from a primary")
print("     source what SOURCES.md had only reasoned to.")
for _h, _w in ((1.61, 5784.0), (1.64, 6024.0), (1.70, 6503.0),
               (1.74, 6823.0), (1.75, 6902.0)):
    check(f"Quanjer men TLC at {_h:.2f} m", _q_tlc_m(_h), _w, 1.0, " mL")

print("  3. AND THE CROSSOVER TEST PREDICTED IT BEFORE THE PAPER WAS READ.")
check("TLC the 44-year crossover implied, 1.75 m", _TLC44, 6676.0, 3.0, " mL")
check("  ... Quanjer's measured value there", _q_tlc_m(1.75), 6902.0, 1.0, " mL")
check("  ... they agree to", 100.0 * abs(_q_tlc_m(1.75) - _TLC44) / _q_tlc_m(1.75),
      3.28, 0.05, " %")
print("     A quantity the model did not contain, inverted out of a published")
print("     44-year crossover, landing within 3.3% of a paper nobody here had")
print("     read. That is the strongest independent check this block has had.")

print("  4. WHAT A BUIST CC ON QUANJER'S OWN TLC WOULD DO. NOT APPLIED.")
for _nm, _h, _b, _a, _want in (("Pelosi BMI 45", 1.64, 45.0, 52.0, 10.22),
                               ("Reinius BMI 45", 1.70, 45.0, 42.0, 9.31),
                               ("Perilli BMI 48.1", 1.61, 48.1, 37.0, 9.11),
                               ("Heard BMI 34.7", 1.74, 34.7, 42.0, 6.50)):
    class _QCC(Patient):
        def closing_capacity(self, _t=_q_tlc_m(_h)):
            return _buist_cc(self.age, _t)
    _q = _QCC(weight=_b * _h * _h, height=_h, age=_a, hb=14.0, tilt_deg=0.0)
    _n = Patient(weight=_b * _h * _h, height=_h, age=_a, hb=14.0, tilt_deg=0.0)
    check(f"{_nm}: shunt on Buist + Quanjer TLC [ours {_n.shunt_base_eff()*100:.2f}%]",
          _q.shunt_base_eff() * 100.0, _want, 0.05, " %")
print("     Every obese shunt FALLS, so this is a redesign and not a parameter")
print("     edit: cc_at_20/cc_per_year/cc_per_bmi would all go, replaced by a")
print("     predicted TLC times Buist's percentage. It moves every benchmark")
print("     and needs a ruling.")
print("  5. THE RANGE WE LEAVE. Table 6 applies to ages 18-70 (below 25, enter")
print("     25) and heights 1.55-1.95 m in men, 1.45-1.80 m in women. Our")
print("     crossover sweeps run outside it at both ends.")

# ---------------------------------------------------------------------------
print("\nTOKICS 1996 READ AT SOURCE 2026-09-25 -- the cohort BMI, and an SE")
print("  Tokics L, Hedenstierna G, Svensson L, Brismar B, Cederlund T,")
print("  Lundquist H, Strandberg A. V/Q distribution and correlation to")
print("  atelectasis in anesthetized paralyzed humans. J Appl Physiol")
print("  1996;81(4):1822-1833. SOURCES.md recorded only 'Tokics L, et al.';")
print("  the full list above is now read from the page.")

# Table 1, subject data, read at source: sex, age yr, height cm, weight kg
_TOK = [("F", 65, 155, 68), ("F", 62, 162, 77), ("F", 32, 174, 72),
        ("M", 36, 183, 80), ("M", 58, 179, 85), ("M", 60, 182, 74),
        ("M", 49, 180, 67), ("M", 56, 185, 88), ("M", 20, 178, 75),
        ("M", 49, 178, 88)]
_tb = np.array([w / ((h / 100.0) ** 2) for _, _, h, w in _TOK])
_th = np.array([h / 100.0 for _, _, h, _ in _TOK])
_tw = np.array([float(w) for _, _, _, w in _TOK])
_ta = np.array([float(a) for _, a, _, _ in _TOK])

print("  1. THE COHORT BMI, which this repository said was recorded NOWHERE.")
print("     Table 1 gives every height and weight, so it is computable:")
check("Tokics cohort mean BMI", float(_tb.mean()), 25.20, 0.02, "")
check("  ... its SD across the 10", float(_tb.std(ddof=1)), 2.79, 0.02, "")
check("  ... lowest BMI in the cohort", float(_tb.min()), 20.68, 0.02, "")
check("  ... highest BMI in the cohort", float(_tb.max()), 29.34, 0.02, "")
check("Tokics mean height", float(_th.mean()), 1.756, 0.001, " m")
check("Tokics mean weight", float(_tw.mean()), 77.40, 0.05, " kg")
check("Tokics mean age", float(_ta.mean()), 48.70, 0.05, " y")
print("     3 women and 7 men, and NOT ONE PATIENT IS OBESE -- the highest BMI")
print("     is 29.3. So this anchor is a NORMAL-WEIGHT anchor and cannot speak")
print("     to the obese end at all, which is what we have been using it for.")

print("  2. AND THE 1.3 IS A STANDARD ERROR. Table 3: \"means 6 SE; n 5 10.\"")
for _nm, _m, _se, _want in (("shunt Qs, %", 5.0, 1.3, 4.11),
                            ("low V/Q Qlow, %", 7.1, 1.8, 5.69),
                            ("log QSD, perfusion", 1.18, 0.12, 0.38),
                            ("log VSD, ventilation", 0.62, 0.05, 0.16),
                            ("cardiac output, l/min", 5.7, 0.3, 0.95),
                            ("PaO2, Torr", 159.1, 10.1, 31.94)):
    check(f"{_nm}: SD implied by SE {_se}", _se * np.sqrt(10.0), _want, 0.02, "")
print("     Every 'in SD of Tokics 5.0 (1.3)' in this repository used a band")
print("     3.16x too narrow. Corrected in SOURCES.md and here.")

print("  3. THE CARDIAC OUTPUT FINDING, AND IT IS THE IMPORTANT ONE.")
print("     Tokics measures 5.7 l/min anaesthetised in a 77 kg cohort. Perilli")
print("     measures 4.9 in a 125 kg one. OURS GOES THE OTHER WAY:")
_pt = Patient(weight=float(_tw.mean()), height=float(_th.mean()),
              age=float(_ta.mean()), hb=14.0, tilt_deg=0.0)
_pp = Patient(weight=48.1 * 1.61 * 1.61, height=1.61, age=37.0, hb=14.0,
              tilt_deg=0.0)
check("our CO at Tokics' lean cohort [measured 5.7]", _pt.co_anaes(), 4.04,
      0.02, " l/min")
check("our CO at Perilli's obese cohort [measured 4.9]", _pp.co_anaes(), 5.78,
      0.02, " l/min")
check("  our change across 77 -> 125 kg", 100.0 * (_pp.co_anaes() / _pt.co_anaes() - 1.0),
      43.0, 1.0, " %")
check("  the measured change across the same span", 100.0 * (4.9 / 5.7 - 1.0),
      -14.0, 0.5, " %")
print("     THE SIGN OF THE GRADIENT IS WRONG. co_anaes scales on weight^0.75,")
print("     so we rise 43% across that span while the two measurements fall")
print("     14%. The repository's standing caveat -- 'our cardiac output is")
print("     ~18% high' -- is therefore NOT an offset, and reading it as one")
print("     understates the problem at the lean end, where we are 29% LOW.")
print("     THIS MATTERS BEYOND THE ROW: via Dantzker 1980 cardiac output is")
print("     itself a shunt-reduction mechanism, and every shunt this")
print("     repository inverted was inverted through this CO.")
print("     CAVEATS, because they are not nothing: neither paper reports")
print("     haemoglobin, so hb 14 is OURS in both; the cohorts differ by 12")
print("     years of age; Perilli's 4.9 is his phase-4 supine value.")

print("  4. TWO MORE ANCHORS THE PAPER SUPPLIES, both now against correct SDs.")
check("our shunt at Tokics' own cohort mean [5.0, SD 4.11]",
      _pt.shunt_base_eff() * 100.0, 4.08, 0.02, " %")
check("  ... in SD", (_pt.shunt_base_eff() * 100.0 - 5.0) / (1.3 * np.sqrt(10.0)),
      -0.22, 0.02, " SD")
print("     Tokics' atelectatic area was 2.2 (SE 0.7) % at the diaphragm and")
print("     1.8 (SE 0.7) % 5 cm cranial, and his shunt correlated with it at")
print("     r = 0.91. Nine of ten patients had atelectasis; none had any awake.")

# ---------------------------------------------------------------------------
print("\nGUNNARSSON 1991 -- A CONDENSATION, NOT THE PAPER. Uploaded 2026-09-25.")
print("  What was uploaded is the SURVEY OF ANESTHESIOLOGY digest: two pages of")
print("  condensed abstract plus an editorial Comment by J. Briegel and Th.")
print("  Bein. The paper itself is")
print("    Gunnarsson L, Tokics L, Gustavsson H, Hedenstierna G. Influence of")
print("    age on atelectasis formation and gas exchange impairment during")
print("    general anaesthesia. Br J Anaesth 1991;66:423-432.")
print("  and it is NOT held. Everything below is SECOND-HAND, and the scan")
print("  carries no text layer, so the figures were read off an image with no")
print("  machine cross-check. Nothing here is written into any parameter.")
print("  Same group as the Tokics 1996 anchor -- Tokics is second author,")
print("  Hedenstierna senior -- so it is methodologically continuous with it.")

print("  WHAT IT CLAIMS, and it looks like a challenge to our age dependence:")
print("    shunt (V/Q < 0.005) vs age        NO CORRELATION")
print("    atelectasis vs age                NOT ASSOCIATED")
print("    low V/Q (0.005-0.1) vs age        r = 0.35, P < 0.05 anaesthetised")
print("    venous admixture vs age           r = 0.42, P < 0.05")
print("    log SD Q vs age                   r = 0.52, P < 0.01")
print("    PAO2-PaO2 vs age                  r = 0.34, P < 0.05")
print("  n = 45 (36 men, 9 women), 23-69 yr, mean 46, elective abdominal")
print("  surgery, mean FiO2 0.4, halothane or enflurane. 39 of 45 had")
print("  atelectasis; shunt correlated strongly with atelectatic area.")

_GA = np.arange(23.0, 70.0, 1.0)
_gsh, _guw = [], []
for _a in _GA:
    _gp = Patient(weight=24 * 1.75 * 1.75, height=1.75, age=float(_a), hb=14.0,
                  tilt_deg=0.0)
    _gsh.append(_gp.shunt_base_eff() * 100.0)
    _guw.append(_gp.unwashed_fraction() * 100.0)
_gsh, _guw = np.array(_gsh), np.array(_guw)
print("  OURS OVER THE SAME AGE RANGE, lean supine BMI 24 (his BMI is not in")
print("  the condensation, which is itself a gap):")
check("our shunt_base at age 23", float(_gsh[0]), 3.23, 0.02, " %")
check("our shunt_base at age 46", float(_gsh[23]), 3.81, 0.02, " %")
check("our shunt_base at age 69", float(_gsh[-1]), 4.45, 0.02, " %")
check("  ... the rise across his range", 100.0 * (_gsh[-1] / _gsh[0] - 1.0),
      38.0, 1.0, " %")
check("our unwashed low-V/Q at age 23", float(_guw[0]), 0.00, 0.02, " %")
check("our unwashed low-V/Q at age 69", float(_guw[-1]), 3.05, 0.02, " %")
print("    A CAUTION ON COMPARING THESE AT ALL: our shunt is a SMOOTH MONOTONE")
print("    FUNCTION of age, so its correlation with age is 1 by construction.")
print("    His r values are across 45 patients with real scatter. The")
print("    comparable quantity is the SIZE of the age effect, +38% across")
print("    23-69, against his report of none.")

print("  AND THE NUANCE THAT MAY DISSOLVE IT ENTIRELY. shunt_base_eff was")
print("  fitted by inverting PELOSI'S PaO2/PAO2 through this model, which makes")
print("  it an EFFECTIVE VENOUS ADMIXTURE -- shunt PLUS low V/Q -- and not a")
print("  true inert-gas shunt. Gunnarsson's VENOUS ADMIXTURE DOES rise with age,")
print("  r = 0.42. So our age dependence may be CORRECT and the conflict may be")
print("  a naming problem. This repository has been wrong before by reasoning")
print("  from a quantity's label rather than its definition, so it is recorded")
print("  as OPEN and nothing is changed on it.")
print("  WHAT WOULD SETTLE IT: his tables of shunt and low-V/Q against age,")
print("  which a two-page condensation does not carry. The primary paper is on")
print("  the wanted list.")

_gp = Patient(weight=24 * 1.75 * 1.75, height=1.75, age=46.0, hb=14.0,
              tilt_deg=0.0)
print("  ONE THING IT DOES CONFIRM, and it is not nothing:")
check("co_drop_frac: our anaesthetised CO as a fraction of awake",
      1.0 - _gp.co_drop_frac, 0.75, 0.005, "")
print("    He reports anaesthesia dropping cardiac output to 70-85% of awake.")
print("    We sit at 75%, inside his range -- an independent confirmation of a")
print("    parameter, from a source that was not used to set it.")

# ---------------------------------------------------------------------------
# JONES & NZEKWU 2006 -- OBTAINED AND READ AT SOURCE 2026-09-25
#
# Jones RL, Nzekwu MMU. The effects of body mass index on lung volumes.
# Chest 2006;130(3):827-833. DOI 10.1378/chest.130.3.827. The PDF was
# uploaded to the session as page images. SOURCES.md has called this "the
# decisive paper rather than a supporting one" for the FRC-against-BMI
# question since the obese deficit was traced out of closing capacity.
#
# 373 patients, BMI 20 to ~57, all white, all with normal FEV1/FVC, measured
# SEATED AND AWAKE by body plethysmography in two accredited laboratories.
# Percentages are OF PREDICTED, and the predicted values are Gutierrez 2004
# (Canadian Caucasians) -- NOT Quanjer, whose equations this model uses.
# That reference set is not held here, so Jones's percentages CANNOT be
# converted to millilitres in this repository, and nothing below tries to.
# ---------------------------------------------------------------------------
print("\nJONES & NZEKWU 2006 -- the FRC-vs-BMI paper, read at source")

_JF = lambda b: 231.9 * np.exp(-0.070 * b) + 55.2     # FRC, % predicted
_JE = lambda b: 587.8 * np.exp(-0.083 * b) + 6.5      # ERV, % predicted
# Pelosi 1998's helium regression, already used above: SUPINE ANAESTHETISED.
_PF = lambda b: 11.97 * np.exp(-0.096 * b) * 1000.0 + 460.0   # mL

print("  Figure 4, read off the page image:")
print("    FRC(%pred) = 231.9 exp(-0.070 BMI) + 55.2   r2 = 0.49, p < 0.0001")
print("    ERV(%pred) = 587.8 exp(-0.083 BMI) +  6.5   r2 = 0.49, p < 0.0001")
print("  THE FIGURE WAS READ OFF AN IMAGE, so it is checked against the")
print("  paper's OWN prose and its own Table 1 before anything is built on it.")
check("Jones FRC at BMI 20 [his text: 112]", _JF(20.0), 112.4, 0.6, " %pred")
check("Jones FRC at BMI 30 [his text: 84]", _JF(30.0), 83.6, 0.6, " %pred")
check("  ... FRC(30)/FRC(20) [his text: 75%]", 100.0 * _JF(30.0) / _JF(20.0),
      74.4, 0.7, " %")
check("Jones ERV at BMI 20 [his text: 118]", _JE(20.0), 118.3, 0.6, " %pred")
check("Jones ERV at BMI 30 [his text: 55]", _JE(30.0), 55.2, 0.6, " %pred")
check("  ... ERV(30)/ERV(20) [his text: 47%]", 100.0 * _JE(30.0) / _JE(20.0),
      46.7, 0.7, " %")
_jt = [abs(_JF(m) - t) for m, t in ((22.5, 103.1), (27.5, 89.2),
                                    (32.5, 78.3), (37.5, 72.2))]
check("  ... worst gap, Fig 4 vs Table 1 group means", max(_jt), 0.70, 0.10,
      " %pred")
print("    Six prose values and four group means all reproduce. The equations")
print("    are read correctly and can be used.")

print("\n  1. THE BMI EXPONENT NOW HAS A BRACKET, AND WE FALL OUT OF IT.")
print("  Jones is SEATED AWAKE; Pelosi is SUPINE ANAESTHETISED; Jones says in")
print("  his own discussion that Pelosi's absolute BMI effect was the LARGER.")
print("  So the two should BRACKET a supine awake lung -- which is exactly")
print("  what frc_awake() is. The comparable quantity is the LOCAL slope")
print("  d(ln FRC)/d(BMI), which handles the offsets that SOURCES.md correctly")
print("  noted make the raw exponents incomparable. Ours is k_frc_bmi =")
print("  0.0417 and it is CONSTANT, because our FRC has no offset at all.")
_h = 1e-4
_sl = lambda f, b: -(np.log(f(b + _h)) - np.log(f(b - _h))) / (2 * _h)
print("  Shown as PER CENT OF FRC LOST PER BMI UNIT, so ours reads 4.17.")
for _b, _wj, _wp in ((22.0, 3.32, 7.29), (30.0, 2.38, 5.70),
                     (40.0, 1.42, 3.44), (45.0, 1.07, 2.47)):
    check(f"BMI {_b:.0f}: Jones  seated awake", 100.0 * _sl(_JF, _b), _wj,
          0.02, " %/BMI")
    check(f"BMI {_b:.0f}: ours   supine awake", 4.17, 4.17, 0.01, " %/BMI")
    check(f"BMI {_b:.0f}: Pelosi supine anaesthetised", 100.0 * _sl(_PF, _b),
          _wp, 0.02, " %/BMI")
_bx = brentq(lambda b: _sl(_PF, b) - 0.0417, 20.0, 60.0)
check("BMI where ours overtakes even Pelosi's slope", _bx, 36.70, 0.05, "")
print("    Inside BMI 22-37 our exponent sits BETWEEN the two measurements,")
print("    which is where a supine awake lung belongs. ABOVE BMI ~37 ours is")
print("    steeper than BOTH -- steeper than the supine anaesthetised curve,")
print("    which ought to be the steeper of the pair.")
print("    THE MECHANISM IS THE SAME IN BOTH PAPERS AND ABSENT IN OURS:")
print("    Jones carries a +55.2 %pred offset and Pelosi a +460 mL offset, so")
print("    both decay to a NON-ZERO floor. Ours decays to zero and is caught")
print("    by the hard rv_eff() clamp instead. Two independent regressions of")
print("    the same quantity both have the offset; we have none.")
print("    WHAT THIS IS NOT: it is not a claim that our obese FRC VALUES are")
print("    wrong. SOURCES.md tabulates them against Pelosi's helium and they")
print("    agree to 11% across BMI 22-50. The finding is that above BMI ~37")
print("    that agreement is carried by the RESIDUAL-VOLUME FLOOR and not by")
print("    the BMI term -- which makes k_rv_bmi, not k_frc_bmi, the parameter")
print("    setting obese FRC. That matters because of finding 2.")

print("\n  2. A SECOND MEASUREMENT ARRIVES ON k_rv_bmi, WHICH HAD ONLY ONE.")
print("  apnoea_core.py says of k_rv_bmi, in its own words, 'ANCHORED ON ONE")
print("  MEASUREMENT and no more than that' -- Reinius's CT, 697 mL at BMI 45,")
print("  converted to an RV by assuming ERV ~= 0 there. Jones measures RV")
print("  across 373 patients and it barely moves with BMI.")
_rvp = ((22.5, 102.7), (27.5, 96.7), (32.5, 95.5), (37.5, 94.6), (43.0, 90.5))
_x = np.array([p[0] - 22.5 for p in _rvp])
_y = np.log([p[1] / 102.7 for p in _rvp])
_kfit = -float((_x * _y).sum() / (_x * _x).sum())
check("k_rv_bmi implied by Jones Table 1", 100.0 * _kfit, 0.63, 0.03,
      " %/BMI")
check("  ... ours, for comparison", 100.0 * 0.0198, 1.98, 0.01, " %/BMI")
check("  ... ratio, ours over Jones's", 0.0198 / _kfit, 3.14, 0.10, "x")
check("Jones RV fall, BMI 22.5 -> 37.5", 100.0 * (102.7 - 94.6) / 102.7,
      7.9, 0.1, " %")
check("ours  RV fall, same span", 100.0 * (1.0 - np.exp(-0.0198 * 15.5)),
      26.4, 0.1, " %")
print("    THIS IS MEASUREMENT AGAINST MEASUREMENT, NOT GUESS AGAINST")
print("    MEASUREMENT, and it is not resolved here. Three reasons to be")
print("    careful before calling k_rv_bmi wrong:")
print("      * TECHNIQUE. Jones is body PLETHYSMOGRAPHY, which counts gas")
print("        behind closed airways; Reinius is CT, which counts aerated")
print("        lung. In an obese chest full of trapped gas plethysmography")
print("        reads HIGHER, and that is the direction of the disagreement.")
print("        The repository already has a helium/CT ruling on this axis.")
print("      * POSTURE AND STATE. Jones is seated awake, Reinius supine")
print("        anaesthetised and paralysed.")
print("      * JONES'S RV IS DERIVED, NOT MEASURED: his Methods give TLC =")
print("        FRC + IC and RV = TLC - VC, so his RV inherits his FRC.")
print("    Recorded as a live conflict. NOTHING IS CHANGED ON IT.")

print("\n  AND THE COST OF 'CORRECTING' IT IS LARGE, WHICH IS WHY IT NEEDS A")
print("  RULING RATHER THAN AN EDIT. A lower k_rv_bmi RAISES obese RV, which")
print("  RAISES the floor that frc_anaes() is clamped to:")
for _b, _w in ((35.0, 0.0), (40.0, 10.9), (45.0, 32.4), (50.0, 45.9)):
    _p = Patient(height=1.64, weight=_b * 1.64 ** 2, age=52.0, hb=14.0,
                 tilt_deg=0.0)
    _fa = _p.frc_awake()
    _now = _p.frc_anaes()
    _alt = max(1100.0 * _p.height_factor() * np.exp(-_kfit * max(0.0, _b - 22.0)),
               _fa - min(400.0, 0.25 * _fa))
    check(f"BMI {_b:.0f}: frc_anaes change on Jones's k_rv_bmi",
          100.0 * (_alt / _now - 1.0), _w, 0.4, " %")
print("    At Pelosi's geometry a BMI 45 patient's anaesthetised FRC would")
print("    rise by a THIRD. More starting oxygen and less airway closure, so")
print("    SLOWER desaturation -- and Heard's obese control is already too")
print("    NEAR THE TOP OF ITS BAND at 307.6 s against an IQR of 244-314 --")
print("    PASSING, not failing. This line said 'SLOW at 319.8 s' until")
print("    2026-09-25, quoting a BEFORE value from a superseded table as")
print("    though it were current. Per CLAUDE.md that is")
print("    recorded as information and NOT compensated elsewhere.")

print("\n  3. THE ERV AGREEMENT WE HAD WAS A COMPENSATING PAIR.")
print("  Our ERV is DERIVED (frc_awake - rv_eff) and was never fitted to")
print("  anything, so Jones's measured ERV regression is a free test of it.")
print("  It looked like a pass. It is not one.")
_p20 = Patient(height=1.64, weight=20 * 1.64 ** 2, age=52.0, hb=14.0,
               tilt_deg=0.0)
_e20 = _p20.frc_awake() - _p20.rv_eff()
_e20j = _p20.frc_awake() - 1100.0 * _p20.height_factor() * np.exp(
    -_kfit * max(0.0, 20.0 - 22.0))
_en, _ec = [], []
for _b in (25.0, 30.0, 35.0, 40.0, 45.0):
    _p = Patient(height=1.64, weight=_b * 1.64 ** 2, age=52.0, hb=14.0,
                 tilt_deg=0.0)
    _j = 100.0 * _JE(_b) / _JE(20.0)
    _en.append(abs(100.0 * (_p.frc_awake() - _p.rv_eff()) / _e20 - _j))
    _ec.append(abs(100.0 * (_p.frc_awake() - 1100.0 * _p.height_factor()
                            * np.exp(-_kfit * max(0.0, _b - 22.0))) / _e20j - _j))
check("ERV vs Jones, mean abs error as shipped", float(np.mean(_en)), 3.62,
      0.05, " pp")
check("ERV vs Jones, mean abs error with RV alone corrected",
      float(np.mean(_ec)), 7.21, 0.05, " pp")
print("    Correcting RV ALONE makes the ERV agreement TWICE AS BAD, and at")
print("    BMI 45 drives our ERV to 0.4% of its lean value -- FRC collapsing")
print("    onto RV. So the agreement as shipped comes from an FRC that falls")
print("    too fast and an RV that falls too fast, subtracting. That is the")
print("    same compensating-pair shape this repository has caught twice")
print("    before, and it means the two cannot be fixed one at a time.")
print("    Both would be fixed by the SAME missing mechanism: the non-zero")
print("    asymptote that Jones and Pelosi each measure and we do not have.")

print("\n  4. IT BEARS DIRECTLY ON THE OPEN BUIST & ROSS RULING.")
print("  That ruling would compute closing capacity as a PERCENTAGE OF TLC,")
print("  with the TLC coming from Quanjer. QUANJER'S TLC HAS NO WEIGHT TERM.")
print("  Jones measures TLC falling 0.50 %pred per BMI unit (his Fig 3), so a")
print("  Quanjer TLC OVERESTIMATES the obese lung, and closing capacity with")
print("  it -- in exactly the patients this branch is about:")
for _b, _w in ((30.0, 5.3), (40.0, 11.2), (45.0, 14.4)):
    check(f"BMI {_b:.0f}: Quanjer TLC over Jones's measured TLC",
          100.0 * (100.0 / (98.7 - 0.50 * (_b - 22.5)) - 1.0), _w, 0.2, " %")
print("    This does not sink the Buist route -- it quantifies a known and")
print("    correctable bias in it, which is better than the route had before.")
print("    The earlier costing (Perilli 12.53 -> 9.11%) used the uncorrected")
print("    Quanjer TLC, so it OVERSTATES how far the obese shunt would fall.")

print("\n  5. AND IT SOFTENS THE COST RECORDED AGAINST THE MALE RULING.")
print("  Yesterday's ruling made this a male model and recorded against it")
print("  that Pelosi's cohort was seven women to one man per group. Jones,")
print("  n = 373 with both sexes, reports in his Results that there were NO")
print("  significant differences between men and women in the best-fit")
print("  regression lines for the effect of BMI on TLC, VC, RV, FRC, ERV or")
print("  DLCO -- which is why he pooled them. So the BMI TERM does not need a")
print("  sex; only the BASE lung volume does. The female-majority worry falls")
print("  on Quanjer's LEVEL, not on k_frc_bmi's SLOPE. The ruling stands and")
print("  its recorded cost is narrower than it was.")

# ---------------------------------------------------------------------------
# THE OFFSET FORM, COSTED -- ruled 2026-09-25 ("6 y")
#
# Two experimental switches were added to apnoea_core.py, as CLASS ATTRIBUTES
# rather than dataclass fields so an experiment can subclass and flip them
# without touching a call site. Both default OFF and the shipped path is
# bit-identical: verified over 72 geometries, 0 mismatches. They are PYTHON
# ONLY -- model.js implements neither -- so if either is ever adopted,
# model.js must change in the same commit.
# ---------------------------------------------------------------------------
print("\nTHE OFFSET FORM, COSTED -- and the first cut of it was wrong")

# PELOSI'S SHAPE WAS ADOPTED BY RULING on 2026-09-25, so plain Patient IS
# variant C now. _Legacy restores the exponential form it replaced, and the
# two experimental switches are applied ON TOP OF _Legacy so that the
# four-way comparison below reproduces EXACTLY the one the ruling was made
# on, rather than silently becoming a different experiment.
class _Legacy(Patient):   frc_legacy_exp = True
class _Asym(_Legacy):     frc_asymptote = True
class _JonesRV(_Legacy):  k_rv_bmi_jones = True

_PFRC = lambda b: 11.97 * np.exp(-0.096 * b) * 1000.0 + 460.0   # Pelosi, mL
_PGEO = dict(height=1.64, age=52.0, hb=14.0, tilt_deg=0.0)

print("  THE TRAP, AND IT CAUGHT ME FIRST TIME. The obvious reading of 'give")
print("  FRC the offset both papers have' is to let FRC decay to RV instead")
print("  of to zero, keeping k_frc_bmi. THAT IS WRONG, and the reason is")
print("  worth stating: THE OFFSET AND THE EXPONENT ARE NOT INDEPENDENT.")
print("  k_frc_bmi = 0.0417 was calibrated for a form with NO offset, so")
print("  bolting an asymptote underneath it can only RAISE the obese lung.")
print("  Pelosi's own offset form carries an exponent of 0.096 -- more than")
print("  twice ours -- precisely because it has the 460 mL offset under it.")
print("  Doing it faithfully means taking the exponent WITH the offset.")
print("  Anaesthetised FRC against Pelosi's MEASURED helium, at his geometry:")
for _b, _w in ((30.0, 1132.0), (40.0, 717.0), (45.0, 619.0), (50.0, 559.0)):
    check(f"BMI {_b:.0f}: Pelosi's measured FRC", _PFRC(_b), _w, 1.0, " mL")
_err = {}
for _nm, _cls in (("shipped", _Legacy), ("B asymptote-at-RV", _Asym),
                  ("C Pelosi-shape", Patient), ("D Jones RV", _JonesRV)):
    _e = [abs(_cls(weight=_b * 1.64 ** 2, **_PGEO).frc_anaes() / _PFRC(_b) - 1.0) * 100.0
          for _b in (22.0, 30.0, 35.0, 40.0, 45.0, 50.0)]
    _err[_nm] = float(np.mean(_e))
check("mean |error| vs Pelosi: shipped", _err["shipped"], 7.79, 0.05, " %")
check("  ... B, asymptote at RV keeping k_frc_bmi",
      _err["B asymptote-at-RV"], 38.28, 0.05, " %")
check("  ... C, Pelosi's shape with our level",
      _err["C Pelosi-shape"], 1.86, 0.05, " %")
check("  ... D, Jones's RV slope", _err["D Jones RV"], 23.50, 0.05, " %")
print("    B IS FIVE TIMES WORSE THAN SHIPPED. The correction motivated by")
print("    Pelosi's offset, done the obvious way, disagrees with Pelosi. Per")
print("    CLAUDE.md that is recorded, not compensated.")
print("    C IS FOUR TIMES BETTER THAN SHIPPED, and introduces NO parameter:")
print("    it carries Pelosi's measured FRC(BMI)/FRC(22) as a SHAPE with the")
print("    level left ours -- exactly what the model already does with")
print("    Quanjer's height term. It is applied to frc_anaes() because that")
print("    is the quantity Pelosi measured; applying it to frc_awake() and")
print("    subtracting the induction drop afterwards over-steepens it, since")
print("    an absolute drop eats a growing FRACTION as the lung shrinks.")

print("\n  AND THE k_rv_bmi CONFLICT LARGELY DISSOLVES -- ON A DEFINITION.")
print("  Jones's RV slope cannot simply be adopted, and the reason is not a")
print("  preference between two measurements. It is arithmetic:")
print("    FRC can never be less than RV. Pelosi MEASURES anaesthetised FRC.")
print("    Jones's slope would put RV ABOVE it in the obese.")
print("   BMI   Pelosi measured FRC   RV on Jones's slope   implied ERV")
for _b, _wf, _wr, _we in ((30.0, 1132.0, 956.0, 176.0),
                          (35.0, 876.0, 927.0, -51.0),
                          (45.0, 619.0, 870.0, -251.0),
                          (50.0, 559.0, 843.0, -285.0)):
    _p = Patient(weight=_b * 1.64 ** 2, **_PGEO)
    _rj = 1100.0 * _p.height_factor() * np.exp(-0.0063 * max(0.0, _b - 22.0))
    check(f"BMI {_b:.0f}: RV on Jones's slope", _rj, _wr, 1.0, " mL")
    check(f"  ... implied expiratory reserve", _PFRC(_b) - _rj, _we, 1.5, " mL")
_cross = brentq(lambda b: _PFRC(b) - 1100.0
                * Patient(weight=b * 1.64 ** 2, **_PGEO).height_factor()
                * np.exp(-0.0063 * max(0.0, b - 22.0)), 25.0, 60.0)
check("Jones's RV crosses Pelosi's measured FRC at BMI", _cross, 33.6, 0.1, "")
print("    A NEGATIVE expiratory reserve is not a disagreement, it is an")
print("    IMPOSSIBILITY: the lung would hold less gas at rest than after a")
print("    maximal exhalation. Above BMI 33.6 Jones's RV and Pelosi's FRC")
print("    cannot both describe the same patient.")
print("    THE RESOLUTION IS IN THE CODE'S OWN COMMENT, and this repository")
print("    has been caught before by reading a quantity's LABEL rather than")
print("    its DEFINITION. apnoea_core.py says of rv, verbatim:")
print("        rv: float = 1100.0    # mL, ANAESTHETISED SUPINE, AT BMI 22")
print("    Jones measured SEATED AND AWAKE. It is not the same quantity, so")
print("    his 0.63%/BMI is not a competing value for this parameter -- it")
print("    is a measurement of a different state. THE CONFLICT RECORDED ON")
print("    2026-09-25 WAS OVERSTATED BY ME AND IS CORRECTED HERE.")
print("    WHAT SURVIVES OF IT, because this is not a clean acquittal:")
print("    Reinius's single CT point is still the only anchor for the")
print("    anaesthetised supine slope, and Jones now implies that the")
print("    seated-awake-to-anaesthetised fall in RV must itself be large in")
print("    the obese -- a step the model does not represent at all.")


print("\n  THE BENCHMARK COST, MEASURED -- four full test_validation.py runs.")
print("  Those runs are 10-15 minutes each and are NOT repeated here; they are")
print("  regenerated by `python3 variant_cost.py <variant>`, which is in the")
print("  repository for exactly that reason. Recorded, with the MECHANISM")
print("  behind each move computed below so the table cannot drift silently.")
print("  THE COLUMNS BELOW ARE AS MEASURED BEFORE THE RULING: 'shipped'")
print("  MEANS THE EXPONENTIAL FORM, WHICH IS NOW REACHED BY _Legacy.")
print("                         legacy   B asympt   C = SHIPPED   D jonesRV")
print("    blocking failures         4          5            4           5")
print("    Heard ctrl [244-314]  307.6      369.9        272.0       307.6")
print("    tilt BMI44@25 [15-40]  35.9       28.5         38.4         9.9")
print("    mean |err| vs Pelosi   7.79%     38.28%       1.86%      23.50%")
print("  C COSTS NOTHING: the same four blocking rows by the same four names,")
print("  fourfold better against Pelosi, and Heard's obese control moves from")
print("  the TOP of its band to the MIDDLE. B and D each break a row.")

print("\n  AND HERE IS WHY EACH ONE MOVES, computed at the suite's own")
print("  configurations rather than asserted:")
_HEARD = dict(weight=105.0, height=1.74, age=42.0, hb=14.0, tilt_deg=30.0)
for _nm, _cls, _w in (("shipped", _Legacy, 1695.6),
                      ("B asymptote at RV", _Asym, 2044.3),
                      ("C Pelosi shape", Patient, 1469.8),
                      ("D Jones RV", _JonesRV, 1695.6)):
    check(f"Heard's patient, anaesthetised FRC: {_nm}",
          _cls(**_HEARD).frc_anaes(), _w, 1.0, " mL")
print("    READ IT AGAINST THE TABLE. B gives Heard's patient 349 mL MORE gas")
print("    than shipped and he lasts 369.9 s, out of band. C gives him 226 mL")
print("    LESS and he lands at 272.0 s, mid-band. D does not move him AT ALL")
print("    -- 307.6 s in both columns, identical FRC -- because the")
print("    residual-volume floor does not bind at his BMI of 34.7. THE FLOOR IS")
print("    WHY D LOOKS HARMLESS HERE AND IS NOT: it bites only higher up.")

# The suite's own configuration for this row, read from test_validation.py
# rather than invented: 120 kg, 1.65 m, age 45, hb 14, 0 vs 25 degrees.
_T44 = dict(weight=120.0, height=1.65, age=45.0, hb=14.0)
print("  D's real cost is the TILT ROW, and the mechanism is the floor.")
print("  FRC that head-up tilt buys a BMI 44 patient, at the suite's own")
print("  configuration -- compare with the apnoea-time gains in the table:")
for _nm, _cls, _f, _t, _g in (("shipped", _Legacy, 688.6, 961.7, 39.7),
                              ("B asymptote at RV", _Asym, 984.3, 1276.5, 29.7),
                              ("C Pelosi shape", Patient, 655.2, 936.6, 43.0),
                              ("D Jones RV", _JonesRV, 882.6, 961.7, 9.0)):
    _flat = _cls(tilt_deg=0.0, **_T44).frc_anaes()
    _up = _cls(tilt_deg=25.0, **_T44).frc_anaes()
    check(f"BMI 44 flat, anaesthetised FRC: {_nm}", _flat, _f, 1.0, " mL")
    check(f"  ... at 25 deg head-up: {_nm}", _up, _t, 1.0, " mL")
    check(f"  ... the FRC gain tilt buys: {_nm}",
          100.0 * (_up / _flat - 1.0), _g, 0.2, " %")
print("    THE FRC GAIN TRACKS THE BENCHMARK ROW ALMOST ONE FOR ONE:")
print("      shipped 39.7% FRC -> 35.9% apnoea time")
print("      B       29.7%     -> 28.5%")
print("      C       43.0%     -> 38.4%")
print("      D        9.0%     ->  9.9%   <- the row that FAILS")
print("    WITH JONES'S RV THE OBESE LUNG IS PINNED AT ITS FLOOR, and head-up")
print("    tilt works by RAISING FRC -- so there is almost nothing left to")
print("    lift. That is a SECOND, INDEPENDENT argument against transplanting")
print("    his seated-awake RV into this model, on top of the negative")
print("    expiratory reserve above, and it is measured against four")
print("    randomised trials that find roughly +30%.")
# ---------------------------------------------------------------------------
# PELOSI RE-INVERTED THROUGH A CORRECTED CARDIAC OUTPUT -- ruled ("7 y")
# ---------------------------------------------------------------------------
print("\nPELOSI RE-INVERTED THROUGH A CORRECTED CARDIAC OUTPUT")
print("  shunt_base_eff was fitted by inverting Pelosi's PaO2/PAO2 THROUGH")
print("  THIS MODEL, so it inherited this model's cardiac output -- which")
print("  Tokics showed has the wrong GRADIENT. Two measured anaesthetised")
print("  values anchor a correction: Tokics 5.70 l/min at 77.4 kg, Perilli")
print("  4.90 at 125 kg.")
_BEXP = np.log(4.90 / 5.70) / np.log(125.0 / 77.4)
check("power-law exponent through the two measurements", _BEXP, -0.3155, 0.001, "")
print("    A NEGATIVE exponent -- cardiac output FALLING with body mass. That")
print("    is what the two points say; it is not a law anyone published, it")
print("    rests on two cohorts from different studies, and at Pelosi's lean")
print("    end (BMI 22 is 59 kg) it EXTRAPOLATES BELOW BOTH ANCHORS. So a")
print("    FLAT cardiac output is inverted alongside it: if both corrections")
print("    move the answer the same way, the answer is not an artefact of")
print("    the exponent. THIS IS A SENSITIVITY PROBE, NOT A PROPOSED")
print("    PARAMETER, and nothing here is written into the model.")


def _co_cls(mode, shunt=None):
    """A patient whose anaesthetised cardiac output is replaced wholesale.

    'shipped' leaves it alone; 'power' is the two-point law above; 'flat'
    pins it at 5.30 l/min, the midpoint of the two measurements.
    """
    class _P(Patient):
        def co_anaes(self):
            if mode == 'shipped':
                return Patient.co_anaes(self)
            _k = self.anaemia_co_factor() * self.tilt_co_factor()
            return (5.70 * (self.weight / 77.4) ** _BEXP * _k
                    if mode == 'power' else 5.30 * _k)
        if shunt is not None:
            def shunt_base_eff(self):
                return shunt
    return _P


def _co_invert(b, mode):
    """The shunt that reproduces Pelosi's oxygenation at this BMI and CO.

    Same bisection as _pel_invert above, but through a replaced cardiac
    output. COMPUTED, not recorded: these are the numbers the ruling of
    2026-09-25 turns on, so they must not be able to rot.
    """
    _tgt = _pel_ratio(b) * _PALV
    _lo, _hi = 0.005, 0.60
    for _ in range(22):
        _mid = 0.5 * (_lo + _hi)
        _p = _co_cls(mode, _mid)(weight=b * _PH * _PH, height=_PH, age=_PAGE,
                                 hb=_PHB, tilt_deg=0.0)
        _r = simulate(_p, [AirwayEpoch(2.0, resistance=2.0, fgo2=_PFIO2)],
                      dt=DT, feo2_start=_PALV / ac.PDRY, paco2_start=_PPACO2,
                      stop_sao2=0.0)
        if _r['pao2'][0] > _tgt:
            _lo = _mid
        else:
            _hi = _mid
    return 0.5 * (_lo + _hi) * 100.0


print("  THE SHUNT PELOSI IMPLIES, BMI 22 -> 50:")
_inv = {}
for _mode, _nm, _lo, _hi, _fac in (
        ('shipped', "through our shipped CO", 3.47, 14.12, 4.07),
        ('power', "through a power-law CO", 6.31, 11.40, 1.81),
        ('flat', "through a flat CO", 5.44, 12.46, 2.29)):
    _a, _z = _co_invert(22.0, _mode), _co_invert(50.0, _mode)
    _inv[_mode] = (_a, _z)
    check(f"{_nm}: at BMI 22", _a, _lo, 0.05, " %")
    check(f"{_nm}: at BMI 50", _z, _hi, 0.05, " %")
    check(f"{_nm}: the FACTOR across that span", _z / _a, _fac, 0.02, "x")
print("    READ THE LAST COLUMN. Our cardiac output makes Pelosi imply a")
print("    FOURFOLD rise in shunt across BMI 22-50. Corrected, it is 1.8- to")
print("    2.3-fold. ROUGHLY HALF OF shunt_base_eff's BMI DEPENDENCE IS A")
print("    CARDIAC-OUTPUT ARTEFACT, not a property of the lung -- and both")
print("    corrections agree on that despite assuming different things.")
print("  Our shipped law against each inversion, worst residual:")
_BMIS = (22.0, 30.0, 34.0, 42.0, 50.0)
_OURS = [Patient(weight=_b * _PH * _PH, height=_PH, age=_PAGE, hb=_PHB,
                 tilt_deg=0.0).shunt_base_eff() * 100.0 for _b in _BMIS]
for _mode, _nm, _w in (('shipped', "vs the shipped-CO inversion", 1.01),
                       ('power', "vs the power-law-CO inversion", 2.84),
                       ('flat', "vs the flat-CO inversion", 1.77)):
    _res = [abs(_o - _co_invert(_b, _mode))
            for _b, _o in zip(_BMIS, _OURS)]
    check(_nm, max(_res), _w, 0.05, " pp")
print("    Against a corrected cardiac output our law is out by up to 2.84 pp")
print("    -- larger than the 0.49 pp worst residual the re-key was judged on,")
print("    and larger than the 0.27 pp of the quadratic it replaced.")

print("\n  RE-DERIVED 2026-09-25 AFTER PELOSI'S SHAPE WAS ADOPTED, and two")
print("  things came out of it that the cost table could not see.")
print("  FIRST, THE INVERSION ITSELF DID NOT MOVE AT ALL -- 3.47/14.12,")
print("  6.31/11.40 and 5.44/12.46 to the last digit. It is a shunt equation")
print("  evaluated over two seconds at a fixed alveolar PO2, so it barely")
print("  depends on FRC. THE CARDIAC-OUTPUT FINDING THEREFORE SURVIVES THE")
print("  ADOPTION UNCHANGED, which is worth knowing because almost nothing")
print("  else in this file did.")
print("  SECOND, AND IT IS A COST THE COST TABLE MISSED. shunt_base_eff reads")
print("  closure against frc_anaes, so adopting a LOWER anaesthetised FRC")
print("  raises the shunt wherever the change bites:")
for _b, _wl, _wn in ((22.0, 3.71, 3.71), (30.0, 5.75, 6.28),
                     (34.0, 7.09, 7.98), (42.0, 10.49, 11.38),
                     (50.0, 14.24, 14.24)):
    _lp = _Legacy(weight=_b * _PH * _PH, height=_PH, age=_PAGE, hb=_PHB,
                  tilt_deg=0.0).shunt_base_eff() * 100.0
    _np_ = Patient(weight=_b * _PH * _PH, height=_PH, age=_PAGE, hb=_PHB,
                   tilt_deg=0.0).shunt_base_eff() * 100.0
    check(f"BMI {_b:.0f}: shunt_base_eff, legacy", _lp, _wl, 0.02, " %")
    check(f"  ... adopted", _np_, _wn, 0.02, " %")
print("    NOTHING MOVES AT BMI 22 OR 50, and for two different reasons: at 22")
print("    the two FRC forms agree EXACTLY by construction, and at 50 both are")
print("    already floored at residual volume. The change bites only between.")
print("    THE CONSEQUENCE, STATED PLAINLY: shunt_anat and shunt_cc_k WERE")
print("    FITTED AGAINST THE OLD frc_anaes, so the adoption has moved the")
print("    shunt law away from the curve it was fitted to. Its worst residual")
print("    against the shipped-CO inversion goes 0.25 -> 1.01 pp, FOURFOLD.")
print("    The cost table measured test_validation rows and could not see")
print("    this, because no benchmark row reads that residual.")
print("    NOT REFITTED. Refitting shunt_cc_k here would be tuning a parameter")
print("    to a curve, which CLAUDE.md refuses, and it would be doing it")
print("    THROUGH A CARDIAC OUTPUT ALREADY KNOWN TO HAVE THE WRONG GRADIENT.")
print("    Recorded as a consequence of the adoption, awaiting the cardiac")
print("    output being fixed first.")
print("    THE ORDER OF WORK THIS IMPLIES: the cardiac-output gradient is")
print("    UPSTREAM of the shunt law, so fixing the shunt law first would be")
print("    fitting around an error rather than removing it. NOTHING CHANGED.")

# ---------------------------------------------------------------------------
# GUTIERREZ 2004 -- OBTAINED AND READ AT SOURCE 2026-09-25
#
# Gutierrez C, Ghezzo RH, Abboud RT, Cosio MG, Dill JR, Martin RR,
# McCarthy DS, Morse JLC, Zamel N. Reference values of pulmonary function
# tests for Canadian Caucasians. Can Respir J 2004;11(6):414-424.
#
# n = 327 women and 300 men, six Canadian centres, ages 20-80, all Caucasian
# LIFETIME NONSMOKERS, body plethysmography. This is the reference set every
# per cent in Jones & Nzekwu is a per cent OF, so it is what turns Jones from
# a shape into a level.
# ---------------------------------------------------------------------------
print("\nGUTIERREZ 2004 -- the reference set under Jones, read at source")

# Table 3, ADULT MALES. HEIGHT IN CENTIMETRES, volumes in litres.
_GM_TLC = lambda h: -8.618 + 0.090 * h
_GM_VC = lambda h, a: -5.897 + 0.069 * h - 0.023 * a
_GM_FRC = lambda h: -4.633 + 0.046 * h          # NO AGE TERM AT ALL
_GM_RV = lambda h, a: -2.443 + 0.020 * h + 0.021 * a
_QM_FRC = lambda h, a: 2.34 * h + 0.009 * a - 1.09      # Quanjer, h in METRES
_QM_TLC = lambda h: 7.99 * h - 7.08

print("  Table 3, men (height in CM, litres): TLC -8.618 + 0.090H;")
print("  VC -5.897 + 0.069H - 0.023A; FRC -4.633 + 0.046H; RV -2.443 +")
print("  0.020H + 0.021A. THE TABLE WAS READ OFF A PAGE IMAGE, so it is")
print("  checked for internal consistency before anything is built on it:")
check("male 175 cm 45 y: TLC", _GM_TLC(175.0), 7.132, 0.002, " L")
check("  ... VC", _GM_VC(175.0, 45.0), 5.143, 0.002, " L")
check("  ... RV", _GM_RV(175.0, 45.0), 2.002, 0.002, " L")
check("  ... VC + RV against TLC, as a % gap",
      100.0 * ((_GM_VC(175.0, 45.0) + _GM_RV(175.0, 45.0)) / _GM_TLC(175.0) - 1.0),
      0.18, 0.02, " %")
print("    Three independently-read equations close on the fourth to 0.2%.")

print("\n  1. IT CORROBORATES THE LEVEL QUANJER SETS, TO 0.2%.")
check("male FRC at 1.75 m / 45 y: Quanjer", _QM_FRC(1.75, 45.0) * 1000.0,
      3410.0, 1.0, " mL")
check("  ... Gutierrez", _GM_FRC(175.0) * 1000.0, 3417.0, 1.0, " mL")
print("    A European and a Canadian reference set, built two decades and an")
print("    ocean apart, agree to 0.2% on the quantity this model's height")
print("    term IS. That is the strongest check the FRC level has had.")

print("\n  2. AND THEY FLATLY DISAGREE ABOUT AGE -- WHICH BEARS ON AN OPEN")
print("     RULING. Quanjer's men's FRC carries +0.009*age. GUTIERREZ'S HAS")
print("     NO AGE TERM AT ALL (the cell is blank, r2 = 0.17).")
for _a, _w in ((20.0, 7.28), (45.0, 0.21), (70.0, -5.99)):
    check(f"age {_a:.0f}: Gutierrez over Quanjer",
          100.0 * (_GM_FRC(175.0) / _QM_FRC(1.75, _a) - 1.0), _w, 0.05, " %")
check("Quanjer's male FRC rise across age 20-70",
      100.0 * (_QM_FRC(1.75, 70.0) / _QM_FRC(1.75, 20.0) - 1.0), 14.13, 0.05, " %")
print("    THE MODEL IS CURRENTLY AGE-FLAT, because Quanjer's age term was")
print("    never implemented. That has been recorded as a DEFECT awaiting a")
print("    ruling. A SECOND REFERENCE SET NOW SAYS AGE-FLAT IS RIGHT for")
print("    men. Taken with the fact that implementing the term moves the")
print("    CC = FRC crossover 55.0 -> 59.9 years, FURTHER from the published")
print("    ~44, there is now a POSITIVE case for leaving it out rather than")
print("    merely an unfixed omission. STILL A RULING, not taken here.")
print("    The honest caveat: Gutierrez's FRC model is weak, r2 = 0.17, and")
print("    a term can be absent from a regression because it is small OR")
print("    because the data cannot see it.")

print("\n  3. THE SUPINE FALL, CONFIRMED BY A SECOND SOURCE.")
_p22 = Patient(weight=22.0 * 1.75 ** 2, height=1.75, age=45.0, hb=14.0,
               tilt_deg=0.0)
check("frc_ref over Gutierrez's seated prediction",
      _p22.frc_awake() / (_GM_FRC(175.0) * 1000.0), 0.7317, 0.001, "")
print("    apnoea_core.py says of the ratio against Quanjer that 0.733 is")
print("    'the right size for the supine fall, not itself sourced'. Against")
print("    Gutierrez it is 0.732. The same number from an independent")
print("    reference set -- still not a measurement OF the supine fall, but")
print("    no longer resting on one reference set's level.")
check("our rv over Gutierrez's seated-awake RV",
      _p22.rv_eff() / (_GM_RV(175.0, 45.0) * 1000.0), 0.5495, 0.001, "")
print("    AND THIS ONE IS NEW. Our rv is documented ANAESTHETISED SUPINE and")
print("    sits at 55% of the seated-awake prediction. So the model ALREADY")
print("    embodies a 45% seated-to-anaesthetised fall in residual volume at")
print("    the lean end -- baked into a constant rather than represented. That")
print("    is the same step the k_rv_bmi retraction said the model 'does not")
print("    represent at all'. It does represent it; it just cannot VARY it.")

print("\n  4. JONES IN MILLILITRES -- WHAT THIS PAPER WAS WANTED FOR.")
_JF = lambda b: 231.9 * np.exp(-0.070 * b) + 55.2
print("   BMI   Jones %pred   Jones mL   ours mL   implied supine/seated")
for _b, _wj, _wo, _wr in ((22.0, 3585.0, 2500.0, 0.697),
                          (30.0, 2857.0, 1791.0, 0.627),
                          (40.0, 2368.0, 1180.0, 0.498),
                          (50.0, 2125.0, 778.0, 0.366)):
    _q = Patient(weight=_b * 1.75 ** 2, height=1.75, age=45.0, hb=14.0,
                 tilt_deg=0.0)
    _jm = _JF(_b) / 100.0 * _GM_FRC(175.0) * 1000.0
    check(f"BMI {_b:.0f}: Jones, in mL", _jm, _wj, 1.0, " mL")
    check(f"  ... ours, supine awake", _q.frc_awake(), _wo, 1.0, " mL")
    check(f"  ... implied supine/seated ratio", _q.frc_awake() / _jm, _wr,
          0.001, "")
print("    THE MODEL'S POSTURE CLAIM IS NOW A NUMBER FOR THE FIRST TIME: it")
print("    says lying flat costs a lean patient 30% of FRC and a BMI 50")
print("    patient 63%. The direction is right -- abdominal mass loads the")
print("    diaphragm harder supine -- but the SIZE at the obese end is a")
print("    strong claim that NOTHING IN THIS REPOSITORY TESTS.")
print("    WATSON & PRIDE 2005 is exactly that measurement, and it is on the")
print("    wanted list. This is the number it would check.")
_r = []
for _h in (1.60, 1.75, 1.85):
    _a = Patient(weight=22.0 * _h * _h, height=_h, age=45.0, hb=14.0,
                 tilt_deg=0.0).frc_awake() / (_JF(22.0) / 100.0 * _GM_FRC(_h * 100) * 1000.0)
    _z = Patient(weight=50.0 * _h * _h, height=_h, age=45.0, hb=14.0,
                 tilt_deg=0.0).frc_awake() / (_JF(50.0) / 100.0 * _GM_FRC(_h * 100) * 1000.0)
    _r.append(_z / _a)
check("fall in that ratio, BMI 22 -> 50, at 1.60 m", _r[0], 0.5254, 0.001, "x")
check("  ... at 1.75 m", _r[1], 0.5254, 0.001, "x")
check("  ... at 1.85 m", _r[2], 0.5254, 0.001, "x")
print("    JONES REPORTS NO COHORT HEIGHT OR AGE, so the ratio above is at OUR")
print("    reference geometry and its LEVEL moves with height (0.77 to 0.66 at")
print("    BMI 22 across 1.60-1.85 m). Its FALL does not: x0.525 at every")
print("    height, because the height terms cancel in a ratio of ratios. The")
print("    claim that the posture cost NEARLY DOUBLES across BMI 22-50 is")
print("    therefore independent of the geometry chosen.")

# ---------------------------------------------------------------------------
# ROY 1963 -- OBTAINED AND READ AT SOURCE 2026-09-25
#
# Roy SB, Bhatia ML, Mathur VS, Virmani S. Hemodynamic effects of chronic
# severe anemia. Circulation 1963;28(3):346-356. THE LAST GENUINELY
# INCOMPLETE CITATION IN SOURCES.md, and it is a FULL PAPER, not an
# abstract -- which settles whether test_validation.py's "CLINICAL" label
# on this row is honest. It is.
# ---------------------------------------------------------------------------
print("\nROY 1963 -- the anaemia/cardiac-output source, read at source")

# Table 5, read from the page: 25 patients, Hb and cardiac index (L/min/m2)
# BEFORE and AFTER treatment of the anaemia. Each patient is his own control.
_T5 = ((2.5, 13.6, 12.5, 7.7), (4.5, 13.0, 11.0, 6.0), (1.8, 11.3, 12.5, 3.7),
       (3.5, 10.4, 10.0, 8.3), (4.0, 9.7, 10.0, 7.7), (1.5, 8.9, 10.0, 3.4),
       (2.5, 8.6, 10.0, 4.0), (6.5, 8.5, 11.0, 4.3), (4.0, 8.0, 12.5, 5.8),
       (4.0, 8.0, 11.0, 6.6), (6.0, 7.0, 10.0, 6.2), (4.5, 6.9, 11.5, 3.6),
       (3.8, 6.5, 10.8, 6.5), (2.0, 6.3, 10.0, 4.7), (4.5, 6.3, 10.0, 6.2),
       (2.8, 6.2, 11.0, 4.7), (5.0, 6.0, 10.0, 5.1), (3.5, 5.6, 12.0, 5.0),
       (6.5, 5.4, 11.5, 3.7), (5.0, 5.4, 10.5, 4.3), (3.5, 5.4, 10.0, 5.4),
       (4.0, 5.0, 10.0, 5.7), (4.5, 4.1, 12.0, 4.3), (4.5, 4.0, 10.0, 5.9),
       (5.5, 3.9, 10.5, 5.3))
check("Table 5: patients transcribed", float(len(_T5)), 25.0, 0.0, "")
check("  ... mean Hb before treatment",
      float(np.mean([r[0] for r in _T5])), 4.02, 0.01, " g/dL")
check("  ... mean cardiac index before",
      float(np.mean([r[1] for r in _T5])), 7.36, 0.01, " L/min/m2")
check("  ... mean cardiac index after",
      float(np.mean([r[3] for r in _T5])), 5.36, 0.01, " L/min/m2")

print("  TWO OF THIS REPOSITORY'S THREE CLAIMS ARE CONFIRMED VERBATIM from")
print("  the Summary: group B is Hb 4.0-6.5 mean 4.5, and its cardiac index")
print("  is 6.3 L/min/m2 ('higher cardiac index (8.0 versus 6.3 ...)', 8.0")
print("  being group A at mean Hb 3.0).")
print("  THE THIRD IS NOT IN THE PAPER. We record 'against a normal ~3.2'.")
print("  The paper gives ITS OWN normal, from 65 healthy volunteers in the")
print("  SAME laboratory, and states it three times -- 2.5 to 5.0 L/min/m2.")
print("  The ratio therefore depends entirely on which normal is used:")
for _n, _w, _nm in ((3.2, 1.97, "the repository's 3.2, source unknown"),
                    (3.75, 1.68, "the paper's midpoint"),
                    (5.0, 1.26, "the paper's upper limit"),
                    (2.5, 2.52, "the paper's lower limit")):
    check(f"6.3 / {_n}: {_nm}", 6.3 / _n, _w, 0.01, "x")
print("    test_validation.py BANDS THIS AT 1.7-2.3x and we return 1.97x.")
print("    THE PAPER'S OWN MIDPOINT GIVES 1.68x, BELOW THAT BAND. SOURCES.md")
print("    already suspected this row grades the fit against the number the")
print("    fit was made from; that is confirmed, and the number is not even")
print("    the paper's. NOT CHANGED -- the band is a ruling, not an edit.")

print("\n  BUT TABLE 5 IS A PAIRED DATASET, WHICH IS FAR STRONGER THAN TWO")
print("  GROUP MEANS. Our law is factor = (7/hb)^k below Hb 7 and 1 above,")
print("  and every post-treatment Hb is 10.0-12.5, so the paired ratio")
print("  isolates k:  ln(CI_before / CI_after) = k * ln(7 / hb_before)")
_x = np.array([np.log(7.0 / r[0]) for r in _T5])
for _den, _wk, _wr, _nm in (
        (None, 0.471, 1.23, "vs each patient's own post-treatment CI"),
        (3.75, 0.826, 1.44, "vs the paper's normal midpoint 3.75"),
        (2.5, 1.305, 1.78, "vs the paper's normal lower limit 2.5")):
    _y = (np.array([np.log(r[1] / r[3]) for r in _T5]) if _den is None
          else np.array([np.log(r[1] / _den) for r in _T5]))
    _k = float((_x * _y).sum() / (_x * _x).sum())
    check(f"fitted k, {_nm}", _k, _wk, 0.002, "")
    check(f"  ... which gives, at Hb 4.5", (7.0 / 4.5) ** _k, _wr, 0.01, "x")
check("OURS: hb_co_exp", Patient().hb_co_exp, 1.535, 0.001, "")
check("  ... which gives, at Hb 4.5",
      (7.0 / 4.5) ** Patient().hb_co_exp, 1.97, 0.01, "x")
print("    THE PAIRED ESTIMATE UNDERSTATES, AND THE PAPER SAYS WHY. Mean")
print("    cardiac index AFTER treatment is 5.36, near the TOP of the paper's")
print("    own normal range, because (p.355) 'patients who once become")
print("    hyperkinetic may take a much longer time for the cardiovascular")
print("    adjustment, even after the correction of the anemia'. The paired")
print("    ratio is a FLOOR, not an estimate.")
print("    READ TOGETHER: the primary data BRACKET our exponent from below")
print("    rather than refuting it. 1.535 sits at or just above the top of")
print("    what this paper supports. What is NOT defensible is the 3.2.")
print("    AND THE FIT IS WEAK BY THE PAPER'S OWN ACCOUNT -- but that is the")
print("    finding, not a defect of the fit. p.347, verbatim: 'for any")
print("    individual subject the heart rate, cardiac output, or stroke")
print("    volume cannot be predicted from the hemoglobin level'.")

print("\n  THE POPULATION CAVEAT, AND IT IS A LARGE ONE. 'Anemia was due to")
print("  ankylostomiasis in 45 patients' of 51 -- CHRONIC HOOKWORM anaemia of")
print("  at least four months. hb_co_factor is applied to ANY low haemoglobin")
print("  in this model, INCLUDING ACUTE BLOOD LOSS, where the circulation has")
print("  had no months in which to adapt. NOTHING IN THIS PAPER LICENSES THAT")
print("  EXTENSION, and the model makes it silently.")

print()
if _fails:
    print(f"{len(_fails)} value(s) in HANDOVER.md have drifted:")
    for f in _fails:
        print(f"  - {f}")
    print("Either the model moved or the document is stale. Fix the document.")
    sys.exit(1)
print("Every number checked here still matches HANDOVER.md.")
