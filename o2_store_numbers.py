# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
o2_store_numbers.py -- regenerates every number in HANDOVER's entry on WHERE
THE OXYGEN THAT SETS A DESATURATION TIME COMES FROM, and fails if one has
drifted.

Same contract as handover_numbers.py, frc_level_numbers.py, buccal_numbers.py,
aa_numbers.py and hewlett_numbers.py: NOT in the pre-commit hook, because these
are claims about the world rather than invariants of the code, and they are
EXPECTED to move when the model is corrected. The point is that they must not
move SILENTLY.

    python3 o2_store_numbers.py

SLOW -- 799 s measured 2026-10-18, so budget about 13 minutes and run it in the
background. Four benchmark rows and the section 6 pair run at the suite's own
timestep of 0.05 s, and section 2b sweeps four timesteps down to 0.025 s. Two
earlier figures in this header were wrong and are corrected here: "~30 s" was
written before section 2b existed, and "a few minutes" was a guess that was
never timed. CLAUDE.md's table carried the same stale figure.

WHY THIS FILE EXISTS. frc_level_numbers.py section 9 costed lowering frc_ref
(the awake reference lung volume) to Hewlett 1974's measured value and found it
breaks four benchmark rows that are themselves clinical measurements. It closed
by recording an UNTESTED hypothesis: that desaturation time might depend on the
TOTAL oxygen store rather than on lung volume alone, so that frc_ref could be
standing in for oxygen the model keeps somewhere else, letting both sets of
measurements be right.

A. Heard RULED on that hypothesis 2026-10-18: THERE IS NO OTHER SIGNIFICANT
STORE OF OXYGEN. This file is what the ruling is recorded against. It does two
things the cost table could not:

  (a) it checks that the model holds the stores that DO exist -- lung gas,
      arterial blood, venous blood and tissue -- and that its oxygen
      book-keeping closes;
  (b) it shows the MECHANISM that makes the ruling bite, which is that the
      non-lung store is locked behind the saturation threshold that is itself
      the benchmark endpoint.

