---
title: "Little's law"
short_title: "ch05 Little's law"
---

(littles-law)=
# ch05 · Little's law

## The question

What can you infer about a system from the one relationship that is always true, and what can you
not?

Part I ended with a rate: how much work arrives at the busy hour. This chapter turns that rate
into a count of requests in flight. It also turns a count of requests in flight back into the
time each request spent in the system, queues included. It assumes nothing about how the system
works.

## The material

### The law

The number of requests in a system is the rate they arrive at, times how long each one stays.

```{literalinclude} ../models/web_service/stages/04-littles_law/model.yaml
:language: yaml
:start-at: service_seconds:
:end-before: outputs:
```

That is the whole of it. One multiplication, and a label that is doing a lot of work. *If none
waited* is the time each request stays as this chapter leaves it: the time a processor spends on
it and nothing else. [ch06](#queueing-and-the-knee) adds the waiting, and this number goes up.

The law earns a chapter for what it leaves out. It says nothing about how requests arrive: they
may be bursty, periodic or adversarial. Nothing about the order they are served in. Nothing about
the shape of anything. No queueing model, no exponential anything.

It has one condition. The system is in a steady state over the window you are looking at: as much
going out as coming in.

### What a request costs, and how busy that makes the fleet

Little's law needs a rate and a time. [ch04](#peak-mean-and-growth) supplied the rate. The time
is the first quantity in this book that belongs to the software rather than to the workload:

```{literalinclude} ../models/web_service/stages/04-littles_law/model.yaml
:language: yaml
:start-at: service_demand:
:end-before: one_core:
```

Read the note on the first node twice. Service demand is how much of a processor a request
*costs*. It is not how long the request takes. The difference is queueing, and the whole of
Part II is about that difference. Service demand also belongs on a reference machine. Nobody has
declared one. So the model holds it as an assumption, and its source says what measurement would
replace it. It does not pose as a measured constant, because no measurement is behind it
([ch03](#where-the-numbers-come-from)).

The second node is the one a spreadsheet hides. Its note says why it is an input and not a
result: the model recommends a fleet, a person decides one, and every ceiling from here on asks
what happens to the fleet that was bought.

Multiply the rate by the cost and you have the processors the busy hour keeps busy. Divide by the
processors the fleet has and you have how busy it is:

```{literalinclude} ../models/web_service/stages/04-littles_law/model.yaml
:language: yaml
:start-at: cores:
:end-before: service_seconds:
```

*Utilisation* is that ratio, and it is the number [ch06](#queueing-and-the-knee) turns into a
waiting time. Nothing here says whether the fleet is too busy. That needs a ceiling, and the file
has none yet.

Here is the graph as this chapter leaves it. Click *utilisation* to see the rate and the cost
meeting. Drag *hosts in the fleet* and watch it move, while nothing yet says how far is too far.

```{iframe} /models/web_service_littles_law-reference.html
:width: 100%
The graph as ch05 leaves it: the busy hour, what a request costs, and how busy that makes a fleet.
```

```{iframe} /playground/littles-law/
:width: 100%
The same file, running. Halve the CPU time per request and watch how many requests are in flight.
```

### Running the law backwards

Nobody measures residence time. It is the hardest of the three quantities to get at honestly. An
application's own timer starts when the request reaches the application, which is after it has
finished queueing, and the queueing is generally most of the answer.

The other two are easy. Every system counts requests. Every system can expose a gauge of how many
are in flight: a connection count, a thread-pool depth, a semaphore.

So divide. The residence time that comes out is the *true* one, including every queue the request
sat in on the way. Problem 5.2 is that division.

### What the fleet says

```{include} _generated/littles-law-outputs.md
```

```{image} _figures/littles-law-in-flight.svg
:alt: Requests in flight at the busy hour, as a distribution
:width: 100%
```

Look at the shape rather than at the numbers. The width is not Little's law's doing. One
multiplication passes an ordinary spread straight through, and a product of two narrow things
would be narrow. The width comes from what is being multiplied: a busy hour five years out, which
[ch04](#peak-mean-and-growth) gave a band, and a time per request nobody has measured on this
software. The graph shows where each of them came from:

```{image} _figures/littles-law-graph.svg
:alt: The sub-graph that produces the number of requests in flight
:width: 100%
```

Two things are missing from that picture, and both arrive in the next chapter. The time each
request stays is its service time, so nothing here waits. And the utilisation in the table has
nothing to judge it against: the model can say how busy the fleet is, and cannot yet say whether
that is too busy. [ch06](#queueing-and-the-knee) supplies the waiting and the verdict together,
because they are the same fact.

### Three things the law lets you catch

**A latency that is not the latency.** Measure in-flight requests and arrival rate, divide, and
compare against what your service reports. If the two disagree, the gap is queueing that happens
before your timer starts: a connection backlog, a load balancer, a thread pool. Nothing in the
application can see that gap. The user waits through it all the same.

**A capacity claim that cannot be true.** A system claiming to serve some rate with some
concurrency is claiming a residence time. If that residence time is below its own service time,
somebody has made an arithmetic error, and the law finds it in one line.

**A queue nobody declared.** If in-flight requests grow while the arrival rate is flat, residence
time is growing. Something downstream has slowed, and the queue in front of it is absorbing the
difference. It will keep doing that silently until it cannot.

### What the law will not do

It will not tell you *why* residence time is what it is. It relates three numbers and has no
opinion about which of them is causing the others.

A law that assumes nothing has no mechanism in it, and a chapter about it has less to say than
the ones that buy one.

:::{note} Key takeaways
- **Requests in the system equal the arrival rate times the time each one stays.** One
  multiplication, true of any system in a steady state, assuming nothing about how the system works.
- **What a request costs is not how long it takes.** Service demand is processor time per request,
  the first quantity in the model that belongs to the software rather than the workload. The
  difference between the two is queueing.
- **Run the law backwards to get the residence time nobody measures.** Divide the requests in flight
  by the arrival rate, and the answer includes every queue a request sat in before your timer
  started.
- **The fleet is an input, not a result.** The model recommends a fleet, a person decides one, and
  every ceiling from here on asks what happens to the fleet that was bought.
- **The law relates three numbers and has no opinion about which one moved.** Outside a steady
  state, or about the tail, it says nothing at all.
:::

## What this cannot tell you

**Anything about a system that is not in a steady state.** The one condition, and the one people
forget. During an incident, which is when somebody reaches for the law, arrivals exceed departures
and the queue is growing. Then "how many are in the system" is not a stable quantity for the law
to be about. Applied to a five-minute window in the middle of a pile-up, it produces a number that
describes nothing.

**Which of the three quantities moved.** If in-flight requests doubled, the law says the product
of the other two doubled. It cannot say which, and the two have completely different remedies.

**What the average is hiding.** The law is about averages, and a queue's average hides both of the
states it is averaging over. A system with a handful of requests in flight on average can spend
most of its time empty and the rest badly backed up. The average describes neither.

**Anything about the tail.** It relates means. A residence time inferred this way is a mean, and
it says nothing about the 99th percentile, which is the number anybody cares about during an
incident.

## Problems

Three, in `tests/littles_law/`. The first two have tests. The last does not, and says why.

**5.1 — The law.**
One multiplication, checked against the model's own node: the one [ch06](#queueing-and-the-knee)
adds, with the waiting in it, so that the check covers the time a request stays rather than the
time it is being served. Checked at the point estimate first, then across every future the
model drew.

```bash
python3 -m pytest tests/littles_law/test_problem_1_the_law.py
```

**5.2 — The law backwards.**
Infer residence time from in-flight requests and arrival rate, the two things every system
already exposes. Then decide what to return when nothing is arriving. That decision is a
judgement, not arithmetic.

```bash
python3 -m pytest tests/littles_law/test_problem_2_backwards.py
```

**5.3 — Your own steady state.** No test: the measurement is of your queue, and nothing here can
see it.

Pick a queue you run: a request tier, a job pipeline, anything with work arriving and leaving.
Measure two of the three quantities over a window: how fast work arrives, how much is in flight,
how long a unit takes. Infer the third, then measure it too.

Watch the chapter's first limit. The law holds in a steady state, and your window almost
certainly was not one. If the inferred and measured values disagree, you have not found an
error in arithmetic that has been true since 1961. You have found out that arrivals and
departures did not balance over your window, which is worth more than the number was.

A good answer states the window, the three values, and the gap between inferred and measured. If
there is no gap at all, check whether your window was long enough to contain a busy period.

## Where to go next

Little's original proof @little1961proof is five pages, and worth reading for how little it
assumes.

[ch06](#queueing-and-the-knee) buys a mechanism. It costs assumptions, and it explains the shape
of the distribution above.
