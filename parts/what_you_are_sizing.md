---
title: "Part I — What you are sizing"
short_title: "Part I — What you are sizing"
---

(part-what-you-are-sizing)=
# Part I — What you are sizing

> Which quantities size a system, where they come from, and how much any of them is worth?

Four chapters, all about demand: what arrives, what accumulates, and how sure anybody is of
either.

The first is what a single number is worth, and it is why the other three exist. Those three begin
the model the book carries all the way through: a web service and its data on a fleet of hosts,
sized in Part III and costed in Part V.

**[ch01 · Point estimates](#point-estimates)** is the argument the rest of the book answers. A
point estimate is not wrong. It is silent, about the spread it threw away at the first
multiplication and about the kind of error no amount of sampling can see. It also draws the line
this book is built on, between a model whose structure nobody doubts and one that rests on a
measured constant or runs into a limit.

**[ch02 · What a workload is](#what-a-workload-is)** writes the first nodes of the web service
model: the rate of requests that arrive and the volume of data that accumulates. It shows why
those two are different and where the boundary is between what the world does and what you decide.

**[ch03 · Where the numbers come from](#where-the-numbers-come-from)** separates three kinds of
numbers: what you measured, what you were told, and what you decided. Those three categories
disappear into one column once they are all cells together. This is where a *measured constant*
stops being a fact about the world and becomes a fact about a piece of software at a version.

**[ch04 · Peak, mean and growth](#peak-mean-and-growth)** shows which number in a demand curve
matters most for sizing, then turns to growth. Growth moves the answer further than any other
input in this book, and no amount of provenance discipline can make it a measurement instead of
a forecast.

Nothing here is about what a system *does* with the demand. That is Part II, and it is where the
arithmetic stops being multiplication.
