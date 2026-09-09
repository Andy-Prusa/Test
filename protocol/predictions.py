"""Regenerate every number quoted in protocol/study.html.

The protocol registers its predictions as coming from "the model at a recorded
commit". That claim is only worth anything if the numbers can be reproduced, so
this script derives all of them from apnoea_core and checks them against what
the document says. Run it before the protocol is submitted, and again against
any later commit, to see whether the registered predictions still hold.

    python3 protocol/predictions.py

The scenario throughout is a preoxygenated, paralysed adult whose tracheal tube
is occluded at end-expiration: a single AirwayEpoch at infinite resistance,
FgO2 0.87, from an anaesthetised FRC.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apnoea_core import (GASK, PB, PH2O, AirwayEpoch, Patient,  # noqa: E402
                         simulate)

PDRY = PB - PH2O
OBS = np.inf
DT = 0.1
FGO2 = 0.87
CMH2O = 1.35951                 # mmHg per cmH2O

_fails = []


def check(what, got, want, tol, unit=""):
    ok = abs(got - want) <= tol
    print(f"  {'ok  ' if ok else 'FAIL'} {what:<44} {got:8.1f}{unit}"
          f"   document says {want:g}{unit}")
    if not ok:
        _fails.append(what)


def run(weight, height, age=45, hb=14.0, duration=200.0):
    pt = Patient(weight=weight, height=height, age=age, hb=hb)
    rec = simulate(pt, [AirwayEpoch(duration, resistance=OBS, fgo2=FGO2)],
                   dt=DT, stop_sao2=0.0)
    return pt, rec


def entrained(rec):
    """Gas the lung has lost, expressed at atmospheric pressure, in mL.

    This is exactly the volume drawn in when the occlusion is released and the
    lung returns to its relaxed FRC: releasing restores both the volume and the
    pressure, so the mouth must deliver back every millilitre that was absorbed.
    Two components are separable and are reported apart:

        chest wall     the volume the thorax actually lost
        decompression  the extra gas needed because what remains sits below
                       atmospheric pressure and is therefore rarefied
    """
    v = rec['va']
    p_dry = PB + rec['palv_cmh2o'] / CMH2O - PH2O
    n_atm = v * p_dry / PDRY
    return n_atm[0] - n_atm, v[0] - v


def at(rec, seconds):
    return int(round(seconds / DT))


# --------------------------------------------------------------------------
print(__doc__.strip().splitlines()[0])
print()

print("2.3  Pre-specified predictions -- 70 kg, 1.75 m")
pt, rec = run(70, 1.75)
ent, dvol = entrained(rec)
print("    t      Paw    PaCO2   SaO2     CO    MAP   Ventrained")
for s in (30, 60, 120, 180):
    i = at(rec, s)
    print(f"  {s:4d}  {rec['palv_cmh2o'][i]:7.1f} {rec['paco2'][i]:7.1f}"
          f" {rec['sao2'][i]:6.1f} {rec['co'][i]:6.2f} {rec['map'][i]:6.0f}"
          f" {ent[i]:11.0f}")

i180 = at(rec, 180)
check("Paw at 180 s", rec['palv_cmh2o'][i180], -15.6, 0.2, " cmH2O")
check("PaCO2 at 180 s", rec['paco2'][i180], 58.8, 0.3, " mmHg")
check("SaO2 at 180 s", rec['sao2'][i180], 98.4, 0.2, " %")
check("entrained volume at 180 s", ent[i180], 739.0, 6.0, " mL")
check("entrained volume at 120 s", ent[at(rec, 120)], 494.0, 6.0, " mL")
check("entrained volume at 60 s", ent[at(rec, 60)], 235.0, 6.0, " mL")
check("entrained volume at 30 s", ent[at(rec, 30)], 100.0, 6.0, " mL")

# --------------------------------------------------------------------------
print("\n2.4  What the entrained volume is made of, at 180 s")
scale = rec['va'] / PDRY                     # mL of gas per mmHg, at 1 atm
d_o2 = -(scale[0] * rec['pao2_alv'][0] - scale[i180] * rec['pao2_alv'][i180])
d_co2 = -(scale[0] * rec['paco2_alv'][0] - scale[i180] * rec['paco2_alv'][i180])
d_n2 = -(scale[0] * rec['pan2'][0] - scale[i180] * rec['pan2'][i180])
check("oxygen removed", d_o2, -840.0, 8.0, " mL")
check("carbon dioxide added", d_co2, -9.0, 4.0, " mL")
check("nitrogen returned", d_n2, 110.0, 6.0, " mL")
check("sum of the three", -(d_o2 + d_co2 + d_n2), 739.0, 8.0, " mL")
check("chest wall component", dvol[i180], 718.0, 6.0, " mL")
check("decompression component", ent[i180] - dvol[i180], 21.0, 3.0, " mL")
check("absorption rate near 180 s",
      (ent[i180] - ent[at(rec, 179)]), 4.0, 0.6, " mL/s")

# --------------------------------------------------------------------------
print("\n2.4  Recruitment shortfall if closed lung does not reopen")
# The model refills to FRC unconditionally, so it cannot itself produce a
# shortfall. The size a shortfall WOULD have is the gas held by lung that has
# left the ventilated circuit -- global closure plus per-unit absorption
# collapse -- as a share of the anaesthetised FRC.
for w, h in ((70, 1.75), (100, 1.75)):
    p2, r2 = run(w, h)
    j = at(r2, 180)
    closed = r2['atelectasis'][j] + r2['collapsed'][j]
    print(f"  BMI {p2.bmi():4.1f}   closed fraction {closed:.3f}"
          f"   FRC {p2.frc_anaes():5.0f} mL"
          f"   shortfall {closed * p2.frc_anaes():5.0f} mL")
p2, r2 = run(70, 1.75)
j = at(r2, 180)
check("shortfall at BMI 22.9",
      (r2['atelectasis'][j] + r2['collapsed'][j]) * p2.frc_anaes(),
      125.0, 10.0, " mL")
p3, r3 = run(100, 1.75)
j = at(r3, 180)
check("shortfall at BMI 32.7",
      (r3['atelectasis'][j] + r3['collapsed'][j]) * p3.frc_anaes(),
      161.0, 12.0, " mL")

# --------------------------------------------------------------------------
print("\n4.3  The inrush, and why a pneumotachograph is the wrong instrument")
pt4 = Patient(weight=70, height=1.75, age=45, hb=14.0)
fine = 0.005
r4 = simulate(pt4, [AirwayEpoch(180, resistance=OBS, fgo2=FGO2),
                    AirwayEpoch(10, resistance=2.0, fgo2=FGO2)],
              dt=fine, stop_sao2=0.0)
i0 = int(round(180 / fine))
flow = r4['inflow'][i0:] * GASK / PDRY / 1000.0 / 60.0        # L/s
cum = np.cumsum(r4['inflow'][i0:]) * (fine / 60.0) * GASK / PDRY
# The inrush is over long before the epoch is. Nearly all of it arrives in the
# first fifth of a second, but the last few millilitres trickle in over about a
# second as the refill term closes the remaining deficit, so the integral is
# taken to one second. Beyond that what is being counted is ongoing metabolic
# absorption, not the release.
ceases = int(np.argmax(flow < 0.01 * flow.max())) * fine
end = int(round(1.0 / fine))
vol = cum[end]
t90 = float(np.argmax(cum >= 0.90 * vol) * fine)
print(f"  peak flow {flow.max():.2f} L/s;  90% of the volume by {t90:.2f} s;"
      f"  flow below 1% of peak by {ceases:.2f} s;  total at 1 s {vol:.0f} mL")
check("peak inspiratory flow", flow.max(), 7.8, 0.3, " L/s")
check("time to 90% of the volume", t90, 0.20, 0.03, " s")
# the two routes to the same number: gas balance, and integrating the inrush
check("inrush integral vs gas balance", vol, ent[i180], 10.0, " mL")

# --------------------------------------------------------------------------
print("\n5  Safety margins")
pt5, r5 = run(70, 1.75, duration=420.0)
check("SaO2 at 200 s, end of the volume manoeuvre",
      r5['sao2'][at(r5, 200)], 96.8, 0.3, " %")
check("SpO2 reaches 95%", float(np.argmax(r5['spo2'] < 95.0) * DT),
      253.0, 4.0, " s")
check("SpO2 reaches the 94% stopping threshold",
      float(np.argmax(r5['spo2'] < 94.0) * DT), 261.0, 4.0, " s")

# --------------------------------------------------------------------------
print()
if _fails:
    print(f"{len(_fails)} prediction(s) no longer match the protocol document:")
    for f in _fails:
        print(f"  - {f}")
    print("Either the model has moved or the document is stale. Do not submit "
          "the protocol until they agree.")
    sys.exit(1)
print("All registered predictions reproduce from this commit.")
