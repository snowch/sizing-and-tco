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

[ch05](#littles-law) related three quantities without assuming anything, and could therefore
explain nothing. This chapter buys a mechanism, and the price is a set of assumptions somebody can
argue with.

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

That single division is the whole chapter.

### Residence time against utilisation

```{image} _figures/queueing-and-the-knee-curve.svg
:alt: Residence time against utilisation, flat and then vertical
:width: 100%
```

Nearly flat while there is slack. Nearly vertical when there is not. **Nothing in the arithmetic
warns you which side you are on.** The system at the flat part and the system at the cliff run the
same software on the same machines serving the same requests. The only difference is a number
nobody was watching.

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
- *Headroom* is the margin somebody declared, and *allowed* is the limit less that margin.
- The *verdict* judges the point estimate alone: `ok` under the allowed line, **over** past the
  limit, and *into the margin* between the two, where the design is spending the reserve that was
  declared to protect it.
- The last two columns ignore the point estimate. Across everything the model thinks could
  happen, they give the share of futures past the allowed line and the share past the limit.

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

A capacity ceiling is a cliff you fall off. A full disk, which [ch09](#capacity) adds to this
model, is one: you find out immediately. A queueing ceiling is not a cliff. You slide down it,
paying in latency on every request, for as long as nobody looks. There is no page, no
alert, no failure. There is just a system that is worse than it was, in a way that shows up in
somebody else's dashboards.

The way back is worse, too. Coming back from a full disk means deleting something. Coming back
from a queue means shedding load or adding machines, and
[ch07](#when-adding-servers-stops-helping) is about how little the second one buys.

### What this model assumes, and what it costs

The formula above is the simplest useful queueing result, and it assumes a great deal:

- **one queue, one class of work.** Real systems have several, and a request usually visits more
  than one of them.
- **requests that do not care about each other.** No batching, no locking, no cache that one
  request warms for the next.
- **a service time that does not change with load.** This one is the big lie. On a real system,
  a busier machine is a slower machine per request: caches miss more, locks are held longer,
  collection runs while somebody is waiting. The model declares that arrival rate and service
  demand move together, which admits the effect without correcting for it.

Every one of those makes the real curve **steeper** than the drawn one. The picture above is the
optimistic case.

### The cap, and why it is declared

At a utilisation of one the formula divides by zero. Infinity is not a prediction, so the model
clamps, and says so in a node with a name and a stated reason. Beside it is the margin the ceiling
above audits against. It is declared once, so that the sizing and the audit cannot drift apart:

```{literalinclude} ../models/web_service/stages/09-queueing/model.yaml
:language: yaml
:start-at: utilisation_cap:
:end-before: effective_utilisation:
```

Past that point the formula has stopped describing a queue and started describing an arithmetic
accident. The clamp does not hide that. The ceiling watches the real utilisation rather than the
capped one, so a future out there is still reported **over**. The model does not know what happens
past the cap, and says so rather than extrapolating.

```{iframe} /playground/queueing-and-the-knee/
:width: 100%
The same file, running. Raise the request rate until utilisation passes the cap and run it again:
the residence time stops rising, while the ceiling goes on reporting the real utilisation.
```

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

**Whether the service time is constant.** It is not, the model says it is, and the declared link
between arrival rate and service demand admits that without correcting for it. The real curve is
steeper, and this chapter cannot say by how much.

## Key takeaways

:::{div}
:class: takeaways

- **Response time is the work divided by what is left of the system.** Nearly flat while there is
  slack, nearly vertical when there is not, and nothing in the arithmetic warns you which side you
  are on.
- **There is no knee.** The curve has no special point. What people call the knee is where the slope
  first exceeded what they would put up with, which is a fact about the person.
- **So the book declares a margin with a reason instead of a knee rule.** A ceiling records where
  the quantity stops meaning anything, how much room is kept below that, and why.
- **The verdict judges one future. The last two columns judge them all.** A design can read *ok* at
  the point estimate and still be over the limit in a good share of its futures.
- **A queueing ceiling is a slope, not a cliff.** Nothing fails and nobody is paged. The system gets
  slower for as long as nobody looks, and the way back is adding machines, which buys less than it
  promises.
:::

## Problems

Three, in `tests/queueing_and_the_knee/`. The first two have tests. The last does not, and says
why.

**6.1 — The formula.**
Write the division. Work out what you are dividing by before you look it up, then decide what to
return at a utilisation of one. An infinity is defensible, and so is raising an error. A large
finite number is not, because somebody will put it in a slide.

```bash
python3 -m pytest tests/queueing_and_the_knee/test_problem_1_residence.py -m problem
```

**6.2 — Where is the knee?**
Invert the formula and find the utilisation at which requests take a given multiple of their idle
time. Then compare what comes out for a tolerant engineer and a strict one. The gap between their
two answers is a decision, not a discovery.

```bash
python3 -m pytest tests/queueing_and_the_knee/test_problem_2_knee.py -m problem
```

**6.3 — Where your own knee is.** No test: the curve is your system's, and this repository has no
access to it.

The chapter says there is no knee, only a tolerance, so start with yours: how many times its idle
latency may a request take before you would act? Write the multiple down before you look at any
data. Then plot response time against utilisation for one device or one tier, as a scatter of
the last few weeks rather than an average, and read off the utilisation at which the scatter
crosses your multiple. That is your knee, and it is yours rather than the system's.

Then answer the question the chart cannot: what utilisation does your system run at, and who
chose it? In most places the answer is that nobody chose it. It is wherever the last capacity
argument left off.

A good answer is the multiple, the utilisation the scatter crosses it at, and the name of whoever
chose the utilisation you run at. If the scatter never crosses, there are two possibilities.
Either you are nowhere near your tolerance, which is worth knowing and probably worth money, or
your utilisation metric is averaged over a window long enough to hide every peak. The second is
the commoner.

## Where to go next

[ch07](#when-adding-servers-stops-helping) takes the obvious response to everything above, adding
machines, and works out what it buys.

[ch11](#headroom-and-failure-domains) chooses the margin this chapter refused to choose, and shows
what happens when two of them end up multiplied together.
