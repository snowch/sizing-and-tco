---
title: "Point estimates"
short_title: "ch01 Point estimates"
---

(point-estimates)=
# ch01 · Point estimates

## The question

What is a single number worth, and what can it not tell you, even when the arithmetic is right?

Somebody has asked how big the system needs to be. You can do the arithmetic. That is rarely the
hard part. What comes out is one number, and the number says nothing about how much you would
stake on it.

A single number leaves out two things, and they are not the same thing. The first is the spread
the arithmetic threw away, and [ch13](#monte-carlo) measures it. The second is an error in the
model's shape, and no amount of measuring will find it.

## The material

### A point estimate is not wrong. It is silent.

A **point estimate** is the number you get when you choose one value for every input and do the
arithmetic once. It is what a spreadsheet gives you. It is what almost every sizing conversation
is about. The tables in this book put it in a column with that name.

Think about what goes into one. To size a fleet for a web service you need to know:

- how many requests arrive in the busy hour;
- how fast that grows;
- how much processor time each request takes;
- how much of the data has to stay in memory;
- what a host holds; and
- what a host costs.

Six numbers, and you know none of them exactly. The growth rate is a forecast. The time per
request was measured on somebody else's build. The price is a quote that expires.

Pick the middle of each, multiply along the chain, and you get one number. The arithmetic is
right. But you never had six numbers. You had six ranges, and you threw the ranges away at the
first step.

Multiplying uncertain numbers does not average their doubt out. It compounds it. Each input can be
wrong in the same direction as the others, so the answer stretches further than any single input
does. Problem 1.1 is that arithmetic, done on this book's web service model with nothing but the
spreads the model already declares. The compounded spread is not the widest input's, and it is not
their average.

So the honest answer to *how big* is not a number. It is a range, and some values in it are far
more likely than others. You get the range by doing the arithmetic over and over. Each time you
pick a different value for every input, from the spread that input honestly has, and you keep
every answer that comes out. Here is that for this book's web service: the single number first,
then what the repeated answers did.

```{include} _generated/point-estimates-outputs.md
```

Read the first row. The point estimate is a real number, correctly computed. Beside it are the
smallest and the largest of the answers the same arithmetic gave, and they are not close.
Nothing in the first calculation was wrong. It had no way to say that it was a bet.

The smallest and the largest are a poor summary of the spread, because a handful of extreme
answers set them. The chart below shows where the answers piled up. Every later table
in this book reports a narrower band than this column, and [ch13](#monte-carlo) says which band
and why.

```{image} _figures/point-estimates-tco-spread.svg
:alt: The five-year total cost as a spread of answers, with the single number marked on it
:width: 100%
```

Each bar counts how many of those answers landed on a given five-year total. It is the table's
second row, drawn. Most of the answers sit in the middle, a thin tail runs far to the right, and
the red line is where the single-number answer falls.

Doing that arithmetic over and over needs a program to pick each input's value, and
[ch13](#monte-carlo) builds one. You do not need one to feel the force of it. Problem 1.1 does the
same job on paper: every input at the bottom of its range together, then every input at the top
together. It asks you to set what comes out beside the smallest and largest answer in the table.
Those are two honest ways of admitting the same doubt, and they do not agree with each other.

### The error a range cannot show

Almost all of the first row's width came from one input: the growth rate. It is a forecast, it
compounds over five years, and it moves the host count further than any other input in the model.
Finding that out, rather than guessing it, is [ch19](#which-input-is-the-answer)'s subject. It is
the most useful thing you can do with a model you already have.

The second row moves for different reasons. It is the cost of the fleet somebody decided to buy,
and the growth rate never reaches it. Keeping those two kinds of doubt apart is most of Parts III
and V.

Letting inputs vary and watching what happens is honest work, and most of this book is about
doing it well. But it can only report the doubt somebody wrote down. There is a second kind of
error it cannot see at all. Whether you are exposed to it depends on which of two kinds of model
you have.

**A cost model has a deterministic structure with uncertain parameters.** Its relationships are
accounting identities and physics: watts times hours times price; capital plus running cost over
a horizon; a total divided by a denominator. Nothing in that structure is in doubt. Only the
inputs are uncertain, and the cost moves roughly in proportion to them, so sampling the inputs is
enough. A cost model can be wrong because a price was wrong. It is rarely wrong because the system
it describes started behaving differently.

**A sizing model has the same structure and adds two things.**

*Measured constants.* How much smaller a record is on disk than in memory, once it is compressed.
How many records one request leaves behind when a system is traced. How much work one processor
core gets through in a second. These are measured, not derived. Each belongs to one implementation
at one version, each has a measurement error, and none is a fact about the world. A chain of
multiplications built on them inherits their errors, their version, and their standing as
measurements rather than facts. A model that treats them as constants hides all three.

*Non-linear ceilings.* The queueing knee, where response time climbs steeply while the fleet still
has capacity to spare. A host failing at the busy hour, so that its share of the requests lands
on survivors that were already busy. A new field on a measurement, which multiplies the number of
things you store by however many values the field turns out to take. A working set outgrowing
memory. These are regime changes, and **a chain of multiplications cannot model a regime
change**. It will happily report a system running at several times its own limit, which describes
nothing that can happen.

So a sizing model has to do more than produce a number. It has to say how much room it keeps
below each limit, and why. The toolkit enforces that rather than asking for it. A model with a
measured constant or a declared limit in it **is** a sizing model. One with neither **is** a cost
model. The two are held to different rules, and a sizing model that names a limit and keeps no
room below it does not build.

### Where the kind changes

You do not have to take the distinction on trust, and you should not. It decides which half of
this book applies to what you are holding. The web service model starts as a cost model and
becomes a sizing model partway through being built, and the node that changes it can be named.
Problem 1.2 is finding it, on the same model at six stages of construction.

Nobody declares the change. It happens when you add a measured constant or a ceiling to the file,
and the toolkit works the rest out. That is why the stage is worth finding rather than being told,
and why this page does not tell you.

:::{note} Key takeaways
- **A point estimate is silent, not wrong.** One value per input and the arithmetic done once gives
  a correct number that says nothing about how far it could be out.
- **Doubt compounds along a chain.** Multiplying uncertain numbers stretches the answer further than
  any single input does, so the honest answer to *how big* is a range with a most-likely region in
  it, not a figure.
- **A range reports only the doubt somebody wrote down.** An error in the model's shape is invisible
  to any amount of varying the inputs.
- **Two kinds of model, held to two rules.** A cost model has a structure nobody doubts and
  uncertain inputs. A sizing model adds measured constants and ceilings, and has to say how much
  room it keeps below each limit.
- **The kind is read from the file, never declared.** A measured constant or a declared limit makes
  a sizing model, and the toolkit works that out from what is in the model.
:::

## What this cannot tell you

**What the model's structure omits.** Everything above is about a model that has already been
written down. A quantity nobody thought of appears in no point estimate, no range and no
ceiling, and no amount of sampling will put it there. This book's observability model has a hole
of that shape, argued in [Appendix F](#appendix-f-observability-model).
[ch23](#what-the-model-got-wrong) is a post-mortem on a model that was confidently wrong for this
reason.

**Whether the spread anybody declared is the right spread.** The range above faithfully reports
the spreads in the model file. If the growth rate's spread was somebody's mood on a Tuesday, the
range inherits that and says nothing about it. [ch03](#where-the-numbers-come-from) is about
telling a measurement from a claim from a guess. That difference decides whether a range is a
finding or a decoration.

**How much the range should worry you.** A wide range on a number nobody will act on for a
year is not a problem. A narrow one on a purchase order signed on Friday might be. Nothing in the
arithmetic knows which you have, and this book has no opinion about your appetite for risk.
[ch21](#a-tco-for-finance) is about handing somebody a range and the decision it supports,
instead of hiding the doubt inside a single figure.

## Problems

Three, in `tests/point_estimates/`. The first two have tests; run them with
`python3 -m pytest tests/point_estimates/`. The third does not, and says why.

**1.1 — The width of a product.** Read each uncertain input's declared spread off the web service
model. Work out what those spreads become when the inputs are multiplied together. The answer is
neither the widest input nor the average of them. Do it the way you could on paper: every input at
its low together, then every input at its high together. Then set your answer beside the
smallest and largest answer in the table above. The gap between the two is what
[ch13](#monte-carlo) exists to close.

```bash
python3 -m pytest tests/point_estimates/test_problem_1_compounding.py
```

**1.2 — Find where it changes kind.** The web service model appears at six stages of being built.
Classify each stage as a cost model or a sizing model, and name the nodes that decide it. Then
say, in one sentence and to yourself, why the chapter that adds those nodes could not have been
written earlier.

```bash
python3 -m pytest tests/point_estimates/test_problem_2_which_kind.py
```

**1.3 — Your own system.** No test. There is no oracle for this, and pretending otherwise would be
worse than leaving it ungraded.

Take a system you run. Write down the three to six numbers that decide how big it has
to be. Not everything you know about it: the ones that would change the answer. Beside each, write
where it came from: something you measured, something a supplier told you, or something you
decided.

Then answer two questions. Which of them, if it turned out to be wrong by half, would change what
you would buy? And is there a constant in your list that somebody measured on a particular version
of a particular piece of software, or a limit your system runs into before it runs out of
capacity? If there is, you are holding a sizing model, and the chain of multiplications you have
been using is quietly lying to you.

A good answer is short, names its sources, and is uncomfortable in at least one place. If nothing
in it is uncomfortable, you have probably written down the numbers you can measure easily rather
than the ones that decide the answer. Keep it. Every chapter in this book ends with a problem
about a system you run, and this is the first of them. They work best on the same one.

## Where to go next

[ch02](#what-a-workload-is) starts the model this chapter has been quoting from. It writes the
first nodes. By the end you have a file that computes a busy hour and a data volume at the
horizon, and refuses to get there by multiplying a rate by a plain number.

[ch03](#where-the-numbers-come-from) is the question this chapter kept deferring: once you have
written a number down, what are you claiming about it?
