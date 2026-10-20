# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
bloodvol_numbers.py -- regenerates every number quoted from Feldschuh & Enson
1977, and fails if one has drifted.

Same contract as handover_numbers.py, hewlett_numbers.py, aa_numbers.py and
frc_level_numbers.py: NOT in the pre-commit hook, because these are claims
about the world rather than invariants of the code. Fast -- a few seconds,
nothing is simulated.

    python3 bloodvol_numbers.py

THE SOURCE. Feldschuh J, Enson Y. "Prediction of the normal blood volume:
relation of blood volume to body habitus." Circulation 1977;56:605-12. Read in
full from upload 2026-10-20. Published data only.

WHY IT MATTERS, AND WHAT IT CLOSES. o2_store_numbers.py section 5 records that
the model's blood stores do not scale with the patient, and leaves the
direction of any correction OPEN on the explicit grounds that "no measurement
of blood volume against weight, lean mass or body surface area is in
SOURCES.md". THIS PAPER IS THAT MEASUREMENT: 188 observations in 160 normal
volunteers spanning -38.7% to +210.8% of desirable weight, with blood volume
regressed on weight, on height and on body surface area, separately by sex.
The gap that paragraph names is now filled and the direction is no longer
open. Section 6 below is what it changes.

IT ALSO SETTLES THE PROVENANCE OF 70 mL/kg, asked on 2026-10-19. The figure is
real, it is traceable, and the paper that names it is a refutation of using it
as a constant. Section 3.

THE LIMITS, WHICH ARE NOT SMALL.

1. SEX. Every regression is sex-specific and this model has no sex parameter.
   Where an arm's sex is not held, both sexes' predictions are printed and the
   SPAN is the finding, not either endpoint.

2. THE METHOD THE PAPER ITSELF PREFERS IS NOT REPRODUCIBLE HERE. Its best
   predictor is a curvilinear regression on deviation from desirable weight
   (its method 3, standard error +-465 mL). No equation for it is printed --
   it is figure 3 plus the Metropolitan Life Insurance Company Desirable
   Weight tables, neither of which is held. So only its method 2 (linear
   regression on weight or on surface area, standard error +-531 and +-510 mL)
   can be computed, and method 2 is a method the paper reports as still biased
   with respect to height. Any figure below carrying a method-2 prediction
   inherits that bias.

3. BODY HAEMATOCRIT. Blood volume was calculated from plasma volume and body
   haematocrit, and the constants the paper compares against were "corrected
   where necessary to body hematocrit by assuming an average peripheral
   hematocrit of 45% for men and 41% for women". The model's haemoglobin is a
   free parameter set per benchmark, so the two are not haematocrit-matched.
