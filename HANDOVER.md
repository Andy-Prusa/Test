# Apnoeic oxygenation model — handover

A computational model of gas exchange during apnoea after intravenous
induction, built to quantify the effect of buccal oxygen delivery. Two
implementations that must agree: `apnoea_core.py` (reference) and `model.js`
(browser, drives `airway_scenario.html`).

## Start here

```
pip install -r requirements.txt   # numpy, scipy, matplotlib (+ node for the port)
./setup-hooks.sh                  # once per clone: gate commits on the benchmarks
python3 test_validation.py        # every benchmark, as pass/fail
python3 test_parity.py            # apnoea_core.py vs model.js, within 1%
python3 run.py                    # a single scenario with plots
```

`test_validation.py` is the important one. Several changes during development
silently broke earlier agreements and were only caught by re-running things by
hand. That is no longer left to memory: `.githooks/pre-commit` runs both test
files before every commit and refuses the commit if either fails.
`setup-hooks.sh` enables it, and has to be run once per clone because git does
not clone hooks.

If you genuinely need to commit a broken intermediate state, `git commit
--no-verify` skips it — say in the message which benchmark is broken and why.

Both suites exit non-zero on failure and both work under pytest. `check()`
records rather than raises, so one run reports every failure instead of
stopping at the first; a sentinel test at the foot of each file carries the
verdict into pytest.

## Files

| file | what it is |
|---|---|
| `apnoea_core.py` | the model. Reference implementation |
| `bloodgas.py` | O2 and CO2 dissociation, acid-base |
| `model.js` | JavaScript port. Must track the Python |
| `airway_scenario.html` | self-contained interactive page, embeds `model.js` |
| `build_page.py` | regenerates the HTML from `model.js` + template |
| `test_validation.py` | all benchmarks as executable tests |
| `test_parity.py` | the two implementations against each other, within 1% |
| `parity_driver.js` | stdin/stdout shim so Python can drive `model.js` |
| `run.py` | simple entry point for one scenario |
| `.githooks/pre-commit` | page freshness + both test files; blocks on failure |
| `setup-hooks.sh` | enables the hook; run once per clone |
| `requirements.txt` | the Python dependencies. JavaScript has none |

`build_page.py` must be re-run after any change to `model.js`. The pre-commit
hook will not do it for you, but `build_page.py --check` will tell you that you
forgot, and the hook runs it first — the page embeds its own copy of the model,
so a stale HTML runs different physics from the file next to it.

## What is validated, and against what

Two classes of target, and they are not equal. Clinical studies are
measurements in patients and are the arbiters. ICSM/Nottingham results are
another group's simulation — useful comparators, not truth.

### Clinical (all currently pass)

| study | target | model |
|---|---|---|
| Toner 2019, lean sham | 447 s (IQR 405-525) | 402 s |
| Toner 2019, lean buccal | 750 s (IQR 750-750) | held |
| Heard 2017, obese control | 296 s (IQR 244-314) | 288 s |
| Heard 2017, obese buccal | 750 s (IQR 389-750) | held |
| O'Loughlin 2020, SpO2 at 18.7 min | 58/62 no desaturation | 98.9% |
| O'Loughlin 2020, venous PCO2 rate | 0.15 (0.10) kPa/min | 0.22 |
| Sci Rep 2023, cardiac output at 15 min | +30% | +36% |
| Sci Rep 2023, PaCO2 rate | 2.1 mmHg/min | 2.4 |
| Lane / Ramkumar, 20 deg head-up | +24 to +36% | +33% |
| Altermatt, BMI 35, 30 deg | +32% | +40% |
| Dixon, BMI 44, 25 deg | +32% | +24% |

Two things the model reproduces that were not built into it, and which are
therefore worth something: the arterial-venous CO2 gradient REVERSES during
apnoea (O'Loughlin describe this and attribute it to pulmonary CO2 retention
plus the Haldane effect), and failure requires TWO coincident abnormalities
rather than one, which matches Toner's single outlier and O'Loughlin's two.

