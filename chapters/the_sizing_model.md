---
title: "The sizing model"
short_title: "ch11 The sizing model"
---

(the-sizing-model)=
# ch11 · The sizing model

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch08](#capacity), [ch09](#bandwidth-and-the-binding-constraint), [ch10](#headroom-and-failure-domains) |
| **What it produces** | The storage model end to end, and the node count it recommends |
| **Built from** | `storage_cluster-reference`, `storage_cluster-sized_for_growth` |
:::

## The question

What does the whole chain produce, and how much of it would you defend?

Part I described a workload. Part II found the ceilings. Part III has turned both into machines.
This chapter puts them together, arrives at a number, and then makes the number look at itself.

## The material

### The whole model in one graph

```{image} _figures/the-sizing-model-graph.svg
:alt: Everything that feeds the recommended node count
:width: 100%
```

Every node in that sub-graph has appeared in a chapter. The workload on the left
([ch01](#what-a-workload-is)), the growth term ([ch03](#peak-mean-and-growth)), the capacity chain
and the bandwidth chain ([ch08](#capacity), [ch09](#bandwidth-and-the-binding-constraint)), the
margin ([ch10](#headroom-and-failure-domains)), and the larger-of-the-two at the end.

Follow it left to right and there is nothing surprising in it. Sizing models are not clever: they
are a dozen multiplications anybody could check, and the difficulty has never been the arithmetic.

### What the model recommends

```{include} _generated/the-sizing-model-outputs.md
```

The first row is the answer, evaluated at every input's point estimate: what a competently built
spreadsheet would give you. It is also exactly what this book's reference cluster was purchased
against, and the node count's provenance says so in as many words.

### The number looks at itself

```{image} _figures/the-sizing-model-nodes.svg
:alt: The recommended node count, as a distribution
:width: 100%
```

The red line is where the point estimate falls. Everything else is the same model, the same
chains, the same margins, with its inputs allowed to be as uncertain as the people who wrote them
down actually are.

And here is what that cluster does against the ceilings [ch10](#headroom-and-failure-domains)
declared:

```{include} _generated/the-sizing-model-ceilings.md
```

At the point estimate, every ceiling is comfortable. Of course it is — the cluster was sized from
those point estimates, so it satisfies them by construction. A model that reported only the
verdict column would be marking its own homework.

The last two columns ask a different question. Read the *fill level at horizon* row. Buy the
cluster the arithmetic recommends, and across everything this model thinks could happen, it runs
out of space a substantial fraction of the time. Not in an extreme scenario. In a third of them.

Nothing went wrong to produce that. Every input was defensible, every multiplication was correct,
and the result is a cluster with a one-in-three chance of not lasting its horizon. **That is what
sizing from point estimates does.**

### So what is the answer?

There isn't one. Part III has been building to exactly that.

A sizing model does not produce a number. It produces a *relationship between a number and a
risk*, and somebody has to choose a point on it. Problem 11.1 is that choice made explicitly: pick
a breach probability you are willing to be accountable for, and ask the model what it costs in
machines.

That is a different conversation from "how many nodes do we need", and a better one: it is
answerable. Here is one other point on that curve — the same model, the same ceilings, with a
cluster bought for the growth case rather than the expected one:

```{include} _generated/the-sizing-model-resized.md
```

Every figure in the last two columns falls, and the read ceiling stops being breached at all.
What that costs is
[ch20](#a-tco-for-finance)'s table rather than this one — but the pair, *what it costs* beside
*how often it breaks*, is the only form in which this decision can be handed to somebody.

Problem 11.2 is the shape of the trade. Removing risk costs money, the cost is not linear in the
risk removed, and the last few percentage points cost more than all the ones before them. Having
that number is the difference between an argument and a preference, and
[ch20](#a-tco-for-finance) is about putting it to the person whose decision it is.

### The decision is an input

The number of nodes purchased is an **input**, not a derived node, and that is the detail a
spreadsheet hides. It has a provenance and a source like any other. Sizing produces a
*recommendation*. A person then decides, once, before the five years happen. Everything
downstream — every dollar, every watt, every ceiling — follows from what they chose rather than
from what the model would recommend in hindsight.

Deriving it instead would make the ceilings tautologies. A cluster sized to satisfy a fill limit
satisfies it in every sample, and the model would cheerfully report no chance at all of running
out of space. Keeping it an input lets the ceilings ask the only question worth asking: *given
what we actually bought, how often does the world break it?*

## What this cannot tell you

**Whether the structure is right.** Everything above takes the chains as given and asks what the
inputs are worth. A missing chain — rebuild bandwidth, metadata operations, a control plane — is
invisible from inside, and nothing in the output distinguishes a model that is complete from one
that is not. That is [ch19](#the-missing-node).

**What the ceilings are really at.** Both were declared by somebody with a reason
([ch10](#headroom-and-failure-domains)). The probabilities in the last two columns are exact
statements about where the model's samples fall relative to lines that are judgements.

**Where the uncertainty comes from.** The interval is wide, and this chapter has not said which
input makes it wide. That is the only actionable question about a wide interval, and
[ch18](#which-input-is-the-answer) answers it — the answer will not surprise you if you read
[ch03](#peak-mean-and-growth).

**What any of it costs.** Part III has sized a cluster and said nothing about money. Part V is
cost, and it comes after sizing because it consumes sizing's output — including, if anybody is
careful, its uncertainty.

**How any of these numbers were produced.** The last two columns of every ceiling table have been
appearing since [ch05](#queueing-and-the-knee) without explanation. [ch12](#monte-carlo) is the
explanation, and it is next because this is the chapter where a number appeared that you cannot
defend.

## Problems

Two, in `tests/the_sizing_model/`.

**11.1 — Size to a risk, not to a point estimate.**
Find the smallest cluster whose capacity ceiling is breached in at most some fraction of samples.
Bisect rather than step, and turn the sample count down while searching — a search nobody runs
twice is a search nobody runs.

```bash
python3 -m pytest tests/the_sizing_model/test_problem_1_risk.py
```

**11.2 — What a percentage point of risk costs.**
Price the move between two risk targets, then look at the shape as the target tightens. The last
few points cost more than all the ones before them, and knowing by how much is the difference
between an argument and a preference.

```bash
python3 -m pytest tests/the_sizing_model/test_problem_2_cost_of_certainty.py
```

## Where to go next

[ch12](#monte-carlo) is where the last two columns came from. It sits here rather than at the
front of the book for the reason this chapter has just demonstrated: the method is no use to you
until you have a number you cannot defend, and can feel that you cannot defend it.

[Appendix E](#appendix-e-storage-model) is this model in full, through every output the toolkit
produces.
