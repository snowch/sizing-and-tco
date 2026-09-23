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
2. **A flaw in the model's shape.** A chain of multiplications cannot see that a queue has tipped over. The answer describes a fleet running at several times its capacity. Measuring the inputs better will never find this error.

Here is the first of the two. When you work the web service arithmetic the way we just did—all inputs at their bottom, then all at their top—you get two answers. The point estimate (all at middle) sits between them. But not in the middle. Most futures need more hosts than the point estimate says.

```{include} _generated/point-estimates-outputs.md
```

The first row shows the point estimate you'd normally use (54 hosts). Beside it are the smallest and largest answers from all the runs (3 to 1,481). They are not close. The point estimate was right arithmetic on numbers you chose. It had no way to say it was a bet.

## The material

### A point estimate is not wrong. It is silent.

A **point estimate** is the number you get when you pick one value for every input and do the arithmetic once. It is what a spreadsheet gives. It is what sizing conversations are about.

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

You know this without servers. Ask someone: *how much will your commute cost this year?* They do not give a number. They say: *"Maybe 250 days, maybe 260 if I'm in the office more. 25 minutes usually, 40 if the bypass is busy. Fuel is around £1.30 a litre this month, might be £1.50."*

That is three ranges, not three numbers. Work through what that means:

**Run 1** (most likely): 250 days × 25 min × £1.30 = £X

**Run 2** (worse growth): 260 days × 25 min × £1.30 = £Y (higher—more days)

**Run 3** (worse traffic): 250 days × 40 min × £1.30 = £Z (higher—slower journey)

**Run 4** (worst case): 260 days × 40 min × £1.50 = £W (much higher—everything bad at once)

The arithmetic is right in each run. But the four answers are different. Pick one number? Which one did you pick? You do not know.

If you picked the middle value for each (250 days, 25 minutes, £1.30), you got run 1. But the future could be run 2, 3, or 4. Run 4 costs a lot more.

A point estimate assumes everything lands in the middle. Reality does not work that way.

Problem 1.2 does the same arithmetic on the web service model: all six inputs at their bottom together, then all at their top. Two runs, two answers. The second is not the widest input alone, and not their average. It is what happens when everything goes the wrong way at once.

The honest answer to *how big* is not one number. It is the list of answers you could get depending on what turns out to be true.

### The error a range cannot show

So far this is about how wide the answer is. Now a different error: one that running the arithmetic again cannot find, and which decides whether your model needs the second half of this book.

Almost all of the first row's width came from the growth rate. It is a forecast. It compounds over five years. It moves the host count more than any other input. Finding that out, rather than guessing, is later in this book. It is the most useful thing you can do with a model you have.

The second row moves for different reasons. It is the cost of the fleet you decided to buy. The growth rate does not reach it. You can be wrong about how many hosts you need and right about what the fleet costs. One is a question about the world. The other is arithmetic on a decision you already made. Keeping those apart is most of Parts III and V.

Letting inputs vary is honest work, and most of this book is about doing it well. But it reports only the doubt you wrote down. There is a second kind of error it cannot see. Whether you meet it depends on which of two kinds of model you have.

**A cost model has a deterministic structure with uncertain parameters.** Its relationships are accounting identities and physics: watts times hours times price; capital plus running cost; a total divided by a denominator. Nothing in that structure is in doubt. Only the inputs are uncertain. Cost moves roughly with them, so running the arithmetic over their ranges is enough. A cost model fails when a price was wrong, rarely when the system behaves differently.

**A sizing model has the same structure and adds two things.**

*Measured constants.* How much smaller a record is on disk than in memory after compression. How many records one request leaves. How much work one processor core does per second. These are measured, not derived. Each belongs to one implementation at one version. Each has a measurement error. None is a fact about the world. A chain of multiplications built on them inherits their errors, their version, and their standing as measurements, not facts. A model that hides all three treats them as constants.

