---
title: "Distributions, and when each is honest"
short_title: "Appendix C · Distributions"
---

(appendix-c-distributions)=
# Appendix C · Distributions, and when each is honest

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | One page each: what it is for, what it assumes, and how it lies |
| **Source** | `sizing/mc.py`, `bench/results/correlation-effect.json` |
:::

Four shapes. Choosing between them is the most consequential editorial act in building a model,
and most models settle it by taking whichever shape the tool offered first.

Each section below says the same three things: what the shape is for, what it *asserts* about the
world, and the specific way it will mislead you. Read *how it lies* first. A distribution is a
claim, and every claim of this kind is wrong in a direction.

```{image} ../chapters/_figures/appendix-c-distributions-shapes.svg
:alt: The four shapes, drawn from the percentile functions the sampler actually uses
:width: 100%
```

Those are not illustrations. They are the functions in `sizing/mc.py`, sampled at a thousand
percentiles and plotted; change one and this picture changes. Their parameters are chosen to put
roughly the same mass in the same place, because the interesting question is never "which is
wider" but "which is the right claim about what can happen".

## Uniform

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def uniform_ppf
:end-before: def triangular_ppf
```

**What it is for.** Bounds, and nothing else claimed. A contract that caps a price between two
figures. A retention window somebody will pick from a range at a meeting you are not in. A
parameter with a documented minimum and maximum and no reason to prefer the middle.

**What it asserts.** That every value between the bounds is exactly as likely as every other, and
that nothing outside them can happen. Equal likelihood is a strong claim that reads as a weak one:
it looks like saying "I do not know", and it is saying "the extremes are as likely as the
middle".

**How it lies.** By putting mass at the ends where almost nothing real has any. Used as the
default for a quantity that has a typical value, it widens the interval with futures nobody
believes in. That looks cautious and is not: every output interval is inflated by the same wrong
assumption, and the ordering of a tornado can change.

**Use it when the bounds are the claim.** Not when they are the only two numbers you happen to
have.

## Triangular

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def triangular_ppf
:end-before: def lognormal_ppf
```

**What it is for.** An expert's guess, in the shape the answer arrives in: the least it could be,
the most it could be, and the one they would bet on. Most sizing inputs are this and nothing more.

**What it asserts.** That the bounds are hard, and that the density falls linearly away from the
mode. The straight sides are arbitrary and mostly harmless. The hard bounds are not.

**How it lies.** The bounds came from somebody's memory, and the shape says nothing outside them
can occur. So the model cannot produce the case where the peak hour is twice anything anyone has
seen. Every triangular input is a small promise that the world will stay inside the range of what
has already happened, and the futures that hurt are exactly the ones that do not.

**Use it for a human estimate**, and remember that it cannot surprise you.

## Lognormal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def lognormal_ppf
:end-before: def normal_ppf_scaled
```

**What it is for.** Prices, growth rates, and anything that compounds. Parameterised here by two
percentiles rather than by the parameters of the underlying normal, because the percentiles are
something a person can state.

**What it asserts.** That the quantity cannot be negative, and that its uncertainty is
multiplicative — that "half as much" and "twice as much" are equally plausible departures. For a
price, both are usually right.

**How it lies.** It has no upper bound, and the upper tail is longer than it looks. A model with
several of these multiplied together produces an output whose 95th percentile is far above
anything the inputs individually suggested, and that output is *also* lognormal whether or not
anybody chose it. That is why so many sizing answers come out skewed, and why the mean of a sizing
model is usually a worse summary than its median.

**Use it for anything with a price on it**, and read the median rather than the mean.

## Normal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def normal_ppf_scaled
:end-before: SHAPES: dict[str, Callable
```

**What it is for.** One thing in this book: the measurement error of a `measured` constant. A
number was measured, the measurement has a standard error, and the error is as likely to be high
as low.

**What it asserts.** Symmetry, and thin tails.

**How it lies.** It goes negative. Not often, and that is the problem. A price with a small
enough spread will sample a negative value once in a large number of draws, and the run that
finds it will be the one somebody is watching. More importantly, symmetry is the wrong claim about
almost everything else in a sizing model: growth, prices and throughput are all multiplicative,
and a normal says they are additive.

