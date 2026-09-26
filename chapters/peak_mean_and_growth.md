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

[ch02](#what-a-workload-is) established that a workload is a set of quantities, each varying over
time. It reduced each to one number: for requests, the peak request rate in the busy hour on day
one. This raised two questions: how long a busy period must last to size you, and how the busy hour
relates to the daily mean. The growth rate was also reduced to one; this chapter replaces it with a
spread.

## The material

### The busy hour, and what the mean is for

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

The busy hour sizes the fleet. The mean, times how long the fleet runs, is the total requests
served, and that is what a cost per request divides by. [ch17](#unit-economics) shows that a cost
per request quoted against the busy hour comes out several times larger than one quoted against the
mean. So the model carries both.

### Growth is a bet, and the bet compounds

Growth moves the busy-hour rate at the horizon more than any other input.

This is the book's first tornado, so here is how to make one. Take one input and hold every other
still at its middle value. Swing that input from the low end of its band to the high end, and record
how far the answer moves. That distance is its **swing**. Do it for every input and sort the bars
longest first. They form a funnel, which is where **tornado** gets its name. A **future** is one of
many runs of the model's arithmetic, with every uncertain input set to one of its possible values,
picked at random. The table shows the busy-hour rate at the horizon with each input at its low
end—where only one future in ten falls below—and its high end, where only one in ten comes in above.
Inputs that do not feed the busy-hour rate, such as the peak-to-mean ratio, leave it unchanged.

```{image} _figures/peak-mean-and-growth-chart.svg
:alt: Which input moves the busy-hour rate at the horizon most
:width: 100%
```

```{include} _generated/peak-mean-and-growth-tornado.md
```

The growth rate is at the top of this tornado, well ahead of the day-one busy-hour rate. That is not
a quirk of these numbers. A growth rate is the one input that is *raised to a power*; everything
else is multiplied. Over a five-year horizon, the exponent turns an uncertainty in the rate into a
much larger uncertainty in the demand.

```{image} _figures/peak-mean-and-growth-demand.svg
:alt: The busy-hour request rate at the horizon, as a band
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

### Which inputs get a band

Click *records held, day one* in the graph: it keeps a single number and has no band, which is a
decision rather than an oversight. You can count how much data you hold today, and a storage system
reports it whenever you ask. The busy-hour rate is different: to know it, you must observe your
traffic over a period containing the busiest hour, and next quarter's busiest hour has not happened
yet—so it gets a band.

What is uncertain about the records is how fast they grow, and the growth factor carries that for
both the rate and the records. The file explains this reasoning in a note beside the value, and the
viewer shows it under Details. Giving every input a band is not more careful: a band on a countable
number records a doubt you could have removed, and hides that you did not count it.

### Compounding an average is not averaging the compounds

There is a specific and expensive error here. Work through it once by hand.

You have a range of plausible growth rates. You want the capacity in five years. There are two
things you could compute:

- take the **average growth rate**, and compound it; or
- compound **every** growth rate, and average the results.

The two are not the same number. Over horizons longer than one year, the second is larger for any
spread of growth rates. At one year they are equal, because compounding once is a single
multiplication and the average of multiplications is the multiplication by the average. Suppose
growth might double the traffic every year or might halve it, each equally likely. The two feel as
if they cancel, but the ordinary average, the one problem 4.2 uses, is their sum divided by two. A
doubling and a halving average to one and a quarter—growth of a quarter a year. Compound one and a
quarter over five years and the traffic roughly triples. Compound each case separately and then
average: over five years doubling gives thirty-two times, halving gives a thirty-second, and the
average is about sixteen times.

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

This book gives growth a band of the kind called **lognormal**. In plain words, a lognormal band is
lopsided: it runs further above its middle value than below it, and never reaches zero. It fits
growth because growth compounds, and the multiplier each year cannot be zero or less, though it can
be below one for a shrinking service. The file states the band by its two ends: the values where
only one future in ten falls beyond. Stated that way, the band is a sentence you can disagree with:
*surprised below this, surprised above that*. That form is the most useful because a sentence can be
argued with and a bare number cannot. It is not a measurement, and the model does not pretend
otherwise: the input's provenance is `assumption`.

### What a demand figure needs before you can size from it

**A single peak.** "We do forty thousand requests a second at peak" is a rate with no duration.
Forty thousand for ten seconds and forty thousand for four hours size you differently. A ten-second
burst can wait: requests hold briefly while the fleet works through them. A four-hour peak cannot be
deferred: the requests pile up for hours, so your fleet must handle that rate as it arrives.

**The wrong thing, measured well.** Take a year of per-minute rates and find the level that one
minute in twenty is above. That is not the busy hour. If those minutes scatter through the year,
each is a brief excursion and the fleet absorbs it; if they bunch into a few afternoons, those
afternoons spend hours above the level and your fleet is overloaded. Only when the minutes fall
decides whether it is safe to size to that level.

**A growth rate with no horizon.** A growth rate is not an input until you say for how long. Over
one year, it enters the arithmetic once: it multiplies the demand like any other input. Over five
years, it is raised to the power of the horizon, and it dominates the tornado shown earlier in this
chapter.

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

- **The busy hour sizes the fleet; the mean counts the requests.** The mean, times how long the
  fleet runs, is the requests it serves in total, and a cost per request divides by that. The mean
  is not a level the fleet sits at.
- **The peak-to-mean ratio is an observation of your own traffic.** It belongs to your users, so
  borrowing one from another workload sizes you for a daily profile you do not have. It is an
  input, not a measured constant, so the model remains definitional.
- **In this model, growth is the one input raised to a power, so it tops the tornado.** Over a
  horizon, an uncertainty in the rate becomes a much larger uncertainty in the demand.
- **Compounding the average growth rate understates the expected capacity.** Over any horizon
  longer than a year, compounding every plausible rate and averaging the results gives a larger
  answer. The gap grows with the spread and with the horizon.
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
