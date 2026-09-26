# Copyright (c) 2026 A. M. B. Heard. All rights reserved.
# Unpublished research software. See LICENSE: use in any publication
# requires prior written permission. Cite as in CITATION.cff.
"""
apnoea_core.py — induction / apnoea model, stage 2.

STAGE 2 ADDITIONS
  * Closing capacity as a function of age AND body mass index.
  * Progressive airway closure when aerated lung volume falls below CC,
    followed by absorption collapse whose speed depends on the oxygen
    fraction of the trapped gas (pure O2 collapses fast; nitrogen splints).
  * Shunt as a state variable driven by collapsed fraction, with a perfusion
    gain > 1 because collapsed lung is dependent lung and takes more than its
    share of blood flow.
  * Hypoxic pulmonary vasoconstriction as a switchable first-order response,
    modelled at full (intravenous-anaesthesia) gain.
  * Analytic steady-state plateau calculator, checked against the dynamics.

DELIBERATE OMISSIONS, ALL CONSERVATIVE FOR THE DEVICE
  * Gas absorbed from newly collapsing units is discarded rather than credited
    to the blood. That gift is real (~350 mL O2 if 20% of a 2 L lung collapses
    at high FAO2) and ignoring it makes apnoeic oxygenation look slightly
    worse than it is.
  * Collapsed units never reopen: no recruitment without positive pressure,
    so the collapsed fraction ratchets.
  * Cardiac output and VO2 are fixed. This is the important one — see the
    caveat in plateau_sao2().

PARAMETER PROVENANCE
  The closing-capacity regression and the BMI-FRC relation are PLACEHOLDER
  parameterisations chosen to reproduce accepted qualitative behaviour (CC
  crosses supine FRC in middle age; FRC falls steeply with BMI). They are
  exposed as named constants and must be refitted against source data before
  any published result rests on them.
"""

from dataclasses import dataclass
import os as _os
import numpy as np
import bloodgas as bg


# ---------------------------------------------------------------------------
# Provenance. A full afternoon of results was once computed against a stale
# copy of this file sitting in a scratch directory, and only caught because one
# number looked odd. Any throwaway script should print provenance() so its
# output says which model produced it. Running a deliberately modified copy is
# fine -- the point is that the output should say so.
MODEL_FILE = _os.path.abspath(__file__)


def provenance():
    """One line naming the file this model was loaded from, and when it changed."""
    import datetime as _dt
    try:
        m = _dt.datetime.fromtimestamp(_os.path.getmtime(MODEL_FILE))
        stamp = m.strftime('%Y-%m-%d %H:%M')
    except OSError:
        stamp = 'unknown'
    return f"apnoea_core from {MODEL_FILE} (modified {stamp})"


PB = 760.0
PH2O = 47.0
PDRY = PB - PH2O
GASK = 863.0

# ---------------------------------------------------------------------------
# The floor on recoil pressure, and why it is where it is.
#
# There is no measurement of what a human lung does below about -20 cmH2O, and
# there probably never will be: the experiment is a sealed airway in a
# conscious subject past the point of tolerance. Everything below that edge is
# extrapolation of the recoil curve, and the model needs SOME terminator.
#
# RULING (A.H., 2026-09-20): put it at minus the systolic pressure. This is a
# convention, not a derivation, and is recorded as one. Its only defence is
# that it is the pressure scale at which the thorax stops being a gas
# compartment at all -- a transmural gradient that size cannot leave blood in
# the pulmonary vessels -- so nothing the gas model says past it is meaningful
# anyway.
#
# It replaces a -50 cmH2O floor that was ACTIVE from 361 s in a sealed run and
# was therefore shaping results. That floor was found on 2026-09-20 to clamp
# the REPORTED pressure while leaving the volume free, so the model returned a
# pressure its own recoil function contradicted by up to 21 cmH2O. At minus
# systolic the floor is INERT: see handover_numbers.py, which checks that no
# configuration tested comes within 75 cmH2O of it, and that results are
# identical to running with no floor at all. What actually stops the pressure
# falling is not a floor but the absorption gradient closing -- alveolar PO2
# reaching mixed venous PO2, at which point there is nothing left to absorb.
SBP_SUPINE = 110.0                            # mmHg, anaesthetised supine
P_COLLAPSE = -SBP_SUPINE * 1.35951            # = -149.55 cmH2O


