---
title: "Capacity"
short_title: "ch09 Capacity"
---

(capacity)=
# ch09 · Capacity

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch02](#what-a-workload-is) |
| **What it produces** | The raw-to-usable chain of the storage model, node by node |
| **Built from** | `storage_cluster-reference` |
:::

## The question

How far is what you buy from what you can use?

Further than most people's first estimate, in a direction that is always the same, and by a factor
that is a product of four things nobody writes down together.

## The material

### The chain

```{image} _figures/capacity-graph.svg
:alt: The chain from what you need to store to how many machines you must buy
:width: 100%
```

Four terms stand between an application's storage requirement and a purchase order. Two multiply
what you must buy, one divides it, and one is a surcharge.

**Replication.** Whole copies. Three copies costs three times the space and survives two losses,
and it is the simplest thing that works. The alternative is erasure coding, which buys the same
durability for less space by spreading it over more pieces — problem 9.2 is that comparison, and
it exposes the fact that erasure coding is not cleverer, it is just amortised. What it costs
instead is that every read touches more machines, which is a bandwidth problem and therefore
[ch10](#bandwidth-and-the-binding-constraint)'s.

**Compression.** The only term that helps you, and the only one that is a measured constant rather
than a decision:

```{include} _generated/capacity-measured.md
```

Read the last column, then read it again. That ratio belongs to a codec and a body of data. It
does not belong to compression, it does not belong to your data, and the honest use of it is as
the *method* — point the runner at a sample of your own estate and get the number that belongs in
your model ([ch03](#where-the-numbers-come-from)).

**Overhead.** Filesystem, index, journal, superblocks, the space a filesystem keeps for itself.
Small per unit and applied to everything.

**The fill limit.** The term people forget, because it is not a property of the data at all. You
cannot run a storage system full, and [ch11](#headroom-and-failure-domains) is about why the
margin is a rule rather than a number. It is in the chain here because it changes what you buy,
and it changes it by more than compression does.

### The direction that is always the same

Every one of those terms except compression makes you buy more. Compression is the one that helps,
it is the one that is measured rather than decided, and it is therefore the one with a standard
error on it.

That asymmetry is worth naming. The terms that hurt are certain; the term that helps is a
measurement over somebody's corpus. A sizing that treats them all as constants is being optimistic
in exactly one place, and it is the place with the most uncertainty in it.

### Two kinds of terabyte, and the ten per cent

A drive's datasheet says a trillion bytes. A filesystem counts in powers of two. The difference is
about a tenth, both are called a terabyte in conversation, and it is a large fraction of what
compression was going to buy you.

This is why every node in this book declares a unit and why the build converts rather than
assuming. Problem 1.2 in [ch01](#reading-a-model) was that conversion; if you skipped it, it is
worth ten minutes now, because this is the chapter where it costs money.

### What comes out

```{include} _generated/capacity-outputs.md
```

Two rows need a word before they mean anything. *Fill level at horizon* is how full the cluster is
at the end of the period it was bought for, as a fraction of what it can hold: one is full, and an
interval reaching past one is the model saying that in some futures the data does not fit — the
arithmetic carries on past the point the disks stop. And *nodes purchased* shows no interval
because it is not a prediction. It is a decision somebody took, and the rest of the table is what
the model says about it.

The interval on the node count spans most of an order of magnitude, and almost all of that is the
growth rate from [ch04](#peak-mean-and-growth) rather than anything in this chapter's chain. The
capacity arithmetic is the well-understood part of the problem. What it is applied to is not.

## What this cannot tell you

**What your data compresses to.** The constant above was measured over a synthetic mixture this
repository generates, and the mixture's proportions are an assumption stated in the stamped
result. For this figure, that assumption is a larger source of error than the codec, the shard
spread, or anything the standard error reports. The number has an uncertainty and the uncertainty
is about the wrong thing.

**Anything about small objects.** The chain above is a chain of bytes. A cluster storing many
small objects spends a substantial and sometimes dominant share of its capacity on metadata, and
the overhead term here is a flat multiplier that cannot express that. A model of an estate with a
small-object problem needs a term this one does not have.

**What happens during a rebuild.** Every figure is a healthy cluster. Losing a node means
re-replicating its data somewhere, using capacity and bandwidth that were doing something else,
and the capacity chain has no term for the window in which that is happening
([ch11](#headroom-and-failure-domains)).

**Whether the capacity chain is the one that binds.** It usually is, and the model is careful not
to assume it. [ch10](#bandwidth-and-the-binding-constraint) is the other chain, and how often each
of them decides the answer.

## Problems

Two, in `tests/capacity/`.

**9.1 — The chain.**
Four terms, one of which divides. Getting the division upside down gives an answer wrong by the
square of the compression ratio while still looking entirely plausible — check yours against a
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

## Where to go next

[ch10](#bandwidth-and-the-binding-constraint) is the second chain, and the question of which of the
two you are actually buying.

[Appendix D](#appendix-d-units) is the terabyte problem and the rest of the conversions that bite.
