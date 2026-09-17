---
title: "Power first"
short_title: "ch15 Power first"
---

(power-first)=
# ch15 · Power first

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch14](#capex-opex-and-lifecycle) |
| **What it produces** | The storage model resized from a power budget inwards |
| **Built from** | `storage_cluster-reference`, `storage_cluster-power_first` |
:::

## The question

What changes when watts are the binding constraint rather than money?

Everything so far has sized a system from demand and then priced what it sized. Here the sizing
runs the other way: a rack has a power allocation, the allocation is not negotiable, and the
number of machines follows from it.

## The material

### Sizing backwards

When power binds, the chain inverts. You start with an allocation at the wall, divide out what the
building spends on itself, divide by what a machine draws, and round **down**.

That rounding is the only one in this book that goes that way. Every other constraint is a demand
to be satisfied, so it rounds up; this one is a supply that cannot be exceeded. Problem 15.1 is
that inversion. People get the facility multiplier backwards: an inefficient building buys you
*fewer* machines, not more.

### What a power budget does to a cluster sized for demand

```{include} _generated/power-first-scenarios.md
```

The left column is the cluster [ch11](#the-sizing-model) recommended. The right is what fits in
the allocation.

It is smaller. Everything downstream is smaller with it: less capital, less running cost, a lower
total. Read those rows and the power-constrained design looks like a saving.

Then read the ceilings:

```{include} _generated/power-first-ceilings.md
```

Neither is comfortable, and they are uncomfortable in different ways. The capacity ceiling is over
its hard limit at the point estimate — not at some unlucky percentile, at the expected case — and
the model puts it over in most of the futures it thinks are plausible. The bandwidth ceiling is
still under its limit, but it has spent the whole margin that was keeping it there. That is the
verdict column saying *into the margin* rather than *ok*.

So the honest output of this chapter is not a cluster. **It is the statement that this workload
does not fit in this power envelope**, with the numbers to say so.

That is a useful answer, and a spreadsheet does not produce it: sized from a power budget, a
spreadsheet gives a node count and stops. The node count is real. The cluster it describes cannot
do the job it would be bought for.

### Four ways out of a power budget that does not fit

Once the model says the workload does not fit, there are four things to do and the model prices
three of them.

**Get more power.** The expensive one, and often the slowest — a power allocation is a building's
property and sometimes a substation's.

**Use less per machine.** Fewer, denser machines change watts per machine and capacity per
machine together, and the model will say whether the trade is favourable.

**Improve the building.** [ch14](#capex-opex-and-lifecycle)'s facility multiplier is a division.
Problem 15.2 is worth doing for the framing alone: a multiplier quoted as a small surcharge is a
substantial *share* of the bill. Halving the overhead is equivalent to finding machines that draw
materially less, and is often cheaper.

**Want less.** Reduce retention, sample harder, accept a lower service level. Nobody proposes
this in a sizing meeting, and it is frequently the right answer.

### Why power is not a price like the others

Every other cost in [ch14](#capex-opex-and-lifecycle) is a price: negotiable, comparable, subject
to a discount. Energy is physics with a price attached.

```{include} _generated/power-first-tornado.md
```

The things that move the energy bill are a count of machines, a draw per machine, a building
multiplier and a tariff. Three of the four are properties of hardware and buildings rather than of
contracts, and the one that is a price is set by a market nobody in the room influences.

Energy is also the only cost line that is simultaneously a **constraint**. Nobody is told they
may not spend more on drives; they are regularly told the rack has no more power.

### A note on carbon

The model does not carry a carbon figure, and the omission is deliberate rather than an oversight.

Converting energy to emissions needs a grid intensity that varies by region, by hour, and by
whatever contractual instruments an organisation has bought — and those instruments are an
accounting decision rather than a physical one. This book produces the kilowatt-hours, which is
the part it can defend. Multiplying them is somebody else's judgement, and the multiplier is where
all the disagreement is.

Energy price and carbon price move together ([ch13](#correlation-and-convergence)), so a model
that added a carbon line and drew it independently would understate the range of the total.

## What this cannot tell you

**What your allocation actually is.** Contracted power, breaker capacity, cooling capacity and
what the facility will let you draw sustainably are four different numbers, and they are not
usually the same one. This chapter takes one number; getting the right one is a conversation with
whoever runs the building.

**What a machine really draws.** The model uses a typical figure under load, marked as a vendor's
claim. Draw varies with workload, with ambient temperature, and with how full the drives are. The
number that matters for an allocation is a sustained peak rather than a typical figure.

**Anything about the shape of the draw.** Power is billed on energy and constrained on peak. A
cluster that idles overnight and saturates at noon has an energy bill of one shape and a capacity
problem of another, and this model has only the average.

**Whether the building's multiplier is stable.** It varies with outside temperature and with how
full the facility is, and the figure quoted in a contract is usually an annual average under
favourable assumptions.

**What to do about it.** The model prices three of the four responses above. Which to choose is a
decision, and [ch20](#a-tco-for-finance) is about putting one to somebody.

## Problems

Two, in `tests/power_first/`.

**15.1 — Sizing backwards.**
From an allocation to a machine count. Get the multiplier the right way up, and round the way a
supply rounds rather than the way a demand does.

```bash
python3 -m pytest tests/power_first/test_problem_1_budget.py
```

**15.2 — A ratio quoted, a fraction paid.**
One line, worth having in your head. A building that sounds a little inefficient is spending a
substantial share of the bill on itself, and the two framings land very differently in a
conversation about money.

```bash
python3 -m pytest tests/power_first/test_problem_2_pue.py
```

## Where to go next

[ch16](#unit-economics) turns a total into a number somebody outside the team can compare against
something — which is where a power-constrained design either justifies itself or does not.

[ch13](#correlation-and-convergence) is why an energy price and a carbon price should not be drawn
independently.