"""
import io

import numpy as np

import bloodgas as bg

import apnoea_core as A
from apnoea_core import Patient

print(A.provenance())
print()

FAILED = []


def check(name, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    if not ok:
        FAILED.append(name)
    print(f"  {'ok  ' if ok else 'FAIL'} {name:<52}{got:>9.3f}{unit}"
          f"   recorded {want}{unit}")


# ---------------------------------------------------------------- transcription
# TABLE 1, p.607: "Summary of Physical Characteristics and Blood Volumes
# Encountered in 160 Normal Subjects". Mean, SD, range as printed. The men's
# weight, deviation, surface area and blood volume rows carry the footnote
# "*108 observations"; age and height are on 80. 80 + 108 = the 188
# observations figure 2 and table 3 both quote.
T1 = {
    'women': dict(n=80, nobs=80, age=37.0, wt=86.1, dev=58.5, ht=159.7,
                  sa=1.87, bv=4.57, bv_sa=2.44, bv_kg=55.1,
                  bv_kg_sd=8.88, bv_kg_range=(40.0, 83.0),
                  wt_range=(40.1, 157.6), dev_range=(-15.9, 210.8),
                  bv_range=(2.89, 7.24)),
    'men':   dict(n=80, nobs=108, age=35.0, wt=77.7, dev=6.4, ht=175.5,
                  sa=1.92, bv=5.32, bv_sa=2.78, bv_kg=73.3,
                  bv_kg_sd=16.4, bv_kg_range=(43.6, 108.4),
                  wt_range=(47.6, 221.1), dev_range=(-38.7, 208.4),
                  bv_range=(3.37, 9.65)),
}

# FIGURE 2, p.607-8: the six linear regressions, printed in the panels.
# "WBV" is whole blood volume in LITRES; ht in cm, wt in kg, sa in m2.
# Panels are labelled WOMEN (left) and MEN (right), so the sex assignment
# is read off the page and not inferred.
FIG2 = {
    'women': dict(ht=(-2.817, 0.046, 0.349, 0.881),
                  wt=(1.728, 0.033, 0.876, 0.460),
                  sa=(-1.381, 3.187, 0.871, 0.465)),
    'men':   dict(ht=(-1.892, 0.041, 0.373, 0.858),
                  wt=(3.425, 0.024, 0.774, 0.578),
                  sa=(0.391, 2.566, 0.804, 0.541)),
}

# TABLE 3, p.610: observed vs predicted, 188 observations.
T3 = [
    ("1. constant ratio",       "body weight",   0.773, 1529),
    ("1. constant ratio",       "surface area",  0.864,  684),
    ("2. linear regression",    "body weight",   0.842,  531),
    ("2. linear regression",    "surface area",  0.856,  510),
    ("3. curvilinear regr.",    "deviation",     0.901,  465),
]


def wbv(sex, var, x):
    """Whole blood volume in litres from figure 2's regression."""
    a, b, _r, _se = FIG2[sex][var]
    return a + b * x


def dubois_sa(wt_kg, ht_cm):
    """The paper's own footnote: SA = Wt^0.425 x Ht^0.725 x 71.84 (cm2)."""
    return wt_kg ** 0.425 * ht_cm ** 0.725 * 71.84 / 1e4


print("1. THE TRANSCRIPTION, VALIDATED AGAINST THE PAPER'S OWN TABLE. Figure 2's")
print("   six regressions and table 1's six means were transcribed from")
print("   separate pages. A regression passes through the mean of its own")
print("   sample, so evaluating each equation at table 1's mean x MUST return")
print("   table 1's mean blood volume. Three independent variables x two sexes:")
print()
for sex in ('women', 'men'):
    for var, xlab in (('ht', 'height'), ('wt', 'weight'), ('sa', 'surface area')):
        got = wbv(sex, var, T1[sex][var])
        check(f"   {sex:<5} on {xlab:<12} -> blood volume",
              got, T1[sex]['bv'], 0.05, " L")
print()
print("   All six land on the printed mean within 50 mL. The equations and the")
print("   table are read correctly, and the WOMEN/MEN assignment is confirmed")
print("   by the arithmetic as well as by the panel labels -- which matters,")
print("   because the sexes' weight slopes run the counter-intuitive way:")
print(f"   women {FIG2['women']['wt'][1]:.3f} L/kg is STEEPER than men")
print(f"   {FIG2['men']['wt'][1]:.3f} L/kg, on a lower intercept. Swapping them")
print("   would still look plausible and would be wrong.")
print()
print("   ONE APPARENT DISCREPANCY THAT IS NOT ONE, recorded so it is not")
print("   re-discovered as an error. Table 1's printed mL/kg is NOT its mean")
print("   blood volume over its mean weight:")
for sex in ('women', 'men'):
    ratio_of_means = T1[sex]['bv'] * 1000.0 / T1[sex]['wt']
    print(f"     {sex:<5}  printed mean of ratios {T1[sex]['bv_kg']:>5.1f} mL/kg"
          f"   vs ratio of means {ratio_of_means:>5.1f} mL/kg")
print("   The mean of a ratio exceeds the ratio of means when the denominator")
print("   varies (1/weight is convex), and it does so for BOTH sexes and by a")
print("   similar margin. This is Jensen's inequality in a wide-weight cohort,")
print("   not a misreading.")
print()

