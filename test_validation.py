# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
test_validation.py — every benchmark this model has been checked against,
as executable tests.

RUN:  python3 test_validation.py          (plain, no pytest needed)
      pytest test_validation.py -v        (if you prefer)

The point of this file is that any future change either passes or does not.
During development several changes silently broke earlier agreements and were
only caught by re-running things by hand; that should not be possible again.

TWO CLASSES OF TARGET, and they are not equal:
  CLINICAL  - measurements in patients. These are the arbiters.
  MODEL     - other people's simulations. Useful comparators, not truth.

Where a target is a median with an interquartile range, the test asserts the
model lands inside the IQR, not on the median. Where it is a mean with an SD,
the test allows two SD. Anything tighter would be fitting to noise.

EXIT STATUS: check() deliberately does not raise, so that one run reports every
benchmark rather than stopping at the first failure. The process therefore has
to signal failure some other way, and it must, because the pre-commit hook in
.githooks/ gates on it: __main__ exits 1 if anything failed, and under pytest
the sentinel test at the foot of the file carries the same verdict.
"""
import sys

import numpy as np
from apnoea_core import (Patient, AirwayEpoch, simulate, time_to,
                          PB, PH2O)
import bloodgas as bg

DT = 0.05          # dt=0.1 is stable but the nadir does not converge until 0.05
OBS = np.inf
KPA = 7.50062
FAILURES = []
REGRESSIONS = []

# ---------------------------------------------------------------------------
# KNOWN OPEN FAILURES -- the baseline, carrying the VALUE not just the name.
#
# Recorded 2026-09-22 when Stock 1989 was made the arbiter and his OXYGEN
# channel was graded for the first time. Grading it was correct and it put two
# large, real disagreements into the suite that nobody can pass today. Without
# this table the pre-commit hook would block every commit from here on, every
# commit would go in with --no-verify, and a gate that is always bypassed is
# not a gate -- it is a twenty-minute delay. That is how a suite dies.
#
# THE VALUE IS THE POINT. A baseline holding only NAMES is a mute button: the
# row could rot arbitrarily far and nothing would notice. Holding the value
# means the hook still blocks if a known failure gets WORSE, and says so if it
# gets BETTER, so an improvement is a visible event rather than a silent one.
#
# RULES, so this cannot become a dumping ground:
#   1. A row goes in ONLY by written ruling, never to make a red suite green.
#   2. Each row carries the value on the day it was ruled and why it is open.
#   3. A row that starts passing must be REMOVED, not left to rot. The hook
#      prints an explicit instruction when that happens.
#   4. A NEW failure is never covered by this table. It blocks.
#
# tolerance: how far a known failure may drift before it counts as a
# regression. Set from what the number does under ordinary parameter work, not
# from what would be convenient.
KNOWN_OPEN = {
    # CORRECTED 2026-09-26 on a ruling, from 4.60 to 1.94. THE OLD VALUE WAS
    # MEASURED ON THE WRONG COMMIT. Proven, not inferred: a full suite run at
    # c12b22f -- the PARENT of 4579c4e, the V/Q category-error fix whose own
    # ruling recorded this baseline -- gives exactly 4.6, and every commit from
    # 4579c4e forward gives 1.9-2.0. Nine suite runs in nine worktrees, and
    # test_validation.py is byte-identical across the whole window, so the
    # checks cannot be what moved.
    #
    # So the 2026-09-22 ruling took the NAMES from after the fix and the VALUES
    # from before it. The tell is "ICSM jet, PaO2 at cricothyroidotomy", which
    # PASSES at c12b22f and fails after: the names were right. This row has
    # therefore been reporting [WORSE] since the day it was written, and the
    # hook has blocked every commit on that basis for four days.
    #
    # A NOTE ON THE TOLERANCE, left at 0.40 deliberately. It is now 21% of the
    # value rather than 9%, which is looser than it looks -- but retightening it
    # in the same edit that moves the value would be two changes at once, and
    # the honest number to set it from is what this output does under ordinary
    # parameter work. That is currently NOTHING: see the lever sweep in
    # handover_numbers.py, where tau_mix, vq_log_sd, crs and rv all leave this
    # slope at 1.94. Until that inertness is diagnosed there is no defensible
    # basis for a tighter figure, and inventing one would be tuning.
    "Stock obstructed, 1-5 min slope":
        (1.94, 0.40, "the a-A CO2 gap under obstruction; located, not fixed. "
                     "See HANDOVER 'Where the Stock residual actually lives'"),
    # REMOVED 2026-09-22, BECAUSE THEY NOW PASS. Rule 3 at the head of this
    # table says a row that starts passing must come out rather than be left
    # to rot, and the harness printed the instruction to do so. They were:
    #   Stock obstructed, PaO2 at 5 min    61.0 mmHg   now 157.0, band 140-488
    #   Stock obstructed, SaO2 at 5 min    85.3 %      now  99.1, band 92-100
    # Fixed by correcting vq_distribution(), which had been allocating gas
    # VOLUME using the V/Q RATIO -- a ratio of two flows. See apnoea_core.py.
    # The PaO2 row passes at the BOTTOM EDGE of its band, 157 against a
    # central 314, and about 139 mmHg of alveolar-to-arterial gradient is
    # still unexplained at zero shunt. Passing is not the same as solved.
    # CORRECTED 2026-09-26 on the same ruling and for the same reason, 71.7 ->
    # 53.8. c12b22f gives 71.7 to the digit; everything after it gives 53.8-54.1.
    "ICSM jet, PaCO2 at cricothyroidotomy":
        (53.8, 3.0, "rides the same CO2 limb as the Stock slope. MODEL "
                    "comparator, and Laviola's simulator has no V/Q "
                    "distribution, so it cannot arbitrate either way"),
}


def check(name, value, lo, hi, units="", source=""):
    ok = lo <= value <= hi
    if ok:
        tag = "PASS"
        if name in KNOWN_OPEN:
            tag = "FIXED"
            REGRESSIONS.append(
                f"{name}: now PASSES at {value:.2f}. Remove it from "
                f"KNOWN_OPEN in test_validation.py -- a baseline row that "
                f"has started passing must not be left to rot.")
    elif name in KNOWN_OPEN:
        was, tol, _why = KNOWN_OPEN[name]
        if abs(value - was) <= tol:
            tag = "OPEN"
        else:
            tag = "WORSE"
            REGRESSIONS.append(
                f"{name}: {value:.2f}, was {was:.2f} at the ruling "
                f"(tolerance {tol:.2f}). A known failure got worse.")
            FAILURES.append(name)
    else:
        tag = "FAIL"
        FAILURES.append(name)
    print(f"  [{tag}] {name:44s} {value:8.1f}{units:>8}   "
          f"expect {lo:.0f}-{hi:.0f}")
    if source:
        print(f"         {source}")
    if tag == "OPEN":
        print(f"         KNOWN OPEN, was {KNOWN_OPEN[name][0]:.2f} at the "
              f"2026-09-22 ruling: {KNOWN_OPEN[name][2]}")
    return ok


def patent(pt, fg, dur=1200, feo2=0.87, dt=DT):
    return simulate(pt, [AirwayEpoch(dur, resistance=2, fgo2=fg)],
                    dt=dt, feo2_start=feo2, stop_sao2=0.0)


# =====================================================================
def test_toner_2019():
    """Toner AJ et al. Anesth Analg 2019;128:1154-9. CLINICAL.
    Healthy non-obese, prolonged laryngoscopy, supine.
    Sham 447 s (IQR 405-525); buccal 750 s (IQR 750-750), 750 s ceiling.

    PREOXYGENATION HERE IS THE 0.87 DEFAULT, NOT HEARD'S 0.80, and that is
    deliberate. Heard 2017 states an endpoint of EtO2 >= 80% and was read on
    2026-09-22, so the Heard test below uses it. TONER HAS NOT BEEN READ FOR
    A PREOXYGENATION ENDPOINT, so 0.87 stays here as the assumption it has
    always been. Do not harmonise the two: one is a figure from a paper and
    the other is a guess, and making them equal would hide which is which.
    (On 2026-09-22 an unguarded string replace did exactly that and dropped
    this benchmark from 403.4 s to 367.1 s, out of band. Caught by the
    pre-commit hook, which is what it is for.)"""
    p = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)
    t = time_to(patent(p, 0.21), 'spo2', 95)
    check("Toner sham, time to SpO2<95%", t, 380, 525, " s",
          "clinical; IQR 405-525, we allow a little below")
    tb = time_to(patent(p, 1.00), 'spo2', 95)
    check("Toner buccal, held to 750 s", 9999 if tb is None else tb,
          750, 1e9, " s", "clinical; IQR 750-750")


def test_heard_2017():
    """Heard A et al. Anesth Analg 2017;124:1162-7. CLINICAL.
    doi 10.1213/ANE.0000000000001564 (e-pub 2016 Sep 20).
    Obese BMI 30-40, ramped, prolonged laryngoscopy.
    Control 296 s (IQR 244-314); buccal 750 s (IQR 389-750).

    VERIFIED SECONDHAND 2026-09-21, and the paper is still not held. The
    figures above are confirmed by a NEJM Journal Watch commentary (Brown CA
    III, 19 Oct 2016), which quotes them exactly: "750 seconds [range,
    389-750] versus 296 seconds [range, 244-314]", n=40, BMI 30-40, and the
    same DOI. Our patient config (weight 107, height 1.75 -> BMI 34.9) sits
    mid-range. So these two bands are right.

    THE PAPER WAS OBTAINED AND READ 2026-09-22. All three questions this
    docstring used to list as "not resolvable without the paper" are now
    answered, and the configuration below is corrected to match it.

    1. IT IS AN IQR. Verbatim: "Median (interquartile range [IQR]) apnea
       times with SpO2 >= 95% were prolonged in this group; 750 (389-750)
       versus 296 (244-314) seconds". The commentary's "range" was loose.
       So 244-314 is the middle 50%, landing inside it is the STRONGER
       reading, and the band was right all along.
    2. THEIR ENDPOINT REALLY IS EtO2 >= 80%: "At the first reading of
       end-tidal oxygen (EtO2) >= 80%, buccal oxygenation was started at
       10 L/min". feo2_start is now 0.80, not the 0.87 we had granted
       ourselves.
    3. THE AIRWAY IS DELIBERATELY PARTIALLY OBSTRUCTED: laryngoscopy force
       "reduced to the minimum required to maintain a small space between
       epiglottis and posterior pharyngeal wall ... (equivalent to a grade 3
       view), thus simulating the partially obstructed airway". We still
       model it as resistance=2, the most patent setting we have. THIS ONE
       IS NOT FIXED -- it is a known over-estimate of airway patency, and it
       matters more for the buccal arm than the control arm.

    TWO DISCREPANCIES NOBODY HAD NOTICED, both now corrected. The paper
    positions patients at 30 degrees reverse Trendelenburg and we used 25.
    Its cohort is 105 +- 13 kg, 174 +- 9 cm, 42 +- 14 y and we used
    107 kg / 1.75 m / 45 y.

    THE BENCHMARK SURVIVES ALL OF IT, and the corrections very nearly
    cancel, which is why none of this showed:

        shipped, 107/1.75/45, tilt 25, feo2 0.87      289.2 s
        paper's weight/height/age only                311.6 s
        paper's tilt 30 only                          307.1 s
        paper's EtO2 0.80 only                        264.4 s
        PAPER EXACT                                   284.5 s

    Every one is inside 244-314. Read that as a warning rather than as
    reassurance: a benchmark insensitive to a 7-point change in starting
    alveolar oxygen is a weak constraint on the oxygen limb, which is the
    same conclusion the V/Q work reached from the other direction.
    """
    p = Patient(weight=105, height=1.74, age=42, hb=14, tilt_deg=30)
    t = time_to(patent(p, 0.21, feo2=0.80), 'spo2', 95)
    check("Heard control, time to SpO2<95%", t, 244, 314, " s",
          "clinical; IQR 244-314")
    tb = time_to(patent(p, 1.00, feo2=0.80), 'spo2', 95)
    check("Heard buccal, held to 750 s", 9999 if tb is None else tb,
          750, 1e9, " s", "clinical; IQR 389-750")


def test_oloughlin_2020():
    """O'Loughlin CJ et al. Anaesthesia 2020;75:1070-5. CLINICAL.
    BMI 25, age 47, INTRATRACHEAL catheter so pharyngeal fraction is
    irrelevant. Mean apnoea 18.7 min, 58/62 no significant desaturation.
    Venous PCO2 rise 0.15 (0.10) kPa/min."""
    p = Patient(weight=76, height=1.74, age=47, hb=14, tilt_deg=0)
    r = patent(p, 1.00, dur=1400, feo2=0.92)
    check("O'Loughlin SpO2 at 18.7 min",
          np.interp(1122, r['t'], r['spo2']), 95, 100, " %",
          "clinical; 58/62 completed without significant desaturation")
    rate = (np.interp(1122, r['t'], r['pvco2']) - r['pvco2'][0]) / 18.7 / KPA
    check("O'Loughlin venous PCO2 rate", rate * 1000, 50, 350, " Pa/min",
          "clinical; 0.15 (0.10) kPa/min, allow 2 SD")
    # the gradient reversal they describe, which nothing was tuned toward
    early = r['paco2'][int(5/DT)] - r['pvco2'][int(5/DT)]
    late = r['paco2'][int(600/DT)] - r['pvco2'][int(600/DT)]
    check("PaCO2-PvCO2 gradient, 5 s (venous higher)", early, -20, -1, " mmHg")
    check("PaCO2-PvCO2 gradient, 10 min (reversed)", late, 0, 12, " mmHg",
          "their stated mechanism: pulmonary CO2 retention + Haldane")


def test_stock_1989():
    """Stock MC, Schisler JQ, McSweeney TD. The PaCO2 rate of rise in
    anesthetized patients with airway obstruction. J Clin Anesth 1989;1:328-32.
    CLINICAL. 14 healthy adults, enflurane-O2, TRACHEAL TUBE CLAMPED, so this
    is complete obstruction with no fresh gas at all. A logarithmic function
    fitted the PaCO2 rise best; quoted piecewise as 12 mmHg over the first
    minute and 3.4 mmHg/min thereafter.

    This is the only benchmark here that looks at CO2 under OBSTRUCTION, and
    its absence is how the model carried an obstructed rate of rise of 41.75
    mmHg/min -- twelve times the measured value -- through every other check
    in this file. Everything else uses a patent airway, where the three
    defects behind it did not show. Do not remove it.

    The slope band is +-30% of the measured 3.4, which is the same width this
    file already allows elsewhere for a study of this size reported as a
    piecewise fit. The model sits at 4.3, near the top of it: a KNOWN residual,
    not a pass to be proud of. It is recorded in the model's own notes rather
    than tuned away, because the obvious lever -- halving the CO2 stores --
    hits 3.4 exactly while making the stores mean something other than what
    their names say.
    """
    p = Patient(weight=70, height=1.75, age=45, hb=15.0)
    r = simulate(p, [AirwayEpoch(360, resistance=OBS, fgo2=0.21)],
                 dt=DT, stop_sao2=0.0)
    g = lambda s: float(np.interp(s, r['t'], r['paco2']))
    check("Stock obstructed, first minute", g(60) - r['paco2'][0],
          9, 15, " mmHg", "clinical; 12 mmHg measured")
    check("Stock obstructed, 1-5 min slope", (g(300) - g(60)) / 4.0,
          2.4, 4.4, " mmHg/min", "clinical; 3.4 mmHg/min measured, +-30%")
    # A runaway guard, not a shape assertion. Stock's logarithmic fit implies
    # the curve decelerates; ours accelerates modestly over minutes 1-5,
    # because by then the sealed lung has lost half its volume and the rising
    # shunt is what sets arterial CO2. Which of those is right over this
    # window is not settled by anything measured here -- 14 patients fitted
    # piecewise cannot resolve the curvature -- so this checks only that the
    # late slope stays within a factor of three of the early one. That is what
    # actually failed before: the old code reached 41.75 mmHg/min.
    early, late = (g(180) - g(60)) / 2.0, (g(300) - g(180)) / 2.0
    check("PaCO2 rise does not run away", late / max(early, 1e-9),
          0.3, 3.0, " x early slope", "guard: the defect version hit 12x")

    # --- STOCK'S OXYGEN, GRADED FOR THE FIRST TIME 2026-09-22 -------------
    # Ruled on 2026-09-22: Stock is the arbiter. He was arbitrating only his
    # CO2. His OXYGEN sat in HANDOVER.md as prose for months, which is the
    # exact failure CLAUDE.md names -- numbers in markdown rot, numbers in
    # scripts do not. Both rows below fail, and they are the model's LARGEST
    # disagreement with any human measurement, larger than the CO2 slope that
    # has absorbed most of the work. They are in KNOWN_OPEN, which means they
    # are ruled open, not that they are acceptable.
    #
    # Stock Table 2, read 2026-09-14: PaO2 314 (87) mmHg at 5 min, and every
    # one of the 14 patients above 92% saturation throughout, with 7
    # completing the full 300 s.
    #
    # The PaO2 band is +-2 SD (140-488). We sit at 61, so this row fails at
    # ANY band width the measurement can justify -- widening it is not an
    # option anyone should reach for. WHAT WOULD FIX IT is in HANDOVER under
    # "Removing the V/Q spread": arterial blood is a perfusion-weighted
    # CONTENT average across a V/Q distribution, read back through a curved
    # content-to-tension relationship, and above ~150 mmHg that curve is flat
    # enough to make PaO2 hypersensitive to the weighting. Collapsing the
    # spread moves this row 61 -> 157, which is most of the defect and still
    # not all of it.
    #
    # THESE TWO ROWS ARE ONE DISAGREEMENT ON TWO SCALES, not two independent
    # findings, and must not be counted as two pieces of evidence.
    po2 = lambda s: float(np.interp(s, r['t'], r['pao2']))
    sao2 = lambda s: float(np.interp(s, r['t'], r['sao2']))
    check("Stock obstructed, PaO2 at 5 min", po2(300),
          140.0, 488.0, " mmHg", "clinical; 314 (87) measured, we allow 2 SD")
    check("Stock obstructed, SaO2 at 5 min", sao2(300),
          92.0, 100.0, " %", "clinical; every one of 14 above 92% throughout")


def test_anaemia_cardiac_response():
    """Varat, Adolph & Fowler, Am Heart J 1972;83:415-26, and Hemodynamic
    Effects of Chronic Severe Anemia, Circulation 1963;28:346. CLINICAL.

    Varat: chronic anaemia "usually increases the cardiac output when the
    haemoglobin level is 7 g/dL or less". Roy 1963: Hb 4.0-6.5 (mean 4.5)
    gave a cardiac index of 6.3 L/min/m2.

    RE-ANCHORED 2026-09-25, AND THE BAND WIDENED, after Roy was read at
    source. This row used to compare 6.3 against "a normal ~3.2" and band
    the result 1.7-2.3x. THE 3.2 IS IN NO PART OF THAT PAPER. Roy gives his
    own normal, measured on 65 healthy volunteers in the same laboratory and
    stated three times: 2.5 to 5.0 L/min/m2. So what he actually supports is

        6.3 / 5.0 = 1.26x   ...   6.3 / 2.5 = 2.52x

    and the band is now his range, not a number of ours. THE OLD BAND GRADED
    THE FIT AGAINST THE NUMBER THE FIT WAS MADE FROM -- SOURCES.md suspected
    it and the reading confirmed it. The new band is wider and therefore
    weaker, and that is the honest state of this evidence: it can no longer
    discriminate much, because the source cannot.

    The RATIO is what is tested, not the absolute cardiac index. Both
    sources measured awake patients; ours is anaesthetised and carries
    co_drop_frac, so the absolute figures are legitimately lower. Testing
    the absolute value would be testing the anaesthetic drop against awake
    data, which is not what either paper says.

    The first check is the one that matters most: at a normal haemoglobin
    this response must be exactly inert, because every other benchmark in
    this file runs Hb 14-15 and a circulation change that quietly moved the
    oxygenation results would be very hard to trust.
    """
    ref = Patient(weight=70, height=1.75, age=45, hb=15.0)
    for hb in (15.0, 14.0, 10.0, 8.0, 7.0):
        q = Patient(weight=70, height=1.75, age=45, hb=hb)
        check(f"no cardiac response at Hb {hb:.0f} (must be inert)",
              q.co_anaes() / ref.co_anaes(), 1.0, 1.0, " x",
              "Varat: the rise begins at 7 g/dL or less")
    q45 = Patient(weight=70, height=1.75, age=45, hb=4.5)
    check("cardiac output at Hb 4.5", q45.co_anaes() / ref.co_anaes(),
          1.26, 2.52, " x normal",
          "clinical; Roy 1963 CI 6.3 against HIS OWN normal range 2.5-5.0")
    # RULED 2026-09-25: Roy studied CHRONIC anaemia -- hookworm, four months
    # or more -- so the response must not fire on acute blood loss. This
    # check is what stops that extension creeping back in silently.
    q45a = Patient(weight=70, height=1.75, age=45, hb=4.5,
                   anaemia_chronic=False)
    check("ACUTE anaemia at Hb 4.5 gets no cardiac response",
          q45a.co_anaes() / ref.co_anaes(), 0.99, 1.01, " x normal",
          "ruled; Roy 1963 measured chronic anaemia only")
    # Mean arterial pressure must NOT double along with the output. Anaemic
    # patients run a normal or slightly low MAP on a markedly reduced
    # resistance; that reduction is why the output rises in the first place.
    r15 = simulate(ref, [AirwayEpoch(60, resistance=OBS, fgo2=0.21)],
                   dt=DT, stop_sao2=0.0)
    r45 = simulate(q45, [AirwayEpoch(60, resistance=OBS, fgo2=0.21)],
                   dt=DT, stop_sao2=0.0)
    check("MAP holds when the output rises", r45['map'][0] / r15['map'][0],
          0.85, 1.10, " x", "clinical; normal or slightly low MAP in anaemia")
    # The patient must be viable before the apnoea starts. Without this
    # response, Hb 4 gave a delivery-to-consumption ratio of 0.91: the
    # tissues were consuming more oxygen than they were being sent.
    q4 = Patient(weight=70, height=1.75, age=45, hb=4.0)
    do2 = q4.co_anaes() * (bg.HUFNER * 4.0 + bg.O2_SOL * 100) * 10
    check("oxygen delivery exceeds consumption at Hb 4",
          do2 / q4.vo2_anaes(), 1.5, 3.0, " x",
          "extraction ratio must stay survivable at rest")


def test_moreault_2021():
    """Moreault O, Couture EJ, Provencher S, et al. Can J Anesth
    2021;68:791-800. CLINICAL.

    A sealed human lung absorbing its own gas, with the pressure measured
    inside it. Lung isolated with a double-lumen tube or a bronchial blocker
    after ventilation at FiO2 1.0, chest closed, transducer in the
    non-ventilated bronchus. At pleural opening:

        DL-ETT   504 (85) mL resorbed;  -20 (5)  cmH2O
        BB       630 (86) mL resorbed;  -31 (10) cmH2O

    and once the pleura was opened the pressure returned toward atmospheric --
    the negative pressure exists because the chest wall resists it.

    This is the ONLY test of the mechanics limb. Until it existed the model's
    pressure under obstruction was entirely unvalidated while carrying the
    whole obstructed-airway argument, and a competing account had the lung
    staying near atmospheric. It does not: that is what this settles, and
    that is what is asserted here.

    The MAGNITUDE is a known disagreement and is deliberately not asserted.
    Compared at matched gas absorbed (their volumes were measured at
    atmospheric pressure, and the lung shrinks by less than the gas that
    leaves it because the remainder expands), doubled for a whole lung, we
    give -30.4 where they measured -20 (5) and reach the -50 floor where they
    measured -31 (10). We run 10-20 cmH2O too negative, which is the first
    evidence ever brought to bear on `stiff_below_rv` and says it is too
    stiff. Recorded under Known disagreement in HANDOVER.md rather than
    hidden inside a band wide enough to pass.

    Two caveats on the comparison. V_resorb and P_airway were measured in
    SEPARATE randomised groups, so the volume-pressure pairs are cohort means
    rather than paired observations. And doubling one lung to a whole lung is
    rough, and if anything flatters us: their isolated lung sits beside a
    contralateral lung on PEEP 5, so the mediastinum shifts toward it and
    makes its pressure LESS negative than a whole sealed thorax.
    """
    p = Patient(weight=70, height=1.75, age=45, hb=14.0)
    r = simulate(p, [AirwayEpoch(900, resistance=OBS, fgo2=0.21)],
                 dt=DT, stop_sao2=0.0)
    # gas actually gone, expressed at atmospheric pressure, as they measured it
    n_atm = r['va'] * (PB + r['palv_cmh2o'] / 1.35951 - PH2O) / (PB - PH2O)
    lost = n_atm[0] - n_atm
    i500 = int(np.argmax(lost >= 1008.0))
    check("Moreault, sealed lung goes strongly subatmospheric",
          float(r['palv_cmh2o'][i500]), -50.0, -12.0, " cmH2O",
          "clinical; -20 (5) doubled. Direction and regime only -- see docstring")
    # and it must be the chest wall doing it: the pressure has to track the
    # gas lost, not sit at some fixed value
    i250 = int(np.argmax(lost >= 500.0))
    check("Moreault, pressure tracks the gas removed",
          float(r['palv_cmh2o'][i500] - r['palv_cmh2o'][i250]), -40.0, -5.0,
          " cmH2O", "clinical; deeper absorption gives a more negative pressure")


def test_positioning_trials():
    """Lane 2005, Ramkumar 2011, Altermatt 2005, Dixon 2005. CLINICAL.
    All four found roughly +30% safe apnoea time for 20-25 deg head-up."""
    def gain(w, h, hb, tilt, thr):
        out = []
        for t in (0, tilt):
            q = Patient(weight=w, height=h, age=45, hb=hb, tilt_deg=t)
            r = simulate(q, [AirwayEpoch(1200, resistance=OBS, fgo2=0.21)],
                         dt=DT, stop_sao2=0.0)
            out.append(time_to(r, 'spo2', thr))
        return (out[1] / out[0] - 1) * 100
    check("tilt, non-obese 20 deg", gain(70, 1.75, 15, 20, 95), 15, 40, " %",
          "clinical; Lane +36%, Ramkumar +24%")
    check("tilt, BMI 35 at 30 deg", gain(95, 1.65, 14, 30, 90), 20, 45, " %",
          "clinical; Altermatt +32%")
    check("tilt, BMI 44 at 25 deg", gain(120, 1.65, 14, 25, 92), 15, 40, " %",
          "clinical; Dixon +32%")


def test_cardiac_output():
    """Sci Rep 2024 (PMC10864331). CLINICAL. n=91 anaesthetised, paralysed,
    apnoeic on 100% O2: CO 5.0 -> 6.5 L/min at 15 min, PaCO2 +2.1 mmHg/min."""
    p = Patient(weight=75, height=1.75, age=45, hb=14, tilt_deg=0)
    r = patent(p, 1.00, dur=900)
    check("cardiac output rise at 15 min",
          (r['co'][-1] / r['co'][0] - 1) * 100, 20, 45, " %",
          "clinical; reported +30%")
    check("arterial PaCO2 rate", (r['paco2'][-1] - 40) / 15, 1.8, 3.0,
          " mmHg/min", "clinical; 2.1 measured, arterial studies 1.8-3.4")
    sv = r['co'] * 1000 / np.maximum(r['hr'], 1e-6)
    check("stroke volume rises with hypercapnia",
          (sv[-1] / sv[0] - 1) * 100, 5, 30, " %",
          "clinical; Chest: HR, SV, CO and MAP all rose")


def test_icsm_jet_2026():
    """Laviola M, Dinsmore J, Lacquiere D, Niklas C, Heard A, Hardman JG.
    Anesth Analg 2026, DOI 10.1213/ANE.0000000000008194, Supplementary S5.
    MODEL comparator, not measurement.

    The state at the end of apnoea -- the moment of cricothyroidotomy, at
    SaO2 40% after complete upper airway obstruction -- in their 45-90 kg
    cohort:

        PaO2   28.3 (0.4) mmHg      PaCO2  84.6 (4.4) mmHg
        CO     2.7 (0.1) L/min      MAP    57.4 (2.4) mmHg

    Worth having because the two models were built independently and neither
    was tuned to the other, and because the mechanics of the two disagree
    sharply (see the collapse notes in HANDOVER.md) while the GAS state does
    not. Only the gas channels are checked here; the haemodynamic
    disagreement is real and is recorded under Known disagreement rather
    than papered over with a band wide enough to pass.

    DO NOT READ AGREEMENT HERE AS CORROBORATION. Checked 2026-09-19: ICSM's
    apnoea modules are validated against their refs 34-37, which are Fraioli
    1973 (apnoeic oxygenation), Berthoud 1991 (preoxygenation), Baraka 2007
    (nasopharyngeal insufflation) and Gustafsson 2017 (THRIVE). Three of the
    four cannot be done on an obstructed airway at all, because each delivers
    gas to the lung. Their simulator is extrapolating into complete
    obstruction exactly as ours is, so when the two agree they are two
    extrapolations from the same kind of patent-airway data landing in the
    same place. See HANDOVER.md, "How ICSM validated itself".

    CORRECTED 2026-09-22, and the correction reverses the claim. This
    docstring used to end "-- and both land a long way from Stock 1989, the
    one human measurement in this regime." THAT WAS NOT SUPPORTED, and on the
    one channel where it can be tested it is BACKWARDS.

    On CO2 the three can be compared directly, at 10 minutes of obstruction:

        Stock's own piecewise fit carried to 10 min   42.6 mmHg
        Laviola 2026, in silico                       38.2 (8.2)  -> 30.0-46.4
        OURS                                          27.4 mmHg

    Stock's figure sits INSIDE Laviola's 1 SD band. A human measurement and a
    simulator with no V/Q distribution land on the same number and WE are the
    outlier, 28% below both. Two caveats that both tighten rather than loosen
    that: Stock sampled to 5 min, so 42.6 is his fit extrapolated, and he
    describes the rise as LOGARITHMIC, so a linear carry-forward
    over-estimates his own curve; and Laviola's 10 min includes the
    post-cricothyroidotomy insufflations, so it is not pure obstruction
    throughout.

    ON OXYGEN, CORRECTED AGAIN the same day, and this one matters more.
    An earlier version of this note said no ICSM oxygen value existed at a
    Stock-comparable time. THAT WAS WRONG -- it came from searching the 2026
    paper's SDC and main text and inferring absence, which is the move
    CLAUDE.md forbids outright. Laviola M, Niklas C, Das A, Bates DG,
    Hardman JG, "Effect of oxygen fraction on airway rescue: a computational
    modelling study", Br J Anaesth 2020;125(1):e69-e74, doi
    10.1016/j.bja.2020.01.004 -- WHICH THIS REPOSITORY ALREADY HELD --
    publishes PaO2 at ONE-MINUTE INTERVALS through obstructed apnoea, in its
    Figure 1. Read off the FO2 21% panel, apnoea starting at their 3 min mark:

        min of apnoea     0    1    2    3    4    5    6    7
        ICSM PaO2 kPa    74   67  59.5  50  38.5 26.5 14.5    8
        ours      kPa    68   61   44   18   11   8.1   --   --

    AT STOCK'S 5 MINUTES: Stock measured 314 (87) mmHg, ICSM gives about
    26.5 kPa = 199 mmHg, and we give 61 mmHg. ICSM is 37% below Stock; we
    are 81% below. At 199 mmHg their saturation is essentially 100%, which
    agrees with Stock's "every one of 14 above 92%"; ours is 85.3% and does
    not.

    SO THE TWO MODELS DO NOT LAND IN THE SAME PLACE. Our curves start
    together -- 68 against 74 kPa -- and diverge from about two minutes. By
    three minutes we are at 18 kPa and they are at 50. Figure values are
    read off a printed plot and are good to perhaps +-2 kPa, which is
    nowhere near enough to change that.

    NO PRESSURE IS PUBLISHED ANYWHERE IN THAT PAPER. Searched in full: there
    is no cmH2O figure, only the qualitative "a single, passive inhalation
    (caused by intrathoracic hypobaric pressure)" and "the sub-atmospheric
    intrathoracic pressure was relieved by inflow via the newly opened
    airway". They do not report the passive inhalation volume either, which
    would have let their pressure be backed out from their compliance. So
    whether their model floors intrathoracic pressure, and where, is NOT
    determinable from what we hold.
    """
    p = Patient(weight=70, height=1.75, age=45, hb=14.0)
    r = simulate(p, [AirwayEpoch(1400, resistance=OBS, fgo2=0.21)],
                 dt=DT, stop_sao2=0.0)
    t40 = time_to(r, 'sao2', 40)
    # STRUCK 2026-09-22 BY RULING. There was once a band here reading "time to
    # SaO2 40%, 400-620 s, source ~510 s (8.5 min)". THE SOURCE DOES NOT
    # EXIST. We hold both the main text and the Supplementary Digital Content
    # and "510" is in neither; "510" appears zero times in the main text, and
    # every duration the paper does give is something else (3 min
    # preoxygenation, 30 s insufflation interval, 10 min protocol, 60 s and
    # 86 s peak-saturation times, 39 s to restore SaO2 above 90%). The SDC
    # gives the STATE at SaO2 40%, explicitly NOT the time to it.
    #
    # It was left failing-visible from 2026-09-21 so that its removal could
    # not be mistaken for a fix. The ruling is to strike it, and this comment
    # is the record: the suite once graded against a figure nobody could find,
    # and that row is gone, not passed. t40 is still COMPUTED, because the two
    # state comparisons below are taken at that moment -- it is simply no
    # longer graded against anything.
    i = int(np.searchsorted(r['t'], t40))
    # Their SD of 0.4 mmHg is the internal spread of a 100-subject in-silico
    # cohort with tightly controlled parameters, not measurement uncertainty,
    # and it is the wrong yardstick for agreement between two different
    # models. Banded at +-3 mmHg, which is what "these agree" means here.
    check("ICSM jet, PaO2 at cricothyroidotomy", r['pao2'][i],
          25.3, 31.3, " mmHg", "MODEL comparator; 28.3 (0.4), we allow +-3")
    check("ICSM jet, PaCO2 at cricothyroidotomy", r['paco2'][i],
          75.8, 93.4, " mmHg", "MODEL comparator; 84.6 (4.4), 2 SD")


def test_icsm_airway_rescue():
    """Laviola M et al. Br J Anaesth 2020. MODEL, not measurement.
    Obstructed to SaO2 60%, then relieved with supraglottic FO2 100%:
    post-rescue PaO2 42.3 (4.4) kPa."""
    p = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)
    base = simulate(p, [AirwayEpoch(3000, resistance=OBS, fgo2=0.21)],
                    dt=DT, stop_sao2=0.0)
    trig = base['t'][np.where(base['sao2'] < 60)[0][0]]
    r = simulate(p, [AirwayEpoch(trig, resistance=OBS, fgo2=1.0),
                     AirwayEpoch(600, resistance=2, fgo2=1.0)],
                 dt=DT, stop_sao2=0.0)
    peak = r['pao2'][r['t'] >= trig].max() / KPA
    check("ICSM rescue, post-rescue PaO2", peak, 33.5, 51.1, " kPa",
          "MODEL comparator; 42.3 (4.4), we allow 2 SD")
    # their qualitative finding: room air does not sustain the rescue
    ra = simulate(p, [AirwayEpoch(trig, resistance=OBS, fgo2=0.21),
                      AirwayEpoch(600, resistance=2, fgo2=0.21)],
                  dt=DT, stop_sao2=0.0)
    late = np.interp(min(trig + 300, ra['t'][-1]), ra['t'], ra['sao2'])
    check("ICSM rescue on room air is NOT sustained", late, 0, 60, " %",
          "MODEL comparator; their central qualitative result")


def test_physical_consistency():
    """Internal checks that do not depend on anyone's data."""
    p = Patient(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)
    r = patent(p, 1.00, dur=600)
    dur = r['t'][-1] / 60
    balance = (p.vo2_anaes() * dur - (r['lung_o2'][0] - r['lung_o2'][-1])
               - r['cum_o2_in'][-1])
    check("oxygen balance closes (blood+tissue term)", balance, -200, 900,
          " mL", "must be a plausible blood store, not a leak")
    check("stroke volume constant within a run",
          float(np.ptp(r['co'] * 1000 / np.maximum(r['hr'], 1e-6))), 0, 25,
          " mL", "CO is derived from HR, so SV must not drift")
    check("aventilatory mass flow at 2 min",
          float(np.interp(120, r['t'], r['inflow'])), 120, 260, " mL/min",
          "VO2 minus alveolar VCO2 minus returning N2")


