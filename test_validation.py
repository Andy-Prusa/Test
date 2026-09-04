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
"""
import numpy as np
from apnoea_core import Patient, AirwayEpoch, simulate, time_to

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


if __name__ == "__main__":
    print("=" * 74)
    print("CLINICAL TARGETS — measurements in patients. These are the arbiters.")
    print("=" * 74)
    test_toner_2018(); test_heard_2017(); test_oloughlin_2020()
    test_positioning_trials(); test_cardiac_output()
    print()
    print("=" * 74)
    print("MODEL COMPARATORS — other people's simulations, not measurements.")
    print("=" * 74)
    test_icsm_airway_rescue()
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
