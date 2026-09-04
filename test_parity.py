"""
test_parity.py — apnoea_core.py and model.js must produce the same numbers.

RUN:  python3 test_parity.py           (plain, no pytest needed)
      pytest test_parity.py -v         (if you prefer)

HANDOVER.md says of model.js: "JavaScript port. Must track the Python." Nothing
enforced that. The port had in fact drifted: it still carried the superseded
whole-lung-mean nitrogen exchange after apnoea_core.py moved to a
per-compartment one, which by 15 minutes put the two implementations 21% apart
on PaO2 and 14% apart on shunt. Nobody noticed, because SpO2 — the output
anyone actually looks at — stayed within 1% the whole time. The oxygen plateau
holds saturation flat while the gas exchange underneath it drifts, so the
headline number hides the disagreement rather than revealing it. That is
precisely the failure mode this file exists to catch.

WHAT IS COMPARED

Both implementations are run on identical inputs and their output series are
compared sample by sample. "Identical inputs" is the load-bearing phrase, and
js_params() below is where it is enforced: it derives the JavaScript parameter
object FROM the Python Patient, field by field, so the two cannot silently be
given different numbers. Anything model.js hardcodes rather than reading off
its parameter object cannot be set that way, so test_hardcoded_constants()
checks those separately, against the Python fields they correspond to.

THE 1% CONTRACT

For each channel, at each sample:

    relative error = |python - javascript| / max(|python|, floor)

and the assertion is that this stays at or below 1%. The floor is a per-channel
physiological scale (see CHANNELS). It exists because several channels pass
through zero — shunt, HPV, alveolar pressure, atelectasis all start at or near
0 — and a plain relative error against a denominator of ~0 reports thousands of
percent for a difference of no consequence. Below its floor a channel is
therefore held to 1% OF THE FLOOR, an absolute tolerance; above it, to a true
1% relative. Each floor is small next to the range the channel actually covers,
so this loosens nothing that matters.

WHERE IT IS COMPARED

Full-length channel comparison is restricted to the window where the model
claims to predict anything. The model states two limits and both are applied:

  SaO2 >= 70%.  HANDOVER.md: "anything below SaO2 ~70% is not predictive", and
  the bradycardia curve below it is "chosen to look right, not fitted to
  anything". That regime is also numerically vicious — the sigmoid is steep
  enough there to amplify a 0.17% saturation difference into a 1.0% heart-rate
  difference, and once the rhythm degenerates to the terminal escape rates
  heart rate is a step function through zero, where a sub-sample timing
  difference is arbitrarily large in relative terms.

  PaCO2 <= co2_response_cap (150 mmHg).  apnoea_core.py: "Beyond it there is no
  human data in this population ... The model holds them flat instead of
  extrapolating, and is simply not valid past here." It is worse than merely
  unvalidated up there: above roughly 150 mmHg the arterial CO2 inverse becomes
  erratic, and PaCO2 in the REFERENCE implementation jumps around — 218 -> 137
  -> 126 -> 230 mmHg over four minutes of a single apnoea, including 10-second
  intervals in which PaCO2 falls by 43 mmHg, which cannot happen when there is
  no ventilation to remove it. Both implementations reproduce that wobble and
  agree on it to about 0.1%, so it is not a parity defect, but comparing there
  measures agreement about nonsense. See the note at the foot of this file.

Comparing in either excluded region would measure the stiffness of a curve the
model disclaims, not agreement between the implementations.

That window is not a loophole:
  * saturation itself is compared over the WHOLE run, agonal phase included,
    by test_saturation_whole_run() — it is the clinically load-bearing output
    and it does hold to 1% throughout;
  * test_validity_window_is_substantial() fails if the window ever shrinks to
    a stub, so a bug that tanks saturation immediately cannot vacuously pass.
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

import bloodgas as bg
from apnoea_core import Patient, AirwayEpoch, simulate, time_to

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "parity_driver.js")

TOL = 0.01           # the 1%
SAO2_VALID = 70.0    # % — below this the model disclaims predictive value
FAILURES = []


# ---------------------------------------------------------------------------
# Channel map: python key -> (javascript key, floor, unit)
#
# The floor is the scale below which a channel is held to an absolute
# tolerance instead of a relative one; see THE 1% CONTRACT above. Each is a
# small fraction of the range its channel actually covers during an apnoea.
# ---------------------------------------------------------------------------
CHANNELS = [
    # python        js          floor   unit
    ("spo2",        "spo2",       1.0,  "%"),
    ("pao2",        "pao2",       1.0,  "mmHg"),
    ("paco2",       "paco2",      1.0,  "mmHg"),
    ("ph",          "ph",         1.0,  "pH"),
    ("va",          "vol",       10.0,  "mL"),
    ("shunt",       "shunt",      0.01, "fraction"),
    ("collapsed",   None,         0.01, "fraction"),   # no JS counterpart
    ("atelectasis", "atel",       0.01, "fraction"),
    ("hpv",         "hpv",        0.01, "fraction"),
    ("pan2",        "pan2",       1.0,  "mmHg"),
    ("pvo2",        "pvo2",       1.0,  "mmHg"),
    ("palv_cmh2o",  "palv",       0.5,  "cmH2O"),
    ("lung_o2",     "lungO2",     5.0,  "mL"),
    ("co",          "co",         0.05, "L/min"),
    ("hr",          "hr",         1.0,  "bpm"),
    ("map",         "map",        1.0,  "mmHg"),
    ("pap",         "pap",        1.0,  "mmHg"),
    ("sv",          "sv",         1.0,  "mL"),
]

# Python outputs with no JavaScript counterpart, and vice versa. Listed so that
# the gap is a recorded fact rather than something a reader has to rediscover;
# test_output_coverage() fails if this drifts.
PY_ONLY = {"t", "pao2_alv", "paco2_alv", "sao2", "svo2", "inflow",
           "cum_o2_in", "collapsed", "pvco2"}
JS_ONLY = {"t", "fao2"}


# ---------------------------------------------------------------------------
# Identical inputs
# ---------------------------------------------------------------------------
def js_params(pt, feo2):
    """The model.js parameter object for a given Python Patient.

    Derived from the Patient rather than written out as literals, so the two
    implementations cannot be handed different numbers. Every key model.js
    reads off P is set explicitly, including ones whose JS-side default already
    matches, because relying on a default is relying on it never changing.

    frcScale / ccScale / bmrScale exist only in the JavaScript, as interactive
    dials on the page. They have no Patient counterpart, so they are pinned at
    1.0 (the identity) — with any other value the two are not the same model.
    """
    return {
        # anthropometry
        "weight": pt.weight, "height": pt.height, "age": pt.age, "hb": pt.hb,
        # respiratory
        "frcRef": pt.frc_ref, "frcDrop": pt.frc_drop, "tiltDeg": pt.tilt_deg,
        "tiltGainLean": pt.tilt_gain_lean, "tiltGainBmi": pt.tilt_gain_bmi,
        "ccAt20": pt.cc_at_20, "ccPerYear": pt.cc_per_year,
        "ccPerBmi": pt.cc_per_bmi, "ccK": pt.cc_k, "maxClosed": pt.max_closed,
        "crs": pt.crs, "rv": pt.rv, "pCollapse": pt.p_collapse,
        # V/Q and collapse
        "nVq": pt.n_vq, "vqLogSd": pt.vq_log_sd, "tauMix": pt.tau_mix,
        "inflowMechFrac": pt.inflow_mech_frac, "cvFrac": pt.cv_frac,
        "recruitFrac": pt.recruit_frac, "tauRecruit": pt.tau_recruit,
        "shuntBase": pt.shunt_base,
        # HPV
        "hpvEnabled": pt.hpv_enabled, "hpvPvrMax": pt.hpv_pvr_max,
        # metabolic and circulatory
        "vo2Ref": pt.vo2_ref, "coRef": pt.co_ref,
        "hrBase": pt.hr_base, "hrBradyN": pt.hr_brady_n,
        "hrBradySao250": pt.hr_brady_sao2_50,
        "hrTermSao2": pt.hr_term_sao2, "hrTermDelay": pt.hr_term_delay,
        "co2ResponseCap": pt.co2_response_cap, "coCo2Gain": pt.co_co2_gain,
        "coMaxFactor": pt.co_max_factor, "svCo2Gain": pt.sv_co2_gain,
        "svItpGain": pt.sv_itp_gain, "itpFraction": pt.itp_fraction,
        "svrBase": pt.svr_base, "svrCo2Gain": pt.svr_co2_gain,
        "svrFloor": pt.svr_floor, "pvrBase": pt.pvr_base, "pcwp": pt.pcwp,
        # blood pools
        "vArt": pt.v_art, "vVen": pt.v_ven, "vTisO2": pt.v_tis_o2,
        # initial condition
        "feo2": feo2,
        # JS-only interactive dials, pinned to identity
        "frcScale": 1.0, "ccScale": 1.0, "bmrScale": 1.0,
    }


def js_epochs(epochs):
    """AirwayEpoch list -> the {d, R, fg} form model.js expects.

    An occluded airway is np.inf in Python and Infinity in JavaScript, but JSON
    can carry neither, so it goes over the wire as null and parity_driver.js
    converts it back. The driver refuses to let null through as-is, because
    isFinite(null) is true — a sealed airway would silently become a
    zero-resistance open one.
    """
    return [{"d": e.duration,
             "R": None if not np.isfinite(e.resistance) else e.resistance,
             "fg": e.fgo2}
            for e in epochs]


def run_js(pt, epochs, dt, feo2):
    """Run model.js and return its output dict."""
    if shutil.which("node") is None:
        raise RuntimeError(
            "node is not installed, so model.js cannot be run and the port "
            "cannot be checked against the Python. Install node, or commit "
            "with --no-verify and say in the message that parity is unverified.")
    if not os.path.exists(DRIVER):
        raise RuntimeError(f"{DRIVER} is missing; it is what runs model.js.")
    job = {"params": js_params(pt, feo2), "epochs": js_epochs(epochs), "dt": dt}
    proc = subprocess.run([_node(), DRIVER], input=json.dumps(job),
                          capture_output=True, text=True, timeout=600)
    if not proc.stdout.strip():
        raise RuntimeError(f"parity_driver.js produced no output. "
                           f"stderr:\n{proc.stderr}")
    res = json.loads(proc.stdout)
    if not res.get("ok"):
        raise RuntimeError(f"model.js failed: {res.get('error')}")
    return res["out"]


def _node():
    return shutil.which("node")


def run_both(pt, epochs, dt, feo2):
    """Run both implementations and return (python_rec, js_out, stride).

    Python records every timestep; model.js records once a second. stride is
    the Python index step that lands on the JavaScript sample times.
    stop_sao2 is disabled so that Python does not truncate the run partway —
    model.js has no equivalent early stop, and a comparison of two runs of
    different length is not a comparison.
    """
    rec = simulate(pt, epochs, dt=dt, feo2_start=feo2, stop_sao2=0.0)
    out = run_js(pt, epochs, dt, feo2)
    return rec, out, int(round(1.0 / dt))


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def report(name, worst, channel, t, pv, jv, unit, extra=""):
    ok = worst <= TOL
    tag = "PASS" if ok else "FAIL"
    if not ok:
        FAILURES.append(name)
    print(f"  [{tag}] {name:52s} {worst * 100:7.3f}%  (limit {TOL * 100:.0f}%)")
    if not ok:
        print(f"         worst channel {channel} at t={t:.0f}s: "
              f"python {pv:.6g} vs js {jv:.6g} {unit}")
    if extra:
        print(f"         {extra}")
    return ok


def compare(name, pt, epochs, dt=0.1, feo2=0.87, valid_window=True):
    """Compare every mapped channel and report the worst relative error."""
    rec, out, stride = run_both(pt, epochs, dt, feo2)

    # Align the two time bases on the JavaScript sample times, and compare only
    # over the samples both produced: the two can stop a sample apart when the
    # terminal-rhythm break latches on either side of a sample boundary.
    n = min(len(out["t"]), len(rec["t"][::stride]))
    assert n > 10, f"{name}: only {n} comparable samples, something is wrong"
    t = np.asarray(out["t"][:n], dtype=float)

    if valid_window:
        mask = ((rec["sao2"][::stride][:n] >= SAO2_VALID)
                & (rec["paco2"][::stride][:n] <= pt.co2_response_cap))
    else:
        mask = np.ones(n, dtype=bool)
    if not mask.any():
        FAILURES.append(name)
        print(f"  [FAIL] {name:52s}  nothing inside the model's stated "
              f"validity envelope")
        return

    worst, w_ch, w_t, w_p, w_j, w_u = 0.0, "", 0.0, 0.0, 0.0, ""
    for pk, jk, floor, unit in CHANNELS:
        if jk is None:
            continue
        p = np.asarray(rec[pk][::stride][:n], dtype=float)
        j = np.asarray(out[jk][:n], dtype=float)
        rel = np.abs(p - j) / np.maximum(np.abs(p), floor)
        rel = np.where(mask, rel, 0.0)
        k = int(np.argmax(rel))
        if rel[k] > worst:
            worst, w_ch, w_t, w_p, w_j, w_u = rel[k], pk, t[k], p[k], j[k], unit

    span = (f"{int(mask.sum())}/{n} samples compared "
            f"(SaO2 >= {SAO2_VALID:.0f}%, PaCO2 <= {pt.co2_response_cap:.0f})")
    report(name, worst, w_ch, w_t, w_p, w_j, w_u, span)


# ---------------------------------------------------------------------------
# Scenarios. Between them these exercise every path where the two
# implementations could plausibly part company: long apnoeic oxygenation where
# nitrogen accumulation dominates, a desaturating room-air control, the
# reopening inrush with its dead-space advection and refill, a sealed airway
# developing subatmospheric pressure, and the published timestep.
# ---------------------------------------------------------------------------
LEAN = dict(weight=70, height=1.75, age=45, hb=15, tilt_deg=0)
OBESE = dict(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)

OBS = np.inf


def test_lean_patent_buccal():
    """Long apnoeic oxygenation. The case that caught the nitrogen drift:
    15 minutes is long enough for tissue nitrogen to reach the alveolus and
    for a per-compartment treatment to diverge from a well-mixed one."""
    compare("lean, patent, buccal O2, 900 s",
            Patient(**LEAN), [AirwayEpoch(900, resistance=2, fgo2=1.00)])


def test_obese_patent_room_air():
    """The desaturating control arm — Heard's population without the device."""
    compare("obese ramped, patent, room air, 400 s",
            Patient(**OBESE), [AirwayEpoch(400, resistance=2, fgo2=0.21)])