# ---------------------------------------------------------------------------
@dataclass
class Patient:
    weight: float = 70.0
    height: float = 1.75
    age: float = 40.0
    hb: float = 15.0
    temp: float = 37.0
    be: float = 0.0

    # --- respiratory -------------------------------------------------------
    # Lung volumes scale with HEIGHT; adiposity only modifies them. BMI alone
    # cannot carry both, so height enters separately through a scaling factor
    # anchored to the standing predicted-FRC regression
    #     FRC(L) = 2.34*height(m) + 0.009*age - 1.09
    # normalised to a 1.75 m subject. Weight is still needed in its own right
    # for metabolic rate and cardiac output, which is why the model takes
    # height and weight rather than BMI.
    #
    # SOURCED 2026-09-25. IT IS QUANJER 1993, THE MEN'S EQUATION.
    #
    # Flagged 2026-09-21 by the pre-release source audit as "the largest
    # uncited lever in the model" -- no author, no journal, no year anywhere
    # in this repository. The paper was read at source on 2026-09-25:
    #
    #   Quanjer PH, Tammeling GJ, Cotes JE, Pedersen OF, Peslin R, Yernault
    #   JC. Lung volumes and forced ventilatory flows. Report Working Party
    #   Standardization of Lung Function Tests, European Community for Steel
    #   and Coal. Official Statement of the European Respiratory Society.
    #   Eur Respir J 1993;6 Suppl 16:5-40. PMID 8499054.
    #
    # Table 6, p.26, verbatim. H is STANDING HEIGHT in metres, A is age in
    # years, volumes in litres:
    #
    #   Men     FRC = 2.34H + 0.009A - 1.09     RSD 0.6
    #   Women   FRC = 2.24H + 0.001A - 1.00     RSD 0.50
    #   Men     TLC = 7.99H - 7.08              RSD 0.70
    #   Women   TLC = 6.60H - 5.79              RSD 0.60
    #
    # The men's FRC line is OUR THREE COEFFICIENTS EXACTLY. The lever is no
    # longer uncited. Four things follow, and three of them are defects:
    #
    #   * IT IS THE MEN'S EQUATION, AND THAT IS NOW A RULING, NOT AN
    #     ACCIDENT. RULED 2026-09-25: this is a MALE model. Quanjer's men's
    #     equations are used for every patient, deliberately, and a female
    #     patient is modelled as a male of the same height and age.
    #     THE COST IS REAL AND IS RECORDED RATHER THAN WAVED AT. Over
    #     1.55-1.75 m at age 45, Quanjer's own women's equations give:
    #         FRC  women / men   0.856 to 0.870   i.e. about 14% less
    #         TLC  women / men   0.834 to 0.837   i.e. about 16% less
    #     and the age term differs ninefold, 0.001 against 0.009, so a
    #     woman's FRC is very nearly age-flat where a man's is not.
    #     WHO THIS MISSES. Tokics' cohort was 3 women of 10; Pelosi's was
    #     SEVEN WOMEN TO ONE MAN per group -- and Pelosi is the curve
    #     shunt_base_eff is fitted to. So the anchors are not male cohorts,
    #     and a male model is being fitted through female-majority data.
    #     That is a known, ruled limitation and it is not small.
    #     Regenerated by handover_numbers.py.
    #   * QUANJER'S FRC IS MEASURED SEATED (paper, section 6.1: "Measurements
    #     are made with the subject seated upright; other postures should be
    #     noted, as they affect lung volumes"). frc_ref 2500 mL is SUPINE. So
    #     the model takes Quanjer's SHAPE through height_factor() and sets its
    #     own LEVEL. At 1.75 m and age 45 Quanjer predicts 3410 mL seated
    #     against our 2500 mL supine, a ratio of 0.73, which is the right
    #     sort of size for the supine fall but is not itself sourced.
    #   * the age term (0.009*age) is DELIBERATELY NOT IMPLEMENTED --
    #     RULED 2026-09-25, and it is a decision now, not an omission.
    #     height_factor() is height-only, so FRC is AGE-FLAT.
    #     Three things support leaving it out:
    #       - GUTIERREZ 2004, a second reference set read at source (n = 300
    #         men, six Canadian centres), has NO AGE TERM AT ALL in its
    #         men's FRC equation. It agrees with Quanjer to 0.2% at age 45
    #         and disagrees by +7.3% at 20 and -6.0% at 70, precisely
    #         because Quanjer's rises 14.1% across that span and its own is
    #         flat.
    #       - implementing it moves the CC=FRC crossover 55.0 -> 59.9 years,
    #         FURTHER from the literature's ~44.
    #       - so age-flat is what a second primary source predicts, not a
    #         convenience.
    #     THE CAVEAT IS KEPT: Gutierrez's FRC model is weak, r2 = 0.17, and a
    #     term can be absent from a regression because it is small OR because
    #     the data cannot see it. The two reference sets genuinely disagree
    #     and this ruling picks one. See SOURCES.md and handover_numbers.py.
    #   * THE EQUATIONS HAVE A RANGE AND WE LEAVE IT. Table 6 applies to ages
    #     18-70 ("between 18 and 25 yr substitute 25 yr") and was derived from
    #     heights 1.55-1.95 m in men, 1.45-1.80 m in women.
    #
    # AND IT SETTLES THE CONTRADICTION THE AUDIT COULD NOT. airway_scenario.html
    # tells the recipient the FRC-BMI relation is "parameterised, not fitted to
    # source data"; this block said "anchored to the standing predicted-FRC
    # regression". The second is the true one -- the height term is Quanjer's,
    # read from the page. The page's sentence is the one that is wrong.
    # MEASURED 2026-09-21 at the exact test_validation.py configurations,
    # dt=0.05 (regenerated by handover_numbers.py, so it cannot rot):
    #     frc_ref    Heard ctrl [244-314]   Toner sham [380-525]
    #       2200          249.5 ok               346.9 FAIL
    #       2500          289.2 ok               403.4 ok      <- shipped
    #       2800          329.8 FAIL             460.5 ok
    #     k_frc_bmi  Heard ctrl [244-314]
    #       0.0300        344.6 FAIL
    #       0.0417        289.2 ok               <- shipped
    #       0.0550        237.1 FAIL
    # A +-12% error in frc_ref takes one or other headline clinical benchmark
    # out of band, and a +-30% error in k_frc_bmi walks the obese benchmark out
    # in BOTH directions. For scale, Hufner 1.34->1.39 moves desaturation by
    # under 1%. Source this before release: see SOURCES.md.
    #
    # AND k_frc_bmi NOW HAS A BRACKET, 2026-09-25. Jones & Nzekwu 2006
    # (seated awake, n = 373) and Pelosi 1998 (supine anaesthetised) measure
    # the same decline, and Jones states that Pelosi's absolute effect is the
    # larger -- so the two should BRACKET a supine awake lung, which is what
    # frc_awake() is. Per cent of FRC lost per BMI unit:
    #     BMI     Jones    ours    Pelosi
    #      22      3.32    4.17     7.29    <- inside the bracket
    #      30      2.38    4.17     5.70    <- inside
    #      40      1.42    4.17     3.44    <- STEEPER THAN BOTH
    #      45      1.07    4.17     2.47    <- STEEPER THAN BOTH
    # We leave the bracket at BMI 36.70, and THE REASON IS STRUCTURAL: both
    # measured curves carry a non-zero offset (Jones +55.2 %pred, Pelosi
    # +460 mL) and so decay to a floor, because squeezing a chest with body
    # mass cannot drive the lung to nothing. Ours decays to ZERO and is
    # caught by the hard rv_eff() clamp instead.
    # The obese FRC VALUES still agree with Pelosi's helium to 11% across
    # BMI 22-50 -- but above BMI 37 that agreement is the FLOOR's doing and
    # not this parameter's. NOT CHANGED: it needs a ruling.
    # 2500 -> 2860, RULED 2026-09-26 with k_frc_bmi above. Solved jointly
    # from Watson & Pride's two supine cohorts; see k_frc_bmi.
    frc_ref: float = 2860.0      # mL supine awake at BMI 22, height 1.75
    # RE-ANCHORED ON DAMIA 1988, RULED 2026-09-26. Was 0.0417.
    #
    # Damia measured AWAKE SUPINE FRC by helium dilution in 18 morbidly obese
    # patients and reports every one's sex, height and age, so the fraction of
    # Quanjer's SEATED prediction can be computed PER PATIENT rather than from
    # a cohort mean. Regressed against BMI inside his own cohort:
    #
    #     ratio = -0.00083 * BMI + 0.7378
    #     r = -0.049,  t = -0.20 on 16 df   (|t| > 2.12 would be P<0.05)
    #
    # FLAT. Not "weakly falling" -- indistinguishable from a horizontal line.
    # That slope is equivalent to k = 0.0012 near his mean BMI, which is what
    # ships. It is kept as the measured value rather than rounded to zero
    # because 0.0012 is a number that was computed; 0 would be a number that
    # was chosen, and the difference between those two is the whole of this
    # project's method.
    #
    # THE TWO ENDS AGREE, which is why one flat fraction is defensible at all.
    # Damia's ratio extrapolated to BMI 22 is 0.720; the value this model
    # already used at BMI 22, from an entirely different route, is 0.697.
    #
    # WHAT THE OLD 0.0417 DID: it gave Damia's own 18 patients 0.13 to 0.42 of
    # predicted where 0.700 was measured. A factor of 35 in the decay constant.
    #
    # THE LIMIT OF THIS, stated because it will be forgotten otherwise: DAMIA
    # HAS NO LEAN PATIENTS. His range is BMI 37 to 67, so this is evidence for
    # flatness in the obese range plus agreement at one lean point, NOT a
    # measurement across the range. AND IT CONTRADICTS JONES, who measured 373
    # patients seated by plethysmography and found FRC falling to 62% of
    # predicted by BMI 50. Both cannot be right: 0.70 supine against 0.62
    # seated at the same BMI would make supine EXCEED seated. Ruled in Damia's
    # favour 2026-09-26; Watson & Pride would break the tie and has not been
    # obtained.
    # RE-SOLVED ON WATSON & PRIDE 2005, RULED 2026-09-26, and this PARTIALLY
    # SUPERSEDES the Damia re-anchor taken earlier the same day (0.0417 ->
    # 0.0012 -> 0.01074). Both rulings were right on their own evidence and
    # the reason they differ is worth keeping.
    #
    # Damia measured SUPINE FRC in 18 patients spanning BMI 37 to 67 and the
    # fraction of predicted is FLAT across that range (t = -0.20 on 16 df).
    # Watson & Pride measured SITTING AND SUPINE IN THE SAME SUBJECTS, two
    # cohorts by one method in one paper, at BMI 22.5 and 43.4 -- and supine
    # FRC FALLS, 2690 mL to 2220 mL. Neither contradicts the other: the curve
    # falls between BMI 22 and about 43 and is flat above it. That is an
    # OFFSET form, the same shape Jones and Pelosi both publish.
    #
    # A SINGLE EXPONENTIAL CANNOT DO BOTH, and this model's awake curve is a
    # single exponential with no offset. Solving its own form for the two
    # Watson & Pride points gives k = 0.01074 with frc_ref 2860 mL, exact on
    # both. The cost is that it keeps decaying past BMI 43 where Damia says
    # it should not: at BMI 48.4 it gives 2054 against Damia's 2180 (-5.8%)
    # and at 53.2 it gives 1951 against 2250 (-13.3%). Damia was NOT used in
    # the fit, so those are an independent check, and they are the residual
    # this form cannot remove.
    #
    # WHY THIS PAIR AND NOT DAMIA'S FLATNESS: Watson & Pride measure BOTH
    # POSTURES IN THE SAME SUBJECTS, which is the only direct measurement of
    # the quantity this parameter carries, and they span the lean end where
    # Damia has no patients at all. Giving the awake curve an offset would
    # honour both and is the right next change; it is not taken here because
    # it is a structural change and needs its own ruling.
    k_frc_bmi: float = 0.01074   # exponential decline of FRC per BMI unit
    frc_drop: float = 400.0      # mL lost at induction (ICSM 300-500)
    # Bed tilt, degrees. Positive is head-up / reverse Trendelenburg. Head-up
    # lifts the abdominal contents off the diaphragm, so it raises FRC and the
    # gain is larger the more abdomen there is to lift. Calibrated against
    # four randomised trials, all of which found roughly +30% safe apnoea time
    # for 20-25 degrees:
    #   Lane 2005, non-obese, 20 deg:      283 -> 386 s to SpO2 95%
    #   Ramkumar 2011, non-obese, 20 deg:  364 -> 452 s
    #   Altermatt 2005, BMI >35, sitting:  162 -> 214 s to SpO2 90%
    #   Dixon 2005, BMI >40, 25 deg:       +45 s, and 23% higher oxygen tension
    tilt_deg: float = 0.0        # 0 supine, 25 typical ramped, negative = head down
    # REVERTED 2026-09-26 to 0.0130 and +0.00015, THE SAME DAY THEY WERE
    # CHANGED. Both the change and the reversal are recorded because what was
    # learned in between is the most useful thing known about this parameter,
    # and neither value is right.
    #
    # WHAT WATSON & PRIDE 2005 MEASURE, and it is damning for these values.
    # Sitting and supine FRC IN THE SAME SUBJECTS is exactly tilt_factor at
    # about 90 degrees, with no cross-paper step and no inference:
    #
    #     control BMI 23.0    3.43 -> 2.69 L    tilt_factor(90) = 1.275
    #     obese   BMI 43.4    2.29 -> 2.22 L    tilt_factor(90) = 1.032
    #
    # THESE PARAMETERS GIVE 2.170 AND 2.418. The shipped model MORE THAN
    # DOUBLES FRC on sitting a patient up -- at BMI 43.7 it adds 2921 mL where
    # 70 mL is measured, a FACTOR OF 42 -- and its BMI term has the OPPOSITE
    # SIGN to the measurement: it makes head-up help MORE as BMI rises where
    # Watson & Pride measure it helping LESS, because an obese chest has
    # already lost the expiratory reserve there is to recover. Nothing had
    # ever tested this, because no benchmark ran at 90 degrees until the
    # Altermatt row was corrected on 2026-09-26.
    #
    # WHY THE MEASURED VALUES WERE NEVERTHELESS REVERTED. Solving on them
    # (0.003057 and -0.000147) made the model CLINICALLY FALSE: the obese
    # 90-degree row went to -3.5%, i.e. sitting a morbidly obese patient up
    # made them desaturate FASTER, because this model also carries a
    # cardiac-output cost for head-up tilt from Perilli 2003, and once the FRC
    # benefit shrinks to 3% that cost dominates. All four positioning trials
    # measure a 24-36% IMPROVEMENT. The three tilt rows went 29.6 -> 6.1,
    # 42.3 -> -0.1 and 140.5 -> -3.5 per cent.
    #
    # AND THE REASON IS A STATE MISMATCH, WHICH IS THIS PROJECT'S RECURRING
    # ERROR. WATSON & PRIDE MEASURED AWAKE, SPONTANEOUSLY BREATHING SUBJECTS
    # WITH INTACT MUSCLE TONE. tilt_factor acts on the ANAESTHETISED,
    # PARALYSED lung, where the chest wall is relaxed and the diaphragm rides
    # cranially, so posture may matter far more than it does awake. That is
    # the same error as vq_log_sd carrying an awake dispersion (0.70 against a
    # measured 0.95-1.04 anaesthetised), and it is what Rothen's Table II
    # avoids by having no awake column for Crs at all.
    #
    # SO BOTH VALUES ARE WRONG. These are wrong at 90 degrees by a factor of
    # two and wrong in the sign of their BMI term. The measured ones are wrong
    # in the state they were measured in, and are contradicted by every
    # clinical trial of the thing the model actually predicts.
    #
    # WHAT WOULD SETTLE IT: Lane 2005, Ramkumar 2011 and Dixon 2005 are the
    # ANAESTHETISED tilt measurements and this parameter should be solved
    # against them, not against an awake volume study. All three are orderable
    # -- citations in SOURCES.md -- and none is held. A saturating angle law
    # is needed as well: the form here is LINEAR, and Altermatt's own
    # discussion says "most of the change in FRC takes place between supine
    # and 60 degrees head-up position", so no linear law can be right at both
    # 20 and 90 degrees.
    # AWAKE TILT DATA IS EXCLUDED FROM THIS PARAMETER. RULED 2026-09-26:
    # "ignoring awake changes unless we have a conversion or 2 branches."
    # We have NEITHER, so Watson & Pride is not used here -- see the reverted
    # attempt above. tilt_factor() acts on the ANAESTHETISED, PARALYSED lung
    # and only anaesthetised measurements may anchor it.
    #
    # WHAT THAT LEAVES: ONE POINT. Valenza 2007 is the only anaesthetised
    # FRC-against-tilt measurement held -- 0.46 -> 0.85 L at 30 degrees, BMI
    # 42, tilt_factor 1.848 -- and one point cannot solve two parameters.
    # Holding tilt_gain_bmi and solving tilt_gain_lean on it gives 0.0257,
    # double the present value, which would put the lean 20-degree row near
    # +54% against a measured +24 to +36%. So Valenza alone cannot be adopted
    # either, and these values stand UNCHANGED and UNSOURCED.
    #
    # WHAT WOULD RESOLVE IT, and it is a short list: Lane 2005, Ramkumar 2011
    # and Dixon 2005 are anaesthetised tilt measurements at 20-25 degrees.
    # With Valenza's 30 degrees they would give two or three anaesthetised
    # angles and determine both parameters. None is held; all three are
    # orderable, with identifiers in SOURCES.md. Ask of each the question
    # Altermatt failed: WAS THE TILT MAINTAINED THROUGH THE APNOEA?
    tilt_gain_lean: float = 0.0130   # FRC fraction per degree at BMI 25
    tilt_gain_bmi: float = 0.00015   # extra per degree per BMI unit above 25
    vd_anat: float = 150.0
    vd_segments: int = 10
    # --- ventilation-perfusion distribution --------------------------------
    # The alveolar space is a bank of parallel compartments with log-normally
    # distributed V/Q, not one well-mixed box. This matters during apnoea for
    # a reason a single compartment cannot express: a unit with a small gas
    # volume relative to its perfusion exhausts its oxygen first and becomes
    # shunt, progressively, WITHOUT any airway closure. Aventilatory mass flow
    # then distributes by mechanics rather than by perfusion, so the mismatch
    # worsens as the apnoea goes on. ICSM uses 100 compartments.
    #
    # Raised from 20 to 80 on 2026-09-18. At 20 the model did something
    # PHYSICALLY IMPOSSIBLE: arterial CO2 fell 24 times during a clamped-airway
    # apnoea, reaching -41.7 mmHg/min, when CO2 has no route out of a sealed
    # lung. Compartments close one at a time as the lung shrinks, so with few
    # of them each closure steps the shunt and jolts arterial CO2. The falls
    # go 24 -> 8 -> 2 -> 0 at n_vq 20, 40, 60, 80; 80 is the first clean value.
    #
    # It buys correctness, NOT accuracy. The Stock 1-5 min slope is 4.75 at
    # n_vq 20 and 4.72 at 80, against a measured 3.4, and the a-A CO2 gap is
    # converged at ~8.4 mmHg from 60 upward. The disagreement is a property of
    # the model's physics, not of its discretisation, and no refinement will
    # remove it. Costs about 80% more runtime.
    n_vq: int = 80
    # DEAD PARAMETER, established 2026-09-23. It has NO EFFECT on any output,
    # sealed or patent. Swept 0.01 / 0.35 / 0.70 / 1.18 at the Stock reference
    # patient, every channel identical to five significant figures and the
    # desaturation time identical to 0.1 s. Grep confirms it: after the V/Q
    # category-error fix of 2026-09-22 this name appears nowhere in an
    # executable statement in this file -- only in its declaration and in two
    # docstrings, one of which asserted it was still used. model.js is the
    # same: vqDist(n, sd) ignores sd. Both implementations are dead in the
    # SAME way, which is why test_parity.py could never see it.
    #
    # KEPT, NOT DELETED, and the distinction matters. Removing it would change
    # the constructor signature that test_parity.py serialises and would read
    # as though V/Q dispersion had been considered and rejected. It has not
    # been: the model simply has no V/Q dispersion at present. Every one of
    # the n_vq compartments is identical at t=0 and they diverge only through
    # mechanisms -- absorption collapse per compartment, and the unwashed
    # fraction added the same day. That is what vq_distribution()'s own
    # docstring called "the right way to improve on this". The slider it fed
    # on airway_scenario.html has been removed, because a control that does
    # nothing is worse than no control.
    vq_log_sd: float = 0.70      # INERT. See above before using it.
    # Cardiogenic mixing. The beating heart displaces gas within the alveoli
    # and tracheobronchial tree with every systole, stirring the compartments
    # toward a common composition. Without it, parallel compartments are
    # sealed from one another and the low-V/Q units exhaust catastrophically
    # early; with it, the well-oxygenated units subsidise the poor ones. ICSM
    # added exactly this term ("cardiogenic gaseous oscillations within the
    # tracheobronchial tree and alveoli") when extending the Nottingham
    # simulator for apnoea. Time constant is not well characterised: at
    # 10-30 mL displaced per beat and 70 beats/min the stirred volume is of
    # the same order as the whole FRC each minute, so tau of order a minute.
    tau_mix: float = 45.0        # s, inter-compartmental mixing
    # Absorption atelectasis. Compartments share one airway, so pressure
    # largely equalises and inflow goes where gas is being absorbed. But
    # equalisation is not perfect: small airways have finite resistance, so a
    # unit whose uptake outruns its refill shrinks. Low V/Q units - small gas
    # volume for their blood flow - shrink first, reach their own closing
    # volume, and collapse. Nitrogen splints them; pure oxygen does not, which
    # is why this is an absorption phenomenon and why it is worse at high
    # FiO2. This fraction of the inflow is distributed by MECHANICS (volume
    # share) rather than by absorption, and is what allows units to shrink.
    inflow_mech_frac: float = 0.18
    cv_frac: float = 0.55        # a unit closes below this fraction of its
                                 # own starting volume
    # Reinflation partially recruits. A lung refilling after obstruction fills
    # toward its resting distribution, not its collapsed one, so the excess
    # inflow above the metabolic deficit is shared by ORIGINAL volume - that
    # is what lets a collapsed unit see gas again. Recruitment is incomplete
    # because passive reinflation cannot generate the transpulmonary pressure
    # a deliberate recruitment manoeuvre does; recruit_frac is how much of the
    # collapse is recoverable without positive pressure.
    recruit_frac: float = 0.65
    tau_recruit: float = 25.0    # s
    # COMPLIANCE -- how much the lungs and chest wall expand per unit of
    # pressure. Question answered against the paper 2026-09-21; the data
    # exists and we hold it.
    #
    # Rothen 1993 Table II, read off the page: anaesthetised adults,
    # Crs 75 (19) ml/cmH2O in group 1 (n=10) and 60 (15) in group 2 (n=6).
    # ONE CANDIDATE ESCAPE WAS TESTED AND FAILS. The paper calls it "total
    # dynamic compliance ... tidal volume divided by end-inspiratory airway
    # pressure", which sounds like it would sit BELOW a static compliance and
    # so excuse our higher value. It does not: the same Methods paragraph sets
    # "the end-inspiratory pause ... at 0.6 s and the end-expiratory pressure
    # was 0 cm H2O (= ZEEP)". A 0.6 s pause makes that pressure a plateau, and
    # ZEEP measures it from FRC. So it is a quasi-static compliance about FRC
    # -- the same quantity this parameter is -- and the comparison is
    # like-for-like.
    #
    # 85 sat ABOVE the mean of both groups. It was inside one SD of group 1
    # (75 + 19 = 94), so it was defensible rather than unsupported, but it was
    # not central and nothing in this file said so until 2026-09-21.
    #
    # RULED 2026-09-22: MOVED TO 75, Rothen's group 1 mean.
    #
    # Read the sweep before changing this again. Measured slope 3.4, band
    # 2.4-4.4:
    #     crs 60   slope 4.371   PASSES      PaO2 at 300 s 60.61
    #     crs 75   slope 4.601   fails       PaO2 at 300 s 60.86
    #     crs 85   slope 4.716   fails       PaO2 at 300 s 60.98
    #
    # 75 IS THE CHOICE THAT BUYS NOTHING. It is the better-powered of Rothen's
    # two measurements -- group 1 is n=10, group 2 is n=6 -- and it leaves the
    # failing benchmark still failing. 60 would have passed it, which is
    # precisely why 60 could not be taken without the CLAUDE.md "do not tune a
    # parameter to pass a benchmark" objection following it forever. Moving to
    # 75 is sourcing; moving to 60 would have been indistinguishable from
    # fitting, whatever the intent.
    #
    # Note what the sweep also shows: crs moves the CO2 slope by 7% across its
    # whole plausible range and moves PaO2 by 0.6%. It is a CO2-only lever.
    # It cannot be part of any explanation of the oxygen disagreement.
    crs: float = 75.0            # mL/cmH2O. Rothen 1993 group 1, n=10: 75 (19)
    # RESIDUAL VOLUME. Reference value at BMI 22; scaled for body size and
    # for BMI by rv_eff() below. It was a flat constant until 2026-09-23.
    rv: float = 1100.0           # mL, anaesthetised supine, AT BMI 22
    # Exponential decline of RV per BMI unit above 22, ANCHORED ON ONE
    # MEASUREMENT and no more than that.
    #
    # Reinius H et al, Anesthesiology 2009;111:979-87, n=30, BMI 45 (4),
    # measured end-expiratory lung volume by spiral CT after induction and
    # paralysis at ZEEP: 697 (157) mL, down from 1387 (581) awake.
    #
    # Holley 1967 shows expiratory reserve volume collapsing toward zero in
    # this population, and ERV = FRC - RV, so at BMI 45 anaesthetised
    # FRC ~= RV and Reinius's 697 mL is an UPPER BOUND on RV there. Taking
    # it as equality is the conservative choice: it gives the LARGEST RV
    # consistent with the measurement, hence the smallest change.
    #
    #     1100 * exp(-k * (45 - 22)) = 697  ->  k = 0.0198
    #
    # ONE POINT. It is anchored, not fitted -- nothing about a benchmark
    # entered the choice -- but a single measurement cannot establish the
    # SHAPE of the decline, only that a flat 1100 is wrong. Before this,
    # a BMI 45-47 patient was floored at RV 1100 while the measured FRC was
    # 697, i.e. the model insisted on more gas than the CT could find.
    #
    # A SECOND MEASUREMENT ARRIVED 2026-09-25 AND IT DISAGREES. Jones &
    # Nzekwu, Chest 2006;130(3):827-33, n = 373, measured RV seated and awake
    # by body plethysmography: it falls 0.63% per BMI unit against our 1.98%,
    # so WE ARE 3.14x STEEPER. This is measurement against measurement, not
    # guess against measurement, and it is NOT resolved. Reasons for care:
    # plethysmography counts gas behind closed airways while CT counts
    # aerated lung, so in an obese chest Jones should read the higher of the
    # two -- which is the direction of the gap; he is seated awake and
    # Reinius supine anaesthetised; and his RV is itself derived as TLC - VC
    # on a plethysmographic FRC, not measured.
    #
    # AND IT IS NOW THE PARAMETER THAT SETS OBESE FRC. Above about BMI 37
    # frc_anaes() sits on this floor rather than on the BMI term, so
    # k_rv_bmi -- not k_frc_bmi -- is what obese lung volume actually rests
    # on. Adopting Jones's value would raise a BMI 45 anaesthetised FRC by
    # 32% and slow desaturation further, where Heard's obese control is
    # already too slow. NOT DONE: it needs a ruling, not an edit.
    # See SOURCES.md and handover_numbers.py.
    k_rv_bmi: float = 0.0198
    stiff_below_rv: float = 0.15 # compliance retained below RV
    p_collapse: float = P_COLLAPSE   # cmH2O floor on recoil. Minus the
                                 # systolic pressure, by ruling: see
                                 # SBP_SUPINE above for why, and why it is
                                 # deliberately far enough out to be inert.
    # BASELINE SHUNT FROM AIRWAY CLOSURE -- RE-KEYED OFF BMI 2026-09-24.
    #
    # WHAT WAS WRONG ORIGINALLY. shunt_base was a flat 0.05 for every patient,
    # and at t=0 on a patent airway the total shunt IS shunt_base -- the
    # collapse machinery only acts during apnoea. A BMI 45 patient and a BMI
    # 22 patient were given IDENTICAL gas exchange. That is the defect the
    # obese-shunt branch was forked to find.
    #
    # TWO FIXES CAME BEFORE THIS ONE AND BOTH WERE KEYED ON BMI.
    # First a broken line -- flat to BMI 24, a 10.9% plateau from BMI 30 --
    # whose knee came from Hedenstierna 2020's finding that ATELECTASIS
    # plateaus above BMI 30. Pelosi 1998 showed there is no knee, and that
    # both anchors sat in the one interval where the broken line happened to
    # be right. Then Pelosi's own curve, as a quadratic in BMI. It fitted his
    # regression to 0.27 percentage points and STILL could not answer
    # Perilli 2003: head-up tilt raises that patient's FRC 585 -> 840 mL and
    # a function of BMI does not move one hundredth of a percent.
    #
    # THE QUANTITY, NOT THE PROXY. What closes an airway is lung volume
    # falling below closing capacity, and what matters is how far below
    # RELATIVE TO the volume that is left -- 1600 mL below CC is trivial in a
    # 3 L lung and catastrophic in a 700 mL one. That is
    #
    #     x = (cc - v_lung) / v_lung
    #
    # evaluated here at frc_anaes(), the volume the apnoea starts from. It is
    # the SAME quantity the runtime collapse term uses (closed_target) and
    # the same one unwashed_fraction() uses at the awake volume; all three
    # now go through closure_x(). BMI enters only through FRC and closing
    # capacity, where it belongs.
    #
    # THE LAW:
    #
    #     shunt = shunt_anat + (1 - shunt_anat) * x / (x + shunt_cc_k)
    #
    # ITS TWO LIMITS ARE PHYSICS, NOT FIT. At x = 0 -- a lung sitting at or
    # above its closing capacity -- the shunt is shunt_anat, the bronchial
    # and thebesian drainage that bypasses the alveoli in every healthy lung.
    # As v_lung -> 0 the whole perfused bed is closed and x -> infinity, so
    # the shunt tends to 1. THE ASYMPTOTE IS THEREFORE NOT A FREE PARAMETER.
    # That matters because Pelosi's range does not identify one: fitted
    # freely it runs to 87% with the fit still improving, and fixing it
    # anywhere between 60% and 100% moves the worst residual by 0.10
    # percentage points. Only the RATIO shunt_cc_k to the asymptote is
    # identified over BMI 20-55. The saturation is asserted from the limit,
    # not measured, and must not be quoted as a finding.
    #
    # TWO FITTED PARAMETERS WHERE THE QUADRATIC HAD THREE, fitted to the SAME
    # Pelosi inversion, at his cohort's height 1.64 m and age 52, over BMI
    # 20-55 in half-unit steps. shunt_floor is gone with the quadratic: the
    # law cannot return less than shunt_anat, so a 2% floor could never bind.
    #
    # AND IT FITS PELOSI WORSE: worst residual 0.49 percentage points against
    # the quadratic's 0.27, rms 0.23 against 0.094. That is the cost, it is
    # recorded rather than compensated, and no parameter was reached for to
    # hide it. What it buys is a shunt that responds to what actually closes
    # airways -- head-up tilt, age, the induction FRC drop, height -- none of
    # which a function of BMI can see.
    #
    # WHAT IS STILL WEAK:
    #   * the inversion runs Pelosi's blood gas through THIS model's cardiac
    #     output, and ours is about 18% above the only measured obese value
    #     we have (Perilli's 4.9 L/min). Dantzker 1980 makes that matter:
    #     depressing cardiac output is itself a mechanism of shunt reduction.
    #   * closing_capacity() is a PLACEHOLDER REGRESSION -- see the block
    #     below, which says so. The shunt now rests on it DIRECTLY rather
    #     than through a fitted curve, so cc_at_20, cc_per_year and
    #     cc_per_bmi became load-bearing today.
    #     CORRECTED 2026-09-24: an earlier version of this note said none of
    #     them is sourced, and that is WRONG. The quantity has a source and
    #     it was read at source on 2026-09-23 -- Buist & Ross 1973, combined
    #     regression CC/TLC (%) = 0.525*age + 14.348. These three constants
    #     are unsourced VALUES that disagree with it, which is a different
    #     and smaller problem. What blocks the correction is that Buist gives
    #     CC as a PERCENTAGE OF TLC and this model has no TLC. See the
    #     closing-capacity block below and handover_numbers.py.
    #   * Pelosi's cohort is 1 man to 7 women per group, aged 40-75, at
    #     FiO2 0.40. Reinius, Valenza and Perilli differ in all three.
    #   * THE SAME CLOSURE IS NOW COUNTED TWICE, and re-keying is what made
    #     it visible. closed_target applies this same x at the CURRENT lung
    #     volume and grows `collapsed` from ZERO toward it, so the closure
    #     already present at induction -- which is exactly what this baseline
    #     is -- gets added a second time as the apnoea runs. The two terms
    #     were different functions of different drivers until today, which is
    #     why it was never visible. NOT FIXED HERE: the coherent form is one
    #     law with `collapsed` initialised to its induction value, and that
    #     changes the collapse kinetics and every benchmark. See HANDOVER.
    shunt_anat: float = 0.03225  # bronchial + thebesian: the x = 0 limit
    shunt_cc_k: float = 36.16    # half-saturation in x; see the note above
                                 # on why only its ratio to 1 is identified
    # Ceiling: a numerical guard only. It binds at x = 23 -- a lung at a
    # twenty-fourth of its closing capacity -- which no timeline reaches.
    shunt_ceiling: float = 0.40

    # --- closing capacity (PLACEHOLDER VALUES, BUT THE SOURCE IS KNOWN) ----
    #
    # THE SOURCE WAS READ AT SOURCE 2026-09-23. Buist AS, Ross BB, Am Rev
    # Respir Dis 1973;107(5):744-52, combined regression, quoted verbatim in
    # SOURCES.md:
    #
    #     CC/TLC (per cent) = 0.525 * age(years) + 14.348 +- 4.34
    #
    # So this block is not an unsourced QUANTITY, it is three unsourced
    # VALUES that disagree with a source we hold. Those are different sizes
    # of problem and the distinction has already been got wrong once.
    #
    # THE THREE DISAGREEMENTS, argued in full in SOURCES.md:
    #   * the age slope is about a third too shallow (20 mL/yr against
    #     0.525% of TLC per year, which is 30-35 mL/yr at TLC 6-7 L);
    #   * the intercept starts too high, so our curve crosses theirs near 45;
    #   * cc_per_bmi has no support at all. Both sources attribute obese
    #     airway closure to a REDUCED FRC, and BJA Education 2022 states
    #     positively that obesity leaves CC unchanged. Our model opens the
    #     CC-FRC gap from both ends, and roughly 45% of our obese closure
    #     comes from this term.
    #
    # THE CROSSOVER TEST, which has no free parameter in it: both sources put
    # CC = FRC at ~44 years supine. Ours does it at 55.0. Restoring the age
    # term that height_factor() drops makes it 59.9, i.e. WORSE, so the error
    # is not all in this block. Regenerated by handover_numbers.py.
    #
    # THE BLOCKER IS GONE AS OF 2026-09-25: QUANJER WAS READ AT SOURCE.
    # Buist gives CC as a PERCENTAGE OF TLC and this model had no TLC.
    # Quanjer 1993 Table 6 supplies one (see the FRC block above for the
    # citation), with NO AGE TERM -- which confirms from a primary source the
    # claim SOURCES.md had only reasoned to, that TLC is age-stable:
    #
    #   Men    TLC = 7.99H - 7.08   RSD 0.70      H = standing height, m
    #   Women  TLC = 6.60H - 5.79   RSD 0.60
    #
    # AND THE CROSSOVER TEST PREDICTED IT BEFORE THE PAPER WAS READ. Solving
    # the published 44-year supine CC=FRC crossover for TLC gave 6676 mL at
    # 1.75 m. Quanjer's men's equation gives 6902 mL. THEY AGREE TO 3.3%, on
    # a quantity this model did not contain, from a paper nobody here had
    # read. That is the strongest independent check this block has ever had.
    #
    # STILL NOT APPLIED, because it is a redesign and not a parameter edit:
    # cc_at_20/cc_per_year/cc_per_bmi would be replaced by a predicted TLC
    # times Buist's percentage, and cc_per_bmi would go entirely. At Quanjer's
    # TLC the obese shunt FALLS -- Perilli 12.53 -> 9.11%, Reinius 11.47 ->
    # 9.31%, Pelosi BMI 45 12.09 -> 10.22% -- so it moves every benchmark and
    # needs a ruling. See handover_numbers.py, which now regenerates all of it.
    # BUIST & ROSS ON A PREDICTED TLC -- ruled 2026-09-26. See
    # closing_capacity(). These two are the published regression, not a fit:
    #     CC/TLC (per cent) = 0.525 * age + 14.348 +- 4.34
    cc_buist_slope: float = 0.525      # per cent of TLC per year of age
    cc_buist_intercept: float = 14.348  # per cent of TLC at age 0
    # RULED OFF 2026-09-26. Jones & Nzekwu measured TLC falling 0.50 per cent
    # of predicted per BMI unit, and Quanjer's TLC has no weight term, so
    # applying it is defensible -- but it is a SECOND source layered on a
    # first, and the ruling is to take Buist on Quanjer plain. With this off,
    # closing capacity is INDEPENDENT OF BMI, which is what both Milic-Emili
    # and BJA Education say. Obesity reaches closure by lowering FRC, and by
    # nothing else.
    cc_tlc_bmi: bool = False           # Jones's TLC-vs-BMI correction
    # RETIRED 2026-09-26, kept only so cc_legacy=True can reproduce the old
    # curve for the cost table. cc_per_bmi in particular had NO support: both
    # Milic-Emili and BJA Education say obesity does not raise closing
    # capacity, and it is now gone rather than re-fitted.
    # NOT a dataclass field, deliberately: an annotated field's default is
    # baked into __init__, so a subclass setting it is silently overwritten.
    # That cost a measurement today. As a plain class attribute a subclass CAN
    # flip it, which is how variant_cost.py reaches the retired curve.
    cc_legacy = False
    cc_at_20: float = 1800.0
    cc_per_year: float = 20.0
    cc_per_bmi: float = 45.0
    cc_k: float = 1.5            # half-saturation of the closure response
    max_closed: float = 0.25

    # --- collapse kinetics -------------------------------------------------
    tau_collapse_o2: float = 60.0
    tau_collapse_air: float = 900.0
    perfusion_gain: float = 1.2

    # --- hypoxic pulmonary vasoconstriction --------------------------------
    # --- hypoxic pulmonary vasoconstriction --------------------------------
    # Dose-response from Marshall BE, Clarke WR, Costarino AT, Chen L,
    # Miller F, Marshall C. "The dose-response relationship for hypoxic
    # pulmonary vasoconstriction." Respir Physiol 1994;96(3):231-47
    # (canine, independently perfused lung).
    # AUTHOR LIST CORRECTED 2026-09-22. This file previously read "Marshall
    # BE, Marshall C, Frasch F, Hanson CW" -- those four authors wrote a
    # DIFFERENT 1994 paper (Intensive Care Med 20:291-7 and 20:379-89) and
    # the two citations had been merged. The volume and pages were always
    # right, so the equations below are sourced to the right paper; only the
    # attribution was wrong. Search-resolved, NOT read -- see SOURCES.md.
    #     PSO2    = PvO2^0.41 * PAO2^0.59
    #     %PVRmax = PSO2^-2.616 / (6.683e-5 + PSO2^-2.616)   half-max 39.4 mmHg
    #     PVR at maximum = 3.15 (0.18) x its value on 100% oxygen
    # Diversion follows from two parallel beds at fixed total flow:
    #     f_hpv = f0 / (f0 + k(1-f0))
    # A collapsed unit holds no gas, so its PAO2 equals mixed venous and PSO2
    # collapses to PvO2. Atelectatic lung is therefore already about half
    # maximally constricted at a normal venous PO2, and constricts further as
    # the patient desaturates. That negative feedback is the reason to model
    # this properly rather than as a fixed fraction.
    hpv_enabled: bool = True
    hpv_pvr_max: float = 3.15    # PVR multiplier at maximal response
    tau_hpv: float = 250.0       # s, phase-1 onset
    hpv_co2_gain: float = 0.0    # per mmHg PaCO2 above 40. Additive rather
                                 # than synergistic in humans (Balanos et al),
                                 # but UNQUANTIFIED here - off by default.

    # --- metabolic ---------------------------------------------------------
    # vo2_ref IS CONFIRMED BY A HELD SOURCE, 2026-09-26. Farmery & Roe 1996
    # (Br J Anaesth 76:284-91, read in full 2026-09-20 and cited NOWHERE until
    # now) set their standard adult at "VO2 = 0.25 litre min-1". That is this
    # value exactly. SOURCES.md recorded them as quoting Nunn's 0.20 L/min;
    # the paper does not say that, and the audit line is corrected.
    #
    # THE SUBTRACTION BELOW IS THE PROBLEM, AND IT IS STILL UNCITED. Their
    # Table 1 gives a 127 kg OBESE adult 0.378 L/min where this model gives
    # 268 -- 41% LOW, against only 8% low at their 70 kg standard. THE DEFICIT
    # GROWS WITH WEIGHT, which is precisely what makes this model too generous
    # to obese patients in every apnoea row.
    #
    # WHY, STRUCTURALLY: Farmery & Roe scale on TOTAL body weight -- their five
    # Table 1 rows fit weight^0.69, and 250*(127/70)^0.69 = 378 to the digit --
    # while vo2_anaes() scales the positive term on ADJUSTED body weight and
    # then subtracts 0.27 * TOTAL weight. Two different weight bases pulling
    # opposite ways. Removing the subtraction alone gives 304 at 127 kg, still
    # 20% short, so the adjusted-weight basis is itself part of it.
    #
    # NOT CHANGED HERE. VO2 is the dominant lever on every apnoea time -- +20%
    # closes the entire Heard discrepancy on its own -- so it moves nothing
    # without a ruling.
    #
    # Two further Table 1 comparisons, recorded because they came free:
    #   ALVEOLAR VOLUME AGREES. 2328 against their 2500 at 70 kg, 950 against
    #   their 1000 at 127 kg. FRC is not the defect.
    #   CARDIAC OUTPUT IS ~25% LOW AT BOTH ENDS. 3.75 against 5.00, 5.86
    #   against 7.56. A THIRD independent source after Gunnarsson (5.3
    #   measured, model 3.95) and Tokics.
    vo2_ref: float = 250.0
    vo2_drop_per_kg: float = 0.27
    rq: float = 0.8

    # --- circulation -------------------------------------------------------
    # Cardiac output is no longer fixed. During apnoeic oxygenation it RISES,
    # driven by hypercapnic sympathetic stimulation. Measured directly in the
    # relevant population: 91 anaesthetised, paralysed, apnoeic patients on
    # 100% oxygen, continuous cardiac output, arterial gases every 2 min --
    # median CO 5.0 (IQR 4.5-6.0) rising to 6.5 (5.7-7.5) L/min by 15 min with
    # PaCO2 climbing 2.1 mmHg/min (Sci Rep 2024, PMC10864331). That is +30% CO
    # for +31 mmHg PaCO2: 0.97% of baseline per mmHg.
    #
    # The coefficient is fitted to the NET observed change, so any direct
    # acidotic myocardial depression across that range is already inside it.
    # Do not add a separate depression term below PaCO2 ~145 or it is double
    # counted. A separate series found cardiac output still elevated at pH 6.9
    # after 40 min of apnoeic oxygenation (J Anesth 2013), so depression does
    # not dominate anywhere in the range this model is used.
    co_ref: float = 5.0
    co_drop_frac: float = 0.25
    # HEAD-UP TILT COSTS CARDIAC OUTPUT. Added 2026-09-24 by ruling.
    #
    # Until now tilt was a PURE BENEFIT in this model: tilt_factor() raised
    # FRC and nothing anywhere paid for it. That is why the model took too
    # LITTLE extra lung volume from tilt (+46.6% against Valenza 2007's
    # measured +84.8% at 30 degrees) and still produced too MUCH extra apnoea
    # time (+51.1% against the positioning trials' ~+30%). A cost the model
    # does not pay is exactly the shape of thing that explains that.
    #
    # THE MEASUREMENT. Perilli 2003 (Obes Surg 13:605-9, n=20, BMI 48.1 (8.2),
    # cardiac output by oesophageal echo-Doppler) compares phase 4 with phase
    # 5 -- identical but for position, both with subcostal retractors and
    # both without PEEP:
    #     supine            4.9 (0.9) L/min
    #     30 deg head-up    4.0 (0.8) L/min    P < 0.05
    # That is -18.4%, so 0.184/30 = 0.00612 per degree.
    #
    # WHY IT SHORTENS APNOEA RATHER THAN LENGTHENING IT. Oxygen leaves the
    # lung at the metabolic rate whatever the cardiac output, so the LUNG
    # store is not spared by a lower output. What a lower output does is
    # widen the arteriovenous difference, which drops mixed venous oxygen,
    # which the shunt admixes into the artery. With a 10.9% obese shunt that
    # is a real cost.
    #
    # WHAT IS WEAK:
    #   * ONE study, ONE cohort, at BMI 48.1, during OPEN abdominal surgery
    #     with retractors in place. Whether the effect is the same without a
    #     laparotomy is not measured.
    #   * assumed LINEAR in angle from a single 30-degree measurement, and
    #     assumed independent of BMI, neither of which anyone has checked.
    #     The venous-return effect presumably depends on abdominal mass.
    #   * HEAD-DOWN IS EXTRAPOLATION. Negative tilt_deg gives a factor above
    #     1, which is the right direction -- Trendelenburg raises venous
    #     return -- but no measurement here bounds it.
    co_tilt_gain: float = 0.00612   # fractional CO loss per degree head-up
    # --- the circulation's answer to anaemia ------------------------------
    # Below a threshold haemoglobin the resting cardiac output rises to
    # defend oxygen delivery. Two measured anchors fix this, and nothing
    # here is fitted to anything of ours:
    #
    #   Varat, Adolph & Fowler, Am Heart J 1972;83:415-26 -- chronic anaemia
    #   "usually increases the cardiac output when the haemoglobin level is
    #   7 g/dL or less". Above 7, no rise: hence the threshold.
    #
    #   Hemodynamic Effects of Chronic Severe Anemia, Circulation
    #   1963;28:346 -- Hb 4.0-6.5 (mean 4.5) gave a cardiac index of
    #   6.3 L/min/m2 against a normal ~3.2, so very nearly double.
    #
    # A power law through those two points, (thresh/hb)**exp, needs
    # exp = ln(1.97)/ln(7/4.5) = 1.535. It is EXACTLY 1.0 at and above the
    # threshold, so every existing benchmark -- all of which run Hb 14-15 --
    # is untouched by this. That is deliberate: a change to the circulation
    # that silently moved the oxygenation results would be very hard to
    # trust.
    hb_co_threshold: float = 7.0    # g/dL, below which CO starts to rise
    hb_co_exp: float = 1.535        # fitted to the two anchors above
    # Whether this patient's anaemia is CHRONIC. See anaemia_co_factor():
    # Roy 1963 measured chronic hookworm anaemia and nothing licenses
    # extending it to acute blood loss. True is the optimistic default.
    anaemia_chronic: bool = True
    # HOW OFTEN THE BLOOD GAS IS INVERTED, seconds. This was a hardcoded
    # 1.0 until 2026-09-25 and is the source of the SaO2 staircase: PaO2,
    # PaCO2, pH and SaO2 all come from one inversion that was held for a
    # whole simulated second whatever dt was, so the apparent rate of fall
    # was an artefact of the grid and scaled as 1/dt. See HANDOVER.md.
    # RULED 2026-09-25: 0.0 means INVERT EVERY STEP, and that is the default.
    # Any positive value is an interval in seconds, kept only so the old
    # behaviour and the cost curve can be reproduced. The defect was never
    # the 1.0 as such -- it was that the interval did NOT scale with dt, so
    # halving dt doubled the apparent rate of fall. At 0.0 it cannot.
    bg_invert_interval: float = 0.0
    hb_co_max: float = 3.0          # ceiling; the heart cannot do better
    # The measured +30% cardiac output over +31 mmHg PaCO2 is the NET of a
    # rate and a stroke volume response, and the source does not split them.
    # Applying the whole coefficient to rate and then adding a stroke volume
    # response on top double counts it. Split evenly instead: two equal gains
    # of 0.0045 multiply to the measured 1.30 at the observed PaCO2 rise.
    co_co2_gain: float = 0.0045  # fraction of baseline per mmHg PaCO2 over 40
    co_max_factor: float = 2.0   # ceiling; beyond PaCO2 ~145 this extrapolates
    # Hypoxaemic depression is real but has no usable coefficient in this
    # population, and only bites below the range where the rest of the model
    # is defensible. OFF by default; switch on to explore its effect.
    co_hypoxia_enabled: bool = False
    co_hypoxia_sao2_50: float = 0.45
    co_hypoxia_n: float = 6.0
    # --- heart rate --------------------------------------------------------
    # Stroke volume is held constant, so heart rate tracks the cardiac output
    # response: hypercapnia drives both up together. That part inherits the
    # measured CO coefficient and is as well grounded as it is.
    # The bradycardia limb is NOT. Severe hypoxaemia certainly produces
    # bradycardia and then asystole in anaesthetised patients, but I have no
    # usable coefficient for the threshold or the slope in this population.
    # The sigmoid below is chosen to look right, not fitted to anything.
    # Treat the rate it shows below SaO2 ~70% as illustrative only.
    hr_base: float = 70.0        # beats/min after induction
    hr_brady_sao2_50: float = 0.45   # SaO2 at which rate is halved
    hr_brady_n: float = 4.0
    # Terminal sequence. Below the trigger saturation, sustained for the
    # trigger delay, the rhythm degenerates to an escape rate and then stops:
    # three beats in ten seconds, then two, then one, then asystole.
    # Timings chosen for teaching, not measured. Recovery above the trigger
    # saturation resets the sequence at any point before asystole.
    hr_term_sao2: float = 0.40   # fraction
    hr_term_delay: float = 20.0  # s below trigger before the sequence starts
    hr_term_rates: tuple = (18.0, 12.0, 6.0)   # beats/min, 10 s each

    # --- pressures ---------------------------------------------------------
    # Stroke volume is NOT constant. Two couplings, both measured, neither
    # with a usable coefficient, so the gains below are set to reproduce the
    # reported magnitudes rather than taken from a paper:
    #   hypercapnia raises stroke volume (Chest: HR, SV, CO and MAP all rose
    #     with hypercapnia in humans)
    #   a strongly negative intrathoracic pressure lowers it - the Muller
    #     effect, where the ventricle must eject against atmospheric pressure
    #     while surrounded by a vacuum. In sedated pigs, obstructed apnoea on
    #     room air dropped cardiac output 2.97 -> 2.39 L/min while MAP rose
    #     103 -> 124 Torr (J Appl Physiol 1998;84:1289).
    sv_co2_gain: float = 0.0045   # per mmHg PaCO2 over 40; see above
    # The Muller coupling is kept deliberately small, and READ THIS BEFORE
    # TOUCHING IT. The figures quoted above are that study's ROOM-AIR arm. Its
    # OXYGEN arm reached the same -31 Torr (-42 cmH2O) intrathoracic pressure
    # with oxygenation preserved and found stroke volume and cardiac output
    # UNCHANGED, so the fall in the room-air arm is hypoxaemia and its
    # autonomic consequences, not the mechanical Muller effect. Our patient is
    # the oxygenated one. The mechanical coupling the source supports is
    # therefore about zero by ITS OWN CITATION. The NUMBER is nonetheless too
    # SMALL, not too large: two human studies pair intrathoracic pressure with
    # stroke volume in normoxic subjects and both exceed us. Wright 2023
    # (AJP-Heart 325:H1235) n=19, ITP -30 cmH2O for 15 s, SV 70 -> 60 mL, i.e.
    # 0.00476 per cmH2O; Condos 1987 (Circulation 76:1020) n=10 with
    # micromanometry, SV 83 -> 74 at an intrathoracic swing of -24 mmHg, i.e.
    # 0.0033. We are conservative by 1.3-1.9x. The open question is duration:
    # a Mueller manoeuvre is 5-15 s and ours develops over minutes, though
    # Wright's effect grows from 5 s to 15 s rather than fading.
    # Raising it to the human value moves the Stock slope only 4.35 -> 4.24,
    # so this term is nearly inert on the Moreault/Stock conflict despite what
    # HANDOVER's "Known disagreement" section used to claim.
    # See protocol/evidence.md.
    # It is retained anyway, because deleting it in isolation makes the fit
    # WORSE: the Stock obstructed slope goes 4.35 -> 4.51 against a measured
    # 3.4, and `stiff_below_rv` is coupled to it through the same pathway. See
    # "Known disagreement" in HANDOVER.md. Do not remove this on its own.
    # (The pig magnitude would not transfer in any case: those animals were
    # sedated and making inspiratory efforts against a closed airway, which
    # generates large swings actively, where ours is paralysed and the
    # subatmospheric pressure develops slowly from gas absorption alone.)
    sv_itp_gain: float = 0.0025   # per cmH2O of subatmospheric alveolar pressure
    itp_fraction: float = 0.60    # alveolar pressure transmitted to the pleura
    svr_base: float = 18.0        # mmHg per L/min (~1440 dyne.s.cm-5)
    # Systemic resistance FALLS during apnoeic oxygenation - the direct
    # vasodilator action of CO2 on arterioles outweighs central sympathetic
    # vasoconstriction (J Anesth 2013 reports SVR reduced). It has to: if
    # cardiac output rises 30% and MAP rises only modestly, resistance must
    # have dropped. A positive gain here compounds with the CO rise and
    # produces impossible pressures.
    svr_co2_gain: float = -0.0045  # per mmHg PaCO2 over 40
    svr_floor: float = 0.40        # fraction of baseline
    # Every response above is bounded at this PaCO2. Beyond it there is no
    # human data in this population, and in reality acidotic myocardial
    # depression takes over and all of these reverse. The model holds them
    # flat instead of extrapolating, and is simply not valid past here.
    co2_response_cap: float = 150.0
    pvr_base: float = 1.40        # mmHg per L/min (~112 dyne.s.cm-5)
    pcwp: float = 8.0             # mmHg, left atrial pressure
    v_art: float = 1.0
    v_ven: float = 2.0
    v_tis_o2: float = 1.5
    pools: int = 3

    # --- body CO2 stores ---------------------------------------------------
    # Tuned to the MODERN measured arterial rate of rise, ~2.1 mmHg/min
    # (Sci Rep 2024, n=91; Gustafsson 0.24 kPa/min; Toner 0.30 kPa/min
    # transcutaneous). Historical series report 3.0-3.4 mmHg/min arterial
    # (Frumin 1959; Eger & Severinghaus; Stock).
    #
    # These are UNCHANGED from the original fit, deliberately. The obstructed
    # rate of rise was out by a factor of twelve, and it was tempting to
    # correct it here: halving the fast store does hit Stock's 3.4 mmHg/min.
    # It was the wrong lever. The error was three defects in the gas-exchange
    # code (see the per-compartment pH note and the open-fraction perfusion
    # note below), and with those fixed these values give 12.2 mmHg in the
    # first minute against Stock's 12, and 2.4 mmHg/min patent against the
    # measured 2.1, with nothing refitted. Retuning the stores would have
    # buried three real bugs under a parameter that then no longer meant what
    # its name says.
    v_tis_co2_fast: float = 22.0
    v_tis_co2_slow: float = 140.0
    k_co2_slow: float = 0.80

    # --- nitrogen: three perfusion-limited compartments --------------------
    # With no expiration, nitrogen returning from tissue accumulates in the
    # alveolus permanently and displaces oxygen. This is the process that
    # ultimately limits very long apnoeic oxygenation, and it can only be got
    # right with realistic compartment time constants: the vessel-rich group
    # empties in ~3 min, muscle in ~30 min, fat in ~4 h. A single lumped store
    # makes the whole reservoir instantly available and is badly pessimistic.
    n2_pt_init: float = 573.0    # mmHg, air-equilibrated tissue N2 tension
    lambda_n2: float = 1.895e-5  # mL N2 / mL blood / mmHg (Ostwald 0.0144)
    lambda_fat_ratio: float = 5.0    # N2 is ~5x more soluble in fat
    q_frac: tuple = (0.75, 0.18, 0.07)   # CO fraction: vessel-rich, muscle, fat

    # --- monitoring --------------------------------------------------------
    spo2_delay: float = 25.0
    spo2_tau: float = 8.0

    def bmi(self):
        return self.weight / self.height ** 2

    def scale(self):
        return (self.weight / 70.0) ** 0.75

    def ibw(self):
        """Devine ideal body weight, kg (male form)."""
        return 50.0 + 2.3 * (self.height / 0.0254 - 60.0)

    def abw(self):
        """Adjusted body weight: fat is metabolically quiet, so oxygen
        consumption tracks lean mass far more closely than total mass.
        Scaling VO2 on total weight overstates it badly in obesity."""
        return self.ibw() + 0.4 * max(0.0, self.weight - self.ibw())

    def height_factor(self):
        return (2.34 * self.height - 1.09) / (2.34 * 1.75 - 1.09)

    def tilt_factor(self):
        g = self.tilt_gain_lean + self.tilt_gain_bmi * max(0.0, self.bmi() - 25.0)
        return max(0.45, 1.0 + self.tilt_deg * g)

    # FRC CANNOT BE LESS THAN RESIDUAL VOLUME. Floor added 2026-09-23.
    #
    # RV is the volume left after a MAXIMAL exhalation; FRC is the volume left
    # after a QUIET one. FRC < RV is not a marginal case, it is impossible,
    # and it makes the expiratory reserve volume (ERV = FRC - RV) negative.
    #
    # Before this floor, frc_awake() had NO floor at all and frc_anaes() was
    # floored at an arbitrary 400 mL, neither of them at rv. That is not a
    # hypothetical: AT THE SHIPPED PARAMETERS a BMI 47 patient -- Gander
    # 2005's cohort -- got frc_anaes 634 mL against rv 1100, an ERV of MINUS
    # 466 mL. A k_frc_bmi sweep run the same day reported rows that were
    # unphysical for the same reason and it was not noticed until Holley
    # 1967's ERV threshold was checked against them.
    #
    # model.js floored the same quantity at 300 rather than 400. The two
    # implementations therefore disagreed wherever the floor bound, and
    # test_parity.py never caught it because no tested configuration got
    # near it. Both now floor at rv.
    #
    # WHAT THE FLOOR IMPLIES, and it is a real result rather than a tidy-up:
    # once FRC is clamped at RV the oxygen store cannot be reduced any
    # further, so AT HIGH BMI THE FRC ROUTE IS EXHAUSTED. Any remaining
    # disagreement with a morbidly obese measurement has to come from shunt,
    # not from lung volume. See SOURCES.md, Gander 2005.
    def rv_eff(self):
        """Residual volume for THIS patient: body size and BMI applied.

        Until 2026-09-23 the three places that used rv disagreed about
        scaling -- the recoil knee applied height_factor and subtracted
        anatomical dead space, while the FRC floors added the same day used
        the raw constant. They now all go through here.
        """
        return (self.rv * self.height_factor()
                * np.exp(-self.k_rv_bmi_eff() * max(0.0, self.bmi() - 22.0)))

    # ------------------------------------------------------------------
    # EXPERIMENTAL SWITCHES, ADDED 2026-09-25 TO COST A DECISION.
    #
    # These are CLASS ATTRIBUTES, not dataclass fields, so an experiment
    # subclasses and flips them without touching a single call site -- the
    # _forced_shunt idiom handover_numbers.py already uses. Both default to
    # the shipped behaviour, so an ordinary Patient() is bit-identical to
    # what shipped before they existed.
    #
    # PYTHON ONLY, AND THIS MATTERS. model.js implements NEITHER. With
    # either one flipped the two implementations are DIFFERENT MODELS, and
    # test_parity.py runs at the defaults so it cannot see it. IF EITHER IS
    # EVER ADOPTED, model.js MUST CHANGE IN THE SAME COMMIT.
    #
    # frc_asymptote -- give FRC the non-zero floor that both published
    #   regressions have and this model does not. Jones & Nzekwu carry a
    #   +55.2 %pred offset and Pelosi a +460 mL one; ours decays toward
    #   ZERO and is caught by a hard rv_eff() clamp, which is a corner
    #   where the measurements show a smooth approach. The mechanism is
    #   that body mass cannot squeeze a lung below its residual volume, so
    #   the quantity that decays exponentially is the EXPIRATORY RESERVE
    #   (frc - rv), not FRC itself. That is Jones's own ERV regression,
    #   whose offset is 6.5 %pred -- very nearly zero.
    #   NOT A FIT: no new parameter, no benchmark consulted. It re-reads
    #   k_frc_bmi as the decay of ERV rather than of FRC, and the value at
    #   BMI 22 is unchanged by construction.
    #
    # k_rv_bmi_jones -- use Jones's 0.0063 in place of Reinius's 0.0198.
    #   Measurement against measurement, unresolved; see k_rv_bmi above.
    # frc_pelosi_shape -- the offset form done FAITHFULLY, which means
    #   taking the exponent WITH the offset instead of bolting an asymptote
    #   onto an exponent calibrated without one. Pelosi is the only supine
    #   ANAESTHETISED regression we hold, and frc_anaes() is the quantity he
    #   measured, so his curve is used as a SHAPE -- FRC(BMI)/FRC(22) -- with
    #   the level left ours. That is exactly what this model already does
    #   with Quanjer's height term, and it introduces NO new parameter.
    #   Why it is a separate switch from frc_asymptote: those two are
    #   DIFFERENT MECHANISMS, and the first turns out to disagree with the
    #   very measurement that motivated it. See handover_numbers.py.
    #
    # ADOPTED 2026-09-25 BY RULING: frc_pelosi_shape IS NOW THE SHIPPED PATH
    # and is no longer a switch. frc_legacy_exp restores what it replaced, so
    # variant_cost.py can still regenerate the table the ruling was made on.
    frc_asymptote = False
    frc_legacy_exp = False
    k_rv_bmi_jones = False

    @staticmethod
    def _pelosi_frc(bmi):
        """Anaesthetised supine FRC shape, from TWO measurements averaged.

        Pelosi 1998:  FRC = 11.97 exp(-0.096 BMI) + 0.46 L, r 0.86, n = 24
        over BMI 20-66, helium dilution, paralysed, supine, pre-incision.

        RULED 2026-09-26: THE OFFSET IS NOW THE MEAN OF PELOSI AND DAMIA.
        Damia 1988 (Br J Anaesth 60:574-8, read at source 2026-09-26, n = 30)
        measured THE SAME QUANTITY BY THE SAME METHOD under the same
        conditions and got roughly twice as much:

            BMI 48.4   Pelosi 575 mL    Damia  930 mL   1.62x
            BMI 53.2   Pelosi 532 mL    Damia 1090 mL   2.05x

        Two primary sources, no procedural difference to hang it on, and the
        model had been resting on one of them because the other had not been
        obtained. Averaging them is not a fit to a benchmark -- neither
        source is a benchmark, no benchmark was consulted in choosing it, and
        the arithmetic below is fixed by the two papers with nothing free.

        WHERE THE DISAGREEMENT LIVES: in the ASYMPTOTE. Solving Pelosi's own
        functional form for the offset that passes through each Damia cohort
        gives C = 0.8151 and 1.0175 L, mean 0.9163, against Pelosi's 0.46.
        The exponential term is 115 mL at BMI 48 and falls; essentially all
        of the gap is the floor the curve decays to. So the correction is ONE
        NUMBER and introduces no new parameter:

            C = (0.4600 + 0.9163) / 2 = 0.6882 L

        AND THE LEAN END DOES NOT MOVE, by construction. frc_anaes() uses
        this only as a RATIO to its own value at BMI 22, so the ratio at 22
        is 1.0000 before and after. What ships is a FLATTER curve:

            BMI      ratio before   ratio after
             30         0.5932        0.6366
             40         0.3759        0.4425
             53.2       0.2790        0.3560     (+27.6%)

        Regenerate the derivation with handover_numbers.py.
        """
        return 11.97 * np.exp(-0.096 * bmi) + 0.6882

    def k_rv_bmi_eff(self):
        """How fast residual volume falls with BMI, and WHOSE measurement.

        0.0198 is Reinius's single CT point; 0.0063 is Jones's 373 patients
        by plethysmography. They disagree threefold and the conflict is open.
        """
        return 0.0063 if self.k_rv_bmi_jones else self.k_rv_bmi

    def frc_awake(self):
        if self.frc_asymptote:
            # The expiratory reserve decays; FRC therefore decays TO rv,
            # smoothly, instead of toward zero and being clamped at it.
            base = self.frc_ref * self.height_factor() * self.tilt_factor()
            rv = self.rv_eff()
            return rv + max(0.0, base - rv) * np.exp(
                -self.k_frc_bmi * (self.bmi() - 22.0))
        # THE SHIPPED PATH IS LEFT EXACTLY AS IT WAS, factor for factor.
        # Hoisting tilt_factor() out of this product to share it with the
        # branch above reordered the multiply and changed 15 of 72 sampled
        # values in their last bits -- float multiplication is not
        # associative. Caught 2026-09-25 by checking bit-identity rather
        # than assuming it.
        return max(self.rv_eff(), self.frc_ref * self.height_factor()
                   * np.exp(-self.k_frc_bmi * (self.bmi() - 22.0))
                   * self.tilt_factor())

    def frc_anaes(self):
        """Lung volume at the start of apnoea: awake, then the induction drop.

        RULED 2026-09-25 -- this carries PELOSI'S MEASURED SHAPE. Until then
        it was frc_awake() minus an induction drop, with the BMI dependence
        coming entirely from an exponential fitted WITHOUT the offset that
        every published regression of this quantity has. Pelosi 1998 measured
        the quantity this method returns -- supine, anaesthetised, paralysed,
        by helium dilution, n = 24 over BMI 20-66 -- so his curve is carried
        as a SHAPE, FRC(BMI)/FRC(22), with the LEVEL left ours. That is
        exactly what this model already does with Quanjer's height term, and
        IT INTRODUCES NO NEW PARAMETER.

        WHY THE SHAPE GOES HERE AND NOT ON frc_awake(). Pelosi measured the
        ANAESTHETISED lung. Applying his shape to the awake volume and then
        subtracting the induction drop over-steepens it, because the drop is
        ABSOLUTE and so eats a growing FRACTION as the lung shrinks.
        frc_awake() is therefore UNCHANGED, and so are the expiratory reserve
        and unwashed_fraction() that depend on it.

        WHAT IT COST, measured over four full suite runs (variant_cost.py):
        the same four blocking rows by the same four names, agreement with
        Pelosi's measured FRC improving from 7.79% to 1.86% mean absolute
        error, and Heard's obese control moving from the TOP of its band to
        the MIDDLE, 307.6 -> 272.0 s against 244-314.

        THE GUARD, and it is not decoration. Pelosi's regression is STEEPER
        than the form it replaces, so below about BMI 17 it extrapolates the
        anaesthetised lung ABOVE the awake one -- anaesthesia adding gas,
        which is impossible. The induction drop stays an upper bound. The two
        forms agree exactly at BMI 22 by construction, so this binds only
        BELOW it and CANNOT have moved the benchmarks: the leanest patient in
        test_validation.py is BMI 22.86.
        """
        awake = self.frc_awake()
        # the absolute induction drop cannot exceed a quarter of an already
        # small FRC, otherwise the obese lung is emptied unphysiologically
        cap = awake - min(self.frc_drop, 0.25 * awake)
        if self.frc_legacy_exp:
            return max(self.rv_eff(), cap)
        base = self.frc_ref * self.height_factor() * self.tilt_factor()
        at22 = base - min(self.frc_drop, 0.25 * base)
        pel = at22 * self._pelosi_frc(self.bmi()) / self._pelosi_frc(22.0)
        # THE RESIDUAL-VOLUME FLOOR IS GONE, RULED 2026-09-26. It was added
        # 2026-09-23 with the argument, in this file, that "FRC < RV is not a
        # marginal case, it is impossible". DAMIA 1988 MEASURED IT: "Immediately
        # after anaesthesia, FRC decreased to values lower (P<0.01) than the
        # initial value for RV (0.84 +- 0.6 litre less than the baseline RV)",
        # n=18 morbidly obese, preoperative RV 1.94 L against 1.09 L after
        # induction. They anticipated the artefact objection and answered it:
        # Westbrook saw it by body plethysmograph, Ford in three overweight
        # patients postoperatively. So it is not a helium-dilution artefact.
        #
        # The impossibility argument conflates two different volumes. RV is
        # what remains after a MAXIMAL VOLUNTARY exhalation by an AWAKE patient
        # using their expiratory muscles. Anaesthesia with paralysis removes
        # that muscle tone and lets the diaphragm ride cranially under
        # abdominal mass, so the passive relaxation volume of a paralysed obese
        # chest can sit BELOW the awake RV. Nothing is violated.
        #
        # AND THE FLOOR IS NO LONGER LOAD-BEARING ANYWAY. It was doing real
        # work when this curve was a zero-asymptote exponential that decayed
        # toward nothing. The offset form adopted 2026-09-25, with the averaged
        # offset of 2026-09-26, carries its OWN asymptote -- the curve cannot
        # fall below at22 * 0.6882/_pelosi_frc(22) whatever the BMI -- so the
        # clamp is now redundant as well as contradicted.
        #
        # The legacy branch above KEEPS its floor, and must: the exponential it
        # restores has no offset and decays to zero, so without the clamp it
        # returns unphysical volumes. That is the difference between a floor
        # that patches a bad functional form and one that states physiology.
        return min(cap, pel)

    @staticmethod
    def quanjer_tlc(height):
        """Predicted total lung capacity, litres. Quanjer 1993 Table 6, MEN.

        TLC = 7.99H - 7.08, H in metres, RSD 0.70. Read at source 2026-09-25.
        No age term, which Gutierrez 2004 independently agrees with.
        """
        return 7.99 * height - 7.08

    def closing_capacity(self):
        """The lung volume below which airways start to shut.

        RULED 2026-09-26: this is now BUIST & ROSS ON A PREDICTED TLC, which
        is what the source actually says, instead of three constants that
        disagreed with it.

            CC/TLC (per cent) = 0.525 * age + 14.348 +- 4.34
                Buist AS, Ross BB, Am Rev Respir Dis 1973;107:744-752,
                read at source. Their COMBINED regression (men and women).
            TLC = 7.99 * height(m) - 7.08 litres
                Quanjer 1993 Table 6, men. The model is male by ruling.

        WHAT THIS RETIRES. cc_at_20, cc_per_year and cc_per_bmi were unsourced
        VALUES that disagreed with a source this repository holds. cc_per_bmi
        goes entirely, and that is the point rather than a side effect: BOTH
        Milic-Emili AND BJA Education say closing capacity is not raised by
        obesity, and a term with no support is gone rather than re-fitted.
        Obesity now reaches closure the way the physiology says it does --
        by lowering FRC toward an unchanged closing capacity.

        THE BMI TERM ON TLC IS A SEPARATE QUESTION, and is a switch rather
        than an assumption. Quanjer's TLC has NO weight term, but Jones &
        Nzekwu measured TLC falling 0.50 per cent of predicted per BMI unit,
        so a Quanjer TLC overestimates the obese lung -- +11.2% at BMI 40.
        cc_tlc_bmi carries that correction; it defaults ON because leaving it
        off means knowingly using a TLC the measurement contradicts.
        """
        if self.cc_legacy:
            # The retired form, kept ONLY so variant_cost.py can regenerate
            # the table this ruling was made on.
            return (self.cc_at_20
                    + self.cc_per_year * (self.age - 20.0)
                    + self.cc_per_bmi * max(0.0, self.bmi() - 25.0)) * self.height_factor()
        tlc = self.quanjer_tlc(self.height) * 1000.0
        if self.cc_tlc_bmi:
            # Jones & Nzekwu, Fig 3: -0.50 %predicted per BMI unit, anchored
            # at their 20-25 group (mean BMI 22.5, TLC 98.7% of predicted).
            # OFF by ruling -- see the parameter. Kept so the choice stays
            # visible and costable rather than becoming invisible.
            tlc *= (98.7 - 0.50 * (self.bmi() - 22.5)) / 98.7
        frac = (self.cc_buist_slope * self.age + self.cc_buist_intercept) / 100.0
        return tlc * frac

    def vo2_anaes(self):
        # metabolic rate on adjusted body weight; cardiac output on total
        return (self.vo2_ref * (self.abw() / 70.0) ** 0.75
                - self.vo2_drop_per_kg * self.weight)

    def anaemia_co_factor(self):
        """How much the resting cardiac output rises at this haemoglobin.

        1.0 at and above hb_co_threshold, so a normal patient is unaffected.

        AND 1.0 FOR ACUTE ANAEMIA, RULED 2026-09-25. Roy 1963, read at source
        and the only quantitative anchor this limb has, studied CHRONIC
        anaemia of at least four months -- and in 45 of his 51 patients the
        cause was ANKYLOSTOMIASIS, hookworm. A circulation given months to
        adapt is not the circulation of someone who has just bled. The model
        applied his response to ANY low haemoglobin, silently; it no longer
        does.

        THE DEFAULT IS chronic=True, WHICH IS THE OPTIMISTIC READING, and
        that is stated rather than hidden: the raised cardiac output lifts
        mixed venous oxygen, so it SLOWS desaturation. A patient wrongly
        marked chronic is therefore flattered by this model. The default is
        chosen to leave every existing benchmark where it was, not because
        chronic is the safer assumption -- it is not.
        """
        if not self.anaemia_chronic:
            return 1.0
        if self.hb >= self.hb_co_threshold:
            return 1.0
        f = (self.hb_co_threshold / max(self.hb, 0.5)) ** self.hb_co_exp
        return float(min(self.hb_co_max, f))

    def tilt_co_factor(self):
        """Cardiac output multiplier for bed tilt. See co_tilt_gain above.

        The 0.40 floor is a guard, not a physiological claim: it would only
        bind past 98 degrees of head-up, which no timeline reaches.
        """
        return max(0.40, 1.0 - self.co_tilt_gain * self.tilt_deg)

    def co_anaes(self):
        # The anaemia response is applied BEFORE the anaesthetic drop, not
        # after, so anaesthesia blunts the compensation in proportion. That
        # is the clinically important bit: the anaemic patient who was
        # holding their delivery together awake gives some of it back on
        # induction, exactly when the reserve is wanted.
        return (self.co_ref * self.scale() * self.anaemia_co_factor()
                * (1.0 - self.co_drop_frac) * self.tilt_co_factor())

    def n2_capacities(self):
        """N2 capacity of each tissue compartment, mL STPD per mmHg."""
        fat_kg = max(5.0, self.weight * (0.10 + 0.011 * max(0.0, self.bmi() - 20)))
        lean_kg = self.weight - fat_kg
        v_vrg = 5.0 + 0.10 * lean_kg          # L: blood + viscera + brain
        v_mus = 0.50 * lean_kg                 # L
        v_fat = fat_kg / 0.92                  # L
        lam = self.lambda_n2
        return (v_vrg * 1000 * lam,
                v_mus * 1000 * lam,
                v_fat * 1000 * lam * self.lambda_fat_ratio)

    def vq_distribution(self):
        """Perfusion weights and alveolar gas-volume weights.

        THE GAS VOLUME IS ALLOCATED IN PROPORTION TO PERFUSION. Ruled
        2026-09-22. This used to read

            vol = w * np.exp(self.vq_log_sd * z)

        which allocated gas VOLUME using the V/Q RATIO. That is a category
        error, not a mis-set number: V/Q is a ratio of two FLOWS (mL/min per
        mL/min) and gas volume is a VOLUME (mL), and in a SEALED LUNG there
        is no ventilation at all, so V/Q is undefined everywhere and cannot
        be what sets the oxygen store.

        WHAT IT WAS DOING. It produced a 21.8-fold spread in gas volume per
        unit perfusion, 0.175x to 3.80x the mean, with 24.5% of blood flow
        passing through units holding less than HALF the mean oxygen store
        per unit of flow. Those units exhaust early, equilibrate at mixed
        venous tension and from then on behave exactly as shunt -- while the
        model's `shunt` output reports whatever the collapse levers say,
        which is ZERO when they are all off. That is the origin of the
        295 mmHg alveolar-to-arterial gradient at zero shunt, a thing no
        lung can do, and it is why the defect appeared ONLY under
        obstruction: with the airway open, fresh gas refills every
        compartment continuously and the store-size differences never bite.

        WHAT THE CORRECTION BUYS, at the Stock reference patient, 5 min
        sealed (measured: PaO2 314 (87), SaO2 >92%, slope 3.4, band 2.4-4.4):

            vol = w * V/Q (as shipped)   PaO2  60.9  SaO2 85.3  gap 316.0
            separate volume SD 0.35      PaO2  87.3  SaO2 95.0  gap 238.5
            separate volume SD 0.20      PaO2 126.7  SaO2 98.3  gap 176.2
            vol = w (this)               PaO2 157.0  SaO2 99.1  gap 138.9

        THE SATURATION FAILURE IS FIXED and the CO2 slope comes back into
        the low end of its band. THE PaO2 FAILURE IS NOT FIXED: 157 against
        a measured 314, with 138.9 mmHg of gradient still unexplained at
        ZERO shunt and ZERO volume dispersion. Roughly half the defect
        remains and is NOT accounted for by this correction. Do not read
        this as a solution.

        WHY THE LIMITING CASE AND NOT A FITTED DISPERSION. Any intermediate
        value would be a number chosen because it looked good against a
        benchmark, which is what CLAUDE.md forbids. Volume proportional to
        perfusion introduces NO new free parameter; it is an explicit,
        stated assumption that every compartment holds the same gas store
        per unit of blood flow. It is certainly not exactly true of a real
        lung -- dependent regions hold less gas and take more flow -- but
        the model already carries tilt, closing capacity and dependent
        collapse, and deriving the volume distribution from those is the
        right way to improve on this, not a free dispersion parameter.

        vq_log_sd IS NOW INERT -- CORRECTED 2026-09-23. This docstring used
        to claim it "IS STILL USED, for the V/Q ratio itself, which governs
        gas exchange whenever the airway is patent". That was wrong. Nothing
        in this file or in model.js constructs a V/Q ratio from it, so every
        compartment has the SAME ventilation-to-perfusion ratio by
        construction and the parameter changes nothing. Measured, not
        reasoned: swept over a hundredfold range, sealed and patent, every
        output identical to five significant figures.

        So the model currently has NO IMPOSED V/Q dispersion at all. Its
        heterogeneity is entirely derived -- per-compartment absorption
        collapse, and the unwashed fraction from incomplete denitrogenation.
        That is the design this docstring argues for two paragraphs above; it
        is worth being explicit that it is now the actual state rather than an
        aspiration.
        """
        n = self.n_vq
        z = np.linspace(-2.2, 2.2, n)
        w = np.exp(-0.5 * z * z)
        w /= w.sum()                          # perfusion share
        vol = w.copy()                        # gas volume tracks perfusion
        return w, vol

    # ---- LOW V/Q FROM INCOMPLETE DENITROGENATION, added 2026-09-23 --------
    #
    # THE GAP THIS EXISTS TO CLOSE. Gander 2005 measured arterial oxygen of
    # 243 (136) mmHg in morbidly obese patients at the end of five minutes of
    # 100% oxygen. The model gave 563.8, and that number did not move by one
    # decimal place when residual volume was corrected, because arterial
    # oxygen at the start of apnoea is set by preoxygenation and by gas
    # exchange, not by how much gas the lung holds. The FRC route is
    # exhausted; the defect is in gas exchange.
    #
    # AND IT IS NOT MORE SHUNT. Hedenstierna 2020 (n=243, CT) finds
    # atelectasis shows NO FURTHER INCREASE above BMI 30, so this model's
    # shunt ceiling is right. Three sources instead separate a SECOND thing
    # from shunt:
    #
    #   Hedenstierna 2020  "V/Q mismatch caused mainly by airway closure",
    #                      stated as distinct from the atelectasis
    #   Reinius 2009       quantifies "poorly aerated" lung SEPARATELY from
    #                      "nonaerated". Poorly aerated lung still has gas
    #                      in it. That is low V/Q, not collapse
    #   Holley 1967        measured the ventilation redistribution directly,
    #                      with xenon-133, in exactly this population
    #
    # THE MECHANISM. A lung unit whose airway is already closed at the start
    # of preoxygenation never sees the oxygen. It is not collapsed -- it
    # still holds gas, and it is still perfused -- but the gas it holds is
    # the alveolar air it had when the airway shut. Blood leaving it is
    # therefore poorly oxygenated while every other unit's is maximally
    # oxygenated, and the mixture has a low arterial oxygen tension at a
    # normal saturation. That is the definition of low V/Q.
    #
    # WHAT IT PREDICTS, none of which was fitted:
    #   (a) lower arterial oxygen at the START of apnoea, which is where
    #       Gander's disagreement is
    #   (b) scaling with AIRWAY CLOSURE, not with atelectasis, so it grows
    #       with BMI and age wherever closing capacity exceeds FRC and is
    #       exactly ZERO in a patient whose FRC is above closing capacity
    #   (c) MORE atelectasis on 100% oxygen than on 30-50%, because a closed
    #       unit full of oxygen absorbs and a closed unit full of nitrogen is
    #       splinted open. Hedenstierna 2020 measured 12.8 cm2 against
    #       8.1 cm2, which is the sign this predicts
    #
    # NO NEW FREE PARAMETER. The fraction uses the SAME closure law, with the
    # SAME max_closed and cc_k, as the runtime collapse term -- the only
    # difference is that it is evaluated at the AWAKE lung volume, because
    # preoxygenation happens before induction. Nothing here was chosen by
    # looking at a benchmark.
    def closure_x(self, v_lung):
        """How far this lung sits below closing capacity, RELATIVE to what it
        still holds. The one quantity behind every closure term in the model.

        1600 mL below closing capacity is trivial in a 3 L lung and
        catastrophic in a 700 mL one, which is why it is normalised rather
        than left in millilitres. Normalising is also what separates the
        obese from the morbidly obese, which an absolute measure fails to do.

        Three callers, differing ONLY in the volume they pass:
          shunt_base_eff()     frc_anaes(), the volume apnoea starts from
          unwashed_fraction()  frc_awake(), because preoxygenation is awake
          the collapse term     the CURRENT volume, as the lung empties
        """
        return max(0.0, self.closing_capacity() - v_lung) / max(v_lung, 100.0)

    def shunt_base_eff(self):
        """Shunt at the start of apnoea: airway closure at the induction volume.

        Keyed on lung volume against closing capacity, NOT on BMI. See the
        parameter block above for the law, for the two limits that are
        physics rather than fit, for what it costs against Pelosi's curve,
        and for the double count that re-keying exposed.
        """
        x = self.closure_x(self.frc_anaes())
        s = self.shunt_anat + (1.0 - self.shunt_anat) * x / (x + self.shunt_cc_k)
        return float(min(s, self.shunt_ceiling))

    def unwashed_fraction(self):
        """Perfusion share whose airway was shut throughout preoxygenation.

        Zero whenever the awake FRC is at or above closing capacity, which is
        every young lean supine patient. See the block comment above.
        """
        x = self.closure_x(self.frc_awake())
        return self.max_closed * x / (x + self.cc_k)

    def summary(self):
        return (f"{self.weight:.0f} kg BMI {self.bmi():4.1f} age {self.age:.0f} | "
                f"tilt {self.tilt_deg:+.0f} FRC {self.frc_anaes():4.0f} "
                f"CC {self.closing_capacity():4.0f} mL | "
                f"VO2 {self.vo2_anaes():3.0f} CO {self.co_anaes():4.2f}")


