---
title: "The five-year model"
short_title: "ch18 The five-year model"
---

(the-five-year-model)=
# ch18 · The five-year model

## The question

How does a cost model consume a sizing model's output without swallowing its uncertainty?

Badly, almost always. Swallowing the upstream uncertainty is the commonest way a carefully built
model becomes a confident wrong number.

## The material

### Models are joined by numbers written down

Here is a seam that exists in this repository.

```{include} _generated/the-five-year-model-storage.md
```

The storage model produces a cost per usable terabyte per month
([ch17](#unit-economics)). And the observability model buys storage:

```{include} _generated/the-five-year-model-observability.md
```

Its retention cost is stored terabytes times a price per terabyte-month — the same quantity, in
the same units, that the other model computes. `tests/the_five_year_model/` checks that those two
units still match, because if they ever stop matching the two models have quietly stopped
describing the same trade.

So the observability model could be driven by the storage model. It is not. It declares the price
as an assumption with its own invented distribution, so the two models are not joined at all.

### What happens when you do join them

Two ways, and they differ in what becomes of the upstream uncertainty.

**Hand over the distribution.** The downstream model receives the whole bag of possible prices and
propagates it. The uncertainty in the upstream model becomes uncertainty in the downstream one,
which is correct, because it is uncertain.

**Hand over a number.** Somebody reads the upstream median, writes it in a document, and the
downstream model treats it as known. This is what happens in practice. It happens in a meeting,
between two teams, and often between two quarters.

Problem 18.2 measures the second one, and the result is worth predicting before running: the
interval on the downstream answer gets **narrower**.

Not wrong. Narrower. The headline number stays roughly where it was, and the doubt disappears.

That is why the point estimate survives review. A change that moved the answer would be noticed
and argued about. A change that leaves the answer alone and deletes the uncertainty around it
looks like tidying up.

### Why every real estate has this seam

Nobody models an organisation. They model a storage tier, and separately a compute tier, and
separately the observability platform, and the numbers pass between them as figures in documents.
Each model is defensible on its own terms and the joins are undefended.

And the joins are where the correlations live. The upstream price and the downstream volume are
usually driven by the same growth: a year when there is more telemetry is a year when there is
more of everything, so the price and the quantity move together. Put them in two models and each
gets its own independent growth rate, which understates the joint uncertainty twice over — once by
the point estimate at the seam, and once by the correlation that no longer has anywhere to be
declared ([ch14](#correlation-and-convergence)).

### The gap in this book's own toolkit

The DSL has four node kinds and none of them is *"a distribution that came from another model"*.

Problem 18.2 walks you into the gap: to carry the price across, you have to sample the downstream
model by hand, outside `sizing.evaluate`. A test asserts the gap is still there, so adding a fifth
node kind fails that test and the problem gets rewritten.

Whether the DSL *should* have one is a genuine question. The case for is that it would make the
join explicit, checkable and correlatable. The case against is that a model reaching into another
model's samples needs a fingerprint covering both, needs scenarios that agree, and cannot be
reasoned about on its own. One large model is not obviously better than two honest small ones with
a documented seam.

This book has not resolved it. It names the seam and measures what crossing it badly costs.

### The whole five years

```{include} _generated/the-five-year-model-split.md
```

Part V ends there: a total, its composition, and the knowledge that half of it was never argued
about and a good deal of it rests on numbers that crossed a seam.

## What this cannot tell you

**Whether the seam is in the right place.** Two models joined at a price is one choice. Joined at
a capacity, or not joined at all, are others, and each puts the uncertainty somewhere different.

**What the correlation across the seam is.** It exists — both sides are driven by the same growth
— and there is nowhere in this toolkit to declare it. That is the clearest limitation in the
book.

**Anything about the organisation.** Two models is not an estate. The real total includes tiers
nobody modelled, shared costs nobody allocated, and a network between them that appears in neither.

**What the structure omits.** Same as [ch15](#capex-opex-and-lifecycle) and worse, because there
are now two structures and the missing lines in each are invisible
to the other. [ch20 · The missing node](#the-missing-node).

## Problems

Three, in `tests/the_five_year_model/`. The first two have tests. The last does not, and says why.

**18.1 — Carry a distribution across a boundary.**
Pull the storage model's unit cost out as a sample array, not a summary. The whole array — the
next problem is about what a summary costs.

```bash
python3 -m pytest tests/the_five_year_model/test_problem_1_carry.py
```

**18.2 — What a point estimate costs at the seam.**
Drive the downstream model both ways and compare the intervals. Predict the direction first. Then
say, in a comment, whether you think the DSL should have a node kind for this.

```bash
python3 -m pytest tests/the_five_year_model/test_problem_2_seam.py
```

**18.3 — What your total leaves out.** No test: what a total leaves out is not something a total
can be asked.

Build the five-year total for something you run, then list what is not in it. This chapter's model
joins two models at a price and says so; yours will join more, and the seams are where the money
hides.

Start with the things that are not hardware: the people who run it, the migration at the end of
life, the second environment nobody counts, the software that is licensed per machine. Then ask
whether the horizon is a plan or a habit — five years is a convention, and the equipment's actual
life is a different number.

A good answer has a total and a list of exclusions longer than you expected. If the list is short,
you have costed the hardware and called it the total, which is the error the whole part is
about.

## Where to go next

[ch19](#which-input-is-the-answer) begins Part VI and asks the only actionable question about a
wide interval: which input should you go and measure?

[ch20](#the-missing-node) is the error that every chapter in Parts V and VI has deferred.
