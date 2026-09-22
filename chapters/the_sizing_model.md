---
title: "The sizing model"
short_title: "ch12 The sizing model"
---

(the-sizing-model)=
# ch12 · The sizing model

## The question

What does the whole chain produce, and how much of it would you defend?

Part I described a workload. Part II found the ceilings. Part III has turned both into machines.
This chapter puts them together, arrives at a number, and then makes the number look at itself.

## The material

### The whole model in one graph

```{image} _figures/the-sizing-model-graph.svg
:alt: Everything that feeds the recommended host count
:width: 100%
```

Every node in that sub-graph has appeared in a chapter:

- the workload on the left ([ch02](#what-a-workload-is));
- the growth term ([ch04](#peak-mean-and-growth));
- the cost of a request ([ch05](#littles-law));
- the working set ([ch08](#regime-changes));
- the disk chain ([ch09](#capacity));
- a margin per chain, declared where its ceiling was; and
- the largest of the three at the end ([ch10](#bandwidth-and-the-binding-constraint)).

Follow it left to right and there is nothing surprising in it. Sizing models are not clever. They
are a dozen multiplications anybody could check, and the difficulty has never been the arithmetic.
[Appendix E](#appendix-e-web-service-model) lists every one of them, with the chapter that added
it.

### What the model recommends

```{include} _generated/the-sizing-model-outputs.md
```

The first row is the answer, evaluated at every input's point estimate. It is what a competently
built spreadsheet would give you. It is also what this book's reference fleet was bought against,
which is the second row, and the fleet's provenance says so in as many words. The three
rows below are the chains it was the largest of.

### The number looks at itself

```{image} _figures/the-sizing-model-hosts.svg
:alt: The recommended host count, as a distribution
:width: 100%
```

The red line is where the point estimate falls. Everything else is the same model, the same chains
and the same margins, with the inputs allowed to be as uncertain as the people who wrote them
down are. Notice where the line sits: below the middle of the bars.

At the point estimate each chain hands over its own middle, and the model takes the largest of the
three. Let the inputs move, and the model comes back with a smaller fleet only when *all three*
chains land low together — one chain coming in low is covered by whichever of the other two did
not. Needing three things to go your way at once is a weaker bet than needing one, so the largest
of three uncertain counts sits above the largest of their three middles. The spreadsheet's answer
is not merely uncertain. It is low.

And here is what that fleet does against the ceilings the last six chapters declared:

```{include} _generated/the-sizing-model-ceilings.md
```

At the point estimate, every ceiling but one is comfortable. Of course they are. The fleet was
sized from those point estimates against those chains, so it satisfies them by construction. The
one that is not comfortable is the one no chain was sized against:
[ch07](#when-adding-servers-stops-helping)'s utilisation counting coordination. The request chain
ignores it, because the chain divides by the fleet's processors as if each worked alone. The fleet
is inside that margin before a single input has moved. A model that reported only the verdict
column would be marking its own homework, and this one has marked it wrong in one place already.

The last two columns ask a different question. Read the *utilisation at the busy hour* row. Buy
the fleet the arithmetic recommends, and across everything this model thinks could happen, it is
over the knee at the busy hour in a substantial share of the futures. The working set has
outgrown memory in more of them still. The last column says how often, and it is not an
extreme-scenario number.

Nothing went wrong to produce that. Every input was defensible and every multiplication was
correct. The result is a fleet that stands a real chance of not lasting its horizon under the
knee. **That is what sizing from point estimates does.**

Here is all of Part III in one graph, with a slider on every input. Drag *hosts in the
fleet* and watch every ceiling's verdict at once. That is the decision this chapter is about.

```{iframe} /models/web_service_sizing-reference.html
:width: 100%
The sizing model, complete. Nothing arrives in this chapter: it is every earlier one, together.
```

```{iframe} /playground/the-sizing-model/
:width: 100%
The same file, running. It is the file ch02 started, eleven chapters on.
```

### So what is the answer?

There is not one. Part III has been building to that.

A sizing model does not produce a number. It produces a *relationship between a number and a
risk*, and somebody has to choose a point on it. Problem 12.1 is that choice made explicitly: pick
a breach probability you are willing to be accountable for, and ask the model what it costs in
machines.

That is a different conversation from "how many hosts do we need", and a better one, because it
is answerable. Here is one other point on that curve: the same model, the same ceilings, with a
fleet bought for the growth case rather than the expected one:

```{include} _generated/the-sizing-model-resized.md
```

Every figure in the last two columns falls, most of them to a few per cent. The one that falls
least is the coordination ceiling, because more hosts spend more of themselves on each other.
That is [ch07](#when-adding-servers-stops-helping)'s argument, arriving in a sizing table. What
the bigger fleet costs is [ch21](#a-tco-for-finance)'s table rather than this one. But the pair,
*what it costs* beside *how often it breaks*, is the only form in which this decision can be
handed to somebody.

Problem 12.2 is the shape of the trade, counted in hosts, because hosts are all Part III has.
Removing risk costs machines, and not at a steady rate: the last few percentage points cost more
hosts than the ones before them. Having that count is the difference between an argument and a
preference. [ch21](#a-tco-for-finance) prices the same pair of fleets, and puts the price to the
person whose decision it is.

### The decision is an input

The number of hosts in the fleet is an **input**, not a derived node, and that is the detail a
spreadsheet hides. It has a provenance and a source like any other. Sizing produces a
*recommendation*. A person then decides, once, before the five years happen. Everything
downstream, every dollar, every watt and every ceiling, follows from what they chose, not from
what the model would recommend in hindsight.

Deriving it instead would make the ceilings tautologies. A fleet sized to sit under the knee sits
under it in every future, and the model would cheerfully report no chance at all of queueing.
Keeping it an input lets the ceilings ask the only question worth asking: *given what we bought,
how often does the world break it?*

:::{note} Key takeaways
- **A sizing model is a dozen multiplications anybody could check.** The difficulty has never been
  the arithmetic.
- **The spreadsheet's answer is not merely uncertain. It is low.** The largest of three uncertain
  counts is usually larger than the largest of their three point estimates.
- **A fleet sized from point estimates satisfies its ceilings by construction, and still breaks.**
  Across the futures the model thinks plausible it is over the knee at the busy hour in a
  substantial share of them, with nothing having gone wrong.
- **A sizing model produces a relationship between a number and a risk, not a number.** Somebody has
  to pick a point on it, and the only form the choice can be handed over in is *what it costs*
  beside *how often it breaks*.
- **The fleet is an input, because the decision is.** Keeping the host count an input lets the
  ceilings ask the only question worth asking: given what was bought, how often does the world
  break it?
:::

## What this cannot tell you

**Whether the structure is right.** Everything above takes the chains as given and asks what the
inputs are worth. A missing chain, a database's connection limit, a cache's eviction rate or the
network between the hosts, is invisible from inside. Nothing in the output distinguishes a model
that is complete from one that is not. That is [ch20 · The missing node](#the-missing-node).

**Whether the ceilings are where they were declared.** All six were declared by somebody with a reason
([ch11](#headroom-and-failure-domains)). The probabilities in the last two columns are exact
statements about where the model's own answers fall relative to lines that are judgements.

**Where the uncertainty comes from.** The range is wide, and this chapter has not said which
input makes it wide. That is the only actionable question about a wide range, and
[ch19](#which-input-is-the-answer) answers it. The answer will not surprise you if you read
[ch04 · Peak, mean and growth](#peak-mean-and-growth).

**What any of it costs.** Part III has sized a fleet and said nothing about money. Part V is
cost, and it comes after sizing because it consumes sizing's output, including, if anybody is
careful, its uncertainty.

**How any of these numbers were produced.** The last two columns of every ceiling table have been
appearing since [ch06](#queueing-and-the-knee) without explanation. [ch13](#monte-carlo) is the
explanation, and it is next because this is the chapter where a number appeared that you cannot
defend.

## Problems

Three, in `tests/the_sizing_model/`. The first two have tests. The last does not, and says why.

**12.1 — Size to a risk, not to a point estimate.**
Find the smallest fleet whose queueing ceiling is breached in at most some fraction of futures.
Bisect rather than step, and turn the number of draws down while searching. A search nobody runs
twice is a search nobody runs.

```bash
python3 -m pytest tests/the_sizing_model/test_problem_1_risk.py -m problem
```

**12.2 — What a percentage point of risk costs, in hosts.**
Count the hosts between the fleets two risk targets need, then look at the shape as the target
tightens. The last few points cost more machines than the ones before them, and knowing how many
is the difference between an argument and a preference. Part III has no prices, so the answer is
a count of hosts; [ch21](#a-tco-for-finance) prices the same pair.

```bash
python3 -m pytest tests/the_sizing_model/test_problem_2_cost_of_certainty.py -m problem
```

**12.3 — Your own model, as far as it goes.** No test: it is your chain, and the marks on it are
judgements.

Take the quantities from your workload and assemble them into a chain that ends in a count of
machines. Not in a file, unless you want to; on paper is fine. The point is to get from what
arrives to what you buy without skipping a step.

Then find the two things that make it a sizing model rather than a cost model: a constant somebody
measured on a particular version of a particular piece of software, and a limit your system runs
into. Mark each one.

Then turn to the fleet you have, rather than the one the chain recommends. Which of its limits
gives first as the load grows, how often would you expect that to happen over the horizon, and
who accepted that? This chapter's argument is that somebody did, whether or not they knew it.

A good answer reaches a number, has at least one mark on it, and names the risk the bought fleet
accepts and the person who accepted it. A chain with no marks is a cost model. Either your system
genuinely has no measured constants and no ceilings, which is rare, or you have not found them
yet, which is the more likely reading and the more expensive one. A risk nobody accepted is the
commoner finding, and it is the one to take to whoever signs for the fleet.

## Where to go next

[ch13](#monte-carlo) is where the last two columns came from. It sits here rather than at the
front of the book for the reason this chapter has just demonstrated: the method is no use to you
until you have a number you cannot defend, and can feel that you cannot defend it.

[Appendix E](#appendix-e-web-service-model) is this model in full, through every output the toolkit
produces.
