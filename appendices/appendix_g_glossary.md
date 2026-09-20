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
| **Purpose** | Every term the book introduces, with the chapter that introduces it |
| **Source** | `bench/tables.py`, and the chapters themselves |
:::

This book rations its vocabulary. Every term below arrives in one chapter, because a model has
just raised a question that needs it, and never as a definition at the front of a section. The
list is short by design: a reader who finishes the book should have gained under twenty words,
not a dialect.

Four of the terms name kinds of error. Read them as a group. Measurement uncertainty and
parameter uncertainty are what an interval is made of. Scenario uncertainty is why this book runs
a model more than once rather than widening its inputs. Structural error is none of those three.
The model is wrong in shape rather than in its numbers, and it is
[ch20 · The missing node](#the-missing-node).

The last column is not a simplification. It is the sentence to use out loud. Where a term has a
plain-English equivalent, this book says the plain one first and names the term second, including
to a technical audience, where the effect is not condescension but agreement about what is being
discussed.

```{include} ../chapters/_generated/appendix-g-glossary-terms.md
```

## What the repository calls things

Four words appear on every stamped number in the book, and they are the ones a reader is most
likely to meet without an introduction. They name **what was asked a question**:

```{literalinclude} ../bench/stamp.py
:language: python
:start-at: TARGET_MEANING = {
:end-before: #: What a file *is*.
```

Three of those are measurements: something outside this repository was asked a question. A
`model` result is not. It is evidence about what this book's models say and about nothing else,
so its fingerprint covers the whole sampler and every figure derived from it moves when the
method does. Keeping it apart from the other three is what stops the distinction going soft.

The node kinds (`input`, `derived`, `measured`, `ceiling`) and the provenance kinds (`fact`,
`vendor_claim`, `assumption`) are in [Appendix A](#appendix-a-dsl-reference), where the fields
they carry are quoted alongside them.

## Terms this book does not use

None of these is an oversight. Each one has something the book says instead:

**Confidence interval.** The intervals in this book are percentile intervals of a sampled output:
the gap between the fifth and ninety-fifth percentiles of the futures the model produced. The
statistical term means something else, a statement about a procedure repeated over experiments,
and borrowing it would import a guarantee this method does not offer.

Four things get called an interval in conversation and only one of them appears in these pages.
A **percentile interval** is what this book reports: two percentiles of the values a model
produced, and a statement about the model rather than about the world. A **confidence interval**
is a statement about an estimation procedure. A **prediction interval** is a claim about where a
future observation will fall, which would require this book's models to have a track record they
do not have. And the **probability a ceiling is breached**, the last column of every ceiling
table, is none of those three. It is the share of the model's futures that ended on the wrong
side of a declared line, which is why it is reported as a share and never as a range.

**Expected value.** The mean. In a sizing model it is usually worse than the median: outputs that
come from chains of multiplication are skewed, so the mean sits above most of the futures and
describes none of them. This book reports the median and says so.

**Best case and worst case.** Percentiles, named. A "worst case" is whatever the person saying it
last thought of; the ninety-fifth percentile is a specific claim about a specific model that
somebody can disagree with.

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

The middle column of the table above links to the chapter that introduces the term and defines it
in context. Reading those sections in order is a shorter path through the book than reading the
book, and a worse one: every term in that list arrives attached to a model that had just produced
a number nobody could defend, and the term is much easier to remember with the number attached.