### The two implementations against each other

`test_parity.py` runs `apnoea_core.py` and `model.js` on identical inputs and
requires every output to agree within 1%. It currently does with three orders
of margin — worst case 0.03%, and four of the six scenarios agree exactly —
across long apnoeic oxygenation, a desaturating room-air control, the reopening
inrush, a sealed airway and a partial obstruction. The two scenarios that are
not exact are the ones that drive a compartment to gas exhaustion, where the
per-species floor differs (1e-9 mL in Python, 1e-12 in the JavaScript); that
and the other latent differences are listed at the foot of `test_parity.py`.

It did not when it was written. `model.js` had kept the well-mixed nitrogen
exchange that `apnoea_core.py` replaced with a per-compartment one, and by 15
minutes the two were 21% apart on PaO2, 14% on shunt and 25% on absorption
atelectasis. Nothing caught it because SpO2 — the output anyone looks at —
stayed within 1% throughout: the oxygen plateau holds saturation flat while the
gas exchange underneath it drifts. Anything comparing only desaturation times
would have called the port fine.

Three smaller drifts went with it: a sealed airway could vent gas through an
airway that is by definition closed; `lungO2` was reported one step stale,
which is 35% out at an inrush; and the HPV stimulus PvO2 was refreshed only
once a second where the Python refreshes it every step, so hypoxic
vasoconstriction was driven by a tension up to 0.9 s old. That last one is
small — 0.03% on the HPV fraction — but it was the entire residual, and
removing it made four of the six scenarios agree exactly.

The comparison is limited to where the model says it predicts anything —
SaO2 >= 70% and PaCO2 <= 150 — see Numerical notes for why the upper CO2
bound is not merely caution. Saturation is compared over the whole run
regardless.

### Model comparators

| study | target | model |
|---|---|---|
| Laviola 2020, airway rescue | 42.3 (4.4) kPa | 38.7 kPa |
| Ellis 2022, pregnancy BMI 24 | 25.4 min | 18.1 min |
| Ellis 2022, pregnancy BMI 50 | 9.9 min | 5.8 min |

### Known disagreement

Mohanty 2021 (buccal RAE vs nasal cannula, obese) reports a buccal mean of
375 s where Heard reports a median of 750 s in a similar population. Four
candidate reasons, roughly in order of confidence:

1. The statistics are not comparable. Heard is a median against a 750 s
   ceiling; Mohanty a mean against a 600 s ceiling reached by 3/25. Heard's
   IQR runs down to 389 s, so his lower quartile is Mohanty's mean.
2. Mohanty's patients were more shunted, and they measured it: starting PaO2
   328 mmHg after preoxygenation to end-tidal O2 >90% implies about 16%
   shunt. Neither Heard nor Toner reports a starting PaO2.
3. Time zero. Heard began at loss of verbal response, Mohanty after full
   relaxation.
4. Videolaryngoscopy with a simulated grade 3 view may open the airway less
   than prolonged direct laryngoscopy.

Their BETWEEN-ARM result is sound. It is the absolute number that should not
be compared with Heard's.

## Parameter provenance — read before quoting any obese result

### Anchored in measurement
- O2 dissociation: Severinghaus with Kelman Bohr correction. Exact.
- HPV: Marshall BE et al. Respir Physiol 1994;96:231-47. PSO2 =
  PvO2^0.41 x PAO2^0.59, half-max 39.4 mmHg, PVR max 3.15x.
- Cardiac output response: 0.97% of baseline per mmHg PaCO2, from the Sci Rep
  n=91 measurement in exactly this population. Split evenly between rate and
  stroke volume because the source does not separate them.
- Nitrogen kinetics: real Ostwald solubilities and perfusion fractions, giving
  time constants of ~3 min vessel-rich, ~40 min muscle, ~4 h fat.
