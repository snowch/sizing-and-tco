---
title: "The Monte Carlo module, read end to end"
short_title: "Appendix B · sizing/mc.py"
---

(appendix-b-monte-carlo-module)=
# Appendix B · The Monte Carlo module, read end to end

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | `sizing/mc.py`, quoted in order, with the reasoning for each piece |
| **Source** | `sizing/mc.py`, `sizing/normal.py` |
:::

[ch13](#monte-carlo) and [ch14](#correlation-and-convergence) quote pieces of this module where
they need them. This page is the whole of it, in the order it is written, for a reader who wants
to see that there is nothing else in it.

There is no simulation framework underneath this and no statistics package beside it. numpy for
arrays, one rational approximation for the inverse normal, and nothing else. That is not
minimalism for its own sake: a reader who cannot see the sampler cannot check the interval, and
an interval nobody can check is a decoration.

## The one idea

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: ## One idea
:end-before: ## What is deliberately absent
```

Everything below is arrangement around that sentence. Each distribution needs exactly one
function — the value at a given percentile — and sampling it is drawing percentiles at random and
looking the values up.

## The seed

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rng(seed: int)
:end-before: # -- percentile functions
```

Every stamped result computed from a model records the seed that produced it, and
`bench/stamp.py` refuses one that does not. An unseeded run is a measurement nobody can repeat,
which is the thing this repository refuses everywhere else and would be strange to permit here.
Where an experiment uses many seeds — the convergence table on this page uses one per replicate —
what it records is the seed they are all derived from, and the rule that derives them.

## The four percentile functions

### Uniform

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def uniform_ppf
:end-before: def triangular_ppf
```

### Triangular

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def triangular_ppf
:end-before: def lognormal_ppf
```

Two branches meeting at the mode. Below it the area under the triangle grows as the square of the
distance from the minimum, so inverting it is a square root; above it, the same thing from the
other end. That derivation is the whole of adding a distribution to this book, and problem 13.1
asks for it again for a shape that is not here.

### Lognormal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def lognormal_ppf
:end-before: def normal_ppf_scaled
```

Parameterised by two percentiles, not by the mean and standard deviation of the logarithm. Nobody
has an intuition for the second. Everybody has one for the first: *I would be surprised if it were
under this, or over that* is a sentence a person can actually say about a price.

### Normal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def normal_ppf_scaled
:end-before: SHAPES: dict[str, Callable
```

One job in this book: the measurement error of a `measured` node. It is the wrong default for a
price, because it will happily go negative.

### The registry

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: SHAPES: dict[str, Callable[..., np.ndarray]] = {
:end-before: def sample(
```

No registration machinery and no plugin system. Four shapes cover every input in both reference
models, and a fifth should have to argue for itself
([Appendix C](#appendix-c-distributions)).

## Drawing

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def sample(spec: dict
:end-before: def one_shape
```

Two lines, and they are the two lines of the entire subject.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def one_shape
:end-before: # -- inputs that move together
```

## Inputs that move together

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def correlation_matrix
:end-before: def rank_to_score_correlation
```

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rank_to_score_correlation
:end-before: def correlate(
```

This correction is the part that is easy to leave out and then hard to find. Inducing a
correlation on *ranks* and then reading it back on *values* does not return the number you asked
for — it comes back attenuated, by an amount that depends only on the coefficient. Ask for a
strong correlation, measure the result, and it is visibly weaker. The fix is one line of
trigonometry applied before the sort rather than an apology in the documentation afterwards.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def correlate(
:end-before: # -- reading the answer
```

Iman–Conover @imanconover1982, which is short enough to read: build a reference sample with the
correlation you want, rank it, and shuffle each input column into the same rank order. Every
column keeps its own distribution exactly — every value that was drawn is still there — and only
the *pairing* between columns changes. That is why it can be applied to all four shapes without
knowing anything about them.

## Reading the answer

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: PERCENTILES = (5, 25, 50, 75, 95)
:end-before: def interval
```

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def interval(
:end-before: def samples_needed
```

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def samples_needed
:end-before: #: Above this ratio
```

The arithmetic of "enough", both ways round. It is the honest answer to a question people usually
settle with a habit, and it is unforgiving: a factor of ten less wobble costs a hundred times the
samples.

```{include} ../chapters/_generated/appendix-b-monte-carlo-module-convergence.md
```

Two columns, two behaviours, and confusing them is the most common misunderstanding in the
subject. The interval **settles** — it is a property of how uncertain the model's inputs are, and
more samples converge on it rather than shrinking it. The run-to-run spread **falls**, at close to
the square root of ten per decade, because that is a property of how hard you looked.

```{image} ../chapters/_figures/correlation-and-convergence-curve.svg
:alt: The interval half-width and the run-to-run spread, against sample count
:width: 100%
```

## Shipping a distribution

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: #: Above this ratio
```

Counts and edges rather than the draws: a few dozen numbers a node instead of a hundred thousand,
which is what makes it affordable for the interactive page to let a reader click **any** node and
see its distribution, rather than only the outputs. Watching a narrow input turn into a wide
output three steps down the chain is the fastest way to understand a sizing model, and it costs
almost nothing to ship.

The bins are equal in width unless the quantity spans orders of magnitude, in which case they are
equal in *ratio* and the payload says so. A queue near saturation does this: half the draws land
in the first equal-width bin and the picture becomes a spike beside an empty page. The figure
reads that flag and labels its axis accordingly, which is [ch05](#littles-law)'s concurrency
figure.

## What is deliberately absent

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: ## What is deliberately absent
:end-before: """
```

Variance reduction, quasi-random sequences and importance sampling all narrow an interval for the
same number of draws, and all of them make the interval harder to explain to the person who has to
sign for the money. This book's bottleneck was never compute.

Fitting is absent for a different reason. A function that reads your data and tells you which
shape it is produces a model whose central assumption nobody ever wrote down. Choosing a shape is
an editorial act with provenance attached ([ch03](#where-the-numbers-come-from)), and it belongs
in the model file where a reviewer can argue with it.

## The inverse normal

Two of the four shapes need the inverse normal CDF, and there is no closed form. `sizing/normal.py`
is Acklam's rational approximation @acklam2003inverse, implemented here and checked against
Python's own `statistics.NormalDist` across the range:

```{literalinclude} ../sizing/normal.py
:language: python
:start-at: def normal_ppf
```

## Running it

```bash
python3 -m pytest tests/test_mc.py           # the sampler, against properties it must have
python3 -m bench.run_uncertainty             # the correlation and convergence experiments
```