print("2. WHAT THE PAPER MEASURES, in its own words. Results, p.608:")
print()
print('     "In extremely underweight but otherwise normal subjects the ratio')
print('      of BV to body weight is 90-100 ml/kg. As the degree of obesity')
print('      increases the ratio falls until it appears to level off at about')
print('      43 ml of blood per kg body weight. In very thin individuals the')
print('      ratio is almost 2.5 times higher than it is in the presence of')
print('      severe obesity."')
print()
print("   Discussion, p.609-10, restating the same two ends with different")
print("   roundings -- all three are recorded rather than one being chosen:")
print()
print('     asymptote     "approximately 45 ml/kg", and separately "the actual')
print('                    blood content of adipose tissue must lie below the')
print('                    40-43 ml/kg suggested by our data"')
print('     underweight   "individuals who are 25 to 35% underweight ranges')
print('                    from 95-105 ml/kg"')
print()
print("   THE DIRECTION IS THE ONE THAT TRAPS A READER. The RATIO falls with")
print("   obesity, but the ABSOLUTE volume still rises -- the regressions have")
print("   positive weight slopes in both sexes. Reasoning from 'mL/kg falls")
print("   with obesity' to 'the obese have less blood' inverts the finding.")
print()
print("3. WHERE 70 mL/kg COMES FROM. Asked 2026-10-19: '70 mls/kg is what I was")
print("   taught. Search for proof.' The figure is traceable and this paper")
print("   names it -- as the convention it exists to refute. Methods, p.608:")
print()
print('     "The values chosen for the BV to body weight ratio, 72.6 ml/kg for')
print('      men and 66.3 ml/kg for women, represent commonly used averages of')
print('      a number of reports[14,19-21] corrected where necessary to body')
print('      hematocrit by assuming an average peripheral hematocrit of 45%')
print('      for men and 41% for women."')
print()
print("   So 70 mL/kg is not this paper's measurement and is not presented as")
print("   anyone's physiological constant. It is the mid-point of the two")
print("   figures the paper adopts to STAND IN for the teaching convention,")
print("   purely so that convention can be scored in its table 3:")
_mid = (72.6 + 66.3) / 2.0
check("   mean of the two conventional constants", _mid, 69.45, 0.01, " mL/kg")
print("   -- 69.5 mL/kg, which is the taught 70 to within half a millilitre.")
print()
print("   AND THE PAPER EXPLAINS WHY THE TAUGHT FIGURE VARIES BY SOURCE.")
print("   Discussion, p.609-10:")
print()
print('     "These considerations explain the wide range of average normal')
print('      ml/kg values (62-86 ml) for BV reported by different')
print('      investigators. Such studies were usually performed on randomly')
print('      selected normal individuals. However, the range of 62-86 ml/kg')
print('      corresponds (fig. 3) to population groups which vary from 25%')
print('      underweight to 16% overweight. Hence the variation in reported')
print('      values suggests that the populations selected at random actually')
print('      differed significantly in their average composition with respect')
print('      to body habitus."')
print()
print("   THE ANSWER TO THE QUESTION, THEREFORE. 70 mL/kg is sound for the")
print("   habitus it was measured in -- somewhere between 25% underweight and")
print("   16% overweight -- and the paper gives it no wider warrant than that.")
print("   It is held as the convention's value, NOT as a property of blood.")
print()

print("4. WHAT IT COSTS TO USE A CONSTANT RATIO, which is the finding that")
print("   makes this more than a provenance note. Table 3, p.610, scores three")
print("   prediction methods against all 188 observed blood volumes:")
print()
print(f"     {'method':<24}{'reference':<15}{'r':>7}{'SE of estimate':>17}")
for meth, ref, r, se in T3:
    print(f"     {meth:<24}{ref:<15}{r:>7.3f}{se:>14} mL")
