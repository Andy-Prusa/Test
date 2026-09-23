# Sources — what the model rests on, and which of it has been read

Created 2026-09-21 by a pre-release audit of every citation in the repository:
**235 citations, 109 distinct sources**. This file is the single place reading
status is recorded. It exists because the status was previously scattered across
`README.md`, `HANDOVER.md`, `bloodgas.py` and `protocol/evidence.md`, and those
four disagreed with each other — `README.md` was still telling readers a curve
was "written from memory" a week after the paper had been obtained and the
curve verified.

**The rule this file enforces is CLAUDE.md's:** if a paper is not held, the
numbers taken from it are UNVERIFIED, and saying so is not optional.

Three things to understand before using it:

1. **Nothing in the repository is a paper.** `git ls-files` tracks no PDFs, and
   `make_package.sh` builds from `git archive HEAD`, so a recipient gets none of
   the sources below. "Held" throughout means held by the project, not shipped.
2. **"Read from the page" means someone opened the document and read the
   relevant table or equation.** It does not mean the citation was recognised,
   and it does not mean an abstract was read. Those are different things and
   this project has confused them before.
3. **A source being unread does not make its number wrong.** It makes the number
   a claim about the literature that nobody here has checked.

---

## 1. Held and read from the page

Seventeen PDFs are held in the working session. All seventeen were identified on
2026-09-21 by opening them and reading the title page, because several filenames
are opaque and identifying a paper from its filename is exactly the kind of
shortcut this project has been burned by.

| source | what it pins | verified against |
|---|---|---|
| **Stock MC, Schisler JQ, McSweeney TD.** The PaCO2 rate of rise in anesthetized patients with airway obstruction. *J Clin Anesth* 1989;1(5):328-32. PMID 2516732, doi 10.1016/0952-8180(89)90070-6 | the obstructed CO2 benchmark, and the titration line | Abstract, Table 2, Discussion, read 2026-09-14 |
| **Kelman GR.** Digital computer procedure for the conversion of PCO2 into blood CO2 content. *Respir Physiol* 1967;3:111-115 | CO2 solubility and pK′ in `bloodgas.py` | verified word for word, prose against the FORTRAN listing |
| **Kelman GR.** Computer program for the production of O2-CO2 diagrams. *Respir Physiol* 1968;4:260-269 | the Haldane/buffer shift | p.264 read |
| **Douglas AR, Jones NL, Reed JW.** Calculation of whole blood CO2 content. *J Appl Physiol* 1988;65(1):473-477 | whole-blood CO2 content | Eq 6 verified 2026-09-14. **Caught a real defect:** `[Hb]` is g/100 mL and was being passed as mmol/L. Arterial content 51.65 → 47.50 mL/dL |
| **Tokics L, et al.** V̇/Q̇ distribution and correlation to atelectasis in anesthetized paralyzed humans. *J Appl Physiol* 1996;81(4):1822-1833 | the V/Q spread the model is judged against | Table 3 read |
| **Rothen HU, et al.** Re-expansion of atelectasis during general anaesthesia. *Br J Anaesth* 1993;71:788-795 | respiratory compliance range | Summary read |
| **Moreault O, et al.** Double-lumen endotracheal tubes and bronchial blockers exhibit similar lung collapse physiology. *Can J Anesth* 2021;68:791-800, doi 10.1007/s12630-021-01938-y | the pressure limb | Abstract and Statistical analysis read. **Its spread is SEM, not SD** — see §5 |
| **Ebata T, Watanabe Y, Amaha K, Hosaka Y, Takagi S.** Haemodynamic changes during the apnoea test for diagnosis of brain death. *Can J Anaesth* 1991;38(4):436-440 | nothing — see §4 | Table II read |
| **Condos WR, et al.** Hemodynamics of the Mueller maneuver in man. *Circulation* 1987;76:1020 | `sv_itp_gain` | read |
| **Wright SP, et al.** Mueller maneuver attenuates left atrial phasic volumes and myocardial strain. *Am J Physiol Heart Circ Physiol* 2023;325:H1235-H1241, doi 10.1152/ajpheart.00505.2023 | `sv_itp_gain` | read |
| **Chen L, Scharf SM.** Systemic and myocardial hemodynamics during periodic obstructive apneas in sedated pigs. *J Appl Physiol* 1998;84(4):1289-1298 | context only; excluded as a benchmark | read |
| **Hardman JG, Wills JS.** The development of hypoxaemia during apnoea in children. *Br J Anaesth* 2006;97(4):564-570, doi 10.1093/bja/ael178 | MODEL comparator | Table 1 read. **Its online Appendix 1 is not held**, and that appendix is the paper's own validation |
| **Venegas JG, Harris RS, Simon BA.** A comprehensive equation for the pulmonary pressure-volume curve. *J Appl Physiol* 1998;84(1):389-395 | nothing — see §4 | held |
| **Wei J, Gao L, Sun F, Zhang M, Gu W.** Volume of tidal gas movement in the nonventilated lung during one-lung ventilation. *BMC Anesthesiology* 2020;20:20 | nothing — see §4 | held |
| **Ellis R, et al.** Comparison of apnoeic oxygen techniques in term pregnant subjects: response. *Br J Anaesth* 2023;130:e429-e430 (correspondence) | context | read. Holding the correspondence does **not** verify the 2022 paper's numbers |
| **Laviola M, Dinsmore J, Lacquiere D, Niklas C, Heard A, Hardman JG.** Jet oxygenation via a narrow-bore cannula in the CICO scenario — **Supplementary Digital Content only** | MODEL comparator state at SaO2 40% | Table S5 read. **The main text is not held** — see §3 |
| **O'Loughlin CJ, Phyland DJ, Vallance NA, Giddings C, Malkoutzis E, Gunasekera E, Webb A, Barnes R.** Low-flow apnoeic oxygenation for laryngeal surgery: a prospective observational study. *Anaesthesia* 2020;75:1070-1075, doi 10.1111/anae.14959 | four bands in `test_validation.py`, and five claims in `editorial.md` | **Read in full 2026-09-21.** n=64, age 47 (16), BMI 25 (4) — our test configuration is exact. Caught one error: see §5 |
| **Toner AJ, Douglas SG, Bailey MA, et al.** Effect of apneic oxygenation on tracheal oxygen levels, tracheal pressure, and carbon dioxide accumulation. *Anesth Analg* 2019;128:1154-1159, PMID 31094782, doi 10.1213/ANE.0000000000003810 | two bands, the lean config, one CO2-store anchor | **READ IN FULL 2026-09-22.** n=20, patent airway. Sham median 447 s, **IQR 405-525, stated as "median (interquartile range)"**. Early CO2 LINEAR at 3.16 buccal / 2.82 sham mmHg/min; prolonged buccal nonlinear, declining, averaging 2.22. Mean tracheal pressure 0.21 (SD 0.39) buccal, 0.56 (SD 1.25) sham cmH2O. **Located the patent-airway defect** |
| **Kaiser HA, Bauer T, Riva T, et al.** Carbon dioxide and cardiac output as major contributors to cerebral oxygenation during apnoeic oxygenation. *Sci Rep* **2024**;14:3617, PMC10864331, doi 10.1038/s41598-023-49238-3 | `co_co2_gain`, `sv_co2_gain`, three bands | **READ IN FULL 2026-09-22. Our n=91 was RIGHT; the YEAR was wrong, 2024 not 2023.** PaCO2 43 (IQR 10) to 73 (IQR 14) over 15 min, mean change 2.1 mmHg/min; cardiac output 5.0 to 6.5 L/min, **+30% confirmed**. The circularity stands: we fit to that +30% then grade against it |
| **Farmery AD, Roe PG.** A model to describe the rate of oxyhaemoglobin desaturation during apnoea. *Br J Anaesth* 1996;76:284-291 | nothing yet — see §4 | read in full 2026-09-20 |

---

## 2. Not held, and something rests on it

Ordered by what breaks. Every identifier below is one the repository already
records; **where none is recorded the entry says so rather than guessing one**,
because a search tool once confabulated an attribution for this project and that
is recorded in `HANDOVER.md` as the oldest failure mode here.

| source | what rests on it | why it matters |
|---|---|---|
| ~~**Heard A, et al.** *Anesth Analg* 2017;124:1162-7~~ **OBTAINED AND READ 2026-09-22** | — | **CLOSED.** Moved to §1b. The band is confirmed as an IQR and was right; the configuration was wrong in four ways and is corrected |
| **The four positioning trials: Lane 2005, Ramkumar 2011, Altermatt 2005, Dixon 2005.** Surnames and years only | `tilt_gain_lean` and `tilt_gain_bmi`, stated in `apnoea_core.py` as "calibrated against four randomised trials", then graded by three bands set from those same four | **Not retrievable as cited, by anyone, including us.** Also a fit graded by its own calibration target (§6). The limb is not confined to the positioning test: the obese buccal configuration runs `tilt_deg=25` |
| **The one-lung-ventilation narrative review**, doi 10.3390/jcm15135078. No author or title recorded | `protocol/evidence.md` calls it "obtained and read" and draws an **absence** claim from it | Reasoning from what a document does not contain is the move CLAUDE.md forbids outright. Open access |
| ***Circulation* 1963;28:346**, "Hemodynamic Effects of Chronic Severe Anemia". **No author recorded** | `hb_co_exp` = 1.535, derived from it; a band in `test_validation.py` | The band grades the fit against the number the fit was made from. Whether it is a paper or a meeting abstract is **unknown**, and that changes whether the "CLINICAL" label is honest |
| **Varat MA, Adolph RJ, Fowler NO.** *Am Heart J* 1972;83:415-26 | `hb_co_threshold` = 7.0 | A **verbatim quotation in quotation marks** ships in three files from a paper nobody here has read |
| **Laviola 2026, main text** (SDC held) | ~~a band sourced "~510 s"~~ **STRUCK 2026-09-22**, plus the scorecard row and the claim that "two independently built models agree" | **The 510 s is in no document held.** The band that rested on it has been removed from `test_validation.py` by ruling; see §1b. The SDC gives the state at SaO2 40%, explicitly not the time to it, and names no journal, volume or DOI — the citation in `test_validation.py` is the repository speaking, not the document |
| **Siggaard-Andersen O.** The van Slyke equation. *Scand J Clin Lab Invest Suppl* 1977;146:15-20, doi 10.3109/00365517709098927 | the non-bicarbonate buffer term `(9.5 + 1.63·cHb)` in `bloodgas.py` — the pH at which every CO2 content and every PaCO2 slope is computed | `bloodgas.py` defends its unit convention with an **unsourced assertion**, which is the exact pattern of the Douglas `[Hb]` bug this same file shipped once. The DOI above was read off the held Laviola SDC's reference list, so it is sound |
| **"Chest"** — a journal name and nothing else | the only check of the stroke-volume limb of the CO2 response | It can be neither confirmed nor refuted, and it is counted toward the benchmark total quoted to a sponsor. **Fixable without a library:** complete the citation or strike the band |
| **Flin R, Fioratou E, Frerk C, Trotter C, Cook TM.** *Anaesthesia* 2013;68:817-25 | two precise second-hand figures in `editorial.md`, regenerated by no script | No sensitivity bounds this one. It is simply right or wrong |
| **Hardman JG, Wills JS, Aitkenhead AR.** Investigating hypoxaemia during apnoea: validation of a set of physiological models. *Anesth Analg* 2000;90(3):614-8 | could falsify a sentence in `test_validation.py`'s shipped docstring | Sought 2026-09-19, not obtained. The narrow refs-34-37 claim is verified against the held SDC and stands; the broader sentence "their simulator is extrapolating into complete obstruction exactly as ours is" is not self-limiting |

