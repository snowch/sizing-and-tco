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
| **Purpose** | `sizing/mc.py` and `sizing/normal.py`, in the order the files are written and the order a run calls them |
| **Source** | `sizing/mc.py`, `sizing/normal.py` |
:::

This page quotes the files in the order they are written: `sizing/mc.py` from its opening
docstring onwards (omitting only the title line and imports), then `sizing/normal.py` from its
first constant to its end. The point is to show there is nothing else in either.

A run calls the pieces in a different order:

1. `rng`, once, seeded from the scenario.
2. For each uncertain input the scenario has not pinned: `sample` with its declared distribution,
   or for a measured constant, `normal_ppf_scaled` with its measured value and standard error.
3. If the model declares correlations between inputs that were drawn: `correlation_matrix`, then
   `correlate`, once, over all the drawn inputs together.
4. The model's formulas, applied to whole columns of draws at once. (This step is not in
   `sizing/mc.py`.)
5. `summarise` and `histogram`, for every node whose value varies.

The function that makes these calls is `evaluate` in `sizing/evaluate.py`.

```{include} ../sizing/mc.py
:start-after: Monte Carlo, from first principles.
:end-before: """
```

Each uncertain input in the model file declares which shape it follows, written alongside its
provenance kind and source ([ch03](#where-the-numbers-come-from)). A reviewer can then see the
choice and argue with it, where a fitting function would leave the decision undeclared.

## Two constants

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: #: The percentile the
:end-before: def rng(seed: int)
```

## The seed

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rng(seed: int)
:end-before: # -- percentile functions
```

The enforcement happens outside this function: `bench/stamp.py` refuses to stamp any model result
that does not record its seed. When an experiment uses many seeds, the result records the base
seed and the rule that derives them. The convergence table under *Reading the answer* is an
example: it runs the model many times at each sample count, each time with its own seed, and its
result records the base seed and the rule.

## The four percentile functions

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: # -- percentile functions
:end-before: def uniform_ppf
```

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

### Lognormal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def lognormal_ppf
:end-before: def normal_ppf_scaled
```

### Normal

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def normal_ppf_scaled
:end-before: #: The distributions a model file may declare
```

## The registry

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: #: The distributions a model file may declare
:end-before: def sample(
```

`sample` looks up shapes in `SHAPES`, but it is not the only function that does. The module in
`sizing/evaluate.py` uses the same percentile functions for the point estimate of each input (its
median value) and for each input's swing in the tornado, the chart that ranks inputs by how far
each moves the output. So sampling, point estimation, and the tornado all reach shapes through this
single table. [Appendix C](#appendix-c-distributions) covers when each shape suits an input and how
each misleads.

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
:start-at: # -- inputs that move together
:end-before: def rank_to_score_correlation
```

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rank_to_score_correlation
:end-before: def correlate(
```

Inducing a correlation on *ranks* and then reading it back on *values* does not return the number
you asked for. It comes back attenuated, by an amount that depends only on the coefficient: ask
for a strong correlation, measure the result, and it is visibly weaker. This is the correction
that is easy to leave out and hard to find afterwards, and the fix is one line of trigonometry
before the sort rather than an apology in the documentation after it.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def correlate(
:end-before: # -- reading the answer
```

The method of Iman and Conover @imanconover1982 works in three steps:

1. Build a reference set with one column of normal scores per input, each shuffled independently
   using the run's generator, so the stamped seed reproduces it.
2. Apply the wanted score correlations using two Cholesky factors—a standard way to give a set of
   columns a chosen correlation—calculated from both the correlation the shuffled set has and the
   correlation wanted.
3. Reorder each input's draws to match its shaped column: largest draw where the largest score is,
   and so on down.

Where a set of declared correlations cannot all hold together, step 2 fails with an error
directing you to look for a triangle of strong correlations that conflict. The model does not run
with a revised set.

## Reading the answer

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: # -- reading the answer
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

The `half_width` measures one run's answer width. The run-to-run spread measures how far the answer
lands from one run to the next when only the seed changes. `samples_needed` takes the run-to-run
spread and returns how many draws make it no more than a target; given a `half_width`, it returns a
count that means nothing, because the half-width does not fall as draws grow. The law is that ten
times smaller spread costs a hundred times the draws. The table below measures this on the web
service model's five-year total: the model run many times at each sample count, each with its own
seed, and a column heading says how many runs.

```{include} ../chapters/_generated/appendix-b-monte-carlo-module-convergence.md
```

The interval **settles**; the run-to-run spread **falls**. The half-width barely moves from the row
for a thousand samples down. It comes from how uncertain the model's inputs are, and more draws
converge on it rather than shrinking it. The run-to-run spread keeps falling from row to row.

The last row shows how much it fell per tenfold step from a thousand samples up, and sets this
against the square root of ten, which is what the law predicts. The single-row falls wander above
and below that line. Each spread in the table is estimated from a limited number of runs, so it
carries its own noise; read the last row, not any single row, to see the trend. The figure measured
is the 95th percentile, a tail number that follows the law but more slowly than the mean does.
`tests/test_mc.py` holds the mean to the law closely and the 95th percentile only loosely for that
reason. So read the last row as a comparison with the law, not as a test it failed.

```{image} ../chapters/_figures/correlation-and-convergence-curve.svg
:alt: The interval half-width and the run-to-run spread, against sample count
:width: 100%
```

## Shipping a distribution

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: #: Above this ratio
```

Every node whose value varies ships its distribution as a count per bin and the bin edges, computed
by calling `histogram` with its default `bins`. The model viewer that the chapters embed uses these
to draw whichever node you click, whether input, intermediate step or output, in its details panel.

The bins are equal in width unless the quantity spans orders of magnitude, in which case they are
equal in *ratio* and `spacing` says which. To see a ratio-spaced histogram, open the model in
[ch06](#queueing-and-the-knee) and click *requests in the system*, which is a queue near saturation.
The viewer labels such histograms to show the bars are equal in ratio. The book's static figures
read `spacing` too, and draw a logarithmic axis when it says so.

## The inverse normal

Everything in `sizing/mc.py` that needs the normal distribution's percentile function calls
`normal_ppf` from `sizing/normal.py`: the lognormal and normal shapes, the normal scores in
`correlate`, and the constant `Z90`. There is no closed form for it. `sizing/normal.py` implements
Acklam's rational approximation @acklam2003inverse: two rational functions, one for the middle and
one for the tails, switching at `_TAIL`; the coefficients are Acklam's and the code is this
repository's. Python's standard library includes `statistics.NormalDist().inv_cdf`, which is
accurate but takes one number at a time, whereas the sampler works on arrays, so the approximation
is used instead. `tests/test_mc.py` uses the standard library as its reference, checking they agree
across the range, both tails included:

```{literalinclude} ../sizing/normal.py
:language: python
:start-at: #: Where the central rational approximation stops
```

## Running it

```bash
python3 -m pytest tests/test_mc.py           # the sampler, against properties it must have
python3 -m bench.run_uncertainty             # the correlation and convergence experiments
```
