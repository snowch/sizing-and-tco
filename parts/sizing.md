---
title: "Part III — Sizing"
short_title: "Part III — Sizing"
---

(part-sizing)=
# Part III — Sizing

> How do you get from a stated workload to a number of machines you would defend?

Everything so far has been preparation. This part does the arithmetic, and then looks at what it
produced.

[ch09](#capacity) is the chain from what an application stores to what a purchase order says, and
the asymmetry in it: every term that hurts is certain, and the one term that helps is a
measurement.

[ch10](#bandwidth-and-the-binding-constraint) is the second chain, the fact that the two disagree,
and the number nobody computes: how far short you fall in the cases where the chain you dropped is
the one that binds.

[ch11](#headroom-and-failure-domains) is the margin under both, why it is a rule rather than a
number, and the arithmetic that catches people: margins compose by multiplication, and nobody in
the room multiplies them.

[ch12](#the-sizing-model) assembles all of it and produces the number the book is about. Then it
asks the model what that number is worth, and the answer is the reason Part IV exists.

The transition out of this part is the only one in the book that is a *feeling* rather than a
topic: you have a number, and you cannot defend it.
