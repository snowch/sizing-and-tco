---
title: "Part IV — Uncertainty"
short_title: "Part IV — Uncertainty"
---

(part-uncertainty)=
# Part IV — Uncertainty

> The number is indefensible. What is the machinery for saying how indefensible?

Two chapters, placed here rather than at the front of the book on purpose. The method is not
useful until you have a model that has produced a number you cannot defend, and
[ch11](#the-sizing-model) is where that happened.

[ch12](#monte-carlo) gives you the whole technique, from first principles, in about as much code
as fits on a page. It assumes you can read code and do arithmetic, and nothing at all about
statistics. Four words of vocabulary arrive in it, each because a model has just raised a question
that needs it.

[ch13](#correlation-and-convergence) picks up the two things the first chapter assumed without
establishing: that the inputs move independently, and that a hundred thousand samples was enough.
Draw inputs independently when they in fact move together, and the model reports a narrower
interval than the evidence supports. More samples do not narrow an interval at all; they settle
where it sits.

Read both knowing what neither can do, which is [ch19](#the-missing-node)'s subject: sampling
quantifies the uncertainty a model can see, beautifully, and says nothing whatever about the
uncertainty it cannot.
