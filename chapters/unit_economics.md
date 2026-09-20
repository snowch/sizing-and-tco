---
title: "Unit economics"
short_title: "ch17 Unit economics"
---

(unit-economics)=
# ch17 · Unit economics

## The question

What does a cost per unit have to have before it means anything?

A total is a number about one system. A unit cost is a claim that can be compared: against a
supplier, against last year, against another team. Comparison is the whole point of computing
one. A unit cost that is not comparable is worse than no unit cost, because it will be compared
anyway.

## The material

### Two divisions: a quantity and a period

```{image} _figures/unit-economics-graph.svg
:alt: Everything that feeds the unit cost, including its denominator
:width: 100%
```

A unit cost is a total divided by a quantity. This fleet produces two unit costs from the same
money, and the trap sits in a different place in each.

For the cost per stored terabyte, the quantity is itself per period, and the period is the trap.
Per terabyte-month and per terabyte-year differ by a factor of twelve, and they look equally
authoritative on a slide. Problem 17.1 is that arithmetic. In a model, the toolkit catches it:
the two have identical dimensions and different units, and the toolkit converts. The same factor
of twelve is in [Appendix D](#appendix-d-units), where this repository nearly published it. On a
slide, nothing catches it.

For the cost per million requests, the period is already inside the denominator: a rate, times
how long it ran. So the trap moves. Was the rate the busy hour or the mean? The two differ by the
ratio [ch04](#peak-mean-and-growth) put in the model. A cost per request quoted against the busy
hour is several times the same cost quoted against the mean, and both describe the same fleet.

### The denominator is the part nobody checks

Take one model, one set of samples, one five-year total. Ask for a cost per stored terabyte per
month. There are at least four defensible denominators, and problem 17.2 computes all of them:

- what is held at the horizon, which is what you will be paying for at the end;
- what is held on day one, which is what you are paying for now;
- the average of the two, a straight line under a curve that is not straight;
- the per-sample ratio: each total divided by what its own future holds, then summarised.

They are not close together. The spread between them is larger than most of the things people
argue about when comparing unit costs. And every one of them is a number somebody could defend in
a meeting.

Three of the four have a subtler problem. They divide a figure from one possible world by a
figure from another: a median total that came from a set of futures, over a median capacity that
came from a different set. Only the per-sample ratio puts the *same* future in the numerator and
the denominator.

The model's own figure uses the straight-line average. It says so in the node's note rather than
in a footnote:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: average_request_rate:
:end-before: cost_per_million_requests:
```

It is stated as a convention with a known bias, because that is the most anybody can honestly do.

### Why the unit cost has a wide interval

```{image} _figures/unit-economics-distribution.svg
:alt: Cost per million requests, as a distribution
:width: 100%
```

That is the most counter-intuitive figure in the book, and it is worth sitting with.

A unit cost falls when growth arrives. You bought a fleet for a future. If the future turns up,
the fleet serves the requests it was bought for, and the cost per million of them is low. If it
does not, you have paid for hosts nobody kept busy, and the same fleet is expensive per request.

So the wide interval on this figure is not measurement error. It is the model saying that **the
unit cost of a fleet depends on something that has not happened yet**. Most of the uncertainty is
in the denominator, not in the numerator.

```{include} _generated/unit-economics-tornado.md
```

That is why the growth rate is at the top of this tornado too, with the busy hour and the
peak-to-mean ratio under it and every price below those. It is also why a unit cost quoted
without a date is quoting a guess about the future.

The same total over the other denominator this fleet carries, the records it holds, is a
different unit cost with a different shape:

```{image} _figures/unit-economics-per-stored.svg
:alt: The same total over a different denominator, cost per stored TB per month
:width: 100%
```

Same money, same futures. One figure is what the fleet costs per unit of the work it does. The
other is what it costs per unit of what it keeps. A service that is mostly compute looks
expensive by the second measure and cheap by the first. Neither is the cost of anything. Each is
the answer to a question, and the question has to travel with it.

### What makes a unit cost comparable

Three things. A unit cost missing any of them cannot be compared with anything.

**The period.** Per month or per year, stated. See above.

**The denominator's definition.** Requests or terabytes. The busy hour or the mean. At what point
in the life. Before or after replication. Two organisations comparing "cost per request" are
usually comparing different requests, and the peak-to-mean ratio in
[ch04](#peak-mean-and-growth) is larger than the difference either is arguing about.

**What is in the numerator.** People or not. Network or not. The building or not. A supplier's
figure includes their margin and excludes your staff. An internal figure usually does the
reverse.

The book's own figure states all three in the model file, where a reviewer can see them. A unit
cost stated that way is the only kind that survives being quoted by somebody who was not there.

### What a unit cost is for

Not for deciding. A unit cost is a comparison, and comparisons are how you find the question
worth asking. A unit cost that is out of line with a supplier's is a reason to go and find out
why. It is not a reason to buy from the supplier.

The decision needs the total, the risk, and what the alternatives would cost. That is
[ch21](#a-tco-for-finance). A unit cost is what gets you invited to that meeting.

:::{note} Key takeaways
- **A unit cost is a total divided by a quantity, and the trap is in the division.** Per month and
  per year differ by a factor of twelve. The busy hour and the mean differ by the peak-to-mean
  ratio. Both look equally authoritative on a slide.
- **The denominator is the part nobody checks.** At least four defensible ones exist for the same
  total, they are not close together, and only the per-sample ratio puts the same future above and
  below the line.
- **The unit cost of a fleet depends on a future that has not happened yet.** If the growth arrives,
  the fleet is cheap per request. If it does not, the same fleet is expensive. Most of the interval
  is in the denominator.
- **A unit cost is comparable only with its period, its denominator's definition and its numerator's
  contents stated.** Two organisations comparing cost per request are usually comparing different
  requests.
- **A unit cost finds the question worth asking. It does not decide.** The decision needs the total,
  the risk, and what the alternatives would cost.
:::

## What this cannot tell you

**Whether the comparison is like for like.** Everything above makes this model's figure explicit.
It does nothing about the figure it is being compared against. That figure has its own
conventions, and will not state them.

**What the right denominator is.** The four in problem 17.2 are all defensible, and the model
picks one. There is no fact of the matter. There is only a convention, stated or unstated, and
this book's position is that stating it is the whole of the discipline.

**What the structure omits.** A unit cost inherits every missing line from the total it comes
from ([ch15](#capex-opex-and-lifecycle)). Dividing by a large denominator makes a missing line
look smaller, not more visible. [ch20 · The missing node](#the-missing-node).

**Anything about marginal cost.** Every figure here is an average: total over quantity. What the
*next* million requests cost is a different number. It is nothing until a threshold, and then a
whole host. No average can express that ([ch08](#regime-changes)).

## Problems

Three, in `tests/unit_economics/`. The first two have tests. The last does not, and says why.

**17.1 — A total, a quantity, a period.**
Two divisions. If your answer is out by twelve, one of you is working in years.

```bash
python3 -m pytest tests/unit_economics/test_problem_1_unit_cost.py
```

**17.2 — Four defensible denominators.**
Compute all four and look at the spread. Then decide which you would put on a slide, and whether
you would be willing to say which it was.

```bash
python3 -m pytest tests/unit_economics/test_problem_2_denominators.py
```

**17.3 — Your denominator, and who chose it.** No test: the denominator is a choice, and there is
no right one to check it against.

Work out your own cost per unit, then interrogate the denominator. Per terabyte stored, per
terabyte ingested, per request, per user, per team: all defensible, all different numbers. The
choice usually predates anybody currently looking at it.

Then find out what the figure is used for. A unit cost quoted in a budget meeting and a unit cost
used to decide whether to build or buy need different denominators. The same number is routinely
used for both.

A good answer gives the figure, the denominator, who chose it and what it is used for. If the
denominator turns out to have been chosen because it made an earlier comparison look favourable,
you have found something worth more than the number.

## Where to go next

[ch18](#the-five-year-model) is what happens when a unit cost from one model becomes an input to
another, which is where most of them end up.

[ch19](#which-input-is-the-answer) is the question the tornado above keeps raising.
