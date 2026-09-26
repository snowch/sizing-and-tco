---
title: "Power first"
short_title: "ch16 Power first"
---

(power-first)=
# ch16 · Power first

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

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

The left column is the fleet [ch12](#the-sizing-model) recommended from demand. The right is what
fits in the allocation.

It is smaller. *Hosts the model recommends* is the same in both columns. The model works it out from
demand (the largest of the host counts its three chains ask for), and a power budget changes nothing
about demand. What power changes is *hosts in the fleet*, the fleet you buy. The gap between those
two rows in the right-hand column is what the allocation takes away.

Read the rows below the host counts, down to energy. Capital falls, annual running cost falls, the
total cost of ownership falls, the cost per million requests falls, and annual energy falls. The
power-constrained design looks like a saving.

Then look at the last row, *residence time*: the seconds a request spends in the system at the busy
hour. Its ratio is far above one. Residence time is the time a request needs to run divided by the
share of the fleet that is idle at the busy hour. The same load on fewer machines leaves less of the
fleet idle. This is the knee from [ch06](#queueing-and-the-knee): the division by idle fraction is
nearly flat while there is slack, and nearly vertical when there is not.

Then read the ceilings:

```{include} _generated/power-first-ceilings.md
```

Five of the six ceilings are in trouble. Three are over their hard limit at the point estimate:

- *working set against memory*: the working set no longer fits in the fleet's memory;
- *disk fill at horizon*: the disks are full;
- *utilisation, counting coordination*: at the busy hour, more requests arrive than the fleet can
  serve once the work its hosts do for each other is counted.

The *disk fill* row reads as if it sits exactly on its limit. The table rounds to two decimal
places; the value behind it is just past the limit, and the verdict comes from that value, not from
the rounded figure.

Two more ceilings are *into the margin*: *utilisation at the busy hour* and *utilisation with one
host down*. Each is still under its limit but past the line where the margin was meant to keep it.
That margin was what kept the fleet off the knee, and spending it is why residence time rose.

The sixth ceiling, *fraction of the fleet doing nothing useful*, is ok. A smaller fleet loses a
smaller share of itself to coordination. This does not help, because the busy-hour load did not
shrink with the fleet: this fleet wastes less of itself yet still cannot keep up.

None of this is an unlucky future. Every verdict above is at the point estimate: the answer with
every input at its middle value.

For each of the three ceilings that are over, the table below shows the share of the model's futures
in which that ceiling is past its limit, for each fleet:

The reference fleet already breaks each of the three in some of its futures. The power budget raises
every one of those shares.

So the honest output of this chapter is not a fleet. **It is the statement that this workload
does not fit in this power envelope**, with the numbers to say so.

That is a useful answer, and a spreadsheet does not produce it. Sized from a power budget, a
spreadsheet gives a host count and stops. The host count is real. The fleet it describes cannot
do the job it would be bought for.

### Four ways out of a power budget that does not fit

Once the model says the workload does not fit, there are four things you can do. The model has no
node for the power allocation itself, so it cannot work out a host count from watts. The power-first
scenario holds the fleet at a host count that was worked out outside the model. To try any of the
four, you work out the new host count yourself using your answer to Problem 16.1, and set *hosts in
the fleet* in the model. Then the model prices the fleet you end up with: its capital, its running
cost, its total and its ceilings.

For only one of the four, *use less per machine*, does the model also price what the change itself
costs. For the other three it has no node for that cost.

**Get more power.** A power allocation is a property of the building, and sometimes of the
substation that feeds it. The model can price the larger fleet that more power would let you run. It
has no node for what the extra power costs.

**Use less per machine.** Fewer, denser machines change the watts per machine and the capacity per
machine together. Every side of that trade is an input to the model: the machine's draw (*host
power*), its capacity (*cores per host*, *ram per host*, *disk per host*) and its price (*host
price*). So the model can say whether the trade is favourable.

To price it:

1. Make a copy of `models/web_service/model.yaml` outside the repository.
2. In your copy, set *host power*, *cores per host*, *ram per host*, *disk per host* and *host
   price* to the denser machine's figures.
3. Run your Problem 16.1 function on the allocation (the dashed line in the wall figure), the new
   *host power* and the model's *PUE*, to get the number of machines that fit.
4. In your copy, set *hosts in the fleet* to that number.
5. Run `python3 scripts/verify-models.py <your copy>`
   ([Appendix H](#appendix-h-running-the-toolkit)) to check the model and read the ceilings and the
   total at the point estimate. It prints node names (`tco` for the total), and a ceiling above one
   is over its limit. Compare them against the power-first column of the first table on this page.

**Improve the building.** In [ch15](#capex-opex-and-lifecycle), the facility multiplier multiplies
the machines' draw to give what the whole facility draws for each watt the machines draw. When
sizing backwards, you divide by it. The multiplier is a ratio quoted as a number a little above one.
Such a number sounds like a building that is close to perfect.

Problem 16.2 turns the same multiplier into the share of the electricity bill that pays for the
building rather than the machines. That share is money that buys no computing. The contrast between
how the ratio sounds and how the bill share sounds is the point of the problem.

In the model, the multiplier and the draw per machine multiply each other. Lowering the multiplier
by some proportion frees the same watts as machines that draw that proportion less. The model prices
the energy a better building saves through *PUE*. It has no node for what the building work costs,
so it cannot say which of the two is cheaper.

**Want less.** Shed the least valuable requests at the busy hour. Keep fewer records. Accept a
longer tail. The model can show what a smaller demand does to the fleet's ceilings, through *peak
request rate, day one*, *records held, day one*, and *queueing margin*. Accepting a longer tail
means running with less margin.

This is the only one of the four that buys nothing. Its cost is what the shed requests and records
were worth. The people who own the service have to judge it.

### Why power is not a price like the others

Every other cost in [ch15](#capex-opex-and-lifecycle) is a price: negotiable, comparable, subject
to a discount. Energy is physics with a price attached.

```{include} _generated/power-first-tornado.md
```

The table shows the fleet's energy in kilowatt-hours a year, not the bill in money. A fleet's
energy is the number of machines it runs, times the draw per machine, times the facility
multiplier, times the hours in a year. The bill is that energy times the electricity price.

The table's two rows show the draw per machine and *PUE*, which is the facility multiplier: power
usage effectiveness, what the whole facility draws for each watt the machines draw
@iso30134pue2016. Only these two inputs move the kilowatt-hours in this scenario. The number of
machines moves them too, but it is fixed at your choice: it is not a row. The hours in a year are a
definition. The electricity price does not move the kilowatt-hours; it enters only when you turn
them into money.

So how much energy a fleet uses is set by its machines and its building. The price is the only part
of the energy line that is a price.

Energy is also the only cost line that is a **constraint** at the same time. Nobody is told they
may not spend more on hosts. People are regularly told the rack has no more power.

### A note on carbon

The model does not carry a carbon figure. The omission is deliberate.

Converting energy to emissions needs a grid intensity. That varies by region, by hour, and by
whatever contractual instruments an organisation has bought. Those instruments are an accounting
decision, not a physical one. This book produces the kilowatt-hours, which is the part it can
defend. Multiplying them is somebody else's judgement, and the multiplier is where all the
disagreement is.

If energy price and carbon price move together, a model that added a carbon line and drew its price
independently of the energy price would understate the range of the total.
[ch14](#correlation-and-convergence) showed that drawing correlated inputs independently makes the
result's interval narrower than it should be.

## What this cannot tell you

**What your allocation is.** Contracted power, breaker capacity, cooling capacity and what the
facility will let you draw sustainably are four different numbers. This chapter takes one number.
The model does not hold even that one: it has no node for the allocation. Nothing in the model
notices when a fleet outgrows its power. Its ceilings watch memory, disks and queues; none watches
watts against a supply. Getting the right number is a conversation with whoever runs the building.

**What a machine draws.** The model uses a typical figure under load, marked as a vendor's
claim. Draw varies with workload, with ambient temperature, and with how busy the processors are.
The number that matters for an allocation is a sustained peak, not a typical figure.

**Anything about the shape of the draw.** Power is billed on energy and constrained on peak. A
fleet that idles overnight and saturates at noon has an energy bill of one shape and a capacity
problem of another. This model has only the average.

**Whether the building's multiplier is stable.** It varies with outside temperature and with how
full the facility is. The figure quoted in a contract is usually an annual average under
favourable assumptions.

**What to do about it.** The model prices the fleet you end up with for each of the four responses
above. Only for using less per machine does it also price what the change costs. It has no node for
what more power, building work, or a smaller demand would cost you. Which to choose is a decision,
and [ch21](#a-tco-for-finance) is about putting one to the people who pay for it.

## Key takeaways

:::{div}
:class: takeaways

- **When power binds, the chain runs backwards and rounds down.** Start at the wall, divide out what
  the building spends on itself, divide by what a machine draws, and take the whole number below.
- **A fleet that fits the allocation can fail to do the job.** Sized to the power budget, the
  running example is over three hard limits at the point estimate and into the margin on two more
  of its six ceilings. Its capital and running cost fall with the fleet, but the time a request
  spends in the system rises steeply.
- **The honest output is a statement that the workload does not fit, with the numbers to say so.** A
  spreadsheet sized from a power budget gives a host count and stops.
- **There are four ways out, and the model prices the whole trade for only one of them.** More
  power, less per machine, a better building, or wanting less. For each, the model prices the
  fleet you end up with; only for using less per machine does it also price what the change
  costs.
- **Energy is the one cost that is also a constraint.** Nobody is told they may not spend more on
  hosts. People are regularly told the rack has no more power.
:::

## Problems

Three, in `tests/power_first/`. The first two have tests. The last does not, and says why.

**16.1 — Sizing backwards.**
From an allocation to a machine count. Three things to get right: the allocation is in kilowatts
and the draw per machine is in watts; get the multiplier the right way up; and round the way a
supply rounds rather than the way a demand does. The Check grades your function against the
power-first scenario: given what that fleet draws, your function has to give back that fleet. You
will use the function again when you price the *use less per machine* response above.

```bash
python3 -m pytest tests/power_first/test_problem_1_budget.py -m problem
```

**16.2 — A ratio quoted, a fraction paid.**
Your function takes a facility multiplier and returns the share of the electricity bill that goes
on the building rather than the machines, a number between zero and one. The multiplier is quoted
as a ratio to what the machines draw; the share is of the whole bill, the machines' draw included.
They are different numbers, and the two framings land differently in a conversation about money.
The Check grades your function against the model's energy bill run across a range of buildings.

```bash
python3 -m pytest tests/power_first/test_problem_2_pue.py -m problem
```

**16.3 — What you are allowed to draw.** No test: the numbers are held by people, not by this
repository.

Find out your real power allocation, and find out who holds each part of it. Contracted power,
breaker capacity, cooling capacity and what the facility will let you draw sustainably are four
different numbers. Each may be held by a different person: whoever holds the power contract,
whoever runs the electrical supply, whoever runs the cooling. None of them may be the person who
plans capacity. The smallest of the four is your allocation.

Feed that number into your Problem 16.1 function, with your machines' draw under load and your
building's multiplier, to get the number of machines your power allows. A good answer has the four
numbers, each with its unit and who gave it. For any you could not get, name who would have to be
asked. Say which is smallest, and give the machine count from 16.1.

An answer is wrong if the count from 16.1 is larger than a fleet you already run that has tripped a
breaker, run too hot, or been refused more power. Then one of your four numbers is too high, or the
draw per machine is too low. It is also wrong if two of your four numbers turn out to be the same
figure reported twice under different names. Then you have fewer than four, and the missing one may
be the smallest.

## Where to go next

[ch17](#unit-economics) turns a total into a cost per unit of work, which someone outside the team
can compare. It is about the part of a unit cost that goes unchecked: what it divides by. The first
table shows a lower *cost per million requests* for the power-first fleet. But the model divides the
total by the requests the demand brings over the horizon, not by the requests the fleet can serve.
The power-first fleet cannot serve them all at the busy hour, so its lower unit cost divides by work
it cannot do.