@dataclass
class AirwayEpoch:
    """One segment of the airway timeline.

    The airway is a RESISTANCE, not a throttle. The aventilatory mass flow is
    only ~3.3 mL/s, and the pressure cost of driving that through even a badly
    narrowed airway is tiny: a 3 mm aperture costs 0.016 cmH2O, a 1 mm aperture
    1.3 cmH2O, against several cmH2O of subatmospheric recoil available within
    the first minute. The system is self-regulating — volume falls just far
    enough for recoil to drive the required flow, and then stops falling.

    The practical consequence is that patency is close to binary. Anything
    above about 1 mm of continuous channel is effectively free; only true
    occlusion (soft palate apposition, laryngospasm, a mass) matters.

    Typical values, cmH2O/(L/s):
        2      open airway / laryngoscopy
       20      partly obstructed, jaw thrust or oral airway
      200      poorly held mask, tongue back
     2000      near-complete, a chink only
      inf      complete occlusion
    """
    duration: float
    resistance: float = 2.0      # cmH2O/(L/s); np.inf = complete occlusion
    fgo2: float = 0.21
    label: str = ""

    @property
    def patent(self):
        return np.isfinite(self.resistance)


# ---------------------------------------------------------------------------
def plateau_sao2(pt: Patient, shunt, pao2_alv=570.0, co=None):
    """
    Steady-state arterial saturation during MAINTAINED apnoeic oxygenation.

    Substituting the Fick relation CvO2 = CaO2 - VO2/(10Q) into the shunt
    equation CaO2 = (1-f)Cc'O2 + f CvO2 and solving:

        CaO2  =  Cc'O2  -  [ f / (1-f) ] * VO2 / (10 Q)

    The fixed point exists ONLY because apnoeic oxygenation holds Cc'O2
    constant. With no maintained supply of alveolar oxygen, Cc'O2 itself
    decays and there is no fixed point: saturation falls without limit.
    The iteration has gain f < 1, so the plateau is always stable and is
    approached geometrically over roughly 1/(1-f) circulation times.

    CAVEAT: assumes VO2 and cardiac output constant. Below roughly SaO2 60-70%
    that fails in both directions — oxygen delivery becomes supply-limited
    (VO2 falls, raising the plateau) while myocardial hypoxia and acidosis cut
    cardiac output (lowering it). Treat plateaus below ~70% as indicative.
    """
    cc_o2 = bg.HUFNER * pt.hb + bg.O2_SOL * pao2_alv
    # cardiac output must be the CURRENT value, not the baseline: it is the
    # denominator of the correction term, so using the resting value once the
    # model made cardiac output dynamic put the two out of step.
    d_av = pt.vo2_anaes() / (10.0 * (co if co is not None else pt.co_anaes()))
    f = np.clip(shunt, 0.0, 0.95)
    ca_o2 = cc_o2 - (f / (1.0 - f)) * d_av
    sao2 = np.clip((ca_o2 - 0.15) / (bg.HUFNER * pt.hb), 0.0, 1.0)
    return sao2, ca_o2, d_av


