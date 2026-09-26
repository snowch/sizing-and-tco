---
title: "Capacity"
short_title: "ch09 Capacity"
---

(capacity)=
# ch09 · Capacity

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

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

Here is that chain on its own: the nodes that feed *hosts for storage*, from the records and
growth rate through the four terms. The interactive graph below is the same chain with the rest of
the model around it. One node in it is a colour no earlier chapter's graph has had: the measured
constant, *record compression ratio*, is amber. The chain ends in a ceiling, *limit on disk fill at
horizon*. A measured constant is the other thing that makes a model conditional, and it would have
made this model conditional even if no ceiling had.

```{iframe} /models/web_service_capacity-reference.html
:width: 100%
Open *Inputs*, drag *replication factor* and watch *hosts for storage* under *Outputs*.
```

**Replication.** Whole copies. Three copies cost three times the space, survive two losses, and
are the simplest thing that works. Erasure coding buys the same protection for less space by
spreading the data over more pieces. Problem 9.2 is that comparison. Erasure coding pays for the
space it saves with reads that touch more machines. No model in this book has a term for that cost.

**Compression.** The only term that reduces what you buy, and the only one measured rather than
decided or assumed:

```{include} _generated/capacity-measured.md
```

That ratio belongs to one codec and one body of data, not to your data;
[ch03](#where-the-numbers-come-from) is where the book makes that argument. To get the ratio that
belongs in your model, replace the generator the stamped result names,
`bench.measure.application_records`, with a generator that reads your own records and measure
again.

Click *record compression ratio* in the graph and open *In the file* under *Details*. Its entry
holds no number. It holds only the name of the stamped result its number comes from,
`result: records-compression`. *Details* also shows the measured value with its standard error,
what it was measured against, and the path of the stamped result. A spreadsheet cell holding the
same number could not tell you where it came from.

**Overhead.** Indexes, the write-ahead log and the filesystem's own bookkeeping: the space the
store keeps beside the records so that it can find them and survive a crash. It multiplies
everything stored. Nobody has counted it for this service, so the model holds it as an assumption
with a range. Its source says the range is for a service with a few indexes per table, and that a
search-heavy service is off the top of it.

**The fill limit.** The fill limit is not a property of the data. You cannot run a disk full, and
the model holds back a share of every host's disk, set by the slider *disk margin*.
[ch11](#headroom-and-failure-domains) is about why the margin is a rule rather than a number. It
is in the chain because the space you hold back is space you still have to buy.

### Where the uncertainty in the chain is

Two of the four terms are decisions you make: *replication factor* and *disk margin*. Each is one
number, with no range, so neither can surprise you. The other two carry uncertainty of different
kinds. *Index overhead* is an assumption with a range. *Record compression ratio* is a measurement
with a standard error. The table below is a tornado (the chart [ch04](#peak-mean-and-growth)
taught): it swings one input at a time across its range and records how far *raw disk needed at
horizon* moves.

Growth is at the top, as it was in ch04. Of the chain's own terms, *index overhead* is the one
whose range moves the disk. *Record compression ratio* barely moves it: its standard error is tiny
next to the overhead's range. Fixing compression at its measured value costs you nothing. The
overhead's range is lopsided: it reaches further above the value the model plans with than below
it. When overhead is wrong, it can be wrong by more on the side of needing more disk.

Compression's risk is not its standard error. It is a bias. The repository compressed each shard
of records as one continuous stream. A store compresses page by page, so it sees less repetition
between records than a stream does. So the measured ratio is an upper bound on what a store
achieves, not an estimate of it. A real store compresses less and needs more disk than the chain
says. Nothing in this repository measures how much less. Both uncertain terms therefore lean the
same way: a sizing that takes one number for each term is optimistic.

### Two kinds of terabyte, and the ten per cent

A drive's datasheet counts a terabyte as a trillion bytes. A filesystem counts in powers of two,
and its unit, the tebibyte, is about a tenth larger. Both are called a terabyte in conversation.
This model's example is *disk per host*, from a spec sheet declared in decimal terabytes, as its
source says. If a plan reads the datasheet in the filesystem's unit, each drive holds about a tenth
less than planned, and that shortfall comes out of the *disk margin*: the disks reach their fill
limit sooner than the plan says, before any growth has arrived to explain it.

So every node in this book declares a unit, and the toolkit converts rather than assuming. Problem
9.3 is that conversion.

### What comes out

```{include} _generated/capacity-outputs.md
```

*Raw disk needed at horizon* is what the disks must hold at the end of the period, once every
copy, every index and the compression are counted. *Hosts for storage* is how many hosts' disks
that takes, with each disk filled only up to what the *disk margin* leaves. It is this chain's
answer, and the model will end up with three such answers and have to choose between them.

*Disk fill at horizon* is how full the disks are at the end of the period: *raw disk needed at
horizon* divided by the disk installed in the fleet. A fill of one is full. The fleet it is
measured on is *hosts in the fleet*, not *hosts for storage*; *hosts in the fleet* is an input, the
fleet the model is told you bought. Its source says it is set the way a fleet usually is: at what
the model recommends when every input sits at its point estimate.
[ch12](#the-sizing-model) is where that decision is made. In this model *hosts in the fleet* is
larger than *hosts for storage*, because another chain asks for more hosts, and the fill at the
plan sits below the line the margin draws.

Read the row as [ch06](#queueing-and-the-knee) taught. *Headroom* is the *disk margin*. *Allowed*
is the limit less the margin: past it, the space held back to re-copy a dead host's records has
been spent on data. *Limit* is one. *Over allowed* and *Over limit* are the share of the model's
futures past each line; the second is how often the records do not fit the fleet you bought.

The range on the host count is wide. Most of its width is the growth rate from
[ch04](#peak-mean-and-growth), as the tornado above showed, not anything in this chapter's chain.
The disk arithmetic is the well-understood part of the problem. What it is applied to is not.

## What this cannot tell you

**What your data compresses to.** The constant was measured over records this repository
generates: a fixed mixture of user profiles, orders and events. The proportions and schemas were
chosen, not observed. Nothing here measures how a different mixture would move the ratio. The
standard error covers only how much the ratio varied across the shards of that one corpus, with
the mixture held fixed; it says nothing about your data. Nothing here measures how much less a
store gets by compressing page by page instead of as one stream. What it would take to know:
compress your own records with the codec and setting you run, in the units your store compresses
in. Problem 9.5 is that measurement.

**Anything about record size.** The chain above is a chain of bytes: it starts from *records held,
day one*, declared in terabytes, and never counts records. A store keeps bookkeeping for each
record as well as for each byte: a header, an index entry. For small records that per-record cost
is a larger share of the disk than for large ones, but nothing in this repository measures how large that share is.
*Index overhead* is one multiplier on every byte and cannot express a cost depending on record
count. A model of a service with many small records needs a term this one does not have.

**What happens when a host's disks are lost.** Every figure is a healthy fleet. Losing a host means
its copies have to be re-made on the survivors, using disk and bandwidth that were doing something
else. The chain has no term for the window in which that is happening
([ch11](#headroom-and-failure-domains)).

**Whether disk is the chain that binds.** It is the chain this chapter followed. It is not the one
that most often decides, and the model assumes neither.
[ch10](#bandwidth-and-the-binding-constraint) is the other two chains, and how often each of the
three decides the answer.

## Key takeaways

:::{div}
:class: takeaways

- **Four terms stand between the bytes an application holds and what you buy.** Replication and
  overhead multiply it, compression divides it, and the fill limit is a surcharge on all of it.
- **Of the chain's four terms, overhead carries the range that matters and compression carries a
  bias.** Replication and the disk margin are decisions with no range. Overhead's range moves the
  disk more than any other term in the chain, reaching further towards more disk. Compression's
  standard error is negligible.
- **The measured compression ratio is an upper bound for a real store.** It was measured as one
  stream from one generated body of records; a real store compresses page by page and gets less.
  Measure your own records in the units your store compresses in.
- **A datasheet terabyte and a filesystem terabyte differ by about a tenth.** A drive counted in
  the wrong unit holds less than planned, and the shortfall comes out of the disk margin. Every
  node declares its unit and the toolkit converts.
- **Almost all of the width in the host count is the growth rate, not the disk arithmetic.** The
  chain is the well-understood part of the problem. What it is applied to is not.
:::

## Problems

Five, in `tests/capacity/`. The first four have tests. The last does not, and says why.

**9.1 — The chain.**
The amount you must keep and the three terms that turn it into the disk you buy, one of which
divides; the fill limit is left to the node that counts hosts. Getting the division upside down
gives an answer wrong by the square of the compression ratio while still looking plausible. Check
yours against a case you can do in your head first.

```bash
python3 -m pytest tests/capacity/test_problem_1_raw.py -m problem
```

**9.2 — Erasure coding against copies, at equal safety.**
Work out the replication factor that survives the same number of losses as a given code, so the
two can be compared on space rather than on enthusiasm. Then notice what the saving grows with,
and what else grows with it.

```bash
python3 -m pytest tests/capacity/test_problem_2_erasure.py -m problem
```

**9.3 — The other kind of terabyte.**
Re-declare every unit that carries a terabyte in tebibytes, inputs included, and convert each
input's number so that it still means the same bytes. The test runs over the finished web service
model, with the nodes later chapters add, so the result carries prices in dollars. Nothing the
model buys has moved means the same hosts, the same money, and every tebibyte figure reading
smaller by exactly the ratio of the two units. The test also hands your function a price per
terabyte-month of its own, because no input in the model has a terabyte below the line.
Converting is not compensating, and the difference between the two is the chapter. If a host
count moved, a unit was missed, and finding it is the exercise.

```bash
python3 -m pytest tests/capacity/test_problem_3_binary_units.py -m problem
```

**9.4 — Turn it back into a definitional model.**
Name what has to go to make the web service model a definitional model: every measured constant,
every ceiling, and everything downstream of them. At least one of its outputs has to survive. The
test uses the finished model, which includes ceilings from chapters you have not read yet. You do
not need to know them: the stub hands you every node's kind and the nodes each one reads, and that
is enough to find what to delete. Then write one sentence saying what the result can no longer
tell anybody. If you cannot name it, you removed something that was doing no work, and the model
should not have had it.

```bash
python3 -m pytest tests/capacity/test_problem_4_classification.py -m problem
```

**9.5 — What your data compresses to.** No test: the corpus is your data, and this
repository has never seen it.

The constant in this chapter was measured over records this repository generates, compressed as
one stream. Measure your own: take a real selection of the records you store and compress them
with the codec you run, at the setting you run it at. Compress them in the units your store
compresses in, a page or block at a time, not as one long stream, because a one-stream ratio is an
upper bound on what the store gets. Record the ratio, how many records and bytes you measured, and
the page or block size you compressed in.

Compare it with the figure your capacity plan is currently using, and find out where that figure
came from. It may be a vendor's claim, a measurement of a different codec or setting, or a number
whose source nobody recorded.

A good answer has a ratio, how many records it came from, the codec and its setting, the unit it
was compressed in, and a sentence about the number it replaces. If your measured ratio matches the
planning figure exactly, find out who measured it first. You may have just re-derived a guess.

## Where to go next

[ch10](#bandwidth-and-the-binding-constraint) is the other two chains, and the question of which
of the three you are buying.

[Appendix D](#appendix-d-units) is the terabyte problem and the rest of the conversions that bite.
