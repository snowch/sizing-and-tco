# CLAUDE.md

Project instructions for AI assistants working on this book. These are binding. §4 especially.

## What this is

*Sizing and TCO* — a self-study text and toolkit on capacity planning, sizing and total cost of
ownership, organised around one question: **how big, how much, and how wrong could I be?**

Read **PLAN.md** first: outline, settled decisions, conventions. Read **AUTHORING_GUIDE.md**
before writing or editing a page, and edit every page against **STYLE.md**, the plain-English
checklist. **NEXT_STEPS.md** is the working list of what is left.

## Where these rules came from

This repository was bootstrapped from `snowch/computer-systems`, a book about operating systems.
Four of the five invariants came with it — no code pasted into prose, no numbers typed into
prose, no invented figures, problems are tests — along with the chapter shape and most of
AUTHORING_GUIDE.md. They transfer, because both books are about not being believed without
evidence. Invariant 5 is the one that did not, and it says why in its own entry.

Invariant 4, the distinction below, and the `model` target were written for this book.

So the rules predate the chapters: they were set at scaffold time rather than learned by writing.
When a rule and the material fight, the rule is the more likely to be wrong.

## The distinction the book is built on

Everything follows from this, so do not work around it. ch01 teaches it, the introduction points
at ch01, and `scripts/verify-models.py` enforces it.

- **A definitional model** has a deterministic structure with uncertain parameters. Accounting
  identities and physics: relationships true by definition. Sampling the inputs is sufficient.
- **A conditional model** has the same structure plus **measured constants** (empirical, stack-
  and version-specific, with a standard error) and **non-linear ceilings** (regime changes a chain
  of multiplications cannot represent). It holds only on those conditions, so it needs headroom
  rules, not just a number.

The test ch01 teaches: *is the answer guaranteed to be right if every input is right?* If no, the
model is conditional.

In the DSL, a model with a `measured` node or a `ceiling` node **is** a conditional model. A
conditional model that declares a limit with no headroom does not build.

These were once called *cost* and *sizing* models. Readers took those as steps in a job — size,
then cost — and the book used them that way too, so the classification collided with the
pipeline. "Sizing model" and "cost model" keep their ordinary meaning (the model that produces a
host count; the one that turns it into money). Do not use them for the classification. If you find yourself wanting to relax
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

**MyST parses. This repository renders.** `mystmd` is pinned in `package.json` (npm), **not** in
`requirements.txt` — one source of truth. It is a parser and a reference checker here, not a
theme: `myst build --strict` resolves every cross-reference and fails on a broken one, and
`scripts/build-site.py` turns that parse into the pages that publish. There is no `--html`
anywhere, so nothing reaches the MyST template registry and the whole site builds offline —
which is why `make check` builds the site that deploys rather than a preview of one.

The renderer is `bench/render.py`. It raises on a node type it does not handle rather than
dropping it. There is no PDF: the models are things a reader drags and paper cannot hold one, so
`scripts/build-offline.py` writes the service worker that keeps the site readable with no network
instead.

```bash
make check     # ./scripts/ci-check.sh — exactly what CI runs
make models    # evaluate and stamp every model
make measure   # re-take the corpus constants
make book      # build the site and serve it
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
5. **Problems are tests where a test is possible.** Most are: a stub under
   `tests/<chapter-slug>/` with a test that passes only when solved, marked `problem` so CI
   deselects it, with **unmarked scaffolding tests beside it** that CI does run and that assert
   the problem is answerable. Never write the answer anywhere in the repository. The expected
   values are derived at test time from an oracle, never stored. The chapter page runs the same
   test under Pyodide from a Check under the problem, over the files
   `sizing.playground.toolkit.problem_files` lists; `tests/test_problems.py` holds every
   chapter's tests to running on exactly those. The Check counts the marked tests and no
   others, and the command under the problem ends `-m problem` so a desk counts the same ones.
   A stub takes plain numbers or a callable the test builds, never the toolkit's own API; where
   the chapter taught the model file, the reader edits a file the test names in `EDITABLE`,
   shown whole in the page.

   **A problem about the reader's own system has no oracle, and is still a problem.** This rule
   arrived from a book whose exercises were code, where a passing test or a booting kernel is the
   oracle. Here the reader's output is judgement — how much headroom to keep, which input to go
   and measure, whether what they have is a definitional model or a conditional one — and demanding an oracle
   for that left the book with fifty-two problems of which fifty-one were arithmetic on its own
   models. A problem of the second kind carries no test. It says what a good answer contains and
   what would falsify it, and sits in the same `## Problems` section, numbered the same way. The
   book is not doing its job if a chapter has none.

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
- **Vendor neutrality is absolute.** No product is named in any chapter, model or figure, and
  `tests/test_book.py::test_no_product_is_named` is what makes that a rule rather than a habit. A
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
- Prefer showing a result that surprises the reader to asserting a rule. The fleet the point
  estimates bought, over the knee at the busy hour in a substantial share of the model's own
  futures, is worth more than a paragraph about prudence.
- A model's *structure* is the thing Monte Carlo cannot check. Every chapter with a model in it
  must say in *What this cannot tell you* what its structure omits.

## 6. Voice

Direct, precise, British English, active voice, short sentences. First-person plural sparingly. No
marketing tone, no filler, no "in this chapter we will". Figures are drawn by code and must show a
mechanism.

**STYLE.md is the checklist** that gets a page to this voice: one idea per paragraph, the point
first, a concrete example, ordinary words, the reader as *you*. Edit every page against it, and
run both of its closing passes over the page before you finish: the first over the sentences, the
second over whether the idea arrived. The second is the one that was missing for a long time, and
its absence is why pages came out short-sentenced and still abstract. Its rules 17 to 22 name the habits
two outside reviews of the finished book found on page after page: very short sentences that
label instead of landing, demonstratives with no noun in reach, intensifiers, decorative idiom,
*somebody* for any actor, and evaluations with no grounds. Where its rule to define a term at
once meets the vocabulary ration below, the ration wins.

