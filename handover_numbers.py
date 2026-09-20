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
print("    cannot pass p_collapse = -50 cmH2O, an order of magnitude less.")
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
check("Laviola CICO: time to SaO2 40% (theirs ~510)", float(_t40), 502.0, 6.0,
      " s")
check("Laviola CICO: CO  (theirs 2.7 +- 0.1)", float(_lv['co'][_i]), 1.90,
      0.08, " L/min")
check("Laviola CICO: MAP (theirs 57.4 +- 2.4)", float(_lv['map'][_i]), 28.4,
      1.0, " mmHg")
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