def test_obese_obstructed_then_rescue():
    """The inrush. When the airway opens after obstruction, ~600 mL arrives
    within seconds through the dead space; this is the largest transient the
    model contains and the hardest thing for two ports to agree on.

    Ten minutes, not fifteen: this patient's PaCO2 crosses the 150 mmHg
    response cap at around 11 minutes, and past it the reference implementation
    itself becomes erratic (see the note at the foot of this file). Running
    longer would spend most of the scenario comparing the two implementations
    in a regime the model disclaims, rather than on the transient it is here to
    exercise.
    """
    compare("obese, obstructed 120 s then patent buccal, 600 s",
            Patient(**OBESE),
            [AirwayEpoch(120, resistance=OBS, fgo2=1.00),
             AirwayEpoch(480, resistance=2, fgo2=1.00)])


def test_lean_sealed_airway():
    """A sealed airway, where the lung shrinks against its own recoil and
    alveolar pressure goes subatmospheric. Exercises the recoil solve, the
    stiffening below residual volume, and the collapse floor."""
    compare("lean, sealed airway, room air, 600 s",
            Patient(**LEAN), [AirwayEpoch(600, resistance=OBS, fgo2=0.21)])


def test_partial_obstruction():
    """A poorly held mask: patent enough to pass the mass flow, resistive
    enough that the lung must go subatmospheric to drive it."""
    compare("lean, R=200 partial obstruction, room air, 600 s",
            Patient(**LEAN), [AirwayEpoch(600, resistance=200, fgo2=0.21)])


