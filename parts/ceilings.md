---
title: "Part II — Ceilings"
short_title: "Part II — Ceilings"
---

(part-ceilings)=
# Part II — Ceilings

> Where does a chain of multiplications stop describing a real system?

Part I described demand. This part is about what happens to a system when that demand arrives.
It justifies [ch01](#point-estimates)'s distinction between a definitional model and a conditional one.

**[ch05 · Little's law](#littles-law)** is the one relationship that needs no assumptions at all,
and can therefore explain nothing.

**[ch06 · Queueing, and the knee](#queueing-and-the-knee)** buys a mechanism and pays for it in
assumptions. It also takes the knee out of its own title. The curve has no corner in it, and what
people point at is their own tolerance.

**[ch07 · When adding servers stops helping](#when-adding-servers-stops-helping)** is the obvious
response to a system that is too busy: buy more machines. It works less well than the arithmetic
suggests, and past some count it works in reverse.

**[ch08 · Regime changes](#regime-changes)** is the argument the other three have been
assembling. A threshold with different physics on either side is something no product of
quantities can express, however careful anybody is about the inputs. That is why the model file
format has a node kind for it, and why the toolkit refuses a model that declares a limit without
a margin.

If you take one thing from this part, take this: **the model is not wrong about the number; it is
wrong about what the number means past a point it cannot represent**.
