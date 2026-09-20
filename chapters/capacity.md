---
title: "Capacity"
short_title: "ch09 Capacity"
---

(capacity)=
# ch09 · Capacity

## The question

How far is what you buy from what you can use?

Further than most people's first estimate, and always in the same direction: you buy more than you
can use. Four terms separate the two, and nobody writes them down together.

## The material

### The chain

```{image} _figures/capacity-graph.svg
:alt: The chain from what you need to store to how many hosts you must buy
:width: 100%
```

Four terms stand between an application's storage requirement and a purchase order. Two multiply
what you must buy. One divides it. One is a surcharge.

Here is that chain with the rest of the model around it. One node is a colour nothing earlier in
the book has had: the measured constant is orange. The ceiling the chain ends in is the third in
the model. The constant is the other thing that makes a sizing model, and it would have made this
one a sizing model even if no ceiling had.

```{iframe} /models/web_service_capacity-reference.html
:width: 100%
The disk chain in the graph. Drag *replication factor* and watch how many hosts the chain asks for.
```

**Replication.** Whole copies. Three copies cost three times the space, survive two losses, and
are the simplest thing that works. Erasure coding buys the same durability for less space by
spreading the data over more pieces, and problem 9.2 is that comparison. Erasure coding is not
cleverer, only amortised. It pays for the space it saves with reads that touch more machines,
which is a bandwidth problem, and therefore [ch10](#bandwidth-and-the-binding-constraint)'s.

**Compression.** The only term that helps you, and the only one that is a measured constant rather
than a decision:

```{include} _generated/capacity-measured.md
```

Read the last column. That ratio belongs to one codec and one body of data. It does not belong to
compression in general, and it does not belong to your data. Take the method rather than the
number: point the runner at a sample of your own records and get the ratio that belongs in your
model ([ch03](#where-the-numbers-come-from)).

**Overhead.** Indexes, the write-ahead log, the filesystem's own bookkeeping: the space the store
keeps beside the records so that it can find them and survive a crash. Applied to everything, and
larger than people expect once the indexes are counted.

**The fill limit.** People forget this one because it is not a property of the data at all. You
cannot run a disk full, and [ch11](#headroom-and-failure-domains) is about why the margin is a
rule rather than a number. It is in the chain here because the space you hold back is space you
still have to buy.

### Every term but one makes you buy more

Compression is the only term that helps. It is also the only one measured rather than decided or
assumed. Replication and the margin are decisions, and a decision is certain. The overhead is an
assumption with a shape, because nobody has counted the indexes. And a measurement over somebody's
corpus carries a standard error, which none of the others do.

A sizing that treats all four as constants is optimistic in the one place that helps. That place
is the one whose uncertainty was measured.

### Two kinds of terabyte, and the ten per cent

A drive's datasheet says a trillion bytes. A filesystem counts in powers of two. The difference is
about a tenth. Both are called a terabyte in conversation, and a tenth is a large fraction of what
compression was going to buy you.

So every node in this book declares a unit, and the toolkit converts rather than assuming. Problem
9.3 is that conversion, and this is the chapter where getting it wrong costs money.

### What comes out

```{include} _generated/capacity-outputs.md
```

Three rows, and each needs a word.

- *Raw data* is what the disks must hold once every copy, every index and the compression are
  counted.
- *Hosts for storage* is how many hosts' disks that takes. It is this chain's answer, one of three
  the model will have by [ch10](#bandwidth-and-the-binding-constraint).
- *Disk fill at horizon* is how full the disks of the fleet somebody bought are at the end
  of the period, as a fraction of what they can hold. One is full. An interval reaching past one
  says that in some futures the records do not fit, because the arithmetic carries on past the
  point where the disks stop.

The interval on the host count spans an order of magnitude. Almost all of that width is the
growth rate from [ch04](#peak-mean-and-growth), not anything in this chapter's chain. The disk
arithmetic is the well-understood part of the problem. What it is applied to is not.

The measured constant is in the file the same way a ceiling is, and the toolkit reads its stamp
rather than its number:

```{iframe} /playground/capacity/
:width: 100%
The chain above, running. Read the measured constant's row: it says which corpus and which codec
its number belongs to, which is more than a spreadsheet cell can say.
```

:::{note} Key takeaways
- **Four terms stand between the bytes an application holds and what you buy.** Replication and
  overhead multiply it, compression divides it, and the fill limit is a surcharge on all of it.
- **Compression is the only term that helps, and the only one that is measured.** Replication and
  the margin are decisions, overhead is an assumption with a shape, and the measured constant
  carries a standard error the others do not.
- **The measured ratio belongs to one codec and one body of data.** Point the runner at a sample of
  your own records and use the ratio that comes out, not the book's.
- **A datasheet terabyte and a filesystem terabyte differ by about a tenth.** Every node declares
  its unit and the toolkit converts, because this is the chapter where getting it wrong costs money.
- **Almost all of the width in the host count is the growth rate, not the disk arithmetic.** The
  chain is the well-understood part of the problem. What it is applied to is not.
:::

## What this cannot tell you

**What your data compresses to.** The constant above was measured over a synthetic mixture this
repository generates, and the mixture's proportions are an assumption stated in the stamped
result. For this figure, that assumption is a larger source of error than the codec, the shard
spread, or anything the standard error reports. The number has an uncertainty, and the
uncertainty is about the wrong thing.

**Anything about record size.** The chain above is a chain of bytes. A store holding many small
records spends a substantial and sometimes dominant share of its disk on per-record
bookkeeping. The overhead term here is a flat multiplier and cannot express that. A model of a
service with a small-record problem needs a term this one does not have.

**What happens when a host's disks are lost.** Every figure is a healthy fleet. Losing a host means
its copies have to be re-made on the survivors, using disk and bandwidth that were doing something
else. The chain has no term for the window in which that is happening
([ch11](#headroom-and-failure-domains)).

**Whether disk is the chain that binds.** It is the chain this chapter followed. It is not the one
that most often decides, and the model assumes neither.
[ch10](#bandwidth-and-the-binding-constraint) is the other two chains, and how often each of the
three decides the answer.

## Problems

Five, in `tests/capacity/`. The first four have tests. The last does not, and says why.

**9.1 — The chain.**
Four terms, one of which divides. Getting the division upside down gives an answer wrong by the
square of the compression ratio while still looking plausible. Check yours against a
case you can do in your head first.

```bash
python3 -m pytest tests/capacity/test_problem_1_raw.py
```

**9.2 — Erasure coding against copies, at equal safety.**
Work out the replication factor that survives the same number of losses as a given code, so the
two can be compared on space rather than on enthusiasm. Then notice what the saving grows with,
and what else grows with it.

```bash
python3 -m pytest tests/capacity/test_problem_2_erasure.py
```

**9.3 — The other kind of terabyte.**
Re-declare every node held in terabytes in binary units and change nothing else. The outputs must
come out smaller by exactly the right ratio, and the model must still typecheck. If you find
yourself editing a value to compensate, stop.

```bash
python3 -m pytest tests/capacity/test_problem_3_binary_units.py
```

**9.4 — Turn it back into a cost model.**
Remove what makes the web service model a sizing model: the measured constant this chapter adds,
and every ceiling before and after it. Keep it working. Then write one sentence saying what the
result can no longer tell anybody. If you cannot name it, you removed something that was doing no
work, and the model should not have had it.

```bash
python3 -m pytest tests/capacity/test_problem_4_classification.py
```

**9.5 — What your data compresses to.** No test: the corpus is your data, and this
repository has never seen it.

The constant in this chapter was measured over a synthetic mixture, and the chapter says so.
Measure your own: take a real sample of what you store, compress it with the codec you run, at
the setting you run it at, and record the ratio and how much you measured.

Then compare it with the figure your capacity plan is currently using, and find out where that
figure came from. In this book's experience it is a vendor's marketing number, a different
codec's, or nobody remembers.

A good answer has a ratio, a sample size, the codec and its setting, and a sentence about the
number it replaces. If your measured ratio matches the planning figure exactly, find out who
measured it first. You may have just re-derived a guess.

## Where to go next

[ch10](#bandwidth-and-the-binding-constraint) is the other two chains, and the question of which
of the three you are buying.

[Appendix D](#appendix-d-units) is the terabyte problem and the rest of the conversions that bite.
