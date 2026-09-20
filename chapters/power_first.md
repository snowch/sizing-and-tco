---
title: "Power first"
short_title: "ch16 Power first"
---

(power-first)=
# ch16 · Power first

## The question

What changes when watts are the binding constraint rather than money?

Everything so far has sized a system from demand, then priced what it sized. Here the sizing runs
the other way. A rack has a power allocation. The allocation is not negotiable. The number of
machines follows from it.

## The material

### Sizing backwards

When power binds, the chain inverts. You start with an allocation at the wall. You divide out
what the building spends on itself. You divide by what a machine draws. Then you round **down**.

That rounding is the only one in this book that goes that way. Every other constraint is a demand
to be satisfied, so it rounds up. This one is a supply that cannot be exceeded. Problem 16.1 is
that inversion. People get the facility multiplier backwards: an inefficient building buys you
*fewer* machines, not more.

Here is the same fleet on two axes:

```{image} _figures/power-first-wall.svg
:alt: Facility power and five-year cost against host count, with the allocation drawn as a wall across the power axis and nothing across the cost axis
:width: 100%
```

On the left, watts against hosts, and a wall: what the building will supply, the largest whole
number of hosts that stays under it, and the next one, which does not. On the right, the same
hosts against what they cost over the horizon. It is a slope, and there is nothing across it to
stop anybody. That is the difference between a constraint and a price, and the rest of this
chapter is about what happens to the fleet the wall leaves you.

### What a power budget does to a fleet sized for demand

```{include} _generated/power-first-scenarios.md
```

