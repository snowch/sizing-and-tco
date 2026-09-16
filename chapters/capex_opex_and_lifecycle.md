---
title: "Capex, opex and the lifecycle"
short_title: "ch15 Capex, opex and the lifecycle"
---

(capex-opex-and-lifecycle)=
# ch15 · Capex, opex and the lifecycle

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch12](#the-sizing-model) |
| **What it produces** | The storage model's capital and running cost split, over its declared horizon |
| **Built from** | `storage_cluster-reference` |
:::

## The question

What do you pay once, what do you pay every month, and what does this book deliberately not model?

Part V begins here, and it begins after Part III because cost consumes sizing's output. The
cluster has already been chosen. This is what it costs.

## The material

### The split

```{include} _generated/capex-opex-and-lifecycle-split.md
```

Read the two headline rows before anything else. Over the declared horizon, the capital cost and
the running cost are roughly the same size — and one of them was argued about.

Capital arrives as a single invoice with somebody's signature on it. It gets a meeting, a
comparison, a negotiation. Running cost arrives in pieces, monthly, from several directions, and
is nobody's decision in particular: an electricity bill, a support renewal, a fraction of a
salary. Each piece is too small to argue about and the total is not.

Problem 15.1 is the one division that makes this concrete. For most infrastructure the cumulative
running cost overtakes the purchase well inside the horizon the thing was bought for, which means
the argument was had about the smaller half.

### What is actually in each

The capital rows split three ways and the proportions are worth noticing: the chassis dominates,
the drives are a smaller share than most people guess, and the network is a rounding error that
grows with cluster size in a way this model does not capture.

The running rows are the interesting ones.

**Energy** is physics: watts times hours times price, with a facility multiplier on top. It is the
one line in the model with no judgement in it at all, and [ch16](#power-first) is about what
happens when it becomes the binding constraint rather than a line item.

**Support** is a percentage of capital, which means it is not really a running cost — it is a
deferred part of the purchase, indexed to the purchase. If capital is negotiated down, this falls
with it, which is a thing to know before negotiating.

**People** is the line most models omit and the one that is hardest to defend either way. The
model carries a fraction of an engineer at a fully loaded rate, both of them assumptions. It is
in the model because leaving it out is a decision too, and a less honest one.

### What moves it

```{include} _generated/capex-opex-and-lifecycle-tornado.md
```

The running cost is driven by the things you would expect and in an order most people get wrong.
The support rate — a percentage nobody negotiates because it is presented as standard — moves the
annual figure more than the electricity price does.

### The refresh, and the convention nobody writes down

Hardware is bought against a refresh cycle, and the cycle interacts with the horizon in a way that
is worth more than it looks.

A five-year horizon with a five-year refresh is either one purchase or two, depending on whether
the refresh at the end counts. Nobody writes the convention down. The difference is an entire
cluster — the largest single line in the model — and two people can produce two totals from the
same inputs and both be right.

Problem 15.2 is that boundary. The test accepts either convention and checks only that you are
consistent, because which one is correct is a modelling choice rather than a fact. What is not
optional is saying which you chose.

### What this book does not model, and why

Named here so nobody has to guess whether it was forgotten.

**Tax and depreciation.** How capital is written down, over what period, against what — these are
jurisdiction- and company-specific, they change the answer a great deal, and a book that guessed
at them would be giving financial advice. What this chapter produces is a cash total: what leaves
the bank and when. Hand that to somebody who knows your tax position.

**Discount rates.** Money later is worth less than money now, by a rate that is a policy decision
rather than an engineering one. The model produces undiscounted cash flows on purpose, so that
whoever applies a discount rate applies theirs.

**Procurement reality.** Lead times, minimum orders, the discount you get for asking, the price
that changes between the quote and the purchase order. Real, and not a modelling problem.

**Anything with a contract in it.** Commitments, reserved capacity, early termination. Those are
the terms that decide whether a plan can change, and they are not quantities.

The line this chapter draws is: **cash out, over time, from physics and prices**. Everything on
the other side of it belongs to somebody whose job it is.

## What the model says

```{include} _generated/capex-opex-and-lifecycle-split.md
```

```{include} _generated/capex-opex-and-lifecycle-outputs.md
```

## What this cannot tell you

**What the model's structure omits.** Every cost line above is one somebody thought of. There is
no line for rack space, cross-connects, backup, disaster recovery, licences, the network gear
between racks, or the cost of the migration that fills the cluster. Each absent line is a cost the
model reports as zero, confidently, and nothing in [ch13](#monte-carlo) or
[ch14](#correlation-and-convergence) can see one. That is [ch20](#the-missing-node).

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

[ch16](#power-first) is the line in this chapter that is physics rather than negotiation, and what
changes when it stops being a line item and starts being the constraint.

[ch17](#unit-economics) turns the total into a number somebody outside the team can compare
against something.
