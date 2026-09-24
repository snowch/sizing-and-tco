---
title: "Peak, mean and growth"
short_title: "ch04 Peak, mean and growth"
---

(peak-mean-and-growth)=
# ch04 · Peak, mean and growth

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

Which number in a demand curve sizes you, and what is a five-year growth rate a claim about?

[ch02](#what-a-workload-is) established that a workload is a set of quantities. Each of them
varies over time, and that chapter collapsed every one into a single number without saying which
moment it had picked. This chapter is about which collapse is the right one.

## The material

### The mean is the one number nobody experiences

Demand has a shape. It is low overnight, high in the afternoon, and different again on a Tuesday
in November. Sizing for the average means sizing for a level that demand passes through twice a
day.

The number that sizes you is the busy hour. Or the busy minute, or the busy Tuesday, depending on
how long your system takes to fail and how long your users will wait for it to recover. Which of
those to use is yours to decide, from your traffic and your tolerance, and the model cannot make
the choice for you.

The arithmetic is trivial: the busiest hour's share of the day, times the day's total. Problem
4.1 is that arithmetic. The peak-to-mean ratio behind it is not trivial. It is a measured
quantity, it varies by workload, and quoting somebody else's is how a system gets sized for a
shape it does not have.

This chapter puts that ratio into the model as an input with a shape rather than a figure,
because nobody has measured it on this service, and the file says so. It then derives the mean
rate from the busy hour:

```{literalinclude} ../models/web_service/stages/07-uncertainty/model.yaml
:language: yaml
:start-at: peak_to_mean:
:end-before: outputs:
```

The busy hour sizes the fleet. The mean is what the fleet spends most of its life serving, and it
is the denominator of every cost per request in [ch17](#unit-economics). That is why the model
carries both.

### Growth is a bet, and the bet compounds

Growth moves the answer more than any other input in this book.

The chart below is the first of many like it, so here is how it is made. Take one input. Hold
every other input still, swing that one from the low end of its range to the high end, and record
how far the answer moves. That distance is its **swing**. Do it for every input and sort the bars
longest first. They make a funnel, which is where the name **tornado** comes from. The two columns
in the table are the ends of each swing: low enough that only about one future in ten comes in
under, and high enough that only about one in ten comes in over.

```{image} _figures/peak-mean-and-growth-chart.svg
:alt: Which input moves the recommended host count most, when swung across its middle 80%
:width: 100%
```

```{include} _generated/peak-mean-and-growth-tornado.md
```

The growth rate is at the top, and nothing else is close. It is at the top of every tornado in this
book whose answer depends on the future. Not every answer does: the cost of a fleet somebody has
already bought is a question about prices, and [ch15](#capex-opex-and-lifecycle) is where that
difference is drawn. But wherever the future enters the arithmetic, growth is at the top of it. That is
not a quirk of these numbers. A growth rate is the one input that is *raised to a power*; everything
else is multiplied. Over a five-year horizon, the exponent turns an uncertainty in the rate into a
much larger uncertainty in the demand.

```{image} _figures/peak-mean-and-growth-demand.svg
:alt: The busy-hour request rate at the horizon, as a distribution
:width: 100%
```

That is what a five-year demand forecast looks like when its growth assumption is stated
honestly: the busy hour the fleet will have to serve, as a band. The point estimate is somewhere
in the middle of it.

The graph has gained two nodes since [ch03](#where-the-numbers-come-from): the peak-to-mean ratio,
and the mean it implies. Three inputs have gained a shape. Click *annual growth factor* and the
band that produced the figure above is written there. Drag its slider and the point moves while
the band stays. That is the difference this chapter is about.

```{iframe} /models/web_service_uncertainty-reference.html
:width: 100%
The same graph, with the growth rate as a band rather than a figure. Clicking it shows the band.
```

Click *records held, day one* and there is no band. That is a claim rather than an omission: you
can go and count how much data you hold, and nobody can count next quarter's busy hour. The rate
has a shape because a peak is something somebody has to catch. The level does not, because it is
a number a storage system will tell you. The file says as much, in a line beside the value.

Giving every input a band is not the more honest choice. It is the less honest one, if a figure
among them is something you could have gone and checked.

### Compounding an average is not averaging the compounds

There is a specific and expensive error here. Work through it once by hand.

You have a range of plausible growth rates. You want the capacity in five years. There are two
things you could compute:

- take the **average growth rate**, and compound it; or
- compound **every** growth rate, and average the results.

They are not the same number, and the second is always larger, for any spread at all. Suppose
growth might double the traffic every year or might halve it, each as likely as the other. The
average of those two is no growth, so compounding it leaves you where you started. Compound each
and average the results: over five years doubling gives thirty-two times, halving gives a
thirty-second, and the average is over sixteen times.

Compounding curves upwards, so the high rates run away faster than the low ones fall. Averaging
first flattens the curve and throws that away. The gap widens with the spread and with the
horizon, which makes it largest over exactly the five-year plan a fleet gets bought against.

Problem 4.2 is that comparison. Write down which way you think it goes before you run it.

The practical consequence: a capacity plan built by compounding a single "expected" growth rate
understates the expected capacity. Not a pessimistic case: the *expected* one. The plan is
optimistic before any of its other assumptions have been questioned.

### What a growth rate is a claim about

Nothing in [ch03](#where-the-numbers-come-from) helps here.

A compression ratio can be measured. A price can be quoted. A growth rate is a claim about the
future, and no amount of provenance discipline turns one into a measurement. The best available
version is: the last three years, extrapolated, with a band wide enough to admit that the next
three might not resemble them. The width of that band is a judgement nobody can check.

So this book gives growth a lognormal shape: growth compounds, and the multiplier it compounds
cannot be zero or less. The ends of the band are stated as a sentence somebody could disagree
with: *surprised below this, surprised above that*. That is the most honest form available,
because a sentence can be argued with and a bare number cannot. It is not a measurement, and the
model does not pretend otherwise.

### Three ways a demand curve is described badly

**A single peak.** "We do forty thousand requests a second at peak" is a rate with no duration
attached. Forty thousand for ten seconds and forty thousand for four hours size differently. One
of them is absorbed by a queue; the other is a queue.

**The wrong thing, measured well.** Take a year of per-minute rates and find the level that one
minute in twenty is above. That is not the busy hour. Whether those minutes are scattered
evenly through the year or bunched into a few afternoons decides whether sizing to it is right or
badly wrong.

**A growth rate with no horizon.** A growth rate is not an input until somebody says for how
long. Over one year it is a rounding error against the other uncertainties. Over five it is the
model.

## What this cannot tell you

**What your peak-to-mean ratio is.** Nothing in this repository can measure it. It is a property
of your traffic, and it belongs to the `estate` target ([ch03](#where-the-numbers-come-from)).
Everything above tells you what to do with one once you have it.

**Whether growth will continue.** The model extrapolates. Extrapolation is the assumption that the
mechanism producing the last three years is still running. The one thing a capacity model cannot
see is the quarter it stops: a product retired, a customer lost, a competitor won.

**Whether the band's width is honest.** A growth rate stated as *surprised below here, surprised
above there* is a claim about somebody's surprise, and nobody goes back afterwards to count how
often they were surprised. Nothing here calibrates that.

**Anything about a shape that changes.** Every figure above assumes demand grows without changing
its daily profile. A workload that grows by adding a different kind of user grows in a different
shape, and the busy hour moves.

## Key takeaways

:::{div}
:class: takeaways

- **The busy hour sizes you. The mean is what you serve most of the time.** The mean is the one
  number nobody experiences, and the model carries both because each has a job.
- **The peak-to-mean ratio is a measurement, not a constant.** It belongs to your traffic, and
  borrowing somebody else's sizes a system for a shape it does not have.
- **Growth is the one input raised to a power, so it tops every tornado that depends on the
  future.** Over a horizon, an uncertainty in the rate becomes a much larger uncertainty in the
  demand.
- **Compounding the average growth rate understates the expected capacity.** Compound every
  plausible rate and average the results, and the answer is always larger. The gap grows with the
  spread and with the horizon.
- **A growth rate is a claim about the future, and no provenance turns it into a measurement.** The
  honest form is a band stated as *surprised below this, surprised above that*, with a horizon
  attached.
:::

## Problems

Three, in `tests/peak_mean_and_growth/`. The first two have tests. The third does not, and says why.

**4.1 — The busy hour.**
Given a day's shape as relative weights and a daily total, return the rate during the busiest
hour. The weights do not sum to anything in particular, which is most of the problem.

```bash
python3 -m pytest tests/peak_mean_and_growth/test_problem_1_busy_hour.py -m problem
```

**4.2 — Compound the average, or average the compounds?**
Compute both, and find out which is larger and by how much. Predict the direction before you run
it. The gap widens with the spread and with the horizon, so it is worst when the plan matters
most.

```bash
python3 -m pytest tests/peak_mean_and_growth/test_problem_2_growth_gap.py -m problem
```

**4.3 — What is your growth rate a claim about?** No test. This chapter has already said that
nobody can check the width of a growth band, and writing a test for it would contradict that on
the same page.

Find the growth rate somebody is currently using to plan the system you work on. Then answer
three questions about it. What is it extrapolating: users, requests, retained data, or revenue
that somebody has converted into one of those? Over what period was it measured, and is that
period long enough to contain the thing that would break it? And what would have to happen for it
to be wrong by half, in either direction?

Now write the two ends as a sentence: *I would be surprised if it came in under this, and
surprised if it came in over that.* Say it out loud to whoever owns the plan. The sentence is the
deliverable, not the number. A range you are willing to be quoted on is worth more than a point
estimate nobody will defend.

A good answer names the mechanism, not just the trend, and its band is wide enough to be
uncomfortable. If the band is narrow and comfortable, you have described the last three years
rather than the next three.

## Where to go next

[ch05](#littles-law) begins Part II, and changes the subject from how much demand there is to what
happens to a system when it arrives.

[ch13](#monte-carlo) is where the band in this chapter's second figure comes from.
[ch19](#which-input-is-the-answer) is what to do about growth sitting at the top of the tornado.
