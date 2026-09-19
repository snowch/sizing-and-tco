---
title: "Peak, mean and growth"
short_title: "ch04 Peak, mean and growth"
---

(peak-mean-and-growth)=
# ch04 · Peak, mean and growth

## The question

Which number in a demand curve sizes you, and what is a five-year growth rate actually a claim
about?

[ch02](#what-a-workload-is) established that a workload is a set of quantities. Each of those
quantities is a *distribution over time* that somebody has collapsed into one number. This chapter
is about which collapse is the right one.

## The material

### The mean is the one number nobody experiences

Demand has a shape. It is low overnight, high in the afternoon, and different again on a Tuesday
in November. Sizing for the average means sizing for a level that occurs twice a day on the way
past.

The number that sizes you is the busy hour — or the busy minute, or the busy Tuesday, depending on
how long your system takes to fall over and how long anybody is willing to wait for it to recover.
Which of those you should use depends on your traffic and your tolerance, and somebody has to
decide it.

The arithmetic is trivial — the busiest hour's share of the day, times the day's total — and
problem 4.1 is that arithmetic. The peak-to-mean ratio behind it is not trivial. It is a measured
quantity, it varies by workload, and quoting somebody else's is how a system gets sized for a
shape it does not have.

### Growth is a bet, and the bet compounds

Growth does most of the damage in this book.

The chart below is the first of many like it, so here is how it is made. Take one input. Hold
every other input still, swing that one from the low end of its range to the high end, and record
how far the answer moves. That distance is its **swing**. Do it for every input, sort the bars
longest-first, and they make a funnel — which is where the name **tornado** comes from. The two
columns in the table are the ends of each swing: low enough that only about one future in ten
comes in under, high enough that only about one in ten comes in over.

```{image} _figures/peak-mean-and-growth-chart.svg
:alt: Which input moves the recommended node count most, when swung across its middle 80%
:width: 100%
```

```{include} _generated/peak-mean-and-growth-tornado.md
```

The growth rate is at the top, by a distance, and it is at the top of almost every tornado in this
book. That is not a quirk of these numbers. It is structural: a growth rate is the one input that
is *raised to a power*, and everything else is multiplied. Over a five-year horizon, the exponent
turns an uncertainty in the rate into a much larger uncertainty in the capacity.

```{image} _figures/peak-mean-and-growth-capacity.svg
:alt: Usable capacity at the horizon, as a distribution
:width: 100%
```

That is what a five-year capacity plan actually looks like when its growth assumption is stated
honestly. The point estimate is somewhere in the middle of it.

The graph has not gained a node since [ch03](#where-the-numbers-come-from); one node has gained a
shape. Click *annual growth factor* and the band that produced the figure above is written there.
Drag its slider and the point moves while the band stays, which is the difference this chapter is
about.

```{iframe} /models/storage_cluster_uncertainty-reference.html
:width: 100%
The same graph, with the growth rate as a band rather than a figure. Clicking it shows the band.
```

### Compounding an average is not averaging the compounds

There is a specific and expensive error here, and it is worth working through once by hand.

You have a range of plausible growth rates. You want the capacity in five years. Two things you
could compute:

- take the **average growth rate**, and compound it;
- compound **every** growth rate, and average the results.

They are not the same number, and the second is always larger — for any spread at all, because
compounding is convex. The gap widens with the spread of the growth rates and with the horizon, so
it is largest exactly when somebody reaches for a five-year plan.

Problem 4.2 is that comparison. Write down which way you think it goes before you run it.

The practical consequence: a capacity plan built by compounding a single "expected" growth rate
understates the expected capacity. Not the p95 capacity — the *expected* one. The plan is
optimistic before any of its other assumptions have been questioned.

### What a growth rate is a claim about

Nothing in [ch03](#where-the-numbers-come-from) helps here.

A compression ratio can be measured. A price can be quoted. A growth rate is a claim about the
future, and no amount of provenance discipline turns one into a measurement. The best available
version is "the last three years, extrapolated, with a distribution wide enough to admit that the
next three might not resemble them" — and the width of that distribution is a judgement nobody can
check.

So this book gives growth a lognormal: growth compounds, and the multiplier it compounds cannot
be zero or less. Its percentiles are stated as a sentence somebody could disagree with:
*surprised below this, surprised above that*. That is the most honest form available, and it is not a measurement — the
model does not pretend otherwise.

Here is that stage of the storage model, with two percentiles where a number used to be:

```{iframe} /playground/peak-mean-and-growth/
:width: 100%
The growth rate, as a claim rather than a figure. The value shown against it is not one anybody
typed — it is the middle of the band, and it is not the average of the two ends. Move either
percentile and watch which way the middle goes.
```

### Three ways a demand curve is described badly

**A single peak.** "We do forty thousand requests a second at peak" is a rate with no duration
attached. Forty thousand for ten seconds and forty thousand for four hours size differently,
because one of them is absorbed by a queue and the other is a queue.

**A percentile of the wrong thing.** The 95th percentile of per-minute rates across a year is not
the busy hour. It is the level one minute in twenty is above, and whether those minutes are
scattered evenly through the year or bunched into a few afternoons decides whether sizing to it is
right or badly wrong.

**A growth rate with no horizon.** A growth rate is not an input until somebody says for how
long. Over one year it is a rounding error against the other uncertainties; over five it is the
model.

## What this cannot tell you

**What your peak-to-mean ratio is.** Nothing in this repository can measure it — it is a property
of your traffic, and it belongs to the `estate` target ([ch03](#where-the-numbers-come-from)).
Everything above tells you what to do with one once you have it.

**Whether growth will continue.** The model extrapolates. Extrapolation is the assumption that the
mechanism producing the last three years is still running, and the one thing a capacity model
cannot see is the quarter it stops — a product retired, a customer lost, a competitor won.

**Whether the distribution's width is honest.** A growth rate stated as *surprised below here,
surprised above there* is a claim about somebody's surprise, and nobody goes back afterwards to
count how often they were actually surprised. Nothing here calibrates that.

**Anything about a shape that changes.** Every figure above assumes demand grows without changing
its daily profile. A workload that grows by adding a different kind of user grows in a different
shape, and the busy hour moves.

## Problems

Three, in `tests/peak_mean_and_growth/`. The first two have tests. The third does not, and says why.

**4.1 — The busy hour.**
Given a day's shape as relative weights and a daily total, return the rate during the busiest
hour. The weights do not sum to anything in particular, which is most of the problem.

```bash
python3 -m pytest tests/peak_mean_and_growth/test_problem_1_busy_hour.py
```

**4.2 — Compound the average, or average the compounds?**
Compute both, and find out which is larger and by how much. Predict the direction before you run
it. The gap widens with the spread and with the horizon, so it is worst when the plan matters
most.

```bash
python3 -m pytest tests/peak_mean_and_growth/test_problem_2_growth_gap.py
```

**4.3 — What is your growth rate a claim about?** No test. This chapter has already said that
nobody can check the width of a growth distribution, and writing a test for it would contradict
that on the same page.

Find the growth rate somebody is currently using to plan the system you work on. Then answer
three questions about it. What is it extrapolating — users, requests, retained data, or revenue
that somebody has converted into one of those? Over what period was it measured, and is that
period long enough to contain the thing that would break it? And what would have to happen for it
to be wrong by half in either direction?

Now write the two percentiles as a sentence: *I would be surprised if it came in under this, and
surprised if it came in over that.* Say it out loud to whoever owns the plan. The sentence is the
deliverable, not the number — a range you are willing to be quoted on is worth more than a point
estimate nobody will defend.

A good answer names the mechanism, not just the trend, and its band is wide enough to be
uncomfortable. If the band is narrow and comfortable, you have described the last three years
rather than the next three.

## Where to go next

[ch05](#littles-law) begins Part II, and changes the subject from how much demand there is to what
happens to a system when it arrives.

[ch13](#monte-carlo) is where the distribution in this chapter's second figure comes from, and
[ch19](#which-input-is-the-answer) is what to do about growth sitting at the top of the tornado.