### The ICSM validation chain

`test_validation.py` and `HANDOVER.md` argue that every MODEL comparator row
carries almost no evidential weight, because the comparator simulator's apnoea
modules were validated against **Fraioli 1973, Berthoud 1991, Baraka 2007 and
Gustafsson 2017**, three of which require a patent airway by construction.

**None of those four is held.** `HANDOVER.md` says so plainly and hedges
Berthoud explicitly: *"we have not read [it] and its apnoea airway state is not
determinable from the citation… Only the citations were read, not the papers."*
`test_validation.py`'s docstring **drops both hedges** and reads "Checked
2026-09-19", which a reader will take as verification of papers nobody opened.
The argument is probably right. It is currently made from citations, not papers.

---

## 1b. Obtained 2026-09-21, and what they changed

**Laviola M, Dinsmore J, Lacquiere D, Niklas C, Heard AH, Hardman JG.
Emergency Jet Oxygenation Via a Narrow-Bore Cannula: A Computational Modelling
Investigation.** *Anesthesia & Analgesia*, Research Letter, 4 pp.
**doi 10.1213/ANE.0000000000008194** — the DOI `test_validation.py` asserted is
CORRECT, now confirmed against the paper.

**THE "~510 s" IN OUR ARBITER DOES NOT EXIST IN EITHER DOCUMENT.** We now hold
the main text AND the Supplementary Digital Content. `test_validation.py` bands
time-to-SaO2-40% at 400-620 s and sources it "MODEL comparator; ~510 s
(8.5 min)". Searched exhaustively: the string "510" appears **zero** times in
the main text, and every duration in the paper is 3 min (preoxygenation), 30 s
(insufflation interval), 10 min (protocol length), 60 s and 86 s (peak
saturation times) and 39 s (time to restore SaO2 >90%). The SDC gives the
*state* at SaO2 40%, explicitly not the *time* to it. **That band's stated
source is not in the source.** It must be struck or re-sourced; it cannot stand
as written.

**STRUCK 2026-09-22 BY RULING.** The band is gone from `test_validation.py`.
It is not passed, not re-banded and not re-sourced — it is removed, and the
comment left in its place says what it was and why, so the removal cannot be
mistaken for a fix. The suite is one check shorter and one unsourced claim
lighter. The re-sourcing candidate below (PaCO2 38.2 (8.2) mmHg over 10 min)
is a **different quantity** and was not substituted in; if anyone wants it as
a benchmark it has to be argued for on its own.

**What the main text does give us, verified:**

- **PaCO2 rose by a mean of 38.2 (8.2) mmHg over 10 minutes.** This is a real,
  citable comparator and a far better one than the figure it replaces.
- Protocol: 3 min preoxygenation, then apnoea with **complete upper airway
  obstruction**; cricothyroidotomy completed at SaO2 40% with a 14-gauge cannula
  and a RapidO2 device at 15 L/min (250 mL/s); insufflations every 30 s if SaO2
  <70%; continued 10 min.
- SaO2 restored above 90% within **39 s** in all subjects.

**WHAT THEY DO NOT GIVE, and it is the thing most often wanted: any arterial
oxygen tension at a FIXED TIME.** The SDC reports the state at SaO2 40% — an
endpoint defined by saturation, not a moment on a clock — and the main text
reports no oxygen time course. So the question "does ICSM agree with Stock
under obstruction?" **can be answered for CO2 and cannot be answered for
oxygen**, and a docstring in `test_validation.py` asserted an answer anyway
until 2026-09-22 (struck; see that file and `handover_numbers.py`). On CO2 at
10 minutes the answer is that **Stock's own fit, carried forward, sits inside
Laviola's 1 SD band, and OURS is the outlier 28% below both** — the reverse of
what was claimed. Any ICSM publication carrying a PaO2 or SaO2 time course
under complete obstruction would close this.
- Peak end-inspiratory pressure limited to **10.5 cmH2O**.

---

**Shamohammadi H, Weaver L, Saffaran S, Tonelli R, Laviola M, Laffey JG,
Camporota L, Scott TE, Hardman JG, Clini E, Bates DG.** Airway pressures
generated by high flow nasal cannula in patients with acute hypoxemic
respiratory failure: a computational study. *Respiratory Research*
2025;26:9, doi 10.1186/s12931-025-03096-x. Open access.

**This is the Nottingham simulator for the seventh time.** Laviola, Hardman,
Bates and Saffaran are all on it, and Saffaran is the author of the paediatric
ARDS paper already in the ICSM validation chain. It is a MODEL, not a
measurement — "a high-fidelity mechanistic computational model of the
cardiopulmonary system". It reinforces rather than relieves `HANDOVER.md`'s
"THESE ARE NOT SIX INDEPENDENT COMPARATORS. THEY ARE ONE SIMULATOR". Nothing in
our model does high-flow nasal oxygen, so it sets no parameter here; its value
is as another window on how that simulator is built.

---

**Brown CA III. Buccal Oxygenation During Prolonged Laryngoscopy Prevents
Desaturation in Obese Patients.** NEJM Journal Watch, 19 October 2016. One
page. **This is a commentary ON Heard, not the paper** — but it turned out to
be worth more than that, and my first assessment of it as unable to verify a
band was wrong.

It quotes Heard's headline result verbatim: **"750 seconds [range, 389-750]
versus 296 seconds [range, 244-314]"**, n=40, BMI 30-40, single-centre
Australian, randomised to usual care or buccal oxygen via a modified 3.5 mm
RAE tube on the left cheek, doi 10.1213/ANE.0000000000001564. **Both our Heard
bands are therefore verified secondhand and both are right**, and our patient
configuration (BMI 34.9) sits mid-range.

**Three things it exposes that only the paper can settle:**

1. It calls those spreads **"range"**; we call them **"IQR"**. Different
   claims. If 244-314 is the full observed min-max rather than the middle
   50%, our model landing at 289 s inside it is a considerably weaker result
   than we have been reporting.
2. Heard preoxygenated to **end-tidal O2 >= 80%**; our test starts from an
   alveolar fraction of 0.87. A floor and a starting fraction are not the same
   quantity.
3. Heard created **"a deliberate grade III view to mimic partial airway
   obstruction"** and held it. We model that as the most patent setting the
   model has. For the control arm probably harmless; for the buccal arm less
   obviously so, since the question at issue is whether oxygen reaches the
   trachea past the blade.

**Heard 2017 itself is still not held**, and the file supplied under that name
— three times now — is this commentary.

**`Douglas_AR.docx`** is a reference list, not a source — a page of citations
including Hardman 1998 BJA 81:327-32, Dale & Rahn 1952 and Crotti 2001. Useful
for ordering; it verifies nothing.

**Also obtained 2026-09-21, not yet mined:**

- **Hardman JG, Bedforth NM, Ahmed AB, Mahajan RP, Aitkenhead AR.** A physiology
  simulator: validation of its respiratory components and its ability to predict
  the patient's response to changes in mechanical ventilation. *Br J Anaesth*
  1998;81:327-332. **READ IN FULL 2026-09-22**, including Appendix 1 and 2.
  The foundational validation of the Nottingham simulator. **Its lung is ONE
  well-mixed alveolar compartment with blood flow split two ways, shunted and
  non-shunted — it has no V/Q distribution at all**, where we run 80 parallel
  compartments. "apnoea", "apnea", "V/Q" and "ventilation-perfusion" appear
  zero times in the paper; it was validated on 31 stable ICU patients against
  changes in minute volume or FiO2. See HANDOVER, *Hardman 1998 and Laviola
  2020 read*, for why this voids any use of an ICSM number to argue about V/Q.
- **Laviola M, Niklas C, Das A, Bates DG, Hardman JG.** Effect of oxygen
  fraction on airway rescue: a computational modelling study. *Br J Anaesth*
  2020. **READ IN FULL 2026-09-22.** 100 virtual subjects, 3 min of 100%
  oxygen, obstructed apnoea, relief at SaO2 20/40/60%; post-rescue PaO2
  **42.3 (4.4) kPa** at SaO2 60%. **Our `test_validation.py` configuration
  matches the published protocol exactly and gives 43.92 kPa, inside one SD**,
  and stays inside 1 SD across every plausible preoxygenation. The
  "NOT REPRODUCIBLE" entry against it in `handover_numbers.py` was stale and
  is struck.
- **Mohanty R, George LR, George SP, Babu M.** Apnoeic oxygenation during
  simulated difficult intubation in obese patients: buccal RAE versus nasal
  cannula. *Anesth Essays Res* 2021;15(4):408-412, doi 10.4103/aer.aer_114_21.
  **Read.** n=50, ASA I-II, BMI >= 30. Buccal RAE mean apnoea **375.3 (116.6) s**
  against nasal cannula 316.1 (94.1), P = 0.054. This **verifies exactly** what
  `HANDOVER.md` records secondhand, and it is the head-to-head that contests
  Heard's buccal figure.

**Duplicates, no new information:** the second `Rothen_HU.pdf` and the second
`venegas-et-al-1998` are byte-identical (same MD5) to the copies already held.

---

## Authorised unpublished data — the Toner transcutaneous trace

**`Glottic01_analysed.xlsx`** (supplied twice, byte-identical) is a **TCM4/40
transcutaneous monitor export for one identified patient**, ID "glottic01",
7 March 2017, 2931 rows of second-by-second O2, CO2, SpO2 and pulse over about
49 minutes, with session and arterialization event marks.

