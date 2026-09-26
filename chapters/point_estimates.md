---
title: "Point estimates"
short_title: "ch01 Point estimates"
---

(point-estimates)=
# ch01 · Point estimates

## The question

What is a single number worth, and what can it not tell you, even when the arithmetic is right?

You need to buy hosts for a new service. The order goes in this week. So you multiply: requests in the busy hour, processor time each one takes, cores per host.

None of those is a single number. Traffic has grown at a different rate each year. You have not chosen a host yet. So you pick the middle value for each — what most people do. The arithmetic is straightforward. What comes out is one number. Nothing in it tells you whether it is safe to sign for.

Two things are hidden in that one number.

1. **The ranges you threw away.** Each input's middle value went into the arithmetic as if it were known exactly. The answer has no trace of the range each input came from.
2. **A structural flaw.** A chain of multiplications cannot see the queueing knee: the point where spare capacity runs out and response time climbs steeply. Measuring the inputs better will never find this error.

The table below shows the first of these for the book's own web service model, in its finished form. It has two rows: the hosts the model recommends, and the five-year total cost of ownership.

The column headed *Point estimate* is the arithmetic done once, with every input at the middle of its range—the value it is as likely to fall below as above. The column headed *Smallest and largest answer* is the same arithmetic done many times over, each time with every input taking a fresh value from its range. That value is usually inside the ends the model gives it, and for some inputs now and then beyond them.

Each end of that column is a single answer: the most extreme one out of all those repetitions. That is why it is unlikely but possible.

```{include} _generated/point-estimates-outputs.md
```

