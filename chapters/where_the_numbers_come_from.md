---
title: "Where the numbers come from"
short_title: "ch03 Where the numbers come from"
---

(where-the-numbers-come-from)=
# ch03 · Where the numbers come from

## The question

What is the difference between a number you measured, a number you were told, and a number you
decided?

Once they are all cells in the same column, none. That is the problem.

## The material

### Three claims, wearing the same clothes

Every input in this book declares which of three things it is.

**`fact`**: traceable to something. A stamped measurement, an invoice, a published specification.
The toolkit refuses a `fact` whose source cites nothing. An assumption wearing a better label is
worse than an assumption.

**`vendor_claim`**: stated by somebody selling it. Often true. Never checked here. It is coloured
differently in every figure it appears in, and it is never quietly promoted. The moment a quoted
throughput becomes "the throughput" in somebody's head, the model has acquired a fact it never
earned.

**`assumption`**: a decision this model makes. Naming it as one is what lets a reviewer argue with
it. An assumption nobody can find is not a weaker claim than a measurement. It is a stronger one,
because nothing can dislodge it.

### The first number somebody else supplied

Every quantity in [ch02](#what-a-workload-is)'s file came from you or from the application: how
many requests arrive, how much is held, how fast both grow, how long the fleet has to last. The
next one does not. How much memory a host carries is decided by whoever sells it. This is the
form that takes:

```{literalinclude} ../models/web_service/stages/02-provenance/model.yaml
:language: yaml
:start-at: ram_per_host:
:end-before: os_reserve:
```

Two clauses of source, and the second one earns its place. *The sheet says gigabytes and means
gibibytes* is the gap between what a spec sheet writes and what it counts. It is only the first
of two gaps between the number on the sheet and the memory a service gets
([Appendix D](#appendix-d-units)). Writing that down is the whole of the discipline. The claim is
recorded as a claim, and what is doubtful about it is recorded beside it.

It takes one more quantity to reach the first node in the model that is about hardware rather
than data: the share of that memory the operating system keeps for itself, an assumption in the
plainest sense of the word.

```{include} _generated/where-the-numbers-come-from-stage.md
```

```{include} _generated/where-the-numbers-come-from-stage-shape.md
```

Three nodes on from [ch02](#what-a-workload-is)'s graph, and the new one at the end is the first
in the model that is about hardware. Click *ram per host* to see whose claim it is.

```{iframe} /models/web_service_provenance-reference.html
:width: 100%
The graph as ch03 leaves it. The vendor's claim is a node like any other, and says so when clicked.
```

```{iframe} /playground/where-the-numbers-come-from/
:width: 100%
The same file, with the vendor's claim in it. Change the `provenance` of a node and run it again.
```

Still a cost model. A vendor's claim is a claim about a number. This book's distinction is not
about who said a number. It is about whether the arithmetic around it stops applying somewhere,
and [ch06](#queueing-and-the-knee) is where that changes.

### Three claims, counted

Here is the census of the running example as this chapter leaves it. It is short, and one row of
it is the claim above:

```{include} _generated/where-the-numbers-come-from-service-provenance.md
```

And here is the same census of the book's second model, the observability platform, which has all
three kinds of claim among its inputs:

```{include} _generated/where-the-numbers-come-from-provenance.md
```

The tally at the bottom is the honest summary of any model, and for most models it is not
flattering. That is fine. Not knowing is not.

### A measured constant is not a fact about the world

A compression ratio is not a property of compression. It is a property of *some data* and *some
software at some version*, and it moves when either changes. So do bytes per sample, spans per
request, and throughput per core. This book calls those **measured constants** and gives them
their own node kind. Every one of them carries the implementation it belongs to:

```{include} _generated/where-the-numbers-come-from-constants.md
```

Read the last column. One of those constants was produced by an encoder that lives in this
repository: this book's own, byte-aligned, and therefore worse than a production format that packs
bits. The figure is correct, and it is about that encoder. Anybody who copied it into a model of a
real system would be wrong by a factor nobody would ever find.

The method is what transfers. The number does not.

### Four targets, and only two of them are yours to take

| Target | What it is | Who can check it |
|---|---|---|
| `corpus` | a codec or an encoder over a declared body of data | anybody with the repository |
| `model` | a model file evaluated and sampled | anybody with the repository |
| `rig` | a throughput or a latency, on the declared reference machine | whoever has that machine |
| `estate` | an observation of a system somebody runs | **nobody** |

The first two are cheap, and the book is full of them. The third is refused on any machine that
is not the declared one, because a throughput measured on whatever machine was free is
indistinguishable from a real one once it is a number in a table.

The fourth cannot be checked by anybody at all.

### The target nobody can check

An observation of a running system cannot be reproduced by anybody, including you, next Tuesday.
There is no corpus to re-run and no machine to re-run it on. The system has moved on.

So `estate` is held to the strictest disclosure rules in the book: what system, over what window,
observed when. That disclosure is the *whole* of its verification. There is nothing else. When a
page uses one, it says so at the point of use rather than in a footnote. A reader is entitled to
know which numbers on a page rest on somebody's word.

This is not a hole in the scheme. It is the honest bottom of it. Some quantities can only be known
by watching a real system, and pretending otherwise would be worse than admitting it.

### When nobody has measured it

```{include} _generated/where-the-numbers-come-from-measured.md
```

Two rows there say *not yet measured*. One needs a reference machine nobody has attached. The
other needs somebody's instrumented application.

The node has no value, so nothing downstream of it has a value either. The state propagates down
the graph without anybody marking anything:

```{include} _generated/where-the-numbers-come-from-unmeasured.md
```

No placeholder. No estimate. No number borrowed from a different stack and quietly rounded. The
figures that depend on those constants are absent, and the box says which constants and what would
close them.

That is inconvenient on purpose. A placeholder is indistinguishable from a measurement after one
copy-paste, and every organisation has a capacity plan built on one.

### The rig, and why the book will not let you fake it

```{include} _generated/where-the-numbers-come-from-rig.md
```

The machine this was written on refuses to produce that figure, and not by convention: the
toolkit compares the running processor and core count against the declared reference machine
and refuses otherwise.

An environment variable would have been easier. It would also have let anybody stamp a laptop
timing as a reference measurement by typing four characters. A target you can set by accident is
not worth having.

### What a measurement is worth

One measurement is a number. It says nothing about how far it would move if you did it again. So
every constant in this book is measured over several independently generated shards, and reported
as a mean with the standard error of that mean beside it.

That standard error becomes the measured node's uncertainty, and [ch13](#monte-carlo) propagates
it through the model like any other. A constant stamped without one is claiming to have been
measured exactly, and the toolkit says so.

A standard error also tells you what more measuring would buy, which is usually less than people
expect. It falls as one over the square root of the count, so halving it costs four times the
work. Problem 3.2 is that arithmetic. It is worth doing *before* agreeing to a measurement
campaign rather than during one.

## What this cannot tell you

**Whether a corpus resembles your data.** Every constant above was measured over a body of data
this repository generates, and the generator's proportions are an assumption stated in the
stamped result. For the record compression ratio, the mix of record kinds in that corpus is the
single largest source of error in the figure. It is larger than the codec, and larger than the
shard-to-shard spread the result reports. The number has a standard error, and the standard error
is about the wrong thing.

**Whether a `vendor_claim` is true.** Nothing here checks one. They are marked so that a reader
can see how much of a model rests on them, and that is all. Where a vendor's number and a measured
one exist side by side, [Appendix F](#appendix-f-observability-model) shows both. Where only the
claim exists, that is what you have.

**Whether an `estate` observation happened.** It is somebody's word, with a disclosure attached.
The book's position is that saying so plainly is better than the alternative, not that it is good.

**Whether an assumption is reasonable.** The provenance census counts them. It does not read them.
A model can be all assumptions, all sourced, all defensible-sounding, and completely wrong.

## Problems

Three, in `tests/where_the_numbers_come_from/`. The first two have tests. The third does not, and says why.

**3.1 — Take a constant, and stamp it so somebody else could check it.**
Pick a quantity a codec decides, measure it over a corpus you generate deterministically, and
produce a stamped payload that satisfies every rule in `bench.stamp.provenance_problems`: corpus,
codec, units with no time in them, and a standard error that came from somewhere.

```bash
python3 -m pytest tests/where_the_numbers_come_from/test_problem_1_measure.py
```

**3.2 — What would it cost to be more sure?**
Given a standard error at some number of shards, work out how many shards a target would need.
Halving your uncertainty costs four times the measuring, and knowing that before the campaign is
worth more than knowing it during one.

```bash
python3 -m pytest tests/where_the_numbers_come_from/test_problem_2_shards.py
```

**3.3 — Label your own numbers.** No test: these are your numbers, and nothing here can check
them.

Take the quantities you wrote down for [ch02](#what-a-workload-is)'s problem 2.5 and put one of
three words against each: `fact`, `vendor_claim`, `assumption`. Then, for every `fact`, write the
source you would hand somebody who asked: a document, an invoice, a measurement with a date on it.
Not where you think it came from. The thing you would actually send.

The useful part is the reclassification. Count how many started as facts and ended as vendor
claims once you looked for the source. Count how many ended as assumptions because the source was
a conversation. In this book's own models, more of the inputs are assumptions than anybody would
guess before counting. That is why the labels are mandatory rather than encouraged.

A good answer has a source line for every `fact` that you could paste into an email, and at least
one line that changed category while you were writing it. If nothing changed category, you have
labelled what you believe rather than what you can show.

## Where to go next

[ch04](#peak-mean-and-growth) is about the input that does the most damage in this book and is
the hardest to measure: a growth rate is a claim about the future, and no amount of provenance
discipline turns one into a measurement.

[ch13](#monte-carlo) is what to do with a standard error once you have one.
