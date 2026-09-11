# Evidence map for the three linked variables

Searched September 2026. **Status: four papers have now been READ IN FULL**
(Wright 2023, Condos 1987, Ebata 1991, and the OLV review) because they were
supplied as files. The rest still rest on abstracts and search summaries: this
environment allows web *search* but blocks every publisher domain, verified
across 17 hosts and both fetch tools. Entries are marked READ or ABSTRACT
ONLY. Nothing marked ABSTRACT ONLY should be entered as a benchmark. The
mistake this file is designed not to repeat is the ICSM one, where a
conclusion was drawn from what a short document did not say.

Reading the three haemodynamic papers overturned two conclusions that had been
recorded from their abstracts. Both are corrected below and in HANDOVER.

The three variables are airway pressure under obstruction (**P**), the rate of
rise of arterial CO2 (**C**), and the haemodynamic response (**H**). The claim
under test is that no study measures more than one of them in the same person.

**That claim was too strong and is corrected here.** Two pairings exist. The
missing pairing is the one that matters most.

---

## What exists, by pairing

| Pairing | Exists? | Best source found |
|---|---|---|
| P alone | yes | Moreault 2021 |
| C alone | yes | Stock 1989; brain-death apnoea-test literature |
| H alone | yes | large |
| **P + H** | **yes** | Wright 2023 (n=19); Condos 1987 (n=10) |
| **C + H** | **yes** | Ebata 1991 (n=9), patent airway |
| **P + C** | **NOT FOUND** | — |
| P + C + H | **NOT FOUND** | — |

So the protocol's premise survives, but its statement of the gap must change.
The gap is not that nobody has paired anything. It is that **nobody has paired
pressure with CO2**, which is precisely the pairing that identifies which limb
of the model is wrong, because those two are what the Muller effect couples.

---

## P + H — human Mueller manoeuvre. This bears on `sv_itp_gain`. READ.

Two studies measure intrathoracic pressure and stroke volume simultaneously in
normoxic humans. Both find a clear effect, and both put our parameter too LOW.

**Wright SP, Dawkins TG, Harper MI, Stembridge M, Shave R, Eves ND. Mueller
maneuver attenuates left atrial phasic volumes and myocardial strain in healthy
younger adults. Am J Physiol Heart Circ Physiol 2023;325:H1235-H1241.** READ.
n=19 healthy (10M/9F, 24+-4 y), Mueller to **ITP -30 cmH2O held 15 s**, six
repeated trials, echocardiography with speckle tracking.

    LV SV, mL     70 +- 16  ->  63 +- 16 (early)  ->  60 +- 16 (late)   back to 72
    LV EDV, mL   120 +- 26  -> 113 +- 28          -> 108 +- 28
    LV ESV, mL    49 +- 11  ->  49 +- 14          ->  48 +- 15   (unchanged)
    LV EF, %      59 +-  3  ->  56 +-  4          ->  55 +-  5
    HR, bpm       60 +- 11  ->  64 +- 13          ->  63 +- 11

SV fell **14.3%** at ITP -30 cmH2O sustained 15 s, giving a gain of
**0.00476 per cmH2O**; at 5 s it was 10%, i.e. 0.0033. ESV unchanged with EDV
down means this is a **preload** effect -- impaired filling, not impaired
ejection -- which is the same mechanism that would operate in our patient.

**Condos WR Jr, Latham RD, Hoadley SD, Pasipoularides A. Hemodynamics of the
Mueller maneuver in man: right and left heart micromanometry and Doppler
echocardiography. Circulation 1987;76:1020-8.** READ. n=10 with normal
haemodynamics at elective cardiac catheterisation, multisensor micromanometry.

    cardiac output   6.0 +- 1.3  ->  5.3 +- 2.0 L/min   p=.026
    stroke volume     83 +- 18   ->   74 +- 29 mL       p=.046
    heart rate        71 +- 9    ->   74 +- 9           NS
    SVR             1331 +- 372  -> 1892 +- 738         p=.013
    mean RA pressure   7 +- 3    ->  -17 +- 14 mmHg     p=.0002
    LV end-diastolic  12 +- 4    ->   -3 +- 13 mmHg     p=.0025
    mean PA           18 +- 4    -> -0.9 +- 16 mmHg     p=.0007

Mean right atrial pressure is the best available proxy for the intrathoracic
swing: **-24 mmHg, i.e. -32.6 cmH2O**. SV fell 10.8%, giving a gain of
**0.0033 per cmH2O**. Note also that this study overturned the prior teaching
that a sustained Mueller INCREASES right heart flow: it does not, it falls.

**Our `sv_itp_gain` is 0.0025.** Both human measurements are higher --
0.0033 and 0.00476 -- so the parameter is **conservative, by between 1.3x and
1.9x**. It is not unevidenced, and it is not too large. An earlier note in
HANDOVER said it was "not evidenced"; that was wrong and is corrected.

