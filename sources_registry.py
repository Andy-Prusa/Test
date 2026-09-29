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
