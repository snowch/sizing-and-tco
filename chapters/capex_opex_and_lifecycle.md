---
title: "Capex, opex and where the total stops"
short_title: "ch15 Capex, opex and where the total stops"
---

(capex-opex-and-lifecycle)=
# ch15 · Capex, opex and where the total stops

## The question

What do you pay once, what do you pay every month, and what does this book deliberately not model?

[ch12](#the-sizing-model) chose the cluster; this chapter prices it. The arithmetic is easy. The
hard parts are the split between the invoice somebody signs and the bills that arrive afterwards,
and knowing where a cost model should stop.

## The material

### The split

```{include} _generated/capex-opex-and-lifecycle-split.md
```

Read the two headline rows before anything else. Over the declared horizon, the capital cost and
the running cost are roughly the same size. Only the capital half got argued about.

Capital cost — *capex* — is what you pay once. Running cost — *opex* — is what you pay every
month for as long as you keep it. Those are the words the tables use and the words the room will
use, and the split between them is not an accounting formality.

Capital arrives as a single invoice with somebody's signature on it. It gets a meeting, a
comparison, a negotiation. Running cost arrives in pieces, monthly, from several directions, and
is nobody's decision in particular: an electricity bill, a support renewal, a fraction of a
salary. Each piece is too small to argue about and the total is not.

Problem 15.1 is that division. Run it against the table above and the running cost overtakes the
purchase inside the horizon the cluster was bought for. The argument was had about the smaller
half.

### What is in each

The capital rows split three ways. The chassis dominates. The drives are a smaller share than
most people guess. The network is the smallest of the three, and it grows with cluster size in a
way this model does not capture.

The three running rows are three different kinds of number.

**Energy** is physics: watts times hours times price, with a facility multiplier on top. It is the
one line in the model with no judgement in it at all, and [ch16](#power-first) is about what
happens when it becomes the binding constraint rather than a line item.

**Support** is a percentage of capital, so it is not really a running cost. It is a deferred part
of the purchase, indexed to the purchase. Negotiate the capital down and the support falls with
it, which is worth knowing before you negotiate.

**People** is the line most models omit and the one that is hardest to defend either way. The
model carries a fraction of an engineer at a fully loaded rate, both of them assumptions. It is
in the model because leaving it out is a decision too, and a less honest one.

### What moves the running cost

```{include} _generated/capex-opex-and-lifecycle-tornado.md
```

The running cost moves with the things you would expect, in an order most people get wrong. The
support rate — a percentage nobody negotiates, because it is presented as standard — moves the
annual figure more than the electricity price does.

### The refresh, and the convention nobody writes down

Hardware is bought against a refresh cycle, and where that cycle lands relative to the horizon
decides how many purchases the total contains.

A five-year horizon with a five-year refresh is either one purchase or two, depending on whether
the refresh at the end counts. Nobody writes the convention down. The difference is an entire
cluster — the largest single line in the model — and two people can produce two totals from the
same inputs and both be right.

Problem 15.2 is that boundary. Which convention is correct is a modelling choice rather than a
fact, so the test accepts either and checks only that you are consistent. Saying which you chose
is the part that is not optional.

### What this book does not model, and why

Named here so nobody has to guess whether it was forgotten.

**Tax and depreciation.** How capital is written down, over what period, against what — all of it
is jurisdiction- and company-specific, all of it changes the answer a great deal, and a book that
guessed at it would be giving financial advice. This chapter produces a cash total: what leaves
the bank, and when. Hand that to somebody who knows your tax position.

**Discount rates.** Money later is worth less than money now, by a rate that is a policy decision
rather than an engineering one. The model produces undiscounted cash flows on purpose, so that
whoever applies a discount rate applies theirs.

**Procurement reality.** Lead times, minimum orders, the discount you get for asking, the price
that changes between the quote and the purchase order. Real, and not a modelling problem.

**Anything with a contract in it.** Commitments, reserved capacity, early termination. Those are
the terms that decide whether a plan can change, and they are not quantities.

The line this chapter draws is: **cash out, over time, from physics and prices**. Everything on
the other side of it belongs to somebody whose job it is.

### What the model says

```{include} _generated/capex-opex-and-lifecycle-outputs.md
```

## What this cannot tell you

**What the model's structure omits.**
Every cost line above is one somebody
thought of. There is no line for rack
space, cross-connects, backup, disaster
recovery, licences, the network gear
between racks, or the cost of the
migration that fills the cluster. Each
absent line is a cost the model reports as
zero, confidently, and neither [ch13](#monte-carlo) nor [ch14](#correlation-and-convergence)
can see it. That is [ch20 · The missing node](#the-missing-node).

**Whether the prices are yours.** Every price in the model is marked as a vendor's claim or an
assumption ([ch03](#where-the-numbers-come-from)). None was measured, because a price is not the
sort of thing this repository can measure.

**What happens if the cluster is wrong.** The cost model takes the node count as given. If
[ch12](#the-sizing-model)'s cluster runs out of space partway through its horizon, the real total
includes an unplanned purchase that no line here represents.

**Anything about when the money is spent.** The split above is a total over a horizon. Whether the
capital lands in one quarter or three changes nothing in this model and a great deal in somebody's
budget.

## Problems

Two, in `tests/capex_opex_and_lifecycle/`.

**15.1 — When does running cost overtake the purchase?**
One division. Then look at where it falls relative to the horizon, and at which of the two halves
got the meeting.

```bash
python3 -m pytest tests/capex_opex_and_lifecycle/test_problem_1_crossover.py
```

**15.2 — The refresh, and the convention nobody writes down.**
Decide what happens when a refresh lands exactly on the end of the horizon, defend it in a
comment, and be consistent. The difference is a whole cluster.

```bash
python3 -m pytest tests/capex_opex_and_lifecycle/test_problem_2_refresh.py
```

## Where to go next

[ch16](#power-first) takes the one line in this chapter that is physics rather than negotiation,
and asks what changes when it stops being a line item and becomes the constraint.

[ch17](#unit-economics) turns the total into a number somebody outside the team can compare
against something.
