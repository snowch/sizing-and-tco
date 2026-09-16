---
title: "Units, and the conversions that bite"
short_title: "Appendix D · Units"
---

(appendix-d-units)=
# Appendix D · Units, and the conversions that bite

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | TB against TiB, bits against bytes, month lengths, and why the build converts |
| **Source** | `sizing/units.py`, `sizing/evaluate.py` |
:::

```{literalinclude} ../sizing/units.py
:language: python
:start-at: A sizing model is a chain of multiplications
:end-before: ## Counting units are units
```

That is the reason this book has a build step at all.

## Counting units are units

```{literalinclude} ../sizing/units.py
:language: python
:start-at: ## Counting units are units
:end-before: ## Why Pint is not in the evaluator
```

```{literalinclude} ../sizing/units.py
:language: python
:start-at: COUNTING_UNITS: tuple[str, ...] = (
:end-before: def registry()
```

Without this, spans-per-request and bytes-per-span are both plain numbers, and multiplying the
wrong pair produces a plausible answer with no complaint from anything. With it, only one product
of those two is well formed.

The cost is the interesting part. Converting between two counting units *requires a node that
names the conversion* — how many spans a request emits, how many samples a series produces per
scrape. That node is exactly the measured constant of [ch03](#where-the-numbers-come-from): an
empirical number belonging to one implementation at one version, with provenance attached. The
unit system pushes you towards declaring the thing the book says you must declare, which is a
better mechanism than a rule in a style guide.

## Dimensions are not enough

The check that catches the most is not the one that catches dimensional nonsense. It is the one
that catches two units with the *same* dimensions and different magnitudes:

```{include} ../chapters/_generated/appendix-d-units-conversions.md
```

Every row is a formula whose result has the right dimensions and the wrong size. Dollars per
terabyte per year and dollars per terabyte per month are dimensionally identical. A check that
compared dimensions alone would pass a unit cost twelve times too large, and it would pass it in
the figure most likely to be quoted in a meeting.

So the build records the factor and applies it. The declared unit wins — a node says what it means
to produce, and the build makes the arithmetic agree or refuses to continue.

## The conversions that actually bite

**Decimal against binary.** A drive is sold in decimal terabytes. An operating system reports
tebibytes. The gap is nearly a tenth of the capacity, it is in the direction that makes a cluster
smaller than the spreadsheet said, and it compounds with the replication factor. The storage
model's drive capacity input says *decimal* in its provenance for this reason.

**Bits against bytes.** Network is quoted in bits per second and storage in bytes per second, and
the factor of eight between them sits at exactly the boundary between two teams. A model that
multiplies a link rate by a duration and compares the result to a volume has to get this right
once; a model that does not declare units has to get it right every time anybody edits it.

**Months.** There is no such unit as a month in this registry, because there is no such quantity.
A model that prices per month and sizes per year has to say which month it means, and dividing a
year by twelve is a decision — a defensible one, and different from using the actual lengths of
the months in the period. The book divides the year, says so, and the conversion appears in the
table above.

**Years.** The same problem, smaller: a year is not exactly three hundred and sixty-five days. The
storage model's `hours per year` input carries the quarter-day and says in its provenance what
that is worth over the horizon — less than the model's other errors, and free to get right.

**Exponents are pure numbers.** A duration cannot be an exponent. Compounding growth over a
horizon needs the horizon divided by one period first, which is why both reference models carry a
node that is just `one year` with a provenance of `fact`. It looks like ceremony until the first
time the check catches a growth factor raised to the power of five *seconds*.

## Where Pint runs, and where it does not

```{literalinclude} ../sizing/units.py
:language: python
:start-at: ## Why Pint is not in the evaluator
:end-before: """
```

Units are checked once, at build time, over the model's formulas with unit-bearing quantities.
After that the units are stripped and the sampler works in plain floating point. A unit-bearing
array across a hundred nodes and a hundred thousand samples is slow, and `sizing/mc.py` is a
chapter of this book that the reader is asked to read — a units library in the middle of it would
be answering a question nobody asked.

**Units are a gate, not a tax.**

## One more thing the check needs

Evaluating a formula in units alone is not always possible: a formula containing `1 - headroom`
has to be evaluated at a *magnitude* as well as a unit, and doing it at one produces a division by
zero in a model that is perfectly sound. So the checker uses each node's real point value where it
has one:

```{literalinclude} ../sizing/evaluate.py
:language: python
:start-at: def plausible_magnitudes
:end-before: def check_units
```

Found by the check itself, on a model that was correct.

## Running it

```bash
python3 scripts/verify-models.py       # every formula, in units, on every model
python3 -m pytest tests/test_models.py # the registry, the conversions, and both models
```
