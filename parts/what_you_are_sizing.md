---
title: "Part I — What you are sizing"
short_title: "Part I — What you are sizing"
---

(part-what-you-are-sizing)=
# Part I — What you are sizing

> Which quantities size a system, where they come from, and how much any of them is worth?

This part has four chapters. The first is what a single number is worth, and it is why the other
three exist.

Those three begin the model the book carries all the way through: a web service and its data on a
fleet of hosts, sized in Part III and costed in Part V. They are mostly about demand: what arrives,
what accumulates, and how sure you can be of either.

**[ch01 · Point estimates](#point-estimates)** is the argument the rest of the book answers. A point
estimate is not wrong. It is silent about the ranges it threw away when it picked one value for each
input. It is also silent about an error that running the arithmetic again cannot find. ch01 draws
the line this book is built on: on one side is a *definitional model*, built only from relationships
that hold by definition; on the other is a *conditional model*, which rests on a measured constant
or runs into a limit.

**[ch02 · What a workload is](#what-a-workload-is)** writes the first nodes of the web service
model: the rate of requests that arrive and the volume of data that accumulates. It shows why
those two are different and where the boundary is between what the world does and what you decide.

**[ch03 · Where the numbers come from](#where-the-numbers-come-from)** separates three kinds of
number: what you measured, what you were told, and what you decided. In a spreadsheet they look the
same once they are all cells. A measured constant belongs to one implementation at one version, and
ch03 shows what that means: a compression ratio is a property of some data and some software at a
version, and it moves when either changes. The chapter also adds the model's first hardware node:
the memory each host gives the service.

**[ch04 · Peak, mean and growth](#peak-mean-and-growth)** shows which number in a demand curve sizes
you, the busy hour, and what the mean is for. Then it turns to growth. In the web service model,
growth moves the busy-hour demand at the horizon more than any other input, because it is the one
input raised to a power. No amount of provenance discipline can make growth a measurement instead of
a forecast.

Nothing in Part I is about what a system *does* with the demand. Part II is. It opens with a law
that is one multiplication and ends with limits that no chain of multiplications can
represent—thresholds where the system behaves differently on each side.
