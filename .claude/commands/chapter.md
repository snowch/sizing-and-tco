---
description: Write a chapter of Sizing and TCO, end to end
---

Write chapter $ARGUMENTS of *Sizing and TCO* (give the slug, not the number — identity is the
slug).

Before writing anything, read `CLAUDE.md`, `PLAN.md`, `AUTHORING_GUIDE.md` and the previous
chapter. Then:

1. **Write the problems and their tests first**, under `tests/<slug>/`, and make sure each one
   fails for the right reason. A problem whose test passes before it is solved is not a problem.
   Mark the reader's assertions `@pytest.mark.problem`; leave an unmarked scaffolding test beside
   each one asserting that the problem is answerable and not trivially answerable. Derive every
   expected value at test time — never store an answer.

   At least one problem takes the reader's own system rather than the book's. That one has no
   oracle and therefore no test: it says what a good answer contains and what would falsify it.
   CLAUDE.md invariant 5.
2. **Build or extend the model** this chapter is about, under `models/`. `make verify` must pass
   before any prose is written about it. Every input gets a provenance kind and a source; every
   ceiling gets a headroom and a reason.
3. **Declare the figures** in `bench/figures.py` and stamp the results with `make models` or a
   runner under `bench/`. For a constant nobody has measured, do nothing special — the state
   propagates and the tables say so. Never a placeholder number.
4. **Write the chapter** to serve the problems and the figures, in the five-part shape. Quote
   code and model files with `{literalinclude}` and text anchors; include figures with
   `{include}` and `{image}`. No number is ever typed into prose.
5. Run `./scripts/ci-check.sh`, then commit.

Obey CLAUDE.md §4 absolutely: original work, no vendor named, no structural mirroring of any
existing text.

Stop and report what the model now says, what is still unmeasured and why, and what the chapter
says it could not tell the reader.