def test_published_timestep():
    """dt=0.05, the timestep HANDOVER.md requires for anything published.
    The others run at 0.1 to keep the pre-commit hook quick; this one confirms
    the agreement is not an artefact of the coarser step."""
    compare("obese, patent buccal, 400 s at dt=0.05",
            Patient(**OBESE), [AirwayEpoch(400, resistance=2, fgo2=1.00)],
            dt=0.05)


# ---------------------------------------------------------------------------
# Checks that are not channel-by-channel
# ---------------------------------------------------------------------------
def test_saturation_whole_run():
    """Saturation, over the whole run including the agonal phase.

    The channel comparisons stop at SaO2 70% because the model disclaims what
    happens below it. Saturation is the exception: it is the output the model
    exists to produce and the one every clinical benchmark is stated in, so it
    is held to 1% for every sample to the end of the run, terminal rhythm and
    all.
    """
    pt = Patient(**LEAN)
    epochs = [AirwayEpoch(600, resistance=OBS, fgo2=0.21)]
    rec, out, stride = run_both(pt, epochs, 0.1, 0.87)
    n = min(len(out["t"]), len(rec["t"][::stride]))
    p = np.asarray(rec["spo2"][::stride][:n], dtype=float)
    j = np.asarray(out["spo2"][:n], dtype=float)
    rel = np.abs(p - j) / np.maximum(np.abs(p), 1.0)
    k = int(np.argmax(rel))
    report("SpO2 agrees over the whole run, to asystole", rel[k],
           "spo2", out["t"][k], p[k], j[k], "%",
           f"all {n} samples, floor SaO2 {rec['sao2'][::stride][:n].min():.0f}%")


