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
list is short by design: a reader who finishes the book should have gained about a dozen words,
not a dialect.

The last column is not a simplification. It is the sentence to use out loud. Where a term has a
plain-English equivalent, this book says the plain one first and names the term second — including
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

Three of those are measurements: something outside this repository was asked. The fourth is not,
and keeping it separate is what stops the distinction going soft. A `model` result is evidence
about what this book's models say and about nothing else — so its fingerprint covers the whole
sampler, and every figure derived from it moves when the method does.

The node kinds — `input`, `derived`, `measured`, `ceiling` — and the provenance kinds — `fact`,
`vendor_claim`, `assumption` — are in [Appendix A](#appendix-a-dsl-reference), where the fields
they carry are quoted alongside them.

## Terms this book does not use

Not an omission in each case. A short account of what it says instead:

**Confidence interval.** The intervals in this book are percentile intervals of a sampled output:
the gap between the fifth and ninety-fifth percentiles of the futures the model produced. The
statistical term means something else — a statement about a procedure repeated over experiments —
and borrowing it would import a guarantee this method does not offer.

**Expected value.** The mean, and in a sizing model the mean is usually the worse summary. Outputs
that come from chains of multiplication are skewed, so the mean sits above most of the futures and
describes none of them. This book reports the median and says so.

**Best case and worst case.** Percentiles, named. A "worst case" is whatever the person saying it
last thought of; the ninety-fifth percentile is a specific claim about a specific model that
somebody can disagree with.

**Contingency.** Headroom, with a stated reason and a ceiling it is measured against
([ch11](#headroom-and-failure-domains)). A contingency is a number added at the end to feel safer;
headroom is a margin below a limit that has a name and a consequence.

**Risk**, unqualified. Used here only where a ceiling gives it something to mean: how often, across
the sampled futures, a design is asked to do something it cannot. That number has a row in a table
and a sentence in plain English attached to it.

**Overhead**, unqualified. Every overhead in both reference models is a named node with a unit and
a provenance, because "about twenty per cent overhead" is four different quantities depending on
who is saying it.

**Estimate.** Where possible: a *point estimate*, which names what it is — one number from one
pass through the model with every input at its central value, and the thing the whole book is
about not confusing with the answer.

## Where each term is introduced

The middle column of the table above links to the chapter that introduces the term and defines it
in context. Reading those sections in order is a shorter path through the book than reading the
book, and a worse one: every term in that list arrives attached to a model that had just produced
a number nobody could defend, and the term is much easier to remember with the number attached.
