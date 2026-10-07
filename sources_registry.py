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
    ("Lane S et al. 2005, *Anaesthesia* 60(11):1064-7 (n=35 analysed)",
     "the `tilt, non-obese 20 deg` benchmark -- the ONLY clean lean anchor",
     "2026-10-02",
     "READ IN FULL from upload. 20 deg head-up vs supine, 3 min "
     "preoxygenation, 40 females for cholecystectomy, BMI 26.3 (4.7) vs 27.9 "
     "(4.9), age 51.8/56.3, Hb 13.7/13.5. Apnoea to SpO2 95%: 386 (343-429) s "
     "head-up vs 283 (243-322) supine, P = 0.002, i.e. +36.4%. THE TILT WAS "
     "MAINTAINED -- 20 deg was chosen because it allows 'airway manoeuvres "
     "and intubation WITHOUT NEEDING AN ALTERATION IN POSITION', in explicit "
     "contrast to the 45 deg study he cites. That is the question Altermatt "
     "failed and Ramkumar also fails, and it makes Lane the only clean lean "
     "anchor for tilt_factor(). NOTE ALSO: FE'O2 at the end of preoxygenation "
     "was 0.89 (0.03) head-up against 0.90 (0.03) supine -- IDENTICAL -- so "
     "his benefit cannot be better denitrogenation and must be lung volume. "
     "TWO CAVEATS: he timed from ROCURONIUM, not apnoea onset, so a fixed "
     "offset inside both arms COMPRESSES the ratio and his true gain is "
     "LARGER than +36.4%; and the apnoea ran with the trachea OPEN TO AIR"),
    ("Ramkumar V, Umesh G, Philip FA 2011, *J Anesth* 25(2):189-94 (n=45)",
     "NOTHING -- struck from the lean tilt row on reading",
     "2026-10-02",
     "READ IN FULL from upload, AND IT DISQUALIFIES ITSELF for this model's "
     "tilt parameter. Three groups of 15: conventional, 20 deg head-up, and 5 "
     "cmH2O PEEP. Non-hypoxic apnoea 452 (71) s head-up vs 364 (83) "
     "conventional, P = 0.030 (+24.2%); PEEP 413 (86), not significant. BUT "
     "THE TILT WAS NOT MAINTAINED: 'Immediately following intubation, the "
     "patients in the head-up group were RETURNED TO SUPINE POSITION', and "
     "all groups were 'left apneic in SUPINE position with the tracheal tube "
     "exposed to atmosphere'. The tilt existed during PREOXYGENATION ONLY, "
     "which is the Altermatt failure exactly. tilt_factor() acts on the lung "
     "DURING apnoea, so this measures denitrogenation and not store. It had "
     "been cited in test_validation.py as a co-anchor with Lane since the row "
     "was written; the two are not the same experiment. Threshold SpO2 93%, 5 "
     "min preoxygenation, thiopentone and suxamethonium"),
    ("Couture EJ et al. 2023, *BMC Anesthesiol* 23:198 (n=48 analysed)",
     "nothing yet -- position and pressure support are CONFOUNDED",
     "2026-10-02",
     "READ IN FULL from upload. Morbidly obese, BMI 47.9 (6.3) vs 47.3 (5.2), "
     "well matched unlike Dixon. Safe non-hypoxic apnoea to SpO2 92%: 258.2 "
     "(55.1) vs 216.7 (42.3) s, P = 0.005. CANNOT ANCHOR THE TILT PARAMETER, "
     "and the reason is sharper than this entry first recorded. "
     "CORRECTION 2026-10-02, the same day: it first said \'NO TILT ANGLE IS "
     "STATED anywhere in the paper\'. THAT IS FALSE. A grep missed it because "
     "the PDF is two-column and the phrase split across lines, and the absence "
     "was then asserted as fact -- which is the move CLAUDE.md names as having "
     "been wrong every time it was tried. THE ANGLE IS STATED THREE TIMES, AND "
     "BOTH ARMS ARE TILTED TO 25 DEGREES: group 1 in a \'25 deg beach-chair "
     "position (upper body portion was tilted upward at a 25 deg angle)\', "
     "group 2 in a \'25 deg reverse Trendelenburg position (the entire "
     "operating table tilted 25 deg)\', and \'table angles were measured at the "
     "hip hinge with a digital angle level\'. SO THERE IS NO UNTILTED ARM -- "
     "nothing in this trial measures tilt against flat, which is why it cannot "
     "anchor tilt_factor(). What it DOES isolate is two things, and they are "
     "CONFOUNDED with each other: (a) HOW a 25 deg tilt is achieved, torso "
     "hinged against whole table tilted -- a distinction THIS MODEL CANNOT "
     "EXPRESS, carrying one tilt_deg and no notion of how the patient got "
     "there; and (b) pressure support 8 cmH2O with PEEP 10 against spontaneous "
     "breathing. The paper notes its beach-chair position \'is similar to the "
     "ramp position\'. ITS VALUE IS ITS REFERENCE LIST: it cites "
     "Couture EJ et al., Can J Anaesth 2018;65(5):522-8, the same group "
     "measuring FRC across six position/ventilation combinations in the same "
     "population -- the volume-and-time pair this project has never held. "
     "Also Boyce JR et al., Obes Surg 2003;13(1):4-9"),
    ("McKechnie A et al. 2025, *Anaesthesia* 80:1103-14 (SOBA guideline)",
     "context only -- no measurement",
     "2026-10-02",
     "READ IN FULL from upload. Best-practice recommendations from the "
     "Society for Obesity and Bariatric Anaesthesia, endorsed by the All "
     "Wales Airway Group, Scottish Airway Group and Difficult Airway Society. "
     "Recommends pre-oxygenation in a ramped, >= 30 degree head-up position "
     "(Grade A, strong). A GUIDELINE, NOT DATA: it contributes no measurement "
     "and must not be used to anchor anything. Held for its reference list "
     "and as evidence of current practice"),
    ("Pelosi P et al. 1998, *Anesth Analg* 87(3):654-60 (n=24, BMI 20-66)",
     "anaesthetised FRC against BMI, and `shunt_cc_k`",
     "2026-09-24",
     "READ IN FULL FROM THE PAGE. 'The effects of body mass on lung volumes, "
     "respiratory mechanics, and gas exchange during general anesthesia.' "
     "ADDED TO THIS REGISTRY ONLY ON 2026-10-01, and the gap is the point: it "
     "had been read, cited and quoted in SOURCES.md since 2026-09-24 and was "
     "load-bearing in THREE places -- the shape frc_anaes() carries, the fitted "
     "constant in the shunt law, and the inversion handover_numbers.py runs -- "
     "while having no row here at all. check_sources.py --check PASSED "
     "throughout, because it verifies README against this file and this file "
     "had nothing to verify. A source can therefore be absent from the one "
     "place CLAUDE.md says the read-fact is written WITHOUT any check noticing. "
     "n=24 in three groups of eight, BMI 21.9 (0.5), 33.6 (2.8), 48.2 (8), age "
     "40-75, 1 man / 7 women per group, height ~1.64 m. Propofol, "
     "suxamethonium, pancuronium, VT 10 mL/kg IBW, FiO2 0.40, ZEEP, supine, 15 "
     "min stabilisation, before surgical intervention, FRC by closed-circuit "
     "helium dilution. THE ONLY SOURCE HELD HERE THAT MEASURES ACROSS THE WHOLE "
     "BMI RANGE CONTINUOUSLY rather than at one cohort mean, and the only one "
     "that publishes REGRESSIONS: FRC = 11.97*exp(-0.096*BMI) + 0.46 L (r "
     "0.86); PaO2/PAO2 = 1.23*exp(-0.037*BMI) + 0.196 (r 0.81); D(A-a)O2 = "
     "-7.15 + 3.37*BMI mmHg (r 0.84); PaCO2 NOT related to BMI (r 0.06), about "
     "33. CAVEATS CARRIED: 1 man to 7 women per group against an explicitly "
     "male model, age 40-75, and FiO2 0.40 where Reinius, Valenza and Perilli "
     "differ. WHAT IT COST ON 2026-10-01: re-inverting his oxygenation "
     "regression showed shunt_cc_k had drifted 8.29 percentage points from him "
     "at BMI 55, because both of its drivers were rewritten on 2026-09-25/26 "
     "and it was never re-fitted. Re-fitted 36.16 -> 16.36; rms 4.145 -> 0.861 "
     "pp. See HANDOVER, twenty-ninth entry"),
    ("O'Loughlin 2020", "desaturation timing", "2026-09-21",
     "read in full; caught a load-bearing error in `editorial.md`"),
    ("Dixon BJ et al. 2005, *Anesthesiology* 102:1110-5 (n=42, BMI>40)",
     "the `tilt, BMI 44 at 25 deg` benchmark -- READ AT SOURCE at last",
     "2026-10-01",
     "READ IN FULL from upload. 'Preoxygenation Is More Effective in the 25 "
     "Degree Head-up Position Than in the Supine Position in Severely Obese "
     "Patients: A Randomized Controlled Study.' 42 consecutive severely obese "
     "patients for laparoscopic gastric banding, randomised supine or 25 "
     "degrees head-up, 3 min preoxygenation, ventilation delayed until SpO2 "
     "92%. "
     "THE BENCHMARK CITED '+32%' AND THAT NUMBER IS NOT IN THE PAPER -- the "
     "only '32' in the text are reference page numbers. Measured: time to "
     "SpO2 92% 201+-55 s head-up against 155+-69 supine, which is +29.7%. "
     "Preinduction PaO2 442+-104 against 360+-99 mmHg, +22.8%, and the "
     "abstract's own headline figure is '23% higher oxygen tensions'. "
     "Correlation between induction PaO2 and time to 92%: r=0.51, P<0.001. "
     "THE GROUPS WERE NOT BMI-MATCHED: supine 47.3, head-up 44.9 (P=0.18). "
     "The benchmark compares ONE patient against itself, which does not "
     "replicate the trial. Replicating it properly -- supine at 47.3, head-up "
     "at 44.9 -- makes the model WORSE, not better. "
     "WHAT THE MODEL DOES, computed 2026-10-01. Absolute supine time is very "
     "good: 158 s against a measured 155. But the tilt gain is +50.6% "
     "replicating Dixon's own groups (+42.3% at a single BMI) against a "
     "measured +29.7%. AND THE CHANNEL IS WRONG: Dixon's benefit is largely "
     "BETTER PREOXYGENATION, PaO2 +22.8%, where the model gives only +8.4% "
     "and reaches its supine time with a patient preoxygenated far too well "
     "(488 mmHg against a measured 360). So the twenty-fourth entry's "
     "denitrogenation mechanism is CONFIRMED IN HUMANS and the model has it "
     "about THREE TIMES TOO WEAK, while its lung-volume channel runs too "
     "strong"),
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
    ("Valenza et al. 2007 (n=20, ANAESTHETISED and PARALYSED, BMI 42)",
     "the ONLY held anaesthetised FRC-against-tilt measurement -- the sole "
     "anchor under tilt_factor()",
     "2026-09-30",
     "REGISTERED 2026-09-30, late: it was load-bearing for months without "
     "appearing here at all, which is exactly what this file exists to "
     "prevent. Its numbers are quoted in detail in apnoea_core.py and in "
     "test_validation.py and have been used throughout. End-expiratory lung "
     "volume by CLOSED-CIRCUIT HELIUM DILUTION, supine against 30 degrees, in "
     "20 anaesthetised paralysed patients at BMI 42: 0.46 (0.1) -> 0.85 (0.3) "
     "litres, P < 0.001, i.e. tilt_factor 1.848. "
     "WHY IT CANNOT BE ADOPTED ALONE, per the parameter block: it is ONE "
     "POINT and tilt_factor has TWO parameters. Solving tilt_gain_lean on it "
     "while holding tilt_gain_bmi gives 0.0257, double the shipped 0.0130, "
     "which puts the lean 20-degree row near +54% against a measured +24-36%. "
     "So tilt_gain_lean and tilt_gain_bmi stand UNCHANGED AND UNSOURCED, and "
     "must not be described as fitted to anything. "
     "THE MODEL FAILS IT: tilt_factor 1.466 against a band of 1.70-2.00. That "
     "is one of the four blocking rows, and the pure-algebra one -- no "
     "simulation, no cardiac output, so nothing downstream can explain it"),
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
     "end of a 1959 nomogram and the model has never been tested. "
     "RE-READ 2026-10-06 FOR THE ARRHYTHMIAS AND THE POTASSIUM, which the "
     "2026-09-29 reading took the CO2 from and left. THE ECTOPY DOES NOT "
     "TRACK pH, and that is the finding: of the two subjects who threw "
     "ventricular extrasystoles, one did so WITHIN 7 MINUTES of the onset "
     "of apnoea (subject 5, terminated at ~18 min, lowest pH 6.97, PaCO2 "
     "130) and the other at the LAST MINUTE of 53 (subject 7, pH 6.72, "
     "PaCO2 250) -- opposite ends of the range -- while the remaining six "
     "had no irregularity at all, one of them through 55 minutes with "
     "'virtually no change in the shape of the complex from control' "
     "(p.791). No pH in this series is therefore an arrhythmia threshold. "
     "THE VENTRICULAR TACHYCARDIA WAS A REOXYGENATION EVENT, NOT AN APNOEA "
     "ONE, and the secondhand reading of this paper loses that: p.791, "
     "after a few premature contractions at 53 min the apnoea was stopped, "
     "and 'the institution of artificial respiration with oxygen was "
     "accompanied WITHIN 15 SECONDS by ventricular tachycardia, lasting "
     "less than one minute. The rhythm became normal spontaneously.' All "
     "eight subjects recovered, so what this paper establishes is a "
     "SURVIVED FLOOR of pH 6.72, not a lethal one. "
     "POTASSIUM IS RULED OUT BY THE AUTHORS THEMSELVES and this is the "
     "answer to whether acute hypercapnia reaches an arrhythmogenic K+: "
     "p.792, the maximum rise from control during apnoea was 0.4 mEq/l "
     "with a further 0.6 or less immediately after; Table 2 (subject 6) "
     "runs 3.8 control, 4.0 at 10 min, 4.0 at 30, 4.3 at 40 (pH 6.87), 4.8 "
     "post-apnoea. p.794: 'The potassium changes in subject 7 in whom the "
     "ventricular tachycardia was demonstrated were SIMILAR to those in "
     "subjects 6 and 8 who had normal rhythms when respirations were "
     "resumed.' So respiratory acidosis does not produce an arrhythmogenic "
     "potassium in this territory, not even at pH 6.72 -- the hyperkalaemia "
     "route is a chronic/metabolic story and this paper is direct evidence "
     "against importing it. The pH line on the Sweeps view is 6.8 on this "
     "basis and is labelled a DECLARED MARKER, not a predicted death; see "
     "HANDOVER entry 40. CAVEAT THE PAPER STATES (p.795) AND THE MODEL "
     "DOES NOT CARRY: these were undisturbed paralysed volunteers with no "
     "endobronchial manipulation, dural traction or other vagal stimulus, "
     "and Frumin cites Bohr and Helmendach that vagally-induced asystole "
     "in dogs lengthened once pH fell 0.4 or more. RULED 2026-10-06 NOT to "
     "record that as a model limitation. "
     "THE OPEN QUESTION ABOVE IS NOW CLOSED, 2026-10-06. It stood from "
     "2026-09-29: the pH/PCO2 relation above PaCO2 ~100 had never been "
     "tested, because the only data were his own nomogram extrapolations. "
     "Potkin & Swenson 1992 is a MODERN electrode in that regime and the "
     "model's Kelman 1967 pK' reproduces his bicarbonate to 4.5 per cent at "
     "pH 6.60 and PaCO2 375 (1.0 per cent if the triple is taken at 37 C "
     "rather than at his own 32.2 C -- see the Potkin entry). So the "
     "disagreement with Frumin is NOT an "
     "acid-base defect. IT DOES NOT FOLLOW that a CO2 rate defect is thereby "
     "discovered: test_frumin_1959 has carried both his rows as RULED OPEN "
     "since 2026-09-29, and 19781b8 of 2026-09-27 withdrew three 'too slow' "
     "claims, one against Frumin by name, ruling the decay past 15 min "
     "'untested, not wrong'. Eliminating acid-base removes an EXCUSE for a "
     "known open row, not the row. Matched per subject on the benchmark's own "
     "configuration the model is 0.66x his rate, range 0.48-0.80. "
     "Checked the other way too: at his measured content of "
     "32.9 mmol/L, Henderson-Hasselbalch reproduces his reported tension to "
     "0.1 per cent at pH 6.87 and 6.97 and to 2.1 per cent at 6.88, and "
     "misses only at 6.72 (215 against his 250) -- the row this entry "
     "already flags as off the end of the nomogram, missing in the direction "
     "that flag predicts. CAVEAT: 32.9 is SUBJECT 6's content and the 6.72 "
     "row is SUBJECT 7, whose content was never reported, so that bounds the "
     "NOMOGRAM and not the patient, and does not license rewriting 250 as "
     "the model's target. See HANDOVER entry 42"),
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
    ("Laws 1968, *Can Anaes Soc J* 15(4):325-331 (n=8 analysed)",
     "frc_drop -- TESTED IT AND LEFT IT UNCHANGED",
     "2026-10-02",
     "read at source from upload. THE ONLY PARALYSED FRC MEASUREMENT HELD, "
     "and therefore the only one in the state frc_anaes() represents: helium "
     "dilution, supine, thiopentone + suxamethonium, intubated, measured 6-7 "
     "min into paralysis. Premedication alone did NOTHING (-2.9%, NS, n=11). "
     "Induction + paralysis fell 9.0% from the premedicated baseline (p<0.01) "
     "and 10.8% from the unmedicated ward baseline (p<0.05); recomputed from "
     "his per-patient table that is 239 mL (SD 238) and 10.81%, reproducing "
     "his stated 10.8% and so verifying the transcription. NOTHING IN THE "
     "MODEL WAS SET FROM IT, RULED 2026-10-02 -- the shipped 14.55% drop at "
     "BMI 22 sits inside Laws's 95% CI (2.18-19.45%) and inside Hewlett's "
     "(10.69-21.51%), and the two papers do not differ from each other "
     "(Welch p = 0.26). A NEGATIVE RESULT: the simulator-sourced value was "
     "tested against the admissible measurement and survived. His age slope, "
     "0.450 %/yr, independently matches Hewlett's 0.430 in a different state "
     "-- NOT IMPLEMENTED, because age is not pursued in any system. Caveats: "
     "n=8, 6F/2M against an explicitly male model, mean 64.8 kg so a light "
     "cohort, and his slope CI (-0.12 to +1.02) contains both Hewlett's "
     "value AND zero"),
    ("Hewlett, Hulands, Nunn & Heath 1974, *Br J Anaesth* 46:486-494 (n=26)",
     "nothing -- corroborates frc_drop's magnitude, wrong state to anchor it",
     "2026-10-02",
     "read at source from upload. 'FRC during anaesthesia II: SPONTANEOUS "
     "RESPIRATION' -- helium dilution, 26 males, supine, thiopentone + "
     "halothane, before and immediately after induction. Mean reduction 390 "
     "mL BTPS, 16.1% (SD 13.4), p<0.001; complete within ~10 min with no "
     "change 6->20 min. TWO OF ITS ROWS KILL MECHANISMS RATHER THAN SUPPORT "
     "THEM: inspired oxygen does not drive the drop (21% at 100% O2 against "
     "20% at 30-35%, pooled with Don), so it is not absorption collapse; and "
     "expiratory muscle activity does not either (13.6% in the 10 patients "
     "with none detectable). The paper states outright that no explanation "
     "is known. NOT USED TO ANCHOR frc_drop, and the reason is recorded "
     "because it was nearly got wrong: THESE PATIENTS WERE BREATHING "
     "SPONTANEOUSLY and frc_anaes() is the paralysed lung -- the same state "
     "trap that disqualified Watson & Pride and Couture 2018. It cites Laws "
     "1968 for the paralysed case but quotes no paralysed value. Its age "
     "regression (% reduction = 4.0 + 0.43 x age, r=0.41, p<0.005) is NOT "
     "implemented; see apnoea_core.py frc_drop and height_factor()"),
    ("Hewlett, Hulands, Nunn & Minty 1974, *Br J Anaesth* 46:479-485",
     "nothing -- it bounds the MEASUREMENT ERROR behind Laws and Hewlett II",
     "2026-10-05",
     "read at source from upload. 'FRC during anaesthesia I: METHODOLOGY', the "
     "companion to Hewlett II. No FRC measurement in patients; it VALIDATES "
     "the helium-dilution technique against a model lung of known volume "
     "(4.528 L by water displacement). THE METHOD IS UNBIASED -- four series, "
     "mean error +35, +31, -17 and +1 mL on 4.5 L, no significant systematic "
     "error in either mode. BUT ARTIFICIAL VENTILATION COSTS PRECISION: SD of "
     "a single measurement 46-60 mL spontaneous against 107-159 mL "
     "ARTIFICIAL, 1.8-3.5x worse, mechanism given (the artificial mode adds "
     "~1.5 L of apparatus volume to the circuit). WHY THAT MATTERS: Laws 1968 "
     "measured his baseline awake-spontaneous and his post-induction value "
     "PARALYSED, so his difference carries one error of each kind -- 116-170 "
     "mL, which is 24-51% of the 238 mL per-patient scatter he reported. "
     "Hewlett II, spontaneous throughout, carries only 65-85 mL, 4-7% of its "
     "325 mL scatter, so its spread is ~95% biological. It also shows LAWS'S "
     "OWN PRECISION CLAIM IS OPTIMISTIC BY HIS OWN ACCOUNT: his CV 0.7% on a "
     "lung analogue is ~32 mL, 3-5x smaller, and he states the reason -- 'no "
     "parallel for oxygen consumption could be designed with this set-up "
     "without loss of helium at the same time'. NOTHING IN THE MODEL WAS SET "
     "FROM IT: frc_drop stays at 400 mL and the 2026-10-02 ruling stands; this "
     "only explains WHY Laws is too imprecise to move it. CAVEAT: these are "
     "HEWLETT'S apparatus and model, and Laws used a Godart meter with a 9 L "
     "Collins spirometer, so it bounds the error of the TECHNIQUE CLASS under "
     "artificial ventilation, not Laws's specific instrument"),
    ("Joyce & Williams 1999, *J Appl Physiol* 86(4):1116-1125 (MODEL, not data)",
     "the KINETICS of absorption atelectasis -- the first external check the "
     "collapse mechanism has ever had",
     "2026-10-07",
     "READ IN FULL from upload, after Dale & Rahn 1952 was sought and A. Heard "
     "confirmed it unavailable. THIS IS A MATHEMATICAL MODEL, NOT A "
     "MEASUREMENT, and that bounds what it can settle: an ideal lung "
     "compartment, Wagner's four-compartment peripheral tissue, and gas uptake "
     "from a closed collapsible cavity. Standard version: pocket = 10 per cent "
     "of preinduction alveolar volume, HPV incorporated, 3 min preinduction. "
     "TIME FOR THE UNVENTILATED POCKET TO COLLAPSE, which is the quantity our "
     "tau_collapse_o2/_air encode: WITH 3 min preoxygenation, about 0.5 h on "
     "air after induction and UNDER 10 MINUTES at FiO2 1.0; WITHOUT "
     "preoxygenation, over 4 h on air and over 0.5 h at FiO2 1.0. "
     "Preoxygenation is at least 4x faster for any given post-induction gas "
     "and is 'the most important determinant of the time to collapse'. Which "
     "inert gas is breathed matters little (N2O cuts the time by no more than "
     "31 per cent, and only with preoxygenation). HPV PROLONGS collapse, more "
     "so without preoxygenation. Without preoxygenation the pocket's PO2 "
     "equilibrates with mixed venous in about 2 min. "
     "OUR MODEL AGREES AT BOTH ENDS, and nothing was fitted toward it -- the "
     "paper was read after the runs. Obstructed and preoxygenated, this "
     "model's per-compartment atelectasis term rises from about 150 s and "
     "plateaus by 600 s, i.e. collapse complete inside 10 minutes against his "
     "'<10 min'. Started on AIR it is 0.000000 through 1200 s, which is what "
     "his '>4 h' requires. THAT IS THE NITROGEN SPLINT, reproduced as a "
     "consequence rather than a switch. "
     "CAVEATS KEPT WITH IT: model against model, which this project has "
     "refused as an anchor before (the Laviola CICO row); his pocket geometry "
     "is a single 10 per cent cavity and ours is a per-compartment fraction; "
     "and 'collapse complete' is not the same event as 'our atelectasis term "
     "plateaus'. NOTHING WAS CHANGED FROM IT. See HANDOVER entry 43"),
    ("Rothen 1996, *Acta Anaesthesiol Scand* 40:524-529 (n=24, RANDOMISED)",
     "the gas-composition effect on INDUCTION shunt -- and the model fails it",
     "2026-10-07",
     "READ AT SOURCE from upload, the paper Magnusson & Spahn cite and the one "
     "that pairs SHUNT with CT AREA in the SAME patients, which is what makes "
     "it decisive. 24 adults with healthy lungs, elective surgery, face-mask "
     "induction on 30% oxygen in nitrogen (group 1, n=12, age 48+-15, BMI "
     "27.2+-6.7) or 100% oxygen (group 2, n=12, age 46+-14, BMI 25.5+-3.4). "
     "Atelectasis by CT 1 cm above the right diaphragm, V/Q by MIGET, awake "
     "and anaesthetised. HEIGHT IS NOT REPORTED. "
     "MEASURED: no atelectasis awake. Atelectasis 0.2+-0.4 cm2 (30%) against "
     "8.0+-8.2 cm2 (100%), P<0.001. Shunt 0.3+-0.7% awake, rising to 2.1+-3.8% "
     "(30%) and 6.5+-5.2% (100%), P<0.05. V/Q mismatch indices did NOT differ "
     "between groups. "
     "IT SETTLES THE EDMARK COMPARISON in HANDOVER entry 43: his CT-AREA ratio "
     "is 40x while his SHUNT ratio is only 3.1x, so area and shunt DO NOT "
     "SCALE TOGETHER and comparing this model's perfusion-fraction term "
     "against a CT-area ratio was the wrong comparison. "
     "AND THE MODEL FAILS IT. Run at Rothen's own cohort (1.75 m assumed), "
     "shunt at 60 s is 6.68% for group 1 and 6.86% for group 2 -- a 0.18 "
     "percentage point difference against his measured 4.4. The 100% arm is "
     "about right (6.86 against 6.5); the 30% arm is THREE TIMES TOO HIGH "
     "(6.68 against 2.1). The reason is visible: unwashed_fraction(), the only "
     "FiO2-dependent induction term, returns 0.15% and 0.00% for these "
     "patients, so apnoea_core's claim to predict 'MORE atelectasis on 100% "
     "oxygen than on 30-50%' does not hold at normal BMI. "
     "CAVEATS: his patients were MECHANICALLY VENTILATED after induction and "
     "this model's t=0 is the onset of APNOEA, which are different states; his "
     "SDs are large on n=12 and 2.1+-3.8 overlaps zero, so the DIFFERENCE "
     "between groups is the firm part and not the absolutes; the groups were "
     "not BMI-matched, though the two heaviest patients (BMI 37.1 and 44.0) "
     "were in the 30% group and had 0.0 and 0.2 cm2 of atelectasis, which "
     "STRENGTHENS the gas effect rather than confounding it. "
     "NOTHING WAS CHANGED FROM IT and no benchmark row was added: that is a "
     "ruling for A. Heard. See HANDOVER entry 43 section 8"),
    ("Magnusson & Spahn 2003, *Br J Anaesth* 91(1):61-72 (REVIEW)",
     "how MUCH lung collapses at different FiO2 -- the magnitude side, which "
     "is the side that moves this model",
     "2026-10-07",
     "READ IN FULL from upload. A REVIEW, so everything in it is secondhand "
     "and the primary papers are named here rather than its summaries trusted. "
     "WHAT IT POINTS AT THAT IS USABLE: Rothen 1996 (Acta Anaesthesiol Scand "
     "40:524-9, NOT YET HELD) -- at FiO2 1.0 shunt rose 0.3 to 6.5 per cent "
     "with atelectasis area 8.0 cm2; at FiO2 0.3, shunt 2.1 per cent and "
     "atelectasis 0.2 cm2. That pairs shunt WITH area in the same patients, "
     "which is what would let our perfusion-fraction atelectasis term be "
     "compared with a CT area at all. Also: FiO2 1.0 after a vital-capacity "
     "manoeuvre brings atelectasis back within 5 min, where 40 per cent keeps "
     "it away for at least 40 min; and COPD patients make almost no "
     "atelectasis but worse V/Q mismatch. "
     "WHAT IT POINTS AT THAT IS NOT USABLE AS IT STANDS: the 80-versus-100 "
     "figures everything else in this entry is cited for -- 0.8 per cent "
     "atelectasis after preoxygenation with 80 per cent oxygen against 6.8 per "
     "cent with 100 per cent, and time to SpO2 90 per cent of 307 s against "
     "391 s -- are its reference 18, EDMARK, ENLUND, KOSTOVA-AHERDAN & "
     "HEDENSTIERNA, ANESTHESIOLOGY 2001; 95: A1330. THE 'A' MAKES IT AN ASA "
     "MEETING ABSTRACT, reaching us SECONDHAND THROUGH A REVIEW. Secondhand "
     "and an abstract is the combination that has produced retractions here "
     "before, so no band was drawn from it. "
     "THE MODEL BRACKETS EDMARK ANYWAY, recorded as information and not as a "
     "pass: time to SpO2 90 per cent after preoxygenation is 521 s (100 per "
     "cent) and 417 s (80 per cent) in the lean configuration, 351 s and 283 s "
     "in the Heard obese one, so his 391 s, 307 s AND his 84 s difference all "
     "fall between our two patients, whose build his abstract does not give. "
     "BUT THE ATELECTASIS RATIO DOES NOT AGREE: 1.77x lean and 1.68x obese "
     "against his 8.5x. Those are DIFFERENT QUANTITIES -- ours is a perfusion "
     "fraction of collapsed units, his is per cent of lung area on a CT slice "
     "-- so the mismatch may be the comparison and not the model. Rothen 1996 "
     "is what would separate them. NOTHING WAS CHANGED FROM IT. See HANDOVER "
     "entry 43"),
    ("Potkin & Swenson 1992, *Chest* 102(6):1742-1745 (CASE REPORT, n=1)",
     "how dangerous pure hypercapnic acidosis actually is -- the pH line's "
     "upper anchor",
     "2026-10-06",
     "READ AT SOURCE from upload (all four pages). A 46-year-old healthy man, "
     "no respiratory disease or sleep apnoea, had elective outpatient cosmetic "
     "facial surgery. HE COULD NOT BE INTUBATED, so he was mask-ventilated for "
     "4-6 h on an unspecified supplemental oxygen mixture, monitored by "
     "oximetry alone -- saturation never fell below 90 per cent, and no "
     "anaesthetic records survived. He did not wake. "
     "TABLE 1, arterial, and these are the numbers: on admission pH 6.60, "
     "PaCO2 375 mmHg, PaO2 40, HCO3 34, base excess -16; at 5 min of mask "
     "ventilation 6.91 / 151 / 244 / 29 / -9; at 25 min of mechanical "
     "ventilation 7.08 / 68 / 56 / 25 / -7; at 90 min 7.19 / 58 / 65 / 21 / "
     "-5. He was comatose, hypotensive at 70 systolic by palpation, heart rate "
     "110, apnoeic, and hypothermic at 32.2 C. "
     "HE RECOVERED COMPLETELY. Gases corrected over 24 h, the pulmonary oedema "
     "resolved, consciousness returned to normal on the second hospital day, "
     "and at discharge his gases, chest film and neurological examination were "
     "all normal, with no memory or attention deficits at follow-up. The "
     "authors call 375 'the highest reported value in a surviving human' while "
     "stating plainly that it is an over-read -- the PCO2 electrode was past "
     "its calibration range and the log PCO2/pH relation deviates toward "
     "acidosis above 100 mmHg -- but put the true value 'over 300 mm Hg' on "
     "Prys-Roberts's data. Earlier complete recoveries span 130-270 mmHg. "
     "WHAT IT PINS, AND IT IS A CEILING NOT A PARAMETER: pure respiratory "
     "acidosis is survivable far below any pH this model will reach in an "
     "hour, PROVIDED oxygenation and perfusion hold. Their own condition is "
     "quoted verbatim on the Sweeps page: profound hypercapnia and severe "
     "respiratory acidosis for many hours 'can be tolerated and are associated "
     "with no long-term morbidity WHEN OXYGENATION AND TISSUE PERFUSION ARE "
     "MAINTAINED'. The mechanism they give is why that proviso is not "
     "decoration: intracellular pH defence runs on Na+/H+ exchange and "
     "H+-translocating ATPases, both energy-consuming, so it fails exactly "
     "when the cell is hypoxic or underperfused. "
     "POTASSIUM, AGAIN, AND AT A FAR LOWER pH THAN FRUMIN: the serum drawn "
     "with the second gas gave K+ 5.1 mmol/L -- mildly raised and nowhere near "
     "arrhythmogenic -- at an arterial pH of about 6.6-6.9. With Frumin's 0.4 "
     "mEq/l maximum rise this is now two independent human sources saying "
     "acute respiratory acidosis does not produce a dangerous potassium. "
     "AND IT EXPLAINS AN ARTEFACT THIS PROJECT HAS BEEN FIGHTING: the base "
     "excess of -16 did NOT mean a metabolic acidosis. The venous anion gap "
     "was 9, i.e. normal, and the authors attribute the apparent deficit to "
     "the difference between whole blood in vitro and the whole body -- "
     "intracellular pH regulation moves HCO3- into cells at the expense of "
     "the extracellular space, which reads as lost bicarbonate. They state "
     "there are no data to quantitate the error of standard base-excess "
     "calculations in extreme hypercapnia. THAT BEARS DIRECTLY on the "
     "handover_numbers.py base-excess sweep, which records that no base excess "
     "reproduces Frumin's pH and CO2 content together: a measured 1959 base "
     "excess at PaCO2 above 100 may not be a metabolic quantity at all. "
     "NOTHING IN THE MODEL WAS CHANGED FROM IT. It is a ceiling on how "
     "alarming a pH line may be drawn, and the reason the Sweeps pH limbs are "
     "labelled markers rather than death lines; see HANDOVER entry 41. "
     "CAVEATS: n=1, he was hypothermic at 32.2 C which the authors say may "
     "have helped and which they cannot test since 'there are no human data "
     "above a PCO2 of 270 mm Hg'; and the tolerance is for NONHYPOXIC "
     "acidosis -- his PaO2 was 40 on admission, so the oximetry that reported "
     "above 90 per cent through the operation is the weakest link in the "
     "account. "
     "IT ALSO CLOSES THE ACID-BASE OPEN QUESTION ON FRUMIN, 2026-10-06. The "
     "model's Kelman 1967 pK' predicts his reported bicarbonate from his own "
     "measured pH and PaCO2, with no base excess involved. TEMPERATURE "
     "MATTERS HERE AND THE FIRST VERSION OF THIS NOTE IGNORED IT: the paper "
     "calls these TEMPERATURE-CORRECTED values and he was 32.2 C, so the "
     "triple most likely belongs at his temperature. At 32.2 C the model "
     "gives 35.5 against 34 (4.5 per cent), 30.3 against 29 (4.4 per cent) "
     "and 22.9 against 21; at 37 C, 34.3 (1.0 per cent), 29.1 (0.4 per cent) "
     "and 21.9. THE 4.5 IS THE FIGURE TO QUOTE and the 1.0 was quoted "
     "unqualified until A. Heard pointed at the hypothermia on 2026-10-06. "
     "The paper does not say which temperature its DERIVED HCO3 column used, "
     "so both are pinned in handover_numbers.py and the less flattering one "
     "is the headline. The relation is right "
     "in the regime where it had never been tested, so the Frumin "
     "disagreement is not an acid-base one -- which removes an excuse for an "
     "already ruled-open row rather than discovering it; see HANDOVER entry "
     "42 section 7. "
     "HIS ROW 3 IS INTERNALLY INCONSISTENT AND IT IS THE PaCO2 -- an "
     "inference about the PAPER, not a finding about the model. Each row ties "
     "four numbers with two equations; the other three agree with themselves "
     "to within 4 mmHg, while row 3's pH 7.08 and HCO3 25 imply 86.2 mmHg "
     "against a printed 68. At 87 both his HCO3 (25.2) and his base excess "
     "(-6.5) fall out; at 68 neither does. 87 -> 68 is a digit transposition, "
     "and classic Henderson-Hasselbalch at pK 6.1 gives the same 19.6 at 68, "
     "so it is not an artefact of Kelman. That row is EXCLUDED from the "
     "validation above and the exclusion is stated rather than silent. "
     "THE BASE-EXCESS COLUMN DOES NOT REPRODUCE from his own pH and HCO3: "
     "-16 printed against -9.1 computed at admission, a 6.9-unit gap in the "
     "direction he describes -- but the 90-min row goes the OTHER way (-5 "
     "printed, -7.8 computed) and he was 32.2 C and warming, so temperature "
     "correction confounds the column. SUGGESTIVE, NOT ESTABLISHED. NOTHING "
     "WAS TUNED ON IT, and that is the point: fitting the model's be to chase "
     "Frumin's pH would have been fitting a parameter to an artefact. "
     "THIS PAPER MAY NOT BE USED AS A CO2-RATE COMPARATOR, ruled 2026-10-06 "
     "by A. Heard: 'the hypothermic patient cannot be used as a comparison "
     "for our scenario'. A one-sided test was proposed -- apnoea eliminates "
     "no CO2 while this man was partly ventilated, so the apnoeic model "
     "should reach at least his tension on the same clock -- and a six-hour "
     "run was STOPPED UNFINISHED on the ruling, with nothing from it "
     "recorded. The ruling is right: his rise is production MINUS "
     "elimination where Frumin's is production alone, he was hypothermic by "
     "an unmeasured amount which lowers production, and the 4-6 h is the "
     "surgeon's estimate rather than a measured clock. His implied mean rate "
     "of 0.72-1.40 mmHg/min is therefore NOT comparable with Frumin's "
     "apnoeic 2.7-4.9, and Frumin is not an outlier against him because this "
     "paper cannot test him. Frumin remains an outlier only against Kaiser "
     "2024 (2.10 at 15 min), and that is itself 18-55 min against 15"),
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
