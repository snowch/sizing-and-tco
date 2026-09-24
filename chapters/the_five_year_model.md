---
title: "The five-year model"
short_title: "ch18 The five-year model"
---

(the-five-year-model)=
# ch18 · The five-year model

:::{note}
**Draft.** This chapter is written and complete. It is undergoing final review and polish.
:::

## The question

How does a cost model consume a sizing model's output without swallowing its uncertainty?

Badly, almost always. Swallowing the upstream uncertainty is the commonest way a carefully built
model becomes a confident wrong number.

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

**Hand over the distribution.** The downstream model receives the whole bag of possible prices
and propagates it. The uncertainty in the upstream model becomes uncertainty in the downstream
one. That is correct, because it is uncertain.

**Hand over a number.** Somebody reads the upstream median, writes it in a document, and the
downstream model treats it as known. This is what happens in practice. It happens in a meeting,
between two teams, and often between two quarters.

Problem 18.1 measures the second one. Predict the result before you run it: the interval on the
downstream answer gets **narrower**.

Not wrong. Narrower. The headline number stays roughly where it was, and the doubt disappears.

That is why the point estimate survives review. A change that moved the answer would be noticed
and argued about. A change that leaves the answer alone and deletes the uncertainty around it
looks like tidying up.

### Why every real estate has this seam

Nobody models an organisation. They model a web service, and separately the store under it, and
separately the observability platform. The numbers pass between them as figures in documents.
Each model is defensible on its own terms. The joins are undefended.

And the joins are where the correlations live. The upstream price and the downstream volume are
usually driven by the same growth. A year with more telemetry is a year with more of everything,
so the price and the quantity move together. Put them in two models and each gets its own
independent growth rate. That understates the joint uncertainty twice over: once by the point
estimate at the seam, and once by the correlation that no longer has anywhere to be declared
([ch14](#correlation-and-convergence)).

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

```{include} _generated/the-five-year-model-split.md
```

Part V ends there: a total, its composition, and the knowledge that most of it was never argued
about and a good deal of it rests on numbers that crossed a seam.

And here is the whole file as a graph, for the first time. It holds everything
[ch02](#what-a-workload-is) started with and everything the chapters between added to it. Every
input has a slider. Two of the inputs are zero and stay zero until [ch22](#comparing-two-tcos),
where a second quote arrives and needs them.

```{iframe} /models/web_service-reference.html
:width: 100%
The finished model. Click *five-year total cost of ownership* to see how much of the graph feeds
it, and how much does not.
```

## What this cannot tell you

**Whether the seam is in the right place.** Two models joined at a price is one choice. Joined at
a capacity, or not joined at all, are others. Each puts the uncertainty somewhere different.

**What the correlation across the seam is.** It exists, because both sides are driven by the same
growth, and there is nowhere in this toolkit to declare it. That is the clearest limitation in
the book.

**Anything about the organisation.** Two models is not an estate. The real total includes tiers
nobody modelled, shared costs nobody allocated, and a network between them that appears in
neither.

**What the structure omits.** The same as [ch15](#capex-opex-and-lifecycle), and worse. There are
now two structures, and the missing lines in each are invisible to the other.
[ch20 · The missing node](#the-missing-node).

## Key takeaways

:::{div}
:class: takeaways

- **Models are joined by numbers written down, and the joins are undefended.** Each model is
  defensible on its own terms. The seam between them is where the doubt goes missing.
- **Hand over a number instead of a distribution and the downstream interval gets narrower, not
  wrong.** The headline stays where it was and the doubt disappears, which is why it survives
  review.
- **The seam is also where the correlations live.** Both sides are usually driven by the same
  growth, and two separate models each give it an independent rate, understating the joint
  uncertainty twice over.
- **This toolkit has no node for a distribution that came from another model.** The gap is named,
  tested for, and left open on purpose, because one large model is not obviously better than two
  honest small ones with a documented seam.
- **What Part V hands on is a total, its composition, and what crossed a seam.** Most of the money
  was never argued about, and a good deal of it rests on numbers that crossed a join.
:::

## Problems

Two, in `tests/the_five_year_model/`. The first has a test. The second does not, and says why.

**18.1 — What a point estimate costs at the seam.**
The test evaluates both models and hands you the two sides of the seam: the terabytes one model
stores and the price per terabyte-month the other computes. Join them twice, once with the price
carried across as a distribution and once as its median, and return the interval on the storage
cost each time. Predict the direction first. Then say, in a comment, whether you think the model
file format should have a node kind for this.

```bash
python3 -m pytest tests/the_five_year_model/test_problem_1_seam.py -m problem
```

**18.2 — What your total leaves out.** No test: what a total leaves out is not something a total
can be asked.

Build the five-year total for something you run, then list what is not in it. This chapter's
model joins two models at a price and says so. Yours will join more, and the seams are where the
money hides.

Start with the things that are not hardware: the people who run it, the migration at the end of
life, the second environment nobody counts, the software that is licensed per machine. Then ask
whether the horizon is a plan or a habit. Five years is a convention. The equipment's actual life
is a different number.

A good answer has a total and a list of exclusions longer than you expected. If the list is
short, you have costed the hardware and called it the total. That is the error the whole part is
about.

## Where to go next

[ch19](#which-input-is-the-answer) begins Part VI and asks the only actionable question about a
wide interval: which input should you go and measure?

[ch20](#the-missing-node) is the error that every chapter in Parts V and VI has deferred.