**AUTHORISED 2026-09-21 by A. Heard, who owns the data** ("yes we can use
glottic spreadsheet from toner"). This is the single exception to CLAUDE.md's
published-data-only rule and it is recorded here so it stays an exception.

**The file itself does not go into the repository** and is not tracked, because
`make_package.sh` builds from `git archive HEAD` and would ship it to every
recipient. What is authorised is USING it.

**Terms, so this does not become the thing the rule was written to prevent:**

1. A finding that rests on this trace is **reported as resting on it, by
   name** — "the Toner transcutaneous trace, one patient, 7 March 2017" — and
   never as an unattributed number.
2. It does not become **the value of a parameter** and it does not become a
   **band in `test_validation.py`**. It is one patient. It can corroborate,
   contradict, or suggest; it cannot calibrate.
3. Anything derived from it that reaches a **publication** needs the study's
   own authorship and consent position settled first, which is not a modelling
   question.

**Why it is worth having.** A second-by-second transcutaneous CO2 trace through
an apnoea is close to what this project has been asking the Toner group for
since 2026-09-16. Our single most-failing benchmark is the obstructed CO2 rate
of rise, and the entire case for the three-way study is that no published
source records pressure and CO2 together. This trace does not record pressure —
but it is a real CO2 time course in a real patient, which is more than the CO2
limb has ever been tested against outside Stock's eight sampled points.

---

### Gander 2005 — the morbidly obese benchmark, and it says the shunt is ABSENT

**Gander S, Frascarolo P, Suter M, Spahn DR, Magnusson L.** Positive
end-expiratory pressure during induction of general anesthesia increases
duration of nonhypoxic apnea in morbidly obese patients. *Anesth Analg*
2005;100(2):580-4. Held and read 2026-09-23.

**This is the dataset this file has called "the single most valuable missing
dataset" since before 2026-09-22.** n=30 morbidly obese, control arm n=15
(11 with blood gases), **BMI 47 (6)**, age 38 (12), 13/15 female. Five minutes
of 100% O2 with NO CPAP, induction, mechanical ventilation without PEEP, then
apnoea to SpO2 90%.

| | control | PEEP group |
|---|---|---|
| apnoea to SpO2 90% | **127 (43) s** | 188 (46) s |
| PaO2 before apnoea | **243 (136) mmHg** | 376 (145) |
| PaCO2 before apnoea | 46 (6) | 47 (11) |
| PaO2 at SpO2 92% | **68 (10)** | 64 (11) |
| PaCO2 at SpO2 92% | **53 (4)** | — |

BMI against apnoea duration: **R2 0.51, P 0.003 in the control arm**, and
R2 0.14 (NS) in the PEEP arm — the BMI effect is abolished by preventing
atelectasis, which is the mechanism demonstrated by its own removal.

**OUR MODEL AT BMI 47.** Recomputed 2026-09-23 after residual volume was
made BMI-dependent (see Reinius 2009 below). The configuration is now written
down and scripted in `handover_numbers.py`, so it cannot go the way of the
Ellis rows: height 1.70 m, weight 47 x 1.70^2 = 135.8 kg, age 38, Hb 14,
end-tidal oxygen at the start 0.90, starting PaCO2 46, patent airway on room
air. Three of these — height, Hb, and how well they preoxygenated — are OURS,
not Gander's; the paper gives BMI and age only.

| | ours, flat RV | ours, BMI-dependent RV | measured |
|---|---|---|---|
| PaO2 before apnoea | 563.8 | **563.8** | **243 (136)** |
| shunt at t=0 | 5.0% | **5.01%** | implied ~20%+ |
| time to SpO2 90% | 251.2 s | **164.4 s** | **127 (43)** |
| PaO2 at SpO2 92% | 43.3 | 44.2 | 68 (10) |
| PaCO2 at SpO2 92% | 51.5 | 55.6 | 53 (4) |

**The timing disagreement is now inside one standard deviation** — 164 s
against 127 (43), whose 1 SD band is 84–170 s. It was 251 s. Nothing about
this benchmark entered the choice of `k_rv_bmi`, which was fixed by Reinius's
CT volume and Holley's ERV threshold before this was run.

**The oxygen disagreement did not move at all.** PaO2 before apnoea is 563.8
either way, to one decimal place, because the arterial oxygen tension at the
moment apnoea starts is set by preoxygenation and by gas exchange, not by how
much gas is in the lung. That is the cleanest available statement of where the
remaining defect is: **not in lung volume.**

**OUR MORBIDLY OBESE PATIENT CARRIES THE LEAN BASELINE SHUNT.** 5.0% at BMI
47. The collapse machinery contributes essentially nothing at the point where
a real patient is most atelectatic. Their PaO2 243 on FiO2 1.0 with PaCO2 46
implies an alveolar PO2 near 655 and an a-A gradient near 410 mmHg — a shunt
measurement in all but name. (That arithmetic is ours; they report no shunt
fraction. n=11 with SD 136 on a mean of 243, so the scatter is large.)

**THE TIMING ERROR WENT UP, THEN CAME BACK DOWN, AND BOTH MOVES WERE RIGHT.**
Before any floor, expiratory reserve volume was **-466 mL** — impossible — and
we took 166 s against a measured 127. Flooring FRC at a flat residual volume
removed the impossibility and the answer went to **251 s**: the unphysical
negative ERV had been hiding half the error by giving the patient an impossibly
small oxygen store. Making residual volume itself fall with BMI, on Reinius's
measurement, brings it to **164 s**. That is close to the original 166 s and it
is worth being explicit that this is NOT a return to the old answer by a
roundabout route — the old 166 s came from a negative ERV, the new 164 s comes
from an ERV of zero, which is what Holley measured in this population.

**AND IT SETTLES WHERE THE DEFECT CANNOT BE.** FRC is now at its floor, so the
oxygen store cannot be reduced further by any parameter. **At BMI 47 the FRC
route is exhausted.** Whatever is missing is in GAS EXCHANGE — shunt or low
V/Q — not in lung volume.

Also available and unused: an obese CO2 slope, 46 -> 53 mmHg over ~127 s,
about 3.3 mmHg/min. We hold no obese CO2 comparator at all.

### Hedenstierna 2020 — READ. THE SHUNT CEILING IS CORRECT AND I WAS WRONG

**Hedenstierna G, Tokics L, Reinius H, Rothen HU, Ostberg E, Ohrvik J.**
Higher age and obesity limit atelectasis formation during anaesthesia: an
analysis of computed tomography data in 243 subjects. *Br J Anaesth*
2020;124(3):336-344. doi 10.1016/j.bja.2019.11.026. **Held and read
2026-09-23.** n=243, age 18-78, **BMI 18-52**, CT awake and during
anaesthesia, preoxygenated FIO2 >0.8 then ventilated FIO2 >=0.3, no PEEP.

**THIS REVERSES A DIAGNOSIS GIVEN WITH CONFIDENCE EARLIER THE SAME DAY.**
It was recorded here that our shunt saturation — 7.2% at BMI 26.4 rising only
to 9.8% at BMI 39.6 — was "a structural ceiling" and a defect, on the
strength of a TWO-POINT extrapolation from Rothen. **The saturation is
correct.**

**THEY FIT A BROKEN LINE WITH THE KNEE AT BMI 30.** Abstract: "Log
atelectasis area was also related to a **broken-line function of the BMI with
the knee at 30 kg m-2** (r2=0.06; P<0.001)." Conclusions: "Atelectasis
increased with BMI in normal and overweight patients, but showed **no further
increase in obese subjects (BMI >=30)**."

| BMI | our shunt | Hedenstierna |
|---|---|---|
| 26.4 | 7.2% | rising limb, below the knee |
| 29.7 | 8.4% | approaching the knee |
| 34.7 | 9.5% | plateau |
| 39.6 | 9.8% | plateau |

**Our collapse machinery already produces the shape they measured.** And
Rothen's two groups (BMI 24.9 -> 4.7%, BMI 27.7 -> 9.9%) sit on the RISING
LIMB BELOW THE KNEE, which is exactly why extrapolating them past 30 gave
nonsense. This file had already flagged that extrapolation as invalid
because it yields negative shunt below BMI 22, and then leaned on it anyway.

**AND THEY SEPARATE THE TWO MECHANISMS EXPLICITLY.** Introduction: "Atelectasis
causes **shunting** of blood through non-ventilated lung tissue, which,
together with **ventilation/perfusion mismatch caused mainly by AIRWAY
CLOSURE**, impedes oxygenation of blood."

**THEIR RESULTS SHOW THE TWO DECOUPLE, and the age data are the cleanest
demonstration:** "Atelectasis increased with increasing age up to 50 yr, and
then decreased with further increase in age... **The P/F ratio, in contrast,
decreased with increasing age even beyond the age of 50 yr.**"

Atelectasis peaks at 50 and falls; oxygenation keeps worsening. **So the
worsening oxygenation is NOT atelectasis-driven.** The same holds across BMI:
atelectasis plateaus above 30 while P/F keeps falling in the obese (P<0.001
between BMI groups during anaesthesia; PaO2 P=0.003).

Other numbers read from the page: atelectasis present in **90%** of subjects,
median **7.0 cm2** (IQR 2.8-12.5), mean 8.8 (SD 7.7), maximum 39 cm2. FIO2 1.0
gave more atelectasis than 0.3-0.5 (12.8 vs 8.1 cm2, P<0.001). P/F fell from
57.6 awake to 44.5 kPa anaesthetised. Awake median PaO2 12.0 kPa, PaCO2 5.2.
Full multiple regression r2=0.23.

**WHERE THIS LEAVES THE OBESE INVESTIGATION.** Gander's BMI 47 patients have
PaO2 243 mmHg on FIO2 1.0, an a-A gradient near 410. If atelectasis has
plateaued by BMI 30, most of that gradient is **airway-closure-driven low
V/Q**, not shunt — which is what Holley 1967 measured with xenon-133 and what
this paper names in its first paragraph.

**AND THIS MODEL NOW HAS NO SUCH MECHANISM.** The V/Q volume-allocation
correction of 2026-09-22 removed the only low-V/Q behaviour it had. That
removal was correct — a ratio of FLOWS cannot allocate a VOLUME — but the
artefact had been standing in for a real effect and nothing replaced it.
**That is the gap, and it is a missing mechanism rather than a mis-set
parameter.**

**THE LESSON, recorded because it is the third instance today.** A two-point
extrapolation, already flagged invalid in this very file, was used to call a
correct feature a defect. The 243-subject measurement was obtainable the whole
time. Rothen was mined for compliance and shunt but the question "does
atelectasis keep rising with BMI?" was answered by arithmetic rather than by
looking.

---

### ~~A CONTRADICTION TO CHECK BEFORE ANY SHUNT PARAMETER MOVES~~ — RESOLVED, see above

Search-resolved 2026-09-23, **NOT READ**, and it reverses a conclusion given
with confidence earlier the same day:

**Hedenstierna G, Tokics L, Reinius H, Rothen HU, Ostberg E, Ohrvik J.**
*Higher age and obesity limit atelectasis formation during anaesthesia: an
analysis of computed tomography data in 243 subjects.* **Br J Anaesth
2020;124(3):336-344. PMID 31918847.** n=243, **BMI 18-52**, CT awake and
during anaesthesia, preoxygenated FIO2 >0.8, no PEEP.

Per the search summary: atelectasis "increased with BMI in normal and
overweight patients but showed **no further increase in obese subjects (BMI
>=30)**", and peaked around age 50 rather than rising monotonically.

**IF THAT HOLDS, OUR SHUNT CEILING IS CORRECT AND THE EARLIER DIAGNOSIS WAS
WRONG.** This file recorded on 2026-09-23 that our saturation — 7.2% at BMI
26.4, 9.5% at 34.7, 9.8% at 39.6 — was a structural defect, on the strength
of a TWO-POINT extrapolation from Rothen's BMI 24.9 and 27.7. That
extrapolation was already flagged here as invalid because it gives NEGATIVE
shunt below BMI 22. A 243-subject pooled CT analysis beats it comprehensively.

**Then Gander's PaO2 of 243 at BMI 47 needs a different mechanism, and the two
papers read today supply a candidate.** Hedenstierna measures ATELECTASIS,
which is true shunt. Holley 1967 measured TIDAL AIRWAY CLOSURE and V/Q
maldistribution, which tracks ERV and is a different thing. If shunt plateaus
above BMI 30 while airway closure keeps worsening as ERV falls, morbidly obese
hypoxaemia becomes increasingly **low-V/Q rather than shunt**.

**Which is uncomfortable**, because the V/Q volume-allocation correction of
2026-09-22 removed this model's only low-V/Q pseudo-shunt. That removal was
right — a ratio of flows cannot allocate a volume — but the artefact may have
been standing in for a real low-V/Q effect the model now has no mechanism for
at all.

**NOTHING MOVES UNTIL HEDENSTIERNA 2020 IS READ.** It is a search summary, it
reverses a stated conclusion, and acting on it would repeat the exact failure
recorded twice already in this file.

**Reinius 2009 was obtained and read 2026-09-23 — see its own section below.**
Still worth having: **Eichenberger A, et al.** *Morbid obesity and
postoperative pulmonary atelectasis: an underestimated problem.* Anesth Analg
2002;95(6):1788-92. PMID 12456460.

---

### The low-V/Q mechanism — BUILT 2026-09-23, and what it costs

Three papers on this branch say the same thing in three different ways, and
none of them is this model's shunt:

| source | what it separates from atelectasis |
|---|---|
| Hedenstierna 2020, n=243, CT | "V/Q mismatch caused mainly by airway closure", stated as a thing distinct from the collapse |
| Reinius 2009, n=30, CT | quantifies **poorly aerated** lung separately from **nonaerated**. Poorly aerated lung still has gas in it |
| Holley 1967, n=8, xenon-133 | measured the ventilation redistribution directly, in this population |

And Hedenstierna 2020 closes the alternative: atelectasis shows **no further
increase above BMI 30**, so this model's shunt ceiling is correct and cannot be
where the missing hypoxaemia comes from. The V/Q correction of 2026-09-22
removed the model's only low-V/Q behaviour — as an artefact, rightly, because
it was allocating gas volume by a ratio of flows — and left nothing in its
place.

#### The mechanism: incomplete denitrogenation

A lung unit whose airway is **already shut when preoxygenation begins** never
sees the oxygen. It is not collapsed: it still holds gas, and it is still
perfused. But the gas it holds is the alveolar **air** it had when the airway
closed, so the blood leaving it is poorly oxygenated while the blood leaving
every other unit is maximally oxygenated. The mixture has a low arterial
oxygen tension at a nearly normal saturation, which is what low V/Q means.

`unwashed_fraction()` in `apnoea_core.py` is that perfusion share. It uses the
**same closure law, with the same two parameters**, as the collapse term that
already runs during apnoea — `max_closed` and `cc_k`, the ceiling on closure
and its half-saturation. The only difference is that it is evaluated at the
**awake** lung volume, because preoxygenation happens before induction.
**No new free parameter, and nothing in it was chosen by looking at a
benchmark.**

The gas in those units is the alveolar gas equation on room air,

    PAO2 = 0.2093 x (PB - 47) - PaCO2 / RQ

which is arithmetic from constants already in the model. Alveolar gas is never
inspired gas, so inspired air would have been the wrong choice as well as the
more flattering one.

#### What it predicts, none of it fitted

1. **Lower arterial oxygen at the start of apnoea** — which is exactly where
   Gander's disagreement is, and where nothing else has ever moved.
2. **Scaling with airway closure, not with atelectasis** — so it is exactly
   **zero** in any patient whose awake FRC exceeds closing capacity, and grows
   with BMI and with age.
3. **More atelectasis on 100% oxygen than on 30–50%** — a closed unit full of
   oxygen absorbs and collapses; a closed unit full of nitrogen is splinted
   open. Hedenstierna 2020 measured **12.8 cm2 against 8.1 cm2**. The sign is
   the one this mechanism requires.

#### What it does, measured 2026-09-23

Perfusion share in unwashed units:

| patient | awake FRC | closing capacity | unwashed |
|---|---|---|---|
| Stock/Toner reference, 45 y, BMI 22.9 | 2412 | 2300 | **0.00%** |
| the same patient at 80 years | 2412 | 3000 | 3.49% |
| Heard cohort, BMI 34.7, 30° head-up | 2096 | 2655 | 3.78% |
| Gander cohort, BMI 47, supine | 847 | 3027 | **15.79%** |

Every row that moved in `test_validation.py`, and it is the whole list:

| row | before | after | band | |
|---|---|---|---|---|
| Heard control, SpO2<95% | 319.8 s | **310.2 s** | 244–314 | **FAIL → PASS** |
| tilt, BMI 44 at 25° | 33.4% | 35.9% | 15–40 | PASS |
| tilt, BMI 35 at 30° | 45.4% | **51.1%** | 20–45 | FAIL, and worse |
| Toner sham, SpO2<95% | 444.5 s | 444.5 s | 380–525 | unchanged |
| tilt, non-obese 20° | 28.6% | 28.6% | 15–40 | unchanged |
| every Stock row | | | | unchanged to 1 dp |

**Everything obese or elderly moved; everything lean is bit-identical.** That
is the signature the mechanism requires, and it was not arranged — it falls out
of the fraction being zero whenever FRC exceeds closing capacity.

Blocking rows go **5 → 4**. `test_parity.py` passes.

#### The cost, recorded and not compensated

**The head-up tilt benchmark got worse: 45.4% → 51.1% against a measured
~+30%,** band 20–45. Head-up tilt raises awake FRC, which shrinks the unwashed
fraction, so in this model tilt now gets **two bites** — once by enlarging the
oxygen store and once by improving denitrogenation. Whether a real lung gives
it both is an open question and a good one; the four positioning trials cannot
separate the two routes.

That row was already failing at 45.4 before this change. Nothing has been
reached for to compensate it, per CLAUDE.md.

#### And what it does NOT do

**Gander's arterial oxygen is still wrong.** 563.8 → **446.9** mmHg against a
measured 243 (136). The mechanism is the first thing that has ever moved this
number at all — it did not shift by one decimal place across the whole
residual-volume correction — but it closes under half the gap. The right
reading is that this is the right KIND of mechanism and not yet the whole size
of it. Candidates for the rest, none of them tested: the fraction may be
larger than the collapse law says because tidal closure during preoxygenation
is intermittent rather than absolute; the unwashed units may hold *less* oxygen
than alveolar air if they have been closed for some time before induction; and
Gander's own preoxygenation was five minutes by face mask **without CPAP** in
patients who are hard to seal, so their starting end-tidal oxygen may have been
well below the 0.90 we assume.

---

### Reinius 2009 — READ 2026-09-23, and it sets the residual-volume floor

**Reinius H, Jonsson L, Gustafsson S, Sundbom M, Duvernoy O, Pelosi P,
Hedenstierna G, Freden F.** Prevention of atelectasis in morbidly obese
patients during general anesthesia and paralysis: a computerized tomography
study. *Anesthesiology* 2009;111(5):979-87. PMID 19809292. Uploaded to the
session and read; **not in the repository**, so the numbers below are what was
read from that upload on the date given and nothing else.

n=30, BMI 45 (SD 4), randomised to PEEP / recruitment+PEEP / neither, CT at
end-expiration after induction and paralysis.

Two things it gives that nothing else in the repository does:

**1. An end-expiratory lung volume in morbid obesity, measured, after
induction and paralysis: 697 (157) mL.** That is the whole lung volume at the
end of a passive expiration, in an anaesthetised paralysed patient at BMI 45 —
about a third of what a lean anaesthetised patient holds.

**2. "Poorly aerated" lung is quantified SEPARATELY from "nonaerated" lung.**
Nonaerated is collapsed lung with no gas in it — true shunt. Poorly aerated is
lung that still contains gas but is ventilating badly — **low V/Q, not shunt**.
This is the same separation Hedenstierna 2020 makes in prose ("V/Q mismatch
caused mainly by airway closure") and that Holley 1967 measured with
xenon-133. Three independent sources now say the same thing: obesity produces
a low-V/Q compartment that is not atelectasis, and the model has no mechanism
for it. That is the open item, recorded in HANDOVER.

#### A CORRECTION TO THE COMMIT THAT MADE THIS CHANGE

The commit message for the BMI-dependent residual volume says the benchmark
suite is **"bit-identical either side of it"** and that the change **"adds none
and fixes none"**. Both statements are false, and the way they came to be
written is the failure mode this file exists to catch: three Stock rows were
spot-checked against a clean checkout, the rest were reasoned about rather than
run, and the reasoning was that the residual-volume floor could not bind in a
patient whose FRC was above it. Running the whole suite on both sides, **four
rows moved**:

| row | before | after | |
|---|---|---|---|
| tilt, BMI 44 at 25° | **0.0%** | 33.4% | FAIL → **PASS** |
| tilt, BMI 35 at 30° | 34.5% | **45.4%** | PASS → **FAIL** |
| Stock obstructed, PaO2 at 5 min | 157.0 | 157.2 mmHg | PASS |
| Moreault, pressure tracks gas removed | −13.3 | −11.8 cmH2O | PASS |

The blocking count stayed at five **by coincidence** — one tilt row fixed, the
other broken.

**And the zero is the finding the spot-check missed.** At BMI 44 the flat
residual-volume floor bound at *both* tilt angles, so head-up tilt bought that
patient **exactly nothing** — a gain of 0.0% against four positioning trials
measuring about +30%. That is independent support for making residual volume
BMI-dependent, and it was invisible until the suite was run properly. All three
tilt gains are now regenerated by `handover_numbers.py`.

#### The ruling it settles: `rv` is now BMI-dependent

`rv` is **residual volume** — the gas that cannot be squeezed out of the lungs
at the end of the hardest possible expiration. It is a floor: functional
residual capacity (`frc`, the volume left after a normal quiet breath out)
cannot fall below it. Until 2026-09-23 the model held `rv` at a single value
for everybody, which was wrong in an obvious direction — the chest wall and
abdomen that push FRC down in obesity push residual volume down too.

The anchor is Reinius's 697 mL. Holley 1967 measured expiratory reserve volume
(`erv`, the extra gas you can still blow out below a quiet breath — that is,
FRC minus RV) falling to essentially **zero** in morbid obesity. If ERV is zero
at BMI 45, then FRC *is* RV there, so Reinius's measured 697 mL is an **upper
bound on residual volume at BMI 45**, not a coincidence. Solving

    1100 * exp(-k * (45 - 22)) = 697   ->   k = 0.0198

gives `k_rv_bmi = 0.0198`, with `rv = 1100` mL now stated as the value **at BMI
22**, anaesthetised and supine, rather than as a universal constant.

**This is not tuning a parameter to pass a benchmark.** No benchmark in
`test_validation.py` moves on it — it is a measured volume in a measured
population, and the exponent is fixed by two measurements, not fitted to an
outcome. What it changes is that FRC in the obese is now floored by something
physical instead of by a constant that happened to be a lean patient's.

Recomputed 2026-09-23 against `apnoea_core.py` (provenance printed), height
1.75 m, age 42:

| BMI | residual volume | FRC awake | FRC anaesthetised | ERV anaesthetised |
|---|---|---|---|---|
| 22.9 | 1081 | 2412 | 2012 | 931 |
| 34.3 | 862 | 1498 | 1123 | 261 |
| 44.4 | 706 | 982 | 737 | 31 |
| 46.4 | 679 | 905 | 679 | 0 |

At the Reinius BMI of 45.0 exactly, the model gives residual volume 698 mL and
anaesthetised FRC 719 mL, against Reinius's measured 697 (157). ERV reaching
zero at BMI 46 is Holley's finding falling out of the model rather than being
put into it.

**What this does NOT license.** Reinius's 697 is an end-expiratory volume in
patients who were induced and paralysed, not a residual volume measured by
washout. Reading it as RV depends entirely on Holley's ERV going to zero. If
that link is wrong, the exponent is wrong with it. It is recorded here so that
the dependency is visible rather than buried in a constant.

---

### Holley 1967 — the obesity mechanism, MEASURED, and a bug it exposed

**Holley HS, Milic-Emili J, Becklake MR, Bates DV.** Regional distribution of
pulmonary ventilation and perfusion in obesity. *J Clin Invest*
1967;46(4):475-81. Held and read 2026-09-23. This is the paper both
closing-capacity sources cite for obesity.

n=8 (5 women, 3 men), **95-140 kg**, awake and seated at rest, regional
ventilation and perfusion by **xenon-133**. Verbatim:

> "In four subjects in whom the **expiratory reserve volume** averaged 49% of
> predicted normal, the ventilation distribution as measured with 133xenon was
> normal. In the remaining four subjects, in whom the **expiratory reserve
> volume was reduced to less than 0.4 L** and averaged only 21% of predicted
> values, the distribution of a normal tidal breath was predominantly to the
> **upper zones**."

> "In all subjects the perfusion distribution was predominantly to the lower
> lung zones but was slightly more uniform than in normal nonobese subjects...
> this abnormality bearing a **close relationship to the reduction in
> expiratory reserve volume**."

**THE MECHANISM IS MEASURED, NOT ASSERTED.** Obesity reduces ERV; ventilation
redistributes away from the dependent zones where perfusion is greatest;
V/Q mismatch follows. ERV = FRC - RV, so this is the FRC mechanism. Closing
capacity does not appear. Perfusion distribution barely moved — it was
VENTILATION that shifted.

**AND IT IS A THRESHOLD, NOT A GRADIENT.** Four normal, four abnormal, split
at roughly **ERV < 0.4 L**. That is a sharper prediction than a regression and
it is directly checkable.

**A BUG IT EXPOSED: FRC CAN FALL BELOW RESIDUAL VOLUME.** Checking our ERV
against Holley's threshold showed that `frc_awake()` has no floor at all and
`frc_anaes()` is floored at 400 mL, but NEITHER is floored at `rv`. At BMI
34.7 with `k_frc_bmi` >= 0.10 the awake FRC goes UNDER RV, which cannot
happen; the anaesthetised ERV goes negative from `k` ~ 0.070. **Any sweep of
`k_frc_bmi` above ~0.064 for this patient is meaningless**, and one was run
and reported before this was noticed.

| k_frc_bmi | FRC awake | ERV awake | FRC anaes | ERV anaes |
|---|---|---|---|---|
| 0.0417 (shipped) | 2096 | 996 | 1696 | 596 |
| 0.0490 | 1910 | 810 | 1510 | **410** |
| 0.0639 | 1581 | 481 | 1186 | 86 |
| 0.0700 | 1464 | 364 | 1098 | **-2** |
| 0.1000 | 1001 | **-99** | 750 | -350 |

**AND THE VALUE THAT REPRODUCES HEARD LANDS ON HOLLEY'S THRESHOLD.** At
`k` ~ 0.049 — the value that puts Heard's control arm on its measured median
of 296 s — the ANAESTHETISED ERV is **410 mL** against Holley's dividing line
of **400 mL**. Two independent routes to the same volume.

**Do not overread that.** Holley's subjects were AWAKE and SEATED; ours is
anaesthetised and 30 degrees head-up, and its AWAKE ERV at that setting is
810 mL, comfortably inside his normal group. The agreement is suggestive, not
confirmatory. What it does establish is that the FRC needed to reproduce Heard
puts the patient at the volume where V/Q distribution was measured to start
failing, rather than at some arbitrary fitted value.

**WHAT HOLLEY DOES NOT GIVE:** any shunt fraction, any anaesthetised subject,
any supine measurement. n=8, 1967, awake and seated. It establishes the
mechanism and a threshold; it cannot calibrate an anaesthetised shunt.

---

### The closing-capacity block is wrong in three ways — READ 2026-09-23

Held and read on 2026-09-23, both in full:

**Milic-Emili J, Torchio R, D'Angelo E.** Closing volume: a reappraisal
(1967-2007). *Eur J Appl Physiol* 2007;99(6):567-83.

**Hopton P, et al.** Airway closure in anaesthesia and intensive care.
*BJA Education* 2022;22(4):126-130. doi 10.1016/j.bjae.2021.12.001.
PMID 35531076.

`apnoea_core.py` labels its closing-capacity block "PLACEHOLDER REGRESSION".
It now has a real target, and it is wrong in three separate ways.

**BUIST & ROSS OBTAINED AND READ AT SOURCE 2026-09-23.** Buist AS, Ross BB.
*Predicted values for closing volumes using a modified single breath nitrogen
test.* **Am Rev Respir Dis 1973;107(5):744-52.** It gives a BETTER equation
than the review does, verbatim:

> "No statistical differences between the regression coefficients for men and
> women were found. The combined regression equations are: **CC/TLC in per
> cent = 0.525 age (years) + 14.348 +- 4.34**; CV/VC in per cent = 0.318 age
> (years) + 1.919 +- 4.61."

Milic-Emili's review quotes the SEX-SEPARATED forms; the authors themselves
recommend the COMBINED one, and it is steeper than either. **Use 0.525 and
14.348.**

**THEY MEASURED HEIGHT AND WEIGHT AND NEITHER APPEARS IN THE FORMULA.**
Methods: "After the subject completed the questionnaire, his height and weight
were measured." Table 1 reports both. The published predictor is age alone.
That is stronger than the review's silence on BMI, though it still falls short
of a positive test of weight as a predictor, which the paper does not report.

**THE INVERSION, which kills the obvious defence.** If our regression were
merely theirs expressed against a different lung size, some TLC would
reconcile them. None does:

| age | our CC | Buist CC/TLC | implied TLC |
|---|---|---|---|
| 20 | 1800 mL | 24.8% | 7244 mL |
| 40 | 2200 | 35.3% | 6224 |
| 60 | 2600 | 45.8% | 5671 |
| 80 | 3000 | 56.3% | 5324 |

Ours agrees with theirs **only if TLC falls from 7.2 L at age 20 to 5.3 L at
80**. TLC is approximately age-stable — it is FRC and RV that move with age.
So this is not a scaling choice: **the two regressions have genuinely
different slopes, and ours is too shallow.**

---

**1. THE NORMATIVE REGRESSIONS ARE AGE AND SEX ONLY.** Milic-Emili 2007
quotes Buist & Ross 1973 (n=284 healthy non-smokers, 16-85 yr, single-breath
N2), equations (2) and (3):

    Males   (n=132):  CC/TLC (%) = 14.9 + 0.50 x age(yr)   SE 4.1
    Females (n=152):  CC/TLC (%) = 14.4 + 0.54 x age(yr)   SE 4.4

and Teculescu 1996, equations (4) and (5), which agree closely:
`13.8 + 0.46 x age` males, `12.5 + 0.51 x age` females. **No BMI term, no
weight term.** CC is normalised to TLC, i.e. to body SIZE, not body MASS.

**2. OUR AGE SLOPE IS TOO SHALLOW BY ABOUT A THIRD.** `cc_per_year` = 20
mL/yr against Buist & Ross's 0.50% of TLC per year = **30-35 mL/yr** for TLC
6.0-7.0 L. Our `cc_at_20` = 1800 mL against their implied ~1620 mL at TLC
6.5 L. So our curve starts too high and rises too slowly, crossing theirs
near age 45.

**THE CROSSOVER TEST, which has no free parameters in it.** Both papers put
CC = FRC at **~44 years supine** (Milic-Emili: "in the supine position, CC
exceeds FRC much earlier (~44 years)"; BJA Ed: "recognised at ~44 yrs of age
when supine and ~70 yrs [erect]"). **Ours crosses at 50.6 years.**

**3. THE BMI TERM MODELS A MECHANISM BOTH PAPERS ATTRIBUTE TO FRC.**

> Milic-Emili 2007: "Tidal airway closure is common in obesity (Holley et al.
> 1967), anaesthesia (Hedenstierna 2003)... The tidal airway closure and
> concurrent hypoxemia found in obesity and anaesthesia **have been attributed
> mainly to reduction in FRC**."

> BJA Ed 2022: "**Obesity and pregnancy have little effect on TLC and CC.**
> Decreased FRC in the supine position is associated with a reduced ERV, but
> an **unchanged CC**."

The second is a positive statement, not an absence, which matters because
reasoning from what a paper does not say has been wrong repeatedly here.

Our model opens the CC-FRC gap from BOTH ends: `k_frc_bmi` drops FRC (correct,
and the supported mechanism) AND `cc_per_bmi` = 45 mL per BMI unit raises CC
(unsupported). At BMI 39.6 versus 23.1, FRC falls 1178 mL and CC climbs 654
mL — so roughly **45% of our obese airway closure comes from a term the
literature contradicts**. The same compensating-pair shape as the V/Q volume
error.

**AND CORRECTING IT MAKES THE OBESE BENCHMARK WORSE, WHICH IS THE POINT.**
Removing the BMI term LOWERS obese CC, giving less closure, less shunt and
SLOWER desaturation — and Heard is already too slow at 319.8 s against an IQR
of 244-314. Re-anchoring the age terms only partly offsets it: at Heard's age
42, a steeper slope adds ~264 mL, a corrected intercept removes ~180 mL, and
dropping the BMI term removes ~437 mL at BMI 34.7. **Net, a properly anchored
CC is about 350 mL LOWER for Heard's patient than ours is now.**

**So the obese deficit cannot live in closing capacity.** It is in FRC against
BMI, or in the conversion from closure to shunt. That makes **Jones & Nzekwu,
Chest 2006;130(3):827-33** the decisive paper rather than a supporting one.

**A STRUCTURAL OBSTACLE TO IMPLEMENTING THIS.** Buist & Ross give CC as a
PERCENTAGE OF TLC. **This model has no TLC.** Implementing their regression
faithfully means adding a predicted TLC (Quanjer/ERS 1993, which Milic-Emili
uses) rather than editing three constants. That is a piece of work, not a
parameter change, and it should be costed before it is started.

**Caveat held against ourselves:** Buist & Ross studied healthy non-smokers,
almost certainly not obese. The ABSENCE of a BMI term in their regression is
not by itself proof that CC is BMI-independent in obesity. The BJA Education
sentence is what carries this, because it is a positive claim.

**Two more papers surface from these:** Holley HS et al 1967 (the obesity
airway-closure source both cite) and Hedenstierna 2003 (anaesthesia).

---

### Hardman 2000 and McNamara 2005 — READ 2026-09-22, and they overturn a conclusion

**Hardman JG, Wills JS, Aitkenhead AR.** Factors Determining the Onset and
Course of Hypoxemia During Apnea: An Investigation Using Physiological
Modelling. *Anesth Analg* 2000;90:619-24. **PMID 10702447.** Held and read.

**McNamara MJ, Hardman JG.** Hypoxaemia during open-airway apnoea: a
computational modelling analysis. *Anaesthesia* 2005;60:741-6.
**doi 10.1111/j.1365-2044.2005.04228.x.** Held and read.

**THE NOTTINGHAM SIMULATOR HAS A V/Q DISTRIBUTION. IT ALWAYS DID.** This
repository concluded from Hardman 1998's Appendix 1 — *"Complete mixing of
gases within the alveoli is assumed… blood flow… two compartments: shunted and
non-shunted"* — that ICSM has no V/Q distribution, that our sealed-airway
mechanism is **structurally absent** from their model, and that **"any future
use of an ICSM number to argue about V/Q is void."** All three are false.

> Hardman 2000, Methods: the NPS respiratory models include *"anatomical and
> equipment dead spaces and **100 parallel pulmonary compartments with
> independent compliance curves and ventilation/perfusion ratios**."*

> McNamara 2005, Methods: *"**Five hundred alveolar compartments** were used in
> the model… Each of the 500 alveolar compartments has an **independently
> configured compliance curve and inlet (bronchiolar) resistance**. Each
> alveolar compartment has an associated pulmonary vessel… with an
> **independently configured vascular resistance**."*

**100 compartments by 2000, 500 by 2005, against our 80.** The 1998 text
describes a simpler configuration and does not describe the model used in any
paper we compare against. The quotation was accurate; the inference from it was
not, and it was used to dismiss a comparator.

**McNamara's dispersion is narrower than ours.** Their deliberately
"critically ill" configuration had **mean (SD) V/Q ratio 1.54 (0.84)** — a
coefficient of variation of 0.545, corresponding if log-normal to a log SD near
**0.51**, against our 0.70. A lung they built to be pathological is less
dispersed than our healthy one. Recorded as an observation, not a target.

**HARDMAN 2000 MODELS THE CLOSED AIRWAY EXPLICITLY, which is Stock's regime.**
70 kg, FRC 2500 mL, VO2 0.25 L/min, Hb 145 g/L, 2 min denitrogenation. Their
Figure 1 gives arterial oxygen tension against time for three venous admixtures
with the airway closed. Read at **5 minutes of apnoea**:

| | PaO2 at 5 min |
|---|---|
| NPS closed airway, 1% venous admixture | ~55 kPa ≈ 412 mmHg |
| NPS closed airway, 10% venous admixture | ~45 kPa ≈ 337 mmHg |
| **Stock 1989, MEASURED in 14 humans** | **314 (87) mmHg** |
| ours | **61 mmHg** |

**Their 10%-shunt closed-airway curve lands on Stock's measurement.** Ours is a
fifth of it. Figure values are read off a printed plot, good to perhaps ±5 kPa,
which is nowhere near enough to matter.

Their Table 1: time to SaO2 50% is **8 min 13 s closed** against 11 min 37 s
open, so obstruction costs about 3½ minutes in their model. We reach SaO2 40%
at 8.6 min. **The timing is comparable; the tension is not** — which is exactly
the signature of a defect in how arterial oxygen is composed from alveolar
oxygen, not in the oxygen budget.

**NO PRESSURE IN EITHER PAPER.** Hardman 2000 notes only that *"the modelled
patient made no respiratory efforts during apnea with a closed airway, which
would otherwise have caused fluctuating intrathoracic pressures"*. Whether ICSM
floors intrathoracic pressure remains undeterminable from anything we hold.

**Other things worth having from McNamara 2005:** oxygen extracted at
250 mL/min with CO2 added at 10 mL/min gives a **net gaseous flow from alveoli
to blood of 240 mL/min** (our aventilatory-mass-flow benchmark sits at 224);
only about **5% of produced CO2 enters the lungs**, consistent with Holmdahl's
90% dissolving in body water.

---

### Laviola 2020 — WE HELD THE OXYGEN TIME COURSE ALL ALONG

**Laviola M, Niklas C, Das A, Bates DG, Hardman JG.** Effect of oxygen
fraction on airway rescue: a computational modelling study. *Br J Anaesth*
2020;125(1):e69-e74. **doi 10.1016/j.bja.2020.01.004.** Held and read.

**A CORRECTION TO THIS FILE, 2026-09-22.** Earlier the same day it was
recorded here and in `test_validation.py` that no ICSM oxygen value existed at
a time Stock also measured. That was reached by searching the **2026** paper's
SDC and main text and inferring absence. **It was wrong, and the data was in a
paper already on the shelf.** Figure 1 of this 2020 paper gives PaO2 at
**one-minute intervals** through obstructed apnoea, for three supraglottic
oxygen fractions. Reasoning from what a document does not contain is the move
CLAUDE.md forbids, and this is the second time it has cost something here.

Read off the FO2 21% panel, apnoea beginning at their 3 min mark:

| min of apnoea | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| ICSM PaO2 (kPa) | 74 | 67 | 59.5 | 50 | 38.5 | **26.5** | 14.5 | 8 |
| ours (kPa) | 68 | 61 | 44 | 18 | 11 | **8.1** | — | — |

**At Stock's five minutes: Stock 314 (87) mmHg measured, ICSM ~199 mmHg,
ours 61 mmHg.** ICSM sits 37% below the measurement; we sit 81% below. At
199 mmHg their saturation is essentially 100%, consistent with Stock's "every
one of 14 above 92%". Ours is 85.3% and is not.

**This kills the "two extrapolations landing in the same place" story.** The
curves start together — 68 against 74 kPa — and diverge from about two
minutes. Values are read off a printed figure, good to perhaps ±2 kPa, which
is nowhere near enough to matter.

**NO PRESSURE APPEARS ANYWHERE IN THE PAPER.** Searched in full: not one
cmH2O figure. Only the qualitative *"a single, passive inhalation (caused by
intrathoracic hypobaric pressure)"* and *"the sub-atmospheric intrathoracic
pressure was relieved by inflow via the newly opened airway"*. The passive
inhalation **volume** is not reported either, which would have let their
pressure be backed out from their compliance. **So whether ICSM floors
intrathoracic pressure, and at what value, is not determinable from what we
hold** — a question worth asking, because our own sealed lung reaches about
−79 cmH2O and the floor that used to guard it was shown to be inert.

Their protocol, verified: 100 virtual subjects, 65–75 kg, FRC 2.1–2.3 L, 3 min
of 100% oxygen, then apnoea with complete upper airway obstruction; rescue at
SaO2 20%, 40% or 60% to supraglottic FO2 of 100%, 60% or 21%; no positive
pressure at any point.

---

### Heard 2017 — OBTAINED AND READ 2026-09-22, and it moved four things

**Heard A, Toner AJ, Evans JR, Aranda Palacios AM, Lauer S.** Apneic
Oxygenation During Prolonged Laryngoscopy in Obese Patients: A Randomized,
Controlled Trial of Buccal RAE Tube Oxygen Administration. *Anesth Analg*
2017;124(4):1162-7. **doi 10.1213/ANE.0000000000001564.** Read in full.

This is the paper three earlier sends were not — those were the Brown
commentary on it. Every figure below is read off the page.

**THE BAND WAS RIGHT, and it is an IQR.** Verbatim: *"Median (interquartile
range [IQR]) apnea times with SpO2 ≥ 95% were prolonged in this group; 750
(389–750) versus 296 (244–314) seconds, P < .0001."* The commentary called
these "range" and this file recorded the ambiguity as unresolvable without the
paper. It is resolved: **IQR**. Landing inside 244-314 is the stronger
reading, not the weaker one.

