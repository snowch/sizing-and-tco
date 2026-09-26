---
title: "Unit economics"
short_title: "ch17 Unit economics"
---

(unit-economics)=
# ch17 · Unit economics

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

What does a cost per unit have to have before it means anything?

A total is a number about one system. A unit cost is a claim that can be compared: against a
supplier, against last year, against another team. Comparison is the point of computing
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

For the cost per stored terabyte, the quantity is itself a stock: terabytes held at one moment, with
no period built in. A cost per stored terabyte needs a period added — per terabyte-month or per
terabyte-year, and that second division is where the trap sits for storage. Per terabyte-month and
per terabyte-year differ by a factor of twelve, and on a slide they look equally authoritative.
Problem 17.1 is that arithmetic. In a model file, the toolkit catches it: the two units have the
same dimensions and different sizes, and the toolkit converts between them.

This model's own unit cost is an example where its formula divides by a horizon in years and the
node declares its unit per month, so the build applies the factor of twelve.
[Appendix D](#appendix-d-units) lists that conversion and notes that a check comparing dimensions
alone would miss an error of that magnitude. On a slide, nothing catches it.

For the cost per million requests, the period is already inside the denominator: a rate, times
how long it ran. So the trap moves. Was the rate the busy hour or the mean? The two differ by the
ratio [ch04](#peak-mean-and-growth) put in the model. A cost per request quoted against the busy
hour is several times the same cost quoted against the mean, and both describe the same fleet.

### The denominator is the part nobody checks

Take one model, one set of samples, one five-year total, and ask for a cost per stored terabyte per
month. The denominator hides two separate choices, and each has more than one defensible answer. The
first choice is when in the fleet's life you count what is held: on day one, at the horizon, or as
an average over the years between. The second choice is the order: divide each future's total by
that same future's holding and then take the median, or take the median total and the median holding
first, and divide one by the other. Problem 17.2 computes four combinations:

- at the horizon, medians first: what you will be paying for at the end;
- day one: what you are paying for now. Day one's holding is one number, the same in every future,
  so the order makes no difference to it;
- the straight-line average of day one and the median horizon holding, medians first;
- at the horizon, divided first: each total over what its own future holds at the horizon, then the
  median.

They are not close together. What is held at the horizon is what is held on day one, compounded over
five years by the annual growth factor, so most of the gap between the four is the first choice: day
one against the rest. Problem 17.2 shows you how far apart they are.

The second choice is about what the figure means. Dividing first keeps each future's total over that
same future's holding. Taking medians first sets a total from one set of futures over a holding from
another, so the result describes no single future.

### The model's own denominator

The model's own cost per stored terabyte-month is a fifth combination, using the straight-line
average and dividing first. Each future's total goes over the straight line between day one's
holding and that future's own horizon holding, per month. The median printed on the
cost-per-stored-terabyte chart further down this page is that fifth figure. The model states its
choice in the node's note:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: average_stored:
:end-before: outputs:
```

The holding compounds, so its curve bends upward, and the straight line between its two ends lies
above the curve everywhere in between. So the straight-line average overstates what is held on
average, and a larger denominator gives a smaller unit cost: the straight line flatters the figure.
The faster the growth, the larger the overstatement, as this table shows across the three growth
factors from the model's own band for annual growth: its p10, its median and its p90.

### Why the unit cost has a wide interval

```{image} _figures/unit-economics-distribution.svg
:alt: Cost per million requests, as a distribution
:width: 100%
```

That is the most counter-intuitive figure in the book.

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
worth asking. A unit cost that is out of line with a supplier's is a reason to find out why. It
is not a reason to buy from the supplier.

The decision needs the total, the risk, and what the alternatives would cost. That is
[ch21](#a-tco-for-finance). A unit cost is what gets you invited to that meeting.

## What this cannot tell you

**Whether the comparison is like for like.** Everything above makes this model's figure explicit.
It does nothing about the figure it is being compared against. That figure has its own
conventions, and will not state them.

**What the right denominator is.** The four in problem 17.2 are all defensible, and this book's
model uses a fifth combination, the straight-line average divided first. There is no fact of the
matter. There is only a convention, stated or unstated, and this book's position is that stating it
is the discipline.

**What the structure omits.** A unit cost inherits every missing line from the total it comes from
([ch15](#capex-opex-and-lifecycle)). Dividing by a large denominator makes a missing line look
smaller, not more visible. [ch20](#the-missing-node) teaches how to look for a line the total does
not have, an error no amount of sampling can see.

**Anything about marginal cost.** Every figure here is an average: total over quantity. What the
*next* million requests cost is a different number. It is nothing until a threshold, and then a
whole host. No average can express that ([ch08](#regime-changes)).

## Key takeaways

:::{div}
:class: takeaways

- **A unit cost is a total divided by a quantity, and the trap is in the division.** Per month and
  per year differ by a factor of twelve. The busy hour and the mean differ by the peak-to-mean
  ratio. Both look equally authoritative on a slide.
- **The denominator is the part nobody checks.** The denominator hides two choices: when in the
  fleet's life you count what is held, and whether you divide before or after taking the median. At
  least four defensible combinations exist for the same total, they are not close together, mostly
  because growth separates day one from the horizon, and only dividing first puts the same future
  above and below the line.
- **The unit cost of a fleet depends on a future that has not happened yet.** If the growth arrives,
  the fleet is cheap per request. If it does not, the same fleet is expensive. Most of the interval
  is in the denominator.
- **A unit cost is comparable only with its period, its denominator's definition and its numerator's
  contents stated.** Two organisations comparing cost per request can be comparing different
  requests without either knowing, because neither figure says which it used.
- **A unit cost finds the question worth asking. It does not decide.** The decision needs the total,
  the risk, and what the alternatives would cost.
:::

## Problems

Three problems are on this page. The first two have tests, in `tests/unit_economics/`. The third has
no test, and says why.

**17.1 — A total, a quantity, a period.**
Divide the total by the quantity and then by the period in months. If your answer is out by twelve,
one of you is working in years. If it is out by the number of months in the horizon, you have
divided only once.

```bash
python3 -m pytest tests/unit_economics/test_problem_1_unit_cost.py -m problem
```

**17.2 — Four defensible denominators.**
The test hands you the five-year totals and what is held at the horizon, sample by sample, with day
one's holding and the months in the horizon. Compute all four and look at the spread. Then set them
beside the model's own figure, the median on the cost-per-stored-terabyte chart above, which is none
of the four. Then decide which you would put on a slide, and whether you would be willing to say
which it was.

```bash
python3 -m pytest tests/unit_economics/test_problem_2_denominators.py -m problem
```

**17.3 — Your denominator, and who chose it.** No test: the denominator is a choice, and there is
no right one to check it against.

Work out your own cost per unit, then interrogate the denominator. Per terabyte stored, per
terabyte ingested, per request, per user, per team: all defensible, all different numbers. The
choice usually predates anybody currently looking at it.

Then find out what the figure is used for. A unit cost quoted in a budget meeting and a unit cost
used to decide whether to build or buy need different denominators. The same number is routinely
used for both.

A good answer gives the figure, its denominator, its period, what its numerator includes, who chose
the denominator and what the figure is used for. If you divide the total by the denominator and the
period you named and do not get the figure you started from, the denominator you were told is not
the one that was used, and the answer has to start again from the one that was. A second way to be
wrong: the person you name as having chosen the denominator did not choose it, they inherited it.
Keep going back until you find a decision, or a record that nobody made one. If the denominator
turns out to have been chosen because it made an earlier comparison look favourable, you have found
something worth more than the number.

## Where to go next

[ch18](#the-five-year-model) is what happens when a unit cost from one model becomes an input to
another, which is where most of them end up.

[ch19](#which-input-is-the-answer) is the question the tornado above keeps raising.
