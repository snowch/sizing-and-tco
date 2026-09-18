---
title: "What one number hides"
short_title: "ch01 What one number hides"
---

(what-one-number-hides)=
# ch01 · What one number hides

## The question

What is a single number worth, and what can it not tell you even when the arithmetic is right?

Somebody has asked how big the system needs to be. You can do the arithmetic; that is rarely the
hard part. What comes out is one number, and that number tells you nothing about how much you
would be willing to stake on it. This chapter is about the two things it leaves out, and they are
not the same thing: one of them a later chapter measures, and the other no amount of measuring
will find.

## The material

### A point estimate is not wrong. It is silent.

A **point estimate** is the number you get by choosing one value for every input and doing the
arithmetic once. It is what a spreadsheet gives you, and it is what almost every sizing
conversation is about. The tables in this book put it in a column of that name.

Think about what goes into one. To size a storage cluster you need to know how much data arrives,
how fast that grows, how well it compresses, how many copies you keep, what a drive holds and what
a drive costs. Six numbers, and you know none of them exactly. The growth rate is a forecast. The
compression ratio was measured on somebody else's data. The price is a quote that expires.

Pick the middle of each, multiply along the chain, and you get one number. The arithmetic is
right. But you never had six numbers — you had six ranges, and you threw the ranges away at the
first step.

Worse, multiplying uncertain quantities does not average their doubt out. It compounds it. Each
one can be wrong in the same direction as the others, and the answer stretches further than any
single input does. Problem 1.1 is that arithmetic, done on this book's storage model with nothing
but the widths the model already declares: the compounded width is not the widest input, and it is
not their average.

So the honest answer to *how big* is not a number. It is a range, with some values in it far more
likely than others. You get one by doing the arithmetic over and over — each time picking a
different value for every input, from the spread that input honestly has — and keeping every
answer that comes out. Here is that for this book's storage cluster: the single number first, and
then what the repeated answers did.

```{include} _generated/what-one-number-hides-outputs.md
```

Read the first row. Its point estimate is a real number, correctly computed — and beside it the
**90% interval**, the range nine of those answers in ten fell into, spans most of an order of
magnitude. Nothing in the first calculation was wrong. It simply had no way to mention that it
was a bet.

Why nine in ten, rather than the smallest and largest answers? Because the smallest and largest
are not properties of the problem. They are properties of how many answers you collected: collect
ten times as many and the largest gets larger, every time, because you gave the unlucky
combinations more chances to turn up. The ends drift. The middle settles, and settles quickly
enough to be worth quoting. Ninety per cent is then a convention, and this book uses the same one
everywhere so that two figures can be compared.

```{image} _figures/what-one-number-hides-tco-distribution.svg
:alt: The five-year total cost as a distribution, with the point estimate marked on it
:width: 100%
```

Each bar counts how many of those answers landed on a given five-year total — the table's second
row, drawn — and the red line is where the single-number answer falls.

