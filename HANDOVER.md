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
| Stock 1989, obstructed, first minute | 12 mmHg | 12.2 |
| Stock 1989, obstructed, 1-5 min slope | 3.4 mmHg/min | 4.3 |
| Varat 1972, cardiac output rise below Hb 7 | none above 7 | none |
| Circulation 1963, cardiac output at Hb 4.5 | 1.97x (CI 6.3 vs 3.2) | 1.97x |
| Moreault 2021, sealed lung, 1008 mL gas absorbed | -20 (5) cmH2O | -30.4 |
| Moreault 2021, sealed lung, 1260 mL gas absorbed | -31 (10) cmH2O | -50.0 |
| Lane / Ramkumar, 20 deg head-up | +24 to +36% | +33% |
| Altermatt, BMI 35, 30 deg | +32% | +40% |
| Dixon, BMI 44, 25 deg | +32% | +24% |

### CO2 under obstruction: three defects, found 2026-09

Every CO2 benchmark above uses a PATENT airway. Under OBSTRUCTION the model
was producing 41.75 mmHg/min against Stock's measured 3.4 -- twelve times
too fast -- and nothing in the suite looked, so nothing failed. There is now
a `test_stock_1989` and it should not be removed.

Three separate defects, all in the same few lines of gas exchange:

1. **One pH for the whole lung.** `ph_c` was solved once from mean alveolar
   PCO2 and applied to every compartment. Pricing a compartment at 60 mmHg
   with the lung mean's pH inflated its CO2 content by up to 2.45x; content
   went linear in PCO2, losing the dissociation curve's saturation, and
   arterial PCO2 ran to 250 while alveolar sat at 112 and venous at 113 --
   arterial outside both, which is impossible. Now solved per compartment.

2. **The pole at pH 8.142 is reachable, and per-compartment pH reaches it.**
   Item 4 below was right that this was closer than it looked. A compartment
   whose gas has collapsed onto the 1e-9 floor has a PCO2 that is the ratio of
   two floor values: a sealed run visits 1.8e-06 and 566 mmHg. Anything below
   ~2.4 mmHg puts the pH past `co2_content`'s pole, where content changes
   sign. The lung mean was always physiological so it never met the pole;
   per compartment walks into it, and Python and JavaScript landed either side
   and disagreed by 8.5%. The pH solve input is now clamped to [5, 250].

3. **Collapsed compartments kept their perfusion.** `q_w` is the resting
   distribution and never changed with collapse. Collapse was handled only in
   aggregate, as `shunt`, so the right AMOUNT of blood bypassed but not from
   the right COMPARTMENTS: a fully collapsed unit still received its full
   share of the non-shunted blood and set arterial content with its floor-value
   gas. Non-shunted perfusion is now weighted by `q_w * (1 - coll_c)`.

**The CO2 store parameters were deliberately NOT touched.** Halving
`v_tis_co2_fast` hits Stock's 3.4 exactly, and that is the trap: it buries
three real bugs under a parameter that then no longer means what its name
says. Fixing the three and refitting nothing leaves the obstructed slope at
4.3 against 3.4, which is where it stands -- a known 26% residual, recorded
rather than tuned away.

**Open.** Stock found a LOGARITHMIC fit best, i.e. a decelerating curve; ours
accelerates modestly over minutes 1-5, because by then the sealed lung has
lost half its volume and the rising shunt sets arterial CO2. Nothing measured
settles which is right over that window -- 14 patients fitted piecewise cannot
resolve the curvature -- so the benchmark guards only against runaway.

### Haemoglobin is a dial now, and the circulation answers to it

Hb was always in the physics -- oxygen content, CO2 content, the Van Slyke
base excess through cHb, the Haldane term. What was missing was any
CIRCULATORY response to it, and without one the low end of the range was not
a patient: at Hb 4 with a fixed cardiac output, oxygen delivery came to 0.91
times consumption. The tissues were being sent less than they were using
before the apnoea started.

Two measured anchors, neither fitted to anything of ours:

  Varat, Adolph & Fowler, Am Heart J 1972;83:415-26 -- the rise begins at
  7 g/dL or less. Above that, nothing.

  Hemodynamic Effects of Chronic Severe Anemia, Circulation 1963;28:346 --
  Hb 4.0-6.5 (mean 4.5) gave a cardiac index of 6.3 L/min/m2 against a
  normal ~3.2. Very nearly double.

A power law through both, (7/hb)**1.535, capped at 3x. Delivery at Hb 4 is
now 2.16 times consumption. Systemic vascular resistance is divided by the
same factor, because reduced viscosity and vasodilatation are WHY the output
rises: without that, mean arterial pressure would double alongside it, where
real anaemic patients run a normal or slightly low MAP on a markedly reduced
resistance. MAP holds at 68 mmHg across the whole range.