print()
print("   The taught constant ratio on body weight is the WORST row in the")
print("   table: r = 0.773 and a standard error of estimate of +-1529 mL.")
_relerr = 1529.0 / ((T1['women']['bv'] + T1['men']['bv']) / 2.0 * 1000.0) * 100.0
check("   +-1529 mL as % of the two cohorts' mean BV", _relerr, 30.9, 0.2, "%")
print("   About a third of the quantity being predicted. The paper's own")
print("   preferred method cuts that to +-465 mL, which it reports as '+-9")
print("   percent of the mean' -- a better than threefold reduction.")
print()
print("   Abstract, in the authors' summary: blood volume 'is not a constant")
print("   fraction of body weight or SA in this population. Its prediction")
print("   from such constant ratios results in a large error of estimate which")
print("   is systematically biased with respect to height and weight.'")
print()
print("   AND THE BIAS HAS A DIRECTION, p.609: 'BV is overestimated in obese")
print("   and underestimated in lean individuals' by the body-weight constant.")
print()
print("5. THE MODEL'S OWN BLOOD VOLUME AGAINST THIS PAPER. The three stores sit")
print("   at apnoea_core.py lines 1514-1516. UNTIL 2026-10-20 THEY CARRIED NO")
print("   COMMENT AND NO CITATION, and SOURCES.md had never listed them either,")
print("   although between them they are the model's entire non-lung oxygen")
print("   store. Both omissions were closed the day this paper was read, and")
print("   what the code comment now says is a summary of this section:")
print()
print(f"     v_art     arterial blood                  {Patient.v_art} L")
print(f"     v_ven     venous blood                    {Patient.v_ven} L")
print(f"     v_tis_o2  'tissue', but holds a BLOOD     {Patient.v_tis_o2} L")
print("               oxygen content (o2_store_numbers.py section 1)")
print()
_blood = Patient.v_art + Patient.v_ven
_total = _blood + Patient.v_tis_o2
check("   unambiguously blood, v_art + v_ven", _blood, 3.0, 1e-9, " L")
check("   all three, if the tissue term is blood", _total, 4.5, 1e-9, " L")
print()
print("   SO THE MODEL HAS TWO BLOOD VOLUMES AND THE NAMING DECIDES WHICH.")
print("   That ambiguity is already logged as an open question (whether to")
print("   rename the tissue compartment); this paper is the first thing held")
print("   that makes it cost something, because 3.0 L and 4.5 L fall on")
print("   opposite sides of every prediction below.")
print()
print("   WHAT FELDSCHUH'S METHOD-2 REGRESSIONS GIVE AT THE SUITE'S ARMS. The")
print("   model has no sex, so both are printed and the SPAN is the finding.")
print("   Berthoud's sex mix is NOT held in this repository, which is why no")
print("   single column is picked out:")
print()
ARMS = [
    ("generic 70 kg row",     70.0,  1.75),
    ("Berthoud control",      63.0,  float(np.sqrt(63.0 / 23.1))),
    ("Berthoud obese",       123.5,  float(np.sqrt(123.5 / 49.0))),
]
print(f"     {'arm':<20}{'BMI':>6}{'women':>9}{'men':>8}{'  (on weight)':<14}"
      f"{'women':>8}{'men':>8}  (on SA)")
_pred = {}
for nm, wt, ht in ARMS:
    bmi = wt / ht ** 2
    sa = dubois_sa(wt, ht * 100.0)
    w_wt, m_wt = wbv('women', 'wt', wt), wbv('men', 'wt', wt)
    w_sa, m_sa = wbv('women', 'sa', sa), wbv('men', 'sa', sa)
    _pred[nm] = (w_wt, m_wt, w_sa, m_sa)
    print(f"     {nm:<20}{bmi:>6.1f}{w_wt:>9.2f}{m_wt:>8.2f}{' L':<14}"
          f"{w_sa:>8.2f}{m_sa:>8.2f} L")
