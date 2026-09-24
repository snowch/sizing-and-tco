---
title: "Regime changes"
short_title: "ch08 Regime changes"
---

(regime-changes)=
# ch08 · Regime changes

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

Which ceilings can a chain of multiplications not model at all?

Everything in Parts I and III is a product of quantities. This chapter is about the points where a
system stops behaving like a product. It is also about why no amount of care over the inputs will
warn you that you are near one. Those points are why [ch01](#point-estimates) separates a conditional
model from a definitional one.

## The material

### What a chain of multiplications can and cannot say

Every sizing model in this book is, at heart, a product. Bytes per line times lines per second
times seconds of retention. Terabytes times replication divided by compression. Each output is
linear in each input: double one thing, double the answer.

A product covers an enormous amount of the world, which is why the technique works. It cannot
express a **regime change**: a point at which the system stops obeying one rule and starts obeying
another.

Problem 8.1 puts a straight line through a system that has a regime change in it. Fit the line to
the loads the system has run at, which for a healthy system means nothing above half.
Then extrapolate to the loads you are planning for. The fit is excellent where it was made. Out
where it matters, it is not wrong by a percentage. It is wrong by a multiple, and the multiple
grows.

```{image} _figures/regime-changes-knee.svg
:alt: The queueing knee, as a regime change a multiplication cannot express
:width: 100%
```

Nothing in the flat part of that curve contains any information about the vertical part. A model
fitted there, by any method, predicts the wrong thing. It predicts it confidently, because the
data it was fitted to was clean.

### Four regime changes, and what each one does

**The queueing knee.** [ch06](#queueing-and-the-knee). Response time is work divided by what is
left of the system, so it goes from flat to vertical with no warning in between. A multiplicative
model of latency says load times some constant, and that constant does not exist.

**A host lost at the busy hour.** A fleet that loses a host does not lose one host's worth of
capacity and carry on. That host's share of the requests lands on the survivors. Every one of
them moves up [ch06](#queueing-and-the-knee)'s curve at once, and a fleet that was comfortably
under the knee can be over it with nothing else having changed. The survivors' utilisation is one
line of arithmetic. What happens to them past the knee is not arithmetic at all, which is why
[ch11](#headroom-and-failure-domains) gives it a margin rather than a formula.

**Cardinality explosion.** A label multiplies every series that carries it. Add one with a
thousand values and the series count is multiplied, not incremented. A chain of multiplications
expresses this one correctly. The trouble is what that arithmetic does to the uncertainty:

```{image} _figures/regime-changes-cardinality.svg
:alt: Label cardinality as a distribution — a product of uncertain counts
:width: 100%
```

That is three counts multiplied together, and nobody would describe any of them as alarming. The
product is far wider than any of the three. Uncertainty compounds when quantities multiply, and
[ch01](#point-estimates)'s problem 1.2 measured that compounding. The same spread shows up in
every tornado the series count appears in:

```{include} _generated/regime-changes-tornado.md
```

**A working set that stops fitting.** Data served from memory and data served from disk differ by
orders of magnitude, and the transition between them is a step, not a slope. A model with an
average access cost in it describes neither side. It describes the mixture only at the one ratio
it was calibrated for.

This is the one this chapter adds to the running example: the share of the records a busy hour
touches, the memory the fleet has for them, and a ceiling on the ratio, whose reason says what is
on the other side of it.

```{literalinclude} ../models/web_service/stages/11-regime/model.yaml
:language: yaml
:start-at: hot_fraction:
:end-before: outputs:
```

The service time [ch05](#littles-law) built on is a memory-served time. Past this ceiling it is a
different number from a different regime, and every chain that used the old one is quietly wrong.

```{iframe} /models/web_service_regime-reference.html
:width: 100%
The graph as ch08 leaves it. Drag *share of records touched in a busy hour* and watch the working
set cross the memory the fleet has.
```

```{iframe} /playground/regime-changes/
:width: 100%
The same file, running. The ceiling's reason is the only place in it that says what happens on the
other side.
```

### What the four have in common

Each of them is a **threshold with different physics on either side**. In each case a
multiplicative model computes the crossing quantity perfectly well. The model is not wrong about
utilisation, or about how full the disks are, or about how many series there are. It is wrong
about what those numbers *mean* past a point it cannot represent.

So the model file format has a node kind for this. A `ceiling` does not model the regime
change; nothing in a spreadsheet-shaped model can. It declares where the change is, keeps a margin
away from it, and reports how much of the model's own uncertainty falls on the wrong side:

```{include} _generated/regime-changes-ceilings.md
```

Read the last two columns. Not "the system will be this busy", but "across everything this model
thinks could happen, this fraction of it puts you past the point where the model stops applying".

### Why running a definitional model over its ranges is enough, and a conditional model's is not

A definitional model has no regime changes in it. Watts times hours times price is an accounting identity.
It is true at every scale, and there is no load at which electricity starts behaving differently.
So for a definitional model, running the arithmetic over the inputs' ranges is enough. The structure is not in doubt; only the
numbers are.

A conditional model has thresholds in it, and past a threshold the structure itself changes. Run the
inputs of a model that has stopped applying across their ranges and you measure, precisely, the
doubt in a number that has stopped describing anything.

So a model with a `ceiling` in it is classified as a conditional model, and the toolkit refuses one
that declares a limit with no margin. The distinction is not taxonomy. It separates a model whose
uncertainty you can quantify from a model whose *applicability* you have to bound.

## What this cannot tell you

**Where your thresholds are.** Every ceiling in this book was declared by somebody. The queueing
one comes from a formula with strong assumptions. The memory and disk ones come from judgement
about how full either can be before it stops behaving like the model. None was measured, and
measuring one means running a system into the regime you are trying to avoid.

**How many thresholds you have.** Four are named above because four were thought of. A real system
has more: a connection limit, a file-descriptor ceiling, a licence tier, a garbage collector that
changes behaviour at some heap size, a network that reorders under load. Each one you have not
declared is a ceiling the model cannot report on, and the model will not tell you it is missing.
[ch20](#the-missing-node) is about that gap.

**What happens past one.** A ceiling says where the model stops applying and says nothing about
the other side. That is deliberate: extrapolating into a regime nobody has characterised is the
mistake problem 8.1 measures.

**Whether the margin is enough.** A headroom is a decision, and this chapter argues only that it
must exist and have a reason. Whether a given one is generous or reckless depends on how fast your
load moves and how long you take to notice, neither of which this book can see.

## Key takeaways

:::{div}
:class: takeaways

- **A chain of multiplications cannot express a regime change.** It computes the crossing quantity
  perfectly and is wrong about what the number means past a point it cannot represent.
- **Four thresholds in the running example, each with different physics on either side.** The
  queueing knee, a host lost at the busy hour, a label multiplying every series it touches, and a
  working set that stops fitting in memory.
- **A ceiling does not model the other side. It declares where the change is.** It keeps a margin
  away from it and reports how much of the model's own uncertainty falls beyond it.
- **A model fitted where the system was healthy predicts the wrong thing, confidently.** Nothing in
  the flat part of the curve holds any information about the vertical part.
- **A ceiling is what makes a model conditional.** Running the inputs over their ranges
  quantifies a definitional model's doubt. A conditional model's applicability has to be bounded
  as well.
:::

## Problems

Three, in `tests/regime_changes/`. The first two have tests. The last does not, and says why.

**8.1 — Do what a spreadsheet would do.**
Fit the line and extrapolate it well past everything it was fitted to. The test measures how
wrong it is where it matters.

```bash
python3 -m pytest tests/regime_changes/test_problem_1_straight_line.py -m problem
```

**8.2 — A host lost at the busy hour.**
Lose one host from the fleet at the busy hour and work out where the survivors land: their
utilisation, and the residence time [ch06](#queueing-and-the-knee)'s division then gives them.
Predict before you run it whether the residence time rises by the same factor as the utilisation.
The test then shrinks the fleet at the same utilisation until the survivors are past one, where
the division has nothing left to divide by.

```bash
python3 -m pytest tests/regime_changes/test_problem_2_host_loss.py -m problem
```

**8.3 — Every threshold you have.** No test: nothing here knows what your system runs into
first.

Four ceilings appear in this book because four were thought of. List yours: every limit your
system runs into before it runs out of the thing you normally count. Memory before storage. File
handles. A connection pool. A licence tier. A queue depth somebody set in 2019.

For each, write what happens when it is crossed: not what you would do about it, but what the
system does. The ones where the honest answer is "I do not know" are the expensive ones.

A good answer has more than four entries and at least one nobody in your team had written down
before. If the list has exactly the ceilings this book names, you have listed the book's system
rather than yours.

## Where to go next

Part III begins at [ch09](#capacity), and puts everything in Parts I and II to work: a chain of
multiplications from a stated workload to a number of machines, with ceilings declared where the
chain stops applying.

[ch20](#the-missing-node) is the version of this chapter's limitation that no technique in the
book can address. From inside the model, a threshold nobody declared is indistinguishable from a
threshold that is not there.
