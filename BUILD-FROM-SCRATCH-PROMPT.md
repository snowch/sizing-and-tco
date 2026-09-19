# Prompt: build *Sizing and TCO* from scratch

Paste everything below the line into Claude Code, in an empty directory.

---

Build me a self-study book and toolkit called **Sizing and TCO**, published as a website that a
browser keeps for reading offline. Work in this directory. Take your time and get the architecture
right before writing prose — the architecture is most of what makes this book different from the
ones that already exist.

## What the book is

A book about capacity planning, sizing and total cost of ownership, organised around one question:

> **How big, how much, and how wrong could I be?**

*How big* is sizing. *How much* is total cost of ownership. Both are arithmetic and most engineers
can already do them. The book is really about the third part — how to find which input your
answer rests on, how far the answer moves when that input moves, and what it would cost to find
out. Almost nobody is taught this, and it is what decides whether anybody should act on a number.

## Who it is for

An engineer who has been asked how big something needs to be, or what it will cost, and who wants
to give an answer they would still defend a year later. They are comfortable with code and
arithmetic. **Assume they know nothing about statistics.** Six words are all they need —
distribution, sample, percentile, interval, correlation, convergence — and each must arrive
because a model has just raised a question that needs it, never as a definition. Where a
statistical term has a plain-English equivalent, use the plain one first and name the term second.

They are reading to *do something at work*, not to admire a method.

## Learning goals

By the end a reader should be able to:

1. Write down a workload as named quantities with units, and tell a rate from a level.
2. Say where every number came from — measured, quoted by a vendor, or assumed — and know what
   that difference is worth.
3. Build a chain from a workload to a machine count, and know where the chain stops being true.
4. Recognise a ceiling: a point where a chain of multiplications stops describing the system.
   Queueing knees, rebuild-under-failure, cardinality explosions, working sets leaving memory.
5. Put uncertainty through a model by sampling it, and read the interval that comes out.
6. Cost the result over its life, including the parts that are not on the invoice.
7. **Find which input the answer actually rests on, and what measuring it better would buy.**
8. Know the error that none of the above can see — a missing term — and what to do instead.
9. Hand a number to somebody who has to sign for it, with the one sentence that says what it hides.

## The distinction the whole book is built on

Everything follows from this. Do not work around it.

- **A cost model** has a deterministic structure with uncertain parameters. Accounting identities
  and physics: watts × hours × price, capital plus running cost over a horizon. Sampling the
  inputs is genuinely sufficient.
- **A sizing model** has the same structure plus **measured constants** (empirical, specific to
  one stack at one version, with a standard error) and **non-linear ceilings** (regime changes
  that a chain of multiplications cannot represent). It needs headroom rules, not just a number.

**Enforce this in the build, not in prose.** A model file with a `measured` node or a `ceiling`
node *is* a sizing model; one with neither *is* a cost model; a script decides which and holds the
two to different rules. A sizing model that declares a limit with no headroom must fail to build.
A thesis the repository does not enforce is a paragraph.

## Non-negotiable: build the model in front of the reader

This is the single most important structural decision, and the easiest to get wrong.

**Do not hand the reader a finished fifty-node model and explain it backwards.** Start the model
in the first chapter with a handful of nodes they fully understand, and add nodes as the chapters
earn them. Each chapter shows the file as it stands at the end of it, and what it computes.

Make the staged models **derived from the finished model by a manifest** that says which chapter
introduces which node — never hand-maintained copies, which drift. Then write tests that pin the
story:

- **Every node in the model is introduced by some chapter.** A node nobody introduces is one the
  reader meets fully formed in a figure, with the book never saying where it came from. This is
  the load-bearing test.
- No stage ever takes a node away; stages run in the book's own reading order.
- Every stage passes every rule the finished model passes.
- **Each stage classifies as the kind of model the book says it is** — and ask the loader rather
  than asserting it. This pins the moment a cost model becomes a sizing model to the chapter that
  claims it. If someone later moves the ceiling, the test names the chapter whose claim just
  became false.

The payoff: the reader adds a measured constant and a ceiling, runs the build, and **the build
tells them their cost model has become a sizing model**. The book's thesis is discovered, not
defined. It is the one idea that genuinely cannot be taught before the reader has a model in hand.

Two traps this will surface, both of which are the design working:
- A node introduced early that nothing consumes until much later will fail the "every node feeds
  an output" rule at the intermediate stages.
- A correlation between two inputs cannot exist at a stage where one of them is still a single
  number. A correlation is a statement about two things that vary.

## The five invariants

