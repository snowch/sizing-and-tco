---
title: "The sizing model"
short_title: "ch12 The sizing model"
---

(the-sizing-model)=
# ch12 · The sizing model

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

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

The red line marks where the point estimate falls. Everything else shows the same model, the same
chains and the same margins, with the inputs allowed to be as uncertain as those who wrote them
down. The figure also has a solid dark line labelled *median* — the middle answer, with half the
model's answers below it and half above. The red line sits to its left. That means more of the
model's answers need a bigger fleet than the point estimate than need a smaller one.

At the point estimate each chain hands over its own middle, and the model takes the largest of the
three. Let the inputs move, and the model comes back with a smaller fleet only when *all three*
chains land low together — one chain coming in low is covered by whichever of the other two did
not. Needing three things to go your way at once is a weaker bet than needing one, so the largest
of three uncertain counts sits above the largest of their three middles. The spreadsheet's answer
is not merely uncertain. It is low.

And here is what that fleet does against the ceilings the last six chapters declared:

```{include} _generated/the-sizing-model-ceilings.md
```

At the point estimate, five of the six ceiling verdicts read *ok*. *Utilisation, counting
coordination* reads *into the margin*. The three chains were each sized against one ceiling: the
request chain against *utilisation at the busy hour*, the memory chain against *working set against
memory*, and the disk chain against *disk fill at horizon*. Each chain divides by that ceiling's
margin. The fleet is at least as large as every chain's count, so at the point estimate those three
ceilings cannot be past their allowed lines. They pass by construction. The memory chain set the
fleet: *hosts for memory* equals *hosts in the fleet* in the outputs table. So *working set against
memory* sits level with its allowed line. It passes with nothing to spare.

