---
title: "Little's law"
short_title: "ch05 Little's law"
---

(littles-law)=
# ch05 · Little's law

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch02](#what-a-workload-is) |
| **What it produces** | Requests in flight, from a rate and a duration, across the whole range |
| **Built from** | `service_tier-reference` |
:::

## The question

What can you infer about a system from the one relationship that is always true, and what can you
not?

Part I was about describing demand. Part II is about what happens to a system when that demand
arrives, and it opens with the only statement in it that needs no assumptions at all.

## The material

### The law

The number of requests in a system is the rate they arrive at, times how long each one stays.

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: concurrency:
:end-before: queueing_headroom:
```

That is the whole of it. One multiplication.

What makes it worth a chapter is what it does **not** assume. Nothing about how requests arrive —
they may be bursty, periodic, adversarial. Nothing about the order they are served in. Nothing
about the distribution of anything. No queueing model, no exponential anything.

One condition only: the system is in a steady state over the window you are looking at. As much
going out as coming in. Everything else in Part II needs assumptions somebody could argue with;
this does not.

### It is usually used backwards

Nobody measures residence time. It is the hardest of the three quantities to get at honestly —
an application's own timer starts when the request reaches the application, which is after it has
finished queueing, and the queueing is generally most of the answer.

But the other two are trivial. Every system counts requests. Every system can expose a gauge of
how many are in flight — a connection count, a thread-pool depth, a semaphore.

So: divide. You get the residence time the two imply, and it is the *true* one, including every
queue the request sat in on the way. Problem 5.2 is that inversion, and it is the most immediately
useful thing in this chapter.

### What the tier says

```{include} _generated/littles-law-outputs.md
```

```{image} _figures/littles-law-concurrency.svg
:alt: Requests in the system, as a distribution on a logarithmic axis
:width: 100%
```

Look at the shape rather than at the numbers, and start with the axis: it is logarithmic, because
the middle ninety per cent of this quantity spans more than two decades. Drawn any other way it is
a spike against an empty page.

Then look at the right-hand end, where a stack of samples piles up against a wall. That is
[ch06](#queueing-and-the-knee) arriving early. Past the utilisation this model is willing to admit
to, it stops computing a residence time and clamps — so every sample beyond that point lands in
the same place, and the pile is the model saying *I do not describe anything out here* rather than
the tier doing something interesting.

None of that is a property of Little's law, which is one multiplication and would pass an ordinary
distribution straight through. It comes from the other multiplicand:

```{image} _figures/littles-law-graph.svg
:alt: The sub-graph that produces the number of requests in the system
:width: 100%
```

Residence time is what does it, and [ch06](#queueing-and-the-knee) is why.

### Three things the law lets you catch

**A latency that is not the latency.** Measure in-flight requests and arrival rate, divide, and
compare against what your service reports. If the two disagree, the gap is queueing that happens
before your timer starts — a connection backlog, a load balancer, a thread pool. That gap is
invisible to the application and is the whole of what a user experiences.

**A capacity claim that cannot be true.** A system claiming to serve some rate with some
concurrency is claiming a residence time. If that residence time is below its own service time,
somebody has made an arithmetic error, and the law finds it in one line.

**A queue nobody declared.** If in-flight requests grow while the arrival rate is flat, residence
time is growing. Something downstream has slowed and the queue in front of it is absorbing the
difference — which it will keep doing silently until it cannot.

### What it will not do

It will not tell you *why* residence time is what it is. It relates three numbers; it has no
opinion about which of them is causing the others.

That is the honest limit, and it is why this is the shortest chapter in Part II. A law with no
assumptions has no mechanism in it either, and everything from here on is the business of buying
a mechanism by making assumptions you have to state.

## What the model says

```{include} _generated/littles-law-outputs.md
```

## What this cannot tell you

**Anything about a system that is not in a steady state.** The one condition, and the one people
forget. During an incident — the exact moment somebody reaches for this — arrivals exceed
departures, the queue is growing, and "how many are in the system" is not a stable quantity for
the law to be about. Applied to a five-minute window in the middle of a pile-up, it produces a
number that describes nothing.

**Which of the three quantities moved.** If in-flight requests doubled, the law says the product
of the other two doubled. It cannot say which, and the two have completely different remedies.

**What the average is hiding.** The law is about averages, and averages of a queue are unkind.
A system averaging a handful of requests in flight can be spending most of its time empty and the
rest of it badly backed up, and the average is a description of neither state.

**Anything about the tail.** It relates means. A residence time inferred this way is a mean
residence time, and the number anybody actually cares about during an incident is the 99th
percentile, which this says nothing about.

## Problems

Two, in `tests/littles_law/`.

**5.1 — The law.**
One multiplication, checked against the model's own node — which arrives at the same quantity by a
different route through the graph, so agreeing is evidence rather than tautology. Checked at the
point estimate and then across every sample.

```bash
python3 -m pytest tests/littles_law/test_problem_1_the_law.py
```

**5.2 — The law backwards.**
Infer residence time from in-flight requests and arrival rate — the two things every system
already exposes. Then decide what to return when nothing is arriving, which is the part with a
judgement in it.

```bash
python3 -m pytest tests/littles_law/test_problem_2_backwards.py
```

## Where to go next

Little's original proof @little1961proof is five pages and is worth reading for how little it
assumes, which is the property this chapter has been claiming for it.

[ch06](#queueing-and-the-knee) buys a mechanism. It costs assumptions, and it explains the shape
of the distribution above.
