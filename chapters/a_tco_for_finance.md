---
title: "A TCO for a finance audience"
short_title: "ch21 A TCO for a finance audience"
---

(a-tco-for-finance)=
# ch21 · A TCO for a finance audience

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

How do you present an interval to somebody who has asked you for a number?

Every chapter so far has been about getting the answer right. This one is about the twenty
minutes in which it is either used or ignored. Those are not the same skill. A model that nobody
acts on has the same value as a model that was never built.

## The material

### The two things the room wants

The instinct on the engineering side is to protect the interval. It was hard won. It is the most
honest thing in the document. Collapsing it to a single figure feels like throwing away the work.

The instinct on the finance side is to get one number into a spreadsheet. That is not laziness.
A budget line is a single number by construction. A commitment is a single number. The question
"can we afford this" cannot be answered by a range until someone, somewhere, picks a point in it.

Both instincts are right. The argument between them is usually conducted as though only one of
them can be. No compromise is needed, because the two sides want different things. Finance wants
a number to **commit** to. Engineering wants to say what the number **hides**. Those two fit
together.

### The number, and the sentence

So the deliverable is a pair.

> **One number, and one sentence saying what it leaves out.**

Not a range. Not a range with a recommendation attached. A number, chosen deliberately and named
as a choice, and then a single sentence that says the thing the number cannot.

Which number you pick is a decision. You can defend any of these three out loud:

**The median.** Half the futures cost more. Honest, easy to explain, and the one most people mean
when they say "the estimate". It is also the number that will be wrong half the time in the
direction that hurts.

**A high percentile.** The figure you would be comfortable committing to. Choose this when
overrunning is expensive and underspending is not.

