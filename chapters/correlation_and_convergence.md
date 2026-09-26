---
title: "Correlation and convergence"
short_title: "ch14 Correlation and convergence"
---

(correlation-and-convergence)=
# ch14 · Correlation and convergence

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

[ch13](#monte-carlo) drew two pairs of inputs together—a host's price with the network's price,
and the busy hour with what a request costs—and said so at its end. It did not show how the
pairing is done or what it changed. This chapter does both.

ch13 assumed that a hundred thousand samples was enough to settle the answer, but said it had not
established that. This chapter works out what "enough" means. One thing to know now: more samples
do not make an interval narrower. They tell you where it is more precisely.

## The material

### Inputs that move together

ch13's figures already drew two pairs of the web service model's inputs together. This section
shows the pairs as the model file declares them. Drawing two inputs independently is a claim: a
high draw of one is as likely to meet a low draw as a high one. Across many draws they partly
cancel. If the two tend to move together, that cancellation does not happen, and drawing them
independently makes the model's interval narrower than the evidence supports.

Two inputs that move together are **correlated**, and how strongly is their **correlation**. A
model file declares each pair in a `correlations:` block: the two inputs, the rank correlation
`rho`, and a `because` that says why.

The rank correlation asks whether two inputs' ranks tend to move together. An input's rank is its
position when all draws of that input are sorted, smallest first. The scale runs from minus one
(the two always rank in opposite orders) through zero (one rank tells you nothing about the
other's) to plus one (they always rank in the same order).

```{include} _generated/correlation-and-convergence-declared.md
```

Both of the web service model's pairs are positive and moderate: see the Rank correlation column.
The Because column is required for every pair; the build refuses a correlation with an empty
`because`. A coefficient with no reason is a number the next modeller copies without knowing what
it was for.

### Correlating ranks, not values

The obvious way to make two inputs move together is to push each value higher when the other is
high. Do that and you have changed the host price distribution: the one you chose in
[ch13](#monte-carlo), with its percentiles and its shape. You set out to add one belief and
overwrote another.

The toolkit reorders the draws instead, using Iman and Conover's method @imanconover1982. Every
draw of each input stays in its column. All that changes is the order: after reordering, the
highest host prices tend to sit beside the highest network prices. The method builds a **normal
scores** column for each input by reading percentiles evenly spaced across the normal shape ch13
used. It gives these stand-in columns the declared correlations, then sorts each input's real
draws to match the rank order of its stand-ins. Because the stand-ins have the same shape
regardless of each input's distribution, the method works the same on a lognormal price as on a
triangular one.

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def correlate(
:end-before: # -- reading the answer
```

The rank correlation that comes out is slightly weaker than the normal scores were. Karl Pearson
published the formula that links the two @pearson1907further. The toolkit inverts that formula
before use, so the rank correlation you declare in a model file is the rank correlation you get.
The code below is the inversion:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def rank_to_score_correlation
:end-before: def correlate(
```

### What the correlations bought

Both reference models were sampled twice with the same seed: once with their declared
correlations, once with every correlation removed.

```{include} _generated/correlation-and-convergence-effect.md
```

Every row shows a positive difference: removing the correlations made each half-width smaller.
The observability model's `known_ingest` output shows the largest difference. It has two pairs
reaching it: one between annual growth and extra accidental label values, the other between
request rate and lines logged per request. Drawn independently, the four inputs partly cancel.
Declared as correlated, they push the same way together, so the half-width widens.

The web service's rows are small. Each output here is fed by only one declared pair, and both of
its pairs are moderate. The busy-hour pair does not feed the five-year total; the price pair does
not feed the host count.

The `query_utilisation` output has no declared pair with both members feeding it. Its small
difference comes from reordering the draws, not from a correlation affecting it. When only one
input in a pair feeds an output, declaring the correlation does almost nothing there.

**Correlation between inputs that push the same way widens the interval of every output both of
them feed.** Declaring it is not a refinement and does not make the model more precise. It removes
an assumption that was making the model look more certain than it was.

### How many samples is enough

Now the second thing [ch13](#monte-carlo) assumed: that a hundred thousand draws was enough. The
obvious test is to run the model at rising sample counts and watch the interval narrow. That
experiment does not work.

**The interval does not narrow.** Its width is set by how uncertain the model's inputs are. More
draws do not shrink it. They **converge** on it: the answer settles towards the width the inputs
imply.

What more draws buy is knowing more precisely where that interval is. Two runs of the same model
with different random seeds give slightly different answers. The **run-to-run spread** is how far
those answers land from each other. It shrinks as you draw more. The law: the run-to-run spread
falls as one over the square root of the number of draws. Ten times the draws cuts the spread by
the square root of ten. To halve the spread, you need four times the draws.

To measure this law, the web service model's five-year total was run many times at each sample
count, each with its own seed. The spread column's heading says how many runs. The table records
the interval half-width, averaged over those runs, and the run-to-run spread of each run's 95th
percentile.

```{include} _generated/correlation-and-convergence-table.md
```

Read the table's two middle columns. The half-width column settles: from the row for a thousand
samples down, it barely moves. The run-to-run spread column keeps falling. The last row gives the
rate at which the spread fell per tenfold step from a thousand samples up, beside the square root
of ten from the law.

The individual ratios in the last column wander. Each spread is itself estimated from a limited
number of runs, so it is noisy. The rate across the whole range is far steadier than any single
step, which is why it is the number on the last row. Measuring how uncertain something is turns
out to be an uncertain measurement.

The row for a hundred samples is excluded from the law and kept in the table. At that count a
95th percentile is one of the largest handful of draws there were, bounded by the sample itself,
and the square-root law does not yet describe it. The row stays because it is the one where the
half-width has visibly not settled.

```{image} _figures/correlation-and-convergence-curve.svg
:alt: Interval width and run-to-run spread against sample count, with the square-root law
:width: 100%
```

To cut the run-to-run spread by a factor of ten, you need a hundred times as many draws. That is
why nobody buys precision this way past a point.

The law gives a definition of "enough" that is a calculation rather than a habit:

> **Enough samples is when the answer stops moving between runs at the precision you are going to
> report it to.**

If you will report the five-year total to the nearest ten thousand dollars, the run-to-run spread
has to be below that threshold. Read down the spread column to the first row that qualifies. If
you will report it to the nearest million, which is the more defensible choice given everything
else in this book, the row for a thousand samples already qualifies. The reference run took far
more draws than that.

`samples_needed` in `sizing.mc` turns the law into arithmetic. Give it the run-to-run spread you
measured at some number of draws, and the spread you want; it returns how many draws you need:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: def samples_needed
:end-before: #: Above this ratio
```

### What settling is not

A model whose answer has stopped moving between runs has settled its *arithmetic*. That is all it
has settled.

You can run a model at a million samples, watch the interval stabilise to four significant
figures, and present it with complete confidence, while a whole cost line is missing from the
model. The sampling converged beautifully on the wrong number. Convergence is a statement about
the calculation, never about the thing being calculated. [ch20](#the-missing-node)'s problem 20.3
hands you a model in that state, and an invoice it cannot reach.

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

## Key takeaways

:::{div}
:class: takeaways

- **Inputs that move together must be drawn together.** Drawing a host price and a network price
  independently claims that one can offset the other. It makes the interval of every output both
  prices feed narrower than the evidence supports.
- **Correlate the ranks, not the values.** Reordering the draws expresses the pairing without
  changing the distribution each input was given, and the relation is inverted first so the declared
  strength comes out as written.
- **Correlation between inputs that push the same way widens the interval of every output both of
  them feed.** It is not a refinement. It removes an assumption that made the model look more
  certain than it was.
- **More samples do not narrow an interval.** The width belongs to the inputs. More draws settle
  where the interval is, and the run-to-run spread falls as one over the square root of the number
  of draws.
- **Enough samples is when the answer stops moving at the precision you will report it to, and a
  settled answer has settled its arithmetic and nothing else.** A model can converge beautifully on
  the wrong number.
:::

## Problems

Four. The first two are graded, in `tests/correlation_and_convergence/`. The last two are not,
and say why.

**14.1 — Show the square-root law.**
Write `spread_at` in `stubs.py`. The test hands you the run of the web service model's five-year
total at a sample count and seed; the seeds, the 95th percentile of each run and the spread between
them are yours. The test calls your function at the table's counts from a thousand samples up, and
you return the run-to-run spread; it checks that yours falls by about the square root of ten at
each tenfold step. The tolerance comes from the number of runs at each count, shown in the spread
column's heading; fewer runs would make each spread too noisy to test a ratio of them. The Check
runs the model many times, so expect it to take far longer than the Check under 14.2.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_1_root_n.py -m problem
```

**14.2 — Correlate two inputs, and change neither.**
Below is one entry for a model's `correlations:` block, pairing `host_price` with
`network_price_per_host`. Fill in the rank correlation and the reason. The test adds your entry to
a copy of the web service model with every other correlation removed, and checks five things:

- the entry names the two prices with a rank correlation above zero and below one;
- the 90% interval half-width of the capital cost (`capex`) grows;
- neither price's own distribution moves: each keeps its percentiles;
- the rank correlation measured in the model's draws is the one you declared;
- the `because` says why the two move together.

The third check shows that reordering keeps each input's distribution: adjusting the values
instead would change the percentiles.

```bash
python3 -m pytest tests/correlation_and_convergence/test_problem_2_marginals.py -m problem
```

**14.3 — Two rules about seeds.** No test: the answer is an argument about what an observation
shows, and there is nothing for a test to compute.

[ch13](#monte-carlo) says every result in this book records its seed, and re-running with that
seed gives the same numbers to the last digit. Imagine somebody re-runs the web service model with
its recorded seed several times, gets the same 95th percentile of the five-year total each time,
and concludes by this chapter's definition that the sample count was enough. Say whether that
observation supports the conclusion, and why. Then say what you would change to find out whether
the count was enough, and what result would show the change had worked. Finally, ch13 fixes the
seed and this chapter varies it; say what job each rule does.

A good answer explains what re-running with one seed can and cannot show about sampling noise,
and names what has to differ between runs for their spread to measure anything. It says what the
spread should do as the sample count rises if your change worked, and gives each seed rule a job
in one sentence each. The falsifier is accepting identical re-runs as evidence of settling, or
proposing more draws while keeping the same seed.

**14.4 — Which of your inputs move together.** No test: nothing here can see which of your
quantities move together.

Nothing in this book discovers a correlation; they are all declared. Go through your own inputs in
pairs and find the ones that are not independent: the growth rate and the peak ratio, the price
and the quantity, the compression ratio and the kind of data.

For each pair, say which direction and roughly how strongly. Then say what it does to your answer.
Correlated inputs moving the same way widen the interval of every output they both feed. The table
in "What the correlations bought" above shows it: declaring the correlations widened every row.
Treating them as independent makes the model report less doubt than it has.

A good answer names at least one pair and says whether ignoring it makes your interval too narrow
or too wide. If you find no pairs at all in a chain of six quantities about one system, look
again. Independence is a strong claim. It says that knowing one quantity tells you nothing about
the other.

## Where to go next

Iman and Conover's paper @imanconover1982 is the method in this chapter, and is unusually
readable for a statistics paper of its era. The section on what the method does *not*
guarantee is the part to read twice.

[ch19](#which-input-is-the-answer) is the question this chapter keeps deferring: given that the
interval is wide, which single input should you go and measure?

[ch20](#the-missing-node) is the failure that neither this chapter nor [ch13](#monte-carlo) can
see.

The three functions this chapter quotes from `sizing/mc.py` are quoted in
[Appendix B](#appendix-b-monte-carlo-module) alongside the rest of the module, in the order the
file is written.
