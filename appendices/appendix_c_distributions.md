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
| **Purpose** | One section per shape: what it is for, what it asserts about the world, how it misleads, and when to use it |
| **Source** | `sizing/mc.py`, `bench/results/correlation-effect.json` |
:::

The toolkit samples inputs from four shapes: `uniform`, `triangular`, `lognormal` and `normal`,
declared in `sizing/mc.py` under `SHAPES`. Each shape gets its own section below, with four parts:
what it is for, what it asserts about the world, how it will mislead you, and when to use it. A
section under *Choosing* sets all four side by side, then gives five questions, in order, to pick
one for an input. A shape is a claim about what can happen, and each claim of this kind is wrong in
some direction — *How it lies* names that direction for each shape.

```{image} ../chapters/_figures/appendix-c-distributions-shapes.svg
:alt: The four shapes, drawn from the percentile functions the sampler uses
:width: 100%
```

The figure is drawn from the four percentile functions in `sizing/mc.py` — the same functions the
toolkit samples from, not drawings of them. Each is evaluated at evenly spaced percentiles and
plotted as a histogram. The build redraws the figure when one of those functions changes. The four
are set up to cover about the same range of values, centred in about the same place, so the
picture compares their shapes, not their widths. The question each section below answers is which
shape is the right claim about what can happen.

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

**How it lies.** It draws values near the two bounds as often as values in the middle, and for a
quantity with a typical value, values near the bounds are rare in the real world. Used as the
default for such a quantity, it widens the interval with futures nobody believes in. That looks
cautious and is not: every output interval is widened by the same wrong assumption. A tornado
swings each input across the middle of its own shape. A uniform's middle covers more of its range
than a triangular's with the same bounds, so a uniform input gets a longer bar than the evidence
gives it, and the ordering of the tornado can change.

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

**What it asserts.** That the bounds are hard: no value below the least or above the most can
occur. Values are most likely at the one you would bet on, and likelihood falls in straight lines
down to none at each bound. The straight lines are a convenience of the shape, not a claim you
made; the hard bounds are the claim that misleads.

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

**What it is for.** Prices, growth rates, and anything that compounds. You give it two values: a
low one and a high one, `p10` and `p90` in the model file. One future in ten falls below the low
value, and one in ten above the high one — so a value outside the two turns up in one future in
five. The two values are not bounds you would be astonished to see crossed. If the two values you
have in mind are ones you would expect to be crossed less often than that, the toolkit still reads
them as one in ten each side, and the input comes out wider than you meant. Give the values that
one future in ten would pass. The shape is described by these two values rather than by the two numbers its
formula uses internally, because a person can state these two about a price.

**What it asserts.** That the quantity cannot be negative, and that its uncertainty is
multiplicative — that "half as much" and "twice as much" are equally plausible departures. For a
price, both are usually right.

**How it lies.** It has no upper bound, and the upper tail is longer than it looks. A model that
multiplies several of these together produces an output whose 95th percentile is far above
anything the inputs suggested one at a time. That output is roughly lognormal, whether or not
anybody chose the shape: roughly, because the models also add costs and mix in triangular inputs.
That is why sizing answers come out lopsided, with a long high side, and why the median of a
sizing model is usually a better summary than its mean.

**Use it for anything with a price on it**, and read the median rather than the mean.

