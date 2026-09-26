---
title: "Part IV — Uncertainty"
short_title: "Part IV — Uncertainty"
---

(part-uncertainty)=
# Part IV — Uncertainty

> The number is indefensible. What is the machinery for saying how indefensible?

Every ceilings table since ch06 carries two columns, *Over allowed* and *Over limit*: the share of
the model's futures past the allowed line, and the share past the limit. ch06 explains what these
mean. This part shows how they are computed, in two chapters.

**[ch13 · Monte Carlo](#monte-carlo)** gives you the whole technique, from first principles, in
about as much code as fits on a page. It assumes you can read code and do arithmetic and assumes
nothing about statistics. Four words of vocabulary arrive in it, each because a model has just
raised a question that needs it.

**[ch14 · Correlation and convergence](#correlation-and-convergence)** takes up two things ch13's
figures already carry but ch13 did not explain. First, ch13 drew inputs together that move as pairs:
network price with host price, and the busy hour with what a request costs. ch14 shows how the
pairing is done and what it changed. If you treat inputs that move together as if each moved on its
own, the model reports a narrower spread of answers than the evidence supports.

Second, ch13 assumed it had run the computation enough times but did not show it. ch14 works out
what "enough" means: running the computation more times does not narrow the spread, but tells you
more precisely where it sits.

Read both knowing what neither can do, which is [ch20](#the-missing-node)'s subject. The method
shows the doubt written into the model file about the inputs it has; it says nothing about a term
the file leaves out, because nothing in the file describes that term.
