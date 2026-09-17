---
title: "Part I — What you are sizing"
short_title: "Part I — What you are sizing"
---

(part-what-you-are-sizing)=
# Part I — What you are sizing

> Which quantities size a system, where they come from, and how much any of them is worth?

This part begins the model the book carries all the way through: a storage cluster, sized in
Part III and costed in Part V. Three chapters, all of them about demand — what arrives, what
accumulates, and how sure anybody is of either.

**[ch01 · What a workload is](#what-a-workload-is)** separates rates from levels, and what the
world does to you from what you have decided to do about it. It writes the first nodes of the
storage model, and ends with a file that runs and a table that cannot yet tell the two apart.

**[ch02 · Where the numbers come from](#where-the-numbers-come-from)** is the difference between a
number you measured, a number you were told and a number you decided — which is invisible once all
three are cells in one column. It is also where a *measured constant* stops being a fact about the
world and becomes a fact about some software at some version.

**[ch03 · Peak, mean and growth](#peak-mean-and-growth)** picks the number in a demand curve that
actually sizes you, and then turns to growth: the input that does most of the damage in this book,
and the one no amount of provenance discipline can turn into a measurement.

Nothing here is about what a system *does* with the demand. That is Part II, and it is where the
arithmetic stops being multiplication.
