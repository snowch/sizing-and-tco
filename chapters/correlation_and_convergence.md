---
title: "Correlation and convergence"
short_title: "ch14 Correlation and convergence"
---

(correlation-and-convergence)=
# ch14 · Correlation and convergence

## The question

[ch13](#monte-carlo) produced an interval, and it rested on two things nobody checked: that every
input moves on its own, and that a hundred thousand samples was enough to settle the answer.

Both are testable, and this chapter tests both. More samples do not make an interval narrower,
which is the opposite of what most people expect.

## The material

### Inputs that move together

The web service model prices a host and the network port it plugs into. Ask anybody who has
bought either: a year when hosts are scarce is usually a year when optics are, because they come
through the same supply chain and are quoted in the same quarter.

Drawing them independently is not a neutral choice. It is the claim that one can save you from
the other: that a bad host quarter will, on average, be offset by a good network quarter. If that
is false, the model is reporting a narrower interval than the evidence supports.

Narrower is the direction that gets a plan approved.

Two inputs that tend to move together are **correlated**, and how strongly they do is their
**correlation**. A model file can declare it, along with why:

```{include} _generated/correlation-and-convergence-declared.md
```

The last column is required. A correlation coefficient with no reason attached is a number
somebody will copy into the next model without knowing what it was for.

### Correlating ranks, not values

The obvious way is to correlate the *values*: nudge each host price up a little when the network
price is up. Do that and you have changed the host price distribution: the thing you carefully
chose in [ch13](#monte-carlo), with its own percentiles and its own shape. You set out to encode
one belief and quietly overwrote another.

The method this book uses only ever **reorders**. Every value that was going to be in a column is
still in it, in the same quantity. All that changes is which draws line up with which. So each
input keeps exactly the distribution the modeller chose. The correlation is expressed in the
pairing, not in the numbers.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def correlate(
:end-before: # -- reading the answer
```

One subtlety in there is easy to skip, and then to be quietly wrong about. The method works by
correlating normal scores, and the rank correlation that comes out is weaker than the one that went
in, by a known amount. Apply no correction, and every declared correlation lands slightly weaker
than it was written. That error is small and consistent, and it is the kind that survives review
forever, because nobody expects the number they typed to come back as a different number. So the
relation is inverted before use:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rank_to_score_correlation
:end-before: def correlate(
```

Problem 14.2 checks both halves of the claim: that the correlation comes out where it was asked
for, and that each input's own distribution did not move.

### What the correlations bought

Both reference models, sampled twice: once with their declared correlations, once with the
correlations deleted.

```{include} _generated/correlation-and-convergence-effect.md
```

Every row is positive. Assuming independence made every interval narrower, and in the
observability model's ingest chain it made it *substantially* narrower. That chain has several
inputs feeding off the same growth, and pretending they are strangers lets them cancel each other
out.

The web service's rows are modest, and they are in the table deliberately: its two declared pairs
are weak ones, and one of them does not reach the five-year total at all. Seeing a correlation
that barely matters beside one that does is the fastest way to stop treating the subject as
magic.

The general rule: **correlation between inputs that push the same way widens the interval**. It
is not a correction. It is not a refinement. It does not make the model more precise. It removes
an assumption that was making the model look better than it was.

### How many samples is enough

Now the second thing [ch13](#monte-carlo) assumed. The obvious experiment is to run the model at
rising sample counts and watch the interval narrow.

That experiment does not work.

**The interval does not narrow.** A 90% interval is a property of the distribution the model
describes, which is to say of how uncertain the model's inputs are. More samples do not
make that smaller. They **converge** on it: the answer settles towards the interval the inputs
imply. Run the web service model with ten thousand draws and with a million, and the interval is
the same width. It was never a function of how hard you looked.

What more samples buy is knowing **where** that interval is. Two runs of the same model with
different random seeds give slightly different answers, and the gap between them shrinks as you
draw more. So the experiment has to be run many times over at each sample count, and what gets
recorded is the spread between those runs:

```{include} _generated/correlation-and-convergence-table.md
```

Two columns, two behaviours. The first settles. The second falls, by about the square root of ten
per decade across the range. That is the law measured rather than asserted, and measured with
noise, which is the next paragraph.

Look at the individual ratios before you believe the summary, because they wander. Each spread in
that column is itself *estimated*, from a limited number of independent runs. An estimate of a
spread is noisy in the way everything else in this chapter is noisy. Measuring how
uncertain something is turns out to be an uncertain measurement, and a figure demonstrating that
law had better not be the one place in the book that forgets it. The overall rate across the
range is far steadier than any single step. That is why it is the number on the last row.

The smallest row is excluded from the law and kept in the table. At that count a 95th percentile
is one of the largest handful of draws there were, bounded by the sample itself, and nowhere near
the regime the square-root law describes. It stays because it shows the *other* column at its
clearest: that is the one row where the interval has visibly not settled.

```{image} _figures/correlation-and-convergence-curve.svg
:alt: Interval width and run-to-run spread against sample count, with the square-root law
:width: 100%
```

To halve the wobble, take four times as many samples. To get it down by a factor of ten, take a
hundred times as many. That is brutal, and it is why nobody buys precision this way past a point.

The law also gives a definition of "enough" that is a calculation rather than a habit:

> **Enough samples is when the answer stops moving between runs at the precision you are going to
> report it to.**

If you are going to write the five-year total to the nearest hundred thousand, you need the
run-to-run spread below that, and the table says which sample count gets you there. If you are
going to write it to the nearest million, which is the more defensible choice given everything
else in this book, you needed far fewer samples than you took.

`sizing.mc` has the arithmetic both ways round:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def samples_needed
:end-before: def histogram
```

### What settling is not

A model whose answer has stopped moving between runs has settled its *arithmetic*. That is all it
has settled.

You can run a model at a million samples, watch the interval stabilise to four significant
figures, and present it with complete confidence, while a whole cost line is missing from the
model. The sampling converged beautifully on the wrong number. Convergence is a statement about
the calculation, never about the thing being calculated.

:::{note} Key takeaways
- **Inputs that move together must be drawn together.** Drawing a host price and a network price
  independently claims that one can save you from the other, and it makes every interval narrower
  than the evidence supports.
- **Correlate the ranks, not the values.** Reordering the draws expresses the pairing without
  changing the distribution each input was given, and the relation is inverted first so the declared
  strength comes out as written.
- **Correlation between inputs that push the same way widens the interval.** It is not a refinement.
  It removes an assumption that made the model look better than it was.
- **More samples do not narrow an interval.** The width belongs to the inputs. More draws only
  settle where the interval is, and the run-to-run wobble falls with the square root of the count.
- **Enough samples is when the answer stops moving at the precision you will report it to, and a
  settled answer has settled its arithmetic and nothing else.** A model can converge beautifully on
  the wrong number.
:::

## What this cannot tell you

**Which correlations exist.** Everything above takes the declared pairs as given. Nothing here
discovers a correlation, and nothing here warns you about one you failed to declare. From inside
the model, an undeclared correlation is indistinguishable from a correlation of zero. That is the
same failure as a missing node, and it belongs to [ch20](#the-missing-node).

**Whether the coefficient is right.** A rank correlation declared as moderate rather than strong
is a guess with the same standing as any other assumption in the model. The `because` field
beside it in the model file is the only thing standing behind it.

**Anything about correlations that are not monotonic.** Rank correlation describes two quantities
that tend to move in the same direction. Two that move together up to a point and then diverge,
which is what a ceiling does to everything downstream of it, are not described by a single
coefficient at all. This book does not pretend otherwise.

**That more samples are ever the answer to a wide interval.** They are not. More samples tell you
where the interval is, not how wide it is. A wide interval means the inputs are uncertain. The
only things that narrow it are measuring something or deciding something:
[ch19 · Which input to go and measure](#which-input-is-the-answer).

## Problems

Five. The first three are graded, in `tests/correlation_and_convergence/`. The last two are not,
and say why.

**14.1 — Show the square-root law.**
Run one output of the web service model at several sample counts, with several independent seeds at
each, and assert that the run-to-run spread falls as one over the square root of the count. The
tolerance is itself a sampling question, and the test makes you confront that.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_1_root_n.py
```

**14.2 — Correlate without disturbing the marginals.**
Add a correlation to a model and assert two things: that the interval on a shared output widens,
and that every input's own distribution is unchanged. The second is the property that makes the
method trustworthy, and it is one line to check.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_2_marginals.py
```

**14.3 — Find the missing node.**
A model file in the test directory is deliberately incomplete, and its stated interval is a lie:
an observed total, stamped separately, falls outside it. Repair the model so the observation lands
inside the interval, without widening any input's distribution to get there. There is no answer
key; the oracle is an independent figure the model does not contain.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_3_missing_node.py
```

**14.4 — Break the convergence experiment.** No test. The experiment in this chapter uses a
different seed for every replicate. Change it so that every replicate at a given sample count
shares one seed, re-run it, and explain what the figure now shows and why it is worthless. Then say
what else in this repository would have to be wrong for that mistake to survive review.

**14.5 — Which of your inputs move together.** No test: nothing here can see which of your
quantities move together.

Nothing in this book discovers a correlation; they are all declared. Go through your own inputs in
pairs and find the ones that are not independent: the growth rate and the peak ratio, the price
and the quantity, the compression ratio and the kind of data.

For each pair, say which direction and roughly how strongly. Then say what it does to your answer.
Correlated inputs moving the same way widen the result, and treating them as independent is the
commonest way a model quietly reports less doubt than it has.

A good answer names at least one pair and says whether ignoring it makes your interval too narrow
or too wide. If you find no pairs at all in a chain of six quantities about one system, look
again. Independence is a strong claim, and it is rarely true.

## Where to go next

Iman and Conover's paper @imanconover1982 is the method in this chapter, and is unusually
readable for a statistics paper of its era. The section on what the method does *not*
guarantee is the part to read twice.

[ch19](#which-input-is-the-answer) is the question this chapter keeps deferring: given that the
interval is wide, which single input should you go and measure?

[ch20](#the-missing-node) is the failure that neither this chapter nor [ch13](#monte-carlo) can
see.