**A round number above the median.** Round up rather than to the nearest step, and you buy some
cover against the futures that cost more without committing to a high percentile. Rounding also
matches what you can claim: a figure to the dollar claims precision the model does not have. The
precision the model can support is set by how wide its interval is, not by how many digits the
arithmetic prints. [ch14](#correlation-and-convergence)'s run-to-run wobble sets a second limit: it
must be below the last digit you quote.

Here is the distribution you choose from. It shows the five-year total for the reference design over
the model's sampled futures, as it did in [ch13](#monte-carlo).

```{image} _figures/a-tco-for-finance-distribution.svg
:alt: The five-year total for the reference design, with the point estimate and the median marked on it
:width: 100%
```

The red line is the point estimate, and it is not the middle. The chart marks the point estimate,
the median (the dark dashed line), and the ends of the 90% interval; the subtitle gives the median
and the interval's ends as figures. Pick any of the three choices off the chart, and say which one
it was.

The number must not arrive without the sentence. The sentence carries the engineering position, and
there is room for one. So it names something specific: which percentile the number is, a cost the
total leaves out, or an input the total rests on—the growth rate, a vendor's price. "There is some
uncertainty" names nothing, and the person who signs hears it as "no". Problem 21.2 asks for that
pair: the number, taken from the chart, and the sentence that names what it leaves out.

### A decision, not an interval

Present two designs with a price, not one design with an interval.

```{include} _generated/a-tco-for-finance-scenarios.md
```

The table has two columns, one per design. The left column buys what the model recommends with every
input at its point estimate. The right column buys what the model recommends when the annual growth
factor reaches its 90th percentile—growth that one future in ten exceeds. Every other input stays at
its point estimate. This is the bigger fleet [ch12](#the-sizing-model) set against the ceilings, now
with a price attached, chosen deliberately instead of by default.

Read the rows across both columns and the question changes. It is no longer "is this estimate
right", which no one at the table can answer. It becomes "is the extra money in the right column
worth the fall in the busy-hour row". The person who signs can answer that question without knowing
anything about queues. It asks what extra spending buys, in terms of something that goes wrong.

**An interval is a statement about the world. A decision table is a statement about what you can
buy.** Only the second can be acted on by someone who cannot change the world but can sign for
the extra machines.

### Pricing a risk

Lead with the decision table's busy-hour row, the only one that says what goes wrong in terms you
can picture. The table below is a different one: every ceiling the model watches, for the reference
design alone.

```{include} _generated/a-tco-for-finance-ceilings.md
```

*Over limit* is the share of the sampled futures in which the fleet is asked to do more than it can.
For the busy-hour row, the limit is the fleet fully busy: over it, the busy hour brings more
requests than the fleet can serve. *Verdict* judges only one value: the one in *At the plan* against
the margin. A row can say *ok* while its *Over limit* column is large. The plan passes at its point
estimate; it fails in a share of the futures.

The busy-hour row is this in plain English: this is how often you buy this fleet and it cannot serve
the busy hour it was bought for. That sentence persuades where argument about the growth rate does
not. No one at the table has an opinion about a lognormal. Everyone there has one about the service
being slow on its busiest day.

The right-hand design is over its busy-hour limit in far fewer futures. The decision table shows by
how much and what it costs. Put the two together and you have the one sentence in the document that
is a recommendation: *this much additional capital buys this much less chance of that happening*. If
the answer is plainly yes, the meeting is over. If it is plainly no, the meeting is also over, and
the decision is in writing rather than in someone's memory.

### Where each number came from

Last in the hand-over comes where each input came from. It goes with the one page described in *What
to hand over*, as an attachment.

```{include} _generated/a-tco-for-finance-provenance.md
```

Every input carries one of three marks: fact (●), vendor claim (◐) or assumption (○). The table
lists the vendor claims and counts the other two kinds; its last line counts every input by kind. A
vendor claim is a number supplied by the party being paid. It may be right. It has not been checked
here, and the book marks it so you can tell it from a checked figure
([ch03](#where-the-numbers-come-from)). Finance is entitled to know which inputs to a capital
request came from the supplier, which is why the table lists those.

Handing this over before anyone asks makes the rest of the document easier to believe. A model that
says which of its inputs are guesses is not trying to win an argument. The full list, every input
with its mark and source, is in [Appendix E](#appendix-e-web-service-model), under *Where the inputs
came from*.

### Three ways to lose the room

Each way of losing the room is something defensible handed over without its sentence.

**Presenting the interval instead of the decision.** "Somewhere between these two figures" with no
recommendation is not caution. It refuses the last part of the job, and asks the person across the
table to absorb an uncertainty you understand and they do not.

**Presenting a high percentile as the cost.** It gets approved, the money is set aside, and the
spend comes in well under. That looks like success once. The next time, finance trusts your figure
less before you have finished giving it. They mark down the whole figure, because they cannot tell
which parts of it were cautious.

**Presenting the median as though it were the plan.** The first two fail in how they look. This one
fails in what happens: half the futures cost more, and nothing has been said about them.

### What to hand over

One page:

- The number, and the sentence.
- The decision table: what each design costs, and how often each one breaks.
- The ceilings, in the language of what fails rather than the language of utilisation.
- The provenance table, marked.
- A link to the model file, because it re-runs. They can change an input and see what happens.

And the cash flow, separated by year rather than summed. [ch15](#capex-opex-and-lifecycle) says
why this book does not discount: the rate is a policy decision, not an engineering one. The first
thing a finance team will do with a five-year total is discount it. They can only do that if the
years have not already been added together.

## What this cannot tell you

**What running out is worth.** Every figure in the decision table is a cost of *building* the fleet.
The model has no term for what happens when the busy hour goes over its limit: the busy hour spent
turning users away, the emergency purchase at list price, the quarter spent recovering, the
conversation with whoever was promised the service. The right-hand column's extra capital buys a
smaller chance of that. The model prices the capital, with an interval around it, and the risk not
at all. Anyone who says the extra machines are not worth it is making a claim about a cost this
model does not contain.

**Your organisation's appetite for it.** How much should a real chance of the busiest hour going
over the knee cost to avoid? That is not an engineering quantity, and there is no defensible way
to derive it from the model. It belongs to the people who carry the consequence. That is one more
reason to put the ceiling row in front of them rather than resolving it yourself.

**What the money is worth.** The totals here add dollars from different years as though they were
the same dollar. They are not. Applying a discount rate would change the comparison between a
design that spends capital up front and one that spends it over time, and the two columns above
differ in that way. The model hands over the shape of the spend so that somebody can
apply theirs. It does not pretend the undiscounted total is the answer.

**Whether the structure is complete.** [ch20](#the-missing-node) is the standing limitation, and it
does not stop applying because the audience has changed. The decision table is a comparison between
two designs inside one model, and both columns inherit whatever that model is missing. The
comparison is safe only from omissions that cost the same in both: they add the same amount to each
column and cancel when you subtract. The staff cost is one already in the model: it does not depend
on the number of hosts. Most of the model's cost lines grow with the fleet: host prices, network,
licences, support and energy. A missing line of that kind would cost the right-hand column, which
has more hosts, more than the left. Leaving out a cost that grows with the fleet makes the bigger
fleet look cheaper, against the smaller one, than it is. The gap between the columns is understated,
not protected.

**Whether it worked.** There is no measurement in this repository of whether a document shaped
like this gets a better decision than one shaped some other way. This chapter is the one place in
the book arguing from experience rather than from a stamped result.

## Key takeaways

:::{div}
:class: takeaways

- **Finance wants a number to commit to. Engineering wants to say what the number hides.** Both are
  right, and they fit together.
- **The deliverable is one number and one sentence saying what it leaves out.** The number is a
  choice made out loud: the median, a high percentile, or a round figure above the median. The
  sentence names something specific.
- **Present two designs with a price, not one design with an interval.** The question becomes
  whether the difference between the columns is worth the difference in how often each one breaks,
  and that is a question the room can answer.
- **Lead with how often each design fails at the busy hour.** "This is how often you buy this fleet
  and it cannot serve the busy hour it was bought for" is a sentence the person who signs can
  weigh, because they have an opinion about the service being slow on its busiest day, and none
  about a growth distribution.
- **Volunteer where every number came from.** A model that says which of its inputs are the
  supplier's is not a model trying to win an argument, and it is believed more for it.
:::

## Problems

Three, in `tests/a_tco_for_finance/`. The first two have tests and neither is arithmetic. The last
has no test, and says why.

**21.1 — The decision table.**
The test hands you the stamped result of each of the two designs. Build the two-design comparison
from them, with the columns that answer the question and no others. The test grades the numbers
against the stamped results and the shape against what fits in somebody's head.

```bash
python3 -m pytest tests/a_tco_for_finance/test_problem_1_decision_table.py -m problem
```

**21.2 — They have asked for one number.**
Give it. Then write the sentence. Any defensible choice of number passes. The test checks that it
came out of the model, that it is rounded to a precision the model can support, and that the
sentence names something specific.

```bash
python3 -m pytest tests/a_tco_for_finance/test_problem_2_one_number.py -m problem
```

**21.3 — Write the page, and hand it over.** No test: a page is graded by the person it is for.

Write the one-page version *What to hand over* describes, for your own system, and give it to
whoever signs for it. The model prices what overbuying costs: the difference between the columns. It
does not price running short. If you put a cost on running short, that figure is your estimate: it
goes on the page marked as an assumption, with its source, like any input in the provenance table.

Then do the part that is not writing: watch what they ask. The question they ask first is the thing
your page failed to answer.

A good answer is one page and gets a decision. If it gets a request for more detail, the detail they
asked for belongs on the page and something now on it does not. This book has no measurement of
whether a document like this works, so the only test is handing it to the person it is for.

## Where to go next

[ch22](#comparing-two-tcos) is the last step of the argument. When the two columns are two quotes
rather than two sizes of one fleet, the difference between them is what somebody is deciding, and
it has an interval of its own.

[ch23](#what-the-model-got-wrong) is what happens afterwards: at the model's horizon, when one of
the futures in that table turned out to be the one you got.

What remains after it is reference material:
[Appendix A](#appendix-a-dsl-reference) for the model file format in full,
[Appendix B](#appendix-b-monte-carlo-module) for the sampler read end to end,
[Appendix C](#appendix-c-distributions) for choosing a shape,
[Appendix E](#appendix-e-web-service-model) and [Appendix F](#appendix-f-observability-model) for
the web service and observability models in full, and
[Appendix G](#appendix-g-glossary) for the vocabulary, including the terms this book refuses.

If you read one thing again, make it [ch20](#the-missing-node). Everything in this chapter is
about presenting what the model knows, and the hardest sentence to write is still the one about
what it does not.
