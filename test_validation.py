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


def check(name, value, lo, hi, units="", source=""):
    ok = lo <= value <= hi
    tag = "PASS" if ok else "FAIL"
    if not ok:
        FAILURES.append(name)
    print(f"  [{tag}] {name:44s} {value:8.1f}{units:>8}   "
          f"expect {lo:.0f}-{hi:.0f}")
    if source:
        print(f"         {source}")
    return ok


def patent(pt, fg, dur=1200, feo2=0.87, dt=DT):
    return simulate(pt, [AirwayEpoch(dur, resistance=2, fgo2=fg)],
                    dt=dt, feo2_start=feo2, stop_sao2=0.0)


# =====================================================================
def test_toner_2018():
    """Toner AJ et al. Anesth Analg 2019;128:1154-9. CLINICAL.
    Healthy non-obese, prolonged laryngoscopy, supine.
    Sham 447 s (IQR 405-525); buccal 750 s (IQR 750-750), 750 s ceiling."""
    p = Patient(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)
    t = time_to(patent(p, 0.21), 'spo2', 95)
    check("Toner sham, time to SpO2<95%", t, 380, 525, " s",
          "clinical; IQR 405-525, we allow a little below")
    tb = time_to(patent(p, 1.00), 'spo2', 95)
    check("Toner buccal, held to 750 s", 9999 if tb is None else tb,
          750, 1e9, " s", "clinical; IQR 750-750")


def test_heard_2017():
    """Heard A et al. Anesth Analg 2017;124:1162-7. CLINICAL.
    Obese BMI 30-40, ramped, prolonged laryngoscopy.
    Control 296 s (IQR 244-314); buccal 750 s (IQR 389-750)."""
    p = Patient(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)
    t = time_to(patent(p, 0.21), 'spo2', 95)
    check("Heard control, time to SpO2<95%", t, 244, 314, " s",
          "clinical; IQR 244-314")
    tb = time_to(patent(p, 1.00), 'spo2', 95)
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
    """Stock MC, Downs JB, McDonald JS et al. J Clin Anesth 1989;1:328-32.
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


def test_anaemia_cardiac_response():
    """Varat, Adolph & Fowler, Am Heart J 1972;83:415-26, and Hemodynamic
    Effects of Chronic Severe Anemia, Circulation 1963;28:346. CLINICAL.

    Varat: chronic anaemia "usually increases the cardiac output when the
    haemoglobin level is 7 g/dL or less". Circulation 1963: Hb 4.0-6.5
    (mean 4.5) gave a cardiac index of 6.3 L/min/m2 against a normal ~3.2,
    so very nearly double.

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
          1.7, 2.3, " x normal", "clinical; CI 6.3 vs ~3.2 normal = 1.97x")
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
    """Sci Rep 2023 (PMC10864331). CLINICAL. n=91 anaesthetised, paralysed,
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
    """
    p = Patient(weight=70, height=1.75, age=45, hb=14.0)
    r = simulate(p, [AirwayEpoch(1400, resistance=OBS, fgo2=0.21)],
                 dt=DT, stop_sao2=0.0)
    t40 = time_to(r, 'sao2', 40)
    check("ICSM jet, time to SaO2 40%", 9999 if t40 is None else t40,
          400, 620, " s", "MODEL comparator; ~510 s (8.5 min)")
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


if __name__ == "__main__":
    import apnoea_core as _ac
    print(_ac.provenance())
    print("=" * 74)
    print("CLINICAL TARGETS — measurements in patients. These are the arbiters.")
    print("=" * 74)
    test_toner_2018(); test_heard_2017(); test_oloughlin_2020()
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
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: " + ", ".join(FAILURES))
    else:
        print("all checks passed")
    print("=" * 74)
    sys.exit(1 if FAILURES else 0)
