---
title: "Queueing, and the knee"
short_title: "ch06 Queueing, and the knee"
---

(queueing-and-the-knee)=
# ch06 · Queueing, and the knee

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

Why does response time climb long before a device is busy, and what does headroom buy?

[ch05](#littles-law) related three numbers: requests in the system, the rate they arrive, and how
long each one stays. It holds under one condition, a steady state, and assumes nothing about how
the system works, so it cannot say why the time a request spends in the system grows as the system
gets busier. This chapter buys a mechanism, and the price is a set of assumptions you can argue
with, set out under *What this model assumes, and what it costs*.

## The material

### One division

A request costs some amount of work. The system is already busy some fraction of the time, so only
what is left over is available to do that work. The time it takes is the work divided by what is
left.

```{literalinclude} ../models/web_service/stages/09-queueing/model.yaml
:language: yaml
:start-at: residence_time:
:end-before: waiting_time:
```

The denominator, `1 - effective_utilisation`, is the share of time the system is not busy.
`effective_utilisation` is the utilisation capped just below one, and why it is capped is explained
further down, under *The cap, and why it is declared*.

### Residence time against utilisation

```{image} _figures/queueing-and-the-knee-curve.svg
:alt: Residence time against utilisation, flat and then vertical
:width: 100%
```

The curve rises slowly while much of the fleet is idle and steeply when little of it is. **Nothing
in the arithmetic warns you which side you are on.** Each row shows the same fleet, software and
machines, but more requests: the arrival rate alone changes. Utilisation is the sole variable that
differs. The dashed line marks the ceiling's allowed utilisation (full utilisation less your
queueing margin), shown in the ceilings table below as *Allowed*.

```{include} _generated/queueing-and-the-knee-table.md
```

Read down the last column. For most of the range, "busier" costs almost nothing. Then, over the
last stretch, it costs everything. A system that has been comfortable for two years, at a load
creeping up the whole time, does not degrade gradually. It degrades all at once, on the Tuesday
the load crosses a threshold nobody had computed.

### There is no knee

The word is in this chapter's title, and there is no such point on the curve.

Look at the curve again. It is smooth. It has no corner, no inflection, no special point. It is
the same shape at every scale, and if you plot any portion of it stretched to fill the axes you
get the same picture back. There is nothing in it to find.

What people point at when they say "the knee" is the place where the slope first exceeded what
they were willing to put up with. That is a statement about the person, not about the queue.
Problem 6.2 measures how much that person matters. Invert the formula, ask where requests take
twice as long, then ask where they take ten times as long, and watch the answer travel across
most of the useful range of a system.

Two engineers with different tolerances will size the same system differently, and both will say
they sized it to the knee.

So this book does not have a knee rule. It has a **declared margin, with a reason attached**:

```{include} _generated/queueing-and-the-knee-ceilings.md
```

This is the first ceilings table in the book, and every later chapter prints one, so read the
columns once.

- *At the plan* is where the design sits at the point estimate.
- *Limit* is where the quantity stops meaning anything: a full disk, a saturated device.
- *Headroom* is the margin you declared, and *Allowed* is the limit less that margin.
- The *verdict* judges the point estimate alone: `ok` under the allowed line, **over** past the
  limit, and *into the margin* between the two, where the design is spending the reserve that was
  declared to protect it.
- *Over allowed* and *Over limit* ignore the point estimate. Across everything the model thinks
  could happen, they give the share of futures past the allowed line and the share past the limit.

