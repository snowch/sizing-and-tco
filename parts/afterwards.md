---
title: "Part VIII — Afterwards"
short_title: "Part VIII — Afterwards"
---

(part-afterwards)=
# Part VIII — Afterwards

> The design failed. What does the model have to say about that, and what does it not?

Every part before this one ends before anything happens: the model is built, the interval is
reported, the decision is taken. This part follows the design to the model's horizon, the end of the
refresh cycle the fleet was bought against, and asks what the model has to say when the design fails
at that point.

**[ch23 · What the model got wrong](#what-the-model-got-wrong)** is what happens next. It takes the
fleet [ch12](#the-sizing-model) recommended and the futures at the horizon in which the utilisation
at the busy hour went past its limit—the model's own futures, not an observed incident. It asks the
two questions a team asks afterwards: *what went wrong*, and *could we have known*.

The answers are uncomfortable in opposite directions. The model could have told you, and it did: as
a percentage, in a column nobody read out loud. In a large minority of the failures, nothing was
extreme: the busy hour, growth, and the cost of a request were each a little above their usual, and
together that was enough. The attribution the model produces afterwards is specific and ranked, and
it cannot name any cause that was not already in the file.

This part is one chapter because the lesson is one sentence: **a model gets better by being compared
against what happened, and a prediction that was not recorded before the fact cannot be compared.**
