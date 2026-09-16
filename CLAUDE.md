# CLAUDE.md

Project instructions for AI assistants working on this book. These are binding. §4 especially.

## What this is

*Sizing and TCO* — a self-study text and toolkit on capacity planning, sizing and total cost of
ownership, organised around one question: **how big, how much, and how wrong could I be?**

Read **PLAN.md** first: outline, settled decisions, conventions. Read **AUTHORING_GUIDE.md**
before writing or editing a page. **NEXT_STEPS.md** is the working list of what is left.

## The distinction the book is built on

Everything follows from this, so do not work around it. The front matter states it;
`scripts/verify-models.py` enforces it.

- **A cost model** has a deterministic structure with uncertain parameters. Accounting identities
  and physics. Sampling the inputs is sufficient.
- **A sizing model** has the same structure plus **measured constants** (empirical, stack- and
  version-specific, with a standard error) and **non-linear ceilings** (regime changes a chain of
  multiplications cannot represent). It needs headroom rules, not just a number.

In the DSL, a model with a `measured` node or a `ceiling` node **is** a sizing model. A sizing
model that declares a limit with no headroom does not build. If you find yourself wanting to relax
that: the distinction is the book's thesis, and a thesis the repository does not enforce is a
paragraph.

## The four targets

`bench.stamp.TARGET_MEANING` is the source of truth; this is the prose version. Three of them are
measurements — something outside this repository was asked a question. The fourth is not, and
keeping it separate is what stops the distinction going soft.

- **`corpus`** — a deterministic measurement over a declared body of data with a named codec.
  Reproducible anywhere, re-derived by CI on every push, and **never allowed to carry a rate or a
  duration**. How fast a codec ran is a property of the machine that ran it.
- **`rig`** — a throughput or latency figure, measured natively on the machine declared in
  `rig/machine.yml` and refused anywhere else. `bench.stamp.require_rig` enforces it.
- **`estate`** — an observation of a running system. Reproducible by nobody, checkable by nobody,
  and therefore held to the strictest disclosure rules in the book: system, window, date. This is
  the one target the build cannot verify, and a page using one says so at the point of use.
- **`model`** — computed from a model file in this repository. No machine and no body of data was
  involved, so it is evidence about what the book's own models say and about nothing else. Its
  fingerprint covers the whole DSL core, so the claim moves when the method does. A `kind: model`
  result must declare this target: a model run is a computation, not a measurement of anything
  outside the repository.

## Build

Jupyter Book 2, whose CLI is `mystmd`. Pinned in `package.json` (npm), **not** in
`requirements.txt` — one source of truth.

```bash
make check     # ./scripts/ci-check.sh — exactly what CI runs
make models    # evaluate and stamp every model
make measure   # re-take the corpus constants
make book      # live preview
make machine   # what this computer is, and whether it may take a rig measurement
```

## The five invariants

1. **No numbers typed into prose.** Every figure comes from a stamped JSON in `bench/results/`,
   declared in `bench/figures.py`, rendered to `chapters/_generated/` or `chapters/_figures/` by
   `scripts/render-figures.py`, and `{include}`d. Pages contain no executable cells.
   `scripts/verify-numbers.py` scans every published page and fails the build. The only exemption
   is `% number-ok: <reason>` on the preceding line, where a reviewer will see it.
2. **No code pasted into prose.** `{literalinclude}` with `:start-at:` / `:end-before:` **text**
   anchors, never `:lines:`. Line numbers rot on the first edit above them, and a test fails a
   page that uses them. Model files are quoted the same way.
3. **No invented figures.** A constant nobody has measured is a node with no value, and so is
   everything downstream of it. Those figures render as *not yet measured* and the blocked chain
   is named. The state propagates on its own — nothing is marked by hand, so nothing can be
   forgotten when the measurement lands. Never a placeholder, never an estimate, never a number
   from a different stack.
4. **Every input says where it came from.** A provenance kind (`fact` / `vendor_claim` /
   `assumption`) and a non-empty source. A `fact` must cite something. A `vendor_claim` is
   coloured differently in every figure and is never silently promoted.
5. **Problems are tests.** Each is a stub under `tests/<chapter-slug>/` with a test that passes
   only when solved, marked `problem` so CI deselects it, with **unmarked scaffolding tests beside
   it** that CI does run and that assert the problem is answerable. Never write the answer
   anywhere in the repository. The expected values are derived at test time from an oracle, never
   stored.

