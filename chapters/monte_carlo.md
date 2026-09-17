---
title: "Monte Carlo"
short_title: "ch13 Monte Carlo"
---

(monte-carlo)=
# ch13 · Monte Carlo

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch12](#the-sizing-model) |
| **What it produces** | The storage model sampled rather than evaluated, and the probability each of its ceilings is breached |
| **Built from** | `storage_cluster-reference`, `storage_cluster-sized_for_growth` |
:::

## The question

The sizing model has produced a node count. How sure are we?

[ch12](#the-sizing-model) took a stated workload, multiplied along two chains, took the larger of
the two answers, and produced a number. Every step was arithmetic you could check by hand. The
number is correct. What nobody has established is whether it is *right*, and those turn out to be
different questions — because every input to that chain was itself uncertain, and the chain has
no way to say so.

This chapter is the machinery for asking the second question. It assumes you can read code and do
arithmetic, and it assumes nothing at all about statistics.

## The material

### A single number is a bet you did not know you placed

Start with the model as [ch12](#the-sizing-model) left it.

```{include} _generated/monte-carlo-outputs.md
```

The first column is what the chain produced: one value per output, from one value per input. The
second column is the same model, with each input allowed to be as uncertain as the person who
wrote it down actually is.

Look at the node count. The point estimate is a real number, correctly computed, and it is
somewhere in the middle of a range that spans most of an order of magnitude. Nothing went wrong.
The calculation had no way to mention that its inputs were guesses, so it did not mention it.

```{image} _figures/monte-carlo-nodes-distribution.svg
:alt: The recommended node count as a distribution, with the point estimate marked
:width: 100%
```

That is the whole motivation, and everything below is how the second column was produced.

### Instead of one value, a bag of values

The idea is almost embarrassingly simple. If you do not know what the growth rate will be, do not
give the model one growth rate. Give it a bag of plausible growth rates. Run the model once for
every value in the bag. You get a bag of answers out, and the bag is the answer.

That is Monte Carlo. There is no more to it than that; everything else is bookkeeping about how
to fill the bag and how to read it.

Two words, and you will not need many more. The bag of plausible values for an input is its
**distribution**. One value drawn from the bag is a **sample**. The bag of answers that comes out
the other end is the output's distribution, and reading it is the last section of this chapter.

### Where the bag comes from: pick a percentile at random

Here is the part that makes it work, and it is one line of code.

Every distribution can be described by a function that answers one question: *what value sits at
this percentile?* Give it 0.5 and it hands back the middle value. Give it 0.9 and it hands back
the value that nine tenths of the distribution is below. Call that function the distribution's
**percentile function**.

Now: pick a percentile uniformly at random, between zero and one, and ask the function what value
sits there. Do it a hundred thousand times. You have sampled the distribution.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def sample(spec: dict, n: int, generator: np.random.Generator)
:end-before: def one_shape
```

`generator.random(n)` draws the percentiles. The percentile function turns them into values. That
is the entire sampler, and it is why adding a distribution to this book is three lines rather
than a new dependency.

The technique is called **inverse transform sampling**, and the name is the least interesting
thing about it. What matters is what it buys: any distribution whose percentile function you can
write down, you can sample. Problem 13.1 asks you to write one.

Here is the simplest:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def uniform_ppf
:end-before: def triangular_ppf
```

Percentile zero gives the minimum, percentile one gives the maximum, and everything in between is
a straight line. You could have guessed that one. The next is the first that needs thinking about:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def triangular_ppf
:end-before: def lognormal_ppf
```

Two branches, meeting at the mode. Below the mode the area under the triangle grows as the square
of the distance from the minimum, so inverting it gives a square root. That is the whole
derivation, and it is worth doing on paper once — after which every other distribution in this
chapter is the same exercise with different algebra.

### Which shape for which input

This is where the judgement is, and it is not a technical question. Choosing a distribution is a
claim about the world, and it is the claim a reviewer should argue with first.

**Lognormal, for prices and growth and anything that compounds.** Two properties earn it its
place. It cannot go negative, and neither can a price. And a product of several lognormals is
another lognormal — which is what a chain of multiplications *is*, so the uncertainty arriving at
the end of a sizing chain has roughly this shape whether or not anybody chose it.

The parameters here are two percentiles rather than the mean and standard deviation of a
logarithm, because nobody has an intuition for the second and everybody has one for the first.
*"I would be surprised if it were under eleven or over nineteen"* is a sentence a person can say
about a price, and it is exactly what the model file records.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def lognormal_ppf
:end-before: def normal_ppf_scaled
```

**Triangular, for an expert's guess.** The least it could be, the most it could be, and the one
they would bet on. Most sizing inputs arrive in this shape, because it is the shape of the answer
to "what is it, roughly?". Its flaw is worth naming every time it is used: it asserts that nothing
outside the bounds can happen, and the bounds came out of somebody's memory.

**Uniform, when the bounds really are all you know.** A price capped by a contract. A retention
window somebody will pick from a range. Honest exactly there, and dishonest as a default — it
says the extremes are as likely as the middle, and almost nothing real is like that.

**Normal, for measurement error.** In this book it means one thing: the standard error beside a
measured constant. A number was measured, the measurement wobbles, and it is as likely to wobble
high as low. It is the wrong default for a price, for the reason lognormal is the right one: the
normal will happily go negative and a price will not.

Choosing badly is not a rounding error. It is a claim about what can happen, made in a model file
that will outlive the meeting it came from. So the build refuses an input that is sampled without
naming its shape and saying why, and every input in this book records who claimed it, on what
basis, and which of the four it is:

```{include} _generated/monte-carlo-provenance.md
```

The tally at the bottom is the honest summary of any model. This many of the numbers are
traceable; this many are somebody's sales material; this many were decided in a room.

### Running the bag through the model

Nothing changes. That is the point worth pausing on.

The model is a graph of quantities, each computed from the ones before it. Evaluating it at a
point walks the graph in order, doing arithmetic on numbers. Sampling it walks the same graph in
the same order, doing the same arithmetic on arrays — because `a * b` means the same thing
whether `a` and `b` are two numbers or two hundred thousand. The evaluator in this book has one
expression walker and hands it a different set of functions depending on which pass it is doing.

So uncertainty propagates for free. An input with a distribution becomes an array; everything
downstream of it becomes an array; everything else stays a single number and broadcasts.

```{image} _figures/monte-carlo-graph.svg
:alt: The sub-graph feeding the five-year total, coloured by node kind
:width: 100%
```

Every node in that graph has a distribution once the model has been sampled, not just the ones at
the end. The interactive version of this figure will show you any of them, which is the fastest
way to find out *where* an interval got wide — you walk the chain until the histograms stop being
narrow.

### Reading the answer

```{image} _figures/monte-carlo-tco-distribution.svg
:alt: The five-year total as a distribution, with the point estimate marked on it
:width: 100%
```

Two words for this, and then we are done with vocabulary.

A **percentile** is the value a given fraction of the bag is below. The 5th percentile is the
value only one sample in twenty came in under.

An **interval** is the gap between two of them. This book reports the gap between the 5th and the
95th percentile, calls it the 90% interval, and deliberately does not call it a confidence
interval. That phrase means something precise to a statistician and something vaguer to everybody
else, and what is meant here is only the plain reading: *the model put nine tenths of its belief
in this range*.

Note where the red line sits relative to the middle of the distribution. For a chain of
multiplications with skewed inputs, the answer you get from the average inputs is not the average
answer, and it is not the middle one either. There is a theorem behind that; you do not need it.
You need to have seen it happen once.

### What the ceilings do with this

Here is the output that has no equivalent in a spreadsheet, and the reason the whole apparatus
was worth building.

```{include} _generated/monte-carlo-ceilings.md
```

At the point estimate, every ceiling is fine. That is not surprising — [ch12](#the-sizing-model)
sized the cluster from the point estimates, so of course it satisfies them. The last two columns
are the same model asked a different question: across everything this model thinks could happen,
how often is this limit breached?

That is a sizing answer. Not "you need this many nodes" but "at this many nodes, this is how often
the thing you were trying to avoid happens anyway". Somebody can take responsibility for the
second. Nobody can take responsibility for the first, because it does not say anything.

And once the question is in that form, it has a price. Here is the same model with a bigger
cluster bought:

```{include} _generated/monte-carlo-ceilings-resized.md
```

What the extra capital buys is the difference between two percentages. Whether it is worth it is
not a modelling question, and [ch21](#a-tco-for-finance) is about how to put it to the person
whose decision it is.

### The seed

Every sampled result in this book records the seed its random numbers came from, and the sample
count, and a hash of the sampler's source. Run it again with those three and you get the same
numbers to the last digit.

That is not fastidiousness. An unseeded simulation is a measurement nobody can repeat, and a
figure nobody can repeat is a figure nobody can check — which is the thing this repository
refuses everywhere else and has no reason to start allowing here.

## What this cannot tell you

**Whether the model has the right shape.** Everything above takes the structure as given and asks
what the inputs are worth. If a cost line is missing, if a ceiling was never declared, if two
quantities were multiplied that should have been added — sampling will propagate the error
beautifully and report a confident interval around the wrong answer. This is *structural error*,
it is invisible to every technique in this chapter, and it is the subject of
[ch20](#the-missing-node).

**Whether the shapes were chosen honestly.** A triangular with generous bounds and a lognormal
with tight ones will give different intervals for the same input, and nothing here can tell you
which was right. The distribution is an assumption like any other, and this book makes you write
it in a file with your name on it for that reason.

**How the inputs were drawn together.** The sampler above draws each input on its own. The
intervals above were not produced that way: this model declares two pairs that move together —
drives and chassis, which are quoted by the same supply chain, and growth and read load, which
are the same year seen twice — and the evaluator applies them after the draw. So every figure on
this page already carries them, and none of this chapter has said so. Drawing those pairs
independently instead would make every interval here *narrower*, which is the direction that gets
a plan approved. [ch14](#correlation-and-convergence) names the pairs, and measures what they
were worth.

**Whether a hundred thousand samples was enough.** It was assumed here and not established. The
argument, and the way to work it out for a model of your own, is also
[ch14](#correlation-and-convergence).

**How likely any of this actually is.** The interval is a statement about the model's declared
inputs. It is not a forecast, it carries no track record, and its 95th percentile is not a
promise. It is the best available summary of what you have written down — which is worth a great
deal more than a single number, and a great deal less than knowledge.

## Problems

Four. The first three are in `tests/monte_carlo/` and are graded against definitions the tests
compute for themselves. The fourth has no test and no known answer.

**13.1 — Add a distribution.**
Implement the percentile function for a distribution this book does not have, and show that
inverse-transform sampling reproduces the properties its parameters claim. Both targets are
derived from the parameters at test time, so there is nothing to look up.

```bash
python3 -m pytest tests/monte_carlo/test_problem_1_ppf.py
```

**13.2 — Sample a model by hand.**
Take the storage model, sample two of its inputs yourself without using `sizing.evaluate`, and
reproduce the interval the build publishes for one output to within sampling error. The point is
to discover how small the machinery actually is.

```bash
python3 -m pytest tests/monte_carlo/test_problem_2_by_hand.py
```

**13.3 — Make the point estimate lie.**
Find a set of input distributions, within the ranges the model already declares, for which the
point estimate of the five-year total falls outside the 50% interval of the sampled answer. Then
say in one sentence what property of the model made it possible.

```bash
python3 -m pytest tests/monte_carlo/test_problem_3_point_lies.py
```

**13.4 — Defend a distribution.**
No test. Take a price you actually pay, find two years of invoices for it, and decide which of
the four shapes in this chapter you would use and why. Then check what the last two years would
have looked like under your choice. If the answer embarrasses you, that is the exercise working.

## Where to go next

Metropolis and Ulam's original paper @metropolis1949monte is seven pages, is readable without any
statistics, and is a useful corrective to the idea that this is a modern technique.

`numpy.random`'s documentation on generators and seeding is worth twenty minutes, particularly
the part about why `default_rng` exists and what it replaced.

[ch14](#correlation-and-convergence) picks up the two things this chapter used without
establishing: the correlations the intervals above already carry, and the sample count.