*Non-linear ceilings.* The queueing knee, where response time climbs steeply with spare capacity left. A host failing at the busy hour, so its load lands on already busy survivors. A new field on a measurement, multiplying stored things by how many values the field takes. A working set outgrowing memory. These are regime changes. **A chain of multiplications cannot model a regime change.** It reports a system running at several times its own limit, which cannot happen.

A sizing model must do more than produce a number. It says how much room it keeps below each limit and why. The toolkit enforces it. A model with a measured constant or a declared limit **is** a sizing model. One with neither **is** a cost model. They are held to different rules. A sizing model that names a limit and keeps no room below it does not build.

### Where a cost model becomes a sizing model

Do not take the distinction on trust. It decides which half of this book applies. The web service model starts as a cost model and becomes a sizing model partway through. One node makes the change. Problem 1.3 is finding it at six stages of construction.

You find the stage rather than being told it.

:::{note} Key takeaways
- **A point estimate is silent, not wrong.** One value per input and the arithmetic done once gives
  a correct number that says nothing about how far it could be out.
- **Doubt compounds along a chain of multiplications.** Multiplying uncertain numbers stretches
  the answer further than any single input does, so the honest answer to *how big* is a range with
  a most-likely region in it, not a figure.
- **A range reports only the doubt you wrote down.** An error in the model's shape is invisible
  to any amount of varying the inputs.
- **Two kinds of model, held to two rules.** A cost model has a structure in no doubt and
  uncertain inputs. A sizing model adds measured constants and ceilings. It must say how much
  room it keeps below each limit.
- **The kind is read from the file, never declared.** A measured constant or a declared limit makes
  a sizing model, and the toolkit works that out from what is in the model.
:::

## What this cannot tell you

**What the model's structure omits.** Everything above is about a model already written down. A quantity nobody thought of appears nowhere in the model. No amount of running the arithmetic will put it there. The observability model has a hole of that shape.

**Whether the spread is right.** The range reports the spreads in the file. If the growth rate's spread was a guess nobody checked, the range inherits the guess. It says nothing about it. The difference between measurement, claim and guess decides whether a range is a finding or decoration.

**How much the range should worry you.** A wide range on a number nobody will act on for a year is not a problem. A narrow one on a purchase order might be. The arithmetic knows neither. This book has no opinion about your risk appetite.

## Problems

Four in `tests/point_estimates/`. The first three have tests: run with `python3 -m pytest tests/point_estimates/ -m problem`. The fourth has no test.

**1.1 — How wide is one input?** The test gives you the band the model declares for each of six inputs. Write each as its top over its bottom.

```bash
python3 -m pytest tests/point_estimates/test_problem_1_each_input.py -m problem
```

**1.2 — How wide are they together?** Do the arithmetic on paper: all six inputs at their bottom together, then at their top. Set the ratio beside the smallest and largest answers in the table above.

```bash
python3 -m pytest tests/point_estimates/test_problem_2_together.py -m problem
```

**1.3 — Find where it changes kind.** The web service model appears at six stages of construction. Classify each as cost or sizing. Name the nodes that decide it. Say why the chapter that adds those nodes could not have been written earlier.

```bash
python3 -m pytest tests/point_estimates/test_problem_3_which_kind.py -m problem
```

**1.4 — Your own system.** No test.

Take a system you run. Write down three to six numbers that decide how big it must be. Not everything you know about it: what would change the answer. Beside each, write where it came from: measured, told by a supplier, or decided.

Then answer two questions. Which, if wrong by half, would change what you would buy? Is there a constant somebody measured on one version of one piece of software? Or a limit your system hits before running out of capacity? If so, you are holding a sizing model, and your multiplications are quietly lying.

A good answer is short, names its sources, and is uncomfortable somewhere. Keep it. Every chapter ends with a problem about a system you run. They work best on the same one.

## Where to go next

[ch02](#what-a-workload-is) starts the model. It writes the first nodes to compute a busy hour and a data volume at the horizon. It refuses to multiply a rate by a plain number.

[ch03](#where-the-numbers-come-from) answers the question this chapter deferred: once you write a number down, what are you claiming about it?