The left column is the fleet [ch12](#the-sizing-model) recommended. The right is what fits in
the allocation.

It is smaller. Everything downstream is smaller with it: less capital, less running cost, a lower
total. Read those rows alone and the power-constrained design looks like a saving.

Then read the ceilings:

```{include} _generated/power-first-ceilings.md
```

None of them is comfortable, and they are uncomfortable in different ways. Three are over their
hard limit at the point estimate:

- the working set no longer fits in the fleet's memory;
- the disks are full;
- the fleet spends more of itself on coordination than its margin allows.

That is not an unlucky percentile. It is the expected case, and the model puts each of the three
over in a large share of the futures it thinks plausible. The two queueing ceilings are still
under their limit. But they have spent the whole margin that was keeping them there. That is what
the verdict column means by *into the margin* rather than *ok*.

So the honest output of this chapter is not a fleet. **It is the statement that this workload
does not fit in this power envelope**, with the numbers to say so.

That is a useful answer, and a spreadsheet does not produce it. Sized from a power budget, a
spreadsheet gives a host count and stops. The host count is real. The fleet it describes cannot
do the job it would be bought for.

### Four ways out of a power budget that does not fit

Once the model says the workload does not fit, there are four things you can do. The model
prices three of them.

**Get more power.** The expensive one, and often the slowest. A power allocation is a building's
property, and sometimes a substation's.

**Use less per machine.** Fewer, denser machines change watts per machine and capacity per
machine together. The model will say whether the trade is favourable.

**Improve the building.** [ch15](#capex-opex-and-lifecycle)'s facility multiplier is a division.
Problem 16.2 is that division, and the framing is the point: a multiplier quoted as a small
surcharge is a substantial *share* of the bill. Halving the overhead is equivalent to finding machines that draw
materially less, and it is often cheaper.

**Want less.** Shed the least valuable requests at the busy hour. Keep fewer records. Accept a
longer tail. Nobody proposes this in a sizing meeting, and it is frequently the right answer.

### Why power is not a price like the others

Every other cost in [ch15](#capex-opex-and-lifecycle) is a price: negotiable, comparable, subject
to a discount. Energy is physics with a price attached.

```{include} _generated/power-first-tornado.md
```

Four things move the energy bill: a count of machines, a draw per machine, a building multiplier
and a tariff. Three of the four are properties of hardware and buildings, not of contracts. The
one that is a price is set by a market nobody in the room influences.

Energy is also the only cost line that is a **constraint** at the same time. Nobody is told they
may not spend more on hosts. People are regularly told the rack has no more power.

### A note on carbon

The model does not carry a carbon figure. The omission is deliberate.

Converting energy to emissions needs a grid intensity. That varies by region, by hour, and by
whatever contractual instruments an organisation has bought. Those instruments are an accounting
decision, not a physical one. This book produces the kilowatt-hours, which is the part it can
defend. Multiplying them is somebody else's judgement, and the multiplier is where all the
disagreement is.

Energy price and carbon price move together ([ch14](#correlation-and-convergence)). A model that
added a carbon line and drew it independently would understate the range of the total.

:::{note} Key takeaways
- **When power binds, the chain runs backwards and rounds down.** Start at the wall, divide out what
  the building spends on itself, divide by what a machine draws, and take the whole number below.
- **A fleet that fits the allocation can fail to do the job.** Sized to the power budget, the
  running example is over three hard limits at the point estimate and has spent the margin on the
  other two.
- **The honest output is a statement that the workload does not fit, with the numbers to say so.** A
  spreadsheet sized from a power budget gives a host count and stops.
- **There are four ways out, and the model prices three of them.** More power, less per machine, a
  better building, or wanting less. The last is rarely proposed and often right.
- **Energy is the one cost that is also a constraint.** Nobody is told they may not spend more on
  hosts. People are regularly told the rack has no more power.
:::

## What this cannot tell you

**What your allocation is.** Contracted power, breaker capacity, cooling capacity and
what the facility will let you draw sustainably are four different numbers. They are not usually
the same one. This chapter takes one number. Getting the right one is a conversation with whoever
runs the building.

**What a machine draws.** The model uses a typical figure under load, marked as a vendor's
claim. Draw varies with workload, with ambient temperature, and with how busy the processors are.
The number that matters for an allocation is a sustained peak, not a typical figure.

**Anything about the shape of the draw.** Power is billed on energy and constrained on peak. A
fleet that idles overnight and saturates at noon has an energy bill of one shape and a capacity
problem of another. This model has only the average.

**Whether the building's multiplier is stable.** It varies with outside temperature and with how
full the facility is. The figure quoted in a contract is usually an annual average under
favourable assumptions.

**What to do about it.** The model prices three of the four responses above. Which to choose is a
decision, and [ch21](#a-tco-for-finance) is about putting one to somebody.

## Problems

Three, in `tests/power_first/`. The first two have tests. The last does not, and says why.

**16.1 — Sizing backwards.**
From an allocation to a machine count. Get the multiplier the right way up, and round the way a
supply rounds rather than the way a demand does.

```bash
python3 -m pytest tests/power_first/test_problem_1_budget.py
```

**16.2 — A ratio quoted, a fraction paid.**
One line, worth having in your head. A building that sounds a little inefficient is spending a
substantial share of the bill on itself. The two framings land very differently in a conversation
about money.

```bash
python3 -m pytest tests/power_first/test_problem_2_pue.py
```

**16.3 — What you are actually allowed to draw.** No test: the numbers are held by people, not by
this repository.

Find out your real power allocation, and find out who knows it. Contracted supply, breaker
capacity, cooling capacity and what the machines currently draw are four different numbers. The
smallest is the one that sizes you.

Expect this to be hard. In most organisations the people who plan capacity and the people who
hold the power contract have never been in the same meeting. The constraint that binds first is
owned by neither.

A good answer has four numbers, or has fewer and names who would have to be asked for the rest.
If you already knew all four without asking anybody, you are in an unusual organisation, and the
rest of this chapter is easier for you than for most readers.

## Where to go next

[ch17](#unit-economics) turns a total into a number somebody outside the team can compare against
something. That is where a power-constrained design either justifies itself or does not.

[ch14](#correlation-and-convergence) is why an energy price and a carbon price should not be drawn
independently.