**It is exactly 1.0 at and above 7 g/dL**, so every pre-existing benchmark --
all of which run Hb 14-15 -- is untouched by construction, and the first
check in `test_anaemia_cardiac_response` asserts that inertness. A change to
the circulation that quietly moved the oxygenation results would be very hard
to trust afterwards.

Two things to know:

- **The knee at 7 is hard, and reality's is soft.** Varat says the rise
  "usually" begins there, "with many exceptions". The artefact is that the
  worst oxygen delivery in the whole range sits exactly at Hb 7 (1.56x),
  because that patient has the small blood store and no compensation yet.
  Nothing incoherent comes of it, but a smooth onset would be more faithful
  if anyone wants to source one.
- **Desaturation time barely moves with Hb** -- 298 s at Hb 15 against 302 s
  at Hb 4, obstructed. That is not a bug. During apnoea the FRC oxygen
  dominates the store, not the blood, so quartering the haemoglobin barely
  touches the time course. It surprises people, including me: I predicted a
  large shortening and measured almost none.

Cyanosis, when the head visualisation lands, should be driven by
DEOXYGENATED haemoglobin rather than saturation -- roughly 5 g/dL is the
clinical threshold. At Hb 15 the head starts turning around SpO2 67%, which
is right; at Hb 4 deoxyHb cannot reach 5 g/dL at ANY saturation, so that
patient can never look cyanotic however dead they are. That is the classic
trap, and driving it from deoxyHb gives it for nothing.

### Axial cardiogenic mixing: tested, bounded, not the answer

`tau_mix` stirs gas BETWEEN compartments. The same heartbeat also stirs it
ALONG the airway, and that arm is absent: there is no outflow term anywhere,
`inflow` is clamped non-negative, so with a patent airway CO2 has no route out
of the lung at all. That looked like the missing CO2 clearance path.

It was built and measured. As a diffusive chain over pharynx | dead space |
alveoli, scaling with cardiac output, with the pharyngeal boundary present
only when the airway is patent -- so obstruction removes the boundary rather
than the stirring, the dead space equilibrates in seconds, and net transport
stops by itself. Gated that way the obstructed case is bit-identical at every
strength (12.16 mmHg first minute, 4.35 mmHg/min slope), which is the right
behaviour and worth keeping if anyone rebuilds this.

**It is capped by oxygenation, not by CO2.** Dispersion is species-independent,
so the same chain that carries CO2 out carries nitrogen IN whenever the
pharynx is room air. Toner's sham arm is the binding constraint:

| end-to-end mL/min | Toner sham (380-525 s) | patent PaCO2 (2.1) |
|---|---|---|
| 0 | 402 | 2.45 |
| 50 | 394 | 2.44 |
| 100 | **377 FAIL** | 2.40 |
| 300 | 313 | 2.16 |

The value that would fix CO2 is ~300 mL/min. The ceiling is ~75. So at any
strength the oxygenation data permits -- about 1 mL per beat -- it changes the
patent CO2 rate by ~1%, and it is NOT the explanation for CO2 clearance. That
is why the store and curve-shape account above is the one the model uses.

Two caveats before anyone re-opens this. The bound assumes pharyngeal FO2 =
0.21 in the sham arm, which item 2 below already flags as uncertain; a higher
residual pharyngeal FO2 would loosen it. And a first attempt at this measured
the mechanism at roughly a tenth of its true strength by parameterising the
per-node conductance rather than the end-to-end one -- the dead space is
discretised into `vd_segments` for the inrush CFL condition only, and putting
physics on that number makes it depend on a numerical choice.

Worth knowing for anything that reads per-compartment gas: **a collapsed
compartment's gas fractions are numerical debris**, not small numbers. Any new
code that touches `fr_c` per compartment must either clamp or weight by the
open fraction, exactly as these three fixes do.

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
| ICSM jet 2026, PaO2 at cricothyroidotomy | 28.3 (0.4) mmHg | 29.1 |
| ICSM jet 2026, PaCO2 at cricothyroidotomy | 84.6 (4.4) mmHg | 82.7 |
| ICSM jet 2026, time to SaO2 40% | ~510 s | 500 s |

### The collapse investigation, 2026-09 -- read before touching the mechanics

Chasing the jet-insufflation scenario exposed the mechanics limb, which had
never been benchmarked by anything. What follows is the whole investigation,
including the parts that failed, so nobody repeats them.

**The question.** At SaO2 40% after complete obstruction the model puts the
lung at 590 mL -- 29% of FRC -- on the `p_collapse = -50` floor. The comparator
model's published pressures implied a lung near its relaxation volume. Same
oxygen uptake, opposite sign of pressure.