def test_timestep_stability():
    """The inflow-compliance loop has tau = R x Crs. At R=2 that is 0.17 s,
    so dt must stay well under it. This test fails if someone raises dt."""
    p = Patient(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)
    a = patent(p, 1.00, dur=900, dt=0.05)
    b = patent(p, 1.00, dur=900, dt=0.025)
    d = abs(np.interp(900, a['t'], a['paco2']) - np.interp(900, b['t'], b['paco2']))
    check("PaCO2 converged between dt 0.05 and 0.025", d, 0, 2.0, " mmHg",
          "if this fails the integrator is unstable, not the physiology")


def test_zz_all_benchmarks_passed():
    """Sentinel: carries the verdict of every check() above into pytest.

    check() records rather than raises, so without this pytest would collect
    each test_* function, watch it print FAIL, and still report the run green.
    Named zz_ because pytest executes in definition order and this has to run
    last, after every other test has had its say.
    """
    assert not FAILURES, (f"{len(FAILURES)} benchmark(s) failed: "
                          + ", ".join(FAILURES))
    assert not REGRESSIONS, "; ".join(REGRESSIONS)


if __name__ == "__main__":
    import apnoea_core as _ac
    print(_ac.provenance())
    print("=" * 74)
    print("CLINICAL TARGETS — measurements in patients. These are the arbiters.")
    print("=" * 74)
    test_toner_2019(); test_heard_2017(); test_oloughlin_2020()
    test_positioning_trials(); test_cardiac_output()
    test_anaemia_cardiac_response()
    test_stock_1989(); test_moreault_2021()
    print()
    print("=" * 74)
    print("MODEL COMPARATORS — other people's simulations, not measurements.")
    print("=" * 74)
    test_icsm_airway_rescue(); test_icsm_jet_2026()
    print()
    print("=" * 74)
    print("INTERNAL CONSISTENCY")
    print("=" * 74)
    test_physical_consistency(); test_timestep_stability()
    print()
    print("=" * 74)
    _open = [k for k in KNOWN_OPEN if k not in FAILURES]
    if FAILURES:
        print(f"{len(FAILURES)} BLOCKING: " + ", ".join(FAILURES))
    else:
        print("no blocking failures")
    if _open:
        print(f"{len(_open)} KNOWN OPEN (ruled, not blocking): "
              + ", ".join(_open))
        print("These are real disagreements with measurement. They do not")
        print("gate the hook because they are ruled open, NOT because they")
        print("are acceptable. See KNOWN_OPEN at the head of this file.")
    for _r in REGRESSIONS:
        print("  !! " + _r)
    print("=" * 74)
    sys.exit(1 if (FAILURES or REGRESSIONS) else 0)
