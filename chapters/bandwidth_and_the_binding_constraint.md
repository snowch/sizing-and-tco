---
title: "Three chains, and the binding constraint"
short_title: "ch10 Three chains, and the binding constraint"
---

(bandwidth-and-the-binding-constraint)=
# ch10 · Three chains, and the binding constraint

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

When three chains each demand a different size, which one are you buying?

[ch09](#capacity) followed one chain from stored bytes to hosts. There are two more: one from the
requests, one from the working set. The three disagree with each other, and the disagreement is
not to be averaged away.

## The material

### Three chains from one workload

A web service has to serve its requests, keep its working set in memory, and hold its records on
disk. Those are three requirements with three different arithmetics, and none of them can be derived
from the others.

- The request chain runs from the busy hour, through the cost of a request and the margin under the
  knee, to a number of hosts.
- The memory chain runs from the records held, through the share of them a busy hour touches, to the
  hosts whose memory can hold that with room to spare.
- The disk chain is [ch09](#capacity)'s.

The chains share inputs. One growth factor multiplies both the peak request rate and the records
held. The memory and disk chains both start from the records held. So in a future where the service
grows fast, all three chains ask for more, and they tend to rise and fall together. They still do
not move in step, because each chain has inputs the others do not have: the CPU time per request for
the request chain, the share of records touched for the memory chain, and replication, compression
and index overhead for the disk chain.

The table shows what each chain asks for, and what the model recommends, at the point estimate:
every input at the middle of its range, and the arithmetic done once.

The three counts are close together, and the memory chain asks for the most. A small move in almost
any input can change which chain is largest.

The three figures that follow show each chain's host count across all the model's futures, one
figure per chain.

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

The request and memory spreads almost coincide. The disk spread stops lower at the top. Three
separate spreads cannot say which chain is the largest in any one future, and that is the question
the purchase turns on. The table in the next section answers it future by future. None of the three
is the answer.

### Buy the largest, not the average, the usual winner or the sum

The count that satisfies all three is the largest of them, and problem 10.1 is that one function
call. There are three wrong answers, and each fails in its own way.

**The average.** It is never below all three chains, because it is at least the smallest. But it
falls short of the largest chain whenever the three differ, in almost every future, and which chain
is the largest changes from one future to the next.

**The usual winner.** The memory chain asks for the most more often than the others, but still wins
outright less than half the time. A fleet sized on it alone is too small whenever another chain asks
for more, which happens more often than not. The table in the next section shows both: "The working
set decides it" and "Sized on the memory chain alone, too small".

**The sum.** It buys a fleet for a workload that does not exist. The three chains describe the same
hosts doing three things, not three sets of hosts. So the sum buys more than any chain asked for, in
every future.

### How often each one wins

```{include} _generated/bandwidth-and-the-binding-constraint-table.md
```

No chain decides most of the time. The working set wins more often than the others. The request rate
is close behind. The disk chain, the one [ch09](#capacity) spent a chapter on, wins least. Then read
the three rows after the tie. Size on any one chain alone, even the usual winner, and the fleet is
too small more often than not. *Wins most often* is a fact about a three-way race. *Too small* is a
fact about losing to anybody.

In each future, the gap is the difference between what the winning chain asks for and the runner-up;
the row "Median gap between the winner and the runner-up" is the middle of those gaps. Set the
median gap against the three *Median of the … chain alone* rows. The gap is a sizeable share of what
any one chain asks for. These are not three estimates of the same thing that differ slightly: they
are three different questions with three different answers. The row "Gap exceeded in one future in
twenty" shows how wide the gap gets: in one future in twenty it exceeds that value.

The row "Median of the largest of the three" sits above every one of the three chain medians because
the largest of three uncertain counts usually sits above where any one of them usually does. So the
fleet the model recommends is bigger than any chain's typical answer. That is not waste. It is what
buying for three requirements at once costs, when each of them is uncertain on its own.

All three chains are in the model below, with the node that takes the largest. To read the whole
file, press **Expand** and choose **Model file**: three nodes ask for a host count, and a fourth,
*hosts the model recommends*, takes the largest. Drag *CPU time per request* **up** and watch the
Outputs list: at the book's value the memory chain asks for the most. As you drag up, only *hosts
for requests* rises, and a little above the book's value it passes *hosts for memory*, pulling
*hosts the model recommends* with it. Dragging down changes nothing, because the memory chain
already asks for more; the viewer greys the rows it cannot move, *hosts for memory* and *hosts for
storage*.

```{iframe} /models/web_service_binding-reference.html
:width: 100%
The model with three chains and the node that takes the largest. Click *hosts the model recommends*
in the Outputs list, and the Details panel shows its formula and the three chains that feed it under
*Fed by*.
```

### The shortfall, and the chain that usually wins

Sizing on the memory chain is the obvious choice, because it wins more often than either other
chain. What it costs comes down to two numbers: how often the fleet is too small because another
chain asked for more, and by how much when it is. The table above shows how often: the row "Sized on
the memory chain alone, too small", which is more often than not. How much depends on which futures
you count: in every future where the memory chain asks for at least as much as each other chain, the
shortfall is zero.

The table below has two rows for a fleet sized on the memory chain alone: "Median shortfall across
all futures" and "Average shortfall across all futures", both counting every future including the
zeros.

The median across all futures is small next to "Median of the memory chain alone"—it looks like a
rounding error—because the zeros take the lower part of the shortfalls and the middle value lands
just past them. The average across all futures is larger, pulled up by a minority of futures where
another chain asks for far more than the memory chain. So "median across all futures" makes the
shortfall look harmless, but "averaged over every future" does not.

At the point estimates in the first section, the three chains ask for nearly the same count. So
which chain wins changes with small moves in the inputs, and there is nothing unusual about a
neglected chain winning. When it does, it can win by a lot: each chain's count has a long upper
tail, with a small share of futures running on to a count far past the rest. The row "Gap exceeded
in one future in twenty" shows how wide the gap between the winner and the runner-up gets.

Count only the futures where the fleet is short, and the zeros drop out. Problem 10.2 asks for the
median counted that way. The summary of sizing on one chain is two numbers: how often it is wrong,
and how badly when it is; one of them alone is a way of not answering.

### Why this gets worse with more chains

The web service has three. A real service has more: a database's connection limit, a cache's
eviction rate, the network between the hosts, a licence tier. Each is another chance for the
answer to be set by something nobody was watching.

The chance that *some* constraint binds unexpectedly rises with the number of chains, even while
the chance of any particular one doing so stays small. Say six chains, each of which surprises you
one time in ten. If the surprises are unrelated to each other, the chance that none of them happens
is nine-tenths multiplied by itself six times, which is a little over a half. So a model with six
such chains spends about half its life with something nobody was watching in charge, and every one
of the six looked safe on its own.

But that arithmetic treats every chain as a separate gamble. The chains in this service share the
growth factor, so they tend to surprise you in the same futures. The chance that none surprises you
is then higher than the arithmetic gives. It still does not follow that more chains are safe: adding
a chain never makes it less likely that *some* chain surprises you.

The observability model in [Appendix F](#appendix-f-observability-model) also has three chains, one
each for metrics, logs and traces. There the chains are different workloads that share one ingest
pipeline and one store, so their demands add. Adding is right there, wrong here: here the three
chains are three demands of one workload on the same hosts. What carries over is the ceilings: its
three tiers carry four ceilings, each checked on its own. No single number summarises them, and a
model that produced one would hide the thing you needed.

## What this cannot tell you

**Whether there are only three chains.** This model has the three chains the book chose. A chain
that is not in the model cannot bind inside it, however often it binds outside. For this service the
likeliest missing chain is network bandwidth: ch09's erasure coding saves disk by requiring each
read to touch more machines, and the read traffic each host can carry would give a host count of its
own. This model has no network chain. The missing chain is [ch20](#the-missing-node)'s subject, and
nothing here addresses it.

**What a request costs.** The request chain rests on the CPU time one request costs, which the model
file declares an assumption, not a measurement, because no reference machine is declared. You can
read the declaration by clicking *CPU time per request* and opening *In the file* under Details. A
measured figure would be a `rig` result nobody has taken—the kind quoted from a bench with nothing
else running.

**Whether another host adds a whole host.** The request chain divides the cores busy at the busy
hour by what one host can carry, assuming each added host adds a whole host of work—that is, a
straight line. However, [ch07](#when-adding-servers-stops-helping) showed this assumption does not
hold. The model checks the fleet you decide on against coordination in the ceiling *utilisation,
counting coordination*, but the chain that recommends a count leaves it out. So wherever
coordination costs something, the request chain asks for fewer hosts than the requests need.

**Any feedback between the chains.** The chains share inputs: the growth factor, and for memory and
disk the records held, but in this model none acts on another. In a real service, a working set that
no longer fits in memory turns memory reads into disk reads, raising the cost of a request and
moving the request chain. The model flags this with the ceiling *working set against memory*, but
nothing carries that into the CPU time per request. That is [ch08](#regime-changes)'s regime change
running through the sizing arithmetic.

**Which chain binds *for you*.** The shares above come from one model's uncertainty over one
stated workload. A service that serves small records to many users and one that holds large
records for a few are the same model with different inputs and opposite answers.

## Key takeaways

:::{div}
:class: takeaways

- **Three chains size the same fleet, and none of them is the answer.** Requests, memory and disk
  each ask for a host count from a different arithmetic. They share the workload and its growth, so
  they tend to rise and fall together, but none can be worked out from the others.
- **Buy the largest, not the average, the usual winner or the sum.** The average falls short of the
  largest chain whenever the three differ. The usual winner falls short whenever another chain asks
  for more, which is more often than not. The sum buys more than any chain asked for, in every
  future.
- **No chain wins most of the time.** Size on any single chain, even the one that wins most often,
  and the fleet is too small more often than not.
- **The honest summary of sizing on one chain is two numbers.** How often it is wrong, and by how
  much when it is. Either one alone is a way of not answering.
- **More chains mean more chances to be caught out.** The chance that some constraint binds
  unexpectedly rises with their number, even while each one's chance stays small.
:::

## Problems

Three, in `tests/bandwidth_and_the_binding_constraint/`. The first two have tests. The last does
not, and says why.

**10.1 — Three chains, one purchase.**
The function `size_for_all` receives the three chains' host counts, one count per future in each. It
returns one count for every future, the count that satisfies all three chains in that future—not one
number for the whole set. One function call. Work out what happens under each of the three obvious
wrong answers before writing the right one.

```bash
python3 -m pytest tests/bandwidth_and_the_binding_constraint/test_problem_1_all_three.py -m problem
```

**10.2 — The cost of sizing on the chain that usually wins.**
The function `cost_of_sizing_on_one` receives the chain that usually wins, as `chosen`, and the
other two, as `others`. It returns two numbers. The first is the share of futures in which a fleet
sized on `chosen` alone is too small—a fraction between nought and one, not a percentage. A future
counts as too small only where some other chain asks for strictly more; a tie is not a shortfall.
The second is the median shortfall, in hosts, *in those futures only*. The first is larger than
"usually wins" suggests, and the second is what stops the shortfall looking harmless.

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

Each chain divides by a capacity less a margin: the request chain by a queueing margin, the memory
chain by a cache margin, the disk chain by a disk margin. [ch11](#headroom-and-failure-domains)
sorts margins into three kinds by what they protect—a capacity margin against a cliff, a queueing
margin against a slope, a scaling margin against a budget—and asks what happens when a host dies
at the busy hour.

[ch12](#the-sizing-model) puts all of Part III together and produces a number.