The method that produced the interval is [ch13](#monte-carlo)'s, not this chapter's. It is no use
to you until you have built a model, got a number out of it, and felt that you could not defend
the number. Problem 1.1 deliberately does the crude version instead, and the crude version is
wrong in a way worth seeing early.

### The error an interval cannot show

Almost all of that width came from one input. The growth rate is a forecast, it compounds over
five years, and it moves the answer further than everything else in the model put together.
Finding that out rather than guessing it is [ch19](#which-input-is-the-answer)'s subject, and it
is the most useful thing you can do with a model you already have.

Letting inputs vary and watching what happens is honest work, and most of this book is about
doing it well. But it can only ever report the doubt somebody wrote down. There is a second kind
of error it cannot see at all, and which of two kinds of model you have decides whether you are
exposed to it.

**A cost model has a deterministic structure with uncertain parameters.** Its relationships are
accounting identities and physics: watts times hours times price, capital plus running cost over
a horizon, a total divided by a denominator. Nothing in that structure is in doubt. Only the
inputs are uncertain, cost scales roughly in proportion to them, and sampling the inputs is
genuinely sufficient. A cost model can be wrong because a price was wrong. It is rarely wrong
because the system it describes started behaving differently.

**A sizing model has the same structure and adds two things.**

*Measured constants.* How many bytes a stored measurement takes once it is compressed. How many
records one request leaves behind when a system is traced. How much work a single processing core
gets through in a second. These are empirical, they belong to a particular implementation at a
particular version, they have measurement error, and none of them is a fact about the world. A
chain of multiplications built on them inherits every one of those properties, and a model that
treats them as constants hides them all.

*Non-linear ceilings.* The queueing knee, where response time climbs steeply while a device still
has capacity to spare. Rebuild under failure, where losing one machine costs capacity you were
using. A new field attached to a measurement, which multiplies how many separate things you have
to store by however many values that field turns out to take. A working set outgrowing memory.
These are regime changes, and **a chain of multiplications cannot model a regime change**. It will
happily report that a system is running at several times its own limit, which is not a description
of anything that can happen.

So a sizing model has to say how much room it keeps below each limit, and why, rather than only
producing a number. This repository enforces that rather than asking for it: a model with a
measured constant or a declared limit in it **is** a sizing model, one with neither **is** a cost
model, and the build holds the two to different rules. A sizing model that names a limit and keeps
no room below it does not build.

### Where the kind changes

You do not have to take the distinction on trust, and you should not, because it decides which
half of this book applies to what you are holding. The storage model starts as a cost model and
becomes a sizing model partway through being built, and the exact node that does it is nameable.
Problem 1.2 is finding it, on the same model at five stages of construction.

That is also why the change is worth watching rather than being told: nobody declares it. It
happens because two nodes get added, in [ch09](#capacity) and [ch10](#bandwidth-and-the-binding-constraint), and the build notices.

## What this cannot tell you

**What the model's structure omits.** Everything above is about a model that has already been
written down. A quantity nobody thought of does not appear in a point estimate, an interval, or
a ceiling, and no amount of sampling will introduce it. This book's observability model has a hole
in it of exactly that shape, argued in [Appendix F](#appendix-f-observability-model), and
[ch22](#what-the-model-got-wrong) is a post-mortem on a model that was confidently wrong for this
reason.

**Whether the spread anybody declared is the right spread.** The interval above is a faithful
report of the distributions in the model file. If the growth rate's range was somebody's mood on
a Tuesday, the interval inherits that and says nothing about it. [ch03](#where-the-numbers-come-from)
is about telling a measurement from a claim from a guess, and it is the chapter that makes this
one worth anything.

**How much the interval should worry you.** A wide interval on a number nobody will act on for a
year is not a problem. A narrow one on a purchase order signed on Friday might be. Nothing in the
arithmetic knows which you have, and this book has no opinion about your risk appetite —
[ch21](#a-tco-for-finance) is about handing somebody an interval and the decision it
supports, rather than hiding the doubt inside a single figure.

## Problems

Three, in `tests/what_one_number_hides/`. The first two have tests; run them with
`python3 -m pytest tests/what_one_number_hides/`. The third does not, and says why.

**1.1 — The width of a product.** Read each uncertain input's declared spread off the storage
model, and work out what those spreads become when the quantities are multiplied together. The
answer is neither the widest input nor the average of them. It is also, deliberately, the crude
version of the calculation — assuming every input is at its low together and then at its high
together — and comparing it with the interval in the table above will tell you something about
how much [ch13](#monte-carlo) is actually buying.

```bash
python3 -m pytest tests/what_one_number_hides/test_problem_1_compounding.py
```

**1.2 — Find where it changes kind.** The storage model appears at five stages of being built.
Classify each as a cost model or a sizing model, and name the nodes that decide it. Then say, in
one sentence and to yourself, why the chapter that adds those nodes could not have been written
earlier.

```bash
python3 -m pytest tests/what_one_number_hides/test_problem_2_which_kind.py
```

**1.3 — Your own system.** No test, because there is no oracle for this and pretending otherwise
would be worse than leaving it ungraded.

Take something you actually run. Write down the three to six quantities that decide how big it
has to be — not everything you know about it, the ones that would change the answer. Beside each,
write where the number came from: something you measured, something a supplier told you, or
something you decided. Then answer two questions. Which of them, if it turned out to be wrong by
half, would change what you would buy? And is there a constant in your list that somebody measured
on a particular version of a particular piece of software, or a limit your system runs into before
it runs out of capacity — because if there is, you are holding a sizing model and the chain of
multiplications you have been using is quietly lying to you.

A good answer is short, names its sources, and is uncomfortable in at least one place. If nothing
in it is uncomfortable, you have probably written down the quantities you can measure easily
rather than the ones that decide the answer. You will be able to check the second half of it
properly by [ch12](#the-sizing-model), and the first half by [ch19](#which-input-is-the-answer).

## Where to go next

[ch02](#what-a-workload-is) starts the model this chapter has been quoting from. It writes the
first nodes of it, and by the end of that chapter you have a file that runs and cannot yet tell
you anything you did not type into it — which is the honest place to begin.

[ch03](#where-the-numbers-come-from) is the question this chapter kept deferring: given that you
have written a quantity down, what are you actually claiming about it?
