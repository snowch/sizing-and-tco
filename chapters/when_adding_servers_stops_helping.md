---
title: "When adding servers stops helping"
short_title: "ch07 When adding servers stops helping"
---

(when-adding-servers-stops-helping)=
# ch07 · When adding servers stops helping

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch06](#queueing-and-the-knee) |
| **What it produces** | The scaling curve, and the peak the coefficients predict |
| **Built from** | `scaling-curve`, `service_tier-reference`, `service_tier-twice_the_nodes` |
:::

## The question

How far does a system scale, and how would you find out from the two measurements you actually
have?

[ch06](#queueing-and-the-knee) ended with a tier too close to its margin and an obvious remedy:
buy more machines. This chapter is about how much less that works than the arithmetic suggests,
and about the fact that it eventually works in reverse.

## The material

### Two costs, and only one of them is famous

Machines do not simply add up, and there are two separate reasons.

**Contention.** Some fraction of the work cannot be done in parallel — a lock, a single writer, a
shared queue, a coordinator. That fraction costs a fixed share of every machine you add. It grows
with the *count*, it flattens the curve, and it is the famous one: Amdahl's argument, and the
ceiling it implies.

**Crosstalk.** Machines have to agree with each other. Every new one has to be told about all the
others, so the cost grows with the number of *pairs* rather than the number of machines.

That second term is the one worth internalising, because it does something contention never does.
Contention flattens a curve. Crosstalk **turns it over**. Past some count, the next machine costs
more in agreement than it brings in work, and the total goes down.

Both terms together are the universal scalability law @gunther2007usl:

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: achievable_throughput:
:end-before: scaling_efficiency:
```

### What it looks like

```{image} _figures/when-adding-servers-stops-helping-curve.svg
:alt: Throughput against node count, against the straight line a budget assumes
:width: 100%
```

The dashed line is what a budget assumes. The solid one is what the machines do. They separate
almost immediately, and the dashed line leaves the top of the figure while the real curve is still
climbing slowly — and then stops climbing.

```{include} _generated/when-adding-servers-stops-helping-table.md
```

Read the last column, which is what each machine is worth. It falls the whole way down. By the
peak, a machine is contributing a fraction of what the first one did, and every one after that
contributes less than nothing.

The last row is the thing to trust. The peak found by sweeping the model and the peak its two
coefficients predict are computed independently, and they agree — which is the only reason the
closed form in problem 7.3 is worth having.

### What doubling actually buys

```{include} _generated/when-adding-servers-stops-helping-scenarios.md
```

Twice the machines. Read down.

Utilisation halves, exactly as arithmetic says it should. Waiting time falls by a great deal more
than half, because [ch06](#queueing-and-the-knee)'s division is not linear and this is the
direction in which that helps you.

And throughput goes up by not much more than a quarter — for a doubling of the fleet.
Efficiency falls by more than a third at the same time, which is the same fact stated as an
accusation.

So: doubling a tier is an excellent way to fix latency and a poor way to buy capacity. Those are
different purchases, they are usually conflated, and the model tells them apart.

### The utilisation you were quoted was optimistic

Here is the part [ch06](#queueing-and-the-knee) could not say, because it had no scaling term.

The queueing chapter computed utilisation as work arriving divided by what the machines could do
*if each of them worked alone*. But they do not work alone. Some of their capacity is spent on
each other, and the honest utilisation is the arriving work divided by what the tier can actually
deliver.

The model carries both numbers, side by side, on purpose:

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: utilisation_including_coordination:
:end-before: optimism:
```

At the reference point the two differ by half again. The queueing view is not wrong; it is
optimistic, by a factor nobody notices until they measure the tier at two sizes and find the
second one disappointing.

Which is precisely how the coefficients get fitted.

### Fitting it from what you have

Three unknowns, so three measurements determine them exactly. You will usually have: one machine
on a bench, the cluster you are running, and the cluster you were running before you grew it.
That is not much data and it is what exists.

Problem 7.2 is the algebra. It is worth doing by hand once, because rearranging the law to make it
linear is the step that shows why three points is the minimum and why they must be at *different*
counts — two measurements at the same size determine nothing at all.

Then notice what you have done. You have extended a two-parameter curve out to hundreds of
machines from three points clustered at the low end, and you are about to spend money on the
extrapolation. The coefficients in this book's model are assumptions and say so in their
provenance. **The shape is the claim. The position of the peak is a guess.**

## What the model says

```{include} _generated/when-adding-servers-stops-helping-table.md
```

```{include} _generated/when-adding-servers-stops-helping-scenarios.md
```

## What this cannot tell you

**Where your peak is.** The coefficients here are assumptions, the peak follows from them, and the
model's own tornado shows the peak's interval spans a factor of several. Fitting them from three
measurements gives numbers with the same problem and a false air of precision. What transfers is
that a peak exists and is a property of the software.

**Whether the coefficients are stable.** They are fitted from a system doing one kind of work at
one size. A different workload mix has a different serial fraction; a version that adds a
coordination round has different crosstalk. A curve fitted last year describes last year's
software.

**What to do about it.** The law says where scaling stops paying. It has nothing to say about
which lock to remove, and removing the lock changes the coefficients in a way only another
measurement can establish.

**Anything about failure.** Every figure above is a healthy tier. Machines coordinating while one
of them is unreachable behave differently and worse, and this model has no term for it —
[ch11](#headroom-and-failure-domains) is where that gets a margin rather than a model.

**Whether the tier is even the constraint.** The whole chapter assumes throughput is what you are
buying. If the system is bounded by something else — a database, a licence, a single-threaded
step — the curve above is a description of a queue in front of the real problem.

## Problems

Three, in `tests/when_adding_servers_stops_helping/`.

**7.1 — Write the law.**
Two terms in the denominator, behaving differently. The tests check that contention alone flattens
the curve and that crosstalk alone turns it over, which is the distinction worth having.

```bash
python3 -m pytest tests/when_adding_servers_stops_helping/test_problem_1_law.py
```

**7.2 — Fit it from three measurements.**
Rearrange the law until it is linear, then solve. Write the rearrangement down before you code it.

**7.3 — Find the peak.**
Differentiate and set to zero. It comes out as a square root, and it says the peak belongs to the
software rather than to the budget. Handle zero crosstalk honestly: there is no peak, and a large
number is not the same answer.

Both are checked by one file, because the peak is what the fit is for:

```bash
python3 -m pytest tests/when_adding_servers_stops_helping/test_problem_2_fit.py
```

## Where to go next

Gunther's paper @gunther2007usl derives the law from a queueing argument rather than by fitting a
curve to data, which is worth reading if the second term has so far felt like an extra parameter.

[ch08](#regime-changes) is what this chapter and the last one have in common: a place where the
chain of multiplications stops describing anything, and why no amount of care about the inputs
would have warned you.