A design can read `ok` and still be over the limit in a good share of its futures, and the table
above is one. [ch12](#the-sizing-model) is where that becomes a decision.

A margin is a decision, and it belongs to somebody. A ceiling's `because` field is where they say
what they were protecting. The toolkit refuses a ceiling that leaves it empty.
[ch11](#headroom-and-failure-domains) is where that decision gets made deliberately instead of
inherited.

All of it is in the graph now: the division, the clamp and the ceiling. Drag *hosts in the
fleet* down and watch the verdict change before the number under it looks alarming.

```{iframe} /models/web_service_queueing-reference.html
:width: 100%
The graph as ch06 leaves it, with the first ceiling in it. Click *utilisation at the busy hour* for
its margin and its reason.
```

### Why the margin is so large

The margin in that table is wide, and a percentage on its own says nothing about what it is
protecting against.

A capacity ceiling fails at once. A full disk, which [ch09](#capacity) adds to this model, is one:
writes stop and you find out immediately. A queueing ceiling is different: crossing it fires no
alarm, nothing fails, and no one is paged. Instead, every request takes longer, and the curve above
shows that each new load step costs more than the last. The cost is pure latency — slower
responses, not errors — paid until someone looks at latency against utilisation.

The way back is worse, too. Coming back from a full disk means deleting something. Coming back
from a queue means shedding load or adding machines, and
[ch07](#when-adding-servers-stops-helping) is about how little the second one buys.

### What this model assumes, and what it costs

The formula above @kleinrock1975queueing is the standard result for the mean time in the system,
for one server and one queue with random independent requests. It assumes a great deal:

- **One server.** The model applies the formula to the whole fleet: utilisation is busy cores over
  all the fleet's cores. Many servers sharing one queue wait less than one server at the same
  utilisation, so the drawn curve overstates the wait at moderate load. **Flatter.**
- **One queue, one class of work.** Real systems have several queues, and a request usually visits
  more than one. Which way that moves the curve depends on the system. **Either.**
- **Requests that arrive at random.** Traffic that arrives in bursts waits longer than random
  traffic at the same utilisation. **Steeper.**
- **Requests that do not affect each other.** Locking between requests makes a busy system slower
  (**steeper**). Batching, and a cache that one request warms for the next, make a busy system do
  less work per request (**flatter**).
- **A service time that does not change with load.** The curve holds it fixed: only the request
  rate moves. On a real system a busier machine is often slower per request: caches miss more,
  locks are held longer, garbage collection runs while requests wait. Nothing in the model makes a
  request slower as load rises. **Steeper.**

The assumptions push in both directions, so the drawn curve is not a bound on your system's curve.
The way to get yours is to measure it; problem 6.3 asks you to.

### The cap, and why it is declared

At a utilisation of one the formula divides by zero. The model caps utilisation in a named input
you declare — `utilisation_cap`, which carries its reason in its note. Beside it is
`queueing_margin`, the margin the ceiling checks against:

```{literalinclude} ../models/web_service/stages/09-queueing/model.yaml
:language: yaml
:start-at: utilisation_cap:
:end-before: effective_utilisation:
```

The cap does not hide a future past it: the ceiling watches the real utilisation, not the capped
one, so a future past the cap is still reported **over**. Past the cap, residence time stops
rising. The model does not say what happens there and does not extrapolate. The cap is safe only
because the ceiling sits beside it — a cap alone would turn an overloaded system into an
ordinary-looking number.

## What this cannot tell you

**What your system's curve looks like.** Everything above is one queueing model with strong
assumptions, swept across one input. A real system is several queues in series with feedback
between them, and the only honest way to get its curve is to measure it. That needs the reference
machine, and it is a `rig` measurement nobody has taken.

**Anything about the tail.** This chapter computes mean residence time. The slowest one request
in a hundred is worse, and the gap between the two widens as utilisation rises, by a factor this curve cannot
report.

**When the load will cross the line.** The model says what happens at a given utilisation, not
when yours will get there. That is [ch04](#peak-mean-and-growth)'s question, and its answer rests
on a growth rate nobody can measure.

**How much a fleet's many cores help.** The formula is the one-server result, applied to a whole
fleet of cores. Many servers sharing work wait less than one server at the same utilisation, so at
moderate load this curve overstates the wait for a fleet. This chapter does not compute by how
much.

**How much slower a busy request is.** The curve holds the service time fixed. On a real system it
rises with load. Nothing in this model makes a request slower as load rises, so for that reason
alone the real curve is steeper, by an amount this chapter cannot say.

## Key takeaways

:::{div}
:class: takeaways

- **Response time is the work divided by what is left of the system.** Nearly flat while there is
  slack, nearly vertical when there is not, and nothing in the arithmetic warns you which side you
  are on.
- **There is no knee.** The curve has no special point. The bend you see in a drawing of it sits
  wherever the axis stops. What people call the knee is where the slope first exceeded what they
  would put up with, which is a fact about the person.
- **So the book declares a margin with a reason instead of a knee rule.** A ceiling records where
  the quantity stops meaning anything, how much room is kept below that, and why.
- **The verdict judges one future. The last two columns judge them all.** A design can read *ok* at
  the point estimate and still be over the limit in a good share of its futures.
- **Crossing a queueing ceiling fires no alarm.** Nothing fails and no one is paged. Every request
  gets slower, by more with each step of load. The way back is shedding load or adding machines.
- **The drawn curve is not a bound on yours.** It is the one-server result: a fleet of many cores
  sharing work waits less, while bursty traffic and requests that slow under load wait more.
:::

## Problems

Three, in `tests/queueing_and_the_knee/`. The first two have tests. The last does not, and says
why.

**6.1 — The formula.**
The formula is in the first YAML: write it as a function. Decide what it returns at utilisation one
and above — the division gives infinity at one and a negative number past it, neither acceptable.
An infinity is defensible, as is an error; a large finite number is not, because somebody will put
it in a slide. The model caps because its ceiling watches the uncapped value; your function has
nothing beside it, so you must not cap. The utilisation may be a single number or a numpy array;
return one answer per value.

```bash
python3 -m pytest tests/queueing_and_the_knee/test_problem_1_residence.py -m problem
```

**6.2 — Where is the knee?**
Invert the formula from problem 6.1: given a tolerance, return the utilisation at which a request
takes that many times as long as it would on an idle system. The tolerance multiplies the whole
time in the system, waiting included. The queueing table above has a row for some tolerances; the
function must answer for any, including ones the table has no row for. Then compare a strict
engineer's answer (twice the idle time) and a tolerant one's (ten times): the gap between their
answers is a decision, not a discovery.

```bash
python3 -m pytest tests/queueing_and_the_knee/test_problem_2_knee.py -m problem
```

**6.3 — Where your own knee is.** No test: the curve is your system's, and this repository has no
access to it.

The chapter says there is no knee, only a tolerance, so start with yours: how many times its idle
latency may a request take before you would act? Write the multiple down before you look at any
data. Idle latency comes from the same scatter you will plot: the response time at the lowest
utilisations it shows, the floor of the scatter at its left-hand end. If the scatter has no quiet
periods, it has no floor and you have no idle latency from it — note that in your answer. Then plot
response time against utilisation for one device or tier, drawing a scatter of the last few weeks
rather than an average. Read off the utilisation at which the scatter crosses your multiple. That
is your knee, and it is yours rather than the system's.

Then answer the question the chart cannot: what utilisation does your system run at, and who chose
it? In most places the answer is that nobody chose it. It is wherever the last capacity argument
left off.

The scatter is an `estate` observation of a running system ([ch03](#where-the-numbers-come-from)).
Nobody else can repeat it, so your answer must record which system, over what window, and when. A
good answer contains the multiple, the idle latency and where it came from on the scatter, the
utilisation where the scatter crosses the multiple, who chose the utilisation you run at, and the
system, window and date. If the scatter never crosses, there are two possibilities. Either you are
nowhere near your tolerance (worth knowing and probably worth money), or your utilisation metric is
averaged over a window long enough to hide every peak. The second is the commoner.

## Where to go next

[ch07](#when-adding-servers-stops-helping) takes the obvious response to everything above, adding
machines, and works out what it buys.

[ch11](#headroom-and-failure-domains) chooses the margin this chapter refused to choose, and shows
what happens when two of them end up multiplied together.
