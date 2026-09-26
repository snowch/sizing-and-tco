---
title: "Part II — Ceilings"
short_title: "Part II — Ceilings"
---

(part-ceilings)=
# Part II — Ceilings

> Where does a chain of multiplications stop describing a real system?

Part I described demand. This part is about what happens to a system when that demand arrives.
It justifies [ch01](#point-estimates)'s distinction between a definitional model and a conditional one.

**[ch05 · Little's law](#littles-law)** assumes nothing about how the system works: no pattern of
arrivals, no order of service. It has one condition: the system is in a steady state over the window
you are looking at, with as many requests leaving as arriving. The law relates three numbers, and it
cannot tell you why any of them is what it is.

**[ch06 · Queueing, and the knee](#queueing-and-the-knee)** buys a mechanism and pays for it in
assumptions. It also takes the knee out of its own title. The curve has no corner in it, and what
people point at is their own tolerance.

**[ch07 · When adding servers stops helping](#when-adding-servers-stops-helping)** addresses the
obvious response to a system that is too busy: buy more machines. This works less well than the
arithmetic suggests, and past some count it works in reverse, as each new machine costs more in
coordination than it brings in work.

**[ch08 · Regime changes](#regime-changes)** is the argument the other three have been assembling. A
threshold with different physics on either side is something no product of quantities can express,
however carefully the inputs are chosen. That is why the model file format has a ceiling node kind
and why the toolkit refuses a model that declares a limit without a margin.

If you take one thing from this part, take this: **the model is not wrong about how busy the fleet
is or about how big its working set is, but it is wrong about what those numbers mean past the
limit.**
