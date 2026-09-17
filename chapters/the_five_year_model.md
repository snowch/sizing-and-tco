---
title: "The five-year model"
short_title: "ch18 The five-year model"
---

(the-five-year-model)=
# ch18 · The five-year model

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch17](#unit-economics) |
| **What it produces** | Both reference models, and the seam where one buys from the other |
| **Built from** | `storage_cluster-reference`, `observability-reference` |
:::

## The question

How does a cost model consume a sizing model's output without swallowing its uncertainty?

Badly, almost always, and the mechanism is worth seeing because it is the commonest way a
carefully built model becomes a confident wrong number.

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
as an assumption with its own invented distribution, and that is a way of not joining them at all.

### What happens when you do join them

Two ways, and the difference is the chapter.

**Hand over the distribution.** The downstream model receives the whole bag of possible prices and
propagates it. The uncertainty in the upstream model becomes uncertainty in the downstream one,
which is correct, because it is uncertain.

**Hand over a number.** Somebody reads the upstream median, writes it in a document, and the
downstream model treats it as known. This is what happens in practice. It happens in a meeting,
between two teams, and often between two quarters.

Problem 18.2 measures the second one, and the result is worth predicting before running: the
interval on the downstream answer gets **narrower**.

Not wrong. Narrower. The headline number stays roughly where it was, and the doubt disappears.

That is why it survives review. A change that moved the answer would be noticed and argued about.
A change that leaves the answer alone and deletes the uncertainty around it looks like tidying up.

### Why every real estate has this seam

Nobody models an organisation. They model a storage tier, and separately a compute tier, and
separately the observability platform, and the numbers pass between them as figures in documents.
Each model is defensible on its own terms and the joins are undefended.

And the joins are where the correlations live. The upstream price and the downstream volume are
usually driven by the same growth: a year when there is more telemetry is a year when there is
more of everything, so the price and the quantity move together. Split into two models, each is
sampled with its own independent growth rate, and the joint uncertainty is understated twice over
— once by the point estimate at the seam, and once by the correlation that no longer has anywhere
to be declared ([ch14](#correlation-and-convergence)).

### The gap in this book's own toolkit

The DSL has four node kinds and none of them is *"a distribution that came from another model"*.

That is a real limitation and problem 18.2 makes the reader run into it: to carry the price
across, you have to sample the downstream model by hand, outside `sizing.evaluate`. There is a
test asserting the gap is still there, so that if a fifth node kind is ever added, the test fails
and the problem gets rewritten.

Whether the DSL *should* have one is a genuine question. The case for is that it would make the
join explicit, checkable and correlatable. The case against is that a model which reaches into
another model's samples is a model whose fingerprint has to cover both, whose scenarios have to
agree, and which cannot be reasoned about on its own — and one large model is not obviously better
than two honest small ones with a documented seam.

This book has not resolved it. What it does is name the seam and measure what crossing it badly
costs.

### The whole five years

```{include} _generated/the-five-year-model-split.md
```

Which is where Part V ends: a total, its composition, and the knowledge that half of it was never
argued about and a good deal of it rests on numbers that crossed a seam.

## What this cannot tell you

**Whether the seam is in the right place.** Two models joined at a price is one choice. Joined at
a capacity, or not joined at all, are others, and each puts the uncertainty somewhere different.

**What the correlation across the seam is.** It exists — both sides are driven by the same growth
— and there is nowhere in this toolkit to declare it. That is the clearest limitation in the book
and it is stated here rather than discovered later.

**Anything about the organisation.** Two models is not an estate. The real total includes tiers
nobody modelled, shared costs nobody allocated, and a network between them that appears in neither.

**What the structure omits.** Same as [ch15](#capex-opex-and-lifecycle) and worse, because there
are now two structures and the missing lines in each are invisible to the other.
[ch20](#the-missing-node).

## Problems

Two, in `tests/the_five_year_model/`.

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

## Where to go next

[ch19](#which-input-is-the-answer) begins Part VI and asks the only actionable question about a
wide interval: which input should you go and measure?

[ch20](#the-missing-node) is the error that every chapter in Parts V and VI has deferred.
