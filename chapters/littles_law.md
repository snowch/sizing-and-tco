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

Part I ended with a rate: how much work arrives, at the busy hour. This chapter is the arithmetic
that turns that rate into a count of requests in flight, and a count of requests in flight back
into the time each request really spent in the system. It assumes nothing about how the system
works.

## The material

### The law

The number of requests in a system is the rate they arrive at, times how long each one stays.

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: concurrency:
:end-before: queueing_headroom:
```

That is the whole of it. One multiplication.

The law earns a chapter for what it leaves out. Nothing about how requests arrive — they may be
bursty, periodic, adversarial. Nothing about the order they are served in. Nothing about the
distribution of anything. No queueing model, no exponential anything.

One condition only: the system is in a steady state over the window you are looking at. As much
going out as coming in.

### Running the law backwards

Nobody measures residence time. It is the hardest of the three quantities to get at honestly. An
application's own timer starts when the request reaches the application, which is after it has
finished queueing — and the queueing is generally most of the answer.

But the other two are trivial. Every system counts requests. Every system can expose a gauge of
how many are in flight — a connection count, a thread-pool depth, a semaphore.

So divide. The residence time that comes out is the *true* one, including every queue the request
sat in on the way. Problem 5.2 is that division.

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

Then look at the right-hand end, where a stack of samples piles up against a wall. The wall is the
model's utilisation cap. *Utilisation* is the work arriving divided by the work the machines
could do — busy capacity over capacity owned — and past the highest utilisation this model will
admit to, it stops computing a residence time and clamps. Every sample beyond that point lands in
the same place. The pile is the model saying *I do not describe anything out here*, not the tier
doing something interesting.

None of that is a property of Little's law. One multiplication would pass an ordinary distribution
straight through. Both the width and the wall come from the other multiplicand, residence time:

```{image} _figures/littles-law-graph.svg
:alt: The sub-graph that produces the number of requests in the system
:width: 100%
```

[ch06](#queueing-and-the-knee) explains why residence time behaves like that.

### Three things the law lets you catch

**A latency that is not the latency.** Measure in-flight requests and arrival rate, divide, and
compare against what your service reports. If the two disagree, the gap is queueing that happens
before your timer starts — a connection backlog, a load balancer, a thread pool. Nothing in the
application can see that gap, and the user waits through it all the same.

**A capacity claim that cannot be true.** A system claiming to serve some rate with some
concurrency is claiming a residence time. If that residence time is below its own service time,
somebody has made an arithmetic error, and the law finds it in one line.

**A queue nobody declared.** If in-flight requests grow while the arrival rate is flat, residence
time is growing. Something downstream has slowed and the queue in front of it is absorbing the
difference — which it will keep doing silently until it cannot.

### What the law will not do

It will not tell you *why* residence time is what it is. It relates three numbers and has no
opinion about which of them is causing the others.

A law that assumes nothing has no mechanism in it, which is why this is the shortest chapter in
Part II.

## What this cannot tell you

**Anything about a system that is not in a steady state.** The one condition, and the one people
forget. During an incident — exactly when somebody reaches for the law — arrivals exceed
departures and the queue is growing, so "how many are in the system" is not a stable quantity for
the law to be about. Applied to a five-minute window in the middle of a pile-up, it produces a
number that describes nothing.

**Which of the three quantities moved.** If in-flight requests doubled, the law says the product
of the other two doubled. It cannot say which, and the two have completely different remedies.

**What the average is hiding.** The law is about averages, and a queue's average hides both of the
states it is averaging over. A system with a handful of requests in flight on average can spend
most of its time empty and the rest badly backed up. The average describes neither.

**Anything about the tail.** It relates means. A residence time inferred this way is a mean, and
it says nothing about the 99th percentile, which is the number anybody cares about during an
incident.

## Problems

Two, in `tests/littles_law/`.

**5.1 — The law.**
One multiplication, checked against the model's own node. The node reaches the same quantity by a
different route through the graph, so agreement is evidence rather than tautology. Checked at the
point estimate first, then across every sample.

```bash
python3 -m pytest tests/littles_law/test_problem_1_the_law.py
```

**5.2 — The law backwards.**
Infer residence time from in-flight requests and arrival rate — the two things every system
already exposes. Then decide what to return when nothing is arriving. That decision is a
judgement, not arithmetic.

```bash
python3 -m pytest tests/littles_law/test_problem_2_backwards.py
```

## Where to go next

Little's original proof @little1961proof is five pages, and worth reading for how little it
assumes.

[ch06](#queueing-and-the-knee) buys a mechanism. It costs assumptions, and it explains the shape
of the distribution above.