Published sources only. The four cohorts are copied from test_validation.py and
are Berthoud 1991 (both arms), Heard 2017 (control arm) and Stock 1989. No
number here comes from anywhere but a simulation run in this process.
"""
import math

import numpy as np

import apnoea_core as A
import bloodgas as bg
from apnoea_core import Patient, AirwayEpoch, simulate, time_to

print(A.provenance())
print()

DT = 0.05            # the suite's timestep (test_validation.py:36)
FAILED = []


def check(name, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    if not ok:
        FAILED.append(name)
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<52}{got:>9.2f}{unit}"
          f"   recorded {want}{unit}")


def content(sat_pct, po2, hb):
    """Blood oxygen content, mL per dL -- the model's own form.

    apnoea_core.py builds content as HUFNER * hb * saturation + O2_SOL * PO2
    and inverts exactly that at line 2395. rec['sao2'] and rec['svo2'] are
    recorded as PERCENTAGES (lines 2920, 2923), so they are converted back to
    fractions here. Getting that wrong inflates every blood figure a
    hundredfold, and the mass balance below is what catches it.
    """
    return bg.HUFNER * hb * (sat_pct / 100.0) + bg.O2_SOL * po2


def stores(rec, i, pt):
    """Oxygen held in each compartment at sample i, mL.

    lung  -- alveolar gas, mL STPD, as the model itself records it.
             rec['lung_o2'] is n[:, 0].sum() (line 2927), so it covers the
             alveolar compartments ONLY and excludes anatomical dead space.
    art   -- arterial blood: content x v_art (1.0 L) x 10 dL/L.
    ven   -- venous blood: content x v_ven (2.0 L).
    tis   -- tissue: content x v_tis_o2 (1.5 L). The tissue compartment is
             initialised to the venous content and both gives and takes.
    """
    ca = content(rec['sao2'][i], rec['pao2'][i], pt.hb)
    cv = content(rec['svo2'][i], rec['pvo2'][i], pt.hb)
    return dict(lung=float(rec['lung_o2'][i]),
                art=ca * pt.v_art * 10.0,
                ven=cv * pt.v_ven * 10.0,
                tis=cv * pt.v_tis_o2 * 10.0)


# The four rows that broke when frc_ref was lowered to Hewlett's value, with
# the configurations copied verbatim from test_validation.py.
_b_ctl_h = math.sqrt(63.0 / 23.1)
_b_obs_h = math.sqrt(123.5 / 49.0)
CASES = (
    ("Berthoud control BMI 23",
     Patient(weight=63.0, height=_b_ctl_h, age=45, hb=14, tilt_deg=0.0),
     [AirwayEpoch(1200, resistance=2, fgo2=0.21)], 0.90, 'spo2', 90.0, None),
    ("Berthoud obese BMI 49",
     Patient(weight=123.5, height=_b_obs_h, age=45, hb=14, tilt_deg=0.0),
     [AirwayEpoch(1200, resistance=2, fgo2=0.21)], 0.90, 'spo2', 90.0, None),
    ("Heard control",
     Patient(weight=105, height=1.74, age=42, hb=14, tilt_deg=30),
     [AirwayEpoch(1200, resistance=2, fgo2=0.21)], 0.80, 'spo2', 95.0, None),
    ("Stock obstructed",
     Patient(weight=70, height=1.75, age=45, hb=15.0),
     [AirwayEpoch(360, resistance=np.inf, fgo2=0.21)], 0.87, None, None, 300.0),
)

# Recorded values, every one produced by this script. Tolerances are loose
# enough to absorb timestep noise and tight enough that a real change shows.
RECORDED = {
    # name: (t_end s, FRC mL, lung held mL, blood+tissue held mL,
    #        lung held %, lung supplied %, mL across the dead-space face,
    #        residual mL, dead-space oxygen EXCESS over inspired mL)
    "Berthoud control BMI 23": (544.3, 2070, 1428, 735, 66.0, 90.9, 432, -30.4, 85.5),
    "Berthoud obese BMI 49":   (168.6,  625,  347, 730, 32.2, 68.7, 185, -45.4, 85.5),
    "Heard control":           (287.1, 1526,  909, 692, 56.8, 91.3, 294, -25.3, 73.1),
    "Stock obstructed":        (300.0, 2313, 1554, 789, 66.3, 99.3,   0,  -2.3, 81.8),
}

print("1. THE MODEL HOLDS FOUR OXYGEN COMPARTMENTS, AND ONLY FOUR. Declared")
print("   together at apnoea_core.py:1477-1480 and integrated at 2881-2897:")
print()
print(f"     lung gas      the alveolar array n[:, 0], sized from frc_anaes()")
print(f"     arterial      v_art      = {Patient.v_art} L")
print(f"     venous        v_ven      = {Patient.v_ven} L")
print(f"     tissue        v_tis_o2   = {Patient.v_tis_o2} L")
print(f"     (each blood compartment is split into pools = {Patient.pools} "
      f"sub-pools for transit delay)")
print()
print("   The blood and tissue volumes total "
      f"{Patient.v_art + Patient.v_ven + Patient.v_tis_o2} L of distribution")
print("   volume. A. Heard ruled 2026-10-18 that no other significant store of")
print("   oxygen exists in the patient, so THE ACCOUNTING IS COMPLETE and the")
print("   oxygen-store route to reconciling Hewlett with the clinical")
print("   desaturation times is CLOSED.")
print()

print("2. WHERE THE OXYGEN THAT SETS EACH BENCHMARK TIME ACTUALLY COMES FROM.")
print("   'held' is the store at the start of apnoea; 'supplied' is what each")
print("   compartment gave up before the benchmark's own endpoint was reached.")
print()

rows = {}
for nm, pt, epochs, feo2, key, thr, fixed_t in CASES:
    rec = simulate(pt, epochs, dt=DT, feo2_start=feo2, stop_sao2=0.0)
    s0 = stores(rec, 0, pt)
    t_end = fixed_t if fixed_t is not None else time_to(rec, key, thr)
    i_end = int(min(t_end, rec['t'][-1]) / DT)
    s1 = stores(rec, i_end, pt)

    drawn = {k: s0[k] - s1[k] for k in s0}
    supplied = sum(drawn.values())
    # cum_o2_in IS NOT OXYGEN ENTRAINED FROM THE BREATHING CIRCUIT, and reading
    # it that way was an error corrected here before this file was committed.
    # apnoea_core.py:2866 accumulates `add[0]`, and `add` is built at 2838 as
    # `add += ds[-1] * dn` -- the gas crossing the DEAD-SPACE/ALVEOLUS FACE.
    # So it books the dead space's own preoxygenated oxygen excess as though it
    # had come from the circuit: vd_anat * PDRY/GASK * (feo2 - fgo2), which is
    # 81.8 mL at a 150 mL dead space, EtO2 0.87 and room air at the lips.
    crossed = float(rec['cum_o2_in'][i_end])
    consumed = pt.vo2_anaes() * t_end / 60.0
    ds_excess = pt.vd_anat * A.PDRY / A.GASK * max(0.0, feo2 - epochs[0].fgo2)
    held_bt = s0['art'] + s0['ven'] + s0['tis']

    rows[nm] = dict(
        t_end=t_end, frc=pt.frc_anaes(), lung_held=s0['lung'], bt_held=held_bt,
        lung_held_pct=100.0 * s0['lung'] / sum(s0.values()),
        lung_supplied_pct=100.0 * drawn['lung'] / max(supplied, 1e-9),
        inflow=crossed, resid=supplied + crossed - consumed, ds=ds_excess,
        vo2=pt.vo2_anaes(), supplied=supplied, consumed=consumed)

    print(f"   --- {nm}  (BMI {pt.bmi():.1f})")
    print(f"       {t_end:6.1f} s to endpoint; FRC {pt.frc_anaes():5.0f} mL; "
          f"VO2 {pt.vo2_anaes():5.1f} mL/min")
    print(f"       HELD at t=0    lung {s0['lung']:6.0f}   art {s0['art']:4.0f}   "
          f"ven {s0['ven']:4.0f}   tis {s0['tis']:4.0f}   "
          f"total {sum(s0.values()):6.0f} mL")
    print(f"       SUPPLIED       lung {drawn['lung']:6.0f}   art {drawn['art']:4.0f}   "
          f"ven {drawn['ven']:4.0f}   tis {drawn['tis']:4.0f}   "
          f"total {supplied:6.0f} mL")
    print(f"       lung HELD {rows[nm]['lung_held_pct']:4.1f}% of the store but "
          f"SUPPLIED {rows[nm]['lung_supplied_pct']:4.1f}% of the oxygen")
    print(f"       balance: supplied {supplied:6.0f} + crossed the dead-space "
          f"face {crossed:5.0f} - consumed {consumed:6.0f} "
          f"= {rows[nm]['resid']:+6.1f} mL "
          f"({100*abs(rows[nm]['resid'])/max(consumed,1e-9):.1f}% of throughput)")
    print()

print("   Every figure above, checked against the record:")
print()
for nm in RECORDED:
    t, frc, lh, bt, lhp, lsp, inf, res, ds = RECORDED[nm]
    r = rows[nm]
    check(f"{nm}: time to endpoint", r['t_end'], t, 0.6, " s")
    check(f"{nm}: anaesthetised FRC", r['frc'], frc, 2.0, " mL")
    check(f"{nm}: lung oxygen held", r['lung_held'], lh, 4.0, " mL")
    check(f"{nm}: blood+tissue held", r['bt_held'], bt, 4.0, " mL")
    check(f"{nm}: lung % of store held", r['lung_held_pct'], lhp, 0.5, " %")
    check(f"{nm}: lung % of oxygen supplied", r['lung_supplied_pct'], lsp, 0.5, " %")
    check(f"{nm}: crossed the dead-space face", r['inflow'], inf, 4.0, " mL")
    check(f"{nm}: mass-balance residual", r['resid'], res, 3.0, " mL")
    check(f"{nm}: dead-space excess over inspired", r['ds'], ds, 0.3, " mL")
print()

print("2b. WHAT THE RESIDUAL IS, AND WHAT IT IS NOT. The accounting above")
print("    reproduces oxygen consumption to within 1.5-3.9% of throughput, so")
print("    there is no large leak. But the residual does NOT vanish as the")
print("    timestep shrinks -- it CONVERGES -- so it is structural, not")
print("    discretisation. Over a fixed 500 s window in the Berthoud control:")
print()
_bh = math.sqrt(63.0 / 23.1)
_bp = Patient(weight=63.0, height=_bh, age=45, hb=14, tilt_deg=0.0)


def _total(rec, i, pt):
    s = stores(rec, i, pt)
    return s['lung'] + s['art'] + s['ven'] + s['tis']


_prev, _ratios, _last = None, [], None
print("        dt      residual    ratio to previous")
for _dt in (0.2, 0.1, 0.05, 0.025):
    _r = simulate(_bp, [AirwayEpoch(520, resistance=2, fgo2=0.21)],
                  dt=_dt, feo2_start=0.90, stop_sao2=0.0)
    _i = int(500.0 / _dt)
    _res = (_total(_r, 0, _bp) - _total(_r, _i, _bp)
            + float(_r['cum_o2_in'][_i]) - _bp.vo2_anaes() * 500.0 / 60.0)
    _rt = "" if _prev is None else f"{_res / _prev:8.3f}"
    if _prev is not None:
        _ratios.append(_res / _prev)
    print(f"      {_dt:6.3f}  {_res:+10.3f} mL  {_rt}")
    _prev, _last = _res, _res
print()
check("residual at the finest timestep", _last, -10.43, 0.15, " mL")
check("last halving ratio (1.0 = converged, 0.5 = first order)",
      _ratios[-1], 1.023, 0.03, " x")
print()
print("    A FIRST-ORDER ERROR WOULD HALVE ON EACH HALVING. These ratios run")
print("    1.11, 1.05, 1.02 -- toward one, not one half -- so about 10 mL of")
print("    this is real and dt-independent.")
print()
print("    THE LEADING CANDIDATE IS THE DEAD SPACE, AND IT IS NOT CONFIRMED.")
print("    cum_o2_in is the flux across the dead-space/alveolus face, not")
print("    oxygen entrained from the breathing circuit (apnoea_core.py:2866")
print("    accumulates `add[0]`, and `add` is built from `ds[-1] * dn` at")
print("    2838). So the dead space's own preoxygenated excess is booked on the")
print("    INFLOW side of this balance -- at a 150 mL dead space, EtO2 0.87 and")
print("    room air at the lips that is exactly")
print(f"    150 * PDRY/GASK * (0.87 - 0.21) = "
      f"{150.0 * A.PDRY / A.GASK * (0.87 - 0.21):.2f} mL -- while never")
print("    appearing on the STORE side, because rec['lung_o2'] records the")
print("    alveolar compartments only. That asymmetry is the obvious home for a")
print("    dt-independent offset of this size and sign, but it has NOT been")
print("    pinned down to the millilitre and is recorded as open, not solved.")
print()
print("    NONE OF THIS TOUCHES SECTION 3. The held-and-supplied shares below")
print("    are computed from compartment contents directly and never read the")
print("    balance. The balance's job here was to catch a units error, and it")
print("    did: an early draft of this file treated the recorded saturations as")
print("    fractions when they are percentages, inflating every blood figure a")
print("    hundredfold, and the balance is what exposed it.")
print()

print("3. THE MECHANISM: THE NON-LUNG STORE IS LOCKED BEHIND THE ENDPOINT.")
print("   In every row the lung supplies a LARGER share of the oxygen than it")
print("   holds, and in three of four it supplies over 90% while holding under")
print("   two-thirds:")
print()
print("                              held by lung    supplied by lung")
for nm in RECORDED:
    r = rows[nm]
    print(f"     {nm:<26}{r['lung_held_pct']:9.1f}%{r['lung_supplied_pct']:16.1f}%")
print()
print("   THE REASON IS THE ENDPOINT ITSELF. Every one of these benchmarks")
print("   stops its clock at a SATURATION threshold -- SpO2 90% for Berthoud,")
print("   95% for Heard. Haemoglobin does not give up its oxygen until")
print("   saturation falls, so the blood and tissue store cannot be drawn on")
print("   until the clock has ALREADY stopped. The ~700-790 mL sitting in blood")
print("   and tissue is real, and the ruling is right that nothing else exists,")
print("   but almost none of it is available on the near side of the endpoint.")
print()
print("   Stock is the limiting case and proves the point from the other end:")
print("   the trachea is clamped, so there is no inflow at all, saturation")
print("   barely moves across the 5-minute window, and the lung supplies")
print(f"   {rows['Stock obstructed']['lung_supplied_pct']:.1f}% of the oxygen "
      f"consumed. Of the 789 mL held in blood")
print("   and tissue, that row draws 9 mL. This is why Stock's PaO2 row is the")
print("   most frc_ref-sensitive in the suite: it is very nearly a pure")
print("   measurement of lung gas.")
print()

print("4. WHAT THIS SETTLES. Lung volume is effectively the whole lever on a")
print("   desaturation time in this model, not because the other stores are")
print("   missing or mis-sized, but because they are unreachable before the")
print("   endpoint. So there is no slack anywhere for frc_ref to be trading")
print("   against: lowering it by the ~515 mL that separates Watson & Pride")
print("   from Hewlett removes oxygen directly from the only supply that")
print("   matters. That is the MECHANISM behind the monotonic cost already")
print("   measured in frc_level_numbers.py section 9, and it means the cost")
print("   was not an artefact of the benchmark set.")
print()
print("   THE OXYGEN-STORE HYPOTHESIS IS THEREFORE CLOSED, on the ruling plus")
print("   this decomposition. frc_ref is still not to be moved, and there is")
print("   now no store-side route by which Hewlett's awake volumes and these")
print("   four clinical desaturation times could both be reproduced.")
print()

print("5. WHAT THIS DOES *NOT* SETTLE, recorded so it is not mistaken for part")
print("   of the ruling. The blood and tissue stores DO NOT SCALE WITH THE")
print("   PATIENT. v_art, v_ven and v_tis_o2 are plain constants and nothing")
print("   multiplies them by weight, height, body surface area or lean body")
print("   mass, so the two Berthoud arms -- 63.0 kg and 123.5 kg, a 96%")
print("   difference in body weight -- are given stores of")
print(f"   {rows['Berthoud control BMI 23']['bt_held']:.0f} mL and "
      f"{rows['Berthoud obese BMI 49']['bt_held']:.0f} mL, which differ by "
      f"{abs(rows['Berthoud obese BMI 49']['bt_held'] / rows['Berthoud control BMI 23']['bt_held'] - 1) * 100:.1f}%")
print("   -- and differ at all only through haemoglobin and saturation, not")
print("   through size. The lung store meanwhile falls from 1428 to 347 mL")
print("   across the same pair, so the blood share rises from 34% to 68%")
print("   entirely because the lung shrank.")
print()
print("   WHETHER THAT IS WRONG IS NOT ESTABLISHED HERE AND MUST NOT BE GUESSED.")
print("   How total blood volume ought to vary with body size is NOT settled by")
print("   anything held in this repository: no measurement of blood volume")
print("   against weight, lean mass or body surface area is in SOURCES.md, and")
print("   this project's history is that supplying such a figure from memory")
print("   produces retractions. So the direction of any correction is left")
print("   OPEN here rather than asserted. Section 3 also shows the quantity")
print("   is nearly inert on these endpoints -- the obese arm draws 60 mL of")
print("   arterial oxygen in total -- so a plausible correction would move")
print("   little. Recorded as an unanchored constant, not as a defect, and")
print("   needing a held measurement of blood volume against body size before")
print("   anything is done. It is NOT a candidate for the awake-FRC conflict:")
print("   a larger obese blood store would lengthen the obese arm, which")
print("   already passes, and would not touch Stock at all.")
print()

print("6. TWO DEFECTS IN THE OXYGEN BOOK-KEEPING, FOUND WHILE CHECKING THE")
print("   RULING AND VERIFIED HERE. Neither changes the ruling and neither")
print("   props up the four blocking rows -- which is itself the point, and is")
print("   why they are recorded rather than acted on.")
print()
print("   (a) THERE IS NO OXYGEN MASS-BALANCE INVARIANT. The carbon-dioxide")
print("       side records its stores explicitly (the 'co2_stores' series) and")
print("       bands the residual tightly. The oxygen side records no store at")
print("       all: there is no 'o2_stores' key anywhere in the tracked files.")
print("       test_validation.py:1219-1226 instead INFERS the blood-and-tissue")
print("       term as a residual and bands it -200 to +900 mL -- a window")
print("       1100 mL wide against a store that is only about 700 mL.")
print()
print("   (b) THE ONE CHECK NEVER VISITS THE REGIME THAT MATTERS, AND FAILS")
print("       THERE WHEN IT DOES. It runs a patent 100%-oxygen case that never")
print("       desaturates. The same expression on a desaturating run exceeds")
print("       its own ceiling, and then exceeds the entire store the patient")
print("       ever had, because oxygen consumption is a constant subtracted")
print("       unconditionally and the tissue compartment is unbounded below.")
print()

_pc = Patient(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)


def _balance(rec, i, pt):
    """test_validation.py:1220-1221's own expression, evaluated at sample i."""
    return (pt.vo2_anaes() * rec['t'][i] / 60.0
            - (rec['lung_o2'][0] - rec['lung_o2'][i])
            - rec['cum_o2_in'][i])


