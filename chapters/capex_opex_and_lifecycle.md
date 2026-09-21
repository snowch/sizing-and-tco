---
title: "Capex, opex and where the total stops"
short_title: "ch15 Capex, opex and where the total stops"
---

(capex-opex-and-lifecycle)=
# ch15 · Capex, opex and where the total stops

## The question

What do you pay once, what do you pay every month, and what does this book deliberately not model?

[ch12](#the-sizing-model) chose the fleet. This chapter prices it. The arithmetic is easy. Two
things are hard. The first is the split between the invoice somebody signs and the bills that
arrive afterwards. The second is knowing where a cost model should stop.

## The material

### The split

```{include} _generated/capex-opex-and-lifecycle-split.md
```

Read the two headline rows first. Over the declared horizon, the running cost is several times
the capital cost. Only the capital got argued about.

Capital cost, or *capex*, is what you pay once. Running cost, or *opex*, is what you pay every
month for as long as you keep the fleet. The tables use those words, and so will the room. The
split between them is not an accounting formality.

Capital arrives as one invoice with somebody's signature on it. So it gets a meeting, a
comparison and a negotiation. Running cost arrives in pieces, every month, from several
directions: an electricity bill, a support renewal, a fraction of a salary. Nobody in particular
decided any of them. Each piece is too small to argue about. The total is not.

Problem 15.1 is that division. Run it against the table above. The running cost overtakes the
purchase well inside the horizon the fleet was bought for. The argument was had about the smaller
part.

### What is in each

The capital rows split two ways. The hosts dominate. The network port each one needs is the
smaller share. It also grows with fleet size in a way this model does not capture: a fleet twice
the size needs more than twice the switching.

The four running rows are four different kinds of number.

**Energy** is physics: watts times hours times price, with a facility multiplier on top. It is
the one line in the model with no judgement in it. [ch16](#power-first) is about what happens
when it stops being a line item and becomes the binding constraint.

**Licences** are a vendor's price per core per year. Every core the fleet has is a core somebody
pays for annually, busy or idle. So a decision about hosts becomes a recurring bill nobody
remembers agreeing to. Here it is the second-largest running line.

**Support** is a percentage of capital. It is a deferred part of the purchase, indexed to the
purchase, rather than a running cost. Negotiate the capital down and the support falls with it.
That is worth knowing before you negotiate.

**People** is the line most models omit, and the hardest to defend either way. The model carries
a fraction of an engineer at a fully loaded rate. Both numbers are assumptions. The line is in
the model because leaving it out is a decision too, and a less honest one. Here it is the largest
line in the total. That is the usual state of affairs, and the usual reason it is left out.

### What moves the running cost

```{include} _generated/capex-opex-and-lifecycle-tornado.md
```

The running cost moves with the things you would expect, in an order most people get wrong. The
top three bars are about people and licences: how many engineers, what a licence costs per core,
and what an engineer costs. The electricity price is the line everybody expects to argue about.
It is near the bottom, with the support rate beside it.

### The refresh, and the convention nobody writes down

Hardware is bought against a refresh cycle. Where that cycle lands relative to the horizon
decides how many purchases the total contains.

Take a five-year horizon with a five-year refresh. That is either one purchase or two, depending
on whether the refresh at the end counts. Nobody writes the convention down. The difference is an
entire fleet of hosts, the largest capital line in the model. Two people can produce two totals
from the same inputs, and both are right.

Problem 15.2 is that boundary. Which convention is correct is a modelling choice, not a fact. So
the test accepts either, and checks only that you are consistent. Saying which you chose is the
part that is not optional.

### What this book does not model, and why

These are named here so nobody has to guess whether they were forgotten.

**Tax and depreciation.** How capital is written down, over what period and against what depends
on the jurisdiction and the company. All of it changes the answer a great deal. A book that
guessed at it would be giving financial advice. So this chapter produces a cash total: what
leaves the bank, and when. Hand that to somebody who knows your tax position.

**Discount rates.** Money later is worth less than money now. The rate is a policy decision, not
an engineering one. The model produces undiscounted cash flows on purpose, so that whoever
applies a discount rate applies theirs.

**Procurement reality.** Lead times, minimum orders, the discount you get for asking, the price
that changes between the quote and the purchase order. All real, and none of it a modelling
problem.

**Anything with a contract in it.** Commitments, reserved capacity, early termination. Those
terms decide whether a plan can change. They are not quantities.

The line this chapter draws is **cash out, over time, from physics and prices**. Everything on
the other side of it belongs to somebody whose job it is.

### What the model says

```{include} _generated/capex-opex-and-lifecycle-outputs.md
```

:::{note} Key takeaways
- **The running cost is several times the capital, and only the capital gets argued about.** Capital
  arrives as one signed invoice. Running cost arrives in pieces that are each too small to fight.
- **The four running lines are four different kinds of number.** Energy is physics, licences are a
  price per core, support is a deferred share of the purchase, and people is the largest line and
  the one most models leave out.
- **Support is indexed to the capital.** Negotiate the purchase down and the support falls with it,
  which is worth knowing before you negotiate.
- **Where the refresh lands against the horizon can add or remove a whole fleet.** Which convention
  is right is a choice. Saying which one you chose is not optional.
- **The model produces cash out over time, from physics and prices, and stops there.** Tax,
  depreciation, discount rates and procurement belong to somebody whose job they are.
:::

## What this cannot tell you

**What the model's structure omits.** Every cost line above is one somebody thought of. There is
no line for rack space, cross-connects, backup, disaster recovery, the database's own licence if
it has one, the network gear between racks, or the cost of the migration that fills the fleet.
The model reports each absent line as zero, confidently. Neither [ch13](#monte-carlo) nor
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

## Problems

Three, in `tests/capex_opex_and_lifecycle/`. The first two have tests. The last does not, and says
why.

**15.1 — When does running cost overtake the purchase?**
One division. Then look at where it falls relative to the horizon, and at which of the two parts
got the meeting.

```bash
python3 -m pytest tests/capex_opex_and_lifecycle/test_problem_1_crossover.py
```

**15.2 — The refresh, and the convention nobody writes down.**
Decide what happens when a refresh lands exactly on the end of the horizon. Defend it in a
comment, and be consistent. The difference is a whole fleet.

```bash
python3 -m pytest tests/capex_opex_and_lifecycle/test_problem_2_refresh.py
```

**15.3 — Prices you can get.** No test: the prices are the ones you can get, and nobody
else can get them.

Every price in this book's model is a vendor's claim or an assumption, and the chapter says so.
Try to get yours. Find the real figure for each cost line: hardware, power, licences, support and
the people. Record where each came from.

Count how many you could obtain. In most organisations the hardware price is easy. The
power price is held by a facilities team who have never been asked. The cost of the people is
either unavailable or politically impossible to write down.

A good answer has a source per line and an honest count of the gaps. The gaps are the finding. A
five-year total built from two real prices and four guesses is not a cost model. Knowing which is
which is the difference between a number and a negotiating position.

## Where to go next

[ch16](#power-first) takes the one line in this chapter that is physics rather than negotiation,
and asks what changes when it stops being a line item and becomes the constraint.

[ch17](#unit-economics) turns the total into a number somebody outside the team can compare
against something.