**THE CONFIGURATION WAS WRONG IN FOUR WAYS. Three are now fixed.**

| | we had | the paper |
|---|---|---|
| weight | 107 kg | **105 ± 13** (83–132) |
| height | 1.75 m | **174 ± 9 cm** (160–191) |
| age | 45 y | **42 ± 14** (19–66) |
| position | tilt 25° | **30° reverse Trendelenburg** |
| preoxygenation | `feo2_start` 0.87 | **EtO2 ≥ 80%** |
| airway | `resistance=2`, fully patent | **deliberate grade 3 view**, "simulating the partially obstructed airway" |

The first five are corrected. **The sixth is not**, and it is recorded as a
known over-estimate of airway patency: we model a deliberately obstructed
laryngoscopy as the most patent setting the model has. It matters more for the
buccal arm than the control arm, because the whole question there is whether
oxygen tracks past the blade.

**THE BENCHMARK SURVIVES ALL OF IT, and that is the uncomfortable part.**
Control arm, time to SpO2 <95%, against a measured IQR of 244-314:

| configuration | t95 |
|---|---|
| shipped (107/1.75/45, tilt 25, feo2 0.87) | 289.2 s |
| paper's weight/height/age only | 311.6 s |
| paper's tilt 30° only | 307.1 s |
| paper's EtO2 0.80 only | 264.4 s |
| **paper exact** | **284.5 s** |