1. **No numbers typed into prose.** Every figure comes from a stamped JSON result, declared in
   one figures module, rendered to generated fragments, and included. Pages contain no executable
   cells. A script scans every published page and fails the build. One exemption mechanism, a
   comment on the immediately preceding line, where a reviewer will see it.
   *Watch for numbers spelled as words — "fifteen petabytes", "seven nodes", "four lines" — the
   digit scanner will not catch them and they rot exactly the same way.*
2. **No code pasted into prose.** Quote from the working tree with text anchors (`start-at` /
   `end-before`), never line numbers, and have a test enforce it. Line numbers rot on the first
   edit above them. *Text anchors stop line numbers rotting; they do not stop you framing the
   wrong node, so check what each quote actually captures.*
3. **No invented figures.** A constant nobody has measured is a node with no value, and so is
   everything downstream of it. Those render as *not yet measured* and the blocked chain is named.
   The state must propagate automatically — nothing marked by hand, so nothing can be forgotten
   when the measurement lands. Never a placeholder, never a number from a different stack.
4. **Every input says where it came from.** A provenance kind (`fact` / `vendor_claim` /
   `assumption`) and a non-empty source. A `fact` must cite something. A `vendor_claim` is
   coloured differently in every figure and never silently promoted.
5. **Problems are tests.** Each is a stub with a test that passes only when solved, marked so CI
   deselects it, with unmarked scaffolding tests beside it that CI *does* run and that assert the
   problem is answerable. Never write the answer anywhere in the repository. Derive expected
   values at test time from an oracle; never store them.

## Where numbers come from: four targets

Every result declares one. Three are measurements of something outside the repository; the fourth
is not, and keeping it separate is what stops the distinction going soft.

| Target | What it is | Who can check it |
|---|---|---|
| `corpus` | a codec or encoder over a declared body of data | anybody, and CI does, every push |
| `model` | a model file evaluated and sampled | anybody with the repository |
| `rig` | a throughput or latency on the declared reference machine | whoever has that machine |
| `estate` | an observation of a system somebody runs | **nobody** |

Rules worth enforcing: a `corpus` result may carry no rate and no duration (how fast a codec ran
is a property of the machine that ran it — check it dimensionally). A `rig` measurement is refused
on any machine that is not the declared one, by comparing the actual processor and core count —
not by an environment variable, which anyone can set by accident. An `estate` observation is held
to the strictest disclosure rules in the book (system, window, date) and a page using one says so
at the point of use, because that disclosure is the whole of its verification.

## Voice

Direct, precise, British English, active voice, short sentences. First-person plural sparingly.
No marketing tone, no filler, no "in this chapter we will".

**Length follows the material.** No page target. Every section earns its place or comes out.

**Say the thing. Do not perform it.** Three habits to hunt:

- *A label where a statement belongs.* "That is the whole motivation" names the paragraph instead
  of saying anything. Write what the motivation is.
- *Withholding, then revealing.* "X is the one that decides…" sets a small puzzle and makes the
  reader wait. Lead with the point.
- *A roundabout purpose.* "The line is there so that a reader who does not believe this table has
  somewhere to go" → "It is there so you can check the table instead of trusting it."

The test for any sentence: **does this state the point, or make the reader work it out?**

**Headings are different.** A heading *is* a label — that is its job — so the three habits above
do not apply. The test for a heading is whether somebody scanning the page can tell what is in the
section. "The question", "What it looks like", "Core concept" all fail it. Name the subject.

**Prefer showing a result that surprises the reader to asserting a rule.** A model with a
one-in-three chance of running out of space is worth more than a paragraph about prudence.

Every chapter ends with **What this cannot tell you**, and a test fails a chapter that leaves it
out. For a chapter with a model in it, that section must name what the model's *structure* omits —
the error no amount of sampling can see.

## Originality — non-negotiable

This covers ground other books cover. It must be entirely original work.

- Do not reproduce, closely paraphrase or structurally mirror any existing book, course or vendor
  guide — not its chapter structure, headings, figures, worked examples, problem sets or
  characteristic phrasings.
- If you notice you are reconstructing a known text's sequence, or a well-known worked example,
  stop and design a different one. The feeling of "this is the standard way to present this" is
  the signal, not the permission.
- Ideas, facts, algorithms and public specifications are not copyrightable; expression is.
  Published algorithms may be implemented and must be cited; the code must be this repository's own.
- **Vendor neutrality is absolute.** No product named in any chapter, model or figure. A measured
  constant names the *implementation* it belongs to — which may be this repository's own encoder —
  because that is what makes it a measurement rather than a claim.

## Shape of the repository

- A small **DSL**: models are YAML files of named quantities. Four node kinds — `input` (a value
  or distribution, with a unit and provenance), `derived` (a formula whose declared unit is
  *checked* against what it produces), `measured` (points at a stamped result and carries its
  standard error), `ceiling` (an expression, a limit, a declared headroom, and a required reason).
