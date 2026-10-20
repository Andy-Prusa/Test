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

A. Heard ASKED, 2026-10-18: is there any other significant store of oxygen?
This file is the working toward an answer. An earlier version of this header
recorded that question as a RULING that no other store exists, which it was
not; the mis-attribution is corrected here rather than quietly reworded,
because everything below was written as though the question had been settled.

It does two things the cost table could not:

  (a) it decomposes the stores the model DOES have -- lung gas, arterial
      blood, venous blood and a compartment named tissue -- and shows what
      each actually supplies before a benchmark's endpoint;
  (b) it computes the one further store it CAN compute -- physically
      dissolved oxygen -- and finds it negligible.

Section 7 records how the question was disposed of: NOT by being answered.
A. Heard decided on 2026-10-18 not to pursue it, after this agent proposed
myoglobin-bound oxygen as a candidate store on no source held anywhere. The
physiology is NOT settled and section 7 says so.

Published sources only. The four cohorts are copied from test_validation.py and
are Berthoud 1991 (both arms), Heard 2017 (control arm) and Stock 1989. No
number here comes from anywhere but a simulation run in this process.
"""
import math
import re

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


def check_src(name, got, want):
    """check() for a fragment of source text rather than a number.

    Added 2026-10-20 when the numeric version below could no longer work: the
    thing being guarded stopped being a literal.
    """
    ok = (got == want)
    if not ok:
        FAILED.append(name)
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<52}{got!r:>14}"
          f"   recorded {want!r}")


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

# Quoted in HANDOVER's fifty-second entry, so recorded here: the oxygen each
# row actually supplies (section 7 uses the range as its denominator) and the
# arterial draw (quoted for Stock's 9 mL and the obese arm's 60 mL).
SUPPLIED = {"Berthoud control BMI 23": 1457.0, "Berthoud obese BMI 49": 473.0,
            "Heard control": 913.0, "Stock obstructed": 1159.0}
ART_DRAWN = {"Berthoud control BMI 23": 55.0, "Berthoud obese BMI 49": 60.0,
             "Heard control": 42.0, "Stock obstructed": 9.0}

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
print("   volume. WHETHER THAT IS THE WHOLE OF THE PATIENT'S OXYGEN IS NOT")
print("   ESTABLISHED HERE -- section 7. What the code shows is that the")
print("   compartment NAMED tissue is not a tissue store:")
print("   its state variable is a blood oxygen content in mL per decilitre, so")
print("   the model carries 4.5 L of blood-like fluid and NO tissue-phase")
print("   oxygen at all.")
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
        vo2=pt.vo2_anaes(), supplied=supplied, consumed=consumed,
        art_drawn=drawn['art'])

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
    check(f"{nm}: total oxygen supplied", r['supplied'], SUPPLIED[nm], 4.0, " mL")
    check(f"{nm}: arterial oxygen drawn", r['art_drawn'], ART_DRAWN[nm], 2.0, " mL")
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
for _i, _want in enumerate((1.110, 1.049, 1.023)):
    check(f"halving ratio {_i + 1} (1.0 = converged, 0.5 = first order)",
          _ratios[_i], _want, 0.03, " x")
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
print("   saturation falls, so most of the blood and tissue store is still")
print("   there when the clock stops. NOT ALL OF IT: read the table above and")
print("   the obese row draws 31.3% of its oxygen from blood and tissue before")
print("   its endpoint, about 150 mL. An earlier draft of this file said that")
print("   store 'cannot be drawn on until the clock has already stopped',")
print("   which its own table contradicts. What is true is the weaker and")
print("   still decisive statement: blood and tissue hold 34-68% of the oxygen")
print("   and supply only 1-31% of what is drawn.")
print()
print("   Stock is the limiting case and proves the point from the other end:")
print("   the trachea is clamped, so there is no inflow at all, saturation")
print("   barely moves across the 5-minute window, and the lung supplies")
print(f"   {rows['Stock obstructed']['lung_supplied_pct']:.1f}% of the oxygen "
      f"consumed. Of the 789 mL held in blood")
print(f"   and tissue, that row draws {rows['Stock obstructed']['art_drawn']:.0f}"
      f" mL. This is why Stock's PaO2 row is the")
print("   most frc_ref-sensitive in the suite: it is very nearly a pure")
print("   measurement of lung gas.")
print()

print("4. WHAT THIS SETTLES. Lung volume is effectively the whole lever on a")
print("   desaturation time in this model, not because the other stores are")
print("   missing or mis-sized, but because they are unreachable before the")
print("   endpoint. So there is no slack anywhere for frc_ref to be trading")
print("   against: lowering it by the 516-535 mL that separates Watson & Pride")
print("   from Hewlett's two cohorts removes oxygen from the only supply that")
print("   matters. That is the MECHANISM behind the monotonic cost already")
print("   measured in frc_level_numbers.py section 9, and it means the cost")
print("   was not an artefact of the benchmark set.")
print()
print("   THE OXYGEN-STORE HYPOTHESIS IS CLOSED FOR SCOPE, not because the")
print("   physiology was settled -- see section 7, which is blunt about it.")
print("   Within the stores the model HAS, it is closed on this table. frc_ref")
print("   still not to be moved, and that conclusion does not depend on this")
print("   file at all: it rests on the cost table in frc_level_numbers.py")
print("   section 9, where the rows that break are themselves measurements.")
print("   What this file adds is why that cost is mechanism rather than")
print("   coincidence. For the record, there is no store-side route WITHIN THE")
print("   MODEL AS IT STANDS by which Hewlett's awake volumes and these")
print("   four clinical desaturation times could both be reproduced.")
print()

print("5. WHAT THIS DOES *NOT* SETTLE, recorded separately so it is not taken")
print("   for part of the above. The blood and tissue stores DO NOT SCALE WITH")
print("   THE")
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
print("   THE DIRECTION IS NOW ESTABLISHED, WHICH IT WAS NOT WHEN THIS SECTION")
print("   WAS WRITTEN. Until 2026-10-20 this paragraph said that no measurement")
print("   of blood volume against weight, lean mass or body surface area was")
print("   held, and left the direction of any correction OPEN on that ground.")
print("   THAT IS NO LONGER TRUE. Feldschuh & Enson, Circulation 1977;56:605-12,")
print("   was read in full from upload on 2026-10-20: 188 observations in 160")
print("   normal volunteers from -38.7% to +210.8% of desirable weight, with")
print("   blood volume regressed on weight and on surface area by sex. The")
print("   numbers and their limits are in bloodvol_numbers.py; the short form is")
print("   that BOTH sexes' weight regressions put a 123.5 kg adult between 5.80")
print("   and 6.39 L against this model's 4.5 L, so the obese arm is 1.30-1.89 L")
print("   LOW and the sign of the correction no longer depends on a guess.")
print()
print("   WHAT IS STILL OPEN IS THE SIZE OF THE EFFECT, NOT ITS SIGN. That extra")
print("   blood is 248-360 mL of oxygen at arterial content -- the same order as")
print("   the whole 347 mL anaesthetised lung at this arm -- so the earlier")
print("   wording that 'a plausible correction would move little' is NOT safe and")
print("   has been withdrawn -- and NOT replaced with a different guess. Against")
print("   the store figure, section 2 above measures this arm as holding 730 mL")
print("   in blood and tissue and SUPPLYING only 148 mL of it before SpO2 90%,")
print("   about a fifth, so at fixed fractional depletion a 22-30% larger store")
print("   would yield only ~33-44 mL more oxygen. But depletion is not fixed: a")
print("   larger store falls more slowly, lengthening the time and raising the")
print("   draw again. Nothing here settles it; only a variant_cost.py run can.")
print("   Still NOT a candidate for the awake-FRC conflict, for the unchanged")
print("   reason that a larger obese blood store would lengthen the obese arm,")
print("   which already passes, and would not touch Stock at all.")
print()

print("6. TWO DEFECTS IN THE OXYGEN BOOK-KEEPING, found while working out where")
print("   this model keeps its oxygen, and verified here. Neither props up the")
print("   four blocking rows -- which is itself the point, and is why they are")
print("   recorded rather than acted on.")
print()
print("   (a) THERE IS NO OXYGEN MASS-BALANCE INVARIANT. The carbon-dioxide")
print("       side records its stores explicitly (the 'co2_stores' series) and")
print("       bands the residual tightly. The oxygen side records no store at")
print("       all: there is no 'o2_stores' key anywhere in the tracked files.")
print("       test_validation.py's test_physical_consistency instead INFERS")
print("       the blood-and-tissue term as a residual.")
print()
print("       THE BAND HALF OF THIS WAS FIXED ON 2026-10-19, THE DAY AFTER IT")
print("       WAS WRITTEN. It read -200 to +900 mL, 1100 mL wide against a")
print("       store of about 700 mL. A. Heard asked what made that a plausible")
print("       blood store, which found the error -- +900 exceeded the whole")
print("       store by 28% and would have passed a 34% leak, while -200 was")
print("       TIGHTER than the real headroom and could have failed a run that")
print("       was behaving -- and he ruled both bounds computed. The suite now")
print("       bands the residual by what the patient actually holds, which the")
print("       checks below pin at -223.6 to +704.4 mL on this patient.")
print()
print("       WHAT IS NOT FIXED IS THE FIRST HALF. The term is still INFERRED")
print("       rather than tracked -- no explicit oxygen store series exists --")
print("       and that is exactly why defect (b) was invisible for so long.")
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
# THE CEILING IS NO LONGER A LITERAL, AND THIS CHECK FIRING IS HOW THAT WAS
# CAUGHT. Until 2026-10-19 test_validation.py bounded the residual by a
# hardcoded -200 to +900 and this line regex-read the 900 out of it, so that
# HANDOVER's "over its own 900 mL ceiling" could not rot silently. The band was
# then RULED computed (A. Heard, 2026-10-19) and the suite now bounds the
# residual by `-headroom, store0` -- the store the patient actually holds. The
# regex stopped matching, _ceiling went to nan, and the check FAILED on the
# next full run. That is precisely what it was built to do, and it is recorded
# rather than quietly deleted.
#
# WHAT REPLACES IT, and why this is stronger than the number it guarded. The
# ceiling's VALUE is already checked just below: _bt0 is the same quantity
# -- ca*v_art*10 + cv*(v_ven+v_tis_o2)*10 -- computed here through stores()
# instead of inline, so the two are independent code paths onto one bound. What
# was left unguarded is STRUCTURAL: nothing stopped either bound reverting to a
# round number, which is the failure mode the original 900 had. So the bounds
# are checked to still be EXPRESSIONS.
_tv = open("test_validation.py").read()
_m = re.search(r'check\("oxygen balance closes \(blood\+tissue term\)",\s*'
               r'balance,\s*(-?[\w.]+),\s*(-?[\w.]+)', _tv)
check_src("  ... suite's LOWER bound, from its source",
          _m.group(1) if _m else None, "-headroom")
check_src("  ... suite's UPPER bound, from its source",
          _m.group(2) if _m else None, "store0")
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

print("7. HOW THE QUESTION WAS DISPOSED OF -- NOT BY BEING ANSWERED.")
print()
print("   A. Heard asked on 2026-10-18 whether any other significant store of")
print("   oxygen exists, available for tissue delivery. Answering it, this")
print("   agent named MYOGLOBIN-BOUND OXYGEN IN MUSCLE as the large candidate.")
print("   He then asked where that had been READ. The answer was NOWHERE: it")
print("   came from background knowledge, not from any source held in this")
print("   repository or uploaded to the session. Asked whether myoglobin was")
print("   worth pursuing at all, he answered NO.")
print()
print("   SO THE ROUTE IS CLOSED FOR SCOPE, NOT BECAUSE THE PHYSIOLOGY WAS")
print("   SETTLED -- the same way the Altermatt and Valenza rows went, and the")
print("   ICSM rescue row after them: retired, not passed. What he decided is")
print("   that this is not to be pursued. He made no physiological finding, and")
print("   three successive drafts of this file wrote one for him, each time")
print("   phrased in terms of an affinity nothing here measures. Those are")
print("   withdrawn. THE QUESTION ITSELF REMAINS UNANSWERED BY THIS REPOSITORY.")
print()
print("   WHAT THE CODE AND THE ARITHMETIC DO SUPPORT, independently of any of")
print("   that:")
print()
print("   (a) THE COMPARTMENT NAMED tissue IS NOT A TISSUE STORE. From the")
print("       arithmetic at apnoea_core.py:2886 its state variable is a BLOOD")
print("       oxygen content in mL per decilitre, initialised to mixed venous.")
print("       The model carries 4.5 L of blood-like fluid and no tissue-phase")
print("       oxygen. The name misdescribes it and is worth fixing.")
print()
print("   (b) PHYSICALLY DISSOLVED OXYGEN IS NEGLIGIBLE. This is the one")
print("       candidate store whose size can be computed from constants already")
print(f"       in this model (bloodgas.O2_SOL = {bg.O2_SOL} mL/dL/mmHg). It is")
print("       computed here because it CAN be, not because it is the only")
print("       possibility:")
print()
_diss = []
for _vol, _po2, _lab in ((1.5, 40.0, "the 1.5 L the tissue compartment claims"),
                         (40.0, 40.0, "40 L of water at venous tension"),
                         (40.0, 100.0, "the same 40 L at arterial tension")):
    _mL = bg.O2_SOL * _po2 * _vol * 10
    _diss.append(_mL)
    print(f"         {_lab:44s}{_mL:7.1f} mL")
print()
print("       THE 40 L IS NOT FROM A SOURCE AND NOT FROM THE MODEL. It is an")
print("       arbitrarily generous round number, larger than any body-water")
print("       volume this model represents, chosen so the conclusion does not")
print("       depend on getting it right. Labelled rather than quietly used,")
print("       because it has the same provenance as the withdrawn myoglobin")
print("       claim: this agent's background knowledge.")
print()
print(f"       Against the {min(rows[k]['supplied'] for k in rows):.0f}-"
      f"{max(rows[k]['supplied'] for k in rows):.0f} mL each row in section 2")
print("       actually supplies, those figures are a few per cent at most --")
print("       and the model already carries the dissolved term inside its blood")
print("       compartments.")
print()
check("dissolved in 1.5 L at venous tension", _diss[0], 1.8, 0.05, " mL")
check("dissolved in 40 L at venous tension", _diss[1], 48.0, 0.5, " mL")
check("dissolved in 40 L at arterial tension", _diss[2], 120.0, 0.5, " mL")
print()
print("   (c) WHAT IS *NOT* SUPPORTED, AND WAS ASSERTED THREE TIMES ANYWAY.")
print("       That a store must be LOWER-affinity than haemoglobin to matter")
print("       here. The reasoning was that these benchmarks end at a SATURATION")
print("       threshold, so a store must release above it. The hole is that the")
print("       endpoint is ARTERIAL saturation while a muscle store would release")
print("       at TISSUE oxygen tension, and a store that offloads locally")
print("       reduces the draw on arterial blood -- so it could slow arterial")
print("       desaturation while arterial saturation is still high. The argument")
print("       treated one tension as the other. This is NOT a claim that")
print("       myoglobin does that; nothing here measures it either way. It is")
print("       the reason the converse must not be asserted.")
print()
print("   NONE OF THIS BEARS ON frc_ref, which stays at 2860 on the cost table")
print("   in frc_level_numbers.py section 9, where the four rows that break are")
print("   themselves clinical measurements. This file explains WHY that cost is")
print("   mechanism rather than coincidence. It was never the reason for the")
print("   conclusion, and nothing in section 7 changes it either way.")
print()

if FAILED:
    print(f"{len(FAILED)} value(s) have drifted:")
    for f in FAILED:
        print(f"  - {f}")
    raise SystemExit(1)
print("Every oxygen-store number still reproduces from this commit.")
