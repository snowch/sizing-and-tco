---
title: "Preface"
short_title: Preface
---

(preface)=
# Preface

*How to size a system, cost it, and know how much to trust the answer.*

## What this book is about

Somebody asks how big the system needs to be. How many machines, how much storage, and how much
it will cost to run for the next three years. They are going to spend real money on whatever you
tell them.

**How big, how much, and how wrong could I be?**

The first two questions are arithmetic.

:::{div}
:class: definition

**Sizing** means working out how much hardware a stated workload needs, and where that hardware
stops coping.
:::

:::{div}
:class: definition

**Total cost of ownership** (TCO) means what that hardware costs over the years you keep it. That
is not the same as what it costs to buy.
:::

Anybody can do the arithmetic for both.

## The question this book answers

Understanding how trustworthy your answer is: the hardest and most important question in sizing and
TCO. Almost nobody is taught it. This book teaches you.

To answer it you need to know:

- which input your answer rests on;
- how far the answer moves when that input moves; and
- what it would cost to find out.

[ch01](#point-estimates) starts there. It shows you what a single number leaves out.

## How the model works

You build one model, and it lasts the whole book.

:::{div}
:class: definition

**Model** — a YAML file containing numbers with their units and sources, plus formulas connecting them.
:::

We build it this way so you can reason about your system: which numbers matter, how they connect,
what happens when they change. Each number has a name, a unit, and a note saying where its value
came from. Each computed number has a formula that refers to the others by name. You can read a
whole model in one sitting.

The model grows through the book. [ch02 · What a workload is](#what-a-workload-is) writes the
first nodes: what arrives and what accumulates. Later chapters add pieces: where each number came
from, what the hardware can hold, where it stops coping, what it costs.
[ch12 · The sizing model](#the-sizing-model) produces a host count.
[ch18 · The five-year model](#the-five-year-model) produces a cost.

Every figure in this book is computed from that file as it stands at that point.

## Why a file, and not a spreadsheet

A spreadsheet cell holds a value and nothing about it. It doesn't tell you the unit, where it came from, or how certain it is. Everything this book does depends on those three things being written down beside the number.

The toolkit enforces what spreadsheets cannot:

- Units on every formula
- Provenance (fact, claim, assumption)
- Measurement status
- Limits with headroom
- Dependency tracking

A spreadsheet loses all of this on the first copy.

[ch02](#what-a-workload-is) writes the first nodes of the model. Each number in the file carries
a unit and a line saying where it came from, and the **build**, the set of checks that turns
these files into this book, refuses a node that leaves either out.

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
about statistics. This book introduces statistical terms as it needs them, in plain English first.
All terms are defined in the chapter where they first matter.

Two models carry the book. Both are written so that the structure is the point and the numbers are
yours to replace:

- a web service and its data, on a fleet of Linux hosts. It is sized and costed end to end, and
  how it behaves under load is not a chain of multiplications at all; and
- an observability platform, which has a hole in it where a measurement should be.

Every chapter ends with problems. Most are implemented as Python tests that fail until you have solved them.

The last problem in every chapter is different. It asks about a system you run, and no test can
check your answer, because only you have the system. Instead, the problem tells you what a good
answer looks like, and what would show that yours is wrong.

## What you need

To read the book and run its models: nothing. The book is a website, and the models are things
you drag. The prose reads on any screen. The models want a tablet held sideways or larger.

All models and code run in your browser.

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
