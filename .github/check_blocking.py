#!/usr/bin/env python3
"""Compare the blocking set from a test_validation.py run against the ruling.

WHY THIS EXISTS. test_validation.py exits non-zero whenever anything blocks,
and on this project things block for a documented reason: a correction that
makes a benchmark worse is information, and CLAUDE.md forbids reaching for a
compensating parameter to clear it. A suite that is permanently red therefore
says nothing at all, and a green tick bought by deleting rows would say
something false.

So the rule here is the same one KNOWN_OPEN uses at the head of
test_validation.py: the baseline holds the SET, and any movement in either
direction is an event.

    a NEW name appears      -> red. Something broke that nobody has ruled on.
    a name DISAPPEARS       -> red. Something started passing and the file
                               must be updated, or the fix goes unnoticed and
                               the baseline rots into a mute button.
    the set matches exactly -> green.

Deliberately checks NAMES, not values. The values are graded inside
test_validation.py, where KNOWN_OPEN already carries the number on the day of
the ruling and reports WORSE if it drifts. Duplicating that here would put the
same number in two places, which is the failure mode handover_numbers.py
exists to prevent.
"""
import re
import sys
from pathlib import Path

BASELINE = Path(__file__).with_name("known-blocking.txt")


def ruled():
    """Names from the baseline file; blank lines and # comments ignored."""
    out = []
    for line in BASELINE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def observed(text):
    """The blocking set as test_validation.py prints it.

    The line is 'N BLOCKING: name, name, ...' and the names themselves contain
    commas ('Heard control, time to SpO2<95%'), so a plain split is wrong. The
    count is authoritative: take it, then split on ', ' and rejoin until the
    number of pieces matches.
    """
    m = re.search(r"^(\d+) BLOCKING: (.*)$", text, re.M)
    if not m:
        if re.search(r"^0 BLOCKING|all benchmarks", text, re.M | re.I):
            return []
        return None
    n, rest = int(m.group(1)), m.group(2)
    pieces = rest.split(", ")
    if n == 0:
        return []
    # Names are two comma-separated fragments in this suite wherever the count
    # does not match the naive split. Rejoin greedily from the left.
    if len(pieces) == n:
        return pieces
    per = len(pieces) / n
    if per != int(per):
        return None
    per = int(per)
    return [", ".join(pieces[i * per:(i + 1) * per]) for i in range(n)]


def main():
    text = Path(sys.argv[1]).read_text()
    want = ruled()
    got = observed(text)
    if got is None:
        print("could not find a 'N BLOCKING:' line in the suite output.")
        print("The suite did not finish, or its summary format changed.")
        return 1
    new = [n for n in got if n not in want]
    fixed = [n for n in want if n not in got]
    for n in sorted(want):
        mark = "ruled open" if n in got else "NOW PASSES"
        print(f"  {mark:<12} {n}")
    for n in sorted(new):
        print(f"  {'NEW':<12} {n}")
    if not new and not fixed:
        print(f"\n{len(got)} blocking, exactly as ruled. See HANDOVER.md.")
        return 0
    print()
    if new:
        print("NEW FAILURES -- these are not ruled open and nothing in the")
        print("repository explains them:")
        for n in sorted(new):
            print(f"  - {n}")
    if fixed:
        print("THESE NOW PASS. Remove them from .github/known-blocking.txt in")
        print("the same commit that fixed them, so the baseline cannot rot:")
        for n in sorted(fixed):
            print(f"  - {n}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
