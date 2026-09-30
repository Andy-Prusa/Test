"""The single source of truth for WHICH PAPERS THIS PROJECT HAS READ.

WHY THIS EXISTS, and it is not tidiness. On 2026-09-25 five separate claims
about what had been read were found to be wrong, in four different documents:

  * README.md told a sponsor that Toner 2019, Heard 2017, O'Loughlin 2020 and
    Kaiser 2024 were unread. ALL FOUR HAD BEEN READ, one of them four days
    earlier. Its summary line said "six of these eight have not been read"
    when SIX OF THE EIGHT HAD BEEN.
  * SOURCES.md's wanted list carried Kaiser 2024 as unobtained three days
    after it was read, and had earlier carried Valenza 2007 and Pelosi 1998
    the same way.
  * SOURCES.md asserted that four citations lacked a title or an author when
    every one of them was recorded elsewhere in the same repository.

The cause is structural, not carelessness: THE SAME FACT WAS WRITTEN IN FOUR
PLACES WITH NO LINK BETWEEN THEM, and prose does not fail a test when it
drifts. CLAUDE.md already says it -- "numbers in markdown rot, numbers in
scripts do not" -- and this is that rule applied to a fact that is not a
number.

So: the status lives HERE, once. `check_sources.py` regenerates README.md's
table from it and fails if the file has drifted. To record that a paper has
been read, change it here and run that script; do not edit the table.

`read` is the date it was read at source, or None. Reading means the PAGE was
seen -- not an abstract, not a search result, and not another paper's
description of it. A condensation does NOT count: see Gunnarsson.
"""

