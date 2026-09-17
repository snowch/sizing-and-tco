---
title: "Which input is the answer?"
short_title: "ch19 Which input is the answer?"
---

(which-input-is-the-answer)=
# ch19 · Which input is the answer?

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch13](#monte-carlo) |
| **What it produces** | Tornado charts across both reference models, and what the widest bars have in common |
| **Built from** | `storage_cluster-reference`, `observability-reference`, `service_tier-reference`, `value-of-information` |
:::

## The question

Which input should you go and measure first, and how would the model tell you?

An interval is a description of a problem. This chapter is the only actionable thing you can do
with one.

## The material

### More samples never help

Worth restating, because it is the instinct. [ch14](#correlation-and-convergence) established that
a wide interval is not sampling noise — the interval is a property of the model's inputs, and more
draws locate it more precisely rather than narrowing it.

So there are exactly two things that narrow an interval. **Measure something**, and replace a guess
with a figure that has a standard error. Or **decide something**, and replace an uncertainty with a
constraint — pin the retention, cap the growth by policy, fix the sampling rate.

Both are work. The question is which one is worth doing, and the answer is not obvious because
the model has dozens of uncertain inputs and only one of them matters.

### Swing one thing at a time

```{image} _figures/which-input-is-the-answer-storage.svg
:alt: Which input moves the five-year total most
:width: 100%
```

Each bar swings one input across the middle eighty per cent of its own distribution, with
everything else held still. Problem 19.1 is building it.

One detail in that construction matters more than it looks: the swing comes from the input's
**declared distribution**, not from its slider range. Otherwise an input somebody gave a generous
slider gets a long bar for free, and the chart measures somebody's UI choices rather than the
model.

The ordering is the useful part. It answers "what should I go and measure first", and that is the
only question a tornado answers well.

### What the widest bars have in common

```{image} _figures/which-input-is-the-answer-observability.svg
:alt: Which input moves the retention store most
:width: 100%
```

```{include} _generated/which-input-is-the-answer-service.md
```

Two charts and a table, because the third is short enough to read as one. Look at what is at the
top of each.

**Cardinality**, in the observability model — a product of uncertain counts, whose uncertainty
compounds ([ch08](#regime-changes)).

**Arrival rate**, in the service tier, with service demand a distant second — the two that meet in
a division by what is left of the system ([ch06](#queueing-and-the-knee)).

**The chassis price**, in the storage model. Which breaks the pattern the other two make, and the
break is the most useful thing on this page.

The pattern the first two make is that **the widest bar is somewhere the model is not linear**: an
exponent, a product of uncertain things, a division by a small remainder. Inputs that are merely
multiplied by constants, or added, hardly move anything, however uncertain they are. So the
storage model ought to be topped by its growth rate, which is raised to a power — and
[ch04](#peak-mean-and-growth)'s tornado, which swings the same inputs against the *recommended*
node count, is topped by growth with nothing else close.

This chart is against the five-year total, and growth is not on it at all. It cannot be. The cost
chain starts at *nodes purchased*, which is a decision somebody took, and a decision has no
distribution. The exponent left the cost model at the moment the cluster was chosen, and what
remains downstream of that choice is a bill of materials, where the largest line item wins.

Which is the rule worth carrying: **a tornado is about the output you point it at, and pinning a
decision can remove the dominant input from everything downstream of it.** Neither chart is wrong.
They answer different questions, and the reason the cost question has a boring answer is that the
interesting one was settled before it was asked.

### The correlation the chart cannot show

```{include} _generated/which-input-is-the-answer-correlation.md
```

Declared correlations widen every interval in the book. A tornado has no way to show that: each
bar moves one input, and a correlation is a statement about two.

So the two figures answer different questions and should not be read against each other. The
tornado says which input is worth measuring; the interval says what the model currently believes.
An input with a short bar that is strongly correlated with a long one is still worth attention,
and neither chart will say so.

### What one-at-a-time misses

The sharper version of the same limitation, and problem 19.2 measures it.

Swing input A alone. Swing B alone. Swing both. If the model were additive in them, the third
would be the sum of the first two. In a model built out of multiplications it is not — and the
model in this book is built out of multiplications.

So a tornado's bars do not add up to the interval, and they are not a decomposition of it. They
are a ranking, and that is all they are. Treating the bar lengths as shares of the variance is a
mistake the chart invites, and a variance-based decomposition — which does answer that question —
is not in this toolkit and is noted in `NEXT_STEPS.md`.

### And what would that buy?

A ranking is not a quantity, and the question that follows a ranking is the one somebody has to
approve: *what would measuring it be worth?*

That is computable, and the computation is the simplest thing that means anything. Take one
uncertain input, pin it at its median — pretend somebody went and measured it, perfectly — and
re-sample the whole model. What comes back is the interval the model would report if that one
thing were known.

```{include} _generated/which-input-is-the-answer-worth-storage.md
```

The last column is a **ceiling**. No real measurement is perfect: one leaves a standard error
behind, that error propagates like any other ([ch03](#where-the-numbers-come-from)), and the
interval closes by less than this. Which is exactly what makes the figure useful — a small number
in that column says the measurement is not worth commissioning *however well it goes*, and that
is a decision somebody can take before spending anything.

Read down it. One input is worth most of the interval and everything below it is rounding. A
campaign to pin down *support rate* would be a quarter's work for a result nobody could see on a
chart.

Then the same experiment on the other model, where the answer has a different shape:

```{include} _generated/which-input-is-the-answer-worth-observability.md
```

Two inputs tie at the top, and **the same number is not the same decision**. One is a count of
label values somebody could go and query this afternoon. The other is a growth rate, which
belongs to no target and cannot be measured at all ([ch04](#peak-mean-and-growth)) — the only
thing available for it is to *decide* it, by policy, and accept the flexibility that costs.

Now the two rows at the bottom of that table, which are the ones worth taking away.

**The measured constants buy nothing.** Bytes per sample and bytes per log line were measured over
a declared corpus, with a standard error, by the most careful machinery in this book — and
removing that standard error entirely does not move the interval. Their *values* matter enormously;
they scale the answer. Their *uncertainty* is not what the answer rests on. Measuring them again,
better, is work that would produce a nicer provenance and the same interval.

**And the rows do not add up.** They come to rather more or rather less than the whole, depending
on the model, and they are not shares of anything. Uncertainty in a chain of multiplications does
not divide between the inputs — which is the same fact problem 19.2 measures, arriving from the
other direction and harder to argue with.

### After you measure it

The point of all this is to change something. Which means the honest end of a sensitivity analysis
is a plan:

- **measure it** — turn an assumption into a measured constant with a standard error, which is
  [ch03](#where-the-numbers-come-from)'s discipline and problem 3.2's arithmetic for how much
  measuring is enough;
- **decide it** — turn an uncertainty into a policy, which costs flexibility rather than money;
- **design around it** — make the answer less sensitive to it, which is usually the most expensive
  and the most durable.

And then re-run the model, because the tornado will have a different input at the top. That is
what progress looks like here: not a narrower interval on the same chart, but a different chart.

## What this cannot tell you

**How much the interval would narrow if you measured it *in practice*.** The table above is the
bound, computed by pretending the measurement is perfect. A real one leaves a standard error
behind, and how large that error would be is not knowable before doing the work — so the honest
figure is the ceiling, and the shortfall against it is somebody's judgement about how good a
measurement they can take.

**Anything about interactions.** One at a time, by construction. Problem 19.2 measures the gap and
the gap is not small in a multiplicative model. An input whose effect appears only in combination
with another gets a short bar and can still be the thing that sinks you.

**Anything about correlated inputs.** As above: a bar is one input and a correlation is two.

**Whether the input can be measured at all.** In the observability model the joint-widest bar is
a growth rate, which is a claim about the future and belongs to no target
([ch04](#peak-mean-and-growth)). The chart will keep pointing at it, and the honest response is to
decide it rather than measure it.

**Whether the model has the right inputs.** An input that is not there has no bar, and a tornado
of a model missing a cost line is a confident ranking of the wrong list.
[ch20](#the-missing-node).

## Problems

Two, in `tests/which_input_is_the_answer/`.

**19.1 — Build the chart.**
Reproduce the tornado the build publishes. Swing from each input's distribution rather than from
its slider, so that every bar answers the same question.

```bash
python3 -m pytest tests/which_input_is_the_answer/test_problem_1_tornado.py
```

**19.2 — What one-at-a-time misses.**
Move two inputs separately, then together, and measure the difference. Do it for a pair that meets
in a product and a pair that meets in a sum, and predict which will show a gap.

```bash
python3 -m pytest tests/which_input_is_the_answer/test_problem_2_interaction.py
```

## Where to go next

[ch20](#the-missing-node) is the input that has no bar because it is not in the model, and the one
error nothing in this book can rank.