**Use it for measurement error.** It is the wrong default for everything else on this page.

## Choosing

The four, side by side:

| Shape | What you give it | What it claims | How it lies | Use it for |
|---|---|---|---|---|
| Uniform | two bounds | every value between them is as likely as any other, and nothing outside can happen | mass at the ends, where almost nothing real has any | an input whose bounds are the whole claim |
| Triangular | the least, the most, and the one you would bet on | hard bounds, with likelihood falling in straight lines away from your bet | nothing outside what has already been seen can occur | a human estimate |
| Lognormal | a low and a high value you would be surprised outside | it cannot be negative, and half as much is as plausible as twice as much | an upper tail longer than it looks, with no bound at all | prices, growth, anything that compounds |
| Normal | a value and its standard error | symmetry, and thin tails | it goes negative, and symmetry is the wrong claim about anything that compounds | measurement error, and nothing else |

Then the questions, in order:

1. **Does it compound, or does it have a price on it?** Lognormal.
2. **Is it a measurement with a standard error?** Normal.
3. **Is it an engineer's least / likely / most?** Triangular.
4. **Are the bounds the only claim?** Uniform.
5. **None of these?** Then the input is the problem, not the shape. Go and measure it, or
   declare it a control knob and run scenarios instead of sampling it
   ([ch12](#the-sizing-model)).

One rule sits under all of them: **the shape is part of the model, so it belongs in the model
file with a source attached**. In all three of this book's models, every input that carries a
distribution says in its `source` which shape it has and why — that a price cannot go negative,
that a count has a hard maximum, that a fit this weak should not be given an upper bound by a
shape. That sentence is what a reviewer argues with; without it the distribution is an assertion
with a nice picture.

`scripts/verify-models.py` refuses an input that is sampled and does not name its shape. The check
is mechanical: it looks for the word, so it cannot tell a reason from a formality. What it can
do is make the omission impossible, which is the same bargain as the rule that a `fact` must cite
something. It was added after an audit of this book's own models found most of them silent.

## Inputs that move together

A shape describes one input on its own. Most models have at least two inputs that move together,
and pretending otherwise is not a neutral simplification:

```{include} ../chapters/_generated/appendix-c-distributions-correlation.md
```

Every row is positive: assuming independence made every interval narrower. Narrower in the
direction that gets a plan approved, which is the direction to be suspicious of.

Independent inputs partly cancel, one high while another is low, and that cancellation is what
makes the interval narrow. Correlated inputs push the same way at the same time, so the
cancellation does not happen. Keep that mechanism in mind: it is why leaving each of these
correlations undeclared made the interval narrower. A model that declares no
correlations is claiming that all of its inputs are strangers, and in a sizing model fed by one
growth rate they are usually relatives.

One row barely moves, and it is there deliberately: a correlation between two inputs that do not
both feed the output in question changes almost nothing. Seeing a correlation that does not matter
beside one that does is the fastest way to stop treating the subject as magic
([ch14](#correlation-and-convergence)).

## What is not here, and why

**Fat-tailed shapes.** Nothing here has a tail heavy enough to model a real outage, a supplier
failing, or a regulation arriving. Those are structural events, and a distribution that tries to
absorb them produces an interval so wide it cannot distinguish two designs, which is the only
thing the model was for. They belong in *What this cannot tell you*, not in a parameter
([ch20](#the-missing-node)).

**Mixtures.** A mixture, two regimes with a probability of each, would be easy to add, and is
deliberately absent. When a quantity has two regimes, the honest model has a node for which
regime it is in and a scenario for each: a number that is bimodal is usually two decisions
wearing one name.

**Empirical resampling.** Drawing from observed history rather than from a shape. It is a good
technique that needs history, and most sizing exercises have none. Where this book has data it
measures a constant and states its uncertainty; where it does not, it says so.

**Fitted distributions.** Deliberate, and the reason is in
[Appendix B](#appendix-b-monte-carlo-module): a function that reads your data and picks a shape
produces a model whose central assumption nobody ever wrote down.

## Adding one

Three lines and a test. A percentile function, an entry in `SHAPES`, and a case in
`tests/test_mc.py` asserting that the percentiles it produces are the ones it was asked for.
Problem 13.1 is that exercise, for a shape that is not on this page.
