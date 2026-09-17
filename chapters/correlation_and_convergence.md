---
title: "Correlation and convergence"
short_title: "ch13 Correlation and convergence"
---

(correlation-and-convergence)=
# ch13 · Correlation and convergence

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch12](#monte-carlo) |
| **What it produces** | What assuming independence was worth, and how many samples is enough |
| **Built from** | `correlation-effect`, `convergence-storage-tco`, `observability-reference` |
:::

## The question

[ch12](#monte-carlo) produced an interval, and it rested on two things nobody checked: that every
input moves on its own, and that a hundred thousand samples was enough to settle the answer.

Both are testable, and this chapter tests both. More samples do not make an interval narrower,
which is the opposite of what most people expect.

## The material

### Inputs that move together

The storage model draws a drive price and a chassis price independently. Ask anybody who has
bought either: a year when drives are scarce is usually a year when servers are, because they
come through the same supply chain and are quoted in the same quarter.

Drawing them independently is not a neutral choice. It is the claim that one can save you from
the other — that a bad drive quarter will, on average, be offset by a good chassis quarter. If
that is false, the model is reporting a narrower interval than the evidence supports.

Narrower is the direction that gets a plan approved.

So a model file can declare which inputs move together, how strongly, and why:

```{include} _generated/correlation-and-convergence-declared.md
```

The last column is required. A correlation coefficient with no reason attached is a number
somebody will copy into the next model without knowing what it was for.

### Correlating ranks, not values

The obvious way is to correlate the *values*: nudge each drive price up a little when the chassis
price is up. Do that and you have changed the drive price distribution — the thing you carefully
chose in [ch12](#monte-carlo), with its own percentiles and its own shape. You set out to encode
one belief and quietly overwrote another.

The method this book uses only ever **reorders**. Every value that was going to be in a column is
still in it, in the same quantity. All that changes is which draws line up with which. So each
input keeps exactly the distribution the modeller chose, and the correlation is expressed in the
pairing rather than in the numbers.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def correlate(
:end-before: # -- reading the answer
```

One subtlety in there is easy to skip and then be quietly wrong about. The method works by
correlating normal scores, and the rank correlation that comes out is weaker than the one that
went in, by a known amount. Apply no correction and every declared correlation lands slightly
weaker than it was written. Small, consistent, and exactly the kind of error that survives review
forever, because nobody expects the number they typed to come back as a different number. So the
relation is inverted before use:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rank_to_score_correlation
:end-before: def correlate(
```

Problem 13.2 checks both halves of the claim: that the correlation comes out where it was asked
for, and that the marginal distributions did not move.

### What the correlations bought

Both reference models, sampled twice: once with their declared correlations, once with the
correlations deleted.

```{include} _generated/correlation-and-convergence-effect.md
```

Every row is positive. Assuming independence made every interval narrower, and in the
observability model's ingest chain it made it *substantially* narrower. That chain has several
inputs feeding off the same growth, and pretending they are strangers lets them cancel each other
out.

One row barely moves, and it is in the table deliberately. A correlation between two inputs that
do not both feed the output changes almost nothing. Seeing one that does not matter beside one
that does is the fastest way to stop treating the subject as magic.

The general shape: **correlation between inputs that push the same way widens the interval**. It
is not a correction, it is not a refinement, and it does not make the model more precise. It
removes an assumption that was making the model look better than it was.

### How many samples is enough

Now the second thing [ch12](#monte-carlo) assumed. The obvious experiment is to run the model at
rising sample counts and watch the interval narrow.

That experiment does not work.

**The interval does not narrow.** A 90% interval is a property of the distribution the model
describes — of how uncertain the model's inputs actually are. More samples do not make that
smaller. They converge on it. Run the storage model with ten thousand draws and with a million,
and the interval is the same width; it was never a function of how hard you looked.

What more samples buy is knowing **where** that interval is. Two runs of the same model with
different random seeds give slightly different answers, and the gap between them shrinks as you
draw more. So the experiment has to be run many times over at each sample count, and what gets
recorded is the spread between those runs:

```{include} _generated/correlation-and-convergence-table.md
```

Two columns, two behaviours. The first settles. The second falls by close to the square root of
ten per decade, which is the law measured rather than asserted.

Look at the individual ratios before you believe the summary, because they wander. Each spread in
that column is itself *estimated*, from a limited number of independent runs, and an estimate of a
spread is noisy in exactly the way everything else in this chapter is noisy. Measuring how
uncertain something is turns out to be an uncertain measurement, and a figure demonstrating that
law had better not be the one place in the book that forgets it. The overall rate across the
range is far steadier than any single step, which is why it is the number on the last row.

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
going to write it to the nearest million — which, given everything else in this book, is the more
defensible choice — you needed far fewer samples than you took.

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

## What this cannot tell you

**Which correlations exist.** Everything above takes the declared pairs as given. Nothing here
discovers a correlation, and nothing here warns you about one you failed to declare. From inside
the model, an undeclared correlation is indistinguishable from a correlation of zero. That is the
same failure as a missing node, and it belongs to [ch19](#the-missing-node).

**Whether the coefficient is right.** A rank correlation declared as moderate rather than strong
is a guess with the same standing as any other assumption in the model. The `because` field
beside it in the model file is the only thing standing behind it.

**Anything about correlations that are not monotonic.** Rank correlation describes two quantities
that tend to move in the same direction. Two that move together up to a point and then diverge —
which is what a ceiling does to everything downstream of it — are not described by a single
coefficient at all, and this book does not pretend otherwise.

**That more samples are ever the answer to a wide interval.** They are not. More samples tell you
where the interval is, not how wide it is. A wide interval means the inputs are uncertain, and
the only things that narrow it are measuring something or deciding something —
[ch18](#which-input-is-the-answer).

## Problems

Four. The first three are graded, in `tests/correlation_and_convergence/`.

**13.1 — Show the square-root law.**
Run one output of the storage model at several sample counts, with several independent seeds at
each, and assert that the run-to-run spread falls as one over the square root of the count. The
tolerance is itself a sampling question, and the test makes you confront that.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_1_root_n.py
```

**13.2 — Correlate without disturbing the marginals.**
Add a correlation to a model and assert two things: that the interval on a shared output widens,
and that every input's own distribution is unchanged. The second is the property that makes the
method trustworthy, and it is one line to check.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_2_marginals.py
```

**13.3 — Find the missing node.**
A model file in the test directory is deliberately incomplete, and its stated interval is a lie:
an observed total, stamped separately, falls outside it. Repair the model so the observation lands
inside the interval, without widening any input's distribution to get there. There is no answer
key; the oracle is an independent figure the model does not contain.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_3_missing_node.py
```

**13.4 — Break the convergence experiment.**
No test. The experiment in this chapter uses a different seed for every replicate. Change it so
that every replicate at a given sample count shares one seed, re-run it, and explain what the
figure now shows and why it is worthless. Then say what else in this repository would have to be
wrong for that mistake to survive review.

## Where to go next

Iman and Conover's paper @imanconover1982 is the method in this chapter, and is unusually
readable for a statistics paper of its era. The section on what the method does *not*
guarantee is the part to read twice.

[ch18](#which-input-is-the-answer) is the question this chapter keeps deferring: given that the
interval is wide, which single input should you go and measure?

[ch19](#the-missing-node) is the failure that neither this chapter nor [ch12](#monte-carlo) can
see.
