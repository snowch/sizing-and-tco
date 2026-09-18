---
title: "Unit economics"
short_title: "ch17 Unit economics"
---

(unit-economics)=
# ch17 · Unit economics

## The question

What does a cost per unit have to have before it means anything?

A total is a number about one system. A unit cost is a claim that can be compared — against a
supplier, against last year, against another team — and comparison is the whole point of computing
one. A unit cost that is not comparable is worse than no unit cost, because it will be compared
anyway.

## The material

### Two divisions: a quantity and a period

```{image} _figures/unit-economics-graph.svg
:alt: Everything that feeds the unit cost, including its denominator
:width: 100%
```

A total, divided by a quantity, divided by a period. Problem 17.1 is the arithmetic, and the trap
in it is the period: per terabyte-month and per terabyte-year differ by a factor of twelve and
look equally authoritative on a slide.

In a model, the build catches that — the two have identical dimensions and different units, and
`sizing/units.py` converts. The same factor of twelve is in [Appendix D](#appendix-d-units),
where this repository nearly published it.

In a slide, nothing catches it.

### The denominator is the part nobody checks

Take one model, one set of samples, one five-year total. Ask for a cost per usable terabyte per
month. There are at least four defensible denominators, and problem 17.2 is computing all of
them:

- the capacity at the horizon — what you will be able to store at the end;
- the capacity on day one — what you can store now;
- the average of the two — a straight line under a curve that is not straight;
- the per-sample ratio — each total divided by its own capacity, then summarised.

They are not close together. The spread between them is larger than most of the things people
argue about when comparing unit costs, and every one of them is a number somebody could defend in
a meeting.

Three of the four have a subtler problem. They divide a figure from one possible world by a figure
from another: a median total that came from a set of futures, over a median capacity that came
from a different set. Only the per-sample ratio is a statement about the *same* future in
numerator and denominator.

The model's own figure uses the straight-line average, and says so in the node's note rather than
in a footnote:

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: average_usable_capacity:
:end-before: cost_per_usable_tb_month:
```

It is stated as a convention with a known bias, because that is the most anybody can honestly do.

### Why the unit cost has a wide interval

```{image} _figures/unit-economics-distribution.svg
:alt: Cost per usable TB per month, as a distribution
:width: 100%
```

That is the most counter-intuitive figure in the book, and it is worth sitting with.

A unit cost falls when growth arrives. You bought a cluster for a future; if the future turns up,
you use the cluster you bought and the cost per terabyte is low. If it does not, you have paid for
capacity nobody filled, and the same cluster is expensive per terabyte.

So the wide interval on this figure is not measurement error. It is the model saying that **the
unit cost of a cluster depends on something that has not happened yet** — and that most of the
uncertainty is in the denominator rather than in the numerator.

```{include} _generated/unit-economics-tornado.md
```

That is why the growth rate is at the top of this tornado too, and why a unit cost quoted without
a date is quoting a guess about the future.

### What makes a unit cost comparable

Three things, and a unit cost missing any of them cannot be compared with anything:

**The period.** Per month or per year, stated. See above.

**The denominator's definition.** Usable or raw, at what point in the life, before or after
replication, before or after compression. Two organisations comparing "cost per terabyte" are
usually comparing different terabytes, and the ratio between raw and usable in
[ch09](#capacity) is larger than the difference either is arguing about.

**What is in the numerator.** People or not. Network or not. The building or not. A supplier's
figure includes their margin and excludes your staff; an internal figure usually does the reverse.

The book's own figure states all three in the model file, where a reviewer can see them. A unit
cost stated that way is the only kind that survives being quoted by somebody who was not there.

### What a unit cost is for

Not for deciding. It is a comparison, and comparisons are how you find the question worth asking:
a unit cost that is out of line with a supplier's is a reason to go and find out why, not a reason
to buy from the supplier.

The decision needs the total, the risk, and what the alternatives would cost —
[ch21](#a-tco-for-finance). A unit cost is what gets you invited to that meeting.

## What this cannot tell you

**Whether the comparison is like for like.** Everything above makes this model's figure explicit.
It does nothing at all about the figure it is being compared against, which will have its own
conventions and will not state them.

**What the right denominator is.** The four in problem 17.2 are all defensible and the model picks
one. There is no fact of the matter — only a convention, stated or unstated, and this book's
position is that stating it is the whole of the discipline.

**What the structure omits.** A unit cost inherits every missing line from the total it comes from
([ch15](#capex-opex-and-lifecycle)), and dividing by a large denominator makes a missing line look
smaller rather than making it visible. [ch20 · The missing node](#the-missing-node).

**Anything about marginal cost.** Every figure here is an average: total over quantity. What the
*next* terabyte costs is a different number, usually much lower until a threshold and then equal
to a whole machine, and no average can express that ([ch08](#regime-changes)).

## Problems

Two, in `tests/unit_economics/`.

**17.1 — A total, a quantity, a period.**
Two divisions. If your answer is out by twelve, one of you is working in years.

```bash
python3 -m pytest tests/unit_economics/test_problem_1_unit_cost.py
```

**17.2 — Four defensible denominators.**
Compute all four, look at the spread, and then decide which you would put on a slide — and whether
you would be willing to say which it was.

```bash
python3 -m pytest tests/unit_economics/test_problem_2_denominators.py
```

## Where to go next

[ch18](#the-five-year-model) is what happens when a unit cost from one model becomes an input to
another, which is where most of them end up.

[ch19](#which-input-is-the-answer) is the question the tornado above keeps raising.
