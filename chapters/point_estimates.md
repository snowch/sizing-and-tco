---
title: "Point estimates"
short_title: "ch01 Point estimates"
---

(point-estimates)=
# ch01 · Point estimates

## The question

What is a single number worth, and what can it not tell you, even when the arithmetic is right?

You have been asked how many hosts to buy for a service that does not exist yet, and the order
goes in this week. So you multiply: requests in the busy hour, processor time each one takes,
how many cores a host has.

Not one of those three is a single number. Traffic has grown at a different rate every year for
the last three, and you have not chosen a host yet. So for each one you take the middle value,
which is what almost anybody would do. The arithmetic is not the hard part. What comes out is
one number, and nothing in it tells you whether it is a number to sign for.

Two things are missing from that number.

1. **The ranges those middles replaced.** Each middle went into the arithmetic as though
   somebody had gone and measured it, and what came out carries no trace of the range it came
   from. [ch13](#monte-carlo) is where you hand the model the whole of each range instead of its
   middle, and get a range of answers back.
2. **An error in the shape of the model.** Multiplying cannot notice that a queue has tipped
   over. The answer comes back describing a fleet running at several times the load it can
   carry, in the same flat tone as everything else. Measuring the inputs better never finds this
   one.

Here is the first of the two, on the web service this book sizes. The mark near the top is the
sums done once. The pile underneath it is the same sums done again and again, with every input
free to move between the two ends somebody wrote down for it:

```{image} _figures/point-estimates-once-and-many.svg
:alt: The single number marked above the pile of answers the same arithmetic gave, with the single number low in the pile rather than in the middle of it
:width: 100%
```

Nothing changed between the mark and the pile except what the inputs were allowed to do. More
than half the answers came out above the single number, and a long tail of them runs off to the
right: futures that need a fleet several times the size. A single number shows none of that —
not how wide the pile is, not where in it you are standing, and not the tail. The tail is the
part that costs money, because those are the futures that need a fleet you did not buy.

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
- how many cores, how much memory and how much disk one host has; and
- what a host costs.

Six numbers, and you know none of them exactly. The growth rate is a forecast. The time per
request was measured on somebody else's build. The price is a quote that expires.

Pick the middle of each, multiply them together, and you get one number. The arithmetic is
right. But you never had six numbers. You had six ranges, and you threw the ranges away at the
first step.

Multiplying uncertain numbers does not average their doubt out. It compounds it.

Say each of them could be a fifth higher than the figure you wrote down.

```{image} _figures/point-estimates-compounding.svg
:alt: How far the answer moves when one, two, three or more inputs are each a fifth high
:width: 100%
```

Two inputs a fifth high do not make the answer a fifth high. They make it nearly half as much
again, because the errors multiply instead of taking turns. By six — which is what the fleet in
this chapter rests on — the answer has tripled, and no single input moved by more than a fifth.
Nothing cancels, because nothing made these inputs disagree with each other.

Problem 1.2 is that arithmetic, done on this book's web service model with nothing but the spreads
the model already declares. The compounded spread is not the widest input's, and it is not their
average.

So the honest answer to *how big* is not a number. It is a range, and some values in it are far
more likely than others.

You get that range by doing the arithmetic over and over. Doing a sum twice is pointless if
nothing changes between the two, so something has to. Each time, you pick a different value for
every input. Not any value: one drawn from the spread that input honestly has, so a value from
the fat middle of the spread comes up often and one from the edge comes up rarely. Then you keep
the answer and go again.

A spread is the part of the model file that says how wrong one input might be.

```{include} _generated/point-estimates-a-spread.md
```

One run answers one question — *what if it turns out like this?* Enough runs answer a different
one: *which outcomes keep coming up, and which barely ever do?* The second question is the one
you need answered before you commit to a fleet.

The service in question is the one this book carries the whole way through. It answers requests
and keeps the records they leave behind. It runs on a fleet of hosts somebody has to buy, and then
pay to run for five years. You need nothing else about it yet: [ch02](#what-a-workload-is) builds
its file a few nodes at a time, and [Appendix E](#appendix-e-web-service-model) shows the finished
thing.

Rather than take that on trust, do it. Press the button below. Every uncertain input the host
count rests on jumps to the value that future brought, the fleet is worked through once, and the
answer drops onto the pile. Press it again and you get a different answer, because you asked a
different question. What a host costs is not among them: the price cannot change how many you
need.

```{iframe} /futures/point-estimates.html
:width: 100%
One press is one future. The ticks under each input pile up where its shape is fat, which is what
*drawn from the spread it honestly has* looks like.
```

A dozen presses is enough to see that the answers are not scattered evenly. Press it fifty
times, or use *Draw 100* once: the shape does not appear until the pile is deep, and the shape
is the whole of the argument.

Here is the same model's answer as the book's own run computed it, the single number first, then
what its repeated answers did.

```{include} _generated/point-estimates-outputs.md
```

Read the first row. The point estimate is a real number, correctly computed. Beside it are the
smallest and the largest of the answers the same arithmetic gave, and they are not close.
Nothing in the first calculation was wrong. It had no way to say that it was a bet.

That second column is not the model admitting it is useless. It is the lowest and the highest
single answer in the whole run — one draw each, and it takes most of the inputs going the same
way at once to produce either. Almost nothing lands near either end. What you would size a fleet
from is where the answers piled up, which the chart below shows and the two ends cannot.

```{image} _figures/point-estimates-tco-spread.svg
:alt: The five-year total cost as a spread of answers, with the single number marked on it
:width: 100%
```

Each bar counts how many of those answers landed on a given five-year total. It is the table's
second row, drawn. Most of the answers sit in the middle, and a thin tail runs far to the right.

The height of a bar means something only because of how the values were picked. Each input was
drawn in proportion to its own spread: a value the file says is common was picked often, one the
file says is rare was picked rarely. So a total that turns up in many of the answers is one that
many combinations of plausible inputs produce, and a total that turns up in few is one that
needs an unlikely combination. Had the values been picked evenly across each range instead, the
pile would be a record of what was tried and would say nothing about what to expect.
The red line is where the single-number answer falls.

The frame above picks the values and does the arithmetic for you, one press at a time.
[ch13](#monte-carlo) is where you build the thing that does it in bulk, and turn a pile of answers
into a figure you can put in a document. Problem 1.2 needs neither. It does the same job on paper:
every input at the bottom of its range together, then every input at the top together. It asks you
to set what comes out beside the smallest and largest answer in the table. Those are two honest
ways of admitting the same doubt, and they do not agree with each other.

### The error a range cannot show

Everything so far has been about how wide the answer is. The rest of this chapter is about a
different error, one that running the arithmetic again cannot find however many times you run
it, and which decides whether your model needs the second half of this book at all.

Almost all of the first row's width came from one input: the growth rate. It is a forecast, it
compounds over five years, and it moves the host count further than any other input in the model.
Finding that out, rather than guessing it, is [ch19](#which-input-is-the-answer)'s subject. It is
the most useful thing you can do with a model you already have.

The second row moves for different reasons. It is the cost of the fleet somebody decided to buy,
and the growth rate never reaches it. So you can be badly wrong about how many hosts the service
will need and exactly right about what the fleet you bought will cost. One is a question about the
world. The other is arithmetic on a decision already taken. Keeping those two kinds of doubt apart
is most of Parts III and V.

Letting inputs vary and watching what happens is honest work, and most of this book is about
doing it well. But it can only report the doubt somebody wrote down. There is a second kind of
error it cannot see at all. Whether you are exposed to it depends on which of two kinds of model
you have.

**A cost model has a deterministic structure with uncertain parameters.** Its relationships are
accounting identities and physics: watts times hours times price; capital plus running cost over
a horizon; a total divided by a denominator. Nothing in that structure is in doubt. Only the
inputs are uncertain, and the cost moves roughly in proportion to them, so running the arithmetic
over their ranges is enough. A cost model can be wrong because a price was wrong. It is rarely wrong because the system
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
change**. It reports a system running at several times its own limit, which describes nothing
that can happen.

So a sizing model has to do more than produce a number. It has to say how much room it keeps
below each limit, and why. The toolkit enforces that rather than asking for it. A model with a
measured constant or a declared limit in it **is** a sizing model. One with neither **is** a cost
model. The two are held to different rules, and a sizing model that names a limit and keeps no
room below it does not build.

### Where a cost model becomes a sizing model

You do not have to take the distinction on trust, and you should not. It decides which half of
this book applies to what you are holding. The web service model starts as a cost model and
becomes a sizing model partway through being built. One node makes the change, and it can be
named. Problem 1.3 is finding it, on the same model at six stages of construction.

You find the stage rather than being told it, which is why this page does not name the node.

:::{note} Key takeaways
- **A point estimate is silent, not wrong.** One value per input and the arithmetic done once gives
  a correct number that says nothing about how far it could be out.
- **Doubt compounds along a chain of multiplications.** Multiplying uncertain numbers stretches
  the answer further than any single input does, so the honest answer to *how big* is a range with
  a most-likely region in it, not a figure.
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
ceiling, and no amount of running the arithmetic again will put it there. This book's observability model has a hole
of that shape, argued in [Appendix F](#appendix-f-observability-model).
[ch23](#what-the-model-got-wrong) is a post-mortem on a model that was confidently wrong for this
reason.

**Whether the spread anybody declared is the right spread.** The range above faithfully reports
the spreads in the model file. If the growth rate's spread was a guess nobody checked, the range
inherits the guess and says nothing about it. [ch03](#where-the-numbers-come-from) is about
telling a measurement from a claim from a guess. That difference decides whether a range is a
finding or a decoration.

**How much the range should worry you.** A wide range on a number nobody will act on for a
year is not a problem. A narrow one on a purchase order signed on Friday might be. Nothing in the
arithmetic knows which you have, and this book has no opinion about your appetite for risk.
[ch21](#a-tco-for-finance) is about handing somebody a range and the decision it supports,
instead of hiding the doubt inside a single figure.

## Problems

Four, in `tests/point_estimates/`. The first three have tests; run them with
`python3 -m pytest tests/point_estimates/ -m problem`. The fourth does not, and says why.

**1.1 — How wide is one input?** The test hands you the band the model declares for each of the
six inputs above, so you do not need to go and read the file. Write each band as its top over its
bottom. Six divisions, and none of them is alarming.

```bash
python3 -m pytest tests/point_estimates/test_problem_1_each_input.py -m problem
```

**1.2 — How wide are they together?** Now do the arithmetic the way you could on paper: every one
of those six at the bottom of its band together, then every one at the top together, with the
hosts the model recommends worked through both times. The second count over the first is neither
the widest band from 1.1 nor the average of them. Set it beside the smallest and largest answer in
the table above. The gap between the two is what [ch13](#monte-carlo) exists to close.

```bash
python3 -m pytest tests/point_estimates/test_problem_2_together.py -m problem
```

**1.3 — Find where it changes kind.** The web service model appears at six stages of being built.
Classify each stage as a cost model or a sizing model, and name the nodes that decide it. Then
say, in one sentence and to yourself, why the chapter that adds those nodes could not have been
written earlier.

```bash
python3 -m pytest tests/point_estimates/test_problem_3_which_kind.py -m problem
```

**1.4 — Your own system.** No test. There is no oracle for this, and pretending otherwise would be
worse than leaving it ungraded.

Take a system you run. Write down the three to six numbers that decide how big it has
to be. Not everything you know about it: the ones that would change the answer. Beside each, write
where it came from: something you measured, something a supplier told you, or something you
decided.

Then answer two questions. Which of them, if it turned out to be wrong by half, would change what
you would buy? And is there a constant in your list that somebody measured, on one version of one
piece of software? Or a limit your system meets before it runs out of capacity? If there is, you
are holding a sizing model, and the chain of multiplications you have been using is quietly lying
to you.

**A good answer is short, names its sources, and is uncomfortable in at least one place.** If
nothing in it is uncomfortable, you have probably written down the numbers you can measure
easily rather than the ones that decide the answer. Keep it. Every chapter in this book ends with a problem
about a system you run, and this is the first of them. They work best on the same one.

## Where to go next

[ch02](#what-a-workload-is) starts the model this chapter has been quoting from. It writes the
first nodes. By the end you have a file that computes a busy hour and a data volume at the
horizon. It refuses to get there by multiplying a rate by a plain number.

[ch03](#where-the-numbers-come-from) is the question this chapter kept deferring: once you have
written a number down, what are you claiming about it?