def test_desaturation_time():
    """The clinical endpoint itself.

    Every benchmark in test_validation.py is a time to a saturation threshold,
    so the two implementations agreeing sample-by-sample is worth little if
    they disagree about when SpO2 crosses 95%. Compared as a relative
    difference in seconds.
    """
    pt = Patient(**OBESE)
    epochs = [AirwayEpoch(600, resistance=2, fgo2=0.21)]
    rec, out, stride = run_both(pt, epochs, 0.1, 0.87)
    t_py = time_to(rec, "spo2", 95)
    js_t, js_s = np.asarray(out["t"], float), np.asarray(out["spo2"], float)
    below = np.where(js_s < 95)[0]
    t_js = None if len(below) == 0 else js_t[below[0]]
    if t_py is None or t_js is None:
        FAILURES.append("time to SpO2<95% agrees")
        print(f"  [FAIL] {'time to SpO2<95% agrees':52s}  "
              f"python {t_py}, js {t_js} — one desaturated and the other did not")
        return
    # Python samples every dt, model.js every second, so the two cannot resolve
    # the crossing more finely than one sample; allow that as well as the 1%.
    rel = abs(t_py - t_js) / max(t_py, 1.0)
    ok = rel <= TOL or abs(t_py - t_js) <= 1.0
    if not ok:
        FAILURES.append("time to SpO2<95% agrees")
    print(f"  [{'PASS' if ok else 'FAIL'}] "
          f"{'time to SpO2<95% agrees':52s} {rel * 100:7.3f}%  (limit 1%)")
    print(f"         python {t_py:.1f} s, javascript {t_js:.1f} s")