Every one passes, and the corrections nearly cancel — which is why four
mismatches sat there unnoticed. **A benchmark insensitive to a 7-point change
in starting alveolar oxygen is a weak constraint on the oxygen limb.** That is
the same conclusion the V/Q work reached by a different route, and it is an
argument for treating the Heard pass as much softer evidence than a green row
suggests.

**THREE COMPARATORS IN THE PAPER THAT WE ARE NOT USING:**

- **Peak EtCO2 40 (38–45) mmHg standard care, 44 (39–50) buccal.** We hold no
  CO2 comparator at all in an obese patent-airway cohort.
- **Lowest SpO2 97 (92–99) standard versus 91 (89–92) buccal.** The buccal arm
  went *lower*, which is counterintuitive and unmodelled.
- **A third of buccal patients did not hold SpO2 ≥ 95% for the full 750 s**,
  which the authors attribute to atelectasis and shunt in obese patients under
  anaesthesia. Directly relevant to the collapse limb.

**A REFERENCE WORTH CHASING, from their reference list:** McNamara MJ, Hardman
JG. *Hypoxaemia during open-airway apnoea: a computational modelling
analysis.* Anaesthesia 2005;60:741-6. That is the Nottingham simulator applied
to apnoea — the nearest thing yet to an answer on where ICSM's oxygen sits.
Note "open-airway", so it may still not cover the obstructed case.

