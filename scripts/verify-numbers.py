#!/usr/bin/env python3
"""Refuse to publish a number the book cannot defend.

Six rules. Each one exists because the failure it catches is silent — a wrong number looks
exactly like a right one, and the reader has no way to tell.

1. **Every figure's result exists.** A page citing a run nobody made fails here rather than
   rendering an empty table.
2. **Every result carries its stamps** — target, kind, what produced it, the units of everything
   in it, and a hash of the code. A number whose conditions are unknown cannot be checked by
   anybody, including its author in six months.
3. **Every result was produced by the code that is checked in.** A content hash over the shared
   core, whatever is core to that kind, and the runner's own sources — so editing the code
   invalidates the number instead of quietly contradicting it. Comparing commit *times* instead
   cannot tell an unrelated new file from a change to the thing being measured, and is wrong in
   both directions.
4. **Provenance matches the target and the kind.** A `corpus` result may carry no figure with
   time in its units; a `rig` result must have been recorded on the reference machine; an
   `estate` observation must disclose the system and the window, because nothing else can check
   it.
5. **A pending figure whose result has landed is an error.** Otherwise a measurement gets taken
   and the book goes on saying it is missing.
6. **No measured figure is typed into prose on any published page**, where regenerating results
   would silently leave it behind.

## The one carve-out in rule 6, and why it is narrow

A percentage is a figure, and *"the 90% interval"* is not: it is the name of a convention this
book defines once in ch13 and then uses as vocabulary, the way a paper says "95% confidence
interval" without quoting a measurement. So that exact shape is exempt and nothing else is — not
"a 34% chance", not "9% of futures", not any percentage that came out of a model. Every other
exemption has to be written into the page as `% number-ok: <reason>`, where a reviewer sees it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.figures import cited_results, pending_results  # noqa: E402
from bench.stamp import (  # noqa: E402
    REQUIRED_STAMPS,
    RESULTS_DIR,
    code_fingerprint,
    provenance_problems,
)


def published_pages() -> list[Path]:
    """Every page the book publishes, the front matter included.

    ``tests/test_book.py`` checks this against ``myst.yml``'s table of contents, so a page added
    to the book cannot quietly be added outside the check. In the template this book is built on
    the preface was the one page exempt from rule 6 for as long as it existed — and it was the
    page carrying a comparison table.
    """
    return sorted(
        [ROOT / "index.md", *(ROOT / "chapters").glob("*.md"), *(ROOT / "appendices").glob("*.md")]
    )


#: Units that make a claim about size, money or speed. A figure carrying one belongs in a
#: generated fragment, because it can only have come from a run that might be redone.
COST_UNITS = (
    r"USD|TB|TiB|GB|GiB|MB|kWh|kW|W|MB/s|GB/s|B/s|bytes?|nodes?|drives?|cores?|"
    r"series|spans?|samples?|lines?|hosts?|queries"
)
#: A figure has to *start* a figure: a leading digit preceded by a word character or a dot is
#: part of something else, such as a version string or a chapter reference.
_START = r"(?<![\w.])"
MEASURED_FIGURE = re.compile(
    rf"{_START}\$\s?\d+(?:[.,]\d+)*"
    rf"|{_START}\d+(?:[.,]\d+)*\s*(?:{COST_UNITS})\b"
    rf"|{_START}\d+(?:\.\d+)?\s*[x×]\b"
    rf"|{_START}\d+(?:\.\d+)?\s*%"
)

#: The book's own name for an interval. See the module docstring.
CONVENTION = re.compile(r"\b\d{1,2}%\s+(?:interval|intervals)\b")

#: A MyST comment on the line before, for a figure that is legitimately a cited definition rather
#: than a measurement. It leaves the reason in the source where a reviewer will see it.
EXEMPTION = re.compile(r"^%\s*number-ok:\s*\S+")


def check_results(problems: list[str]) -> int:
    """Rules 1 to 5."""
    pending = pending_results()

    for name in sorted(cited_results()):
        if not (RESULTS_DIR / f"{name}.json").exists():
            problems.append(
                f"missing result: bench/results/{name}.json is cited by a figure. Generate it "
                f"with the runner named by `grep -rl {name} bench/ models/`."
            )

    for name, reason in sorted(pending.items()):
        if (RESULTS_DIR / f"{name}.json").exists():
            problems.append(
                f"bench/results/{name}.json exists but its figure is still marked pending "
                f"({reason!r}). Remove the `pending=` argument in bench/figures.py and "
                "re-render — the measurement has landed."
            )

    checked = 0
    for path in sorted(RESULTS_DIR.glob("*.json")):
        name = path.stem
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{name}.json is not valid JSON: {exc}")
            continue
        checked += 1

        for stamp in REQUIRED_STAMPS:
            if stamp not in payload:
                problems.append(f"{name}.json is missing the required {stamp!r} stamp")
        if not all(stamp in payload for stamp in ("target", "kind", "summary")):
            continue

        recorded = payload.get("code_fingerprint")
        if recorded is None:
            problems.append(f"{name}.json has no code_fingerprint — regenerate it")
        else:
            try:
                expected = code_fingerprint(
                    payload.get("code_sources"), payload.get("target"), payload.get("kind")
                )
            except FileNotFoundError as exc:
                problems.append(f"{name}.json names a source that no longer exists: {exc}")
                expected = None
            if expected is not None and recorded != expected:
                problems.append(
                    f"{name}.json was produced by different code than is checked in (stamped "
                    f"{recorded}, now {expected}) — re-run the runner that writes it, or delete "
                    "the file if nothing produces it any more"
                )

        problems += provenance_problems(f"{name}.json", payload)

    return checked


def check_prose(problems: list[str]) -> None:
    """Rule 6: a measured figure typed into a sentence is one nobody will ever regenerate."""
    for source in published_pages():
        lines = source.read_text().splitlines()
        fenced = False
        for n, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                fenced = not fenced
                continue
            # Generated tables, their caption lines, directive options and comments carry real
            # figures legitimately.
            if fenced or stripped.startswith(("|", ":", "*Conditions", "%", "<!--", "---")):
                continue
            if n >= 2 and EXEMPTION.match(lines[n - 2].strip()):
                continue
            for hit in MEASURED_FIGURE.findall(CONVENTION.sub("", line)):
                problems.append(
                    f"{source.relative_to(ROOT)}:{n} types the measured figure {hit.strip()!r} "
                    "into prose. Put it in a generated fragment (AUTHORING_GUIDE.md), or, if it "
                    "is a definition rather than a measurement, precede the line with "
                    "`% number-ok: <reason>`."
                )


def main() -> int:
    problems: list[str] = []
    checked = check_results(problems)
    check_prose(problems)

    if problems:
        print("verify-numbers: FAILED")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    pending = pending_results()
    note = f", {len(pending)} figure(s) awaiting a measurement" if pending else ""
    print(f"verify-numbers: OK ({checked} result file(s) stamped and verified{note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
