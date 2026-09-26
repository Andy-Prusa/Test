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
    ("Damia 1988, *Br J Anaesth* 60:574-8 (n=30)",
     "anaesthetised FRC in morbid obesity, and the posture claim",
     "2026-09-26",
     "read at source. It FALSIFIES the model's largest untested claim -- "
     "that lying flat costs a BMI 50 patient 63% of FRC -- by measuring "
     "awake SUPINE FRC at BMI 53.2 as 2250 mL against Jones's SEATED 2125 "
     "mL at BMI 50. It also disagrees with Pelosi 1998 on anaesthetised FRC "
     "by a factor of two at the same BMI, same method, same conditions"),
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