- Bed tilt: fitted to four positioning trials.
- Induction: FRC drop 300-500 mL, VO2 drop 0.27 mL/kg/min (ICSM convention).

### Chosen, not fitted — THIS LAYER CARRIES EVERY OBESE RESULT
- `max_closed` 0.25 — collapse ceiling
- `cc_at_20`, `cc_per_year`, `cc_per_bmi` — the closing-capacity regression is
  invented, not a published equation
- `perfusion_gain` 1.2 — dependent lung takes more than its share
- `inflow_mech_frac` 0.18 — absorption atelectasis
- `recruit_frac` 0.65 — how much reinflation recovers
- `vq_log_sd` 0.70 and `tau_mix` 45 s — these two pull against each other.
  At spread 0.5 / mixing 25 s the model hits Toner and Heard almost exactly;
  at spread 0.9 / mixing 90 s it is 30% short. The middle was chosen rather
  than tuned, deliberately, so the trials stay as validation.

### Unverified
- Douglas, Jones & Reed 1988 CO2 content constants were written from memory.
  Absolute content runs ~6% high (51 vs 48 mL/dL arterial). Slope is right so
  dynamics are unaffected, but CHECK AGAINST THE PAPER before publishing.
- The bradycardia curve and the terminal rhythm timings (18/12/6 bpm, ten
  seconds each) are illustrative. Anything below SaO2 ~70% is not predictive.

## Numerical notes

- The inflow-compliance loop has tau = R x Crs. At R=2 that is 0.17 s, so
  **dt must stay well under 0.1**. dt=0.2 is unstable and gives PaCO2 168
  where the converged answer is 71. Use dt=0.05 for anything published;
  dt=0.1 is fine for the interactive page where only desaturation times show.
- The instantaneous nadir does not converge until dt=0.05. Prefer a
  ten-second rolling minimum, which is also what a monitor would show.
- Runs continued past the terminal rhythm are numerical noise. Do not plot
  them; `stop_sao2` exists for this.
- **Above PaCO2 ~150 the arterial CO2 inverse misbehaves.** Not just
  unvalidated — wrong. In a 15-minute obstructed-then-rescued obese run, PaCO2
  reads 218 mmHg at 650 s, 138 at 700 s, 126 at 725 s, 230 at 825 s: twelve of
  ninety ten-second intervals have PaCO2 FALLING, once by 43.8 mmHg. With no
  ventilation there is nothing to remove CO2, so it cannot fall at all.
  `pco2_from_co2_content` solves a residual whose inner SO2/pH fixed point is
  poorly conditioned at that end, so successive one-second solves land on
  different roots. Both implementations do it and agree with each other while
  doing it, so it is not a port problem. 150 is already `co2_response_cap`,
  past which this file says the model is not valid, and every benchmark
  finishes well below it — so nothing published is affected. But the model
  does not merely stop being predictive up there, it starts producing
  impossible numbers, and if anything is ever to be claimed in that range this
  needs fixing first. Reproduction is in the note at the foot of
  `test_parity.py`.

## Open work, roughly by value

1. **Measured shunt fractions in obese anaesthetised patients against BMI.**
   Would anchor two of the four collapse parameters. This is the single most
   valuable missing dataset. Mohanty's starting PaO2 of 328 mmHg is one such
   measurement and implies ~16% shunt; more would pin the regression.
2. **Toner's tracheal oxygen traces**, if they still exist. Would let
   pharyngeal patency be fitted from measurement rather than assumed. In their
   absence, present pharyngeal FO2 as a declared sensitivity band; Toner's
   published primary outcome (tracheal O2 maintained >90%) already bounds it,
   and O'Loughlin bypasses the question by delivering below the glottis.
3. **Reconcile or explain the Ellis pregnancy comparator.** 40% short in both
   arms and has resisted every structural change. The pregnancy physiology in
   our configuration was assembled from textbook multipliers, not their
   methods, so the fault may be ours.