_r_chk = simulate(_pc, [AirwayEpoch(600, resistance=2, fgo2=1.00)],
                  dt=DT, feo2_start=0.87, stop_sao2=0.0)
_r_des = simulate(_pc, [AirwayEpoch(1200, resistance=2, fgo2=0.21)],
                  dt=DT, feo2_start=0.87, stop_sao2=0.0)
_i_chk = len(_r_chk['t']) - 1
_s0 = stores(_r_des, 0, _pc)
_bt0 = _s0['art'] + _s0['ven'] + _s0['tis']
_t90 = time_to(_r_des, 'spo2', 90)
_i90 = int(_t90 / DT)
_peak = max(_balance(_r_des, i, _pc) for i in range(len(_r_des['t'])))
_cross = next((_r_des['t'][i] for i in range(1, len(_r_des['t']))
               if _balance(_r_des, i, _pc) > _bt0), None)
_spo2_cross = (float(np.interp(_cross, _r_des['t'], _r_des['spo2']))
               if _cross is not None else float('nan'))

print("   Measured, on the very patient the check uses "
      "(107 kg, 1.75 m, 45 y, Hb 14, tilt 25):")
print()
check("check as the suite runs it (patent, 100% O2)",
      _balance(_r_chk, _i_chk, _pc), -13.4, 1.5, " mL")