def critical_shunt(pt: Patient, target_sao2, pao2_alv=570.0, co=None):
    """Shunt fraction at which the plateau equals target_sao2."""
    cc_o2 = bg.HUFNER * pt.hb + bg.O2_SOL * pao2_alv
    d_av = pt.vo2_anaes() / (10.0 * (co if co is not None else pt.co_anaes()))
    ca_target = bg.HUFNER * pt.hb * target_sao2 + 0.15
    ratio = (cc_o2 - ca_target) / d_av
    return 1.0 if ratio <= 0 else ratio / (1.0 + ratio)


# ---------------------------------------------------------------------------
def _recoil(v, frc, crs, rv, stiff, floor):
    """Relaxed recoil pressure, mmHg relative to atmosphere.

    Linear over the normal range, but the chest wall stiffens steeply below
    residual volume. Without this the linear extrapolation lets the lung shrink
    below RV under obstruction, which is not possible and which overstates both
    the shunt and the size of the subsequent passive inhalation.
    """
    p = (v - frc) / crs
    if v < rv:
        p += (v - rv) / (crs * stiff)
    return max(p, floor)


def _solve_obstructed_volume(n_dry, frc, crs_ml_per_mmhg, rv, stiff, floor):
    target = n_dry * GASK
    lo, hi = 1.0, frc + 4000.0
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if (PB + _recoil(m, frc, crs_ml_per_mmhg, rv, stiff, floor) - PH2O) * m < target:
            lo = m
        else:
            hi = m
    v = 0.5 * (lo + hi)
    return v, PB + _recoil(v, frc, crs_ml_per_mmhg, rv, stiff, floor)