What remains true is that its CITATION does not support it: Chen & Scharf's
oxygen arm shows nothing at -42 cmH2O in sedated pigs.

**Duration is still the open question.** A Mueller manoeuvre is 5-15 s; our
patient reaches -15 cmH2O over three minutes. Wright's own data show the effect
GROWING from 5 s to 15 s (10% then 14.3%), which argues against it being a pure
transient, but neither study goes past about 20 s. Nothing published says what
happens at three minutes.

### And it barely matters, which was the surprise

Raising the gain to Wright's measured value changes almost nothing. Run at
hb 15.0, exactly as `test_stock_1989` does:

    stiff  sv_itp_gain | P@1008  P@1260 | 1st min  slope | CO@300  SV@300  shunt
     0.15     0.00250  |  -30.4   -50.0 |   12.2   4.35  |  4.30    56.1  0.181
     0.15     0.00330  |  -30.4   -50.0 |   12.2   4.30  |  4.19    54.6  0.180
     0.15     0.00476  |  -30.4   -50.0 |   12.2   4.24  |  3.98    51.9  0.180
     2.00     0.00250  |  -22.2   -30.4 |   12.2   5.15  |  4.57    58.8  0.181
     2.00     0.00476  |  -22.2   -30.4 |   12.2   5.01  |  4.37    56.4  0.180

Adopting the human value moves the Stock slope 4.35 -> 4.24 against a target of
3.4. **The Muller term does not rescue Stock**, and softening
`stiff_below_rv` to satisfy Moreault still fails it at 5.01 even with the human
gain. The knot is not resolved by this.

### The recorded mechanism for the knot is contradicted by the model itself

HANDOVER says "the coupling is the Muller effect, not the gas". The table above
says otherwise:

    gain 0.0025 -> 0.00476 at stiff 0.15:  CO -7.4%,  slope -2.5%
    stiff 0.15 -> 2.00 at gain 0.0025:     CO +6.3%,  slope +18.4%

Two manipulations of comparable size, acting through cardiac output, with
slope sensitivities differing about **sevenfold** and in opposite proportion.
Cardiac output cannot be the mediator of the stiffness effect. Shunt is
identical across all five rows (0.180-0.181), so it is not shunt either. What
the actual mediator is has NOT been established here, and no guess is recorded.
`stiff_below_rv` still controls the Stock slope strongly; the reason given for
why it does is wrong.

## C + H — the brain-death apnoea test. READ. **My earlier reading of this was wrong.**

**Ebata T, Watanabe Y, Amaha K, Hosaka Y, Takagi S. Haemodynamic changes during
the apnoea test for diagnosis of brain death. Can J Anaesth 1991;38:436-40.**
n=9, severe head injury or cerebrovascular disease, Tokyo. Ventilator
disconnected ten minutes with oxygen insufflated at 6 L/min through a 2.1 mm
catheter 2-5 cm above the carina, so the airway is **patent** and intrathoracic
pressure stays near zero. Pulmonary artery catheter, thermodilution CO
(mean of three), radial arterial line.

                        Before        After        P
    pH               7.37 +- 0.01  7.17 +- 0.02  <0.001
    PaCO2, mmHg        45 +- 1       78 +- 3      <0.001
    PaO2, mmHg        373 +- 46     332 +- 38      NS
    MAP, mmHg          80 +- 5       81 +- 7       NS
    HR, bpm           100 +- 7      100 +- 7       NS
    mean PAP, mmHg     11 +- 1       17 +- 2      <0.01
    PCWP, mmHg          5 +- 1        5 +- 1       NS
    RAP, mmHg           3 +- 1        3 +- 1       NS
    SVR, dyn.s.cm-5  1560 +- 252   1387 +- 259     NS
    PVR, dyn.s.cm-5   112 +- 23     183 +- 37      NS
    CO, L/min         4.8 +- 0.7    5.7 +- 0.8   <0.05

**I previously wrote that this shows our CO2-to-cardiac-output gain is 1.8x too
strong. That was wrong, for four reasons the full text makes plain.**

1. **Baseline PaCO2 is 45, not 40.** Ventilation was deliberately slowed before
   the test to raise it. The excursion is 33 mmHg, not 38.
2. **Every patient was on dopamine** at 5-30 ug/kg/min, two also on dobutamine,
   held constant. A heart already beta-stimulated has less reserve.
3. **Body temperature 34.0-37.4 C** (mean 35.8), which lowers CO2 production.
4. **The paper's entire point is that the response IS depressed** in brain
   death. It says so: "the circulatory stimulating response was markedly
   depressed compared with those in volunteers and patients under general
   anaesthesia". Treating it as a like-for-like comparator for an anaesthetised
   patient inverts its argument.