def test_derived_scalars():
    """The derived patient constants, before any integration.

    model.js returns frc, cc, vo2, coBase and bmi. If these disagree the two
    are not simulating the same patient and every later comparison is
    meaningless, so this is checked across a spread of phenotypes rather than
    only the two the scenarios use.
    """
    phenotypes = [
        dict(weight=70, height=1.75, age=45, hb=15, tilt_deg=0),
        dict(weight=107, height=1.75, age=45, hb=14, tilt_deg=25),
        dict(weight=50, height=1.55, age=22, hb=13, tilt_deg=-10),
        dict(weight=145, height=1.68, age=68, hb=16, tilt_deg=30),
        dict(weight=95, height=1.95, age=30, hb=15, tilt_deg=15),
    ]
    worst, detail = 0.0, ""
    for kw in phenotypes:
        pt = Patient(**kw)
        out = run_js(pt, [AirwayEpoch(2, resistance=2, fgo2=1.0)], 0.1, 0.87)
        for label, py, js in (("frc", pt.frc_anaes(), out["frc"]),
                              ("cc", pt.closing_capacity(), out["cc"]),
                              ("vo2", pt.vo2_anaes(), out["vo2"]),
                              ("co", pt.co_anaes(), out["coBase"]),
                              ("bmi", pt.bmi(), out["bmi"])):
            rel = abs(py - js) / max(abs(py), 1e-9)
            if rel > worst:
                worst, detail = rel, (f"{label} for {kw['weight']:.0f} kg / "
                                      f"{kw['height']:.2f} m: python {py:.6g} "
                                      f"vs js {js:.6g}")
    ok = worst <= TOL
    if not ok:
        FAILURES.append("derived patient constants agree")
    print(f"  [{'PASS' if ok else 'FAIL'}] "
          f"{'derived patient constants agree':52s} {worst * 100:7.3f}%  "
          f"(limit {TOL * 100:.0f}%)")
    if not ok:
        print(f"         {detail}")