---

## 2a. Citations resolved by web search, 2026-09-21 — **RESOLVED, NOT READ**

**Read this header before using anything in this section.**

No paper was obtained. Every publisher domain is blocked on both egress paths
in this environment — `pmc.ncbi.nlm.nih.gov`, `europepmc.org`, `doi.org`,
`api.crossref.org`, `api.openalex.org`, `mdpi.com`, `nature.com`,
`link.springer.com`, `bjanaesthesia.org` and the rest all fail at CONNECT with
403, and `WebFetch` returns `EGRESS_BLOCKED` for the same hosts. Only GitHub is
reachable. The Google Drive connector is present but **not connected**. Web
*search* works, so what follows is bibliographic identity and nothing else.

**These are citations, not readings.** CLAUDE.md is explicit that this project's
oldest failure came from treating a search result as a source, and a search tool
has already confabulated an attribution here once — it confidently gave Stock
1989's numbers to Holmdahl. So:

- **Nothing in this section changes a parameter, a band, or a claim.**
- No numeric result reported in a search summary has been entered anywhere.
- Every row below stays in §2 as unread until someone opens the paper.

What this section does is make the unretrievable retrievable. Four of the §2
entries could not be ordered from a library as written; now they can.

| repo citation | resolved to | identifier |
|---|---|---|
| "Lane 2005" | Lane S, et al. A prospective, randomised controlled trial comparing the efficacy of pre-oxygenation in the 20° head-up vs supine position. *Anaesthesia* 2005;60(11):1064-1067 | PMID 16229689, doi 10.1111/j.1365-2044.2005.04374.x |
| "Ramkumar 2011" | Ramkumar V, Umesh G, Philip FA. Preoxygenation with 20º head-up tilt provides longer duration of non-hypoxic apnea than conventional preoxygenation in non-obese healthy adults. *J Anesth* 2011 | PMID 21293885, doi 10.1007/s00540-011-1098-3 |
| "Altermatt 2005" | Altermatt FR, Muñoz HR, Delfino AE, Cortínez LI. Pre-oxygenation in the obese patient: effects of position on tolerance to apnoea. *Br J Anaesth* 2005;95(5):706-709 | doi 10.1093/bja/aei231 |
| "Dixon 2005" | Dixon BJ, Dixon JB, Carden JR, et al. Preoxygenation is more effective in the 25° head-up position than in the supine position in severely obese patients. *Anesthesiology* 2005;102(6):1110-1115 | PMID 15915022 |
| "Sci Rep 2023 (n=91)", PMCID only | Kaiser HA, Bauer T, Riva T, et al. Carbon dioxide and cardiac output as major contributors to cerebral oxygenation during apnoeic oxygenation. *Sci Rep* **2024;14:3617** | PMC10864331, doi 10.1038/s41598-023-49238-3 |
| "Chest" — journal name only | **CANDIDATE, unconfirmed:** Kiely DG, Cargill RI, Lipworth BJ. Effects of hypercapnia on hemodynamic, inotropic, lusitropic, and electrophysiologic indices in humans. *Chest* 1996;109(5):1215-21 | PMID 8625670 |
| *Circulation* 1963;28:346, no author | Roy SB, Bhatia ML, Mathur VS, Virmani S. Hemodynamic Effects of Chronic Severe Anemia. *Circulation* 1963;28(3):346 | PMID 14059454, doi 10.1161/01.CIR.28.3.346 |
| OLV review, doi only | Byun S-H. Optimizing Lung Collapse During One-Lung Ventilation: Physiological Mechanisms and Clinical Strategies: A Narrative Review. *J Clin Med* 2026;15(13):5078 | PMID 42452539, PMC13363232 |
| Heard 2017 | (citation already complete) | doi 10.1213/ANE.0000000000001564 |
| Toner 2019 | (citation already complete) | PMID 31094782, doi 10.1213/ANE.0000000000003810 |
| Hardman 2000;90:614-8 | (citation already complete) | PMID 10702446. Its companion, Hardman JG, et al. *Factors determining the onset and course of hypoxemia during apnea*, is PMID 10702447 |

