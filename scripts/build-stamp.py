#!/usr/bin/env python3
"""Which commit this build of the book came from.

Every figure in this book says where it came from. The book itself did not: a reader looking at a
page had no way to tell whether it was today's or last quarter's, and a downloaded PDF had no way
to tell them at all.

This is deliberately *not* one of the figures in :mod:`bench.figures`. Those are committed, and
`render-figures.py --check` proves they match the results they were rendered from. A build stamp
cannot work that way — it names the commit being built, so a committed copy is stale the moment
it is committed. So it is written at build time, into a fragment that is not tracked, by
`ci-check.sh`, the Makefile and the deploy workflow alike.

Run it anywhere. Outside a git checkout it says so rather than inventing a commit.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "chapters" / "_generated" / "build.md"
REPOSITORY = "https://github.com/snowch/sizing-and-tco"

BANNER = "<!-- Written by scripts/build-stamp.py at build time. Not committed. -->"


def _git(*arguments: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return done.stdout.strip() or None


def stamp() -> str:
    """One line a reader can check this build against."""
    commit = _git("rev-parse", "--short", "HEAD")
    if commit is None:
        # A tarball, or git is not installed. Say so: a build that cannot name its commit is a
        # build a reader cannot place, and pretending otherwise is the failure this book is about.
        return (
            f"{BANNER}\n\n"
            "*This copy was built outside a git checkout, so it cannot say which commit it came "
            "from.*\n"
        )
    when = _git("show", "-s", "--format=%cs", "HEAD") or datetime.now(UTC).strftime("%Y-%m-%d")
    dirty = _git("status", "--porcelain")
    modified = " with uncommitted changes" if dirty else ""
    # The commit and the date, and nothing else. What was there before went on to explain that
    # newer commits would appear above this one in a commit list, which is a reader who can
    # follow the link being told how the link works.
    return (
        f"{BANNER}\n\n"
        f"*Built from [`{commit}`]({REPOSITORY}/commit/{commit}), committed {when}{modified}.*\n"
    )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(stamp())
    print(f"  wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