The two ends are far apart. The point estimate sits much nearer the smallest answer than the largest, in both rows. The method that produced the second column is taught in [ch13](#monte-carlo).

## The material

### A point estimate is not wrong. It is silent.

A **point estimate** is the number you get when you pick one value for every input—typically the middle of a range—and do the arithmetic once. It is what a spreadsheet gives. It is what sizing conversations are about.

To size a fleet for a web service you need:

- requests in the busy hour;
- growth rate;
- processor time per request;
- data kept in memory;
- cores, memory and disk per host;
- host cost.

You know none of these exactly. The growth rate is a forecast. The processor time came from someone else's build. The price is a quote that expires next month.

Pick the middle of each and multiply. You get one number. The arithmetic is right. But you had six ranges, not six numbers. You threw the ranges away at step one.

Multiplying uncertain numbers does not average their doubt. It compounds it.

:::{div}
:class: example

You know this without servers. Suppose you take a taxi to work and the fare is charged by the minute. Ask someone: *how much will your commute cost this year?* They do not give a number; they say: *"Maybe the usual number of days, a few more if I'm in the office much. The ride is usually short, but much longer when the bypass is busy. The fare is the usual rate, though higher in rush hour."*

That is three ranges, not three numbers. The table below works out the year's fares for each combination: the usual commute first, then each input moved on its own to its most, then all three at once.

| Run | Days | Minutes/day | Rate/min | Total cost |
|-----|------|-------------|----------|-----------|
| 1 (most likely) | 250 | 25 | £0.50 | £3,125 |
| 2 (worse growth) | 260 | 25 | £0.50 | £3,250 |
| 3 (worse traffic) | 250 | 40 | £0.50 | £5,000 |
| 4 (worst case) | 260 | 40 | £0.75 | £7,800 |

The arithmetic in every row is right. Each input moved on its own raises the fares, some a little and some a lot; all three together raise them further than any one does alone. Each usual value is the bottom of its range, so every surprise costs more. If you pick one value for each input, the usual one, you get the first row: a point estimate that is also the cheapest year you could have. One number cannot tell you which row your year will be.

:::


A point estimate treats every input as landing on the value you picked. The table shows what happens when some of them do not.

The honest answer to *how big* is not one number. It is the list of answers you could get depending on what turns out to be true.

### The error a range cannot show

So far this page is about how wide the answer is. There is a second kind of error that running the arithmetic again cannot find. Varying the inputs across their ranges reports only the doubt you wrote down. One question tells you whether your model is exposed to it, and so whether the model needs ceilings with a declared margin below each:

**Is the answer guaranteed to be right if every input is right?**

If yes, you have a definitional model. If no, you have a conditional one.

:::{div}
:class: definition

**Definitional model.** A model built only from relationships that hold by definition: watts times hours times price, requests times bytes per request, capital plus running cost. If every input is right, the answer is right. All of its doubt is in its inputs, so running the arithmetic over their ranges shows you all of it.
:::

:::{div}
:class: definition

**Conditional model.** A model that holds only on conditions. It has at least one of two things a definitional model does not.

*Measured constants.* How much smaller a record is on disk than in memory after compression. How much work one processor core does per request. These are measured, not derived. Each belongs to one implementation at one version, and each has a measurement error. Upgrade the software and the constant is not uncertain, it is wrong, and it lies outside the range you gave it, because that range described the old version.

A number is a measured constant because of where it came from, not because of what it measures. Processor time per request is a measured constant when somebody measured it on one implementation at one version, and the model records it as that measurement. When you estimated it or chose it, it is an ordinary uncertain input with a range, and on its own it leaves the model definitional.

*Ceilings.* The queueing knee, where response time climbs steeply while there is still spare capacity. A host failing at the busy hour, so its load lands on survivors that are already busy. A working set outgrowing memory. These are regime changes, and **a chain of multiplications cannot model a regime change.** It carries on past the limit as if nothing happened, and reports a system running at several times its own limit.

Every input can be right and the answer still wrong. So a conditional model must declare the headroom—the margin below each ceiling—it will not cross. The toolkit enforces this: you cannot build one without these declarations.
:::

The toolkit works out which kind a model is from what is in it: one measured constant or one ceiling makes it conditional, and nobody declares this by hand. The names say what a model contains, not what it is for. A model that works out how many hosts to buy can still be definitional, and the web service model is, until [ch06](#queueing-and-the-knee) adds its first ceiling. When this book says *sizing model* or *cost model* it means what those words mean at work: the model that produces a host count, and the model that turns it into money. Problem 1.3 gives you three model descriptions to sort by kind.

## What this cannot tell you

**What the model's structure omits.** Everything above is about a model already written down. A quantity nobody thought of appears nowhere in the model, and no amount of doing the arithmetic again puts it there. The observability model has no line for the network between its tiers: nothing in the model knows that line is missing. This gap differs from the unmeasured number the introduction mentions, which has a place in the model and is marked as not yet measured; a term nobody thought of has no place, so nothing marks it. [ch20](#the-missing-node) is about this second kind of gap.

**Whether the spread is right.** The range reports the spreads in the file. If the growth rate's spread was a guess nobody checked, the range inherits the guess. It says nothing about it. The difference between measurement, claim and guess decides whether a range is a finding or decoration.

**How much the range should worry you.** A wide range on a number nobody will act on for a year is not a problem. A narrow one on a purchase order might be. The arithmetic knows neither. This book has no opinion about your risk appetite.

## Key takeaways

:::{div}
:class: takeaways

- **A point estimate is silent, not wrong.** One value per input and the arithmetic done once gives
  a correct number that says nothing about how far it could be out.
- **Doubt compounds along a chain of multiplications.** Moving several uncertain inputs at once
  moves the answer further than any single input does on its own; the taxi table shows this—its
  last row costs more than any other row. The honest answer to *how big* is the range of answers
  you could get, not one figure.
- **A range reports only the doubt you wrote down.** An error in the model's shape is invisible
  to any amount of varying the inputs.
- **One question sorts every model.** Is the answer guaranteed to be right if every input is right?
  If yes, the model is definitional and all its doubt is in its inputs. If no, it is conditional:
  it rests on measured constants or ceilings, and must say how much room it keeps below each
  limit.
- **The kind is read from the file, never declared.** A measured constant or a declared limit makes
  a model conditional, and the toolkit works that out from what is in the model.
:::

## Problems

Four in `tests/point_estimates/`. The first three have tests: run with `python3 -m pytest tests/point_estimates/ -m problem`. The fourth has no test.

**1.1 — How wide is one input?** The test gives you the band the web service model declares for each of six inputs that move the host count. Write each as its top over its bottom.

```bash
python3 -m pytest tests/point_estimates/test_problem_1_each_input.py -m problem
```

**1.2 — How wide are they together?** Look at the taxi table: its rows move one input at a time to its most, then all three at once. For each row, work out how many times the usual commute's fares that row costs. The test gives you those multiples for the inputs moved alone, and asks for the multiples when several of them move together: all three and each pair. What you return is a rule that works for any set of them, not a number read off the last row. This is why a point estimate cannot be defended by pointing at how carefully each input was chosen.

```bash
python3 -m pytest tests/point_estimates/test_problem_2_together.py -m problem
```

**1.3 — Find where it changes kind.** Below are three descriptions of models for sizing a web service. Which are definitional (relationships true by definition, uncertain inputs only), and which are conditional (a measured constant or a ceiling added)? For each, return `definitional` or `conditional`.

**Model A.** Cores busy at the peak equals peak requests per second times processor time per request. The peak rate is a forecast, with a range. The processor time per request is an estimate, with a range, that nobody has measured.

% number-ok: measured constant example, not a measurement of the book's model
**Model B.** The arithmetic is the same as Model A. The processor time per request was measured at 0.5 ms on version 2.1 of the backend.

% number-ok: the example's own limits, not measurements of the book's model
**Model C.** The arithmetic is the same as Model A, with the same two inputs. Requests in flight equals peak rate times time each request spends in the service (Little's law, a relationship [ch05](#littles-law) shows is true of any system, whatever is inside it). Response time climbs steeply once the cores are busy more than 75% of the time, so the model keeps them below that. A host gains less benefit from each core it adds beyond 32 cores, because the cores contend with each other.

```bash
python3 -m pytest tests/point_estimates/test_problem_3_which_kind.py -m problem
```

**1.4 — Your own system.** No test.

Take a system you run. Write down three to six numbers that decide how big it must be. Not everything you know about it: what would change the answer. Beside each, write where it came from: measured, told by a supplier, or decided.

Then answer two questions. Which, if wrong by half, would change what you would buy? Is there a constant somebody measured on one version of one piece of software? Or a limit your system hits before running out of capacity? If so, you are holding a conditional model: every input in it can be right and the answer still wrong.

A good answer is short, names its sources, and is uncomfortable somewhere. Your answer is not finished if any of these is true:

- a number beside which you cannot write where it came from;
- a number you wrote down as measured that was measured on a different version, or a different system, from the one you run;
- a limit you found only after you had decided whether your model is definitional or conditional;
- no number on your list, wrong by half, would change what you would buy, so the list is missing the numbers that decide the size.

Keep your answer. Every chapter ends with a problem about a system you run, and they work best on the same one.

## Where to go next

[ch02](#what-a-workload-is) starts the model. It writes the first nodes to compute a busy hour and a data volume at the horizon. It refuses to multiply a rate by a plain number.

[ch03](#where-the-numbers-come-from) answers the question this chapter deferred: once you write a number down, what are you claiming about it?