check("  ... SpO2 it ends at, so the store never moves",
      float(_r_chk['spo2'][_i_chk]), 99.7, 0.3, " %")
check("same expression, desaturating: peak residual", _peak, 948.5, 3.0, " mL")
check("  ... against the ceiling it is banded at", 900.0, 900.0, 0.0, " mL")
check("blood+tissue store the patient ever had", _bt0, 704.4, 3.0, " mL")
check("residual at the SpO2 90% endpoint", _balance(_r_des, _i90, _pc),
      180.7, 3.0, " mL")
check("  ... store still held at that endpoint", stores(_r_des, _i90, _pc)['art']
      + stores(_r_des, _i90, _pc)['ven'] + stores(_r_des, _i90, _pc)['tis'],
      566.0, 3.0, " mL")
check("residual first exceeds the WHOLE store at", _cross, 447.2, 1.0, " s")
check("  ... SpO2 at that moment", _spo2_cross, 38.7, 0.6, " %")
print()
print("   READ THE LAST TWO LINES CAREFULLY. The model begins supplying oxygen")
print("   it does not have only once saturation is under 40%, and every graded")
print("   endpoint in section 2 sits far above that: SpO2 90% is reached with")
print(f"   {_balance(_r_des, _i90, _pc):.0f} mL claimed against "
      f"{_bt0:.0f} mL available, comfortably inside the store.")
print("   SO THE FOUR ROWS THAT BLOCK THE frc_ref MOVE ARE NOT GRADED ON")
print("   PHANTOM OXYGEN, and section 4's conclusion stands independently of")
print("   this defect. Below SpO2 60-70% the model is in any case documented as")
print("   invalid -- see plateau_sao2()'s CAVEAT, which states that oxygen")
print("   consumption and cardiac output are assumed constant and that both")
print("   assumptions fail there. What is NOT currently true is that the suite")
print("   encodes that boundary: the oxygen check's band does not express it,")
print("   and the check never runs where it would bite.")
print()
print("   NEITHER IS FIXED HERE. Clamping the tissue compartment or adding an")
print("   oxygen invariant would change model behaviour or turn the suite red,")
print("   and both need a ruling first. Recorded as open.")
print()

if FAILED:
    print(f"{len(FAILED)} value(s) have drifted:")
    for f in FAILED:
        print(f"  - {f}")
    raise SystemExit(1)
print("Every oxygen-store number still reproduces from this commit.")
