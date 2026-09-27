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

A sizing model is a chain of multiplications. One way for it to be wrong is to multiply two
quantities that should never have met: series by requests, bytes by seconds, a per-node figure by a
per-core one. A spreadsheet cannot see any of these: a cell holds a number, and the number
carries no unit. Every node in this book's models declares its unit, and the build works out the
unit each formula produces and compares it with what was declared. It accepts a unit that matches, converts one that differs only in size, and refuses one that is a different kind of quantity. This
check is why the book has a build step.

## How units combine and cancel

One rule does all of the work: a unit in the denominator of one quantity cancels the same unit
in the numerator of another, and nothing else cancels. Requests per second times seconds is
requests, because the seconds cancel. Requests per second times a plain number is still requests
per second, because a plain number has nothing to cancel with.

The table applies that rule to the combinations a sizing model is made of. Every result in it
was worked out by the registry the build uses, not typed, so the page cannot show a combination
the toolkit would disagree with.

```{include} ../chapters/_generated/appendix-d-units-algebra.md
```

Two rows matter more than the rest. A rate times a duration is an amount. A rate times a plain
number is still a rate. A formula that treats it as an amount is the mistake
[ch02](#what-a-workload-is) shows the toolkit refusing.

A node declares the unit it means to produce. The build works out the unit its formula produces and
compares the two. It does one of three things:

```{include} ../chapters/_generated/appendix-d-units-verdicts.md
```

The build accepts the formula as written, converts it to the declared unit, or refuses. It accepts
when the formula makes exactly the unit declared. It converts when the formula makes the same kind
of quantity as declared, in a different size — one factor is recorded for the node, and the whole
result is converted by it.

A formula that the unit check can work through is still refused for one of two reasons. First, it
may make a different kind of quantity from the one declared: a rate where the node declares an
amount. No factor turns one into the other, and the refusal names both kinds. Second, two numbers of
the same kind in different units may meet in a sum, a difference, a `min` or a `max`, or one may be
rounded by `ceil` or `floor` before it is converted, so the build would round the wrong number. The
rest of this page names the refusals that come before the formula: units the build does not accept
at all, and quantities used where only a plain number will do.

One factor applied to a whole result works for products and quotients, where factors multiply
through. It cannot work for a sum. Adding a number in terabytes to a number in tebibytes adds them
as if the units matched. Scaling the total afterwards does not repair it. The refusal tells you to
declare both in one unit, or convert one of them in a node of its own.

The first two rows are ch02's example and its mistake. The last two rows are the second kind of
refusal. The converted rows are what the rest of this appendix is about: the same kind of quantity
in a different size, which is the error that looks right.

## Counting units are units

% word-ok: a sample here is one reading a scrape takes, a counting unit, not one of the model's draws
The build's unit registry treats things that are counted as units of their own, not as plain
numbers: requests, spans, samples, series, log lines, queries, hosts, nodes, cores, labels, drives,
failures, and money in each currency the toolkit knows.

```{literalinclude} ../sizing/units.py
:language: python
:start-at: #: The currencies a model may price in
:end-before: def _definitions() -> list[str]:
```

Without these units, spans per request and bytes per span are both plain numbers. Multiply the wrong
pair and you get a plausible answer with no complaint. With them, the formula
`request/second × span/request × byte/span` produces `byte/second`, and no other product of those
three is well formed.

% word-ok: a sample here is one reading a scrape takes, a counting unit, not one of the model's draws
Currencies are on the list for the same reason. Adding dollars to euros is as wrong as adding spans
to requests, and without a unit for each currency nothing in the registry would notice. A model
answers in one currency, the one its `currency:` line names, and the build refuses an output in any
other. A price quoted in another currency is converted by an exchange rate: an input of its own, in
a unit such as `USD/EUR`, with a source.

Each conversion between two counting units costs you one node, whose unit is the conversion itself:
spans per request, samples per series, log lines per request, cores per host. That node is an input
like any other, so it must say where its number came from:

% word-ok: a sample here is one reading a scrape takes, a counting unit, not one of the model's draws
- **spans per request** (observability model): a measured constant, belonging to one instrumented
  application at one version; nobody has measured it here.
- **one sample per series** (observability model): a definition — one scrape takes one sample from
  one series.
- **log lines per request** (observability model): an assumption, from reading the logs.
- **cores per host** (web service model): a vendor's claim, from the spec sheet.

Only the first is a measured constant in the sense [ch03](#where-the-numbers-come-from) describes. A
counting unit does not make a model conditional; a measured constant does
([ch01](#point-estimates)). What the unit system does is make you write the conversion down as a
node with a stated source. A rule in a style guide cannot make you do that.

## Dimensions are not enough

Most of what the check does is not refusing. It is converting: two units of the same kind with
different sizes. A unit's dimensions are the kind of thing it measures (a length of time, or money)
without its size; terabytes and tebibytes have the same dimensions. The table below lists every conversion the build applies in the book's models.

```{include} ../chapters/_generated/appendix-d-units-conversions.md
```

Every row is a formula whose result is the right kind of quantity at the wrong size. Dollars per
terabyte per year and dollars per terabyte per month have identical dimensions. A check that
compared dimensions alone would pass a unit cost twelve times too large — the cost per stored TB per
month that [ch17](#unit-economics) works with, a figure likely to be quoted in a meeting.

The units library the build uses defines a bit as a plain number, so every amount of data would be a
plain number too. A growth factor raised to the power of fifteen terabytes would then pass the unit
check. The build's registry changes that one definition, making an amount of data a kind of quantity
of its own, counted in bits. The unit check refuses a formula that makes a plain number for a node
declared in TB, a ceiling in TB with a plain number for its limit, and terabytes used as an exponent
or inside a logarithm.

## Six places a unit goes wrong

**Decimal against binary.** A drive is sold in decimal terabytes. An operating system reports
tebibytes, which are larger, so the same drive shows fewer of them. The gap is nearly a tenth of the
capacity and runs in the direction that makes a fleet's disks smaller than the spreadsheet said. The
gap is a fixed fraction of whatever it applies to, not a growing fraction. The web service model's
disk-per-host input says *decimal* in its provenance for this reason.

Memory runs the other way. A spec sheet says gigabytes and means gibibytes. The web service model
declares memory per host in `GiB/host`, and its provenance says so; the build converts it to decimal
terabytes per host where memory meets the data. The unit tells the build which of the two you meant.
It cannot tell you which one the vendor meant. The build converts a TiB result into a TB node without complaint.

**Bits against bytes.** Network is quoted in bits per second and storage in bytes per second, and
the factor of eight between them sits at the boundary between two teams. A model that
multiplies a link rate by a duration and compares the result to a volume has to get this right
once; a model that does not declare units has to get it right every time anybody edits it.

**Months.** The registry has one, and it is a twelfth of a year, which is no month that has ever
appeared on a calendar. That is the right convention for a price per terabyte-month, where nobody
means February, and the wrong one for anything that has to reconcile against a billing period.
The distinction is invisible until finance does the reconciling, which is why the conversion
appears in the table above rather than in the modeller's head.

**Years.** A year is not exactly three hundred and sixty-five days. The web service model's
`hours per year` input carries the quarter-day. It changes the energy bill by the same small
fraction every year, because energy cost is hours times power times price, so the fraction does
not grow over a longer horizon. It is smaller than the model's other errors, and free to get right.

**Exponents are pure numbers.** A duration cannot be an exponent. Compounding growth over a horizon
needs the horizon divided by one period first, which is why both reference models carry a node that
is just `one year`. It looks like ceremony until the build refuses a growth factor raised to the
power of five *years*.

**Offset and logarithmic scales are refused.** The build converts a node by multiplying by one
factor. Nought degrees Celsius is not zero temperature, so Celsius converts with an offset as well
as a factor. A decibel is a logarithm of a ratio. Neither converts by one factor, so the build
refuses both as units. A model that needs one works in a unit that does, such as kelvin, or a plain
ratio.

## Where Pint runs, and where it does not

Pint is the units library the build uses. It is used by the unit check and nowhere else in the code
that works a model out. The check runs before any number is computed — on every model on every push,
and again each time the toolkit evaluates a model. It hands back one factor per node, then the units
are stripped and the arithmetic is done on plain numbers, each node's result converted by its
factor. The model viewer on the published pages applies the same factors in the browser, with no
units library at all.

Pint is kept out of the arithmetic for two reasons. First, the toolkit reruns each model many times
to see how far the answer can move, and numbers that carry units are slow to work with at that
scale. Second, the code that reruns the model (`sizing/mc.py`) is written to be read end to end,
and [Appendix B](#appendix-b-monte-carlo-module) reads it. A units library inside it would add code
with nothing to do with what that module is for. The check runs once per evaluation, before the reruns begin, so it stops a wrong model without slowing a right one.

## Why the check needs a magnitude

Pint works out the unit of a formula by doing the arithmetic on numbers that carry units. So the
check has to give every node a number, not only a unit. The obvious number is one for every node,
but that breaks sound formulas. The web service model works out hosts for storage as
`ceil(raw_data / (disk_per_host * (1 - disk_margin)))`. With every node at one, `1 - disk_margin`
becomes zero, and the division fails.

The check then reports an error in a formula whose units are right: a false alarm. That false alarm
is how the problem showed up, on a model that was correct. So the check gives each node its real
value where one can be worked out. A measured constant with no value, or an input with no point
value, is given the value one. If a node's arithmetic then fails, it is given a value that cancels
nothing. A node that still cannot be worked out is reported for what it is, not as a unit error:

```{literalinclude} ../sizing/evaluate.py
:language: python
:start-at: def plausible_magnitudes
:end-before: def check_units
```

## Running it

```bash
python3 scripts/verify-models.py       # every formula, in units, on every model
python3 -m pytest tests/test_models.py tests/test_dsl_rules.py tests/test_mixed_units.py  # every model typechecks, and each rule on this page
```
