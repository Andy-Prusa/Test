#!/usr/bin/env python3
"""Sweep the cost of the 2026-09-25 FRC adoption across BMI.

Pelosi's measured FRC shape was adopted for frc_anaes() on 2026-09-25.
Four spot patients were measured at the time; this is the sweep, and it
shows the effect PEAKS IN THE MIDDLE rather than at the obese end.

Not in the pre-commit hook and not called by handover_numbers.py: it is
17 BMI points x 2 arms x 1500 s and takes several minutes. The table it
produces is quoted in SOURCES.md and HANDOVER.md, so run it by hand when
that table is questioned.

    python3 adoption_sweep.py
"""
import numpy as np, apnoea_core
from apnoea_core import Patient, AirwayEpoch, simulate, time_to
OBS=np.inf
print("PROVENANCE:", apnoea_core.provenance())
class L(Patient): frc_legacy_exp=True
print("\nBMI SWEEP: what adopting Pelosi's FRC shape did, 1.65 m, age 45, hb 14,")
print("supine, obstructed airway after preoxygenation. Time to SpO2 90%.\n")
print("  BMI   frc_anaes legacy/adopted   shunt legacy/adopted   t90 legacy  adopted   change")
rows=[]
for b in range(20,53,2):
    w=b*1.65**2
    o=[]
    for cls in (L,Patient):
        p=cls(weight=w,height=1.65,age=45,hb=14.0,tilt_deg=0.0)
        r=simulate(p,[AirwayEpoch(1500,resistance=OBS,fgo2=0.21)],dt=0.05,
                   feo2_start=0.87,stop_sao2=0.0)
        o.append((p.frc_anaes(),p.shunt_base_eff()*100,time_to(r,'spo2',90)))
    d = (o[1][2]-o[0][2]) if (o[0][2] and o[1][2]) else None
    rows.append((b,o[0],o[1],d))
    ds = f"{d:+7.1f}" if d is not None else "     --"
    t0 = f"{o[0][2]:7.1f}" if o[0][2] else "     --"
    t1 = f"{o[1][2]:7.1f}" if o[1][2] else "     --"
    print(f"  {b:3d}   {o[0][0]:7.0f} / {o[1][0]:7.0f} mL   "
          f"{o[0][1]:5.2f} / {o[1][1]:5.2f} %   {t0} {t1}  {ds} s")
valid=[r for r in rows if r[3] is not None]
if valid:
    worst=min(valid,key=lambda r:r[3])
    print(f"\n  LARGEST LOSS: BMI {worst[0]}, {worst[3]:+.1f} s "
          f"({100*worst[3]/worst[1][2]:+.1f}% of {worst[1][2]:.1f} s)")
    print(f"  FRC gap peaks where? ", end="")
    g=max(rows,key=lambda r:(r[1][0]-r[2][0]))
    print(f"BMI {g[0]}, {g[1][0]-g[2][0]:.0f} mL")
