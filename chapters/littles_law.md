---
title: "Little's law"
short_title: "ch05 Little's law"
---

(littles-law)=
# ch05 · Little's law

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

What can you infer from the law when the system is steady, with as many requests leaving as
arriving, and what can you not?

Part I ended with a rate: how much work arrives at the busy hour. This chapter turns that rate
into a count of requests in flight. It also turns a count of requests in flight back into the
time each request spent in the system, queues included. It assumes nothing about how the system
works.

## The material

### The law

Residence time is the time a request spends in the system, from arriving to leaving, including
any time it waits in a queue. The law states that the number of requests in a system equals the
rate they arrive at, times their residence time. The block below is the law as a node in the
model file.

```{literalinclude} ../models/web_service/stages/08-littles_law/model.yaml
:language: yaml
:start-at: in_flight_unqueued:
:end-before: outputs:
```

That is the whole of it. One multiplication. This chapter sets the residence time equal to the
service time: how long one request takes when it waits for nothing. The node's label, *if none
waited*, marks this choice, and the formula uses the service time, the model node
`service_seconds`. The next section works it out from what a request costs.
[ch06](#queueing-and-the-knee) adds the waiting to the residence time, and this number goes up.

The law leaves out several things, which is why it gets a chapter. It assumes nothing about how
requests arrive — they may be bursty, periodic or adversarial — and nothing about the order they
are served in or the shape of anything.

The law has one condition. The system is in a steady state over the window you look at: as many
requests leave as arrive. The practical test is this: count the requests in flight at the start
and end of the window. Over the window, arrivals minus departures equals the change in that
count, because every request that arrived and has not left is still in flight. If the count at
the end is close to where it started, next to the number that arrived, the window balanced and
the law applies.

### What a request costs, and how busy that makes the fleet

Little's law needs a rate and a time. [ch04](#peak-mean-and-growth) supplied the rate: the
busy-hour request rate at the horizon. The time comes from service demand. It is the first input
in the web service model that belongs to the service's own software on a machine, rather than to
the workload.

```{literalinclude} ../models/web_service/stages/08-littles_law/model.yaml
:language: yaml
:start-at: service_demand:
:end-before: hosts:
```

Service demand is the processor time one request costs, in core-seconds, not how long the request
takes. It belongs to one build of the software on one kind of machine. Nobody has measured it here:
no reference machine is declared. Held as an unmeasured constant, it would have no value, nor would
the cores busy, the utilisation, the requests in flight, and later the waiting time or the host
count the model recommends. So the file declares it an **assumption** instead. This is not the
placeholder [ch03](#where-the-numbers-come-from) refused: an assumption carries a declared range —
the three values in the block — and every figure worked out from it carries that range too. A
placeholder is one number that passes for a measurement once it is copied. The assumption's source
says what would replace it: a measurement on a declared machine. The three values are this book's
own choice, not measured on any machine and not taken from any product.

The toolkit calls a model conditional when it holds a measured constant or a ceiling. This file
holds neither, so the toolkit calls it a definitional model. Held as a measured constant, service
demand would make it conditional. The file reads as definitional only because of this choice.

```{literalinclude} ../models/web_service/stages/08-littles_law/model.yaml
:language: yaml
:start-at: service_seconds:
:end-before: in_flight_unqueued:
```

Divide the core out of service demand and you have the service time: how long one request takes
when it waits for nothing, in seconds. It is `service_seconds`, the time the law in the section
above used.

```{literalinclude} ../models/web_service/stages/08-littles_law/model.yaml
:language: yaml
:start-at: hosts:
:end-before: one_core:
```

*Hosts in the fleet* is an input you set, not a result the model works out. A fleet worked out
from the demand would grow and shrink with the demand in every future the model drew, fitting all
of them — and the model could never show a fleet that is too small. Held fixed as an input, the
fleet stays the same while the demand varies, so the tables under "What the fleet says" further
down this page can show futures where it is too small. The model recommends a fleet; a person
decides one; the later chapters ask what happens to the fleet that was bought. The value in the
block is the host count the finished model recommends when every input is at its point estimate.
The block's note and source were written for that finished model: the ceilings, costs and
recommended host count they mention arrive in later chapters, and none is in this file yet.

Multiply the rate by the cost and you have the processors the busy hour keeps busy. Divide by the
processors the fleet has and you have how busy it is:

```{literalinclude} ../models/web_service/stages/08-littles_law/model.yaml
:language: yaml
:start-at: cores:
:end-before: service_seconds:
```

Utilisation is the cores busy divided by the cores the fleet has. It is the number
[ch06](#queueing-and-the-knee) turns into a waiting time. A utilisation above one needs no ceiling
to judge: the busy hour needs more cores than the fleet has, and the fleet cannot keep up. What
this file cannot yet say is how close to one is too close — that takes a ceiling with a margin
below it.

In the graph below, click *cores busy at the busy hour* to see the rate and the cost meet: it
lights *peak request rate at horizon* and *CPU time per request*. Drag *hosts in the fleet* and
watch *utilisation* change under **Outputs**, while *cores busy at the busy hour* stays fixed,
because it does not depend on the fleet.

```{iframe} /models/web_service_littles_law-reference.html
:width: 100%
The graph as ch05 leaves it: the busy hour, what a request costs, and how busy that makes a fleet.
```

### Running the law backwards

An application's own timer does not measure residence time. It starts when the request reaches
the application, which is after any queueing in front of it. Of the three quantities in the law,
residence time is the hardest to measure directly.

The other two are easy. Every system counts requests. Every system can expose a gauge of how many
are in flight: a connection count, a thread-pool depth, a semaphore.

So divide. Requests in flight divided by the arrival rate is the residence time, including every
queue the request sat in before the application saw it. Two hundred requests in flight while a
thousand arrive a second is a fifth of a second each — the true residence time. If the
application's timer reports less than that, the gap has one of two causes: queueing before the
timer starts, which the application cannot see, or a window in which arrivals and departures did
not balance. Problem 5.2 is that division.

### What the fleet says

```{include} _generated/littles-law-outputs.md
```

The rows *cores busy at the busy hour* and *requests in flight, if none waited* are identical in
every column. That is not a mistake. When no request waits, each request in flight holds one core
for the whole time it is in the system, so the count of requests in flight equals the count of
cores busy. Neither row depends on the fleet: both come from the arrival rate and the service
demand alone.

The utilisation row's range runs above one. The table above says in what share of the futures
that happened. Above one, the busy hour needs more cores than the fleet has, requests have to
wait, and the queue grows as long as the busy hour lasts. That breaks the law's one condition:
nothing is steady, and in those futures, the count of requests in flight describes nothing.

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

**A latency that is not the latency.** Measure the requests in flight and the arrival rate over a
window, divide, and compare the answer with the latency your service reports. A gap has one of two
causes: queueing before your timer starts — a connection backlog, a load balancer, a thread pool
— or a window in which arrivals and departures did not balance. The in-flight count at the start
and at the end of the window tells them apart: if it ended close to where it started, the window
balanced and the gap is queueing your timer cannot see. Nothing in the application can see that
queueing. The user waits through it all the same.

**A capacity claim that cannot be true.** A system claiming to serve some rate with some
concurrency is claiming a residence time. If that residence time is below its own service time,
somebody has made an arithmetic error, and the law finds it in one line.

**A queue nobody declared.** If in-flight requests grow while the arrival rate is flat, residence
time is growing. Something downstream has slowed, and the queue in front of it is absorbing the
difference. It will keep doing that silently until it cannot.

## What this cannot tell you

**Anything about a system that is not in a steady state.** The one condition: as many requests
leave as arrive over the window. During an incident, when you are most likely to reach for the
law, arrivals exceed departures and the queue grows. The count of requests in the system is not
stable, so the law has nothing steady to be about. Applied to a window in the middle of a
pile-up, it produces a number that describes nothing. The in-flight count gives it away: it ends
the window well above where it started.

**Which of the three quantities moved.** If the requests in flight doubled, the law says the
product of the other two doubled. It cannot say which. The law has no mechanism in it: it relates
three numbers and does not say which of them causes the others. A higher arrival rate needs more
capacity; a longer residence time means something has slowed, and you have to find it. The two
have different remedies.

**What the average is hiding.** The law is about averages, and a queue's average hides both of the
states it is averaging over. A system with a handful of requests in flight on average can spend
most of its time empty and the rest badly backed up. The average describes neither.

**Anything about the tail.** It relates means. A residence time inferred this way is a mean, and
it says nothing about the slowest one request in a hundred, which is the number anybody cares
about during an incident.

## Key takeaways

:::{div}
:class: takeaways

- **Requests in the system equal the arrival rate times the time each one stays.** One
  multiplication, true of any system in a steady state, assuming nothing about how the system works.
- **What a request costs is not how long it takes.** Service demand is processor time per request,
  the first quantity in the model that belongs to the software rather than the workload. The
  difference between the two is queueing.
- **Run the law backwards to get the residence time your application's timer cannot see.** Divide
  the requests in flight by the arrival rate. The answer includes every queue a request sat in
  before your timer started, if the window balanced.
- **The fleet is an input, not a result.** The model recommends a fleet, a person decides one, and
  every ceiling from here on asks what happens to the fleet that was bought.
- **A utilisation above one is a fleet that cannot keep up.** The busy hour needs more cores than
  the fleet has, the queue grows, and nothing is steady. In those futures the count of requests
  in flight describes nothing, and this file cannot yet flag them.
- **The law relates three numbers and has no opinion about which one moved.** Outside a steady
  state, or about the tail, it says nothing at all.
:::

## Problems

Three, in `tests/littles_law/`. The first two have tests. The last does not, and says why.

**5.1 — The law.**
One multiplication, checked against the model's own node: the one [ch06](#queueing-and-the-knee)
adds, with the waiting in it, so that the check covers the time a request stays rather than the
time it is being served. Checked at the point estimate first, then across every future the
model drew.

```bash
python3 -m pytest tests/littles_law/test_problem_1_the_law.py -m problem
```

**5.2 — The law backwards.**
Infer residence time from in-flight requests and arrival rate, the two things every system
already exposes. Then decide what to return when nothing is arriving. That decision is a
judgement, not arithmetic.

```bash
python3 -m pytest tests/littles_law/test_problem_2_backwards.py -m problem
```

**5.3 — Your own steady state.** No test: the measurement is of your queue, and nothing here can
see it.

Pick a queue you run: a request tier, a job pipeline, anything with work arriving and leaving.
Over one window, measure two of the three quantities: how fast work arrives, how much is in
flight, how long a unit stays. Infer the third, then measure the third as well, and say where
your timer starts. Also record the in-flight count at the start and at the end of the window.
That is the test from "The law" for whether the window was steady.

If the inferred and measured values disagree, you have not found an error in the law. Decide
which of two gaps you have: queueing your timer cannot see, or a window in which arrivals and
departures did not balance. The start and end counts decide it. A count that ended well away from
where it started, next to the number that arrived, means the window did not balance. A count that
ended close to its start means the window balanced, and the gap is queueing your timer cannot
see.

A good answer states: the window; the three values; the in-flight count at the start and the end;
the gap between inferred and measured; which of the two causes it is, and the evidence. What would
falsify the answer: a gap blamed on unseen queueing when the in-flight count ended well away from
where it started; or a window called steady that contained a pile-up, with the count climbing
through it. Agreement is a result, not a warning sign: if the window balanced and the two agree,
your timer sees the whole of the residence time.

## Where to go next

Little's original proof @little1961proof is five pages, and worth reading for how little it
assumes.

[ch06](#queueing-and-the-knee) buys a mechanism, and pays for it in assumptions: one queue and one
class of work, requests that do not affect each other, and a service time that does not change
with load. It explains why residence time climbs steeply as utilisation nears one: the service
time divided by the share of the fleet that is idle. It adds the model's first ceiling, on
utilisation, with a declared margin below it, so the model can say how close to one is too close
and report the futures past it.