# ---------------------------------------------------------------------------
def simulate(pt: Patient, timeline, dt=0.1, feo2_start=0.87, paco2_start=40.0,
             stop_sao2=0.20):
    # crs is mL/cmH2O; _recoil works in mmHg, so the compliance must be
    # expressed as mL/mmHg. Compliance is volume PER pressure, so converting it
    # between pressure units uses the RECIPROCAL of the pressure factor: one
    # mmHg is 1.35951 cmH2O, so a compliance of 85 mL/cmH2O is 85 * 1.35951 =
    # 115.6 mL/mmHg. This line used to DIVIDE, which is the conversion for a
    # pressure (as `p_collapse` below correctly does) and is wrong for a
    # compliance. The error was squared on the round trip out of _recoil and
    # made the respiratory system 1.35951^2 = 1.85x stiffer than the parameter
    # said: an effective 46 mL/cmH2O, below the 60-75 Rothen 1993 measured.
    # Both implementations had it identically, which is why test_parity.py
    # never caught it -- parity tests agreement, not correctness.
    crs_mmhg = pt.crs * 1.35951
    frc = pt.frc_anaes()
    cc = pt.closing_capacity()
    vo2 = pt.vo2_anaes()
    vco2_metab = vo2 * pt.rq
    co = pt.co_anaes()
    hb, temp, be = pt.hb, pt.temp, pt.be

    v_a = frc - pt.vd_anat
    f_o2 = feo2_start
    f_co2 = paco2_start / PDRY
    f_n2 = max(0.0, 1.0 - f_o2 - f_co2)
    q_w, v_w = pt.vq_distribution()          # perfusion and volume shares
    n_tot0 = v_a * PDRY / GASK
    # n[i] = [O2, CO2, N2] in compartment i, mL STPD
    n = np.outer(v_w, np.array([f_o2, f_co2, f_n2])) * n_tot0

    # ---- units that never saw the oxygen -------------------------------
    # See Patient.unwashed_fraction(). A unit whose airway was shut for the
    # whole of preoxygenation still holds the ALVEOLAR AIR it had when the
    # airway closed, not inspired air -- alveolar gas is never inspired gas.
    # Its composition is the alveolar gas equation on room air, which is
    # arithmetic from constants already in this model and not a parameter:
    #
    #     PAO2 = 0.2093 * (PB - 47) - paco2_start / rq
    #
    # The units are taken from the LOW-V/Q end of the distribution, index 0
    # upward, because airway closure happens in the dependent lung. The
    # boundary compartment is split rather than rounded, so the fraction is
    # exact and does not step with n_vq -- which test_parity.py would see.
    f_unwashed = pt.unwashed_fraction()
    if f_unwashed > 1e-9:
        pao2_air = 0.2093 * PDRY - paco2_start / pt.rq
        fa_o2 = max(0.0, pao2_air) / PDRY
        fa_co2 = paco2_start / PDRY
        fa_n2 = max(0.0, 1.0 - fa_o2 - fa_co2)
        share = np.zeros(pt.n_vq)            # unwashed share OF EACH unit
        need = f_unwashed
        for i in range(pt.n_vq):
            if need <= 0.0:
                break
            take = min(q_w[i], need)
            share[i] = take / q_w[i]
            need -= take
        air = np.array([fa_o2, fa_co2, fa_n2])
        pre = np.array([f_o2, f_co2, f_n2])
        n = (np.outer(v_w * (1.0 - share), pre)
             + np.outer(v_w * share, air)) * n_tot0

    nseg = pt.vd_segments
    v_seg = pt.vd_anat / nseg
    ds = np.tile(np.array([f_o2, f_co2, f_n2]), (nseg, 1))

    pha_0 = bg.ph_from_pco2_be(paco2_start, be, hb, so2=0.99, temp=temp)
    # End-capillary oxygen content is now mixed ACROSS COMPARTMENTS, because
    # they no longer all hold the same gas (see f_unwashed above). Taking the
    # uniform alveolar value here would hide the low-V/Q units from the
    # starting PaO2 for the first pool transit -- the same mistake the shunt
    # mixing below was written to avoid. Every compartment carries the same
    # CO2 at t=0, so the CO2 line needs no such mixing.
    fr_0 = n / np.maximum(n.sum(axis=1, keepdims=True), 1e-12)
    cc_o2_0 = float(q_w @ bg.o2_content(fr_0[:, 0] * PDRY, hb, pha_0,
                                        paco2_start, temp))
    caco2_0 = bg.co2_content(paco2_start, pha_0, 0.99, hb, temp)
    # Arterial blood starts SHUNT-MIXED, not at the alveolar value. Solving
    # the shunt equation with the Fick relation gives the resting fixed point
    # directly - the same algebra as plateau_sao2(). Initialising at the
    # alveolar value instead makes the first half-minute falsely optimistic
    # and hides the shunt from the starting PaO2 altogether.
    _f = min(pt.shunt_base_eff(), 0.9)
    cao2_0 = cc_o2_0 - (_f / (1.0 - _f)) * vo2 / (co * 10.0)
    cvo2_0 = cao2_0 - vo2 / (co * 10.0)
    cvco2_0 = caco2_0 + vco2_metab / (co * 10.0)

    art_o2 = np.full(pt.pools, cao2_0); art_co2 = np.full(pt.pools, caco2_0)
    ven_o2 = np.full(pt.pools, cvo2_0); ven_co2 = np.full(pt.pools, cvco2_0)
    tis_o2, tis_co2, slow_co2 = cvo2_0, cvco2_0, cvco2_0
    n2_cap = np.array(pt.n2_capacities())          # mL STPD per mmHg
    n2_p = np.full(3, pt.n2_pt_init)               # tissue N2 tensions, mmHg
    q_frac = np.array(pt.q_frac)
    co_base = co
    collapsed, hpv = 0.0, 0.0
    n_c0 = n.sum(axis=1).copy()          # starting gas per compartment
    coll_c = np.zeros(pt.n_vq)           # collapsed fraction per compartment
    pvo2_prev = 40.0
    paco2_prev, sao2_prev = paco2_start, 0.99
    t_low, hr = 0.0, pt.hr_base
    map_, pap = 80.0, 15.0

    v_art_sub = pt.v_art / pt.pools
    v_ven_sub = pt.v_ven / pt.pools

    total_t = sum(e.duration for e in timeline)
    nsteps = int(round(total_t / dt))
    keys = ('t', 'va', 'palv_cmh2o', 'pao2_alv', 'paco2_alv', 'pao2', 'paco2',
            'sao2', 'spo2', 'pvo2', 'svo2', 'ph', 'inflow', 'cum_o2_in',
            'lung_o2', 'shunt', 'collapsed', 'hpv', 'pan2', 'co', 'hr',
            'map', 'pap', 'sv', 'atelectasis', 'pvco2')
    rec = {k: np.zeros(nsteps + 1) for k in keys}

    sao2_hist, spo2, cum_o2_in = [], 0.99, 0.0
    dt_min = dt / 60.0
    _last = None
    # How many steps between blood-gas inversions. 0.0 means every step, and
    # is the default: the old behaviour held one inversion for a whole
    # simulated second whatever dt was, which made the apparent rate of fall
    # of SaO2 an artefact of the grid, scaling as 1/dt.
    _bg_stride = (max(1, int(round(pt.bg_invert_interval / dt)))
                  if pt.bg_invert_interval > 0 else 1)

    states = []
    for e in timeline:
        states += [e] * int(round(e.duration / dt))
    while len(states) < nsteps + 1:
        states.append(timeline[-1])

    for i in range(nsteps + 1):
        ep = states[i]
        n_dry = n.sum()
        n_c = n.sum(axis=1)                  # dry gas per compartment
        # Volume and pressure always follow the mechanics: a partly obstructed
        # airway must be allowed to develop a subatmospheric pressure, since
        # that pressure is what drives the flow.
        v_a, p_abs = _solve_obstructed_volume(
            n_dry, frc - pt.vd_anat, crs_mmhg,
            max(200.0, pt.rv_eff() - pt.vd_anat),
            pt.stiff_below_rv, pt.p_collapse / 1.35951)
        if p_abs > PB and np.isfinite(ep.resistance):
            # Above atmospheric, gas vents through an open airway. It cannot
            # vent through a SEALED one, so there the pressure is allowed to
            # rise - which is what returning nitrogen does to a closed lung.
            v_a, p_abs = n_dry * GASK / PDRY, PB
        p_dry = p_abs - PH2O
        # all compartments share one alveolar pressure, so volume follows
        # quantity; partial pressures are per compartment
        fr_c = n / np.maximum(n_c, 1e-9)[:, None]
        p_o2_c = fr_c[:, 0] * p_dry
        p_co2_c = fr_c[:, 1] * p_dry
        frac = n.sum(axis=0) / n_dry
        pao2_alv, paco2_alv = frac[0] * p_dry, frac[1] * p_dry

        # ---- per-compartment absorption collapse ---------------------------
        # A unit whose uptake outruns its refill shrinks. Once it is below its
        # own closing volume it is lost, and the residual gas absorbs at a rate
        # set by its composition: oxygen goes fast, nitrogen splints it open.
        # This is the mechanism behind desaturation on good tracheal oxygen -
        # V/Q mismatch from absorption atelectasis, not device failure.
        v_frac_c = n_c / np.maximum(n_c0, 1e-9)
        exposed = np.clip((pt.cv_frac - v_frac_c) / pt.cv_frac, 0.0, 1.0)
        tau_c_c = 60.0 * fr_c[:, 0] + 900.0 * (1.0 - fr_c[:, 0])
        gain = np.maximum(exposed - coll_c, 0.0) * (dt / tau_c_c)
        loss = (np.minimum(exposed - coll_c, 0.0) * (dt / pt.tau_recruit)
                * pt.recruit_frac)
        coll_c = np.clip(coll_c + gain + loss, 0.0, 1.0)

        # ---- airway closure -> absorption collapse -> shunt ---------------
        v_lung = v_a + pt.vd_anat
        # What matters is how far below closing capacity the lung sits
        # RELATIVE TO the volume it still has, not the absolute millilitres:
        # 1600 mL below CC is trivial in a 3 L lung and catastrophic in a
        # 700 mL one. Normalising this way is also what separates the obese
        # from the morbidly obese, which an absolute measure fails to do.
        x = pt.closure_x(v_lung)
        closed_target = pt.max_closed * x / (x + pt.cc_k)
        tau_c = (pt.tau_collapse_o2 * frac[0]
                 + pt.tau_collapse_air * (1.0 - frac[0]))
        if closed_target > collapsed:
            collapsed += (closed_target - collapsed) * (dt / tau_c)
        # ---- HPV: Marshall dose-response on the collapsed bed -------------
        # total collapsed perfusion: global closure plus per-unit absorption
        absorbed = float(q_w @ coll_c)
        f0 = pt.perfusion_gain * min(0.95, collapsed + absorbed)
        if pt.hpv_enabled and f0 > 1e-6:
            pv = max(pvo2_prev, 1.0)
            pso2 = pv ** 0.41 * pv ** 0.59          # collapsed: no alveolar gas
            resp = pso2 ** -2.616 / (6.683e-5 + pso2 ** -2.616)
            resp = min(1.0, resp + pt.hpv_co2_gain * max(0.0, paco2_alv - 40.0))
            hpv += (resp - hpv) * (dt / pt.tau_hpv)
            k_pvr = 1.0 + (pt.hpv_pvr_max - 1.0) * hpv
            f_eff = f0 / (f0 + k_pvr * (1.0 - f0))
        else:
            f_eff = f0
        shunt = float(np.clip(pt.shunt_base_eff() + f_eff, 0.0, 0.95))

        # ---- heart rate, then cardiac output ------------------------------
        # Stroke volume is held constant, so these two are not independent:
        # cardiac output is DERIVED from rate. Hypercapnia drives the rate up,
        # hypoxaemia drives it down, and the terminal rhythm takes flow with
        # it - an agonal escape rate cannot deliver a normal cardiac output.
        co2_arg = max(0.0, min(paco2_prev, pt.co2_response_cap) - 40.0)
        co2_factor = min(pt.co_max_factor, 1.0 + pt.co_co2_gain * co2_arg)
        s_hr = max(sao2_prev, 1e-3)
        _sig = lambda x: x ** pt.hr_brady_n / (x ** pt.hr_brady_n
                                               + pt.hr_brady_sao2_50 ** pt.hr_brady_n)
        # normalised so a normally saturated patient has no bradycardia at all
        brady = min(1.0, _sig(s_hr) / _sig(0.99))
        hr = pt.hr_base * co2_factor * brady
        n_stages = len(pt.hr_term_rates)
        if sao2_prev < pt.hr_term_sao2:
            t_low += dt
        elif t_low < pt.hr_term_delay + 10.0 * n_stages:
            t_low = 0.0                      # recovery, until asystole latches
        if t_low >= pt.hr_term_delay:
            e = t_low - pt.hr_term_delay
            k = int(e // 10.0)
            hr = pt.hr_term_rates[k] if k < n_stages else 0.0
        # stroke volume: hypercapnic inotropy up, Muller effect down
        itp = min(0.0, (p_abs - PB) * 1.35951) * pt.itp_fraction   # cmH2O
        sv_f = ((1.0 + pt.sv_co2_gain * co2_arg)
                * max(0.15, 1.0 + pt.sv_itp_gain * itp))
        co = max(0.02, co_base * (hr / pt.hr_base) * sv_f)
        # pressures
        # Reduced viscosity and vasodilatation are WHY the output rises, so
        # the resistance falls with it. Leaving svr_base alone would double
        # the mean arterial pressure along with the cardiac output, whereas
        # measured anaemic patients have a normal or slightly low MAP and a
        # markedly reduced resistance -- Circulation 1963 records exactly
        # that, and its reversal when the anaemia is treated.
        svr = (pt.svr_base / pt.anaemia_co_factor()
               * max(pt.svr_floor, 1.0 + pt.svr_co2_gain * co2_arg))
        map_ = co * svr
        pvr = pt.pvr_base * (1.0 + (pt.hpv_pvr_max - 1.0) * hpv)
        pap = co * pvr + pt.pcwp
        n2_cond = q_frac * co * 1000.0 * pt.lambda_n2

        # ---- pulmonary capillary ------------------------------------------
        cv_o2, cv_co2 = ven_o2[-1], ven_co2[-1]
        # One pH PER COMPARTMENT. The lung-wide pH this used to use assumed
        # alveolar CO2 varies little between compartments, which is true while
        # the V/Q spread is narrow but fails exactly when the model is being
        # asked its hardest question: under obstruction the spread widens, and
        # pricing a compartment at 60 mmHg with the pH belonging to the lung
        # mean inflated its CO2 content by up to 2.45x. Content then went
        # linear in PCO2 -- the dissociation curve's saturation was lost -- and
        # arterial PCO2 ran away to 250 mmHg while alveolar sat at 112 and
        # venous at 113, which is thermodynamically impossible: arterial must
        # lie between them. The obstructed rate of rise came out at 41.75
        # mmHg/min against Stock's measured 3.4. It costs one scalar solve per
        # compartment per step and nothing else in the model changes.
        #
        # The solve input is clamped, and must be. A compartment whose gas
        # volume has collapsed onto the 1e-9 floor has a PCO2 that is the
        # ratio of two floor values: in a sealed run it ranges from 1.8e-06 to
        # 566 mmHg and carries no physical information. That is not merely
        # noisy, it is out of domain -- the RBC correction in co2_content has
        # a POLE at pH 8.142, which any PCO2 below about 2.4 mmHg reaches, and
        # beyond it the content changes sign. The lung-mean pH was always
        # physiological so it never met the pole; a per-compartment pH walks
        # straight into it, and Python and JavaScript then land either side
        # and disagree by 8.5%. Collapsed units carry almost no perfusion, so
        # clamping to the range over which the correlations are defined
        # changes no gas exchange that is actually happening.
        ph_c = np.array([bg.ph_from_pco2_be(float(pc), be, hb, so2=0.99, temp=temp)
                         for pc in np.clip(p_co2_c, 5.0, 250.0)])
        sc_o2_c = bg.so2_from_po2(p_o2_c, ph_c, p_co2_c, temp)
        cc_o2_c = bg.HUFNER * hb * sc_o2_c + bg.O2_SOL * p_o2_c
        cc_co2_c = bg.co2_content(p_co2_c, ph_c, sc_o2_c, hb, temp)

        qeff = co * (1.0 - shunt) * 10.0     # dL/min through gas exchange
        # Blood that has NOT been shunted goes to the parts of the lung still
        # open, in proportion to how open they are. Weighting it by the
        # RESTING distribution instead -- which is what this did -- keeps
        # sending a fully collapsed compartment its full share of perfusion
        # and then mixes that unit's end-capillary blood into the artery at
        # full weight. The aggregate shunt term above removes the right AMOUNT
        # of blood but not from the right COMPARTMENTS. A unit with no gas
        # left was still setting arterial content, and its gas fractions are
        # by then the ratio of two 1e-9 floor values: in a sealed run those
        # units reach PCO2 of 1.8e-06 and 566 mmHg in the same breath, so what
        # they contributed was numerical debris.
        w_open = q_w * (1.0 - coll_c)
        w_open = w_open / max(w_open.sum(), 1e-12)
        q_c = qeff * w_open                  # per compartment
        vo2_c = q_c * (cc_o2_c - cv_o2)
        vco2_c = q_c * (cv_co2 - cc_co2_c)
        vo2_lung, vco2_lung = vo2_c.sum(), vco2_c.sum()
        # arterial blood is the perfusion-weighted mix, then shunt admixture
        ca_o2_new = (1 - shunt) * float(w_open @ cc_o2_c) + shunt * cv_o2
        ca_co2_new = (1 - shunt) * float(w_open @ cc_co2_c) + shunt * cv_co2

        # ---- nitrogen: sum of three perfusion-limited compartments --------
        pan2 = frac[2] * p_dry
        p_n2_c = fr_c[:, 2] * p_dry
        # Each tissue store exchanges with each COMPARTMENT across that
        # compartment's own nitrogen tension, weighted by its share of
        # perfusion. Driving it from the whole-lung mean lets a unit that has
        # already filled with nitrogen keep taking more, which matters because
        # nitrogen accumulation is what drives both the FgO2 cliff and the
        # absorption atelectasis.
        cond_tot = n2_cond.sum()                   # mL/min/mmHg, all stores
        p_tis_eff = float(n2_cond @ n2_p) / max(cond_tot, 1e-12)
        vn2_c = cond_tot * q_w * (p_tis_eff - p_n2_c)
        vn2 = float(vn2_c.sum())
        # each store gives up its share of the total
        n2_flux = n2_cond * (n2_p - p_tis_eff) + n2_cond / max(cond_tot, 1e-12) * vn2

        # ---- aventilatory mass flow ---------------------------------------
        # WHAT THIS LINE MEANS FOR APNOEIC OXYGENATION, spelled out 2026-09-26
        # because a reply in this session got it backwards. Only the NET
        # absorbed volume is drawn in. So with the airway open and oxygen at
        # the lips, the lung's oxygen changes per minute by
        #
        #     -vo2_lung + inflow*1.0  =  -(vco2_lung + vn2)
        #
        # The store is NOT self-sustaining on 100% oxygen. It falls at exactly
        # the rate carbon dioxide enters the alveolus, plus any nitrogen
        # returning from tissue, because the volume drawn in to replace the
        # oxygen consumed is SMALLER than that oxygen by the volume the CO2
        # now occupies. A. Heard put this in mass terms on 2026-09-26: at
        # ~30 mL/min of alveolar CO2 output, an hour of apnoeic oxygenation
        # costs about 2 L of lung oxygen, so the technique is CO2-limited and
        # finite even in the lean, and reaches its limit sooner in a smaller
        # lung. That is the mechanism by which FRC still governs apnoea time
        # when the store is being topped up -- via falling FAO2, not via
        # exhaustion of the store.
        #
        # THE MODEL RUNS THIS TOO SLOWLY, and the size is recorded rather
        # than tuned. Measured in `handover_numbers.py`: the loss opens at
        # 19.4-21.4 mL/min over minutes 2-10 and DECAYS to a 60-minute mean of
        # 10.6-13.4 across BMI 22-45, against Heard's ~30-34 sustained. It
        # decays because rising PaCO2 closes the alveolar-venous CO2 gradient.
        # So the shortfall is about 1.6x at the start and about 2.5x over the
        # hour -- it is not a constant offset. The CO2 channel
        # being slow is ALREADY a tracked failure -- Stock 1989 obstructed
        # slope, 3.4 mmHg/min measured, this model 2.0 -- and these are the
        # same defect seen from two ends. It is why the oxygenated case
        # reported >3600 s at every BMI.
        deficit = vo2_lung - vco2_lung - vn2
        if np.isfinite(ep.resistance):
            # Flow the airway can pass at the current recoil pressure. During
            # obstruction the lung has been shrinking, so when the airway
            # reopens there is an accumulated volume DEFICIT as well as the
            # ongoing metabolic one. Both are refilled, resistance-limited —
            # this is the audible inrush when a mask is lifted or a blade goes
            # in. Whether that inrush is oxygen or room air is the whole point.
            driving = max(0.0, (PB - p_abs) * 1.35951)          # cmH2O
            q_max = driving / max(ep.resistance, 1e-6)          # L/s BTPS
            q_max = q_max * 1000.0 * 60.0 * PDRY / GASK         # mL/min STPD
            refill = max(0.0, (frc - pt.vd_anat - v_a)) * PDRY / GASK / dt_min
            inflow = min(q_max, max(deficit, 0.0) + refill)
            # Sub-step the dead-space advection so that no more than one
            # segment is displaced per pass (CFL <= 1). Without this a large
            # inrush hands the alveolus a whole timestep of stale dead-space
            # gas at once, which overstates how much oxygen reaches it.
            n_in = max(0.0, inflow) * dt_min
            vol_in = n_in * GASK / PDRY
            add = np.zeros(3)
            if n_in > 0:
                sub = int(min(400, max(1, np.ceil(vol_in / v_seg))))
                dn, k = n_in / sub, (vol_in / sub) / v_seg
                pharynx = np.array([ep.fgo2, 0.0, 1.0 - ep.fgo2])
                for _ in range(sub):
                    add += ds[-1] * dn
                    ds = ds + k * (np.vstack([pharynx, ds[:-1]]) - ds)
            # All compartments hang off one airway, so their pressures
            # equalise and inflow goes wherever gas is being absorbed - not
            # by volume share, which was wrong and over-degraded the lung.
            # Volumes are therefore held, and it is COMPOSITION that diverges:
            # nitrogen returns from tissue by perfusion, so a unit with a small
            # gas volume relative to its blood flow accumulates nitrogen
            # fastest, its alveolar PO2 falls, and it becomes venous admixture
            # without ever closing. That is the mechanism a single well-mixed
            # compartment cannot express.
            deficit_c = np.maximum(vo2_c - vco2_c - vn2_c, 0.0)
            tot_d = deficit_c.sum()
            by_absorption = (deficit_c / tot_d if tot_d > 1e-9
                             else n_c / max(n_c.sum(), 1e-9))
            by_mechanics = n_c / max(n_c.sum(), 1e-9)
            m = pt.inflow_mech_frac
            share = (1.0 - m) * by_absorption + m * by_mechanics
            # Anything above the metabolic deficit is REFILL: it restores the
            # lung toward its resting distribution, so it is shared by the
            # original volumes. Without this a collapsed unit never sees gas
            # again however large the inhalation, and the collapse ratchets
            # even after the airway is reopened.
            excess = max(0.0, inflow - max(deficit, 0.0))
            if excess > 1e-9 and inflow > 1e-9:
                w = excess / inflow
                share = (1.0 - w) * share + w * (n_c0 / n_c0.sum())
            n = n + np.stack([-vo2_c, vco2_c, vn2_c], axis=1) * dt_min \
                  + np.outer(share, add)
            cum_o2_in += add[0]
        else:
            inflow = 0.0
            n = n + np.stack([-vo2_c, vco2_c, vn2_c], axis=1) * dt_min
        # Cardiogenic stirring: relax each compartment's composition toward
        # the lung-mean, conserving each compartment's own gas quantity.
        if pt.tau_mix > 0:
            n_q = n.sum(axis=1)
            mean_frac = n.sum(axis=0) / max(n_q.sum(), 1e-12)
            n = n + (np.outer(n_q, mean_frac) - n) * min(1.0, dt / pt.tau_mix)
        n = np.maximum(n, 1e-9)
        n2_p = np.maximum(0.0, n2_p - n2_flux * dt_min / n2_cap)

        # ---- circulation ---------------------------------------------------
        p_o2, p_co2 = ca_o2_new, ca_co2_new
        for j in range(pt.pools):
            art_o2[j] += (co / v_art_sub) * (p_o2 - art_o2[j]) * dt_min
            art_co2[j] += (co / v_art_sub) * (p_co2 - art_co2[j]) * dt_min
            p_o2, p_co2 = art_o2[j], art_co2[j]

        tis_o2 += ((co * (art_o2[-1] - tis_o2) * 10.0 - vo2)
                   / (pt.v_tis_o2 * 10.0)) * dt_min
        flux_slow = pt.k_co2_slow * (tis_co2 - slow_co2) * 10.0
        tis_co2 += ((co * (art_co2[-1] - tis_co2) * 10.0 + vco2_metab
                     - flux_slow) / (pt.v_tis_co2_fast * 10.0)) * dt_min
        slow_co2 += (flux_slow / (pt.v_tis_co2_slow * 10.0)) * dt_min

        p_o2, p_co2 = tis_o2, tis_co2
        for j in range(pt.pools):
            ven_o2[j] += (co / v_ven_sub) * (p_o2 - ven_o2[j]) * dt_min
            ven_co2[j] += (co / v_ven_sub) * (p_co2 - ven_co2[j]) * dt_min
            p_o2, p_co2 = ven_o2[j], ven_co2[j]

        # ---- outputs --------------------------------------------------------
        if _bg_stride == 1 or i % _bg_stride == 0 or _last is None:
            _last = bg.pco2_from_co2_content(art_co2[-1], be, hb,
                                             art_o2[-1], temp)
        paco2_a, ph_a, sao2, pao2_a = _last

        sao2_hist.append(sao2)
        lag = int(pt.spo2_delay / dt)
        spo2 += (sao2_hist[max(0, len(sao2_hist) - 1 - lag)] - spo2) \
            * (dt / pt.spo2_tau)
        pvo2 = bg.po2_from_o2_content(ven_o2[-1], hb, ph_a, paco2_a, temp)
        pvo2_prev = pvo2
        paco2_prev, sao2_prev = paco2_a, sao2

        rec['t'][i] = i * dt
        rec['va'][i] = v_lung
        rec['palv_cmh2o'][i] = (p_abs - PB) * 1.35951
        rec['pao2_alv'][i] = pao2_alv
        rec['paco2_alv'][i] = paco2_alv
        rec['pao2'][i] = pao2_a
        rec['paco2'][i] = paco2_a
        rec['sao2'][i] = sao2 * 100
        rec['spo2'][i] = spo2 * 100
        rec['pvo2'][i] = pvo2
        rec['svo2'][i] = bg.so2_from_po2(pvo2, ph_a, paco2_a, temp) * 100
        rec['ph'][i] = ph_a
        rec['inflow'][i] = inflow
        rec['cum_o2_in'][i] = cum_o2_in
        rec['lung_o2'][i] = n[:, 0].sum()
        rec['shunt'][i] = shunt
        rec['collapsed'][i] = collapsed
        rec['atelectasis'][i] = absorbed
        # mixed venous PCO2, for comparison with venous-sampling studies
        rec['pvco2'][i] = bg.pco2_from_co2_content(
            ven_co2[-1], be, hb, ven_o2[-1], temp)[0] if i % 20 == 0 \
            else rec['pvco2'][i - 1]
        rec['hpv'][i] = hpv
        rec['pan2'][i] = pan2
        rec['co'][i] = co
        rec['hr'][i] = hr
        rec['map'][i] = map_
        rec['pap'][i] = pap
        rec['sv'][i] = co * 1000.0 / max(hr, 1e-6)

        if hr <= 0.0 and t_low > pt.hr_term_delay + 10.0 * len(pt.hr_term_rates) + 45.0:
            for k in rec:
                rec[k] = rec[k][:i + 1]
            break
        if sao2 < stop_sao2 and stop_sao2 > 0:
            for k in rec:
                rec[k] = rec[k][:i + 1]
            break

    return rec


def time_to(rec, key, threshold, below=True):
    arr = rec[key]
    idx = np.where(arr < threshold)[0] if below else np.where(arr > threshold)[0]
    return None if len(idx) == 0 else rec['t'][idx[0]]
