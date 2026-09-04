"""
bloodgas.py — blood gas physical chemistry for the apnoea model.

Implements:
  * Severinghaus (1979) O2 dissociation curve with Kelman-style Bohr correction
    for pH, PCO2 and temperature, plus an adjustable P50 offset (2,3-DPG).
  * Douglas, Jones & Reed (1988) whole-blood CO2 content.
  * Van Slyke / Siggaard-Andersen base excess for pH from PCO2 at fixed BE.
  * Numerical inverses (content -> partial pressure), warm-started.

PROVENANCE / CONFIDENCE
  Severinghaus standard curve:  VERIFIED against published form. High confidence.
  Kelman Bohr correction terms: implemented from standard form. Medium-high
        confidence; signs checked by directional test (see selftest()).
  Douglas 1988 CO2 content:     implemented FROM MEMORY of the published form.
        UNVERIFIED against the original paper. selftest() reports deviation from
        textbook reference points; see NOTE_DOUGLAS below before publishing.
  Van Slyke BE:                 standard form, medium confidence.

NOTE_DOUGLAS: whole-blood CO2 content at PCO2 40 / pH 7.40 / SO2 0.97 should be
  ~48 mL/dL (21.5 mmol/L). If selftest() reports materially more than that, the
  RBC correction constants below need checking against Douglas AR, Jones NL,
  Reed JW. J Appl Physiol 1988;65:473-77. A single scale factor CO2_CAL is
  exposed so the curve can be calibrated to reference points without changing
  the functional form.

The Hamburger (chloride) shift is IMPLICIT in this empirical whole-blood curve:
  the HCO3-/Cl- exchange is one of the physical processes the curve was fitted
  to. It is not represented as an explicit ion flux. See README for what an
  explicit (Wolf-type) treatment would add.
"""

import numpy as np
from scipy.optimize import brentq

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HUFNER = 1.34          # mL O2 per g Hb (Hufner's constant, in-vivo value)
O2_SOL = 0.003         # mL O2 / dL / mmHg  (dissolved O2)
MLCO2_PER_MMOL = 22.26 # mL CO2 (STPD) per mmol
CO2_CAL = 1.0          # calibration multiplier on whole-blood CO2 content


# ---------------------------------------------------------------------------
# Oxygen
# ---------------------------------------------------------------------------
def _severinghaus_sat(p):
    """Standard O2 dissociation curve (Severinghaus 1979). p in mmHg."""
    p = np.maximum(p, 1e-6)
    return 1.0 / (23400.0 / (p ** 3 + 150.0 * p) + 1.0)


def _bohr_factor(pH, pco2, temp, p50_offset=0.0):
    """
    Multiplier converting an ACTUAL PO2 to the equivalent PO2 on the standard
    curve. Right-shifted (low affinity) blood -> factor < 1 -> lower saturation.
    """
    x = (0.024 * (37.0 - temp)
         + 0.40 * (pH - 7.40)
         + 0.06 * (np.log10(40.0) - np.log10(np.maximum(pco2, 1e-6))))
    # p50_offset in mmHg: a higher P50 is a right shift
    x -= np.log10((26.8 + p50_offset) / 26.8)
    return 10.0 ** x


def so2_from_po2(po2, pH=7.40, pco2=40.0, temp=37.0, p50_offset=0.0):
    """Haemoglobin saturation (fraction) from PO2, with Bohr correction."""
    return _severinghaus_sat(po2 * _bohr_factor(pH, pco2, temp, p50_offset))


def po2_from_so2(so2, pH=7.40, pco2=40.0, temp=37.0, p50_offset=0.0):
    """Inverse of so2_from_po2."""
    so2 = min(max(so2, 1e-9), 0.999999)
    f = lambda p: _severinghaus_sat(p) - so2
    p_std = brentq(f, 1e-6, 2000.0, xtol=1e-9)
    return p_std / _bohr_factor(pH, pco2, temp, p50_offset)


def o2_content(po2, hb, pH=7.40, pco2=40.0, temp=37.0, p50_offset=0.0):
    """Whole-blood O2 content, mL/dL. hb in g/dL."""
    s = so2_from_po2(po2, pH, pco2, temp, p50_offset)
    return HUFNER * hb * s + O2_SOL * po2


def po2_from_o2_content(co2c, hb, pH=7.40, pco2=40.0, temp=37.0,
                        p50_offset=0.0, guess=None):
    """Inverse: PO2 from O2 content (mL/dL). Bracketed, robust."""
    f = lambda p: o2_content(p, hb, pH, pco2, temp, p50_offset) - co2c
    lo, hi = 1e-6, 2000.0
    if f(lo) > 0:
        return lo
    if f(hi) < 0:
        return hi
    return brentq(f, lo, hi, xtol=1e-7)


# ---------------------------------------------------------------------------
# Acid-base
# ---------------------------------------------------------------------------
def _co2_solubility(temp):
    """CO2 solubility in plasma, mmol/L/mmHg (Douglas 1988)."""
    d = 37.0 - temp
    return 0.0307 + 0.00057 * d + 0.00002 * d * d


def _pk_prime(pH, temp):
    """Apparent pK' of the carbonic acid system (Douglas 1988)."""
    return (6.086 + 0.042 * (7.4 - pH)
            + (38.0 - temp) * (0.00472 + 0.00139 * (7.4 - pH)))


