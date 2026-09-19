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

Multiplying two quantities that should never have met is the reason this book has a build step
at all.

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

The cost of that is a node. Converting between two counting units *requires one that names the
conversion* — how many spans a request emits, how many samples a series produces per scrape. That
node is exactly the measured constant of [ch03](#where-the-numbers-come-from): an empirical number
belonging to one implementation at one version, with provenance attached. The unit system makes
you declare what the book says you must declare, which a rule in a style guide cannot do.

## Dimensions are not enough

Most of what the check catches is not dimensional nonsense. It is two units with the *same*
dimensions and different magnitudes:

```{include} ../chapters/_generated/appendix-d-units-conversions.md
```

Every row is a formula whose result has the right dimensions and the wrong size. Dollars per
terabyte per year and dollars per terabyte per month are dimensionally identical. A check that
compared dimensions alone would pass a unit cost twelve times too large, and it would pass it in
the figure most likely to be quoted in a meeting.

So the build records the factor and applies it. The declared unit wins — a node says what it means
to produce, and the build makes the arithmetic agree or refuses to continue.

## Five places a unit goes wrong

**Decimal against binary.** A drive is sold in decimal terabytes. An operating system reports
tebibytes. The gap is nearly a tenth of the capacity, it is in the direction that makes a fleet's
disks smaller than the spreadsheet said, and it compounds with the replication factor. The web
service model's disk-per-host input says *decimal* in its provenance for this reason.

**Bits against bytes.** Network is quoted in bits per second and storage in bytes per second, and
the factor of eight between them sits at exactly the boundary between two teams. A model that
multiplies a link rate by a duration and compares the result to a volume has to get this right
once; a model that does not declare units has to get it right every time anybody edits it.

**Months.** The registry has one, and it is a twelfth of a year — which is no month that has ever
appeared on a calendar. That is the right convention for a price per terabyte-month, where nobody
means February, and the wrong one for anything that has to reconcile against a billing period.
The distinction is invisible until somebody in finance does the reconciling, which is why the
conversion appears in the table above rather than inside somebody's head.

**Years.** The same problem, smaller: a year is not exactly three hundred and sixty-five days. The
web service model's `hours per year` input carries the quarter-day and says in its provenance what
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
array across a hundred nodes and a hundred thousand samples is slow. And `sizing/mc.py` is a
chapter of this book, written to be read: a units library in the middle of it would answer a
question nobody asked.

**Units are a gate, not a tax.**

## Why the check needs a magnitude

Evaluating a formula in units alone is not always possible. A formula containing `1 - headroom`
has to be evaluated at a *magnitude* as well as a unit, and a magnitude of one produces a division
by zero in a model that is perfectly sound. So the checker uses each node's real point value where
it has one:

```{literalinclude} ../sizing/evaluate.py
:language: python
:start-at: def plausible_magnitudes
:end-before: def check_units
```

The check found that case itself, on a model that was correct.

## Running it

```bash
python3 scripts/verify-models.py       # every formula, in units, on every model
python3 -m pytest tests/test_models.py # the registry, the conversions, and both models
```
