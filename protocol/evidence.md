# Evidence map for the three linked variables

Searched September 2026. **Read the caveat first:** this environment's network
policy allows web *search* but blocks the publisher domains, so everything
below comes from abstracts and search summaries, not from full texts. Nothing
here should be entered as a benchmark until the paper has been read. The
mistake this file is designed not to repeat is the ICSM one, where a
conclusion was drawn from what a short document did not say.

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
| **P + H** | **yes** | human Mueller-manoeuvre studies |
| **C + H** | **yes** | Can J Anaesth apnoea-test study, n=9 |
| **P + C** | **NOT FOUND** | — |
| P + C + H | **NOT FOUND** | — |

So the protocol's premise survives, but its statement of the gap must change.
The gap is not that nobody has paired anything. It is that **nobody has paired
pressure with CO2**, which is precisely the pairing that identifies which limb
of the model is wrong, because those two are what the Muller effect couples.

---

## P + H — human Mueller manoeuvre. This bears on `sv_itp_gain`.

These measure intrathoracic pressure and stroke volume simultaneously, in
normoxic humans, and they do show an effect.

- **Healthy adults, n=17 (10M/7F, 24+-4 y), ITP -30 cmH2O held 15 s**,
  echocardiography with speckle tracking: LV stroke volume **-10+-4 mL**,
  LVEDV -11+-9 mL, returning to baseline on release. On a young-adult baseline
  SV near 75 mL that is about **-13%**, i.e. a gain near **0.0044 per cmH2O**.
  (Circ Cardiovasc Imaging 10.1161/CIRCIMAGING.109.901561, and the AJP-Heart
  2023 companion.)
- **Buda / Scharf, Circulation 1987;76:1020**, right and left heart
  micromanometry with Doppler: mitral and aortic flow fell **12.2+-7.2%** and
  **10.1+-6.6%** by the fifth beat. Pressure not confirmed from the abstract.
- **CHF patients at -40 cmH2O**: stroke volume index **-33%** (J Appl Physiol
  1998;85:1476). A failing ventricle is far more preload-dependent, so this is
  not our patient.

**Our `sv_itp_gain` is 0.0025 per cmH2O.** At ITP -30 it predicts -7.5% where
these measure -13%. So the parameter sits INSIDE the range human normoxic data
supports, at the conservative end — it is not, as an earlier note in HANDOVER
said, unevidenced. What is unevidenced is its CITATION: Chen & Scharf's oxygen
arm shows no effect at -42 cmH2O, and that remains true.

**The two literatures disagree, and the likely discriminator is duration.** A
Mueller manoeuvre is 5-15 s, over which venous return has no time to
re-equilibrate. Our patient reaches -15 cmH2O over three minutes, which is the
sustained condition, and the sustained-and-oxygenated evidence is the arm
showing about zero. So the acute human data is best read as an **upper bound**
on a transient, not as a calibration for our case. Which of the two applies at
three minutes is not answerable from any of these papers, and is exactly what
the protocol's haemodynamic channel measures.

---

## C + H — the brain-death apnoea test. A candidate second benchmark.

**Haemodynamic changes during the apnoea test for diagnosis of brain death**,
Can J Anaesth (doi 10.1007/BF03007579), n=9, severe head injury or CVA.
Ventilator disconnected ten minutes with oxygen insufflation, so the airway is
PATENT and intrathoracic pressure stays near zero. That is what makes it
useful: it isolates the CO2 effect from the Muller effect.

    PaCO2 at 10 min      78 +- 3 mmHg        pH 7.17 +- 0.02
    cardiac output       4.8 +- 0.7  ->  5.7 +- 0.8 L/min   (+18.8%)
    mean PAP             11 +- 1     ->  17 +- 2 mmHg
    MAP, HR, PAWP, RAP   unchanged
    plasma noradrenaline rose in all three patients measured

Against our model, run patent with FgO2 1.0:

    PaCO2 60   CO +18.8%    PAP 18.1
    PaCO2 70   CO +28.8%    PAP 19.5
    PaCO2 77   CO ~ +33%    (measured: +18.8% at 78)

So our CO2-to-cardiac-output gain looks roughly **1.8x too strong** on this
dataset. It is not a refutation, for three reasons that must be weighed before
anything is changed:

1. These patients are brain-dead. Central sympathetic outflow is gone and only
   a spinal sympathoadrenal response remains — the authors say so, and offer it
   as the reason the direct depressant effect of hypercapnia did not show. A
   blunted response is expected.
2. Baseline PaCO2 is not given as 40. Apnoea tests are usually begun from a
   preconditioned 40-45, which shrinks the CO2 excursion and the predicted rise.
3. Baseline CO 4.8 against our anaesthetised 3.75 — different populations.

Set against `test_validation.py`'s existing benchmark, which takes +30% from a
Sci Rep n=91 measurement in apnoeic oxygenation and which we meet at +35.8%,
we now have one source at +30% and one at +18.8%, with our model at or above
the top of both. **Read the paper before acting.** If it holds, `co_co2_gain`
and `sv_co2_gain` are too large, and note the direction: reducing them SLOWS
CO2 delivery to the lung and would move the Stock slope from 4.3 toward 3.4.
That is the first correction found so far that pushes Stock the right way.

---

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
- The wider one-lung-ventilation literature uses the same method and reports
  the same phenomenon — airway pressure in the non-ventilated lung becoming
  progressively negative, with entrainment toward it when it is open to
  atmosphere. A 2025 narrative review (doi 10.3390/jcm15135078) is the entry
  point. **This is the most promising place to find a second P dataset**, and
  possibly a P+C one, since OLV studies routinely sample arterial gases.
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

1. **Get Stock 1989 full text** and find out whether airway pressure was
   recorded. Highest value of anything on this list.
2. **Get the Can J Anaesth apnoea-test paper** and check baseline PaCO2 and
   whether the brain-death caveat is disqualifying. If not, it becomes a second
   haemodynamic benchmark and probably shrinks `co_co2_gain`.
3. **Search the one-lung-ventilation literature properly** for bronchial
   pressure paired with arterial gases. This is where a P+C dataset would be,
   if one exists anywhere.
4. Get the Mueller papers to confirm the pressures and baseline stroke volumes,
   so the acute upper bound on `sv_itp_gain` can be stated numerically rather
   than estimated from a percentage.
5. Douglas 1988 full text, for the red-cell CO2 correction. Unchanged from
   before.
