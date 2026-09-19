---
title: "When adding servers stops helping"
short_title: "ch07 When adding servers stops helping"
---

(when-adding-servers-stops-helping)=
# ch07 · When adding servers stops helping

## The question

How far does a system scale, and how would you find out from the two measurements you actually
have?

[ch06](#queueing-and-the-knee) ended with a fleet too close to its margin and an obvious remedy:
buy more machines. This chapter is about how much less that buys than the arithmetic promises. It
is also about the count past which each new machine takes capacity away.

## The material

### Two costs, and only one of them is famous

Machines do not simply add up, and there are two separate reasons.

**Contention.** Some fraction of the work cannot be done in parallel: a lock, a single writer, a
shared queue, a coordinator. That fraction takes a fixed share of every machine you add, so the
cost grows with the *count* of machines, and the curve flattens. This is the famous one: Amdahl's
argument, and the ceiling it implies.

**Crosstalk.** Machines have to agree with each other. Every new one has to be told about all the
others, so the cost grows with the number of *pairs*, not the number of machines.

Crosstalk does something contention never does. Contention flattens the curve. Crosstalk **turns
it over**. Past some count, the next machine costs more in agreement than it brings in work, and
the total goes down.

Both terms together are the universal scalability law @gunther2007usl:

```{literalinclude} ../models/web_service/stages/06-scaling/model.yaml
:language: yaml
:start-at: achievable_throughput:
:end-before: scaling_efficiency:
```

### The curve, against the straight line

```{image} _figures/when-adding-servers-stops-helping-curve.svg
:alt: Throughput against host count, against the straight line a budget assumes
:width: 100%
```

The dashed line is what a budget assumes. The solid one is what the machines do. They separate
almost immediately. The dashed line leaves the top of the figure while the real curve is still
climbing slowly, and then the real curve stops climbing.

```{include} _generated/when-adding-servers-stops-helping-table.md
```

Read the last column: what each machine is worth. It falls the whole way down. By the peak, a
machine contributes a fraction of what the first one did. Every machine after that contributes
less than nothing.

The last row checks the peak twice. One figure comes from sweeping the model, the other from its
two coefficients. The calculations are independent, and they agree. That agreement is why the
closed form in problem 7.3 is worth having.

### What doubling actually buys

```{include} _generated/when-adding-servers-stops-helping-scenarios.md
```

Twice the hosts. Read down.

Utilisation halves, exactly as arithmetic says it should. Time spent queueing falls to about a
quarter, because [ch06](#queueing-and-the-knee)'s division is not linear, and in this direction
the non-linearity runs in your favour. The share of futures over the knee falls by more still.

Throughput goes up by about a third, for a doubling of the fleet. Efficiency falls by about a
third at the same time. That is the same fact, counted from the other end.

So doubling a fleet is an excellent way to fix latency and a poor way to buy capacity. Those are
different purchases. They are usually conflated, and the model tells them apart.

Both are in the graph, and so is the peak. Drag *crosstalk* and watch the peak move while the
fleet you have stays where it is.

```{iframe} /models/web_service_scaling-reference.html
:width: 100%
The graph as ch07 leaves it. Two ceilings arrived with it: one on what the fleet spends on itself,
one on the utilisation the queueing view understated.
```

### The utilisation you were quoted was optimistic

[ch06](#queueing-and-the-knee) had no scaling term, so its utilisation was the work arriving
divided by what the machines could do *if each of them worked alone*. They do not work alone. Some
of their capacity is spent on each other, and the honest utilisation is the arriving work divided
by what the fleet can actually deliver.

The model carries both numbers, side by side, on purpose:

```{literalinclude} ../models/web_service/stages/06-scaling/model.yaml
:language: yaml
:start-at: utilisation_including_coordination:
:end-before: optimism:
```

At the reference point the two differ by half again. The queueing view is not wrong. It is
optimistic, by a factor nobody notices until they measure the fleet at two sizes and find the
second one disappointing.

Measuring the fleet at more than one size is also how the coefficients get fitted.

```{iframe} /playground/when-adding-servers-stops-helping/
:width: 100%
The same file, running. Double the contention and watch where the peak goes: it is the software's
number, and no host count in the file moves it.
```

### Fitting the coefficients from what you have

Three unknowns, so three measurements determine them exactly. You will usually have three: one
machine on a bench, the fleet you are running, and the fleet you were running before you grew it.
That is not much data, and it is what exists.

Problem 7.2 is the algebra, and it is worth doing by hand once. Rearranging the law into a
straight line shows why three points are the minimum, and why they must be at *different* counts.
Two measurements at the same size determine nothing at all.

Then notice what you have done. You have extended a two-parameter curve out to hundreds of
machines from three points clustered at the low end, and you are about to spend money on the
extrapolation. The coefficients in this book's model are assumptions, and they say so in their
provenance. **The shape is the claim. The position of the peak is a guess.**

## What this cannot tell you

**Where your peak is.** The coefficients here are assumptions, and the peak follows from them.
The model's own interval on the peak spans more than a factor of three. Fitting the coefficients
from three measurements gives numbers with the same problem and a false air of precision. What
transfers is that a peak exists, and that it is a property of the software.

**Whether the coefficients are stable.** They are fitted from a system doing one kind of work at
one size. A different workload mix has a different serial fraction. A version that adds a
coordination round has different crosstalk. A curve fitted last year describes last year's
software.

**What to do about it.** The law says where scaling stops paying. It has nothing to say about
which lock to remove, and removing the lock changes the coefficients in a way only another
measurement can establish.

**Anything about failure.** Every figure above is a healthy fleet. Machines coordinating while one
of them is unreachable behave differently and worse, and this model has no term for it.
[ch11](#headroom-and-failure-domains) is where that gets a margin rather than a model.

**Whether the fleet is even the constraint.** The whole chapter assumes throughput is what you are
buying. If the system is bounded by something else, a database, a licence or a single-threaded
step, the curve above describes a queue in front of the real problem.

## Problems

Four, in `tests/when_adding_servers_stops_helping/`. The first three have tests. The last does not,
and says why.

**7.1 — Write the law.**
Two terms in the denominator, behaving differently. The tests check that contention alone flattens
the curve and that crosstalk alone turns it over, so the two cannot stand in for each other.

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

**7.4 — The time adding machines did not help.** No test: the answer is in somebody's memory, not
in a file.

Ask the people who were there. Somewhere in your organisation there is a tier that got a bigger
fleet and did not get proportionally faster, and somebody has a theory about why.

Write down the theory, then write down which of this chapter's two costs it corresponds to:
contention for something shared, or the cost of machines agreeing with each other. If it is
neither, you have found a third mechanism, which is more interesting than the chapter.

A good answer names the tier, the change in machine count, the change in throughput, and which
mechanism it was. If nobody can remember a case, that is an answer too. It means you have never
been near the peak, and the coefficients in this chapter are not about you.

## Where to go next

Gunther's paper @gunther2007usl derives the law from a queueing argument rather than by fitting a
curve to data. Read it if the crosstalk term has so far felt like a free parameter.

[ch08](#regime-changes) is what this chapter and the last one have in common: a point where the
chain of multiplications stops describing the system, and no care over the inputs would have
warned you.