def test_hardcoded_constants():
    """Patient fields that model.js does not read from its parameter object.

    js_params() can only keep the two implementations in step for values the
    JavaScript actually reads off P. Everything below is written into model.js
    as a literal, so changing the Python field silently makes the port a
    different model — exactly the drift this file exists to detect, but
    invisible to a run-and-compare because the scenarios all use the defaults.
    If one of these fires, either put the value on the parameter object or
    change the literal in model.js to match.
    """
    pt = Patient()
    expected = [
        ("k_frc_bmi", pt.k_frc_bmi, 0.0417, "model.js:65 exp(-0.0417*(bmi-22))"),
        ("vo2_drop_per_kg", pt.vo2_drop_per_kg, 0.27, "model.js:68 -0.27*weight"),
        ("co_drop_frac", pt.co_drop_frac, 0.25, "model.js:69 *0.75"),
        ("rq", pt.rq, 0.8, "model.js:78 vco2m=vo2*0.8"),
        ("perfusion_gain", pt.perfusion_gain, 1.2, "model.js:168 f0=1.2*..."),
        ("tau_collapse_o2", pt.tau_collapse_o2, 60.0, "model.js:151 tauC=60*..."),
        ("tau_collapse_air", pt.tau_collapse_air, 900.0, "model.js:151 +900*..."),
        ("tau_hpv", pt.tau_hpv, 250.0, "model.js:173 dt/250"),
        ("hpv_co2_gain", pt.hpv_co2_gain, 0.0, "model.js has no such term"),
        ("lambda_n2", pt.lambda_n2, 1.895e-5, "model.js:71 lam=1.895e-5"),
        ("lambda_fat_ratio", pt.lambda_fat_ratio, 5.0, "model.js:72 *5"),
        ("n2_pt_init", pt.n2_pt_init, 573.0, "model.js:111 n2p=[573,573,573]"),
        ("v_tis_co2_fast", pt.v_tis_co2_fast, 22.0, "model.js:292 /(22*10)"),
        ("v_tis_co2_slow", pt.v_tis_co2_slow, 140.0, "model.js:293 /(140*10)"),
        ("k_co2_slow", pt.k_co2_slow, 0.80, "model.js:291 fs=0.8*..."),
        ("vd_anat", pt.vd_anat, 150.0, "model.js:79 frc-150, vseg=15"),
        ("vd_segments", pt.vd_segments, 10, "model.js:94 NS=10"),
        ("stiff_below_rv", pt.stiff_below_rv, 0.15, "model.js:131 stiff=0.15"),
        ("pools", pt.pools, 3, "model.js:104 NP=3"),
        ("spo2_delay", pt.spo2_delay, 25.0, "model.js:302 Math.round(25/dt)"),
        ("spo2_tau", pt.spo2_tau, 8.0, "model.js:303 *(dt/8)"),
        ("temp", pt.temp, 37.0, "model.js:78 T=37"),
        ("be", pt.be, 0.0, "model.js:78 be=0"),
        ("q_frac", tuple(pt.q_frac), (0.75, 0.18, 0.07),
         "model.js:114 qf=[0.75,0.18,0.07]"),
        ("hr_term_rates", tuple(pt.hr_term_rates), (18.0, 12.0, 6.0),
         "model.js:196 RATES=[18,12,6]"),
        # bloodgas.py exposes CO2_CAL so the Douglas curve can be recalibrated
        # to reference points (HANDOVER.md flags the constants as unverified).
        # model.js has no such factor, so a recalibration there would apply to
        # the Python only.
        ("bloodgas.CO2_CAL", bg.CO2_CAL, 1.0, "model.js:34 has no CO2_CAL"),
    ]
    drift = [(n, p, j, w) for n, p, j, w in expected if p != j]
    ok = not drift
    if not ok:
        FAILURES.append("model.js hardcoded constants match Patient defaults")
    print(f"  [{'PASS' if ok else 'FAIL'}] "
          f"{'model.js literals match Patient defaults':52s} "
          f"{len(drift)} drifted of {len(expected)}")
    for n, p, j, w in drift:
        print(f"         {n}: Patient has {p!r}, {w}")