print()
check("   generic 70 kg row, women on weight", _pred['generic 70 kg row'][0], 4.04, 0.01, " L")
check("   generic 70 kg row, men on weight",   _pred['generic 70 kg row'][1], 5.10, 0.01, " L")
check("   Berthoud obese, women on weight", _pred['Berthoud obese'][0], 5.80, 0.01, " L")
check("   Berthoud obese, men on weight",   _pred['Berthoud obese'][1], 6.39, 0.01, " L")
check("   Berthoud control, women on weight", _pred['Berthoud control'][0], 3.81, 0.01, " L")
check("   Berthoud control, men on weight",   _pred['Berthoud control'][1], 4.94, 0.01, " L")
print()
print("   THE FINDING, AND IT IS NOT THE ONE THE RATIO WOULD SUGGEST. Read on")
print("   the 4.5 L total, the model is inside the control arm's sex span and")
print("   BELOW the obese arm's by a wide margin:")
print()
for nm, wt, ht in ARMS:
    w_wt, m_wt, _w_sa, _m_sa = _pred[nm]
    lo, hi = min(w_wt, m_wt), max(w_wt, m_wt)
    inside = lo <= _total <= hi
    gap = 0.0 if inside else (_total - lo if _total < lo else _total - hi)
    where = "inside the sex span" if inside else f"{gap:+.2f} L outside it"
    print(f"     {nm:<20} model {_total:.1f} L vs {lo:.2f}-{hi:.2f} L   {where}")
print()
print("   So the obese arm is given LESS blood than this paper's regressions")
print("   predict for a 123.5 kg adult, while the 63.0 kg control arm is")
print("   supplied about right. The shortfall, on each reading of the model:")
print()
_ow, _om = _pred['Berthoud obese'][0], _pred['Berthoud obese'][1]
for _lab, _v in (("4.5 L (tissue term counted as blood)", _total),
                 ("3.0 L (v_art + v_ven only)", _blood)):
    print(f"     vs {_lab:<38}"
          f"{_v - _ow:>+7.2f} to {_v - _om:>+6.2f} L"
          f"   ({(_v / _ow - 1) * 100:>+5.1f}% to {(_v / _om - 1) * 100:>+5.1f}%)")
print()
check("   obese shortfall, 4.5 L vs women", _total - _ow, -1.30, 0.01, " L")
check("   obese shortfall, 4.5 L vs men",   _total - _om, -1.89, 0.01, " L")
check("   obese shortfall, 3.0 L vs women", _blood - _ow, -2.80, 0.01, " L")
check("   obese shortfall, 3.0 L vs men",   _blood - _om, -3.39, 0.01, " L")
print()
print("   AND IT IS LOW IN THE DIRECTION THAT MATTERS. o2_store_numbers.py")
print("   section 5 notes that 'a larger obese blood store would lengthen the")
print("   obese arm, which already passes'. That is still true, so this is a")
print("   correction which would push a PASSING row, and the fact that the")
print("   correction is now sourced does not make applying it safe. It must be")
print("   costed with variant_cost.py before any ruling, exactly as the FRC")
print("   conflict was.")
print()
print("6. HOW BIG THE CORRECTION WOULD BE IN OXYGEN, as an UPPER BOUND. The")
print("   extra blood the regressions ask for at the obese arm, valued at")
print("   FULLY ARTERIAL content (hb 14 as that row is run) -- an upper bound,")
print("   because any real split would put some of it in venous blood at a")
print("   lower content:")
print()
_c_art = bg.HUFNER * 14.0 * 1.00 + bg.O2_SOL * 100.0
check("   arterial content at hb 14, SaO2 100%, PaO2 100", _c_art, 19.06, 0.01, " mL/dL")
for _lab, _dv in (("vs women's regression", _ow - _total),
                  ("vs men's regression",   _om - _total)):
    print(f"     {_lab:<24}{_dv:>6.2f} L of blood"
          f"{_dv * 10.0 * _c_art:>8.0f} mL of oxygen at most")
