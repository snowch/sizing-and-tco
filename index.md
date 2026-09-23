---
title: "Introduction"
short_title: Introduction
---

(preface)=
# Introduction

*How to size a system, cost it, and know how much to trust the answer.*

## What this book is about

Somebody asks how big the system needs to be. How many machines, how much storage, and how much
it will cost to run for the next three years. They are going to spend real money on whatever you
tell them.

**How big, how much, and how wrong could I be?**

The first two questions are arithmetic.

**Sizing** means working out how much hardware a stated workload needs, and where that hardware
stops coping.

**Total cost of ownership** (TCO) means what that hardware costs over the years you keep it. That
is not the same as what it costs to buy.

Anybody can do the arithmetic for both.

## The question this book answers

The third question is the hard one, and it is the one this book teaches. To answer it you need
to know:

- which input your answer rests on;
- how far the answer moves when that input moves; and
- what it would cost to find out.

Almost nobody is taught this. It is what decides whether anybody should act on your number.

[ch01](#point-estimates) starts there. It shows you what a single number leaves out.

## How the model works

You build one model, and it lasts the whole book.

A model here is a YAML file: plain text you can read and edit. Each number has a name, a unit,
and a note saying where its value came from. Each computed number has a formula that refers to the
others by name. You can read a whole model in one sitting.

The model grows through the book. [ch02 · What a workload is](#what-a-workload-is) writes the
first nodes: what arrives and what accumulates. Later chapters add pieces: where each number came
from, what the hardware can hold, where it stops coping, what it costs. [ch12 · The sizing
model](#the-sizing-model) produces a host count. [ch18 · The five-year model](#the-five-year-model)
produces a cost.

Every figure in this book is computed from that file as it stands at that point.

## Why a file, and not a spreadsheet

A spreadsheet cell holds a value and nothing about it.

- It does not tell you the unit. Multiply the wrong two cells and the result looks like any other
  number.
- It does not tell you where the number came from. A vendor's claim and a measurement sit in the
  same column, looking the same.
- It does not tell you how certain the number is. The spread is gone after the first
  multiplication.

Everything this book does depends on those three things being written down beside the number. A
file is where they can be. A file also diffs and reviews like code.

The toolkit checks the units of every formula. A rate times a duration is an amount:
`requests per second × seconds = requests`. A rate times a plain number is still a rate. A formula
that calls it an amount is refused. [ch02](#what-a-workload-is) teaches the rule. [Appendix
D](#appendix-d-units) works through the combinations that bite.

[ch02](#what-a-workload-is) writes the first nodes of the model. Each number in the file carries
a unit and a line saying where it came from, and the **build**, the set of checks that turns
these files into this book, refuses a node that leaves either out.

## Every number can be checked

Every number in this book can be checked, and the page tells you how.

**Every number was computed, never typed in.** The italic line under each table opens the model
it came from, with every input on a slider.

**Every model is a file.** Every number declares a unit, so the toolkit refuses a model that
multiplies the wrong two things. Every input says whether it is a fact, a vendor's claim, or an
assumption. An uncertain input says what shape its uncertainty has, and why. Every measured
constant names the measurement behind it. [ch03](#where-the-numbers-come-from) explains what
those distinctions mean.

**Every chapter says what it cannot tell you.** In a book about estimates, that section is usually
the most useful part of the chapter.

## Unknown numbers stay unknown

If a required number has not been measured, the model does not invent one.

When a constant has not been measured, everything that depends on it stays unknown. Those figures
show as *not yet measured*, and the page names the chain that is blocked. There is never a
placeholder, and never a number taken from somewhere else.

## Who this book is for

This is a self-study text and a toolkit. It is for an engineer who has been asked how big
something needs to be, or what it will cost, and who wants to give an answer they would still
defend a year later.

You should be comfortable with code and with arithmetic. You are assumed to know **nothing**
about statistics. The book uses six statistical words:

% word-ok: the list of the six this book rations, which has to name them
- distribution;
- sample;
- percentile;
- interval;
- correlation; and
- convergence.

Each is used in plain English first and named second, in the chapter where a model first needs it.
[ch01](#point-estimates) shows the first spread of answers this book produces and names none of the
six. It shows the smallest and the largest of those answers and how the rest piled up between them,
and that is all it needs. The words arrive one at a time from there on, and Part IV, in
[ch13](#monte-carlo) and [ch14](#correlation-and-convergence), builds the method that produces the
spread and defines all six properly. Until then you take the spread on trust, which is a fair trade:
the method is not useful until you have a number you cannot defend.

No vendor is named anywhere in this book, and no product is recommended. Two models carry the
book. Both are written so that the structure is the point and the numbers are yours to replace:

- a web service and its data, on a fleet of Linux hosts. It is sized and costed end to end, and
  how it behaves under load is not a chain of multiplications at all; and
- an observability platform, which has a hole in it where a measurement should be.

Every chapter ends with problems. They are there so that you do what the chapter argued rather than
agree with it: write the law yourself, add the node the toolkit refuses until its unit is right, say
what a result will be and then run it. Most of them are tests: they fail until you have solved them,
and the answer is nowhere in the repository.

The last problem in every chapter is different. It asks about a system you run, and no test can
check your answer, because only you have the system. Instead, the problem tells you what a good
answer looks like, and what would show that yours is wrong.

## What you need

To read the book and run its models: nothing. The book is a website, and the models are things
you drag. The prose reads on any screen. The models want a tablet held sideways or larger.

The first models appear in [ch02](#what-a-workload-is) and [ch03](#where-the-numbers-come-from) as
live editors. Press **Run**, change a number, and try to multiply a rate by a plain number where
the file expects an amount. The build refuses it.

The finished models have a slider on every input. The appendices name them and show what they
produce.

Once you open the book, it works offline. If you press **Run** once while online, the Python
runtime is kept. **Keep offline** in the header fetches it ahead of need.

The problems run in the page. Under each one that has a test sits the code it grades, yours to
edit. **Check** runs the tests in your browser. Nothing leaves your machine.

To work the problems at a desk with an editor and shell, clone the repository:

```bash
git clone https://github.com/snowch/sizing-and-tco.git
cd sizing-and-tco
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m pytest tests/point_estimates/ -m problem
```

Nothing in this book needs a datacentre, a cloud account, or a licence.

## Where to start

[ch01](#point-estimates) shows what a single number leaves out. Read it first. Everything after
it is an answer to that.
