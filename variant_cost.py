#!/usr/bin/env python3
"""Run test_validation.py against one of the experimental lung-volume forms.

WHY THIS EXISTS. `apnoea_core.py` carries two experimental switches --
`frc_asymptote` and `k_rv_bmi_jones` -- added 2026-09-25 to cost a decision
about the offset form that Jones & Nzekwu and Pelosi both measure and this
model does not have. Both default OFF and the shipped path is bit-identical.

The benchmark cost of turning them on is a table in SOURCES.md. A table in
markdown rots, so this is the script that regenerates it:

    python3 variant_cost.py shipped
    python3 variant_cost.py pelshape

It is deliberately NOT in `.githooks/pre-commit` and NOT called by
`handover_numbers.py`: each variant is a full suite run of 10-15 minutes, and
four of them in parallel saturate a four-core box for a quarter of an hour.
Run it by hand when the question is asked again.

HOW IT WORKS, because the mechanism is worth stating. The switches are CLASS
ATTRIBUTES rather than dataclass fields, so a subclass can flip one without
touching any of the ~40 `Patient(...)` call sites in `test_validation.py`.
Rebinding `apnoea_core.Patient` BEFORE importing the suite means the suite's
own `from apnoea_core import Patient` picks up the subclass. That is the same
idiom `_forced_shunt` uses in `handover_numbers.py`.

A CAVEAT THAT MUST NOT BE LOST: `model.js` implements NEITHER switch, so any
variant other than `shipped` is a DIFFERENT MODEL from the browser port, and
`test_parity.py` runs at the defaults so it cannot see the difference. If one
of these forms is ever adopted, `model.js` changes in the same commit.
"""
import runpy
import sys

import apnoea_core

VARIANTS = {
    'shipped':  {},
    'asympt':   {'frc_asymptote': True},
    'pelshape': {'frc_pelosi_shape': True},
    'jonesrv':  {'k_rv_bmi_jones': True},
    'both':     {'frc_pelosi_shape': True, 'k_rv_bmi_jones': True},
}


def main(argv):
    if len(argv) != 2 or argv[1] not in VARIANTS:
        sys.exit(f"usage: {argv[0]} {{{'|'.join(VARIANTS)}}}")
    name = argv[1]
    attrs = VARIANTS[name]
    if attrs:
        apnoea_core.Patient = type('Patient', (apnoea_core.Patient,), attrs)
    print(f"VARIANT={name}  ATTRS={attrs}")
    print("PROVENANCE:", apnoea_core.provenance())
    runpy.run_module('test_validation', run_name='__main__')


if __name__ == '__main__':
    main(sys.argv)
