---
title: "Part I — What you are sizing"
short_title: "Part I — What you are sizing"
---

(part-what-you-are-sizing)=
# Part I — What you are sizing

> Which quantities size a system, where they come from, and how much any of them is worth?

Four chapters. The first is about what a single number is worth, and is the reason for the other
three. Those three begin the model the book carries all the way through — a web service and its
data on a fleet of hosts, sized in Part III and costed in Part V — and all of them are about
demand: what arrives, what accumulates, and how sure anybody is of either.

**[ch01 · Point estimates](#point-estimates)** is the argument the rest of the book
answers. A point estimate is not wrong; it is silent, about the spread it threw away at the first
multiplication and about the kind of error no amount of sampling can see. It also draws the line
this book is built on, between a model whose structure nobody doubts and one that rests on a
measured constant or runs into a limit.

**[ch02 · What a workload is](#what-a-workload-is)** separates rates from levels, and what the
world does to you from what you have decided to do about it. It writes the first nodes of the
web service model, and ends with a file that runs and a table that cannot yet tell the two apart.

**[ch03 · Where the numbers come from](#where-the-numbers-come-from)** is the difference between a
number you measured, a number you were told and a number you decided — which is invisible once all
three are cells in one column. It is also where a *measured constant* stops being a fact about the
world and becomes a fact about some software at some version.

**[ch04 · Peak, mean and growth](#peak-mean-and-growth)** picks the number in a demand curve that
actually sizes you, and then turns to growth: the input that does most of the damage in this book,
and the one no amount of provenance discipline can turn into a measurement.

Nothing here is about what a system *does* with the demand. That is Part II, and it is where the
arithmetic stops being multiplication.