# key -> (label for the README table, what it pins, date read or None, note)
BENCHMARK_SOURCES = [
    ("Stock 1989", "PaCO2 rise, obstructed", "2026-09-14", ""),
    ("Moreault 2021", "the pressure limb", "2026-09-14", ""),
    ("Toner 2019", "buccal oxygen, time to desaturation", "2026-09-22",
     "the sham IQR 405-525 and the 'median (interquartile range)' wording "
     "are read from the page"),
    ("Heard 2017", "apnoeic oxygenation, obstructed", "2026-09-22",
     "moved four things; see SOURCES.md"),
    ("O'Loughlin 2020", "desaturation timing", "2026-09-21",
     "read in full; caught a load-bearing error in `editorial.md`"),
    ("Lane / Ramkumar / Altermatt / Dixon", "positioning", None,
     "**ORDERABLE SINCE 2026-09-23, note corrected 2026-09-26.** This row "
     "said they were \"cited by surname and year only, so not retrievable as "
     "written\" -- which SOURCES.md's own resolved-citations table, written "
     "to fix exactly that, had already contradicted. All four now carry a "
     "title and an identifier there; Altermatt is doi 10.1093/bja/aei231 and "
     "is the one blocking `tilt, BMI 35 at 30 deg`. STILL UNREAD: the "
     "citations were resolved by search, not by opening a page"),
    ("Kaiser 2024, *Sci Rep* 14:3617 (n=91)", "cardiac output", "2026-09-22",
     "RE-READ FROM THE PDF 2026-09-29 to answer whether it pins the "
     "anaesthetised cardiac-output level. IT HALF DOES. Table 1: cardiac "
     "output 5.0 l/min (IQR 4.5-6.0) at minute 0 rising to 6.5 (5.7-7.5) at "
     "15; paCO2 43 (38-48) to 73 (67-81); paO2 366 to 254; age 47; and it "
     "DOES report haemoglobin, 139 g/l (IQR 130-146) -- a claim that this "
     "project had recorded the wrong way round, and which happens to vindicate "
     "the hb=14 used in its test configuration. Anaemia was an exclusion "
     "criterion, hence the tight spread. BUT IT REPORTS NO WEIGHT, HEIGHT OR "
     "BMI, so its cardiac output cannot be converted to a cardiac index and it "
     "still does not pin the anaesthetised level against body size. One more "
     "thing worth knowing: its fifteen-minute ceiling is a PROTOCOL "
     "termination rule (SpO2<92, tcpCO2>100, pH<7.1, K>6.0, or 15 min), not a "
     "physiological limit, so it could never have tested the CO2 decay. "
     "ASA I-III, elective, Bern. "
     "note corrected 2026-09-26: the title WAS recorded, in SOURCES.md's "
     "resolved-citations table -- \"Carbon dioxide and cardiac output as "
     "major contributors to cerebral oxygenation during apnoeic "
     "oxygenation\", doi 10.1038/s41598-023-49238-3"),
    ("Varat 1972", "the circulation's response to anaemia", None,
     "a verbatim quotation from it ships in three files"),
    ("Roy 1963, *Circulation* 28:346-356 (n=51)",
     "the cardiac-output rise in severe anaemia", "2026-09-25",
     "the author was recorded NOWHERE until this reading; it is Roy SB, "
     "Bhatia ML, Mathur VS, Virmani S, and it is a full paper, not an "
     "abstract"),
    ("Perilli 2000, *Anesth Analg* 91:1520-5 (n=15)",
     "respiratory compliance in morbid obesity, and the tilt response",
     "2026-09-26",
     "read at source. It was wanted because it might carry the lung volumes "
     "Perilli 2003 does not; IT DOES NOT, and the authors say so: \"a "
     "limitation of our study might be the lack of the direct measure of "
     "FRC\". What it does carry is Ctot MEASURED in a BMI 46.7 cohort, "
     "which `crs` currently models as BMI-independent"),
    ("Berthoud 1991, *Br J Anaesth* 67:464-6 (n=12)",
     "the obesity penalty, lean against obese under one protocol",
     "2026-09-26",
     "**THE BEST OBESITY TEST HELD.** Six morbidly obese against six controls "
     "MATCHED for sex, age and height, one protocol, and the clock runs from "
     "the suxamethonium injection so it means the same thing the model means. "
     "196 (80) s at BMI 49 against 595 (142) s at BMI 23.1"),
    ("Rothen 1993, *Br J Anaesth* 71:788-95 (n=16)",
     "`crs`, and the anaesthetised V/Q dispersion",
     "2026-09-26",
     "**WAS RECORDED AS \"SUMMARY READ\" WITH THE PDF SITTING IN THE "
     "SESSION.** Opened 2026-09-26 and it CONFIRMS the `crs` ruling of "
     "2026-09-22 rather than overturning it: Table II group 1 is 75 (19) "
     "mL/cmH2O at BMI 24.9, exactly as recorded, and group 2 is 60 (15) at "
     "BMI 27.7. Crs is measured ONLY anaesthetised -- the awake column is a "
     "dash -- so the comparison is like-for-like, as apnoea_core.py had "
     "already reasoned from the Methods"),
    ("Watson & Pride 2005, *J Appl Physiol* 98:512-7 (n=23)",
     "the posture cost of FRC, sitting against supine",
     "2026-09-26",
     "**RULED UNAVAILABLE 2026-09-25, OBTAINED AND READ 2026-09-26.** It "
     "settles the model's largest structural claim about position and "
     "reverses it: FRC falls 740 mL supine in the lean (P<0.0001) and only "
     "70 mL in the obese (P = ns). It also dissolves the Jones/Damia "
     "conflict rather than deciding it -- in obesity seated and supine are "
     "nearly the same volume, so both papers were right"),
    ("Altermatt 2005, *Br J Anaesth* 95:706-9 (n=40)",
     "the obese tilt benchmark", "2026-09-26",
     "read at source. THE BENCHMARK IS MISCONFIGURED AGAINST IT: Altermatt "
     "measured 90 degrees (sitting), BMI 43, and tilted only during "
     "PRE-OXYGENATION -- both groups were supine for the apnoea. "
     "test_validation.py tests 30 degrees at BMI 35 throughout the run"),
    ("Gunnarsson 1991, *Br J Anaesth* 66:423-32 (n=45)",
     "anaesthetised shunt and V/Q dispersion, by MIGET",
     "2026-09-26",
     "**THE FULL PAPER, at last.** A Survey of Anesthesiology CONDENSATION "
     "was uploaded 2026-09-25 and correctly refused. n=45 is the "
     "best-powered shunt anchor this repository holds, against Tokics' n=10"),
    # ADDED 2026-09-27, and its absence was the exact failure this file
    # exists to prevent. SOURCES.md section 1b has marked Mohanty "Read."
    # since 2026-09-21; this registry -- the SINGLE SOURCE OF TRUTH for what
    # has been read -- did not list him, and no script mentions him either.
    # A paper can be read, written up, and still invisible to anyone who
    # asks the question the supported way.
    ("Mohanty 2021, *Anesth Essays Res* 15(4):408-412 (n=50)",
     "nothing yet -- the buccal head-to-head that CONTESTS Heard's figure",
     "2026-09-21",
     "obese ASA I-II, BMI >= 30, buccal RAE 375.3 (116.6) s against nasal "
     "cannula 316.1 (94.1), P = 0.054. It is the only independent "
     "measurement of a buccal arm this project holds, and NOTHING IN THE "
     "MODEL IS GRADED AGAINST IT -- see the buccal row in test_validation.py, "
     "which is a one-sided floor the model cannot fail"),
    ("Damia 1988, *Br J Anaesth* 60:574-8 (n=30)",
     "anaesthetised FRC in morbid obesity, and the posture claim",
     "2026-09-26",
     "read at source. It FALSIFIES the model's largest untested claim -- "
     "that lying flat costs a BMI 50 patient 63% of FRC -- by measuring "
     "awake SUPINE FRC at BMI 53.2 as 2250 mL against Jones's SEATED 2125 "
     "mL at BMI 50. It also disagrees with Pelosi 1998 on anaesthetised FRC "
     "by a factor of two at the same BMI, same method, same conditions"),
    ("Fraioli 1973, *Anesthesiology* 39(6):588-96 (n=31)",
     "apnoeic-oxygenation PaO2 and the FRC/weight desaturation split",
     "2026-09-28",
     "read in full from upload 2026-09-28; NOT previously held -- it was "
     "listed as an UNREAD ICSM/Laviola validation ref in SOURCES.md. Human "
     "100% O2 apnoeic oxygenation: start PaO2 445-485 torr; Group I "
     "(FRC/weight 53.7 mL/kg) holds ~70% of control at 15 min, Group II "
     "(36.7 mL/kg, heavier 82.5 vs 71.3 kg, final FRC 839 vs 1907 mL) falls "
     "to 91 torr at 15 min; PaCO2 24.5->73.2 torr over 15 min, "
     "GROUP-INDEPENDENT; N2 accumulation 169.5 vs 277.5 mL; VO2 ~350 awake, "
     "285 mL/min apnoeic. Mechanism: PaO2 fall = rising PaCO2 + (mainly) "
     "rising alveolar N2. Agrees with Heller 1963. NO cardiac output, no Hb"),
    ("Benumof, Dagg & Benumof 1997, *Anesthesiology* 87:979-82",
     "time-to-desaturation COMPARATOR (a MODEL, not a measurement)",
     "2026-09-28",
     "read from upload 2026-09-28. MODEL output of Farmery & Roe 1996, "
     "sealed airway (VE=0, no apnoeic oxygenation), initial FAO2 = 0.87 "
     "(= the model's feo2_start default). Fig 1: SaO2 80% reached at 8.7 "
     "(healthy 70kg) / 5.5 (ill) / 3.7 (10kg child) / 3.1 (obese 127kg) min. "
     "Table 1 gives SECONDHAND measured times (primaries Xue/Patel/Teller/"
     "Gambee/Drummond/Bhatia/Jense NOT held -- their numbers may not be "
     "used as bands); its own model OVERpredicts the measured times in 7/11"),
    ("Baraka/Salem/Joseph & Benumof 1999, *Anesthesiology* 90:332-3",
     "nothing -- correspondence, qualitative",
     "2026-09-28",
     "read in full 2026-09-28. Letter + reply, no data of its own; argues "
     "apnoeic diffusion oxygenation delays desaturation. Cites Benumof 1997 "
     "and Teller 1988 (69:980-2), NEITHER HELD"),
    ("Kiely DG, Cargill RI & Lipworth BJ, *Chest* 1996;109(5):1215-21 (n=8)",
     "the source of the `stroke volume rises with hypercapnia` benchmark, and "
     "a HUMAN number for the PVR response the model has no term for",
     None,
     "ABSTRACT VERIFIED 2026-09-30 from the citation record; FULL TEXT NOT "
     "HELD, so this is deliberately NOT marked read. 'Effects of hypercapnia "
     "on hemodynamic, inotropic, lusitropic, and electrophysiologic indices "
     "in humans', Ninewells Hospital, Dundee. Eight healthy male volunteers, "
     "AWAKE, Doppler echo, end-tidal CO2 raised to 7 kPa (52.5 mmHg, +12.5 "
     "over 40) for 30 min on a CO2/air mixture. "
     "WHAT IT SETTLES: it IS the benchmark's source -- 'Heart rate, stroke "
     "volume, cardiac output, and mean arterial BP were increased by "
     "hypercapnia' is the note verbatim. And its CO2 load is SIX TIMES "
     "SMALLER than Stengl's +76.8, so the two do not conflict; the model "
     "operates at +10 to +30, which is KIELY'S range, so the existing "
     "POSITIVE sv_co2_gain is probably right where it is used. "
     "WHAT IT DOES NOT SETTLE: the abstract gives NO MAGNITUDES for HR, SV, "
     "CO or MAP -- only that they rose. THE BENCHMARK'S +5 TO +30% BAND IS "
     "UNSOURCED AND NOW PERMANENTLY SO: the full text could not be "
     "obtained (2026-09-30, author's own attempt), so THE SEARCH IS "
     "CLOSED, NOT PENDING. Do not re-open it expecting the tables. The "
     "row keeps its band because the SIGN is sourced and checked; the "
     "limits are inherited and must never be quoted as measured. "
     "Backing cardiac output out of the reported MPAP and PVR via "
     "PVR = 80(MPAP - PCWP)/CO WAS TRIED AND REJECTED: Kiely did not "
     "measure wedge pressure, and the implied ratio swings from x1.17 to "
     "x2.01 across plausible values. That is reasoning from what a paper "
     "does not say, which this project's rules record as wrong every time. "
     "THE NUMBERS IT DOES GIVE ARE THE PULMONARY ONES, and they are the "
     "useful part: MPAP 9+-1 -> 14+-1 mmHg (x1.56) and PVR 129+-17 -> 171+-17 "
     "dyne.s.cm-5 (x1.33), IN AWAKE HUMANS AT THE MODEL'S OWN CO2 RANGE. "
     "Against Stengl's pig x1.37 at +76.8 that is 5.4x steeper per mmHg, so "
     "the PVR response SATURATES and a linear CO2 gain would be the wrong "
     "form. "
     "Systolic function was UNAFFECTED (peak aortic velocity, aortic mean and "
     "peak acceleration), as were lusitropic indices, so stroke volume rose "
     "by loading and not by contractility -- consistent with Stengl finding "
     "depression only on acute acidic perfusion in vitro. No effect on renin, "
     "angiotensin II or aldosterone, which rules out a RAAS mechanism over 30 "
     "min. "
     "IT CONTRADICTS STENGL ON QT, and the disagreement is recorded rather "
     "than reconciled: Kiely found QTc LENGTHENED 411+-3 -> 428+-8 ms with QT "
     "dispersion 33+-4 -> 48+-2, where Stengl found QT and QTc SHORTENED in "
     "both acidoses. Kiely saw no arrhythmia but flags dispersion as a "
     "substrate; Stengl saw none; Frumin 1959 saw ventricular ectopics that "
     "ended two apnoeas"),
    ("O'Croinin et al. 2024, *Physiol Rep* 12:e16054 (HUMAN, n=26)",
     "whether the heart-rate response to APNOEA is driven by CO2 or by "
     "hypoxia -- the human counterpart to Stengl",
     "2026-09-30",
     "READ AT SOURCE from upload, open access. 26 healthy AWAKE volunteers "
     "(12 female, 23 yr, BMI 24) doing voluntary breath-holds under "
     "hypercapnia (+5 torr PETCO2), hypoxia (PETO2 50 torr) and both. "
     "HEADLINE: 'Under apneic conditions, the cardiac response is driven by "
     "HYPOXIA.' Hypercapnic apnoeas were NOT different from normocapnic "
     "(-14 +- 14 vs -11 +- 15 bpm, p=0.134); hypoxia deepened the "
     "bradycardia (-19 +- 15). This SUPPORTS keying the model's bradycardia "
     "on SaO2, which it does. "
     "IT DOES NOT SETTLE THE CO2->HR GAIN, and must not be cited as if it "
     "did. Its CO2 challenge was +5 torr against the 40-80 mmHg the model "
     "works over; at +5 the current law predicts +1.6 bpm and the "
     "Stengl-derived probe +4.6, both inside a +-14 bpm SD, so the study "
     "cannot discriminate them. "
     "AND IT IS AWAKE. The diving response that produces this bradycardia "
     "needs an intact reflex; the model's population is anaesthetised and "
     "PARALYSED. That is the identical trap already recorded at the Altermatt "
     "tilt row in test_validation.py, where an AWAKE measurement was found to "
     "constrain an anaesthetised parameter nowhere"),
    ("Stengl et al. 2013, *Crit Care* 17:R303 (PIGS, n=8+8+8)",
     "whether the cardiovascular response to acidosis is driven by pH or by "
     "CO2 -- the one design that separates them",
     "2026-09-30",
     "READ AT SOURCE from upload, open access. Anaesthetised, ventilated, "
     "PARALYSED pigs; hypercapnic acidosis (inspired CO2, PaCO2 5.04 -> 15.57 "
     "kPa = 38 -> 117 mmHg) and metabolic acidosis (2 M HCl infusion, PaCO2 "
     "held constant) BOTH TITRATED TO pH 7.10. SPECIES IS THE CAVEAT, not the "
     "state: the preparation matches this model's population. "
     "IT VINDICATES KEYING THE SYSTEMIC TERMS ON CO2 AND NOT ON pH. SVR fell "
     "with hypercapnia (x0.76) and did NOT change with metabolic acidosis at "
     "the same pH (x1.16, ns), so systemic vasodilatation is a CO2 effect. "
     "IT ALSO SHOWS sv_co2_gain HAS THE WRONG SIGN: stroke volume FELL, x0.73 "
     "hypercapnic and x0.66 metabolic, while the model raises it x1.35. "
     "Cardiac output was held up by tachycardia (HR x2.02) instead. The "
     "model's net CO x1.81 against a measured x1.62 is about right BY TWO "
     "ERRORS CANCELLING. "
     "AND PVR IS WHERE A REAL pH TERM IS NEEDED: metabolic acidosis raised "
     "PVR x2.21 at CONSTANT PaCO2, more than hypercapnia did (x1.37). This "
     "model's PVR moves only with hypoxic vasoconstriction and has no "
     "acidosis term at all. "
     "It refines the co2_response_cap comment too: at pH 7.10 in vivo NO "
     "ARRHYTHMIA occurred in either group and trabeculae from the acidotic "
     "animals had NORMAL contraction force -- only acute acidic perfusion in "
     "vitro depressed force. The depressant limb is real in the dish and was "
     "compensated in the animal at this pH. NOTHING WAS CHANGED on the "
     "strength of it; see the seventeenth HANDOVER entry"),
    ("Frumin, Epstein & Cohen 1959, *Anesthesiology* 20(6):789-798 (n=8)",
     "the LONG-WINDOW CO2 rate, and the acid-base trajectory past 15 min",
     "2026-09-29",
     "READ IN FULL from upload. Pages 790-798 had been sought since "
     "2026-09-21 and were unheld; the project cited this paper secondhand "
     "through O'Loughlin and forbade its three headline numbers. ALL THREE "
     "ARE NOW VERIFIED FROM TABLE 1: pH 6.72, PaCO2 250 mmHg and 53 minutes "
     "are subject 7, and lowest arterial saturation is 98-100% in all eight. "
     "Two caveats the secondhand citation never carried: that 250 is "
     "ESTIMATED, not measured, and that subject 7 BEGAN with a moderate "
     "respiratory acidosis. "
     "WHAT IT ACTUALLY SETTLES IS THE DECAY. Apnoeas of 18-55 min with the "
     "airway patent on an oxygen reservoir; the paper's own statement is an "
     "average rate of rise of PaCO2 of approximately 3 mmHg/min, RANGE "
     "2.7-4.9 (per-subject 3.0, 4.9, 3.0, 3.5, 2.7). O'Loughlin's secondhand "
     "0.4 kPa/min is vindicated. This is the FIRST held measurement past 15 "
     "minutes, which the eleventh HANDOVER entry named as the hole, and THE "
     "MODEL FAILS IT: 1.55 mmHg/min over 0-53 min against ~3, PaCO2 122 at "
     "53 min against 250, and pH 7.09 at 40 min against Table 2's 6.87 in "
     "subject 6, whose control pH of 7.36 matches the model's 7.40. Table 2 "
     "is a pH time-series at 10-minute intervals and is a second, "
     "independent long-window test. "
     "HOW THE GASES WERE MEASURED, which changes how this benchmark must "
     "be read (p.790): plasma CO2 CONTENT by Kopp-Natelson microgasometer "
     "and pH potentiometrically by glass electrode, and then 'the "
     "arterial carbon dioxide tension and the buffer base were ESTIMATED "
     "from the nomogram of Singer and Hastings, or from the "
     "Henderson-Hasselbalch equation for the higher carbon dioxide "
     "tension values.' SO NO PaCO2 IN THIS PAPER WAS MEASURED. Every "
     "comparison against it until 2026-09-29 compared a modern electrode "
     "reading to a 1959 derived quantity. Against what he DID measure the "
     "model agrees: plasma CO2 content to 0-7%, mean 1.00x, while its "
     "PaCO2 is 1.75x low. See the thirteenth HANDOVER entry -- the CO2 "
     "store is vindicated and the open question is the pH/PCO2 relation "
     "above PaCO2 ~100, where his estimate is an extrapolation off the "
     "end of a 1959 nomogram and the model has never been tested"),
    ("Stelfox 2006, *Crit Care Med* 34(4):1243-1246 (n=700)",
     "cardiac output against BMI -- the INDEPENDENT test of the BSA law",
     "2026-09-29",
     "read at source from upload. 700 consecutive adults with disease-free "
     "coronary arteries, cardiac output by THERMODILUTION OR FICK during "
     "coronary angiography, BMI mean 28 and range 10.6-91.6 -- far larger and "
     "far wider than Madronio, and invasive rather than imaged. Each 1 kg/m2 "
     "of BMI adds 0.08 L/min (95% CI 0.06-0.10) of cardiac output and 1.35 mL "
     "of stroke volume; CARDIAC INDEX HAS NO ASSOCIATION WITH BMI (0.003 "
     "L/min/m2, 95% CI -0.008 to 0.014, p = .571), and the cardiac-index "
     "difference between below-normal and obese class 3 is 0.3 L/min/m2. "
     "NOTHING IN THE MODEL WAS SET FROM IT: the re-keyed law gives 0.089 "
     "L/min per kg/m2 across Stelfox's own six category means, inside his "
     "confidence interval, and a cardiac-index spread of 0.25 against his "
     "0.3. CAVEAT, and it corrects an expectation recorded before reading: "
     "this is an AWAKE catheterisation cohort, NOT anaesthetised, so it does "
     "NOT bear on co_drop_frac. No haemoglobin reported"),
    ("Madronio 2025, *Heart Lung Circ* 34:1109-1118 (n=57)",
     "cardiac output against body size -- the BSA scaling law",
     "2026-09-28",
     "read at source from upload. Cardiac MRI, AWAKE. 57 participants "
     "(79% FEMALE, mean age 41): healthy n=20, BSA 1.84 (0.17), CO 5.71 "
     "(1.08) L/min; BMI>=30 n=37, BSA 2.45 (0.26), CO 7.69 (1.36). "
     "CARDIAC INDEX IS FLAT -- 3.103 vs 3.139 L/min/m2, 1.1% apart -- so CO "
     "is PROPORTIONAL TO BSA (exponent 1.04), i.e. weight^0.51, NOT the "
     "weight^0.75 this model uses. BSA explains ~50% of CO variance; stroke "
     "volume is the driver, heart rate negligible. IT WITHDRAWS THE 'WRONG "
     "GRADIENT' CLAIM: cardiac output RISES with body size, so the "
     "Tokics->Perilli fall was the confound, not a real reversal. Caveats: "
     "AWAKE, so it pins the SHAPE and the awake level, not co_drop_frac; "
     "79% female against an explicitly male model (the authors flag "
     "generalisability); no haemoglobin reported"),
    ("Babinski, Smith & Bunegin 1986, *Anesthesiology* 65:399-404",
     "nothing -- dog continuous-flow apnoeic ventilation study",
     None,
     "abstract and methods reviewed from upload 2026-09-28; FULL TEXT NOT "
     "READ (an abstract does not count as read -- see the file header). 12 "
     "dogs, CFAV open vs closed chest; no human cardiac output or "
     "desaturation data, set aside as a non-benchmark source"),
]


def unread():
    return [s for s in BENCHMARK_SOURCES if s[2] is None]


def read():
    return [s for s in BENCHMARK_SOURCES if s[2] is not None]


def render_table():
    """The README table, generated. Kept between the markers in README.md."""
    out = ["| source | what it pins | read from the page? |",
           "|---|---|---|"]
    for label, pins, date, note in BENCHMARK_SOURCES:
        if date:
            cell = f"**yes**, {date}"
        else:
            cell = "**no**"
        if note:
            cell += f" — {note}"
        out.append(f"| {label} | {pins} | {cell} |")
    n_read, n_all = len(read()), len(BENCHMARK_SOURCES)
    out.append("")
    out.append(f"**{n_read} of these {n_all} have been read at source.** "
               f"The remaining {n_all - n_read} had their band edges entered "
               "from memory or from abstracts. That does not make them wrong, "
               "but it does mean those bands are claims about the literature "
               "that nobody here has checked.")
    return "\n".join(out)