print()
check("   upper-bound extra O2, women's regression", (_ow - _total) * 10.0 * _c_art,
      248.3, 1.0, " mL")
check("   upper-bound extra O2, men's regression", (_om - _total) * 10.0 * _c_art,
      360.0, 1.0, " mL")
print()
print("   FOR SCALE ON THE STORE SIDE: that is 248-360 mL of oxygen against a")
print("   lung store of 347 mL at this arm (o2_store_numbers.py section 2), so")
print("   the correction is of the SAME ORDER as the whole anaesthetised lung")
print("   at BMI 49. THAT IS THE STORE, NOT THE EFFECT, and the two are very")
print("   different here.")
print()
print("   WHAT THE ENDPOINT ACTUALLY DRAWS, which is the figure that bounds any")
print("   effect on the benchmark. o2_store_numbers.py section 2 measures this")
print("   arm as holding 730 mL in blood and tissue and SUPPLYING 148 mL of it")
print("   before SpO2 90% -- 473 mL total supplied, of which 68.7% came from")
print("   the lung. So it depletes only about a FIFTH of the non-lung store:")
_held_bt, _sup_bt = 730.0, 148.0
check("   fraction of the non-lung store the obese arm draws",
      _sup_bt / _held_bt * 100.0, 20.3, 0.3, "%")
print()
print("   AT FIXED FRACTIONAL DEPLETION a 22-30% larger store would therefore")
print("   yield only about 33-44 mL more oxygen, not 248-360 -- but depletion")
print("   is NOT fixed: a larger store falls more slowly, which lengthens the")
print("   time, which raises the draw again. That feedback is why no arithmetic")
print("   here can settle the size, and why the earlier wording in this project")
print("   -- that the quantity is 'nearly inert' -- was withdrawn rather than")
print("   replaced with a different guess. variant_cost.py is the only thing")
print("   that can say. The 60 mL figure quoted elsewhere is the ARTERIAL")
print("   compartment alone and understates the draw: all three blood")
print("   compartments would scale together.")
print()

print("7. WHAT THIS PAPER DOES NOT SETTLE, kept separate so none of it is read")
print("   as part of the above.")
print()
print("   a. THE ARTERIAL/VENOUS SPLIT IS UNTOUCHED. Feldschuh measures TOTAL")
print("      blood volume. Nothing here speaks to the model's 1.0 : 2.0 L")
print("      split between v_art and v_ven, which remains unanchored.")
print()
print("   b. THE TISSUE COMPARTMENT IS STILL NOT A BLOOD VOLUME. v_tis_o2 holds")
print("      a blood oxygen content over 1.5 L, but no published quantity has")
print("      been identified that it IS. Counting it as blood to compare with")
print("      this paper is a reading taken for the sake of the comparison, not")
print("      a claim that it is correct -- and section 5 shows the two readings")
print("      disagree by 1.5 L, which is as large as the correction itself.")
print()
print("   c. SEX IS NOT RESOLVED, AND IS A LARGE FRACTION OF THE EFFECT WITHOUT")
print("      SWAMPING IT. At 123.5 kg the two sexes' weight regressions differ")
print(f"      by {_om - _ow:.2f} L, against a correction of "
      f"{_ow - _total:.2f}-{_om - _total:.2f} L -- so the sex")
print(f"      ambiguity is {(_om - _ow) / (_om - _total) * 100:.0f}-"
      f"{(_om - _ow) / (_ow - _total) * 100:.0f}% as big as the thing being corrected.")