4. **Check the Douglas 1988 constants**, and while in `bloodgas.py`, make
   `pco2_from_co2_content` well-behaved above PaCO2 150 (see Numerical notes).
   A second root-selection problem sits in the same residual, and it is closer
   than it looks: `co2_content` has a pole at pH 8.142, and the residual goes
   multi-rooted once the pH at the bracket's low end (PCO2 3) passes it, which
   happens from base excess **-0.50** over Hb 10-18 and T 33-38. Base excess 0
   — the value the model actually uses — is therefore already past the pole.
   What keeps the current path clean is only that the band of CO2 contents
   which traps the solver is narrow: at BE 0 the two implementations agree to
   1.3e-7 over 1500 random states. That margin is incidental, not structural,
   so do not record this as "safe below BE +6".

   Where it bites they disagree completely — content 69.0, BE +6, Hb 14, O2
   content 16 gives Python PCO2 3.0004 mmHg at pH 8.203 against `model.js`'s
   58.285 at pH 7.358, 94.9% apart. Note which is which: 3 mmHg at pH 8.2 is
   the spurious root against the bracket's lower end, and it is the PYTHON on
   it. So this is the one place where making the port track the reference is
   the wrong move; fix the bracket in `bloodgas.py` so only the physiological
   root is admitted. It becomes reachable the moment anyone models a metabolic
   alkalosis.
5. **Paediatric parameterisation.** Absent entirely; Hardman & Wills 2006
   cannot currently be tested.
6. **A simulation study of operator performance under stable versus falling
   saturation.** The clinical argument rests on a chain — falling saturation
   raises stress, stress degrades decision-making, that produces fixation and
   trauma. Every link has support; the causal chain itself has none. Needs no
   patients and would convert the central claim from plausible to shown.

## Findings worth keeping

- **The plateau.** Substituting Fick into the shunt equation gives
  CaO2 = Cc'O2 - [f/(1-f)] x VO2/(10Q). A stable fixed point that exists only
  because apnoeic oxygenation holds Cc'O2 constant. Without it there is no
  fixed point and saturation falls without limit. The plateau is set by shunt
  fraction almost alone: critical shunt for a 90% plateau is 0.36-0.37 across
  every phenotype, because VO2 and cardiac output scale together.
- **Patency is near-binary.** Aventilatory mass flow is only ~3.3 mL/s, so a
  1 mm channel costs about 1 cmH2O and a 3 mm channel 0.016. Only a true seal
  defeats the device. Length matters far less than radius: across the whole
  anatomical range the critical calibre varies only 0.49-0.64 mm.
- **Mass flow does not collapse the airway.** It pulls the pharynx 0.07 cmH2O
  below atmospheric at a 2 mm aperture, against the -11 cmH2O of ordinary
  inspiration and measured critical closing pressures of -15 to +5. Apnoeic
  oxygenation is uniquely undemanding of a collapsible pharynx - an argument
  HFNO cannot make, since its benefit partly depends on pressure it generates.
- **Blood clears, mucus does not.** Both face a capillary threshold and
  mucus's is lower. The difference is yield stress: blood is Newtonian and
  clears in milliseconds; mucus does not flow below yield at any pressure.
- **The inrush is the decision point.** When the airway first opens after
  obstruction, ~600 mL rushes in within seconds. If the pharynx holds air that
  is ~474 mL of nitrogen delivered as a bolus, against ~241 mL over the
  following 2.5 min of mass flow. The bolus is twice the drip, which is why
  switching the device on when a difficult airway is recognised is too late:
  in the modelled scenario, starting at 6:10 gives a nadir of 31%,
  indistinguishable from never using it.
- **Every disagreement found so far cuts the same way.** The model is too
  pessimistic about who avoids desaturating on good tracheal oxygen, not too
  generous about the device. The buccal-versus-control gap is unaffected.
