---
title: "Regime changes"
short_title: "ch07 Regime changes"
---

(regime-changes)=
# ch07 · Regime changes

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch05 · Queueing, and the knee](#queueing-and-the-knee) |
| **What it produces** | The ceilings a chain of multiplications cannot express, in both reference models |
| **Built from** | `observability-reference`, `queueing-curve` |
:::

## The question

Which ceilings can a chain of multiplications not model at all?

Everything in Parts I and III is a product of quantities. This chapter is about the points where a
system stops behaving like a product, and about why no amount of care over the inputs will warn
you that you are near one. Those points are why [the introduction](#preface) separates a sizing
model from a cost model.

## The material

### What a chain of multiplications can and cannot say

Every sizing model in this book is, at heart, a product. Bytes per line times lines per second
times seconds of retention. Terabytes times replication divided by compression. Each output is
linear in each input: double one thing, double the answer.

A product covers an enormous amount of the world, which is why the technique works. It cannot
express a **regime change**: a point at which the system stops obeying one rule and starts obeying
another.

Problem 7.1 puts a straight line through a system that has a regime change in it. Fit the line to
the loads the system has actually run at, which for a healthy one means nothing above half, then
extrapolate to the loads you are planning for. The fit is excellent where it was made. Out where
it matters it is not wrong by a percentage: it is wrong by a multiple, and the multiple grows.

```{image} _figures/regime-changes-knee.svg
:alt: The queueing knee, as a regime change a multiplication cannot express
:width: 100%
```

Nothing in the flat part of that curve contains any information about the vertical part. A model
fitted there, by any method, predicts the wrong thing — and predicts it confidently, because the
data it was fitted to was clean.

### Four regime changes, and what each one does

**The queueing knee.** [ch05](#queueing-and-the-knee). Response time is work divided by what is
left of the system, so it goes from flat to vertical with no warning in between. A multiplicative
model of latency says load times some constant, and that constant does not exist.

**Rebuild under failure.** A cluster that loses a node has to put that node's data somewhere,
using bandwidth it was using for something else, for as long as the rebuild takes. During that
window the system is a different system: less capacity, less bandwidth, and less tolerance for a
second failure. No term in a capacity chain represents it — which is why
[ch10](#headroom-and-failure-domains) handles it with a reserved margin rather than a formula.

**Cardinality explosion.** A label multiplies every series that carries it. Add one with a
thousand values and the series count is multiplied, not incremented. A chain of multiplications
expresses this one correctly. The trouble is what that arithmetic does to the uncertainty:

```{image} _figures/regime-changes-cardinality.svg
:alt: Label cardinality as a distribution — a product of uncertain counts
:width: 100%
```

That is three counts, none of which anybody would describe as alarming, multiplied together. The
product is far wider than any of the three: uncertainty compounds when quantities multiply, and
problem 7.2 is where you measure by how much. The same spread shows up in every tornado the series
count appears in:

```{include} _generated/regime-changes-tornado.md
```

**A working set that stops fitting.** Data served from memory and data served from disk differ by
orders of magnitude, and the transition between them is a step rather than a slope. A model with
an average access cost in it describes neither side, and describes the mixture only at the one
ratio it was calibrated for.

### What the four have in common

Each of them is a **threshold with different physics on either side**, and in each case a
multiplicative model computes the crossing quantity perfectly well. The model is not wrong about
utilisation, or about how full the disks are, or about how many series there are. It is wrong
about what those numbers *mean* past a point it cannot represent.

So the DSL has a node kind for exactly this. A `ceiling` does not model the regime change —
nothing in a spreadsheet-shaped model can. It declares where the change is, keeps a margin away
from it, and reports how much of the model's own uncertainty falls on the wrong side:

```{include} _generated/regime-changes-ceilings.md
```

Read the last two columns. Not "the system will be this busy", but "across everything this model
thinks could happen, this fraction of it puts you past the point where the model stops applying".

### Why a cost model can be sampled and a sizing model cannot

A cost model has no regime changes in it. Watts times hours times price is an accounting identity;
it is true at every scale and there is no load at which electricity starts behaving differently.
So for a cost model, sampling the inputs is genuinely sufficient — the structure is not in doubt,
only the numbers are.

A sizing model has thresholds in it, and past a threshold the structure itself changes. Sample the
inputs of a model that has stopped applying and you measure, very precisely, the uncertainty in a
number that has stopped describing anything.

So a model with a `ceiling` in it is classified as a sizing model, and `scripts/verify-models.py`
refuses one that declares a limit with no margin. The distinction is not taxonomy. It separates a
model whose uncertainty you can quantify from a model whose *applicability* you have to bound.

## What this cannot tell you

**Where your thresholds are.** Every ceiling in this book was declared by somebody. The queueing
one comes from a formula with strong assumptions; the capacity ones come from judgement about
rebuild and allocator behaviour. None was measured, and measuring one means running a system into
the regime you are trying to avoid.

**How many thresholds you have.** Four are named above because four were thought of. A real system
has more — a connection limit, a file-descriptor ceiling, a licence tier, a garbage collector that
changes behaviour at some heap size, a network that reorders under load. Each one you have not
declared is a ceiling the model cannot report on, and the model will not tell you it is missing.
[ch19](#the-missing-node) is about that gap.

**What happens past one.** A ceiling says where the model stops applying and says nothing about
the other side. That is deliberate: extrapolating into a regime nobody has characterised is the
mistake problem 7.1 measures.

**Whether the margin is enough.** A headroom is a decision, and this chapter argues only that it
must exist and have a reason. Whether a given one is generous or reckless depends on how fast your
load moves and how long you take to notice, neither of which this book can see.

## Problems

Two, in `tests/regime_changes/`.

**7.1 — Do what a spreadsheet would do.**
Fit the line, extrapolate it well past everything it was fitted to, and measure how wrong it is
where it matters.

```bash
python3 -m pytest tests/regime_changes/test_problem_1_straight_line.py
```

**7.2 — Why cardinality dominates.**
Take three counts that nobody would describe as alarming, multiply them, and compare the spread of
the product against the spread of the widest factor. Predict the direction and the rough size
before you run it.

```bash
python3 -m pytest tests/regime_changes/test_problem_2_combinatorial.py
```

## Where to go next

Part III begins at [ch08](#capacity), and puts everything in Parts I and II to work: a chain of
multiplications from a stated workload to a number of machines, with ceilings declared where the
chain stops applying.

[ch19](#the-missing-node) is the version of this chapter's limitation that no technique in the
book can address — a threshold nobody declared is indistinguishable, from inside the model, from
a threshold that is not there.