### The Marshall citation was WRONG — caught by search, 2026-09-22

`apnoea_core.py` and `HANDOVER.md` both cite the hypoxic-pulmonary-
vasoconstriction dose-response as:

> Marshall BE, **Marshall C, Frasch F, Hanson CW**. *Respir Physiol*
> 1994;96:231-47

**The journal, volume and pages are right. The author list is not.** The paper
at that location is:

> **Marshall BE, Clarke WR, Costarino AT, Chen L, Miller F, Marshall C.**
> The dose-response relationship for hypoxic pulmonary vasoconstriction.
> *Respir Physiol* 1994;96(3):231-47.

The likely mechanism of the error: Marshall BE, Hanson CW, Frasch F and
Marshall C published a DIFFERENT two-part paper the same year — *Role of
hypoxic pulmonary vasoconstriction in pulmonary gas exchange and blood flow
distribution*, parts 1 and 2, *Intensive Care Med* 1994;20:291-7 and
20:379-89. The two citations were merged: the authors of one, the locator of
the other.

**Which way the error runs matters.** Our page numbers point at the right
paper and our author line does not, so the equations in `apnoea_core.py` are
probably sourced correctly and only the attribution is wrong. That is the less
damaging direction, but anyone ordering the paper by the author line gets a
different paper and would conclude our equations are unsupported.

**Search-resolved, NOT read.** The same rule as everything else in this
section: no publisher domain is reachable from this environment and nobody has
opened the paper. The correction to the author list is bibliographic identity
from search. **Marshall stays in §2 as unread.** What changes is that it can
now be ordered successfully, which it could not before.

**This is the argument for the whole audit in one item.** The citation sat
unchallenged for months, reads as authoritative, and carries the entire
pulmonary vascular limb. Nothing in the model detected it, because nothing in
the model can. Only looking it up did.

### Three things this turned up that need checking when the papers arrive

1. ~~**The Sci Rep citation in the repository may be wrong on two counts.**~~
   **ANSWERED 2026-09-22 BY READING THE PAPER, and the answer is split.** We
   recorded "Sci Rep 2023 (n=91)". The paper says **"Ninety-one complete data
   sets were analysed"**, so **n=91 is RIGHT** — the 125 in the search summary
   was the number recruited, not analysed. **The year was WRONG: 2024, not
   2023**, now corrected in `apnoea_core.py`, `test_validation.py` and
   `README.md`.

   Worth noting how close this came to going the other way. The search summary
   offered "125 patients", and had that been written in on the strength of a
   summary it would have replaced a correct number with a wrong one. The paper
   settled it; the summary would have corrupted it.
2. **The *Chest* candidate is plausible but unconfirmed.** Kiely 1996 reports
   hypercapnia's effect on exactly the indices `test_validation.py` names
   ("HR, SV, CO and MAP all rose"), in humans. That is a good fit and nothing more.
   Do not write it into `test_validation.py` as the source until someone has the
   paper in front of them and can confirm the magnitudes the band was set from.
3. **Roy 1963 looks consistent with what the code already says**, which is mildly
   reassuring and is not evidence. `apnoea_core.py` derives `hb_co_exp` from
   "CI 6.3 vs ~3.2 normal = 1.97x" at Hb 4.5; the summary describes a group B of
   n=25 at Hb 4.5 g/dL with cardiac index 6.3. Consistent — but a search summary
   agreeing with a remembered number is the weakest possible confirmation, and if
   anything it raises the question of whether both trace to the same memory.

**None of the above lets any §2 row move to §1.** Reading status is unchanged.

---

## 2b. Partially read — first page only

**Frumin MJ, Epstein RM, Cohen G. Apneic Oxygenation in Man. *Anesthesiology*
1959;20(6):789-798.** doi 10.1097/00000542-195911000-00007.

Page 789 seen 2026-09-21 as a screen capture; pages 790-798 **not seen**.

**Verified from that page:**

- The citation is exactly right as `editorial.md` reference [2] gives it.
- Authors M. Jack Frumin, Robert M. Epstein, Gerald Cohen; Columbia University
  and the Presbyterian Hospital, New York. Accepted 25 June 1959, presented to
  the ASA at Miami Beach 9 October 1959.
- **n = 8**, "essentially healthy patients scheduled for a variety of minor
  operations". The repository has never recorded a sample size for this paper.
- **The airway was PATENT with an oxygen reservoir attached, not obstructed.**
  After denitrogenation the endotracheal tube was left connected to a circle
  apparatus filled with 100% oxygen, and only the manual ventilation stopped.
  That is apnoeic oxygenation with a supply, so nothing in it constrains the
  obstructed regime, which is the regime this project's open defect lives in.
- Method otherwise: premedication meperidine 50-100 mg and scopolamine 0.4 mg;
  100% oxygen by circle for five minutes; thiopental then succinylcholine;
  cuffed endotracheal catheter sealed by cuff inflation; denitrogenation on
  100% oxygen for at least 30 minutes at 8 L/min or more.
- **Two lineage facts worth having.** Its introduction credits Bartlett et al.
  with proposing **"aventilatory mass flow (AVMF)"** — the term
  `test_validation.py` uses for one of its bands, so that band's vocabulary
  traces through here. And it names **Holmdahl** as having reviewed the
  literature and coined "apneic diffusion oxygenation", which is the Holmdahl
  1956 paper this project has been trying to obtain since 2026-09-19.