**What is NOT the problem.** The volume loss is forced: 1936 mL of O2 absorbed
minus ~364 mL of nitrogen returned leaves 1572 mL, and VO2 is benchmarked. The
-50 then follows arithmetically -- the linear term gives -16.6 and the sub-RV
stiffening the other -38.9. No setting of the chosen-not-fitted parameters
escapes it: halving `stiff_below_rv` AND dropping `rv` to 700 mL still only
reaches -26.

**A hypothesis that FAILED, and why.** Collapse ought to be self-limiting:
units that close leave the mechanical circuit, so they stop contributing FRC
and compliance and the deficit is relieved rather than deepened. Implemented
as a closing-pressure feedback, it did not work -- the floor was reached at
420 s instead of 300 s and that was all. The reason is worth knowing:
**the compartments that close first hold 50% of the perfusion but only 25% of
the volume**, so closing the dependent lung creates a large shunt while
relieving almost no mechanical deficit. Mapping "low V/Q" onto "the dependent
lung" is fine for gas exchange and wrong for mechanics; these compartments are
a FUNCTIONAL decomposition, not a spatial one, and the model cannot represent
"the dorsal half collapses and takes half the thoracic volume with it". That
is architectural, not a parameter.

**Nitrogen sets the floor.** Absorption is self-limiting after all, but through
gas exchange rather than mechanics: it stops dead at 430 mL when alveolar PO2
falls to mixed venous, and the residual is 81% nitrogen at tissue equilibrium.
So anything touching body nitrogen stores -- preoxygenation, obesity, the fat
compartment's four-hour time constant -- moves the floor. Dropping FEO2 from
0.87 to 0.60 puts the trigger pressure at -10.9 instead of -50. That lever is
not available (0.87 is right for three minutes of preoxygenation) but it says
what the floor is made of, and nothing benchmarks it.

**Then the measurement arrived, and the model was right.** Moreault 2021
sealed one lung in patients, chest closed, transducer in the bronchus:
-20 (5) cmH2O at 504 mL resorbed, -31 (10) at 630 mL, returning toward
atmospheric once the pleura was opened. A sealed lung DOES develop large
negative pressure. Compared at MATCHED GAS ABSORBED -- their volumes were measured at
atmospheric pressure, and a lung shrinks by LESS than the gas that leaves it
because the remainder expands, an error worth not repeating -- and doubled for
a whole lung, we give -30.4 where they measured -20 (5) and hit the -50 floor
where they measured -31 (10). So the DIRECTION and regime are confirmed and
the MAGNITUDE is not: we run 10-20 cmH2O too negative. That is the first
evidence ever brought to bear on `stiff_below_rv` and it says the term is too
stiff. `test_moreault_2021` asserts the direction, which was genuinely in
doubt; the overshoot is under Known disagreement.

### The comparator model, and a correction

I concluded from the main text of Laviola 2020 and the 2026 jet paper that
ICSM modelled shunt as a fixed 1-3% input with no atelectasis and no lung
mechanics. **That was wrong**, and it was wrong in an avoidable way: it rested
on word-absence in short clinical papers and on reading a cohort-configuration
table as a model specification. The supplementary material (SDC S3a) shows
100 alveolar compartments in parallel, each with configurable compliance,
inlet resistance, vascular resistance, extrinsic pressure and threshold
opening pressure; alveolar pressure as a cubic in volume; `P_ext` explicitly
carrying "the outward pull of the chest wall"; volume-dependent PVR; and
hypoxic vasoconstriction. The 1-3% is the anatomical shunt ON TOP of
V/Q-derived shunt from those 100 compartments. Structurally the two models are
close relatives.

**Where they genuinely differ is one parameter.** ICSM's threshold opening
pressures are **TOP = 3-12 cmH2O**. Rothen 1993 measured re-expansion of
atelectasis by CT in anaesthetised adults with healthy lungs and found
20 cmH2O does essentially nothing (6.4 -> 5.9 cm2), 30 gives 45%, and 40 is
needed to clear it -- and that repeated inflations add nothing. A 1000 mL
insufflation is, in Rothen's own calibration, about a 20 cmH2O inflation.
So whether a narrow-bore cannula insufflation can act as a recruitment
manoeuvre turns entirely on whether TOP is 3-12 or 30-40. If it is the latter,
recruitment needs pressures that also exceed the safe volume envelope: there
is no window between the pressure that recruits and the pressure that injures.
This is the open question, and it is empirically settleable.