print("      It therefore narrows but does not destroy the finding: BOTH sexes'")
print("      regressions put the obese arm above the model, which is why")
print("      section 5's conclusion survives not knowing Berthoud's sex mix.")
print("      A model with no sex parameter still cannot USE these equations")
print("      without a ruling on which sex it represents, or how to pool them.")
print()
print("   d. THE PAPER'S OWN PREFERRED PREDICTOR CANNOT BE USED. Method 3")
print("      (+-465 mL) needs figure 3 and the Metropolitan Life tables,")
print("      neither held. Only method 2 (+-531 mL on weight) is computable,")
print("      and the paper reports method 2 as still biased with respect to")
print("      height -- which the obese arm, at 1.59 m, sits at the short end")
print("      of. The direction of that residual bias at this height is NOT")
print("      established by anything held.")
print()
print("   e. WHETHER A CONSTANT IS EVEN THE WRONG SHAPE HERE. The model is a")
print("      single generic patient and the suite varies weight per benchmark.")
print("      A fixed 4.5 L is not a constant RATIO -- it is the thing table 3")
print("      scores as method 1's worst case only if read per-kg. Read as an")
print("      absolute, it happens to sit inside the sex span at both lean arms")
print("      and fails only at BMI 49. Whether to scale it at all, and on")
print("      what, is the ruling this paper makes possible but does not make.")
print()

print("8. THE AUDIT OF EVERY OTHER FILE THAT RESTATES THESE FIGURES. This exists")
print("   because of 2026-09-25, when five claims about which papers had been")
print("   read were found wrong across four documents -- the same fact written")
print("   in several places with no link between them. The figures above are")
print("   now restated in five other files, each a rot site, so the links are")
print("   made here: the strings are BUILT FROM THE COMPUTED VALUES and looked")
print("   for in each file. Change the computation and this fails, naming every")
print("   file that needs the new number.")
print()
# A RANGE IS CHECKED AS ITS TWO ENDPOINTS, not as one joined string. The first
# version of this audit required "5.80-6.39" verbatim and failed on two files
# that were perfectly correct -- HANDOVER puts the endpoints in separate table
# cells and o2_store_numbers writes "between 5.80 and 6.39 L". Requiring one
# house format would have meant rewording accurate prose to suit the checker.
# Endpoints catch the rot that matters: if the computation moves, the old
# numbers are still sitting in these files and every one of them fires.
_shortfall = (f"{abs(_total - _ow):.2f}", f"{abs(_total - _om):.2f}")
_span = (f"{_ow:.2f}", f"{_om:.2f}")
_pct = (f"{abs(_total / _ow - 1) * 100:.0f}", f"{abs(_total / _om - 1) * 100:.0f}")
_extra = (f"{(_ow - _total) * 10.0 * _c_art:.0f}",
          f"{(_om - _total) * 10.0 * _c_art:.0f}")
RESTATED = {
    'apnoea_core.py':      _shortfall + _span + _pct + _extra,
    'o2_store_numbers.py': _shortfall + _span + _pct + _extra,
    'sources_registry.py': _shortfall + _span + _pct,
    'SOURCES.md':          _shortfall + _span + _pct,
    'HANDOVER.md':         _shortfall + _span + _pct + _extra,
}

for _f, _wanted in sorted(RESTATED.items()):
    try:
        _txt = io.open(_f, encoding='utf-8').read()
    except OSError as _e:
        print(f"  FAIL {_f:<40} unreadable: {_e}")
        FAILED.append(f"{_f} unreadable")
        continue
    _miss = sorted({w for w in _wanted if w not in _txt})
    if _miss:
        FAILED.append(f"{_f} no longer carries {', '.join(_miss)}")
    print(f"  {'ok  ' if not _miss else 'FAIL'} {_f:<40}"
          f"{'all ' + str(len(set(_wanted))) + ' figures present' if not _miss else 'MISSING ' + ', '.join(_miss)}")
print()
print("   README.md is deliberately NOT in that list: it is GENERATED from")
print("   sources_registry.py by check_sources.py, which the pre-commit hook")
print("   already enforces, so it cannot drift independently.")
print()

if FAILED:
    print(f"{len(FAILED)} value(s) have drifted:")
    for f in FAILED:
        print(f"  - {f}")
    raise SystemExit(1)
print("Every Feldschuh & Enson number still reproduces from this commit.")