def test_frc_floor_not_engaged():
    """The one floor the two implementations genuinely disagree on.

    apnoea_core.py floors anaesthetised FRC at 400 mL, model.js at 300. No
    parameter reconciles them, so the scenarios above must stay clear of both;
    if a future scenario does not, its comparison is measuring the floor rather
    than the physics. Checked rather than assumed.
    """
    worst_pt, worst_frc = None, float("inf")
    for kw in (LEAN, OBESE):
        pt = Patient(**kw)
        if pt.frc_anaes() < worst_frc:
            worst_pt, worst_frc = pt, pt.frc_anaes()
    ok = worst_frc > 400.0
    if not ok:
        FAILURES.append("FRC floor not engaged in any parity scenario")
    print(f"  [{'PASS' if ok else 'FAIL'}] "
          f"{'FRC floor (py 400 mL / js 300 mL) not engaged':52s} "
          f"{worst_frc:7.0f} mL  (must exceed 400)")


def test_output_coverage():
    """Which outputs have a counterpart on the other side.

    A channel that exists in only one implementation is a channel this file
    cannot check, so the set is pinned. If someone adds an output to one side,
    this fails and asks them to add it to the other — or to record here, on
    purpose, that it is unmatched.
    """
    pt = Patient(**LEAN)
    epochs = [AirwayEpoch(3, resistance=2, fgo2=1.0)]
    rec = simulate(pt, epochs, dt=0.1, feo2_start=0.87, stop_sao2=0.0)
    out = run_js(pt, epochs, 0.1, 0.87)

    mapped_py = {pk for pk, jk, _, _ in CHANNELS if jk is not None}
    mapped_js = {jk for _, jk, _, _ in CHANNELS if jk is not None}
    py_keys = set(rec.keys())
    js_keys = {k for k, v in out.items() if isinstance(v, list)}

    py_unmatched = py_keys - mapped_py - PY_ONLY
    js_unmatched = js_keys - mapped_js - JS_ONLY
    ok = not py_unmatched and not js_unmatched
    if not ok:
        FAILURES.append("output key coverage")
    print(f"  [{'PASS' if ok else 'FAIL'}] "
          f"{'every output is mapped or declared unmatched':52s} "
          f"{len(mapped_py)} compared, {len(PY_ONLY | JS_ONLY)} declared")
    if py_unmatched:
        print(f"         unmapped python outputs: {sorted(py_unmatched)}")
    if js_unmatched:
        print(f"         unmapped javascript outputs: {sorted(js_unmatched)}")


def test_validity_window_is_substantial():
    """Guard on the SaO2 >= 70% window.

    The window is what makes the channel comparisons meaningful; it would also
    be the obvious place for a real regression to hide, since a change that
    desaturated the patient instantly would leave almost nothing to compare and
    every other test would pass on a handful of samples. Each scenario must
    keep most of its run inside the window.
    """
    cases = [
        ("lean, patent, buccal", Patient(**LEAN),
         [AirwayEpoch(900, resistance=2, fgo2=1.00)], 0.90),
        ("obese, patent, room air", Patient(**OBESE),
         [AirwayEpoch(400, resistance=2, fgo2=0.21)], 0.50),
    ]
    worst, detail = 1.0, ""
    for label, pt, epochs, need in cases:
        rec = simulate(pt, epochs, dt=0.1, feo2_start=0.87, stop_sao2=0.0)
        s = rec["sao2"][::10]
        frac = float((s >= SAO2_VALID).mean())
        if frac < need:
            worst = min(worst, frac / need)
            detail = (f"{label}: only {frac * 100:.0f}% of the run is above "
                      f"SaO2 {SAO2_VALID:.0f}%, expected at least "
                      f"{need * 100:.0f}%")
    ok = not detail
    if not ok:
        FAILURES.append("validity window is substantial")
    print(f"  [{'PASS' if ok else 'FAIL'}] "
          f"{'comparison window covers most of each run':52s}")
    if detail:
        print(f"         {detail}")