- **Units are checked, not just dimensions.** Cost per TB per year and cost per TB per month have
  identical dimensions and differ by a factor of twelve. A dimensional check alone would publish a
  figure twelve times too large and pass.
- A **Monte Carlo module** small enough to read end to end: inverse transform sampling, four
  distributions, Iman–Conover rank correlation, nothing else. A reader who cannot see the sampler
  cannot check the interval, and an interval nobody can check is decoration.
- **Two models**, both vendor-neutral, structure as the point and numbers replaceable: a web
  service and its data on a fleet of Linux hosts (sized and costed end to end, and the one whose
  behaviour under load is *not* a chain of multiplications, so the ceilings part is built on it
  too), and an observability platform (deliberately with a hole in it where a measurement should
  be).
- A build that regenerates every figure, re-derives every corpus constant, and fails on drift.
  One command a contributor runs locally that is exactly what CI runs, so the two cannot diverge.
- **Result fingerprints** covering the code that produced them, so editing the sampler invalidates
  every interval it published. An interval is a claim about a method as much as about a model.

## Structure

Roughly this, though earn each part rather than following it blindly. Chapter numbers are derived
from position and are **never identifiers** — identity is the slug, everywhere: the label, the
file, the test directory, the figure ids, the URL. Have a test fail any identifier containing a
digit, so inserting a chapter is an edit to the outline and nothing else moves.

- **Introduction** — the reader's situation, the three-part question, why a point estimate is
  silent, the cost/sizing distinction, why to believe any of it, who it is for, what you need.
- **Part I — What you are sizing**: what a workload is (and the model begins); where the numbers
  come from; peak, mean and growth.
- **Part II — Ceilings**: Little's law; queueing and the knee; when adding servers stops helping;
  regime changes.
- **Part III — Sizing**: capacity; bandwidth and the binding constraint; headroom and failure
  domains; the sizing model.
- **Part IV — Uncertainty**: Monte Carlo; correlation and convergence.
- **Part V — Cost**: capex, opex and where the total stops; power; unit economics; the five-year
  model.
- **Part VI — What the answer rests on**: which input to go and measure; the missing node.
- **Part VII — Presenting an interval**: a TCO for a finance audience.
- **Part VIII — Afterwards**: what the model got wrong.
- **Appendices**: the DSL in full; the Monte Carlo module end to end; distributions and when each
  is honest; units and the conversions that bite; each model in full; a glossary; running the
  toolkit.

Two chapters people expect that this book should **not** have: a toolchain/setup chapter before
the subject, and a "here is the file format" chapter before the reader has any reason to care.
Put the install in the introduction, the format in an appendix, and let the chapters teach the
node kinds one at a time as the model grows. *If you find yourself writing a part page that tells
readers they may skip to the next part, that part is in the wrong place.*

## How to check the writing

Automated checks catch numbers and code drift. They cannot catch prose that is abstract, or a
concept used before it is explained. For that, use a **cold read**: give a reader one page plus
every page before it and *nothing else* — no search, no other files, no reading ahead — and ask,
paragraph by paragraph:

- Is it clear, concrete English, or does the reader have to work out what is meant?
- Does it explain every concept it uses, here or on a prior page? A term used before it is defined
  is a problem even if the book defines it later, because this reader has not got there.
- Does it flow from the paragraph before, and does the page open where the last one left off?
- Any errors — a claim contradicting a prior page or the page's own tables, a reference to a table
  row that does not say what the prose says it says, a forward reference dressed as a backward one?
- **What does this paragraph add for a reader at this point?**

Two things that make this worth the effort. Readers over-call, so have each finding attacked by an
independent skeptic that tries to refute it — one checking whether a prior page already explained
it, one asking whether a careful reader would genuinely be lost. And the findings that matter most
will be about *your own recent edits*, because the same gap in thinking produced the prose and
your judgement of it. A model cannot audit itself.

## How to work

Start with the toolkit — DSL, unit checking, sampler, stamping, the figure pipeline, the
build — and one model running end to end. The prose is much easier to write against machinery that
already refuses bad input, and several chapters exist to explain things the toolkit does.

Then the models, then the chapters in reading order. Do not write a chapter whose figures do not
yet exist.

Keep a `CLAUDE.md` holding the invariants, the distinction, the voice rules and the things that
break the build, and treat it as binding. Commit in reviewable pieces with messages that say *why*,
including what you got wrong and how you found out — that record is worth more than a tidy history.

Ask me when a decision is genuinely mine: structure, what to cut, anything where different readings
lead to materially different books. Make the routine calls yourself.
