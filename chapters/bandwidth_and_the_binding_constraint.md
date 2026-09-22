---
title: "Three chains, and the binding constraint"
short_title: "ch10 Three chains, and the binding constraint"
---

(bandwidth-and-the-binding-constraint)=
# ch10 · Three chains, and the binding constraint

## The question

When three independent chains each demand a different size, which one are you buying?

[ch09](#capacity) followed one chain from stored bytes to hosts. There are two more: one from the
requests, one from the working set. The three disagree with each other, and the disagreement is
not to be averaged away.

## The material

### Three chains, sharing a workload and nothing else

A web service has to serve its requests, keep its working set in memory, and hold its records on
disk. Those are three requirements with three different arithmetics, and none of them can be
derived from the others.

- The request chain runs from the busy hour, through the cost of a request and the margin under
  the knee, to a number of hosts.
- The memory chain runs from the records held, through the share of them a busy hour touches, to
  the hosts whose memory can hold that with room to spare.
- The disk chain is [ch09](#capacity)'s.

They share the workload and nothing else.

```{image} _figures/bandwidth-and-the-binding-constraint-requests.svg
:alt: The host count the request chain asks for
:width: 100%
```

```{image} _figures/bandwidth-and-the-binding-constraint-memory.svg
:alt: The host count the working set asks for
:width: 100%
```

```{image} _figures/bandwidth-and-the-binding-constraint-storage.svg
:alt: The host count the data on disk asks for
:width: 100%
```

Three spreads, three different shapes, and a great deal of overlap. None of them is the answer.

All three chains are in one file, and it is short enough to read in a sitting:

```{iframe} /playground/bandwidth-and-the-binding-constraint/
:width: 100%
Two more chains, added. Three nodes now ask for a host count and a fourth takes the largest.
Change the cost of a request and watch which chain is in charge.
```

### Buy the largest, not the average, the usual winner or the sum

The count that satisfies all three is the largest of them, and problem 10.1 is that one function
call. Spend a minute on the three wrong answers first. Each of them has shipped:

**The average.** It satisfies at least one chain badly, by construction, and which one depends on
the day. A fleet sized between what the requests need and what the working set needs is too small
for one of them in every future where they differ.

**The usual winner.** Take the memory chain, because it asks for the most more often than either
of the others. This is the commonest of the three. It is defensible until somebody asks the model
what "more often than either" comes to.

**The sum.** It buys a fleet for a workload that does not exist. The three chains describe the
same hosts doing three things, not three sets of hosts.

### How often each one wins

```{include} _generated/bandwidth-and-the-binding-constraint-table.md
```

No chain decides most of the time. The working set wins more often than the others. The request
rate is close behind. The disk chain, the one [ch09](#capacity) spent a chapter on, wins least.
Then read the three rows after the tie. Size on any one chain alone, even the usual winner, and
the fleet is too small more often than not. *Wins most often* is a fact about a three-way race.
*Too small* is a fact about losing to anybody.

The median gap between the winner and the runner-up, the one in the middle when every draw's
gap is sorted, is large. These are not three estimates of
the same thing that differ slightly. They are three different questions with three different
answers. Take the draw one in twenty from the top of that sorted list and the gap is larger
still.

The last row surprises people. The largest of three uncertain counts sits well
above where any one of them usually does, so the fleet the model recommends is bigger than every
chain's typical answer. That is not waste. It is what buying for three requirements at once
costs, when each of them is uncertain on its own.

All three chains are in the graph now, meeting at the node that takes the largest. Drag *CPU time
per request* down and watch which chain is in charge change hands.

```{iframe} /models/web_service_binding-reference.html
:width: 100%
Three chains and the node that picks between them. Click *hosts the model recommends* to see all
three feeding it.
```

### The shortfall, and the chain that usually wins

Sizing on the chain that wins most often is the natural thing to do, and it is what most sizing
does without saying so. Two numbers describe what it costs: how often the fleet is too small
because another chain wanted more, and by how much when it is. Problem 10.2 computes both.

Neither is small here, and people do not compute the second. Averaged over every
future, including the ones where the chosen chain was the right one and the shortfall is zero, it
looks like a rounding error. Counted only over the futures where the fleet is short, it is not. A
chain overtakes another only when its own inputs have gone somewhere unusual, and by the time
they have, the gap is wide.

So the honest summary of sizing on one chain is two numbers: how often it is wrong, and how badly
when it is. One of them alone is a way of not answering.

### Why this gets worse with more chains

The web service has three. A real service has more: a database's connection limit, a cache's
eviction rate, the network between the hosts, a licence tier. Each is another chance for the
answer to be set by something nobody was watching.

The chance that *some* constraint binds unexpectedly rises with the number of chains, even while
the chance of any particular one doing so stays small. Say six chains, each of which surprises you
one time in ten. The chance that none of them does is nine-tenths multiplied by itself six times,
which is a little over a half. So a model with six chains spends about half its life with
something nobody was watching in charge, and every one of the six looked safe on its own.

The observability model in [Appendix F](#appendix-f-observability-model) has three parallel chains
and three separate ceilings for this reason. There is no single number that summarises
them, and a model that produced one would be hiding the thing you needed.

:::{note} Key takeaways
- **Three chains size the same fleet, and none of them is the answer.** Requests, memory and disk
  each ask for a host count from a different arithmetic, and they share the workload and nothing
  else.
- **Buy the largest, not the average, the usual winner or the sum.** Each of the three wrong answers
  has shipped, and each is too small for one chain in every future where they differ.
- **No chain wins most of the time.** Size on any single chain, even the one that wins most often,
  and the fleet is too small more often than not.
- **The honest summary of sizing on one chain is two numbers.** How often it is wrong, and by how
  much when it is. Either one alone is a way of not answering.
- **More chains mean more chances to be caught out.** The chance that some constraint binds
  unexpectedly rises with their number, even while each one's chance stays small.
:::

## What this cannot tell you

**Whether there are only three chains.** This model has the three somebody thought of. A chain
that is not in the model cannot bind inside it, however often it binds outside. That is
[ch20](#the-missing-node), and nothing here addresses it.

**What a request costs.** The request chain rests on a time per request that is an
assumption, marked as such in every figure, because no reference machine is declared. A measured
one is a `rig` result nobody has taken, and it is the kind of figure that is quoted from a bench
with nothing else running.

**Anything about the three chains interacting.** They are treated as independent demands on the
same hosts. They are not. A working set that no longer fits turns memory reads into disk reads,
which raises the cost of a request, which moves the request chain. That is
[ch08](#regime-changes)'s regime change running straight through the sizing arithmetic.

**Which chain binds *for you*.** The shares above come from one model's uncertainty over one
stated workload. A service that serves small records to many users and one that holds large
records for a few are the same model with different inputs and opposite answers.

## Problems

Three, in `tests/bandwidth_and_the_binding_constraint/`. The first two have tests. The last does
not, and says why.

**10.1 — Three chains, one purchase.**
One function call. Work out what happens under each of the three obvious wrong answers before
writing the right one.

```bash
python3 -m pytest tests/bandwidth_and_the_binding_constraint/test_problem_1_all_three.py -m problem
```

**10.2 — The cost of sizing on the chain that usually wins.**
Compute how often that fleet comes up short, and the median shortfall *in those futures only*.
The first is larger than "usually wins" suggests, and the second is what stops the shortfall
looking harmless.

```bash
python3 -m pytest tests/bandwidth_and_the_binding_constraint/test_problem_2_cost.py -m problem
```

**10.3 — Which chain binds for you.** No test: which chain binds depends on quantities only you
have.

This chapter has three chains because this model has three. Work out the ones for your system:
the quantities that each, on their own, decide how many machines you need. Then work out which
binds first.

The useful part is the margin. If one chain binds at twice the other, the second is free capacity
you are paying for and nobody is counting. If they bind within a few per cent of each other, your
sizing is balanced and also brittle. A small change in either moves which one is in charge, and
the argument you rehearsed about the first chain stops applying.

A good answer names at least two chains, says which binds, and by how much. If you can only find
one chain, you have found an assumption rather than a fact.

## Where to go next

[ch11](#headroom-and-failure-domains) is the margin that sits under all three chains, and why it
is three different margins rather than one.

[ch12](#the-sizing-model) puts all of Part III together and produces a number.