**Length follows the material.** There is no page target. A chapter is as long as what it has to
convey and no longer. The six headings in `bench.outline.CHAPTER_SHAPE` are the book's shape and
stay whatever the length — the repetition is what makes every chapter read as one book. The test
is per *sub*section inside them: every one earns its place or comes out, and a short chapter still
owes the reader its *What this cannot tell you* and its *Key takeaways*.

**Statistics vocabulary is rationed.** Distribution, sample, percentile, interval, correlation,
convergence. Each arrives because a model has just raised a question that needs it, never as a
definition. Where a term has a plain-English equivalent, use the plain one first and name the term
second. `tests/test_vocabulary.py` is what makes that a rule rather than a habit: it reads each
word's home chapter out of the glossary and fails any page that uses it earlier. A word in a
different sense — a scrape interval, bytes per sample — takes `% word-ok: <reason>` on the line
before, which covers the block, and the reason sits where a reviewer sees it.

Those six are what the book *teaches*. A seventh may be named where the point is to tell it apart
from one of the six — ch13 names the standard deviation of a logarithm to say nobody has an
intuition for one, the glossary names a confidence interval to say the book's intervals are not
that, and ch19 names variance decomposition to warn a reader off reading a tornado as one. A term
named in order to be rejected is not vocabulary creep; it is the fence around the vocabulary. The
rule used to read "and that is the list", which would have forbidden all three.

**Say the thing. Do not perform it.** "Direct" above was not specific enough to hold, and the
prose drifted into three habits that make a reader extract the point instead of receiving it. The
test for any sentence: *does this state the point, or make the reader work it out?*

- **A label where a statement belongs.** "That is the whole motivation" names the paragraph
  instead of saying anything. Write what the motivation is.
  *Was:* "That is the whole motivation, and this book does not teach the method until ch13 —
  because the method is not useful until…"
  *Now:* "The method that produced that second column is ch13's, not this page's. It is no use to
  you until you have built a model, got a number out of it, and felt that you could not defend
  the number."
- **Withholding, then revealing.** "X is the one that decides…" sets a small puzzle and makes the
  reader wait. Lead with the point.
  *Was:* "The third part is the one that decides whether anybody should act on the answer."
  *Now:* "This book teaches the third part: how to find which input your answer rests on…"
- **A roundabout purpose.** "The line is there so that a reader who does not believe this table
  has somewhere to go" → "It is there so you can check the table instead of trusting it."

This is a rule about the habit, not about the words. `That is the whole of it. One
multiplication.` in ch05 is good writing: short, direct, and the device is doing work rather than
standing in for it. Banning the phrasings would flatten those too. Read the sentence and ask
whether the reader has to decode it.

**Haiku drafts the prose; you check it.** Reader-facing prose goes to a Haiku subagent to draft
before it lands: a new paragraph, a rewording, a provenance `source`, a viewer label. Haiku
writes shorter, plainer sentences than a model that has the whole repository in its head. It also
drops facts and gets them wrong. So the work splits three ways:

1. **You write the brief as a list of facts**, not as prose: what the text must say, each point
   checked against the model file or the code. Add STYLE.md. A prose brief gets its wording copied.
2. **Haiku writes the sentences.**
3. **You check the facts, and nothing else.** Where a fact is missing, add the fewest words that
   carry it. Do not rewrite Haiku's sentences. If a draft is wrong, send it back with a note
   rather than fixing it yourself. Then run STYLE.md's closing passes over what will land.

The first Haiku drafts said a slider came from "a spread" when it comes from a declared range,
and dropped the reason an input is one number. Merging them by rewriting put back the facts and,
with them, the padding the draft had cut: "a busy-hour figure somebody quotes you is really a
spread" broke rules 19 and 21 in one clause.

## Things that will break the build

- **Editing `sizing/mc.py`, `sizing/evaluate.py`, `sizing/units.py` or `sizing/dsl.py`.** They are
  in `KIND_SOURCES["model"]`, so every stamped model result's fingerprint changes and
  `verify-numbers.py` fails until each is regenerated with `make models`. That is intended: an
  interval is a claim about a method as much as about a model.
- **A rate or a duration in a `corpus` result.** `provenance_problems` checks it dimensionally,
  via Pint, and rejects it correctly.
- **A new MyST directive without a branch in `bench/render.py`.** The renderer raises on a node
  type it does not handle, deliberately — the alternative is content silently missing from a
  page. `make check` renders every page, so it fails there rather than in the deploy.

- **JavaScript in a Python string that is not raw.** `PROBLEMS` and `SEARCH` in
  `scripts/build-site.py` carry JavaScript. Without `r"""`, Python eats `\n` and the page ships a
  regex literal that cannot parse — silently, because nothing on the Python side is wrong. This
  has happened twice; `tests/test_scripts.py` now fails without the `r`.
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
digit. Inserting a chapter is an edit to `bench/outline.py` and `myst.yml`. The pages are right
immediately: the renderer derives every `chNN` in the prose from the outline rather than trusting
the text it was given, so no reference can go stale in a paragraph nobody rereads. The markdown
still says the old number, because a renderer cannot edit source — run
`python3 scripts/relabel-references.py` to catch it up, and `tests/test_book.py` fails until you do.

Do not write the list of what is written into this file. Ask the repository:

```bash
python3 -c "from pathlib import Path; from bench.outline import CHAPTERS; \
  print([c.label for c in CHAPTERS if '[To write' not in Path(c.path).read_text()])"
```
