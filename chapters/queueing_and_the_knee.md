---
title: "Queueing, and the knee"
short_title: "ch06 Queueing, and the knee"
---

(queueing-and-the-knee)=
# ch06 · Queueing, and the knee

:::{note} Chapter header
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch05](#littles-law) |
| **What it produces** | The utilisation curve, swept out of the model rather than asserted |
| **Built from** | `queueing-curve`, `service_tier-reference` |
:::

## The question

Why does response time climb long before a device is busy, and what does headroom actually buy?

[ch05](#littles-law) related three quantities without assuming anything, and could therefore
explain nothing. This chapter buys a mechanism, and the price is a set of assumptions somebody can
argue with.

## The material

### One division

A request costs some amount of work. The system is busy some fraction of the time. So the fraction
of the system available to do your work is what is left over — and the time your work takes is the
work divided by that.

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: residence_time:
:end-before: waiting_time:
```

That single division is the whole chapter. Everything below is what it looks like.

### What it looks like

```{image} _figures/queueing-and-the-knee-curve.svg
:alt: Residence time against utilisation, flat and then vertical
:width: 100%
```

Nearly flat while there is slack. Nearly vertical when there is not. And — the part worth sitting
with — **nothing in the arithmetic warns you which side you are on**. The system at the flat part
and the system at the cliff are running the same software on the same machines serving the same
requests. The only difference is a number that was not being watched.

```{include} _generated/queueing-and-the-knee-table.md
```

Read down the last column. For most of the range, "busier" costs almost nothing. Then, over the
last stretch, it costs everything. A system that has been comfortable for two years at a load
that has been creeping up all the while does not degrade gradually; it degrades all at once, on
the Tuesday that load crosses a threshold nobody had computed.

### There is no knee

The word is in this chapter's title and the chapter is going to take it away.

Look at the curve again. It is smooth. It has no corner, no inflection, no special point. It is
the same shape at every scale, and if you plot any portion of it stretched to fill the axes you
get the same picture back. There is nothing in it to find.

What people point at when they say "the knee" is the place where the slope first exceeded what
they were willing to put up with. That is a statement about the person, not about the queue.
Problem 6.2 makes it concrete: invert the formula, ask where requests take twice as long, then ask
where they take ten times as long, and watch the answer move across most of the useful range of a
system.

Two engineers with different tolerances will size the same system very differently and both will
say they sized it to the knee.

So this book does not have a knee rule. It has a **declared margin, with a reason attached**:

```{include} _generated/queueing-and-the-knee-ceilings.md
```

A margin is a decision, it belongs to somebody, and the `because` column is where they say what
they were protecting. [ch11](#headroom-and-failure-domains) is about making that decision
deliberately instead of inheriting it.

### Why the margin is so large

Two ceilings in that table have wide margins and one is wider still. The reason is worth stating,
because a percentage looks like a percentage.

A capacity ceiling is a cliff you fall off: the disk is full, and you find out immediately. A
queueing ceiling is not. You do not fall off it; you slide down it, paying in latency, on every
single request, for as long as nobody looks. There is no page, no alert, no failure — just a
system that is worse than it was in a way that shows up in somebody else's dashboards.

And the cost of crossing it is not symmetric. Coming back from a full disk means deleting
something. Coming back from a queue means reducing load or adding machines, and
[ch07](#when-adding-servers-stops-helping) is about how badly the second of those works.

### What this model assumes, and what it costs

The formula above is the simplest useful queueing result and it assumes a great deal:

- **one queue, one class of work.** Real systems have several, and a request usually visits more
  than one of them.
- **requests that do not care about each other.** No batching, no locking, no cache that one
  request warms for the next.
- **a service time that does not change with load.** This one is the big lie. On a real system,
  a busier machine is a slower machine per request — caches miss more, locks are held longer,
  collection runs while somebody is waiting. The model's declared correlation between arrival rate
  and service demand is an attempt to admit that, and it is an admission rather than a fix.

Every one of those makes the real curve **steeper** than the drawn one. The picture above is the
optimistic case.

### The cap, and why it is declared

At a utilisation of one the formula divides by zero. Infinity is not a prediction, so the model
clamps — and says so, in a node with a name and a stated reason:

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: utilisation_cap:
:end-before: effective_utilisation:
```

Past that point the formula has stopped describing a queue and started describing an arithmetic
accident. The ceiling still reports that the design is over, which is the honest output: the model
does not know what happens there, and it says the design should not go there.

## What the model says

```{include} _generated/queueing-and-the-knee-table.md
```

```{include} _generated/queueing-and-the-knee-ceilings.md
```

## What this cannot tell you

**What your system's curve looks like.** Everything above is one queueing model with strong
assumptions, swept across one input. A real system is several queues in series with feedback
between them, and the only honest way to get its curve is to measure it — which needs the
reference machine, and is the `rig` target nobody has taken.

**Anything about the tail.** This chapter computes mean residence time. During an incident the
number anybody cares about is the 99th percentile, and the ratio between the two grows as
utilisation does — so the tail is worse than this curve, by a factor this curve cannot report.

**When the load will cross the line.** The model says what happens at a utilisation. It says
nothing about when yours will get there, which is [ch04](#peak-mean-and-growth)'s question and is
answered by a growth rate nobody can measure.

**Whether the service time is constant.** It is not, the model says it is, and the correlation
declared between arrival rate and service demand is an admission rather than a correction. The
real curve is steeper and this chapter cannot say by how much.

## Problems

Two, in `tests/queueing_and_the_knee/`.

**6.1 — The formula.**
Write the division. Work out what you are dividing by before you look it up, then decide what to
return at a utilisation of one — an infinity is defensible and so is raising, but a large finite
number is not, because somebody will put it in a slide.

```bash
python3 -m pytest tests/queueing_and_the_knee/test_problem_1_residence.py
```

**6.2 — Where is the knee?**
Invert the formula and find the utilisation at which requests take a given multiple of their idle
time. Then read what comes out for a few different multiples, and watch the answer move across
most of the useful range of a system. That gap is a decision, not a discovery.

```bash
python3 -m pytest tests/queueing_and_the_knee/test_problem_2_knee.py
```

## Where to go next

[ch07](#when-adding-servers-stops-helping) is the obvious response to everything above — add
machines — and is about why it works considerably less well than the arithmetic suggests.

[ch11](#headroom-and-failure-domains) is where the margin this chapter refused to choose gets
chosen, deliberately and with a reason written down.