def test_zz_all_parity_checks_passed():
    """Sentinel: carries the verdict of every check above into pytest.

    The checks above report rather than raise, so that one run shows every
    disagreement instead of stopping at the first. Without this, pytest would
    watch them all print FAIL and still call the run green. Named zz_ because
    pytest runs in definition order and this has to go last.
    """
    assert not FAILURES, (f"{len(FAILURES)} parity check(s) failed: "
                          + ", ".join(FAILURES))


if __name__ == "__main__":
    print("=" * 78)
    print("CROSS-LANGUAGE PARITY — apnoea_core.py vs model.js, identical inputs")
    print(f"tolerance {TOL * 100:.0f}% | channels compared where the model is "
          f"valid: SaO2 >= {SAO2_VALID:.0f}%, PaCO2 <= "
          f"{Patient().co2_response_cap:.0f} mmHg")
    print("=" * 78)
    print("\nsame patient, same airway, same timestep:")
    test_lean_patent_buccal()
    test_obese_patent_room_air()
    test_obese_obstructed_then_rescue()
    test_lean_sealed_airway()
    test_partial_obstruction()
    test_published_timestep()
    print("\nclinical endpoints and derived quantities:")
    test_saturation_whole_run()
    test_desaturation_time()
    test_derived_scalars()
    print("\nthings a run-and-compare cannot see:")
    test_hardcoded_constants()
    test_frc_floor_not_engaged()
    test_output_coverage()
    test_validity_window_is_substantial()
    print()
    print("=" * 78)
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: " + ", ".join(FAILURES))
        print("\nmodel.js and apnoea_core.py have parted company. HANDOVER.md:")
        print('"model.js — JavaScript port. Must track the Python."')
    else:
        print("model.js tracks apnoea_core.py")
    print("=" * 78)
    sys.exit(1 if FAILURES else 0)


# ---------------------------------------------------------------------------
# NOTE — an instability in the REFERENCE, found while building this file.
#
# Not a parity defect. Both implementations do it and agree with each other to
# about 0.1% while doing it, so nothing here is caught by the tests above; it
# is recorded because it was found by them and should not be lost.
#
# Above roughly PaCO2 150 mmHg the arterial CO2 inverse stops behaving.
# Reproduce:
#
#     pt = Patient(weight=107, height=1.75, age=45, hb=14, tilt_deg=25)
#     rec = simulate(pt, [AirwayEpoch(120, resistance=np.inf, fgo2=1.0),
#                         AirwayEpoch(780, resistance=2, fgo2=1.0)],
#                    dt=0.1, feo2_start=0.87, stop_sao2=0.0)
#
# PaCO2 then reads 218 mmHg at 650 s, 138 at 700 s, 126 at 725 s, 230 at 825 s
# and 246 at 850 s. Twelve of the ninety ten-second intervals have PaCO2
# FALLING, once by 43.8 mmHg. With no ventilation there is nothing to remove
# CO2, so PaCO2 cannot fall at all; the trajectory is a numerical artefact, not
# physiology.
#
# The likely mechanism is pco2_from_co2_content (bloodgas.py:159). Its residual
# is solved by brentq on [3, 400] while SO2 and pH are themselves resolved by
# an inner fixed point (bloodgas.py:165-176). At extreme hypercapnia that inner
# loop is poorly conditioned, so the residual is not smooth in PCO2 and the
# bracket admits more than one root; successive one-second solves then land on
# different ones. A related non-monotonicity was found independently in the
# same residual: co2_content has a pole at pH 8.142 (bloodgas.py:154), and for
# BE >= +6 brentq and model.js's bisection select DIFFERENT roots of it and
# disagree by ~89%. Neither implementation is right there — they are two
# arbitrary choices among several roots. That one is unreachable here only
# because base excess is 0 in both (Patient.be, and model.js:78 hardcodes it),
# which test_hardcoded_constants() pins.
#
# Consequences are bounded and no published result rests on this: PaCO2 150 is
# co2_response_cap, past which apnoea_core.py already says the model "is simply
# not valid", and every benchmark in test_validation.py finishes well below it.
# Worth fixing before anything is claimed in that range — most likely by
# bracketing the inner fixed point, or by solving PCO2 monotonically in CO2
# content rather than re-solving from scratch each step.
# ---------------------------------------------------------------------------
