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
import numpy as np
import bloodgas as bg

PB = 760.0
PH2O = 47.0
PDRY = PB - PH2O
GASK = 863.0


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
    frc_ref: float = 2500.0      # mL supine awake at BMI 22, height 1.75
    k_frc_bmi: float = 0.0417    # exponential decline of FRC per BMI unit
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
    # worsens as the apnoea goes on. ICSM uses 100 compartments; 20 captures
    # most of the behaviour at a fraction of the cost.
    n_vq: int = 20
    vq_log_sd: float = 0.70      # log SD of the perfusion distribution
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
    crs: float = 85.0            # mL/cmH2O
    rv: float = 1100.0           # mL residual volume, anaesthetised supine
    stiff_below_rv: float = 0.15 # compliance retained below RV
    p_collapse: float = -50.0    # cmH2O floor: below this units collapse
                                 # outright rather than holding a vacuum
    shunt_base: float = 0.05

    # --- closing capacity (PLACEHOLDER REGRESSION) -------------------------
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
    # Dose-response from Marshall BE, Marshall C, Frasch F, Hanson CW.
    # Respir Physiol 1994;96:231-47 (canine, independently perfused lung):
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
    vo2_ref: float = 250.0
    vo2_drop_per_kg: float = 0.27
    rq: float = 0.8

    # --- circulation -------------------------------------------------------
    # Cardiac output is no longer fixed. During apnoeic oxygenation it RISES,
    # driven by hypercapnic sympathetic stimulation. Measured directly in the
    # relevant population: 91 anaesthetised, paralysed, apnoeic patients on
    # 100% oxygen, continuous cardiac output, arterial gases every 2 min --
    # median CO 5.0 (IQR 4.5-6.0) rising to 6.5 (5.7-7.5) L/min by 15 min with
    # PaCO2 climbing 2.1 mmHg/min (Sci Rep 2023, PMC10864331). That is +30% CO
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
    # The Muller coupling is kept deliberately small. In the pig study the
    # animals were SEDATED and making inspiratory efforts against a closed
    # airway, which generates large negative swings actively. Our patient is
    # paralysed: the subatmospheric pressure develops slowly from gas
    # absorption alone, with no inspiratory effort behind it. The pig
    # magnitude therefore does not transfer, and tuning to it would be wrong.
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
    # (Sci Rep 2023, n=91; Gustafsson 0.24 kPa/min; Toner 0.30 kPa/min
    # transcutaneous). Historical series report 3.0-3.4 mmHg/min arterial
    # (Frumin 1959; Eger & Severinghaus; Stock). O'Loughlin attributes the
    # discrepancy to higher CO2 production under older technique, notably
    # repeated suxamethonium. Our model reproduces the historical rate by
    # raising RQ or VO2 rather than by changing the store, which is the same
    # explanation. Fitted here to contemporary practice.
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

    def frc_awake(self):
        return (self.frc_ref * self.height_factor()
                * np.exp(-self.k_frc_bmi * (self.bmi() - 22.0))
                * self.tilt_factor())

    def frc_anaes(self):
        # the absolute induction drop cannot exceed a quarter of an already
        # small FRC, otherwise the obese lung is emptied unphysiologically
        drop = min(self.frc_drop, 0.25 * self.frc_awake())
        return max(400.0, self.frc_awake() - drop)

    def closing_capacity(self):
        return (self.cc_at_20
                + self.cc_per_year * (self.age - 20.0)
                + self.cc_per_bmi * max(0.0, self.bmi() - 25.0)) * self.height_factor()

    def vo2_anaes(self):
        # metabolic rate on adjusted body weight; cardiac output on total
        return (self.vo2_ref * (self.abw() / 70.0) ** 0.75
                - self.vo2_drop_per_kg * self.weight)

    def co_anaes(self):
        return self.co_ref * self.scale() * (1.0 - self.co_drop_frac)

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
        """Perfusion weights and V/Q ratios over n_vq parallel compartments."""
        n = self.n_vq
        z = np.linspace(-2.2, 2.2, n)
        w = np.exp(-0.5 * z * z)
        w /= w.sum()                          # perfusion share
        ratio = np.exp(self.vq_log_sd * z)    # V/Q relative to the mean
        vol = w * ratio
        vol /= vol.sum()                      # share of alveolar gas volume
        return w, vol

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
    crs_mmhg = pt.crs / 1.35951
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

    nseg = pt.vd_segments
    v_seg = pt.vd_anat / nseg
    ds = np.tile(np.array([f_o2, f_co2, f_n2]), (nseg, 1))

    pao2_0 = f_o2 * PDRY
    pha_0 = bg.ph_from_pco2_be(paco2_start, be, hb, so2=0.99, temp=temp)
    cc_o2_0 = bg.o2_content(pao2_0, hb, pha_0, paco2_start, temp)
    caco2_0 = bg.co2_content(paco2_start, pha_0, 0.99, hb, temp)
    # Arterial blood starts SHUNT-MIXED, not at the alveolar value. Solving
    # the shunt equation with the Fick relation gives the resting fixed point
    # directly - the same algebra as plateau_sao2(). Initialising at the
    # alveolar value instead makes the first half-minute falsely optimistic
    # and hides the shunt from the starting PaO2 altogether.
    _f = min(pt.shunt_base, 0.9)
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
            max(200.0, pt.rv * pt.height_factor() - pt.vd_anat),
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
        x = max(0.0, cc - v_lung) / max(v_lung, 100.0)
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
        shunt = float(np.clip(pt.shunt_base + f_eff, 0.0, 0.95))

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
        svr = pt.svr_base * max(pt.svr_floor, 1.0 + pt.svr_co2_gain * co2_arg)
        map_ = co * svr
        pvr = pt.pvr_base * (1.0 + (pt.hpv_pvr_max - 1.0) * hpv)
        pap = co * pvr + pt.pcwp
        n2_cond = q_frac * co * 1000.0 * pt.lambda_n2

        # ---- pulmonary capillary ------------------------------------------
        cv_o2, cv_co2 = ven_o2[-1], ven_co2[-1]
        # One pH for the whole lung: every compartment is perfused by the same
        # mixed venous blood and alveolar CO2 varies little between them during
        # apnoea. This keeps every per-compartment term analytic.
        ph_c = bg.ph_from_pco2_be(paco2_alv, be, hb, so2=0.99, temp=temp)
        sc_o2_c = bg.so2_from_po2(p_o2_c, ph_c, p_co2_c, temp)
        cc_o2_c = bg.HUFNER * hb * sc_o2_c + bg.O2_SOL * p_o2_c
        cc_co2_c = bg.co2_content(p_co2_c, ph_c, sc_o2_c, hb, temp)

        qeff = co * (1.0 - shunt) * 10.0     # dL/min through gas exchange
        q_c = qeff * q_w                     # per compartment
        vo2_c = q_c * (cc_o2_c - cv_o2)
        vco2_c = q_c * (cv_co2 - cc_co2_c)
        vo2_lung, vco2_lung = vo2_c.sum(), vco2_c.sum()
        # arterial blood is the perfusion-weighted mix, then shunt admixture
        ca_o2_new = (1 - shunt) * float(q_w @ cc_o2_c) + shunt * cv_o2
        ca_co2_new = (1 - shunt) * float(q_w @ cc_co2_c) + shunt * cv_co2

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
        if i % max(1, int(round(1.0 / dt))) == 0 or _last is None:
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