**NOT verified, because it is all on pages we do not have.** `editorial.md:43`
makes four specific claims about this paper — that subjects reached pH below
7.0 within 30 minutes, a pH nadir of **6.72**, a PaCO2 of **250 mmHg at 53
minutes**, and saturation held at **98-100% throughout** — and
`apnoea_core.py` attributes an arterial CO2 rise of **3.0-3.4 mmHg/min** to it.
None of that appears on page 789. It is Methods and introduction only.

**And our own numbers in the same sentence are checked by nothing.**
`editorial.md:43` continues "Our model reproduces this: 2.86 mmHg.min-1 and
pH 7.05 at 30 minutes in a lean adult, but pH 6.95 at 30 minutes in an obese
one". Those three figures appear in no script — not `handover_numbers.py`, not
`buccal_numbers.py`, not `protocol/predictions.py`. They are exactly the
"numbers in markdown rot" case CLAUDE.md warns about, in a tracked document
that ships.

**What to send:** pages 790-798, or just the results tables.

---

## 3. Values with no source at all

These carry specific non-round values and no citation. A precise number with no
provenance is more dangerous than an obviously rough one, because it reads as
measured.

| value | where | note |
|---|---|---|
| `FRC(L) = 2.34·height + 0.009·age − 1.09` | `apnoea_core.py`, `model.js`, `airway_scenario.html` | **The largest uncited lever in the model.** No author, journal or year anywhere. A ±12% error in `frc_ref` takes a headline clinical benchmark out of band; ±30% in `k_frc_bmi` takes the obese one out in both directions. The quoted age term is **not implemented**. Measured and recorded in the code comment, and regenerated by `handover_numbers.py` |
| ~~`crs` = 85.0 mL/cmH2O~~ **RULED 2026-09-22, now 75.0** | `apnoea_core.py`, `build_page.py`, `airway_scenario.html` | **CLOSED.** It was uncited and sat above the 60-75 range the same file cites Rothen for. Now set to Rothen 1993 Table II group 1, n=10, 75 (19) mL/cmH2O — the better-powered of the paper's two groups. The sweep is the reason it is 75 and not 60: measured slope 3.4, band 2.4-4.4, **crs 60 gives 4.371 which PASSES, crs 75 gives 4.601 which FAILS, crs 85 gave 4.716**. 75 is the value that buys nothing, so the §"do not tune" objection does not attach to it; 60 could not have been taken without that objection following it forever. Note also that `crs` moves the CO2 slope 7% and PaO2 0.6% across its whole range — it is a CO2-only lever and cannot bear on the oxygen disagreement |
| `tau_collapse_o2` 60 s, `tau_collapse_air` 900 s, `perfusion_gain` 1.2 | `apnoea_core.py` | No comment, no citation |
| `vo2_ref` 250, `vo2_drop_per_kg` 0.27 | `apnoea_core.py` | No citation. Farmery & Roe (held) quote Nunn's anaesthetised **0.20 L/min** against our 232 mL/min — an external handle that exists and is unused |
| negative-pressure pulmonary oedema; rat upper-airway models; cuirass ventilation | `protocol/evidence.md` | Three whole literatures cited with numbers and **no citations at all**, as the stated reasons for excluding four candidate evidence bodies. Ships in the package |

---

## 4. Held but unused

| source | status |
|---|---|
| **Ebata 1991** | Read, verified — and `apnoea_core.py` cites it **nowhere**. It is the strongest in-session cross-check on the circulatory limb and it is sitting idle. Caveat for whoever uses it: Ebata's own Results mark the PVR and SVR changes **not statistically significant**, which `protocol/evidence.md` omits when proposing PVR +63% as a "clean" benchmark |
| **Farmery & Roe 1996** | Read 2026-09-20, cited nowhere yet. Its `[H+] = 570·FCO2 + 10` gives a titration slope of −0.788/decade against Stock's measured −0.758 and our −0.669, making ours the outlier on a third independent route. Caution: their model sets `dVA/dt = 0`, dropping the term our entire obstructed limb is built on |
| **Venegas 1998** | Held, cited once and only to say it records too few channels. Our recoil curve is bilinear, not the Venegas sigmoid — either an improvement not made or a choice not written down |
| **Wei 2020** | Held, cited once for what it does not supply |

---

## 5. Errors this audit found in documents, not in papers

**Caught by actually reading O'Loughlin, 2026-09-21 — the first error a
newly-obtained paper has exposed.** `editorial.md` said their "own tabulation
shows arterial studies clustering at **0.40-0.45** kPa.min-1". It does not. The
paper's stated range is **0.15-0.45** across all studies, and the arterial and
transcutaneous ones it cites are 0.4 (Frumin), 0.24 (Gustafsson) and 0.30
(Toner) — a spread, not a cluster. The editorial's central CO2 recommendation
leaned on that cluster. Corrected.

Everything else in that paragraph verified word for word: the 18.7 (7.2) min
mean apnoea, the 0.15 (0.10) kPa.min-1 being venous, the explicit statement
that "peripheral venous and end-tidal carbon dioxide measurements
significantly underestimate carbon dioxide accumulation", the BMI>45 and
hypercapnia exclusion criteria, and the conclusion being for "short duration"
surgery in "non-obese patients". Our test configuration is also exact: n=64,
mean (SD) age 47 (16), BMI 25 (4).

**This is the argument for getting the other twelve.** Four claims right, one
wrong, and the wrong one was load-bearing — findable in twenty minutes with
the paper in hand and not findable at all without it.

Fixed on 2026-09-21 in the same pass that created this file:

- `README.md` claimed the suite "were green at the commit in `PROVENANCE.txt`".
  **The suite is red**, 34 of 36, and every package built stamps the commit
  without ever asserting it passed. Corrected, with both failures named.
- `README.md` said the model runs at V/Q spread 0.70. It **delivers 0.644**.
- `README.md`, `HANDOVER.md` and `protocol/evidence.md` all still said the CO2
  red-cell correction was "written from memory", a week after it was verified.
  All three struck.
- `CITATION.cff` — machine-readable, shipped in every package — said **"Twenty
  parallel ventilation/perfusion compartments"**. It is 80.
- `protocol/study.html` read Moreault's "5 cmH2O" as a standard deviation. The
  paper says **SEM**, at n≈10 per group. The implied SD is ~15.8, the 95% CI at
  n=20 is ±7.40 rather than ±2.19, and the sample size for 90% power is
  **n≈108, not 11**. The giveaway was in the arithmetic: 5/√20 = 1.118 is
  exactly the quoted "standard error of 1.12", so the 5 was divided by √n twice.
- `HANDOVER.md` headed a scorecard **"(all currently pass)"** over a table
  containing a failing row and seven pre-compliance-fix values.

Not yet fixed, and each needs a decision rather than an edit — see §6.

---

## 6. Structural issues that no paper closes

1. **Fit graded as validation, at least twice, unflagged.** The tilt gains and
   `hb_co_exp` are each calibrated to a number and then graded against that same
   number by `test_validation.py`, which reports the result as a clinical PASS.
   The repository flags exactly this pattern elsewhere — `handover_numbers.py`
   strikes a Tokics row as "CIRCULAR … not evidence" — and does not flag it
   here. This needs a written ruling under CLAUDE.md, whether or not any paper
   arrives.
2. **The benchmark count overstates the evidence.** `protocol/study.html` tells
   a sponsor the model is "validated against 36 benchmarks". `HANDOVER.md`'s own
   analysis reduces that to **roughly sixteen distinct claims against measured
   data**: five are one assertion counted five times, two pass on a
   never-reached sentinel, and several bands are wide enough to swallow the
   error they exist to catch. The sponsor-facing number should be the honest one.
3. **The MODEL comparators are one lineage.** Every comparator row traces to the
   Nottingham simulator. They are not independent confirmations and
   `HANDOVER.md` says so; Farmery & Roe is the first held source that would
   break that, and it is unused.

---

## Release checklist

Documentary, needing no library:

- [x] `README.md` states the true suite state
- [x] `CITATION.cff` compartment count
- [x] the three stale "written from memory" claims struck
- [x] `protocol/study.html` sample size corrected and marked unsettled
- [x] the FRC regression's missing provenance recorded in the code
- [ ] stamp `CITATION.cff` `version` and `date-released` at release, or delete
      both fields and point to `PROVENANCE.txt`
- [ ] reconcile `airway_scenario.html`'s "parameterised, not fitted to source
      data" against `apnoea_core.py`'s "anchored to the standing predicted-FRC
      regression" — one of them is wrong
- [ ] complete or strike the `"Chest"` citation — §2a names a candidate
      (Kiely 1996, PMID 8625670) which must be **confirmed by reading**, not
      pasted in
- [ ] replace the sponsor-facing "36 benchmarks" with the honest count
- [x] a written ruling on `crs` (§3) — **RULED 2026-09-22, set to Rothen group 1's 75**
- [ ] a written ruling on fit-graded-as-validation (§6.1)
- [ ] `editorial.md` carries no hedge in its own text; the "draft, not peer
      reviewed" label lives only in `README.md`
- [ ] `test_validation.py` names the function `test_toner_2018` while its own
      docstring cites the 2019 paper

Needing the library, cheapest first. **All citations below are now complete
enough to order** — §2a resolved the four that were not. Nothing here can be
obtained from this environment: every publisher domain is egress-blocked, so
these need a machine with library access, or the Google Drive connector
connected and the PDFs placed there.

- [ ] **Byun S-H**, *J Clin Med* 2026;15(13):5078 (the OLV review) — open access,
      PMC13363232. Record the author and title in `protocol/evidence.md`, which
      currently cites it by DOI alone
- [ ] **Kaiser HA, et al.**, *Sci Rep* 2024;14:3617 — open access, PMC10864331.
      **Check the year and the n against what we record** (see §2a)
- [ ] Siggaard-Andersen 1977 — doi 10.3109/00365517709098927
- [ ] Toner 2019, Heard 2017, O'Loughlin 2020 — **record-keeping, not access.**
      The detail already in the repository reads as though someone once had
      these full texts
- [ ] Varat 1972; *Circulation* 1963;28:346 (establish author, and whether it is
      a paper or an abstract); Flin 2013
- [ ] the four positioning trials — Lane 2005, Ramkumar 2011, Altermatt 2005
      and Dixon 2005 are **resolved to full citations in §2a** and can now be
      ordered. The author who fitted the gains should still confirm these are
      the four they used, because a search can identify a plausible paper
      rather than the right one
- [ ] Laviola 2026 main text; Hardman 2000;90:614-8; Hardman & Wills's online
      Appendix 1 — all via the author route recorded in `HANDOVER.md`

---

*Regenerated numbers in this file are checked by `handover_numbers.py`. Prose
claims about which documents are held are checked by nothing, and are dated so
that they can be re-checked.*
