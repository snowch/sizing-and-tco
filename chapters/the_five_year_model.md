---
title: "The five-year model"
short_title: "ch18 The five-year model"
---

(the-five-year-model)=
# ch18 · The five-year model

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

How does one model use a figure another model computed, without losing its uncertainty?

Usually the figure crosses as one number: somebody writes it down, and the second model treats it as
known. The headline number survives that crossing. The uncertainty around it does not, because one
number has no way to carry it.

## The material

### Models are joined by numbers written down

Here is a seam that exists in this repository.

```{include} _generated/the-five-year-model-service.md
```

The web service model produces a cost per stored terabyte per month, for the records on its own
fleet ([ch17](#unit-economics)). The observability model buys storage:

```{include} _generated/the-five-year-model-observability.md
```

Its retention cost is stored terabytes times a price per terabyte-month. That is the same
quantity, in the same units, that the other model computes. `tests/the_five_year_model/` checks
that those two units still match. If they ever stop matching, the two models have quietly stopped
describing the same trade.

So the observability model could be driven by the web service model. Suppose its retention store
ran on the same kind of fleet, at what a terabyte costs there. It is not driven that way. It
declares the price as an assumption with its own invented distribution, so the two models are not
joined at all. Here are the two, on one axis:

```{image} _figures/the-five-year-model-seam.svg
:alt: The web service model's computed cost per stored terabyte-month and the observability model's assumed storage price, on one logarithmic axis
:width: 100%
```

Same quantity, same unit, two models that have never met. The top is computed, and it is wide
because everything upstream of it is. The bottom was written down, from whichever storage tier's
figure somebody had to hand, and its width is that person's guess. The two do not even overlap,
which is the first thing a join would have asked about, and nothing did. The tick is what crosses
a seam in practice: one number.

### What happens when you do join them

There are two ways to join them, and they differ in what becomes of the upstream uncertainty.

**Hand over the distribution.** The downstream model receives every possible price, draw by draw,
and carries it through. The uncertainty in the upstream price becomes uncertainty in the downstream
answer, because the upstream price is uncertain.

**Hand over a number.** Somebody reads the upstream median, writes it in a document, and the
downstream model treats it as known. This is what happens in practice: in a meeting, between two
teams, and often between two quarters.

Problem 18.1 does both joins. The headline number stays roughly where it was, but the interval
narrows because the upstream price's uncertainty is no longer in it. The interval is wrong, not the
headline.

That is why the handover survives review: a change that moved the answer would be noticed, but a
change that removes the doubt looks like tidying up.

The distribution join pairs the i-th stored figure with the i-th price, as if the two sides were
unrelated. The next section asks whether they are.

### Why every organisation has this seam

Nobody models a whole organisation. Teams model a web service, and separately the store under it,
and separately the observability platform. The numbers pass between those models as figures in
documents. Each model is defensible on its own terms. The joins between them are not defended by
anyone.

The joins are also where correlations get lost: two figures in two models can depend on the same
thing, and neither model can say so. If the observability platform watches this web service, both
models' growth describes the same users. The two files declare their growth separately, each with
its own range.

On this seam, growth pushes the two sides in opposite directions. The table shows it.

Why the price falls as growth rises: the web service fleet is a fixed number of hosts, decided in
[ch12](#the-sizing-model). So its five-year total does not depend on growth at all. More growth
means more terabytes stored, and the same total spread over more terabytes is a lower price per
terabyte. Why the stored terabytes rise: the observability model's stored data grows with its growth
factor.

So, if both growth factors describe the same users, the price and the quantity move in opposite
directions. When two numbers that are multiplied move apart, their swings partly cancel: a high
price meets a small volume, and a low price meets a large one. The product varies less than it would
if the two were unrelated. [ch14](#correlation-and-convergence) showed that inputs pushing the same
way widen an interval. Inputs pushing opposite ways narrow it.

So on this seam, pairing the draws as if the two sides were unrelated makes the joined interval
wider than a shared growth rate would allow, not narrower. The general point: an undeclared
correlation can err in either direction. Its sign decides which, and here the sign comes from the
structure of the web service model: a fleet fixed in size.

Neither join in Problem 18.1 accounts for this. The one that would needs a correlation between
inputs in two different files, and a model file can only declare a correlation between two of its
own inputs.

### The gap in this book's own toolkit

The model file format has four node kinds. None of them is *"a distribution that came from
another model"*.

Problem 18.1 walks you into the gap. The downstream model cannot be handed the upstream model's
draws, because no node in a model file can hold them. So the join is arithmetic on two arrays,
outside `sizing.evaluate`: the terabytes one model stores and the price the other computes,
multiplied draw by draw. A test asserts the gap is still there. Adding a fifth node kind fails
that test, and the problem gets rewritten.

Whether the format *should* have one is an open question. The case for: it would make the join
explicit, checkable and correlatable. The case against: a model reaching into another model's
samples needs a fingerprint covering both, needs scenarios that agree, and cannot be reasoned
about on its own. One large model is not obviously better than two honest small ones with a
documented seam.

This book has not resolved it. It names the seam and measures what crossing it badly costs.

### The whole five years

The web service model's five-year total is split into capital paid once and running cost over the
horizon, line by line, using the split [ch15](#capex-opex-and-lifecycle) introduced.

```{include} _generated/the-five-year-model-split.md
```

Part V ends with this total and its composition. The running cost is most of the total;
[ch15](#capex-opex-and-lifecycle) showed that the capital is the part that usually gets argued
about.

And here is the whole file as a graph, for the first time. It holds everything
[ch02](#what-a-workload-is) started with and everything the chapters between added to it. Every
input has a slider. Two of the inputs are zero and stay zero until [ch22](#comparing-two-tcos),
where a second quote arrives and needs them.

```{iframe} /models/web_service-reference.html
:width: 100%
This is the finished model. The box *five-year total cost of ownership* sits near the right-hand end
of the graph, one column in from the last. If it is out of sight, scroll the graph sideways; a note
under the graph says how many boxes are out of sight to the right. Click the box, then *Show only
what feeds it*, to see how much of the graph feeds the total and how much does not.
```

## What this cannot tell you

**Whether the seam is in the right place.** Two models joined at a price is one choice. Joined at
a capacity, or not joined at all, are others. Each puts the uncertainty somewhere different.

**How strongly the two sides are correlated.** The direction follows from the structure: the price
falls as the stored terabytes rise, because the web service fleet is fixed in size. The strength
depends on how far the two models' growth describes the same users. Neither file claims that: each
declares its own growth, with its own range. A model file can declare a correlation only between two
of its own inputs, so there is nowhere in this toolkit to put a correlation across a seam.

**Anything about the organisation.** Two models are not all the systems an organisation runs. The
real total includes tiers nobody modelled, shared costs nobody allocated, and a network between them
that appears in neither model.

**What the structure omits.** The same as [ch15](#capex-opex-and-lifecycle), and worse: there are
now two structures, and the lines missing from each are invisible to the other.
[ch20](#the-missing-node) is about how to find a line a model is missing, which no interval shows.

## Key takeaways

:::{div}
:class: takeaways

- **Models are joined by numbers written down, and the joins are undefended.** Each model is
  defensible on its own terms. The seam between them is where the doubt goes missing.
- **Hand over a number instead of a distribution and the downstream interval gets narrower, not
  wrong.** The headline stays where it was and the doubt disappears, which is why it survives
  review.
- **An undeclared correlation across a seam can err in either direction.** On this seam, price and
  volume move apart: a fixed fleet's total is spread over more terabytes as growth rises, while the
  stored terabytes rise. Pairing them as unrelated makes the joined interval too wide here, the
  mirror of [ch14](#correlation-and-convergence)'s case, where inputs moving together made
  independence too narrow.
- **This toolkit has no node for a distribution that came from another model.** The gap is named,
  tested for, and left open on purpose, because one large model is not obviously better than two
  honest small ones with a documented seam.
- **What Part V hands on is a five-year total and its composition.** Most of the money is running
  cost, the part that seldom gets argued about.
:::

## Problems

Two, in `tests/the_five_year_model/`. The first has a test. The second does not, and says why.

**18.1 — What a point estimate costs at the seam.**
The test evaluates both models and hands you the two sides of the seam: the terabytes the
observability model stores and the price per terabyte-month the web service model computes. Join
them twice: once with the price carried across as a distribution and once as its median. Return the
interval on the storage cost each time.

Before you run it, write down how much narrower you expect the second interval to be than the first,
as a fraction of the first. Then say, in a comment, whether you think the model file format should
have a node kind for this, and whether pairing the i-th stored figure with the i-th price is right
for this seam, given what the section on the seam's correlation found.

```bash
python3 -m pytest tests/the_five_year_model/test_problem_1_seam.py -m problem
```

**18.2 — What your total leaves out.** No test: what a total leaves out is not something a total
can be asked.

Build the five-year total for a system you run, then list what is not in it. This chapter's two
models share one quantity, and nothing in either file joins them; Problem 18.1 joins them by hand.
Your total will take figures from more than one model or team. Wherever a figure crosses from one
into another, note which figure it is and whether its range crossed with it, or only one number.

Start with the costs that are not hardware: the people who run it, the migration at the end of life,
the second environment nobody counts, the software licensed per machine. Then ask whether the
horizon is a plan or a habit. Five years is a convention; the equipment's life is a different
number.

A good answer has a total, a list of exclusions longer than you expected, and for each figure that
crossed from elsewhere, whether its range came with it. If the list of exclusions is short, you have
costed the hardware and called it the total, which is the error [ch15](#capex-opex-and-lifecycle) is
about.

## Where to go next

[ch19](#which-input-is-the-answer) begins Part VI and asks the only actionable question about a
wide interval: which input should you go and measure?

[ch20](#the-missing-node) is about the error this page's *What this cannot tell you* ended on: a
line missing from the model, which no interval shows. It asks how you find that error.
