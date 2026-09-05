"""
run.py — simplest way to drive the apnoea model.

NEEDS: apnoea_core.py and bloodgas.py in the same folder.
       pip install numpy scipy matplotlib

RUN:   python3 run.py

Edit the PATIENT and AIRWAY blocks below and re-run. Everything else is
plumbing.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")                 # drop this line if you want a live window
import matplotlib.pyplot as plt
from apnoea_core import Patient, AirwayEpoch, simulate, time_to, plateau_sao2

# ============================ PATIENT ======================================
patient = Patient(
    weight=107,          # kg
    height=1.75,         # m
    age=45,              # years
    hb=14.0,             # g/dL
    tilt_deg=25,         # 0 supine, 25 typical ramped / head-up, negative head-down
    # --- things worth playing with -----------------------------------------
    # vq_log_sd=0.70,    # spread of ventilation-perfusion ratios
    # tau_mix=45.0,      # s, cardiogenic mixing between compartments
    # max_closed=0.25,   # how collapsible the lung is
    # n_vq=20,           # compartments; drop to 10 if it feels slow
)

# ============================ AIRWAY =======================================
# resistance in cmH2O/(L/s):  2 open  |  20 partly obstructed
#                            200 poor mask, tongue back  |  np.inf sealed
# fgo2: oxygen fraction at the pharynx. 0.21 = room air, 1.0 = buccal device.
OBSTRUCTED = np.inf

def airway(fgo2):
    return [
        AirwayEpoch(120,  resistance=OBSTRUCTED, fgo2=fgo2),  # obstructed
        AirwayEpoch(10,   resistance=8,          fgo2=fgo2),  # LMA passing
        AirwayEpoch(30,   resistance=OBSTRUCTED, fgo2=fgo2),  # LMA, not patent
        AirwayEpoch(120,  resistance=OBSTRUCTED, fgo2=fgo2),  # spasm, roc given
        AirwayEpoch(1520, resistance=2,          fgo2=fgo2),  # laryngoscopy
    ]

FEO2_AT_APNOEA = 0.87        # end-tidal O2 achieved by preoxygenation

# ============================ RUN ==========================================
print(patient.summary())
arms = {
    "no buccal oxygen": simulate(patient, airway(0.21), feo2_start=FEO2_AT_APNOEA),
    "buccal oxygen":    simulate(patient, airway(1.00), feo2_start=FEO2_AT_APNOEA),
}

print(f"\n{'arm':20s} {'SpO2<95':>9} {'SpO2<90':>9} {'end SpO2':>9} "
      f"{'end PaCO2':>10} {'end pH':>7} {'shunt':>7}")
for name, r in arms.items():
    f = lambda t: "held" if t is None else f"{t:.0f}s"
    print(f"{name:20s} {f(time_to(r,'spo2',95)):>9} {f(time_to(r,'spo2',90)):>9} "
          f"{r['spo2'][-1]:8.1f}% {r['paco2'][-1]:9.0f} {r['ph'][-1]:7.2f} "
          f"{r['shunt'][-1]*100:6.0f}%")

sh = arms["buccal oxygen"]['shunt'][-1]
print(f"\nsteady-state plateau at that shunt: {plateau_sao2(patient, sh)[0]*100:.1f}%")

fig, ax = plt.subplots(2, 2, figsize=(11, 7))
for name, r in arms.items():
    st = '-' if 'buccal' in name and 'no' not in name else '--'
    for a, key, lab in ((ax[0,0],'spo2','SpO$_2$ (%)'), (ax[0,1],'va','lung volume (mL)'),
                        (ax[1,0],'paco2','PaCO$_2$ (mmHg)'), (ax[1,1],'shunt','shunt')):
        a.plot(r['t']/60, r[key], st, label=name); a.set_ylabel(lab)
ax[0,0].axhline(90, ls=':', c='grey'); ax[0,0].set_ylim(20,101)
ax[0,0].legend(fontsize=8)
for a in ax.flat:
    a.set_xlabel("minutes from induction"); a.grid(alpha=.3)
fig.tight_layout(); fig.savefig("result.png", dpi=140)
print("\nplot written to result.png")
