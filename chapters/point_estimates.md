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

Two things are hidden in that number.

1. **The ranges you threw away.** Each middle went into the arithmetic as a measured fact. What came out has no trace of the range it came from. Later you will give the model the full range instead of its middle and get a range of answers back.
2. **A structural flaw.** A chain of multiplications cannot see the queueing knee: the point where spare capacity runs out and response time climbs steeply. Measuring the inputs better will never find this error.

:::{note}
Both flaws will be addressed as the book progresses: structural limits in [ch06](#queueing-and-the-knee), and ranges in [ch13](#monte-carlo).
:::

Here is an example of the first of the two. When you work the web service arithmetic the way we just did—all inputs at their bottom, then all at their top—you get two answers. The point estimate (all at middle) sits between them. But not in the middle. Most possible outcomes need more hosts than the point estimate says, as [ch13](#monte-carlo) will show.

```{include} _generated/point-estimates-outputs.md
```

The first row shows the point estimate (54). Beside it are the smallest and largest answers (3 to 1,481). They are not close. These extremes are unlikely, but possible.

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

You know this without servers. Suppose you take a taxi to work and the fare is charged by the minute. Ask someone: *how much will your commute cost this year?* They do not give a number. They say: *"Maybe 250 days, maybe 260 if I'm in the office more. 25 minutes usually, 40 if the bypass is busy. The rate is around £0.50 a minute, might be £0.75 in rush hour."*

That is three ranges, not three numbers. Work through what that means:

| Run | Days | Minutes/day | Rate/min | Total cost |
|-----|------|-------------|----------|-----------|
| 1 (most likely) | 250 | 25 | £0.50 | £3,125 |
| 2 (worse growth) | 260 | 25 | £0.50 | £3,250 |
| 3 (worse traffic) | 250 | 40 | £0.50 | £5,000 |
| 4 (worst case) | 260 | 40 | £0.75 | £7,800 |

The arithmetic is right in each run. But the four answers are different. Pick one number? Which one did you pick? You do not know.

If you picked the middle value for each (250 days, 25 minutes, £0.50), you got run 1. But the outcome could be run 2, 3, or 4. Run 4 costs more than twice as much.

:::


A point estimate assumes everything lands in the middle. Reality does not work that way.

The honest answer to *how big* is not one number. It is the list of answers you could get depending on what turns out to be true.

### The error a range cannot show

So far this is about how wide the answer is. Now a different error: one that running the arithmetic again cannot find, and which decides whether your model needs the second half of this book.

Almost all of the first row's width in the web service model came from the growth rate. It is a forecast. It compounds over five years. It moves the host count more than any other input. Finding that out, rather than guessing, is [ch19](#which-input-is-the-answer). It is the most useful thing you can do with a model you have.

The second row (costing) moves for different reasons. Once you decide how many hosts to buy, the cost is just arithmetic. Sizing is about the world; costing is about a decision you have already made. Keeping those apart is most of Parts III and V.

Varying inputs across their ranges gives you the complete picture, and most of this book teaches how to do it well. But it reports only the doubt you wrote down. There is a second kind of error it cannot see, and one question tells you whether your model is exposed to it:

**Is the answer guaranteed to be right if every input is right?**

If yes, you have a definitional model. If no, you have a conditional one.

:::{div}
:class: definition

**Definitional model.** A model built only from relationships that hold by definition: watts times hours times price, requests times bytes per request, capital plus running cost. If every input is right, the answer is right. All of its doubt is in its inputs, so running the arithmetic over their ranges shows you all of it.
:::

:::{div}
:class: definition

**Conditional model.** A model that holds only on conditions. It has at least one of two things a definitional model does not.

*Measured constants.* How much smaller a record is on disk than in memory after compression. How much work one processor core does per request. These are measured, not derived. Each belongs to one implementation at one version, and each has a measurement error. Upgrade the software and the constant is not uncertain, it is wrong, and it is outside the range you gave it, because that range described the old version.

*Ceilings.* The queueing knee, where response time climbs steeply while there is still spare capacity. A host failing at the busy hour, so its load lands on survivors that are already busy. A working set outgrowing memory. These are regime changes, and **a chain of multiplications cannot model a regime change.** It carries on past the limit as if nothing happened, and reports a system running at several times its own limit.

Every input can be right and the answer still wrong. So a conditional model keeps a declared margin, its headroom, below each ceiling, and the toolkit will not build one that does not.
:::

The names say what a model contains, not what it is for. A model that works out how many hosts to buy can still be definitional, and the web service model is, until [ch06](#queueing-and-the-knee) adds its first ceiling. When this book says *sizing model* or *cost model* it means what those words mean at work: the model that produces a host count, and the model that turns it into money.

### Where a definitional model becomes a conditional one

The kind decides what you must guard against. In a definitional model, uncertainty in the inputs produces uncertainty in the output, and ranges on the inputs alone tell you everything you need. In a conditional model, an input can be inside its range and the answer still be wrong—because an unstated ceiling has been crossed. The toolkit reads the kind from the file: add one measured constant or one ceiling and the verdict changes. Problem 1.3 asks you to find that moment in three model descriptions.

## What this cannot tell you

**What the model's structure omits.** Everything above is about a model already written down. A quantity nobody thought of appears nowhere in the model. No amount of running the arithmetic will put it there. The observability model has a hole of that shape.

**Whether the spread is right.** The range reports the spreads in the file. If the growth rate's spread was a guess nobody checked, the range inherits the guess. It says nothing about it. The difference between measurement, claim and guess decides whether a range is a finding or decoration.

**How much the range should worry you.** A wide range on a number nobody will act on for a year is not a problem. A narrow one on a purchase order might be. The arithmetic knows neither. This book has no opinion about your risk appetite.

## Key takeaways

:::{div}
:class: takeaways

- **A point estimate is silent, not wrong.** One value per input and the arithmetic done once gives
  a correct number that says nothing about how far it could be out.
- **Doubt compounds along a chain of multiplications.** Multiplying uncertain numbers stretches
  the answer further than any single input does, so the honest answer to *how big* is a range with
  a most-likely region in it, not a figure.
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

**1.2 — How wide are they together?** Look at the taxi table above. What is the ratio of run 4's cost to run 1's cost? Compare that ratio to the six you found in problem 1.1. The combined effect is wider than any single input's effect. This is why a point estimate cannot be defended by pointing at how carefully each input was chosen.

```bash
python3 -m pytest tests/point_estimates/test_problem_2_together.py -m problem
```

**1.3 — Find where it changes kind.** Below are three descriptions of models for sizing a web service. Which are definitional (relationships true by definition, uncertain inputs only)? Which are conditional (adding measured constants or ceilings)? Name the measured constants or ceilings that decide it.

% number-ok: model example, not a measurement
**Model A.** Peak requests per second × processor time per request × (100% ÷ utilization fraction) = cores needed. Inputs: peak rate (assumption), processor time per request (assumption), utilization (assumption).

% number-ok: measured constant example, not a measurement of the book's model
**Model B.** Same structure. The processor time per request was measured at 0.5 ms on version 2.1 of the backend.

% number-ok: uncertainty examples and ceilings, not measurements of the book's model
**Model C.** Same structure, plus: requests in flight = peak rate × time per request (Little's law). Response time climbs steeply when utilization exceeds 75%. A host can scale from 1 to 32 cores; beyond that, adding more cores helps less (contention). These are ceilings: the model cannot run at 150% utilization or with infinite cores, but arithmetic alone would claim it could.

```bash
python3 -m pytest tests/point_estimates/test_problem_3_which_kind.py -m problem
```

**1.4 — Your own system.** No test.

Take a system you run. Write down three to six numbers that decide how big it must be. Not everything you know about it: what would change the answer. Beside each, write where it came from: measured, told by a supplier, or decided.

Then answer two questions. Which, if wrong by half, would change what you would buy? Is there a constant somebody measured on one version of one piece of software? Or a limit your system hits before running out of capacity? If so, you are holding a conditional model: every input in it can be right and the answer still wrong.

A good answer is short, names its sources, and is uncomfortable somewhere. Keep it. Every chapter ends with a problem about a system you run. They work best on the same one.

## Where to go next

[ch02](#what-a-workload-is) starts the model. It writes the first nodes to compute a busy hour and a data volume at the horizon. It refuses to multiply a rate by a plain number.

[ch03](#where-the-numbers-come-from) answers the question this chapter deferred: once you write a number down, what are you claiming about it?
