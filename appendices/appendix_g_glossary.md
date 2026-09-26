---
title: "Glossary"
short_title: "Appendix G · Glossary"
---

(appendix-g-glossary)=
# Appendix G · Glossary

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | Words this book uses in a technical sense, each with the chapter introducing it and how to say it plainly |
| **Source** | `bench/tables.py`, and the chapters themselves |
:::

This book rations its vocabulary. The table lists the words this book uses in a technical sense,
each row giving the chapter that introduces the word, what it means in this book, and how to say it
plainly. The rows are in alphabetical order. Six of the words are statistics words: distribution,
sample, percentile, interval, correlation and convergence. Each first appears in the chapter where a
model has just raised a question that needs it. [ch13](#monte-carlo) introduces distribution,
sample, percentile and interval, and [ch14](#correlation-and-convergence) introduces correlation and
convergence. The other words are the book's working vocabulary: capacity-planning terms and the
names of what the book's models contain. A test in the repository fails any page that uses one of
the six before its chapter.

Four kinds of error run through the book, and [ch20](#the-missing-node) sets them side by side in
plain words. A measured constant wobbles: measure it again and it moves, and its standard error says
by how much. An input nobody measured is unknown: its range is a choice, as for a price or a growth
rate. Those two are what an interval is made of, and the model carries both. The world can take a
path the model was not run for: a launch that doubles the busy hour, growth that stops. No interval
covers that. So the book runs a scenario, a second run of the model with some inputs overridden,
instead of widening the inputs.

The model can be the wrong shape: a cost line missing, a ceiling never declared, two quantities
multiplied that should have been added. That is *structural error*. [ch13](#monte-carlo) names it.
It shows up in no interval and no scenario, because nothing in the model file knows the piece is
missing.

The last column is not a simplification. It is the sentence to use out loud. Where a term has a
plain-English equivalent, this book says the plain one first and names the term second, including
to a technical audience, where the effect is not condescension but agreement about what is being
discussed.

```{include} ../chapters/_generated/appendix-g-glossary-terms.md
```

## What the repository calls things

Every stamped result declares a **target**: what was asked to get the number. The four targets
are `corpus`, `rig`, `estate` and `model`. You meet them in [ch03](#where-the-numbers-come-from),
in the table of measured constants, which has a Target column. The words also appear where a
chapter names the evidence a number would need, such as a `rig` measurement that has not been
taken. The table below is generated from the code that stamps results, so it says what the code
says.

```{literalinclude} ../bench/stamp.py
:language: python
:start-at: TARGET_MEANING = {
:end-before: #: What a file *is*.
```

Three of those targets are measurements — something outside this repository was asked a question.
A `model` result is not; it is a computation from the book's own models, evidence about what
those models say and nothing else. A `model` result's fingerprint covers the whole DSL core — the
code that reads, checks, evaluates and samples a model file — so every such figure moves when the
method does. Keeping `model` apart from the other three keeps two things separate: a measurement
of something outside the book, and a computation about the book's own models.

The node kinds (`input`, `derived`, `measured`, `ceiling`) and the provenance kinds (`fact`,
`vendor_claim`, `assumption`) are in [Appendix A](#appendix-a-dsl-reference), where the fields
they carry are quoted alongside them.

## Terms this book does not use

None of these is an oversight. Each one has something the book says instead:

**Confidence interval.** This book reports 90% intervals: the gap between the fifth and the
ninety-fifth percentile of the answers the model produced. A 90% interval is a statement about the
model, not about the world. The statistical term *confidence interval* means something different:
a statement about an estimation procedure repeated over many experiments. Borrowing that name
would import a guarantee this method does not offer. A *prediction interval* is a claim about
where a future observation will fall; that would need a track record, and the book's models do
not have one. The *Over allowed* and *Over limit* columns in a ceiling table report the share of
the model's futures that ended on the wrong side of a declared line — reported as a share, never
as a range — and they are none of those three.

**Expected value.** The mean. Outputs from chains of multiplication in a sizing model are often
skewed, with a long tail on the high side. That tail pulls the mean above the median, so the mean
sits above most of the futures and describes few of them. The output tables in this book report
the point estimate and the 90% interval. When one number has to be handed over,
[ch21](#a-tco-for-finance) makes choosing it a decision said out loud: the median, a high
percentile, or a round number above the median.

**Best case and worst case.** Percentiles, named. A "worst case" is whatever the person saying it
last thought of; the ninety-fifth percentile is a specific claim about a specific model that you
can disagree with. The phrase appears once in this book, as a label in
[ch01](#point-estimates)'s first table, marking the run with every input at its worse value.

**Contingency.** Headroom, with a stated reason and a ceiling it is measured against
([ch11](#headroom-and-failure-domains)). A contingency is a number added at the end to feel safer;
headroom is a margin below a limit that has a name and a consequence.

**Risk**, unqualified. Used here only where a ceiling gives it something to mean: how often,
across the sampled futures, a design is asked to do something it cannot. That number has a row in
a table and a sentence in plain English attached to it.

**Overhead**, unqualified. Every overhead in both reference models is a named node with a unit and
a provenance, because "about twenty per cent overhead" is four different quantities depending on
who is saying it.

**Estimate.** A *point estimate* wherever the book can say so, which names what it is: one number
from one pass through the model with every input at its central value. Not confusing that with the
answer is what the whole book is about.

## Where each term is introduced

The table's second column, *Introduced in*, links each term to the chapter that introduces it. To
read the terms in the book's order, follow the chapter labels in that column. You could read only
those sections, which is quicker than reading the whole book. But you lose something: in the
chapter, each term arrives because a model has just produced a number you cannot yet defend, and a
term is easier to remember with that number beside it.
