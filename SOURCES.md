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
| **Farmery AD, Roe PG.** A model to describe the rate of oxyhaemoglobin desaturation during apnoea. *Br J Anaesth* 1996;76:284-291 | nothing yet — see §4 | read in full 2026-09-20 |

---

## 2. Not held, and something rests on it

Ordered by what breaks. Every identifier below is one the repository already
records; **where none is recorded the entry says so rather than guessing one**,
because a search tool once confabulated an attribution for this project and that
is recorded in `HANDOVER.md` as the oldest failure mode here.

| source | what rests on it | why it matters |
|---|---|---|
| **"Sci Rep 2023", PMCID PMC10864331, n=91.** No author, title, volume or DOI recorded anywhere | `co_co2_gain` and `sv_co2_gain` = 0.0045 (`apnoea_core.py`), three bands in `test_validation.py`, a `README.md` row | **Circular.** The coefficient is fitted to a reported +30% and then graded against that same +30%. Calibration presented as validation. Open access — the cheapest item on this list |
| **Toner AJ, et al.** *Anesth Analg* 2019;128:1154-9 | two bands, the lean patient configuration in `buccal_numbers.py`, one CO2-store anchor, a `README.md` row, `editorial.md` ref [1] | The model gives **403.4 s against a published IQR floor of 405**; it passes only because the band was widened to 380. The sham-arm pharyngeal fraction is a model *input*, not a measurement, and moving it 0.21→0.30 takes the model across most of the published IQR |
| **Heard A, et al.** *Anesth Analg* 2017;124:1162-7 | a band that **is** the published IQR (244-314 s), and the obese configuration behind every obese number in `buccal_numbers.py` and `editorial.md` | A transcription error moves both band edges at once. Mohanty 2021 contests the buccal figure by about 2× (`HANDOVER.md`) |
| **The four positioning trials: Lane 2005, Ramkumar 2011, Altermatt 2005, Dixon 2005.** Surnames and years only | `tilt_gain_lean` and `tilt_gain_bmi`, stated in `apnoea_core.py` as "calibrated against four randomised trials", then graded by three bands set from those same four | **Not retrievable as cited, by anyone, including us.** Also a fit graded by its own calibration target (§6). The limb is not confined to the positioning test: the obese buccal configuration runs `tilt_deg=25` |
| **O'Loughlin CJ, et al.** *Anaesthesia* 2020;75:1070-5 | four bands, and **five unhedged quantitative claims in `editorial.md`** carrying the editorial's central CO2 recommendation | The editorial claims are checkable against nothing held |
| **The one-lung-ventilation narrative review**, doi 10.3390/jcm15135078. No author or title recorded | `protocol/evidence.md` calls it "obtained and read" and draws an **absence** claim from it | Reasoning from what a document does not contain is the move CLAUDE.md forbids outright. Open access |
| ***Circulation* 1963;28:346**, "Hemodynamic Effects of Chronic Severe Anemia". **No author recorded** | `hb_co_exp` = 1.535, derived from it; a band in `test_validation.py` | The band grades the fit against the number the fit was made from. Whether it is a paper or a meeting abstract is **unknown**, and that changes whether the "CLINICAL" label is honest |
| **Varat MA, Adolph RJ, Fowler NO.** *Am Heart J* 1972;83:415-26 | `hb_co_threshold` = 7.0 | A **verbatim quotation in quotation marks** ships in three files from a paper nobody here has read |
| **Laviola 2026, main text** (SDC held) | a band sourced "~510 s", plus the scorecard row and the claim that "two independently built models agree" | **The 510 s is in no document held.** The SDC gives the state at SaO2 40%, explicitly not the time to it. The SDC itself names no journal, volume or DOI — the citation in `test_validation.py` is the repository speaking, not the document |
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

## 3. Values with no source at all

These carry specific non-round values and no citation. A precise number with no
provenance is more dangerous than an obviously rough one, because it reads as
measured.

| value | where | note |
|---|---|---|
| `FRC(L) = 2.34·height + 0.009·age − 1.09` | `apnoea_core.py`, `model.js`, `airway_scenario.html` | **The largest uncited lever in the model.** No author, journal or year anywhere. A ±12% error in `frc_ref` takes a headline clinical benchmark out of band; ±30% in `k_frc_bmi` takes the obese one out in both directions. The quoted age term is **not implemented**. Measured and recorded in the code comment, and regenerated by `handover_numbers.py` |
| `crs` = 85.0 mL/cmH2O | `apnoea_core.py` | Uncited, and **above** the 60-75 range the same file cites Rothen for when arguing the previous value was too stiff. It is also a live lever on the failing benchmark: 85→60 moves the Stock slope 4.72→4.37, which would PASS. That makes moving it a CLAUDE.md §"do not tune" question needing a written ruling, not a quiet edit |
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
- [ ] complete or strike the `"Chest"` citation
- [ ] replace the sponsor-facing "36 benchmarks" with the honest count
- [ ] a written ruling on fit-graded-as-validation (§6.1) and on `crs` (§3)
- [ ] `editorial.md` carries no hedge in its own text; the "draft, not peer
      reviewed" label lives only in `README.md`
- [ ] `test_validation.py` names the function `test_toner_2018` while its own
      docstring cites the 2019 paper

Needing the library, cheapest first:

- [ ] the OLV review — open access, doi 10.3390/jcm15135078
- [ ] "Sci Rep 2023" — open access, PMCID PMC10864331. Record author and title
- [ ] Siggaard-Andersen 1977 — doi 10.3109/00365517709098927
- [ ] Toner 2019, Heard 2017, O'Loughlin 2020 — **record-keeping, not access.**
      The detail already in the repository reads as though someone once had
      these full texts
- [ ] Varat 1972; *Circulation* 1963;28:346 (establish author, and whether it is
      a paper or an abstract); Flin 2013
- [ ] the four positioning trials — **the author who fitted the gains must
      supply full references from their own notes.** Do not reconstruct them
      from a search summary
- [ ] Laviola 2026 main text; Hardman 2000;90:614-8; Hardman & Wills's online
      Appendix 1 — all via the author route recorded in `HANDOVER.md`

---

*Regenerated numbers in this file are checked by `handover_numbers.py`. Prose
claims about which documents are held are checked by nothing, and are dated so
that they can be re-checked.*
