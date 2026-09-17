---
title: "Part IV — Uncertainty"
short_title: "Part IV — Uncertainty"
---

(part-uncertainty)=
# Part IV — Uncertainty

> The number is indefensible. What is the machinery for saying how indefensible?

Two chapters, placed here rather than at the front of the book on purpose. The method is not
useful until you have a model that has produced a number you cannot defend, and
[ch12](#the-sizing-model) is where that happened.

[ch13](#monte-carlo) gives you the whole technique, from first principles, in about as much code
as fits on a page. It assumes you can read code and do arithmetic, and it assumes nothing at all about
statistics. Four words of vocabulary arrive in it, each because a model has just raised a question
that needs it.

[ch14](#correlation-and-convergence) picks up the two things the first chapter assumed without
establishing: that the inputs move independently, and that a hundred thousand samples was enough.
Both turn out to be more interesting than they sound, and one of them is not what most people
think it is.

What neither chapter can do is the subject of [ch20](#the-missing-node), and it is worth reading
them knowing that: sampling quantifies the uncertainty a model can see, beautifully, and says
nothing whatever about the uncertainty it cannot.