## 4. Originality — non-negotiable

This book covers ground other books cover. It must be **entirely original work**.

- **Do not reproduce, closely paraphrase, or structurally mirror any existing book, course or
  vendor guide** — not its chapter structure, section headings, figures, worked examples, problem
  sets or characteristic phrasings.
- **If you notice you are reconstructing a known text's sequence, or a well-known worked example,
  stop and design a different one.** The feeling of "this is the standard way to present this" is
  the signal, not the permission.
- Ideas, facts, algorithms and public specifications are not copyrightable; **expression is**.
  Published algorithms (Iman–Conover, Acklam's inverse normal CDF, delta-of-delta encoding) may be
  implemented and must be cited; their code must be this repository's own.
- **Vendor neutrality is absolute.** No product is named in any chapter, model or figure. A
  measured constant names the *implementation* it belongs to — which may be this repository's own
  encoder — because that is what makes it a measurement rather than a claim.
- Every factual claim cites either a stamped result in `bench/results/` or a primary source in
  `references.bib`.

## 5. Accuracy

- Every number in prose comes from a stamped result. No invented figures, and no "typically
  around thirty per cent" without a measurement or a citation.
- **When something cannot be measured here** — no reference machine, no instrumented application —
  the page says so in the text, shows the reasoning it used instead, and states what it would take
  to measure. It does not substitute a number from somewhere else.
- Prefer showing a result that surprises the reader to asserting a rule. The storage model's
  one-in-three chance of running out of space is worth more than a paragraph about prudence.
- A model's *structure* is the thing Monte Carlo cannot check. Every chapter with a model in it
  must say in *What this cannot tell you* what its structure omits.

## 6. Voice

Direct, precise, British English, active voice, short sentences. First-person plural sparingly. No
marketing tone, no filler, no "in this chapter we will". Figures are drawn by code and must show a
mechanism.

**Length follows the material.** There is no page target. A chapter is as long as what it has to
convey and no longer. The test is per section: every section earns its place or comes out, and a
short chapter still owes the reader *What this cannot tell you*.

**Statistics vocabulary is rationed.** Distribution, sample, percentile, interval, correlation,
convergence — and that is the list. Each arrives because a model has just raised a question that
needs it, never as a definition. Where a term has a plain-English equivalent, use the plain one
first and name the term second.

## Things that will break the build

- **Editing `sizing/mc.py`, `sizing/evaluate.py`, `sizing/units.py` or `sizing/dsl.py`.** They are
  in `KIND_SOURCES["model"]`, so every stamped model result's fingerprint changes and
  `verify-numbers.py` fails until each is regenerated with `make models`. That is intended: an
  interval is a claim about a method as much as about a model.
- **A rate or a duration in a `corpus` result.** `provenance_problems` checks it dimensionally,
  via Pint, and rejects it correctly.
- **A new MyST directive without a branch in `scripts/build-pdf.py`.** The renderer raises on a
  node type it does not handle, deliberately — the alternative is content silently missing from
  the PDF.
- **Changing `sizing/viewer/evaluate.js` without re-running the tests.** `tests/test_viewer.py`
  runs it against values Python computed, for every node of every model. The published page and
  the build must not disagree.
- **Bare `pytest`.** Use `python3 -m pytest`, so tests run under the interpreter with the
  dependencies. A standalone pytest cannot import `sizing`.
- **`BASE_URL`.** This is a project site at `/sizing-and-tco/`. `deploy.yml` sets it from the
  Pages base path; without it every link 404s.

## Chapter status

The toolkit is complete, both reference models run end to end, and every chapter and appendix is
written. A page that is regenerated from `scripts/new-chapter.py` carries `[To write` markers
until it is; that marker is what everything below keys off.

**A chapter's number is never an identifier.** Identity is the slug: `(#monte-carlo)`,
`chapters/monte_carlo.md`, `tests/monte_carlo/`. The number survives only where a reader sees it,
and is derived from `bench/outline.py`. `tests/test_book.py` fails an identifier containing a
digit. Inserting a chapter is an edit to `bench/outline.py` and `myst.yml`, and nothing else moves.

Do not write the list of what is written into this file. Ask the repository:

```bash
python3 -c "from pathlib import Path; from bench.outline import CHAPTERS; \
  print([c.label for c in CHAPTERS if '[To write' not in Path(c.path).read_text()])"
```