No chain was sized against the other three ceilings: *utilisation, counting coordination*,
*utilisation with one host down* and *fraction of the fleet doing nothing useful*. Two of those
three pass at the point estimate, and not by construction. *Utilisation with one host down* passes
because the memory chain bought more hosts than the request chain asked for. The request chain's
formula makes no allowance for a lost host. *Fraction of the fleet doing nothing useful* passes at
this fleet size, and no chain would notice if it did not. The coordination ceiling fails before any
input has moved. The request chain divides the busy cores by the fleet's cores as if each host
worked alone. [ch07](#when-adding-servers-stops-helping) showed that hosts spend part of their
capacity on each other. Counting that, the same fleet is busier than the chain assumed, and it sits
inside the margin. A model that reported only the verdict column would be marking its own homework,
and this one has already marked it wrong in one place.

The last two columns count the futures the model draws, not the point estimate. Read the *Over
limit* column on the *utilisation at the busy hour* row. It is the share of futures in which the
fleet the arithmetic recommends is past its limit at the busy hour: the busy hour needs more cores
than the fleet has. The *working set against memory* row is past its limit in more futures still.
Past that limit the working set no longer fits in memory. That share is not an extreme case. It
comes from the inputs as they were written down.

Nothing went wrong to produce it. Every input was defensible and every multiplication was correct.
The result is a fleet that, in a real share of futures, cannot carry its busy hour by the end of its
horizon. **That is what sizing from point estimates does.**

The live model below is all of Part III in one graph, with a slider on every input. Open **Inputs**.
The sliders are inside it, and *hosts in the fleet* is one of them. Below the sliders is
**Outputs**, and it holds the six ceilings. Each ceiling's value in **Outputs** is coloured by its
verdict: green for *ok*, amber for *into the margin*, red for *over*. Drag *hosts in the fleet* and
watch the colours change. Choosing that number is the decision this chapter is about.

```{iframe} /models/web_service_sizing-reference.html
:width: 100%
The sizing model, complete. Nothing arrives in this chapter: it is every earlier one, together.
```

Press **Expand** on the graph and choose **Model file** to read the file behind it. It is the file
ch02 started, with every chapter since added to it.

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

Suppose the fleet were derived instead: the model's recommendation, worked out afresh in every
future. Then in every future the fleet would be at least as large as each chain's count, so the
three ceilings the chains were sized against would sit at or under their allowed lines in every
future. Those ceilings would report that the fleet never crosses its allowed line. That would be
true by definition, and it would say nothing about the world. Keeping the fleet an input lets the
ceilings ask what a buyer needs to know: *given what we bought, how often does the world break it?*

## What this cannot tell you

**Whether the structure is right.** Everything above takes the chains as given and asks what the
inputs are worth. A missing chain, a database's connection limit, a cache's eviction rate or the
network between the hosts, is invisible from inside. Nothing in the output distinguishes a model
that is complete from one that is not. That is [ch20 · The missing node](#the-missing-node).

**Whether the ceilings are in the right place.** Each of the six ceilings has a limit and a margin
that a person declared with a reason, and [ch11](#headroom-and-failure-domains) is where those
margins were chosen. The last two columns say exactly where the model's own answers fall against
those lines. They cannot say whether the lines are in the right place: the lines are judgements.

**Where the uncertainty comes from.** The range is wide, and this chapter has not said which
input makes it wide. That is the only actionable question about a wide range, and
[ch19](#which-input-is-the-answer) answers it. The answer will not surprise you if you read
[ch04 · Peak, mean and growth](#peak-mean-and-growth).

**What any of it costs.** Part III has sized a fleet and said nothing about money. Part V is
cost, and it comes after sizing because it consumes sizing's output, including, if anybody is
careful, its uncertainty.

**How any of these numbers were produced.** The last two columns of every ceilings table have
appeared since [ch06](#queueing-and-the-knee). ch06 said what they mean. No page has yet said how
they were computed. [ch13](#monte-carlo) is where they are computed.

## Key takeaways

:::{div}
:class: takeaways

- **A sizing model is a dozen multiplications anybody could check.** The difficulty has never been
  the arithmetic.
- **The spreadsheet's answer is not merely uncertain. It is low.** The largest of three uncertain
  counts is usually larger than the largest of their three point estimates.
- **A fleet sized from point estimates passes its three designated ceilings, and still breaks.** It
  passes those three by construction — no chain looks at the other three, and one of those,
  *utilisation, counting coordination*, is already into the margin before any input moves. Across
  the futures the model draws, the fleet is past its limit at the busy hour in a real share of them,
  with nothing having gone wrong.
- **A sizing model produces a relationship between a number and a risk, not a number.** Somebody has
  to pick a point on it, and the only form the choice can be handed over in is *what it costs*
  beside *how often it breaks*.
- **A bigger fleet moves risk rather than removing it.** A fleet bought for the top of the growth
  range is past its limits at the busy hour and in memory in far fewer futures. The same fleet
  pushes the share of it doing nothing useful into that ceiling's margin, because each added host
  brings less capacity than the last, and that ceiling protects the budget.
- **The fleet is an input, because the decision is.** Keeping the host count an input lets the
  ceilings ask the only question worth asking: given what was bought, how often does the world
  break it?
:::

## Problems

Three, in `tests/the_sizing_model/`. The first two have tests. The last does not, and says why.

**12.1 — Size to a risk, not to a point estimate.**
Find the smallest number of hosts for which the *utilisation at the busy hour* row in the ceilings
table is past its limit in at most the target share of futures. That share is the *Over limit*
column on that row. `risk_at(hosts)` asks the model for that share, with that many hosts in the
fleet, over the full number of draws. `risk_at(hosts, samples=n)` does the same over `n` draws
instead.

More hosts never raise that share, so a bisection finds the answer in a few calls. Stepping one host
at a time takes far more. Use fewer draws while you search and the full number for the final answer.
Comparing candidates needs much less precision than reporting one. The model draws the same futures
every time, so a fleet always gets the same share at the full number. The tests hold the answer to
the target exactly, at the full number of draws: one host too small and you miss the target; one
host too large and you have not found the smallest. The Check under this problem runs the model
several times in your browser. It is slow. Wait for it. A search nobody runs twice is a search
nobody runs.

```bash
python3 -m pytest tests/the_sizing_model/test_problem_1_risk.py -m problem
```

**12.2 — What a percentage point of risk costs, in hosts.**
Count the hosts between the fleets two risk targets need, then look at how that count changes as the
target tightens. Your `cost_of_certainty` function must size both fleets by calling your
`hosts_for_risk` from 12.1, using the same `risk_at` both times. A search of its own can land on
different fleets, and the Check fails it. The sign matters: moving to a smaller risk costs hosts, so
the answer is positive; moving the other way gives them back, so the answer is negative. The Check
runs your 12.1 function as well. It is shown again above the Check. It is the same function as the
one under 12.1: an edit to either copy is an edit to both. So 12.2 cannot pass until
`hosts_for_risk` works. The last few points of risk cost more machines than the ones before them.
Knowing how many is the difference between an argument and a preference. Part III has no prices, so
the answer is a count of hosts. [ch21](#a-tco-for-finance) prices the same pair of fleets.

```bash
python3 -m pytest tests/the_sizing_model/test_problem_2_cost_of_certainty.py -m problem
```

**12.3 — Your own model, as far as it goes.** No test: it is your chain, and the marks on it are
judgements.

Take the quantities from your workload and assemble them into a chain that ends in a count of
machines. Not in a file, unless you want to; on paper is fine. The point is to get from what
arrives to what you buy without skipping a step.

Mark what makes the chain a conditional model rather than a definitional one. There are two kinds of
thing to look for: a constant measured on a particular version of a particular piece of software,
and a limit your system runs into. Either kind alone makes the chain conditional. Mark every one you
find, of either kind.

Now take the fleet you have, not the one the chain recommends. Which of its limits gives first as
the load grows? Which input would have to come in where for that limit to give way? Would that value
surprise you, in the sense ch04 used — is it inside or outside the band you would write as
*surprised below this, surprised above that*? Who accepted that risk? This chapter argues that
someone did, whether or not they knew it.

A good answer reaches a count of machines and has at least one mark on the chain. It names the limit
that gives first, the input and the value that would make it give, and says whether that value is
inside your surprise band. It names the person who accepted the risk. A chain with no marks is a
definitional model. Either your system has no measured constants and no limits, which is rare, or
you have not found them yet. The second is the more likely reading, and the more expensive one. How
often the limit would give way, counted as a share of futures, needs the method of
[ch13](#monte-carlo). Here the surprise band is enough. Falsifiers: the answer is wrong if, as the
load grows, a different limit gives first. It is also wrong if the person you named says they never
saw the risk. Then nobody accepted it, and that is the commoner finding. Take it to whoever signs
for the fleet.

## Where to go next

[ch13](#monte-carlo) is where the last two columns came from. It sits here rather than at the
front of the book for the reason this chapter has just demonstrated: the method is no use to you
until you have a number you cannot defend, and can feel that you cannot defend it.

[Appendix E](#appendix-e-web-service-model) is this model in full, through every output the toolkit
produces.