def ph_from_pco2_be(pco2, be, hb, so2=0.97, temp=37.0):
    """
    pH from PCO2, base excess and oxygen saturation.

    Siggaard-Andersen actual base excess:
        ABE = (1 - 0.0143*cHb)*[(cHCO3 - 24.8) + (9.5 + 1.63*cHb)*(pH - 7.4)]
              - 0.2*cHb*(1 - sO2)
    cHb in mmol/L (g/dL * 0.6206).

    The final term is the oxygen-saturation correction. It is the acid-base
    limb of the HALDANE EFFECT: as Hb desaturates it becomes a weaker acid,
    so at fixed BE the blood holds more CO2 at any given PCO2. Omitting it
    (as the short Van Slyke form does) under-represents the a-v CO2 content
    difference by roughly 30%, which in an apnoea model translates directly
    into an overestimate of the rate of rise of PaCO2.
    """
    hb_mm = hb * 0.6206

    def resid(pH):
        s = _co2_solubility(temp)
        hco3 = s * pco2 * 10.0 ** (pH - _pk_prime(pH, temp))
        be_calc = ((1 - 0.0143 * hb_mm)
                   * ((hco3 - 24.8) + (9.5 + 1.63 * hb_mm) * (pH - 7.4))
                   - 0.2 * hb_mm * (1.0 - so2))
        return be_calc - be

    return brentq(resid, 4.5, 10.5, xtol=1e-9)


# ---------------------------------------------------------------------------
# Carbon dioxide
# ---------------------------------------------------------------------------
def co2_content(pco2, pH, so2, hb, temp=37.0):
    """
    Whole-blood CO2 content, mL/dL (STPD). Douglas, Jones & Reed 1988.
    The Haldane effect enters through the so2 term in the RBC correction.
    """
    s = _co2_solubility(temp)
    pk = _pk_prime(pH, temp)
    co2_pl = s * pco2 * (1.0 + 10.0 ** (pH - pk))          # mmol/L plasma
    hb_mm = hb * 0.6206                                     # mmol/L
    rbc_corr = 1.0 - (0.0289 * hb_mm) / ((3.352 - 0.456 * so2)
                                         * (8.142 - pH))
    return CO2_CAL * co2_pl * rbc_corr * MLCO2_PER_MMOL / 10.0


def pco2_from_co2_content(cco2, be, hb, o2c, temp=37.0, guess=40.0):
    """
    Inverse: given whole-blood CO2 content (mL/dL), base excess and O2 content,
    return (PCO2, pH, SO2). Self-consistent because SO2 depends on pH/PCO2 and
    the CO2 curve depends on SO2 (Haldane) — solved by fixed-point on PCO2.
    """
    def state(pco2):
        """Inner fixed point: pH depends on SO2 (Haldane), SO2 depends on pH."""
        so2 = 0.90
        for _ in range(12):
            pH = ph_from_pco2_be(pco2, be, hb, so2=so2, temp=temp)
            po2 = po2_from_o2_content(o2c, hb, pH, pco2, temp)
            s_new = so2_from_po2(po2, pH, pco2, temp)
            if abs(s_new - so2) < 1e-7:
                so2 = s_new
                break
            so2 = s_new
        return pH, po2, so2

    def resid(pco2):
        pH, po2, so2 = state(pco2)
        return co2_content(pco2, pH, so2, hb, temp) - cco2

    lo, hi = 3.0, 400.0
    if resid(lo) > 0:
        pco2 = lo
    elif resid(hi) < 0:
        pco2 = hi
    else:
        pco2 = brentq(resid, lo, hi, xtol=1e-6)
    pH, po2, so2 = state(pco2)
    return pco2, pH, so2, po2


# ---------------------------------------------------------------------------
# Self test / calibration report
# ---------------------------------------------------------------------------
def selftest(verbose=True):
    out = {}
    hb = 15.0

    # --- O2 curve reference points -----------------------------------------
    out['P50'] = po2_from_so2(0.50)
    out['SO2@100'] = so2_from_po2(100.0)
    out['SO2@40'] = so2_from_po2(40.0)
    out['SO2@60'] = so2_from_po2(60.0)

    # Bohr direction check: acidosis must LOWER saturation at fixed PO2
    s_norm = so2_from_po2(40.0, pH=7.40, pco2=40.0)
    s_acid = so2_from_po2(40.0, pH=7.20, pco2=60.0)
    out['bohr_direction_ok'] = bool(s_acid < s_norm)
    out['bohr_delta'] = s_acid - s_norm

    # --- CO2 curve reference points ----------------------------------------
    pH_a = ph_from_pco2_be(40.0, 0.0, hb, so2=0.97)
    out['pH@PCO2_40_BE0'] = pH_a
    out['CaCO2 (ref ~48 mL/dL)'] = co2_content(40.0, pH_a, 0.97, hb)
    pH_v = ph_from_pco2_be(46.0, 0.0, hb, so2=0.75)
    out['CvCO2 (ref ~52 mL/dL)'] = co2_content(46.0, pH_v, 0.75, hb)

    # Haldane direction check: desaturation must RAISE CO2 content
    c_sat = co2_content(40.0, pH_a, 0.97, hb)
    c_des = co2_content(40.0, pH_a, 0.60, hb)
    out['haldane_direction_ok'] = bool(c_des > c_sat)
    out['haldane_delta'] = c_des - c_sat

    # --- Round trip --------------------------------------------------------
    o2c = o2_content(95.0, hb, pH_a, 40.0)
    cco2 = co2_content(40.0, pH_a, 0.97, hb)
    pco2_r, pH_r, so2_r, po2_r = pco2_from_co2_content(cco2, 0.0, hb, o2c)
    out['roundtrip_PCO2_err'] = pco2_r - 40.0
    out['roundtrip_PO2_err'] = po2_r - 95.0

    if verbose:
        for k, v in out.items():
            print(f"  {k:32s} {v}")
    return out


if __name__ == "__main__":
    print("bloodgas.py self-test")
    selftest()
