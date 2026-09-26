---
title: "Monte Carlo"
short_title: "ch13 Monte Carlo"
---

(monte-carlo)=
# ch13 · Monte Carlo

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

The sizing model has produced a host count. How sure are we?

[ch12](#the-sizing-model) took a stated workload, multiplied along three chains, took the largest
of the three answers, and produced a number. Every step was arithmetic you could check by hand. The
number is correct. Whether it is *right* is a different question. Every input to that chain was
itself uncertain, and the chain has no way to say so.

This chapter builds the machinery for asking the second question. It assumes you can read code
and do arithmetic. It assumes nothing about statistics.

## The material

### A single number is a bet you did not know you placed

The table below is the book's finished web service model: [ch12](#the-sizing-model)'s host count,
with the costs later chapters add to it.

```{include} _generated/monte-carlo-outputs.md
```

The *Point estimate* column shows what you get when you work the model out once, with every input at
the middle of its declared range. The *90% interval* column shows what happens when you work the
model out many times, letting each input be as uncertain as the person who wrote it down is. This
column holds the middle nine answers in ten.

Look at the host count row. The point estimate is a correctly computed number. Its range stretches
wide: the top is many times the bottom, and the point estimate sits nearer the bottom than the
middle. Nothing went wrong. The calculation had no way to say that its inputs were uncertain, so it
did not say it.

The finished model draws more uncertain inputs than ch12's, from the same seed. So each input
receives different random values, and the host range can differ from ch12's in its last digit.

```{image} _figures/monte-carlo-hosts-distribution.svg
:alt: The recommended host count as a distribution, with the point estimate marked
:width: 100%
```

The chart shows the host count's answers as bars. Each bar counts how many answers landed in that
stretch of host counts. The solid red line marked *point* is the point estimate. The dashed lines
marked *p5* and *p95* are the two ends of the range. The heading says how many times the model was
worked out. The *median* in the subtitle is the middle answer, with half the answers below it. The
words *sample*, *interval* and the *p* in *p5* are defined in the sections below, where the method
needs them.

The rest of the chapter is how the *90% interval* column was produced.

### Instead of one value, a bag of values

If you do not know what the growth rate will be, do not give the model one growth rate. Give it a
bag of plausible growth rates and work the model out once for every value. You get a bag of answers,
and that bag is the answer.

When several inputs are uncertain, each has its own bag. Each time through the model, you draw one
value from every bag, with each input drawn separately from the others. If two inputs were drawn
together, they would rise and fall together. That is a different claim about the world from two
inputs that vary on their own.

That is Monte Carlo. Everything else is bookkeeping: how to fill each bag and how to read the bag of
answers.

Two words: the bag of plausible values for an input is its **distribution**, and one value drawn
from the bag is a **sample**. The bag of answers is the output's distribution. Two more words arrive
later in this chapter, each where the method needs them.

### Where the bag comes from

Filling a bag takes two lines of code, and the same two lines work for every shape.

Every shape can be described by one function that answers one question: given a fraction between
zero and one, what value is that fraction of the bag below? Give it one half and it returns the
middle value. Give it nine tenths and it returns the value nine tenths of the bag is below.

The value it returns is a **percentile**: the value a given fraction of the bag is below. So the
function turns a fraction into a percentile. The book calls it the shape's **percentile function**.
In the code it is called `ppf`.

Pick a fraction at random between zero and one, every fraction equally likely, and ask the
percentile function for the value there. Do that as many times as the model's scenario asks. The
heading of each chart on this page says how many. The values you get are samples from the
distribution: they fill the bag.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def sample(spec: dict, n: int, generator: np.random.Generator)
:end-before: def one_shape
```

`generator.random(n)` draws the random fractions. The percentile function turns them into values.
That is the whole sampler. That is why adding a shape to this book is three lines of code rather
than a new dependency.

The technique is called **inverse transform sampling**. Any shape whose percentile function you can
write down, you can sample. Problem 13.1 asks you to write one.

Here is the simplest:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def uniform_ppf
:end-before: def triangular_ppf
```

A fraction of zero gives the minimum, a fraction of one gives the maximum, and the values between
lie on a straight line. You could have guessed that one. The next one needs a picture.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def triangular_ppf
:end-before: def lognormal_ppf
```

Picture the triangle. Its base runs from the least value the input could take to the most. Its peak
stands over the value the expert would bet on: the **most likely value**, which the code calls
`likely`. This value is called the **mode**.

The height of the triangle at a value says how likely values near it are. A shape drawn this way
(higher where values are likely, lower where they are not) is the input's **density**. The whole
area under it is one.

The area under the density from the minimum up to a value is the fraction of the bag below that
value. So finding the value for a fraction means finding where the area from the left edge reaches
that fraction.

Left of the peak, the area up to a value is a smaller triangle. Its width and its height both grow
in step with the distance from the minimum. So its area grows as the square of that distance.
Halfway from the minimum to the peak, the small triangle is half as wide and half as tall, so it
holds a quarter of the area it holds at the peak.

Set that area equal to the fraction and solve for the value: you take a square root. That is the
line `below` in the code.

Right of the peak, run the same argument from the maximum, using the area above the value. That is
the line `above`.

`at_mode` is the share of the whole area that lies left of the peak. The code uses `below` when the
fraction is smaller than that, and `above` otherwise.

Work it through on paper once. Problem 13.1 is the same exercise for a shape this book does not
have, and it needs one integral.

### Which shape for which input

Choosing a shape is a judgement, not a technical question. It is a claim about the world, and the
first claim a reviewer should argue with.

**Lognormal, for prices and growth and anything that compounds.** The docstring that follows says
why it is the right shape for those things and explains why it is declared by two values rather than
by a mean.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def lognormal_ppf
:end-before: def normal_ppf_scaled
```

The code uses `normal_ppf` and `Z90`. The first is the normal shape's percentile function, imported
from `sizing/normal.py`. The second is `normal_ppf(0.9)`, defined at the top of `sizing/mc.py`: how
far the 90th percentile of a standard normal sits from its middle. Problem 13.2 needs both.

**Triangular, for an expert's guess.** The previous section shows you the code and explains when it
is honest and what its flaw is.

**Uniform, when the bounds are all you know.** The previous section shows when this shape is honest
and why it is dishonest as a default.

**Normal, for measurement error.** In this book it means one thing: the standard error beside a
measured constant. A number was measured, the measurement wobbles, and it is as likely to wobble
high as low. It is the wrong default for a price: a normal can go negative, and a price cannot.
[Appendix C](#appendix-c-distributions) gives each of the four shapes its own section, and then a
*Choosing* section with a table and five questions for selecting one.

Choosing badly is not a rounding error. It is a claim about what can happen, made in a model file
that will outlive the meeting it came from.

Only the inputs the model samples have a shape; the rest are single values, such as definitions,
spec-sheet figures, margins, and decisions about fleet size. For every sampled input, the build
refuses a source that does not name its shape.

```{include} _generated/monte-carlo-provenance.md
```

The table lists every input and its provenance. For a sampled input, the source names its shape, and
most also say why that shape was chosen. The tally at the bottom shows what the model rests on: how
many inputs trace to a source that can be checked (*fact*), how many come from a vendor's sales
material (*vendor claim*), and how many were decided by the modeller (*assumption*).

### Running the bag through the model

Nothing changes about the arithmetic. The model is a graph of quantities, each computed from the
ones before it. Working it out at a point walks the graph in order, doing arithmetic on single
numbers. Sampling it walks the same graph in the same order, doing the same arithmetic on arrays:
one value per sample. The operation `a * b` means the same thing whether `a` and `b` are two numbers
or two long arrays.

So uncertainty travels through the graph without extra work. An input with a distribution becomes an
array. Everything downstream of it becomes an array. A quantity with nothing uncertain upstream
stays a single number, and the arithmetic uses that one number against every value in the array.

Every node in the graph has its own bag of values once the model has been sampled, not only the
outputs at the end. Open [the web service model](/models/web_service-reference.html) and click any
box in the graph. The panel beside the graph shows that node's values as a bar chart, with its p5,
median and p95 beneath it. Use it to find where the range of answers got wide: start at an input and
click along the chain towards the output until the bar charts stop being narrow.

### Reading the answer

```{image} _figures/monte-carlo-tco-distribution.svg
:alt: The five-year total as a distribution, with the point estimate marked on it
:width: 100%
```

An **interval** is the gap between two percentiles. This book reports the gap between the 5th and
the 95th percentile, and calls it the 90% interval. On the charts they are the dashed lines *p5* and
*p95*. The book does not call it a confidence interval. That phrase means something precise to a
statistician and something vaguer to most readers. What is meant here is the plain reading: the
model put nine tenths of its belief in this range.

Why two percentiles rather than the smallest and the largest answer in the bag: the ends are
properties of how many answers you collected, not of the model. Collect ten times as many and the
largest gets larger, every time, because the unlucky combinations had more chances to turn up. The
middle settles, and [ch14](#correlation-and-convergence) measures how quickly.

The red line marked *point* is the five-year total at the point estimate: every input at the middle
of its range, the value half its bag is below. On this chart it sits below the *median*.

This is not a quirk of these numbers. Pass one uncertain input straight through, and the point is
the middle answer exactly: the middle input gives the middle output. Multiply two uncertain inputs,
and the point stays close to the middle. The staff cost, engineers times salary, is an example.

The five-year total adds several cost lines. Each line's bag is lopsided: a short way down to its
lowest values, a long tail up to its highest. That shape is called **skewed**. Each line's own point
sits at its own middle. Add the lines up. A line that comes in high can be far above its middle; a
line that comes in low can be only a little below it. The highs outweigh the lows, so the middle of
the total sits above the sum of the lines' middles. The point estimate of the total is the sum of
the lines' points, which sit at their middles, so the point sits below the *median* of the chart.

The host count's point also sits low, for a different reason: the model takes the largest of three
chains. [ch12](#the-sizing-model) showed why that step pulls the point below the middle.

So the point estimate is not the middle answer once a model adds lopsided quantities or takes the
largest of several.

### How often each ceiling is breached

This is the ceiling table from [ch12](#the-sizing-model), for the finished model: the same fleet
against the same ceilings. [ch12](#the-sizing-model) read its *Verdict* column, which is the plan at
the point estimate.

```{include} _generated/monte-carlo-ceilings.md
```

The finished model draws more inputs from the same seed, so the table may differ from ch12's in a
single cell.

A ceiling is a node in the graph, so it is sampled like every other node: one value for each time
the model was worked out. *Allowed* is the *Limit* less its *Headroom*: the limit times one minus
the headroom. *Over allowed* is the fraction of the samples whose value is above *Allowed*. *Over
limit* is the fraction above *Limit*. Both lines are fixed at the plan's values; only the ceiling's
own value varies from sample to sample.

The last two columns ask the same fleet a different question from the *Verdict*: across everything
this model thinks could happen, how often is this line crossed?

That changes what the sizing answer is. Not "you need this many hosts", but "at this many hosts,
this is how often the thing you were trying to avoid happens anyway". The person who signs for the
fleet can take responsibility for the second. The first says nothing about risk.

ch12 also showed a bigger fleet against the same ceilings, and [ch21](#a-tco-for-finance) prices it
and puts the choice to the person whose decision it is.

### The seed

Every sampled result in this book records the seed its random numbers came from, and the sample
count, and a hash of the sampler's source. Run it again with those three and you get the same
numbers to the last digit.

That is not fastidiousness. An unseeded simulation gives a result nobody can repeat, and a figure
nobody can repeat is a figure nobody can check. This book refuses that everywhere else, and has no
reason to start allowing it here.

## What this cannot tell you

**Whether the model has the right shape.** Everything above takes the model's structure as given and
asks what the inputs are worth. If a cost line is missing, if a ceiling was never declared, or if
two quantities were multiplied that should have been added, sampling carries the mistake through
every sample and reports a confident interval around the wrong answer. That is *structural error*.
No technique in this chapter can see it, and it is the subject of
[ch20 · The missing node](#the-missing-node).

**Whether the shapes are right.** A triangular with generous bounds and a lognormal with tight
ones will give different intervals for the same input, and nothing here can tell you which was
right. The distribution is an assumption like any other, and this book makes you write it in a file
with your name on it for that reason.

**How the inputs were drawn together.** The sampler above draws each input on its own. The intervals
on this page were not produced that way. The model declares two pairs of inputs that move
together: a host's price and the network's price per host, quoted by the same supply chain; and the
busy-hour request rate and the processor time each request takes, because a busier service is a
slower one per request. The evaluator applies the pairing after the draw, so every figure on this
page already carries it, and the chapter has not said so until now. Drawing those pairs
independently would make every interval downstream of them narrower, which is the direction that
gets a plan approved. [ch14](#correlation-and-convergence) names the pairs and measures what they
were worth.

**Whether enough samples were drawn.** This chapter assumed the number of samples was enough and did
not show it. [ch14](#correlation-and-convergence) has the argument, and the way to work it out for a
model of your own.

**How likely any of this is.** The interval is a statement about the model's declared
inputs. It is not a forecast, it carries no track record, and its 95th percentile is not a
promise. It is the best available summary of what you have written down. That is worth a great
deal more than a single number, and a great deal less than knowledge.

## Key takeaways

:::{div}
:class: takeaways

- **Give the model a bag of plausible values instead of one, and the bag of answers is the answer.**
  Filling a bag takes two lines: pick a fraction between zero and one at random, and ask the shape's
  percentile function for the value there. Each input gets its own draws.
- **The shape is a claim about the world, and the first thing a reviewer should argue with.**
  Lognormal for what compounds, triangular for an expert's guess, uniform when the bounds are all
  you know, and normal for measurement error alone.
- **Sampling the model is the same walk of the same graph, on arrays instead of numbers.** Every
  node gets its own bag of values, not only the outputs, so you can walk the chain to where the
  interval got wide.
- **Read the middle, not the ends.** The smallest and largest answers depend on how many you drew;
  the interval between two percentiles belongs to the model. The point estimate, every input at its
  middle, is not the middle answer once the model adds lopsided cost lines or takes the largest of
  several chains.
- **The ceilings are what the machinery is for.** Their last two columns show the fraction of
  samples over each line. The answer they give is not *you need this many hosts* but *at this many,
  this is how often the thing you were avoiding happens anyway*, which the person who signs for the
  fleet can be held to.
:::

## Problems

Four. The first three are in `tests/monte_carlo/` and are graded against definitions the tests
compute for themselves. The fourth has no test and no known answer.

**13.1 — Add a distribution.**
Implement the percentile function for a shape this book does not have: a quantity known only to
within a factor, whose density is proportional to one over the value. Derive it the way the chapter
derived the triangular's: the area under the density from the minimum up to a value, set equal to
the fraction you are given, then solved for the value. It needs one integral, of one over the value,
whose result is a natural logarithm. The rest of the chapter needs only arithmetic, so that step
stands out. The test grades your function against the density itself, integrating it at test time,
so there is nothing to look up.

```bash
python3 -m pytest tests/monte_carlo/test_problem_1_ppf.py -m problem
```

**13.2 — Sample a model by hand.**
The test hands you two of the web service model's inputs, the engineers the fleet occupies and their
fully loaded salary, each with the distribution the model file declares for it. Both are quoted
below, with the formula for the annual staff cost they feed. Sample each yourself, without the
toolkit's sampler: each input with its own random fractions. Work the annual staff cost from your
samples, one sample at a time, with the model's formula. Reproduce the 5th and 95th percentiles the
book publishes for that cost. Your figures will not match to the last digit: a finite number of
samples makes every percentile wobble a little from one set of draws to the next. That wobble is
called sampling error, and the test allows for it.

The page's `lognormal_ppf` uses two names from outside it: `normal_ppf`, which you import from
`sizing.normal`, and `Z90`, which is `normal_ppf(0.9)`. The point is to find out how small the
machinery is.

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: staff_fte:
:end-before: annual_opex:
```

```bash
python3 -m pytest tests/monte_carlo/test_problem_2_by_hand.py -m problem
```

**13.3 — Where the point estimate sits.**
For each of four outputs of the web service model (the host count the model recommends, the
five-year total cost, capex, and annual opex), find the fraction of its sampled answers that fall
strictly below its point estimate. Some of these fractions sit near one half and some do not. For
each one that does not, name the step in its chain that moved the point, and which way. The section
*Reading the answer* gives you the two kinds of step to look for.

```bash
python3 -m pytest tests/monte_carlo/test_problem_3_where_the_point_sits.py -m problem
```

**13.4 — Defend a distribution.** No test: the invoices are yours, and so is the shape you would
defend.

Take a price you pay, find two years of invoices for it, and decide which of the four
shapes in this chapter you would use and why. Then check what the last two years would have looked
like under your choice. If the answer embarrasses you, that is the exercise working.

A good answer names the shape, the reason for it and not another, and the band, written the way the
model file would declare it. For a lognormal, give the two values you would be surprised to see it
under and over (its p10 and p90). For a triangular or a uniform, give its bounds. Write it as a
sentence a colleague could disagree with.

The invoices show it wrong, and what counts as wrong depends on the shape you chose.

A lognormal declared by its p10 and p90 expects about one invoice in ten below the lower value and
one in ten above the upper, so about one in five outside the band by design. Many more than that
outside means the band was too narrow. None outside, and none near either end, means it was too wide
to be a claim. A triangular or a uniform claims that nothing falls outside its bounds. Any invoice
outside them means the bounds were wrong. The chapter argues that a normal is the wrong default for
a price. An answer that chooses one has to answer that argument first.

## Where to go next

Metropolis and Ulam's original paper @metropolis1949monte is seven pages, is readable without any
statistics, and is a useful corrective to the idea that this is a modern technique.

`numpy.random`'s documentation on generators and seeding is worth twenty minutes, particularly
the part about why `default_rng` exists and what it replaced.

% word-ok: named here only to hand it to ch14, which teaches it
[ch14](#correlation-and-convergence) picks up the two things this chapter used without
establishing: the correlations the intervals above already carry, and the sample count.

[Appendix B](#appendix-b-monte-carlo-module) quotes the complete `sizing/mc.py` and
`sizing/normal.py`, showing the order a model run calls them.