## Normal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def normal_ppf_scaled
:end-before: #: The distributions a model file may declare
```

**What it is for.** One thing in this book: the measurement error of a `measured` constant. A
number was measured, the measurement has a standard error, and the error is as likely to be high
as low. You do not declare this shape yourself. A measurement goes in a `measured` node, which
names a stamped result in `bench/results/` ([ch03](#where-the-numbers-come-from)). The result
supplies the value, its standard error and the implementation it was measured on, and the toolkit
draws the node as a normal: centred on the value, spread by the standard error. `normal` is also
one of the four shapes an input may declare, and the build does not refuse a measurement written
that way. Do not write it that way. As an input, the number loses the implementation it was
measured on. The build no longer checks it against a stamped result, so a stale number passes. The
model loses what makes it a conditional one, so it no longer has to declare the ceiling the build
demands of a model with a measured constant.

**What it asserts.** That error is symmetric: as likely above the value as below by the same
amount, and that values far from the centre are rare, and get rarer quickly the further out you
go.

**How it lies.** It goes negative. A spread that looks modest beside the value is still wide
enough to give a few negative draws in a full run, and a negative price or a negative host count
then flows through every formula downstream. More importantly, symmetry is the wrong claim about
almost everything else in a sizing model: growth, prices and throughput are all multiplicative,
and a normal says they are additive.

**Use it for measurement error.** It is the wrong default for everything else on this page.

## Choosing

The table below shows the four shapes side by side, one row each:

| Shape | What you give it | What it claims | How it lies | Use it for |
|---|---|---|---|---|
| Uniform | two bounds | every value between them is as likely as any other, and nothing outside can happen | it draws values near the bounds as often as values in the middle, and real values are rarely like that | an input whose bounds are the whole claim |
| Triangular | the least, the most, and the one you would bet on | hard bounds, with likelihood falling in straight lines away from your bet | nothing outside what has already been seen can occur | a human estimate |
| Lognormal | a low value and a high value, with one future in ten below the low one and one in ten above the high one | it cannot be negative, and half as much is as plausible as twice as much | an upper tail longer than it looks, with no bound at all | prices, growth, anything that compounds |
| Normal | nothing directly — the toolkit reads the value and its standard error from a stamped measurement | symmetry, and values far from the centre are rare | it goes negative, and symmetry is the wrong claim about anything that compounds | measurement error, through a `measured` node, and nothing else |

Then the questions, in order:

1. **Does it compound, or does it have a price on it?** Lognormal.
2. **Is it a measurement with a standard error?** A `measured` node that names the stamped
   result. The toolkit samples it as a normal. Do not declare `normal:` on an input for it.
3. **Is it an engineer's least / likely / most?** Triangular.
4. **Are the bounds the only claim?** Uniform.
5. **None of these?** Then the input is the problem, not the shape. Either go and measure it,
   which makes it question 2's case, or treat it as a decision: an input you set to one value
   rather than sample (`decided: you` in the model file). Compare the values you are choosing
   between as scenarios of the same model ([ch21](#a-tco-for-finance)).

One rule sits under all of them: **the shape is part of the model, so it belongs in the model
file with a source attached**. In both of the book's models, every sampled input says in its
`source` which shape it has and why — that a price cannot go negative, that a count has a hard
maximum, that a fit this weak should not be given an upper bound by a shape. Here is one such
input: a price, so the first question would make it lognormal, and its source says why it is
triangular instead.

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: network_price_per_host:
:end-before: network_capex:
```

The source sentence is what a reviewer argues with; without it the shape is an assertion with a
picture.

`scripts/verify-models.py` refuses a sampled input whose source names no shape at all. The check
is mechanical: it looks for any of the four shape names anywhere in the source, so it passes a
source that names a different shape from the one declared, and it cannot tell a reason from a
formality. What it can do is make the omission impossible, which is the same bargain as the rule
that a `fact` must cite something.

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

The `query_utilisation` row barely moves: the observability model declares three pairs of
correlated inputs, and two of those pairs each have only one input that feeds `query_utilisation`,
not both. A correlation between two inputs that do not both feed an output changes almost nothing
in that output. The change that does appear comes from the draws being reordered, not from a
correlation reaching it: the toolkit reorders every sampled input's draws once any pair is
declared. The other two small rows, `tco` and `hosts_recommended`, each have one
declared pair with both inputs upstream, which is why they move more
([ch14](#correlation-and-convergence)).

## What is not here, and why

**Shapes that leave room for rare, extreme values.** None of the four here gives rare, extreme
values enough room to model a real outage, a supplier failing, or a regulation arriving. Those are
structural events. A shape that tries to absorb them produces an interval so wide it cannot
distinguish two designs, and distinguishing designs is what the model is for. They belong in *What
this cannot tell you*, not in a parameter ([ch20](#the-missing-node)).

**Mixtures.** A mixture — two regimes with a probability of each — would be easy to add, and is
deliberately left out. When a quantity has two regimes, the honest model has a node for which
regime it is in and a scenario for each. A number that clusters around two different values is
usually two decisions wearing one name.

**Empirical resampling.** Drawing from observed history rather than from a shape. It is a good
technique that needs history, and most sizing exercises have none. Where this book has data it
measures a constant and states its uncertainty; where it does not, it says so.

**Fitted distributions.** Deliberate, and the reason is in
[Appendix B](#appendix-b-monte-carlo-module): a function that reads your data and picks a shape
produces a model whose central assumption nobody ever wrote down.

## Adding one

To add a shape a model can use, you need four things:

- **A percentile function** in `sizing/mc.py`, beside the four, that takes percentiles and returns
  the values at them.
- **An entry in `SHAPES`** in `sizing/mc.py`, under the name a model file will declare the shape
  by.
- **A test** in `tests/test_mc.py` that the percentiles the function returns are the ones it was
  asked for.
- **The same function and entry** in `sizing/viewer/sample.js` under `SHAPES`, because the
  published page samples the model in your browser with its own copy of the sampler.

`tests/test_sample.py` checks the browser copy against the Python one for every shape a model
declares, and fails if `sample.js` lacks one. Nothing else needs registering:
`scripts/verify-models.py` reads the shape names from `SHAPES`, so an input that uses the new shape
must name it in its source like any other. Problem 13.1 ([ch13](#monte-carlo)) asks for the
percentile function of a shape not on this page, graded against that shape's own definition; it
does not add the shape to `SHAPES` or to the browser.
