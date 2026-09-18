#!/usr/bin/env python3
"""Say what this machine can do, and what it therefore cannot be asked for.

    python3 scripts/verify-setup.py

Reports rather than fails, with one exception: a missing Python dependency is a broken checkout
and saying so quietly would waste somebody's afternoon. Everything else is a capability, and a
capability this machine lacks is a class of figure it may not produce — which is the whole point
of the target system and is worth seeing before anything else.
"""

from __future__ import annotations

import importlib
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

#: What the toolkit cannot run without.
REQUIRED = (
    ("numpy", "the sampler and the evaluator"),
    ("pint", "unit checking"),
    ("yaml", "model files"),
)

#: What is optional, and what each one is optional *for*.
OPTIONAL = (
    ("myst", "building the book", "npm install -g mystmd"),
    ("node", "checking the browser evaluator against Python's", "install Node 22"),
    ("chromium", "printing the PDF", "pip install playwright && playwright install chromium"),
)

TICK, CROSS = "  ok  ", " miss "


def main() -> int:
    from bench.stamp import classify_machine, rig_declaration

    print(f"machine   {platform.platform(terse=True)}, python {platform.python_version()}")

    missing = []
    for module, why in REQUIRED:
        try:
            found = importlib.import_module(module)
            version = getattr(found, "__version__", "?")
            print(f"[{TICK}] {module} {version} — {why}")
        except ImportError:
            missing.append(module)
            print(f"[{CROSS}] {module} — {why}")

    for command, why, remedy in OPTIONAL:
        found = shutil.which(command) or any(
            Path(p).exists() for p in ("/opt/pw-browsers/chromium/chrome-linux/chrome",)
        )
        print(f"[{TICK if found else CROSS}] {command} — {why}" + ("" if found else f" ({remedy})"))

    print()
    kind = classify_machine()
    declared = rig_declaration()
    if declared:
        print(f"targets   corpus: yes · model: yes · rig: {'yes' if kind == 'rig' else 'no'}")
    else:
        print("targets   corpus: yes · model: yes · rig: no reference machine is declared")
    print("          estate: never, by any machine — it is an observation somebody takes")
    if kind != "rig":
        print()
        print("This machine may not take a rig measurement, so any figure that needs one renders")
        print("as 'not measured yet' rather than as a number. That is the intended behaviour and")
        print("not a broken checkout (ch03).")

    if missing:
        print()
        print(f"MISSING: {', '.join(missing)}. Run `make install`.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
