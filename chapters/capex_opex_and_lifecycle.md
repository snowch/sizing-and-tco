---
title: "Capex, opex and where the total stops"
short_title: "ch15 Capex, opex and where the total stops"
---

(capex-opex-and-lifecycle)=
# ch15 · Capex, opex and where the total stops

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

What do you pay once, what do you pay every month, and what does this book deliberately not model?

[ch12](#the-sizing-model) chose the fleet. This chapter prices it. The arithmetic is easy. Two
things are hard. The first is the split between the invoice somebody signs and the bills that
arrive afterwards. The second is knowing where a cost model should stop.

## The material

### The split

```{include} _generated/capex-opex-and-lifecycle-split.md
```

Capital cost, or *capex*, is what you pay once. Running cost, or *opex*, is what you pay every
month for as long as you keep the fleet. The table shows the split in its two headline rows:
*Capital, paid once* and *Running, over 5 years*. Over the horizon, the running cost is several
times the capital cost.

Capital arrives as one invoice with a signature on it. So it gets a meeting, a comparison and a
negotiation. Running cost arrives in pieces, every month, from several directions: an electricity
bill, a support renewal, part of an engineer's salary. No single decision produced any of the
pieces, and each is too small to argue about on its own. So the scrutiny goes to the capital,
which is the smaller part of the total.

Problem 15.1 asks how many years of running cost equal the capital cost. The *annual opex* row in
the table under *What the model says* shows the running cost per year. The answer falls well
inside the horizon the fleet was bought for.

### What is in each

The capital rows are *Hosts* and *Network*. The hosts dominate; the network is the smaller share.
The network cost grows with the fleet because the model prices it per host, so if real switching
scales differently, this line cannot show that.

The four running rows are four different kinds of number.

**Energy** is physics in structure: the model multiplies the power per host by the number of
hosts, by a facility multiplier, by the hours in a year, and by the electricity price. The
structure is physics, but the inputs are judgements. The power per host is a vendor's claim, the
facility multiplier and the electricity price are both assumptions, and only the hours in a year
is a fact. [ch16](#power-first) is about what happens when energy stops being one line and
becomes the binding constraint.

**Licences** are a vendor's price per core per year. You pay for every core the fleet has, every
year, busy or idle. So choosing a host count also commits you to a yearly bill that you never
sign as a separate decision. Here it is the second-largest running line.

**Support** is a yearly charge set as a share of the capital cost. It is billed every year like
a running cost and the table counts it under *Running*, but it is sized by the capital, not by how
the fleet is used. So a discount on the capital also cuts the support in every year: each unit of
money taken off the purchase takes more than that off the total.

**People** is carried as about one engineer's time at a fully loaded rate (salary, employer
costs, tooling and overhead), and both the engineer count and the rate are assumptions. The line
is in the model because leaving it out is also a decision: an absent line counts as zero, and
zero has no source. Here it is the largest line in the whole total, larger than the hosts. It is
the hardest line to defend either way.

### What moves the running cost

```{include} _generated/capex-opex-and-lifecycle-tornado.md
```

The table ranks inputs by how far each moves the yearly running cost when swung across its range
with the others held still, using the same method as [ch04](#peak-mean-and-growth) but as a table
only. The top three rows are about people and licences: how many engineers, what a licence costs
per core, and what an engineer costs. The electricity price is near the bottom, next to the
support rate.

Growth does not appear in this table, although it was at the top of ch04's. The host count is
fixed—decided in [ch12](#the-sizing-model)—so no input that describes demand or growth feeds the
running cost. Because this tornado swings prices, per-host figures and the people estimate only,
the order is this model's finding: people and licences move the running cost most, and energy
moves it the least.

### The refresh at the end of the horizon

Hardware is bought against a refresh cycle, and where that cycle lands relative to the horizon
decides how many purchases the total contains. A five-year horizon with a five-year refresh is
either one purchase or two, depending on whether the refresh at the end counts. The difference is
one whole purchase: the entire *Capital, paid once* row, hosts and network together. Both
conventions are defensible, so two people with the same inputs can produce two totals that
differ by a whole purchase and both be right—provided each says which convention they used.

This book's model counts one purchase. The horizon is the refresh cycle—how long until you buy
again—so the refresh that ends the horizon buys the fleet for the next horizon. That fleet's
running cost is not in this total, and neither is its purchase: that capital belongs to the next
plan. The model writes the convention down in the note on the total:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: tco:
:end-before: # -- unit economics
```

Problem 15.2 asks about a refresh that lands on the last day of the horizon. Which convention is
correct is a modelling choice, not a fact. The test accepts either, and checks only that you
apply yours consistently. Saying which you chose, in a comment, is required.

### What this book does not model, and why

These are named here so you know each was left out on purpose, not forgotten.

**Tax and depreciation.** How capital is written down, over what period and against what depends
on the jurisdiction and the company. Any of it can change the answer. A book that guessed at it
would be giving financial advice. So the total is cash only: what leaves the bank, before tax.
Hand it to finance or a tax adviser.

**Discount rates.** Money later is worth less than money now. The rate is a policy decision, not
an engineering one, so the total is undiscounted. The model has no years in it: one yearly running
cost multiplied by the horizon, plus the capital once. Every year costs the same, and nothing
records when the capital is paid. The pieces finance needs to lay the money out by year and apply
its own rate are on this page: the capital, the yearly running cost (*annual opex* under *What the
model says*), and the horizon in the row labels.

**Procurement reality.** Lead times, minimum orders, the discount you get for asking, the price
that changes between the quote and the purchase order. All real, and none of it a modelling
problem.

**Anything with a contract in it.** Commitments, reserved capacity, early termination. Those
terms decide whether a plan can change. They are not quantities.

The line this chapter draws is **one cash total over the horizon, from physics and prices**.
Everything on the other side—when the money is spent, tax, depreciation, discounting,
procurement, and contracts—belongs to finance, tax advisers, or procurement.

### What the model says

```{include} _generated/capex-opex-and-lifecycle-outputs.md
```

The table shows capital, yearly running cost and total at their point estimates and
90% intervals. These come from the method of [ch13](#monte-carlo), where every input is drawn
together many times over. The *capex* and total point estimates match the split table's *Capital* and
**Total** rows. The *annual opex* is the yearly running cost—the split table's *Running* row
divided by the horizon—which is what Problem 15.1 needs.

The interval on the total is the only figure the rest of the page does not give. It is wider than
the whole capital cost, because the *annual opex* interval across the horizon is much wider than
the *capex* interval. The part that gets the least scrutiny—the cost arriving in pieces—is also
the part the model is least certain of.

## What this cannot tell you

**What the model's structure omits.** Every cost line above is one somebody thought of. There is
no line for rack space, cross-connects, backup, disaster recovery, the database's own licence if
it has one, or the network gear between racks. Migration is not missing: the model carries it as
a declared zero, because the design builds on the platform it already runs on. The model
reports each absent line as zero, confidently. Neither [ch13](#monte-carlo) nor
[ch14](#correlation-and-convergence) can see it. That is
[ch20 · The missing node](#the-missing-node).

**Whether the prices are yours.** Every price in the model is marked as a vendor's claim or an
assumption ([ch03](#where-the-numbers-come-from)). None was measured. A price is not the sort of
thing this repository can measure.

**What happens if the fleet is wrong.** The cost model takes the host count as given. If
[ch12](#the-sizing-model)'s fleet goes over the knee partway through its horizon, the real total
includes an unplanned purchase. No line here represents it.

**Anything about when the money is spent.** The split above is a total over a horizon. Whether
the capital lands in one quarter or three changes nothing in this model, and a great deal in
somebody's budget.

## Key takeaways

:::{div}
:class: takeaways

- **The running cost is several times the capital over the horizon, yet receives the least
  scrutiny.** Capital arrives as one signed invoice and gets a negotiation. Running cost arrives
  in pieces, each too small to argue about alone.
- **The four running lines are four different kinds of number.** Energy is physics in structure
  but claims and assumptions in its inputs, licences are a price per core, support is a yearly
  charge tied to the purchase, and people is the largest line this model includes.
- **Support is a share of the capital.** Because it is tied to the purchase, a discount on the
  capital also cuts the support in every year of the horizon.
- **Where the refresh lands against the horizon can add or remove a whole purchase.** Either
  convention is defensible if you say which you chose. This book's model counts one purchase
  because its horizon is the refresh cycle, and the note on the total says so.
- **The model produces one undiscounted cash total over the horizon, from physics and prices, and
  stops there.** When the money is spent, tax, depreciation, discount rates and procurement belong
  to finance, tax advisers, or procurement.
:::

## Problems

Three, in `tests/capex_opex_and_lifecycle/`. The first two have tests. The last does not, and says
why.

**15.1 — When does running cost overtake the purchase?**
Work out how many years of running cost add up to the capital cost, using the *Capital, paid
once* row and the *annual opex* row under *What the model says*. Then compare your answer with
the horizon and with which of the two parts gets the scrutiny, in *The split*.

```bash
python3 -m pytest tests/capex_opex_and_lifecycle/test_problem_1_crossover.py -m problem
```

**15.2 — The refresh at the end of the horizon.**
Given the capital cost, the yearly running cost, the horizon and the refresh cycle, write the
total over the horizon. The first purchase happens at the start, and the whole capital cost is
paid again at every refresh. Decide what happens when a refresh falls exactly on the end of the
horizon, defend your choice in a comment, and apply it consistently; the two choices differ by a
whole purchase.

```bash
python3 -m pytest tests/capex_opex_and_lifecycle/test_problem_2_refresh.py -m problem
```

**15.3 — Prices you can get.** No test: the right figures are your organisation's prices, and
no test in this repository can know them.

Every price in this book's model is a vendor's claim or an assumption, and the page says so under
*What this cannot tell you*. For each of the six cost lines in the split table—hosts, network,
energy, licences, support and people—record where the figure came from. For any you could not
get, record which team holds it. Count how many you obtained.

A good answer shows, for each line, a figure and its source or a named gap. It classifies each
line by its provenance kind from [ch03](#where-the-numbers-come-from): a bill, contract or invoice
is a fact; a quote is a vendor's claim; your estimate is an assumption. It counts the gaps.

An answer is wrong if it has a figure with no source, records a quote as a fact, or leaves an
unobtained line out of the count. The gaps are the finding. A total built partly from guesses is
usable if it names which lines are guesses. This book's model does that: every input carries its
kind.

## Where to go next

[ch16](#power-first) takes the energy line—physics in structure but claims and assumptions in its
inputs—and asks what changes when it stops being a line item and becomes the constraint.

[ch17](#unit-economics) turns the total into a number somebody outside the team can compare
against something.
