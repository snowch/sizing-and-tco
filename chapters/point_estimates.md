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

Here is an example of the first of the two. When you work the web service arithmetic the way we just did—all inputs at their bottom, then all at their top—you get two answers. The point estimate (all at middle) sits between them. But not in the middle. Most futures need more hosts than the point estimate says.

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

You know this without servers. Suppose you take a taxi to work and the fare is charged by the minute. Ask someone: *how much will your commute cost this year?* They do not give a number. They say: *"Maybe 250 days, maybe 260 if I'm in the office more. 25 minutes usually, 40 if the bypass is busy. The rate is around £0.50 a minute, might be £0.75 in rush hour."*

That is three ranges, not three numbers. Work through what that means:

| Run | Days | Minutes/day | Rate/min | Total cost |
|-----|------|-------------|----------|-----------|
| 1 (most likely) | 250 | 25 | £0.50 | £3,125 |
| 2 (worse growth) | 260 | 25 | £0.50 | £3,250 |
| 3 (worse traffic) | 250 | 40 | £0.50 | £5,000 |
| 4 (worst case) | 260 | 40 | £0.75 | £7,800 |

The arithmetic is right in each run. But the four answers are different. Pick one number? Which one did you pick? You do not know.

If you picked the middle value for each (250 days, 25 minutes, £0.50), you got run 1. But the future could be run 2, 3, or 4. Run 4 costs more than twice as much.

A point estimate assumes everything lands in the middle. Reality does not work that way.

Problem 1.2 does the same arithmetic on the web service model: all six inputs at their bottom together, then all at their top. Two runs, two answers. The second is not the widest input alone, and not their average. It is what happens when everything goes the wrong way at once.

The honest answer to *how big* is not one number. It is the list of answers you could get depending on what turns out to be true.

### The error a range cannot show

So far this is about how wide the answer is. Now a different error: one that running the arithmetic again cannot find, and which decides whether your model needs the second half of this book.

Almost all of the first row's width came from the growth rate. It is a forecast. It compounds over five years. It moves the host count more than any other input. Finding that out, rather than guessing, is later in this book. It is the most useful thing you can do with a model you have.

The second row moves for different reasons. It is the cost of the fleet you decided to buy. The growth rate does not reach it. You can be wrong about how many hosts you need and right about what the fleet costs. One is a question about the world. The other is arithmetic on a decision you already made. Keeping those apart is most of Parts III and V.

Letting inputs vary is honest work, and most of this book is about doing it well. But it reports only the doubt you wrote down. There is a second kind of error it cannot see. Whether you meet it depends on which of two kinds of model you have.

:::{div}
:class: definition

**Cost model.** Deterministic structure with uncertain parameters. Its relationships are accounting identities and physics: watts times hours times price; capital plus running cost; a total divided by a denominator. Nothing in that structure is in doubt. Only the inputs are uncertain. Cost moves roughly with them, so running the arithmetic over their ranges is enough. A cost model fails when a price was wrong, rarely when the system behaves differently.
:::

:::{div}
:class: definition

**Sizing model.** The same structure plus two things.

*Measured constants.* How much smaller a record is on disk than in memory after compression. How many records one request leaves. How much work one processor core does per second. These are measured, not derived. Each belongs to one implementation at one version. Each has a measurement error. None is a fact about the world. A chain of multiplications built on them inherits their errors, their version, and their standing as measurements, not facts. A model that hides all three treats them as constants.

*Non-linear ceilings.* The queueing knee, where response time climbs steeply with spare capacity left. A host failing at the busy hour, so its load lands on already busy survivors. A new field on a measurement, multiplying stored things by how many values the field takes. A working set outgrowing memory. These are regime changes. **A chain of multiplications cannot model a regime change.** It reports a system running at several times its own limit, which cannot happen.
:::

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

**1.2 — How wide are they together?** Look at the taxi table above. What is the ratio of run 4's cost to run 1's cost? Compare that ratio to the six you found in problem 1.1. The combined effect is wider than any single input's effect. This is why a point estimate cannot be defended by pointing at how carefully each input was chosen.

```bash
python3 -m pytest tests/point_estimates/test_problem_2_together.py -m problem
```

**1.3 — Find where it changes kind.** Below are the six stages of this book's web service model,
in the order the book builds it. Say which are cost models and which are sizing models, at which
stage the kind changes, and which node makes the change.

**Stage 1.** What the service is asked to do: the busy-hour request rate on day one
(`peak_request_rate_t0`), the records held on day one (`stored_data_t0`), how fast both grow each
year (`annual_growth`), and how many years the fleet must last (`horizon`). From these it computes
the busy hour and the records held at the end of that time.

**Stage 2.** Stage 1, plus the memory one host carries (`ram_per_host`), as the vendor quotes it,
and the share of that memory the operating system keeps (`os_reserve`). From these it computes
the memory the service can use on each host.

**Stage 3.** Stage 2, with the busy-hour rate, the growth rate and the operating system's share
each given as a range instead of one number. It adds how much busier the busy hour is than the
average hour (`peak_to_mean`), also a range, and the average rate that implies.

**Stage 4.** Stage 3, plus the processor time one request takes (`service_demand`), an assumption
given as a range because no reference machine has measured it; the cores one host has
(`cores_per_host`), as the vendor quotes it; and how many hosts you buy (`hosts`), which is your
decision. From these it computes how busy the fleet is (`utilisation`) and how many requests are
in flight.

**Stage 5.** Stage 4, plus the time a request spends queueing and in the system; the highest
utilisation the waiting-time formula will accept (`utilisation_cap`); a margin you choose
(`queueing_margin`); and a declared limit (`queueing_headroom`): utilisation at the busy hour must
stay that margin below a fully busy fleet.

**Stage 6.** Stage 5, plus two properties of the software, each a range: the share of the work
that cannot run in parallel (`contention`) and the cost of hosts agreeing with each other
(`crosstalk`). From these it computes the throughput the fleet can really reach, and it adds two
more declared limits: on utilisation once that coordination is counted (`coordination_headroom`),
and on the share of the fleet doing nothing useful (`scaling_loss`).

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