The paper hands us the ladder to place ourselves on. Citing **Cullen and Eger**
for awake subjects, it gives **0.17 L/min of cardiac output per mmHg PaCO2**,
against **0.05 L/min per mmHg** in its own brain-dead patients. (Their 0.05 does
not reconcile with their own table -- 0.9 L/min over 33 mmHg is 0.027 -- so
either they used individual slopes or it is a slip. Use the table.)

    awake (Cullen & Eger)          0.17  L/min/mmHg
    our model, anaesthetised       0.034 L/min/mmHg   (0.9% of baseline 3.75)
    brain-dead on dopamine, 35.8 C 0.027 L/min/mmHg   (from Ebata's table)

**Our value sits between awake and brain-dead, which is where an anaesthetised
patient belongs**, and it agrees with the benchmark we already hold (Sci Rep
n=91, +30% reported, we give +35.8%). If anything it is on the low side: Price
et al., quoted by Ebata, found anaesthesia reduces the haemodynamic response to
CO2 by a half (cyclopropane) to two-thirds (halothane), which would put an
anaesthetised patient at 0.057-0.085 L/min/mmHg, above ours. **Nothing should be
changed on the strength of this paper**, and the direction of any future change
is more likely up than down.

Ebata's regression lines, worth having (x = change in PaCO2, torr):

    awake         dHR = 0.97x + 3.1      dMAP = 0.59x + 0.1
    cyclopropane  dHR = 0.50x + 0.5      dMAP = 0.20x + 0.7
    halothane     dHR = 0.19x + 2.0      dMAP = 0.09x + 0.9
    brain death   dHR = -0.02x + 0.5     dMAP = -0.02x + 0.9

**Two candidate benchmarks that ARE clean**, because they do not depend on
sympathetic integrity: mean PAP 11 -> 17 mmHg and PVR 112 -> 183 (+63%) at
PaCO2 78 / pH 7.17, with the rise in PAP correlating with the rise in PVR
(r=0.72, P<0.05) -- i.e. hypercapnic pulmonary vasoconstriction, which is a
direct effect. Our pulmonary limb has almost nothing testing it. This is worth
adding.

## C alone — the rate of rise, and how much data exists

- **Stock MC, Schisler JQ, McSweeney TD. The PaCO2 rate of rise in
  anesthetized patients with airway obstruction. J Clin Anesth 1989;1(5):328-32**
  (PMID 2516732, doi 10.1016/0952-8180(89)90070-6). Piecewise linear: 12 mmHg
  in the first minute, 3.4 mmHg/min thereafter; a logarithmic function fitted
  best. **Whether airway pressure was also recorded is still unknown** — the
  abstract does not say and the full text was not reachable. This is the single
  most valuable thing left to check, because if those patients had a pressure
  trace the P+C gap may already be closed.
- **Schafer & Caronna. Duration of apnea needed to confirm brain death.
  Neurology 1978;28:661.** Mean rate of rise **3.2 mmHg/min** over ten minutes.
  Patent airway.
- **Apnoea testing to confirm brain death in clinical practice** (PMID 3093640)
  explicitly could not confirm the assumed 2.5 mmHg/min and found the rate
  non-uniform.
- **The carbon dioxide rate of rise in awake apneic humans** (PMID 3152423).
- **Solsona et al. PaCO2 becomes greater than PvCO2 during apnoea testing for
  brain death. Anaesthesia 2010** (doi 10.1111/j.1365-2044.2010.06261.x). This
  is the same gradient reversal that `test_validation.py` already tests from
  O'Loughlin. A second, independent observation of it.

All of the brain-death data is **patent-airway** apnoea. None of it constrains
the obstructed case, which is Stock's alone.

---

## P alone — and why the one-lung literature is the place to look

- **Moreault 2021** (Can J Anesth, doi 10.1007/s12630-021-01938-y) remains the
  only human measurement we have of pressure developing inside a lung from gas
  absorption. Method: catheter from the non-ventilated bronchus to a
  differential pressure transducer.
- **The OLV narrative review (J Clin Med 2026;15:5078, doi 10.3390/jcm15135078)
  has now been READ. It contains no second pressure dataset** -- it is a
  strategy review, and Moreault is the only pressure measurement it cites. So
  that lead is weaker than it looked.
  Its real value is elsewhere: it is an entire clinical literature built on
  **our model's nitrogen limb**, independently. It frames lung collapse as
  phase I (elastic recoil, passive venting) then phase II (residual gas
  absorption), and its central practical claim is that letting ambient air into
  the non-ventilated lumen lets **nitrogen re-enter and delays absorption
  collapse** -- which is exactly the nitrogen splinting our model uses to set
  the lung-volume floor, arrived at from the operating theatre rather than from
  a simulation. It also notes that hypoxic pulmonary vasoconstriction reduces
  perfusion to the non-ventilated lung and so further slows absorption, another
  coupling we model. Worth citing in the paper as external corroboration.
  Candidate primary sources it names, none yet read: Pfitzner et al. 2001,
  Ko et al. 2009, Yoshimura et al. 2014, Somma et al. 2021, Huang et al. 2024
  (OCAT: median time to complete collapse 10 min vs 25 min), and Quan et al.
  (80 patients, 1 min of -30 cmH2O bronchial suction).
- **Dale WA, Rahn H. Rate of gas absorption during atelectasis. Am J Physiol
  1952;170:606-13.** Held here. The classical source.
- **Alveolar gas exchanges and atelectasis: the mechanism of gas absorption in
  bronchial obstruction** (Arch Surg / JAMA Surgery). Not yet read.

### What does NOT count, and why

Recorded so the same false leads are not followed again.

- **Negative-pressure pulmonary oedema** case literature quotes intrathoracic
  pressures beyond -100 cmH2O. Those come from forced inspiration against a
  closed glottis. Active effort, not absorption — the same category error as
  reading the Chen & Scharf room-air arm as mechanical.
- **Animal obstructive-apnoea models** clamp a tracheal cannula or apply a set
  negative pressure (-50 to -150 mbar in rat upper-airway work). They report
  pressure APPLIED, not pressure DEVELOPED.
- **Obstructive sleep apnoea** oesophageal pressure swings: effort-driven again.
- **Continuous negative extrathoracic pressure** (cuirass, iron lung) does pair
  a known negative pressure with measured cardiac output, and finds cardiac
  index UP 14-24%. But it lowers pressure around the whole thorax including the
  great veins, which augments venous return — the opposite sign of the Muller
  case, where the vacuum is inside the lung and the veins entering the chest are
  at atmospheric pressure. Do not read it as evidence about `sv_itp_gain`.

---

## What to do next, in order

Items 2 and 4 of the previous list are DONE and both reversed their provisional
conclusions. What remains:

1. **Get Stock 1989 full text** and find out whether airway pressure was
   recorded. Still the highest value of anything here, and now the only
   remaining route to a P+C pairing that does not require running the study.
2. **Decide whether to add Ebata's pulmonary benchmarks**: mean PAP 11 -> 17
   and PVR +63% at PaCO2 78. These do not depend on sympathetic integrity, and
   our pulmonary limb is almost untested.
3. ~~Establish what actually couples `stiff_below_rv` to the Stock slope.~~
   **DONE. It is V/Q heterogeneity.** Cardiac output carries about 28% of it;
   shunt, the p_collapse floor and the alveolar CO2 store are all excluded;
   and shrinking `vq_log_sd` from 0.70 to 0.20 takes the coupling to exactly
   zero while the arterial-to-alveolar CO2 gap collapses from +6.7 to -0.8.
   The consequence is larger than the question: `vq_log_sd` controls the Stock
   slope almost entirely, and Stock's measured 3.4 sits at about 0.55 with the
   first-minute rise unchanged at 12.2 against a measured 12. See the "Known
   disagreement" section of HANDOVER.md before acting on that -- it would
   convert Toner and Heard from validation into fit.
4. Consider raising `sv_itp_gain` from 0.0025 toward the human 0.0033-0.00476.
   It changes the Stock slope by about 0.1 and nothing else that is
   benchmarked, so this is a truth-in-labelling change rather than a fit
   improvement -- and it should not be made without deciding the 15 s versus
   3 min question, since a 15 s manoeuvre may not transfer.
5. Douglas 1988 full text, for the red-cell CO2 correction. Unchanged.
6. Pfitzner 2001 and Ko 2009 from the OLV review, for the nitrogen limb.

## Access status

| Paper | Status |
|---|---|
| OLV review, doi 10.3390/jcm15135078 | **Obtained and read** |
| Wright, AJP-Heart 2023;325:H1235 | **Obtained and read** |
| Condos, Circulation 1987;76:1020 | **Obtained and read** |
| Ebata, Can J Anaesth 1991;38:436 | **Obtained and read** |
| Koshino, Circ Cardiovasc Imaging 2010;3:282 | Not obtained. Reports strain, not stroke volume, so low priority |
| Douglas, J Appl Physiol 1988;65:473 | Not obtained |
| Tokics, J Appl Physiol 1996;81:1822 | **Obtained and read.** Settles the V/Q spread: log QSD 0.65 awake, 1.18 anaesthetised by MIGET, 0.80 by isotope, n=10 paralysed supine |
| Stock, J Clin Anesth 1989;1:328 | Not obtained. **The one that matters** |
