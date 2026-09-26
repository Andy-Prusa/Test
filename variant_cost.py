#!/usr/bin/env python3
"""Run test_validation.py against one of the experimental lung-volume forms.

WHY THIS EXISTS. `apnoea_core.py` carries experimental switches
added 2026-09-25 to cost a decision about the offset form that Jones & Nzekwu
and Pelosi both measure. THAT DECISION HAS SINCE BEEN TAKEN -- Pelosi's shape
was adopted the same day -- so `shipped` now means Pelosi's shape and `legacy`
restores the exponential form it replaced.

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
import dataclasses
import os
import re
import runpy
import sys

import apnoea_core

# 'shipped' IS Pelosi's shape as of the ruling of 2026-09-25; 'legacy'
# restores the exponential form it replaced, so the table that ruling was made
# on stays regenerable.
VARIANTS = {
    'shipped':  {},
    'legacy':   {'frc_legacy_exp': True},
    'asympt':   {'frc_asymptote': True},
    'jonesrv':  {'k_rv_bmi_jones': True},
    'legacy_jones': {'frc_legacy_exp': True, 'k_rv_bmi_jones': True},
    # The retired closing-capacity curve -- three unsourced constants --
    # against the Buist & Ross / Quanjer TLC form that replaced it 2026-09-26.
    'cc_legacy': {'cc_legacy': True},
    # The Jones TLC-vs-BMI correction, ruled OFF 2026-09-26. This one is a
    # DATACLASS FIELD, not a plain class attribute -- see _variant_class.
    'cc_tlcbmi': {'cc_tlc_bmi': True},
    # BOTH retirements undone at once: the exponential FRC form AND the
    # three-constant closing capacity. This is the model as it stood at the
    # 2026-09-22 ruling that set the KNOWN_OPEN baselines, so it is the run
    # that says whether the two [WORSE] regressions -- Stock obstructed
    # 1-5 min slope 4.60 -> 1.94, ICSM jet PaCO2 71.70 -> 53.81 -- came from
    # the Pelosi FRC adoption or from something else again.
    'pre_pelosi': {'frc_legacy_exp': True, 'cc_legacy': True},
}


def _variant_class(base, attrs):
    """Subclass `base` with `attrs` overridden, whether or not they are fields.

    THE TRAP THIS EXISTS TO CLOSE, which cost two wrong comparisons on
    2026-09-26. A switch declared as a plain class attribute is overridden by
    an ordinary subclass. A switch declared as a DATACLASS FIELD is not: the
    generated `__init__` assigns the default baked in at class-creation time,
    so `self.cc_tlc_bmi` is reset to the base default a microsecond after the
    subclass attribute would have taken effect. The variant runs, prints its
    ATTRS banner, and reports numbers IDENTICAL to the thing it was supposed
    to differ from -- silently, with no error anywhere.

    The fix is to re-declare the field in the subclass (annotation AND value)
    and re-apply the decorator, which regenerates `__init__` with the new
    default. Non-field attributes are left to ordinary inheritance.
    """
    field_types = {f.name: f.type for f in dataclasses.fields(base)}
    ns = dict(attrs)
    ann = {k: field_types[k] for k in attrs if k in field_types}
    if ann:
        ns['__annotations__'] = ann
    sub = type('Patient', (base,), ns)
    if ann:
        sub = dataclasses.dataclass(sub)
    # Prove it took. A silent no-op here is the whole point of this function.
    probe = sub(weight=70, height=1.75, age=45)
    for k, v in attrs.items():
        got = getattr(probe, k)
        if got != v:
            raise SystemExit(
                f"variant switch {k!r} did not take: wanted {v!r}, instance has "
                f"{got!r}. The variant would have reported the base model's "
                f"numbers under the variant's name.")
    return sub


# TWO PARSER FAULTS, BOTH FOUND BY COUNTING ROWS AGAINST THE FILE.
# 1. The unit can contain spaces ("x normal", "x early slope"). A \S+
#    there dropped 2 benchmarks, one of them the anaemia band.
# 2. The suite has THREE verdicts, not two: [WORSE] marks a KNOWN_OPEN
#    failure that has drifted past its tolerance. Matching only
#    PASS|FAIL hid both regressions -- the most important rows in the
#    file -- and made a BLOCKED suite look like a clean one.
LINE = re.compile(r"^\s*\[([A-Z]+)\]\s+(.*?)\s{2,}(-?[\d.]+)\s+(.*?)\s+expect\s+(\S+)\s*$")


def parse(path):
    """Pull {benchmark name: (verdict, value, unit, expected)} out of a run."""
    out = {}
    for line in open(path):
        m = LINE.match(line.rstrip())
        if m:
            out[m.group(2)] = (m.group(1), float(m.group(3)), m.group(4), m.group(5))
    if not out:
        sys.exit(f"{path}: no benchmark lines found -- did the run finish?")
    return out


def diff(paths):
    """Tabulate several suite runs side by side, worst disagreement first.

    Written 2026-09-26 for the closing-capacity ruling. Comparing runs by eye
    across three 300-line files is how a wrong column gets read, so this reads
    them instead.
    """
    runs = [(path, parse(path)) for path in paths]
    names = list(runs[0][1])
    for _, r in runs[1:]:
        for n in r:
            if n not in names:
                names.append(n)

    def spread(name):
        vals = [r.get(name, (None, None))[1] for _, r in runs]
        vals = [v for v in vals if v is not None]
        if len(vals) < 2 or max(abs(v) for v in vals) == 0:
            return 0.0
        return (max(vals) - min(vals)) / max(abs(v) for v in vals) * 100.0

    names.sort(key=spread, reverse=True)
    w = max(len(n) for n in names)
    print(" " * (w + 2) + "".join(f"{os.path.basename(p)[:16]:>18}" for p, _ in runs)
          + f"{'spread':>9}")
    for n in names:
        row = f"  {n:<{w}}"
        for _, r in runs:
            if n in r:
                verdict, val, _unit, _exp = r[n]
                mark = {"PASS": " ", "FAIL": "*", "WORSE": "!"}.get(verdict, "?")
                row += f"{val:>17.1f}{mark}"
            else:
                row += f"{'--':>18}"
        print(row + f"{spread(n):>8.1f}%")
    print("\n  * = FAIL against its published range."
          "   ! = WORSE, a known-open failure that has drifted past tolerance.")
    for p, r in runs:
        bad = [n for n, v in r.items() if v[0] == "FAIL"]
        worse = [n for n, v in r.items() if v[0] == "WORSE"]
        print(f"  {os.path.basename(p):<22} {len(r) - len(bad) - len(worse):>3} pass, "
              f"{len(bad):>2} fail, {len(worse):>2} worse")
        for _n in bad:
            print(f"      FAIL  {_n}")
        for _n in worse:
            print(f"      WORSE {_n}")


def main(argv):
    if len(argv) > 2 and argv[1] == '--diff':
        return diff(argv[2:])
    if len(argv) != 2 or argv[1] not in VARIANTS:
        sys.exit(f"usage: {argv[0]} {{{'|'.join(VARIANTS)}}}\n"
                 f"       {argv[0]} --diff RUN.out RUN.out [...]")
    name = argv[1]
    attrs = VARIANTS[name]
    if attrs:
        apnoea_core.Patient = _variant_class(apnoea_core.Patient, attrs)
    print(f"VARIANT={name}  ATTRS={attrs}")
    print("PROVENANCE:", apnoea_core.provenance())
    runpy.run_module('test_validation', run_name='__main__')


if __name__ == '__main__':
    main(sys.argv)
