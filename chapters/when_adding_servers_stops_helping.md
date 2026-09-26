---
title: "When adding servers stops helping"
short_title: "ch07 When adding servers stops helping"
---

(when-adding-servers-stops-helping)=
# ch07 · When adding servers stops helping

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

How far does a system scale, and how would you find out from the three measurements you have?

[ch06](#queueing-and-the-knee) ended with a fleet too close to its margin and an obvious remedy:
buy more machines. This chapter is about how much less that buys than the arithmetic promises. It
is also about the count past which each new machine takes capacity away.

## The material

### Two costs, and only one of them is famous

Machines do not add up, and there are two separate reasons.

**Contention.** Some fraction of the work cannot be done in parallel: a lock, a single writer, a
shared queue, a coordinator. That fraction takes a fixed share of every machine you add, so the cost
grows with the *count* of machines and the curve flattens. This is the well-known one of the two
costs: Amdahl's argument @amdahl1967validity. With contention alone, throughput approaches a limit
as machines are added and never reaches it, so the curve never turns down.

**Crosstalk.** Machines have to agree with each other. Every new one has to be told about all the
others, so the cost grows with the number of *pairs*, not the number of machines. Ten machines
make forty-five pairs. Twenty make a hundred and ninety. Doubling the fleet did not double the
agreeing; it roughly quadrupled it.

Crosstalk does something contention never does. Contention flattens the curve. Crosstalk **turns
it over**. Past some count, the next machine costs more in agreement than it brings in work, and
the total goes down.

Both terms together are the universal scalability law @gunther2007usl:

```{literalinclude} ../models/web_service/stages/10-scaling/model.yaml
:language: yaml
:start-at: linear_throughput:
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

The Throughput column rises to the row marked **peak**, then falls in every row after it. Past the
peak, the next machine contributes less than nothing—the machines added took away more throughput
than they brought. The Per host column is the fleet's throughput divided by its host count: the
average over every machine in the fleet, not what the last machine alone added. Per host falls in
every row but never goes below zero, even past the peak, so the drop shows in the Throughput column
instead.

The last row gives the peak twice: one figure from sweeping the host count through the table and
taking the largest throughput, and another from the two coefficients alone. The two are computed
independently, and they agree to within the spacing of the sweep—the swept peak can only land on a
row of the table. The closed form in problem 7.3 lets you find the peak from the two coefficients
alone, without sweeping through the curve.

### The utilisation you were quoted was optimistic

[ch06](#queueing-and-the-knee) had no scaling term, so its utilisation was the work arriving
divided by what the machines could do *if each of them worked alone*. They do not work alone. Some
of their capacity is spent on each other, and the honest utilisation is the arriving work divided
by what the fleet can deliver.

The model carries both numbers, side by side, on purpose:

```{literalinclude} ../models/web_service/stages/10-scaling/model.yaml
:language: yaml
:start-at: utilisation_including_coordination:
:end-before: optimism:
```

The table at the start of the next section prints both utilisations: the queueing view and the one
that counts coordination. Compare the two in the first column to see the gap between them for the
fleet as it stands. The queueing view is not wrong. It is optimistic, and you do not see how much
until you measure the fleet at two sizes and find the larger one delivers less than the arithmetic
promised.

### What doubling buys

```{include} _generated/when-adding-servers-stops-helping-scenarios.md
```

The table compares the fleet as it stands with the same workload on twice the hosts, with everything
else unchanged. The *Ratio* column divides the second by the first. *Hosts in the fleet* and
*throughput if scaling were free* both double. The straight line is one host's throughput times the
count. The throughput the fleet can actually reach rises much less than double, so scaling
efficiency—that throughput divided by the straight line—falls: its *Ratio* is throughput's halved.

*Utilisation* halves: the same busy cores divided by twice the cores, and it is the queueing figure
from [ch06](#queueing-and-the-knee), which does not count coordination. *Utilisation, counting
coordination* falls by much less than half, as it divides the arriving work by what the fleet
actually delivers, which rose by less than double. Time spent queueing falls by more than half
because the calculation uses the optimistic *utilisation* and [ch06](#queueing-and-the-knee)'s
non-linear division, which works in your favour in this direction. *Where adding hosts stops
helping* does not move, as it depends on the two coefficients, not on fleet size.

The next two tables show ch06's ceilings table for the fleet as it stands and for twice the hosts.
They hold the ceiling ch06 introduced and the two this chapter adds. For both utilisation ceilings,
the shares of futures past the allowed line and past the limit fall when the fleet doubles, as the
*Over allowed* and *Over limit* columns show. *Fraction of the fleet doing nothing useful* has a
limit of one—a fleet cannot waste more than all of its work—so it never passes its limit; read its
allowed line instead. That row moves the opposite way when the fleet doubles: its value rises, its
verdict worsens, and the share of futures past the allowed line rises. This ceiling protects a
budget, not latency—nothing fails and nobody is paged—and a fleet past its allowed line is paying
for hosts whose work goes to coordination and contention rather than to requests.

Doubling a fleet buys lower queueing time, by the optimistic measure, and little extra
capacity—different purchases. A request for more hosts does not say which it is buying; the table
shows them as separate rows so you can see which you are getting. The graph below has sliders for
*contention* and *crosstalk*: drag *crosstalk* and the peak moves, while the fleet you have stays
where it is.

```{iframe} /models/web_service_scaling-reference.html
:width: 100%
The graph as ch07 leaves it. Two ceilings arrived with it: one on what the fleet spends on itself,
one on the utilisation the queueing view understated.
```

### Fitting the coefficients from what you have

Measuring the fleet at more than one size is also how you fit the coefficients. The law has three
unknowns—one host's throughput, contention and crosstalk—and three measurements at three different
host counts determine them exactly. You will usually have three: one machine on a bench, the fleet
you run now, and the fleet you ran before you grew it. That is not much data, and it is what exists.

Problem 7.2 is the algebra. Do it by hand once. Rearranging the law into a straight line shows why
three points are the minimum and why they must be at different counts. Two measurements at the same
count tell you no more than one of them.

Then notice what you have done. You have extended a curve with three numbers in it out to hundreds
of machines, from three points clustered at the low end, and you are about to spend money on the
extrapolation. The coefficients in this book's model are not fitted. They are assumptions, and their
provenance says so.

**The shape is the claim. The position of the peak is a guess.**

## What this cannot tell you

**Where your peak is.** The coefficients here are assumptions, and the peak follows from them.
The model's own range on the peak spans more than a factor of three. Fitting the coefficients
from three measurements gives numbers with the same problem and a false air of precision. What
transfers is that a peak exists, and that it is a property of the software.

**Whether the coefficients are stable.** Coefficients fitted from measurements describe one kind of
work over a narrow range of fleet sizes. The three points are at different counts, but they sit
close together at the low end of the curve. A different workload mix has a different serial
fraction, so a different contention. A version that adds a coordination round has different
crosstalk. A curve fitted last year describes last year's software.

**What queueing costs a fleet that coordinates.** This model's queue does not see coordination.
Residence time and time spent queueing are computed from *utilisation*, the figure that divides by
what each host could do alone. No node computes a queueing time from utilisation counting
coordination, in this chapter's model or in the finished one. So every latency figure on this page,
the doubling table's included, is the optimistic one, and the model cannot say by how much.

**What to do about it.** The law says where scaling stops paying. It has nothing to say about
which lock to remove, and removing the lock changes the coefficients in a way only another
measurement can establish.

**Anything about failure.** Every figure above is a healthy fleet. Machines coordinating while one
of them is unreachable behave differently and worse, and this model has no term for it.
[ch11](#headroom-and-failure-domains) is where that gets a margin rather than a model.

**Whether the fleet is even the constraint.** The whole chapter assumes throughput is what you are
buying. If the system is bounded by something else, a database, a licence or a single-threaded
step, the curve above describes a queue in front of the real problem.

## Key takeaways

:::{div}
:class: takeaways

- **Machines do not add up, for two separate reasons.** Contention takes a fixed share of every
  machine you add and flattens the curve. Crosstalk grows with the number of pairs and turns the
  curve over.
- **Past the peak, the next machine takes capacity away.** Each machine adds less throughput than
  the one before it. After the peak, the next machine adds less than nothing and the total falls.
- **Doubling the fleet fixes latency and buys little capacity.** Utilisation halves, queueing time
  falls to about a quarter, and throughput rises by a fraction. Those are different purchases.
- **The utilisation a queueing view quotes is optimistic.** Some of every machine's capacity is
  spent on the others, so the honest figure divides by what the fleet can deliver.
- **The shape of the curve is the claim. The position of the peak is a guess.** Three measurements
  at different sizes fit the coefficients exactly, and extrapolating them to hundreds of machines is
  the bet you are placing.
:::

## Problems

Four, in `tests/when_adding_servers_stops_helping/`. The first three have tests. The last does not,
and says why.

**7.1 — Write the law.**
Two terms in the denominator, behaving differently. The tests check that contention alone flattens
the curve and that crosstalk alone turns it over, so the two cannot stand in for each other.

```bash
python3 -m pytest tests/when_adding_servers_stops_helping/test_problem_1_law.py -m problem
```

**7.2 — Fit it from three measurements.**
Rearrange the law until it is linear, then solve. Write the rearrangement down before you code it.
The function returns all three unknowns: one host's throughput, contention and crosstalk.

```bash
python3 -m pytest tests/when_adding_servers_stops_helping/test_problem_2_fit.py -m problem
```

**7.3 — Find the peak.**
Differentiate and set to zero. It comes out as a square root, and it says the peak belongs to the
software rather than to the budget. Handle zero crosstalk: with no coordination cost the curve never
turns over, so there is no peak. Raise `ValueError`, or return an infinity. A large number is not
the same answer.

```bash
python3 -m pytest tests/when_adding_servers_stops_helping/test_problem_3_peak.py -m problem
```

**7.4 — The time adding machines did not help.** No test: the measurements are your fleet's, and
this repository has none of them.

Somewhere in your organisation there is a tier that got a bigger fleet and did not get
proportionally faster. Find its throughput at two fleet sizes, and a single machine's on a bench if
anyone ever ran one. Those are the three measurements the chapter says you usually have.

Put them through the rearrangement you wrote for 7.2: by hand, or by calling your `fit` at a desk.
The Check on this page runs the book's test cases, not your numbers. Then use 7.3 to write down
where the peak comes out.

With no bench figure you have two measurements and three unknowns, and the law cannot be fitted. You
can still work out throughput per host at each fleet size and say whether it fell as the fleet grew.
If it fell, something is costing you, but you cannot tell which cost or where the peak is. Say that,
and say the missing measurement is one machine on a bench under the same load.

Then write down which of this chapter's two costs the numbers point at: contention for something
shared, or the cost of machines agreeing with each other. If the fit says neither, you have found a
third mechanism. A good answer names the tier, the fleet sizes and their throughputs, the peak the
fit implies, and why you would not spend money on that peak. If you cannot find throughput at two
sizes, that is an answer too. It means nobody measured throughput per host when the fleet grew, and
the next growth is the chance to.

## Where to go next

Gunther's paper @gunther2007usl derives the law from a queueing argument rather than by fitting a
curve to data. Read it if the crosstalk term has so far felt like a free parameter.

[ch08](#regime-changes) is what this chapter and the last one have in common: a point where the
chain of multiplications stops describing the system, and no care over the inputs would have
warned you.
