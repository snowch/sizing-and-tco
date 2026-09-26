---
title: "Part V — Cost"
short_title: "Part V — Cost"
---

(part-cost)=
# Part V — Cost

> What does the thing you have sized cost, over its life, and per unit of what it does?

Part III chose the fleet. This part shows what that fleet costs over its life and per unit of what
it does, and what that figure is and is not comparable with.

**[ch15 · Capex, opex and where the total stops](#capex-opex-and-lifecycle)** splits what you pay
once from what you pay every month, and notices which of the two got the meeting.

**[ch16 · Power first](#power-first)** is what changes when the constraint is watts rather than
money. It is the one place in the book where the sizing runs backwards and the rounding goes the
other way.

**[ch17 · Unit economics](#unit-economics)** turns a total into a number somebody outside the team
can compare against something. It spends most of its time on the denominator, because nobody
checks it.

**[ch18 · The five-year model](#the-five-year-model)** concerns the seam between two models: how one
uses a figure that another computed. Its example is the web service's cost per stored terabyte,
which stands in for the storage price the observability model assumes. The figure usually crosses
the seam as one number in a document, and while the headline value survives, the uncertainty around
it does not, because one number has no room for it.

The cost chains begin with *hosts in the fleet*, a number already decided. What follows is a bill of
materials: counts times prices, added up. Each of those relationships holds by definition, so the
cost chains are definitional in [ch01](#point-estimates)'s sense. That follows from what the chains
contain, not from their being about cost. Sampling their inputs shows all the doubt in the terms the
chains have.

This part adds no ceiling of its own; the ceilings from Parts II and III remain in the model.
[ch16](#power-first) runs into them. Sized from a power budget, the fleet is over the hard limit of
three ceilings at the point estimates. The working set no longer fits in memory, the disks are full,
and the busy hour, counted with coordination, is more than the fleet can serve. The two queueing
ceilings have used up their margin. ch16 concludes that this workload does not fit in this power
envelope.