**And the gas state agrees anyway.** Despite all of the above, at the moment
of cricothyroidotomy the two models land in the same place: PaO2 29.1 vs
28.3 (0.4), PaCO2 82.7 vs 84.6 (4.4), time to SaO2 40% 500 s vs ~510 s, none
of it tuned. The mechanics disagreement does not propagate into the blood
gases. `test_icsm_jet_2026` records the gas channels.

### Known disagreement

**A CONFLICT between two clinical measurements -- read this before touching
`stiff_below_rv`, `itp_fraction` or `sv_itp_gain`.** These three are coupled,
and two measurements in patients now pull against each other through them.

Moreault's pressures say the sub-RV stiffening is far too stiff.
`stiff_below_rv = 0.15` is not the retained compliance directly: the term is
additive in series, so the lung keeps `stiff/(1+stiff)` of its compliance
below RV, i.e. **13%** -- an eightfold stiffening the instant it crosses
residual volume, and it is what drives the pressure onto the -50 floor.
Softening it fixes the pressure. It also breaks Stock:

    stiff  retained  P@1008 (-20)  P@1260 (-31)  Stock 1-5 min (3.4)
    0.15     13%        -30.4         -50.0          4.3   in band
    0.50     33%        -24.4         -40.4          4.9   FAILS
    1.00     50%        ~-23          ~-34           5.1   FAILS
    2.00     67%        -22.2         -30.4          5.2   FAILS

**The coupling is the Muller effect, not the gas.** Alveolar PCO2 barely
moves across that sweep (63.0 -> 63.3 at 300 s). What moves is the heart: the
vacuum suppresses stroke volume, and lifting the vacuum lifts cardiac output,
which delivers CO2 to the lung faster and steepens the arterial rise.

    stiff      P     ITP   stroke vol    CO   PaCO2 at 300 s
    0.15   -50.0   -30.0       56.1     4.30      69.6
    2.00   -28.1   -16.9       58.8     4.57      72.8

So: Moreault says less vacuum; less vacuum means more cardiac output; more
cardiac output means a faster CO2 rise; and Stock says our CO2 rise is
already 26% too fast at 4.3 against 3.4.

**Nothing was changed, deliberately.** Making Stock pass again would mean
moving `itp_fraction` or `sv_itp_gain` at the same time, and those are exactly
as unvalidated as the term being fixed -- `sv_itp_gain` carries its own note
saying the pig magnitude does not transfer and tuning to it would be wrong.
One unvalidated change compensating another is how the single lung-wide pH,
the perfusion of collapsed units and the pole at 8.142 all survived for so
long underneath CO2 store parameters that had been sized to hide them. Do not
repeat it. If you soften the sub-RV term, Stock will fail and that failure is
information, not an obstacle.

**What would settle it:** one study measuring airway pressure AND PaCO2 in the
same patients during obstructed apnoea -- a clamped tracheal tube, which is
physiologically the same event as any circuit disconnection. At present we
have Moreault's pressures in one group and Stock's CO2 in another, thirty
years apart, with no way to know which limb is wrong. That study is designed
and was ready for ethics.

**Pressure under obstruction runs too negative.** Moreault 2021 measured
-20 (5) cmH2O at 504 mL of gas resorbed from one sealed lung and -31 (10) at
630 mL. Doubled for a whole lung we give -30.4 and -50.0. The sub-RV
stiffening term is the likely cause: at these volumes it contributes about
-39 of the total against -17 from the linear term, and it has never had data
behind it. Do not simply soften it -- the collapse notes above show the
volume loss itself is forced by benchmarked VO2, so anything done here has to
keep `test_moreault_2021` and the Stock CO2 rates.

**Haemodynamics below SaO2 ~70%.** At the cricothyroidotomy point ICSM gives
CO 2.7 (0.1) L/min and MAP 57.4 (2.4) mmHg; we give 1.98 and 29. Our patient
is far more shocked. This is not defended -- it is the region the parameter
provenance section already calls illustrative and not predictive, and a MAP of
29 at SaO2 40% is the less plausible of the two. Deliberately NOT given a
benchmark band wide enough to pass, because that would hide it. The gas
channels of the same comparison are benchmarked and agree closely.

**Weight sensitivity of the apnoea.** Our PaCO2 at the trigger spans 64-121
mmHg across 46-90 kg; theirs has an SD of 4.4 over the same range, and their
time to SaO2 80% has an SD of 1 second across the whole cohort. Our
desaturation time varies far more with body size than theirs does. Unexplained.

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

   **Update 2026-09: this became reachable and was hit.** Per-compartment pH
   drove it directly (see "CO2 under obstruction" above). The clamp added
   there guards the alveolar path only. The bracket in `bloodgas.py` is still
   unfixed and this remains the right item to do.

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
