---
title: "A TCO for a finance audience"
short_title: "ch20 A TCO for a finance audience"
---

(a-tco-for-finance)=
# ch20 · A TCO for a finance audience

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch17](#the-five-year-model), [ch18](#which-input-is-the-answer) |
| **What it produces** | The two storage scenarios as a decision, priced |
| **Built from** | `storage_cluster-reference`, `storage_cluster-sized_for_growth` |
:::

## The question

How do you present an interval to somebody who has asked you for a number?

Every chapter so far has been about getting the answer right. This one is about the twenty minutes
in which it is either used or ignored, and the two are not the same skill. A model that nobody
acts on has the same value as a model that was never built.

## The material

### The two things the room wants

The instinct on the engineering side is to protect the interval. It was hard won, it is the most
honest thing in the document, and collapsing it to a single figure feels like throwing away the
work.

The instinct on the finance side is to get one number into a spreadsheet. That is not laziness.
A budget line is a single number by construction; a commitment is a single number; the question
"can we afford this" cannot be answered by a range without someone, somewhere, picking a point in
it.

Both instincts are right, and the argument between them is usually conducted as though only one
of them can be. No compromise is needed, because the two sides want different things. Finance
wants a number to **commit** to. Engineering wants to say what the number **hides**. Those two
fit together.

### The number, and the sentence

So the deliverable is a pair.

> **One number, and one sentence saying what it leaves out.**

Not a range. Not a range with a recommendation attached. A number, chosen deliberately and named
as a choice, and then a single sentence that says the thing the number cannot.

Which number you pick is a decision, and you can defend any of these three out loud:

**The median.** Half the futures cost more. Honest, easy to explain, and the one most people mean
when they say "the estimate". It is also the number that will be wrong half the time in the
direction that hurts.

**A high percentile.** The figure you would be comfortable committing to. Useful when overrunning
is expensive and underspending is not. Its failure mode is quiet: you will be held to it, the
money will be allocated, and when the cost lands lower nobody will thank you for the accuracy.

**A round number above the median.** Not as unprincipled as it sounds. Rounding to a precision
the model can actually support is more honest than quoting a figure to the dollar, and
[ch13](#correlation-and-convergence) gives the arithmetic for what precision that is: the run-to-run
wobble has to be below the digit you are prepared to defend.

Here is the shape all three are chosen from — the same picture [the introduction](#preface) opened
with, now as something to pick a number off rather than something to be alarmed by:

```{image} _figures/a-tco-for-finance-distribution.svg
:alt: The five-year total for the reference design, with the point estimate marked on it
:width: 100%
```

The red line is the point estimate, and it is not the middle. Whichever of the three you choose,
choose it off that chart and say which one it was.

The number must not arrive without the sentence. The sentence is the whole of the engineering
position, and there is only room for one, so it has to name something specific — a percentile, an
omission, an assumption the total rests on. "There is some uncertainty" names nothing and will be
heard as "no".

Problem 20.2 is that pair, and it is graded on the sentence.

### A decision, not an interval

The single most effective change to a sizing document is to stop presenting one design with an
interval and start presenting two designs with a price.

```{include} _generated/a-tco-for-finance-scenarios.md
```

Two columns. The left one buys what the model recommends at the point estimate. The right one
buys the same cluster sized for the growth we might get rather than the growth we expect, which
is the decision of [ch10](#headroom-and-failure-domains) taken deliberately instead of by default.

Read across the rows and the conversation changes shape. The question is no longer "is this
estimate right", which nobody in the room can answer. It is "is the difference between these two
columns worth the difference in the last two rows", which is exactly the sort of question the
people being asked are good at.

**An interval is a statement about the world. A decision table is a statement about what you can
buy**, and only the second is actionable by someone who cannot change the world but can sign for
the extra machines.

### Pricing a risk

The last two rows of that table are the ones to lead with, because they are the only ones that
have a consequence in them.

```{include} _generated/a-tco-for-finance-ceilings.md
```

*Over limit* is how often, across the sampled futures, the cluster is asked to do something it
cannot. The capacity row is a plain English sentence: this is how often we buy the cluster and it
does not hold the data we said it would.

That sentence is worth more than any amount of argument about the growth rate. Nobody in the room
has an opinion about a lognormal. Everybody in the room has an opinion about running out of disk
in year four.

The second scenario reduces that number, and the table says by how much and what it costs. Put
the two together and you have the only sentence in the document that is genuinely a
recommendation: *this much additional capital buys this much less chance of that happening*. If
the answer is obviously yes, the meeting is over. If it is obviously no, the meeting is also
over, and you have the decision in writing rather than in somebody's memory.

### Where each number came from

Then the appendix nobody asks for until they do.

```{include} _generated/a-tco-for-finance-provenance.md
```

Three marks. The one that matters in this room is *vendor claim*: a number supplied by the party
being paid. It may well be right. It has not been checked here, it is coloured differently in
every figure in this book for that reason ([ch02](#where-the-numbers-come-from)), and the finance
audience is entitled to know which of the inputs to a capital request came from the supplier.

Handing this over unprompted makes the rest of the document more believable, and little else
does. A model that volunteers which of its inputs are guesses is not a model trying to win an
argument.

### Three ways to lose the room

**Presenting the interval instead of the decision.** "Somewhere between these two figures" with
no recommendation is not caution, it is a refusal to do the last part of the job. The person
across the table is being asked to absorb uncertainty that you understand and they do not.

**Presenting a high percentile as the cost.** It gets approved, the money is set aside, and the
actual spend comes in well under. That looks like success exactly once. The second time, the
number is discounted before you have finished saying it, and the discount is applied by somebody
who does not know which parts of it were conservative.

**Presenting the median as though it were the plan.** The failure mode of the first two is
optical. This one is real: half the futures cost more, and nothing has been said about what
happens in them.

Each of the three is a way of not saying the sentence.

### What to hand over

One page:

- The number, and the sentence.
- The decision table: what each design costs, and how often each one breaks.
- The ceilings, in the language of what fails rather than the language of utilisation.
- The provenance table, marked.
- A link to the model file, because it re-runs and they can change an input and see what happens.

And the cash flow, separated by year rather than summed. [ch14](#capex-opex-and-lifecycle) says
why this book does not discount: the rate is a policy decision, not an engineering one. The first
thing a finance team will do with a five-year total is discount it, and they can only do that if
the years have not already been added together.

## What this cannot tell you

**What running out is worth.** Every figure in the decision table is a cost of *building*. There
is no term anywhere in this model for what happens when the capacity ceiling is breached: the
emergency purchase at list price, the migration, the quarter spent on it, the conversation with
whoever was promised the capacity. The right-hand column's extra capital buys a reduction in that
risk, and the model prices the capital precisely and the risk not at all. Anybody who says the
extra machines are not worth it is making a claim about a number this book has not measured.

**Your organisation's appetite for it.** How much should a one-in-three chance of running out
cost to avoid? That is not an engineering quantity and there is no defensible way to derive it
from the model. It belongs to the people who carry the consequence, which is one more reason to
put the ceiling row in front of them rather than resolving it yourself.

**What the money is worth.** The totals here add dollars from different years as though they were
the same dollar. They are not. Applying a discount rate would change the comparison between a
design that spends capital up front and one that spends it over time — and the two columns above
differ in exactly that way. The model hands over the shape of the spend so that somebody can
apply theirs; it does not pretend the undiscounted total is the answer.

**Whether the structure is complete.** [ch19](#the-missing-node) is the standing limitation and
it does not stop applying because the audience has changed. The decision table is a comparison
between two designs inside one model, and both columns inherit whatever that model is missing.
The comparison is more robust than either total — a missing cost line that scales with node count
hurts both columns — but "more robust" is not "unaffected".

**Whether it worked.** There is no measurement in this repository of whether a document shaped
like this gets a better decision than one shaped some other way. This chapter is the one place in
the book arguing from experience rather than from a stamped result.

## Problems

Two, in `tests/a_tco_for_finance/`. Neither is arithmetic.

**20.1 — The decision table.**
Build the two-design comparison from the stamped results, with the columns that answer the
question and no others. The test grades the numbers against the model and the shape against what
fits in somebody's head.

```bash
python3 -m pytest tests/a_tco_for_finance/test_problem_1_decision_table.py
```

**20.2 — They have asked for one number.**
Give it. Then write the sentence. Any defensible choice of number passes; the test checks that it
came out of the model, that it is rounded to a precision the model can support, and that the
sentence names something specific.

```bash
python3 -m pytest tests/a_tco_for_finance/test_problem_2_one_number.py
```

## Where to go next

That is the argument. [ch21](#what-the-model-got-wrong) is what happens afterwards — three
years later, when one of the futures in that table turned out to be the one you got.

What remains after it is reference material:
[Appendix A](#appendix-a-dsl-reference) for the DSL,
[Appendix B](#appendix-b-monte-carlo-module) for the sampler read end to end,
[Appendix C](#appendix-c-distributions) for choosing a shape,
[Appendix E](#appendix-e-storage-model) and [Appendix F](#appendix-f-observability-model) for the
storage and observability models in full, and
[Appendix G](#appendix-g-glossary) for the vocabulary, including the terms this book refuses.

If you read one thing again, make it [ch19](#the-missing-node). Everything in this chapter is
about presenting what the model knows, and the hardest sentence to write is still the one about
what it does not.
