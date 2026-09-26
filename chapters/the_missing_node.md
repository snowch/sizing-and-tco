---
title: "The missing node"
short_title: "ch20 The missing node"
---

(the-missing-node)=
# ch20 · The missing node

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

How do you find the error that no amount of sampling can see?

Chapters from [ch01](#point-estimates) onwards have raised this problem and sent you here. It
affects every model in the book, and no technique that works on the model file can find it,
because the missing term is not in the file for any of them to work on. So it has a chapter of its
own rather than appearing at the end of another.

## The material

### Two ways to be wrong

**Wrong about a number.** An input is off. The model is the right shape and the arithmetic is
right, but one of the quantities is not what you thought. Every chapter so far has been about
this error. [ch13](#monte-carlo) quantifies it, [ch14](#correlation-and-convergence) refines it,
and [ch19](#which-input-is-the-answer) says which one to go and fix.

**Wrong about the shape.** A cost line is missing. A chain is not in the model. A ceiling nobody
declared. Two things multiplied that should have been added.

Sampling reports only the doubt you wrote down: the range for each input. It catches a wrong
input only if the range you declared contains the true value. Sampling cannot see the second kind
of error at all, because the model file does not describe what is missing. It does worse: it
produces an interval that has converged around the wrong answer, and the convergence looks like
rigour.

### Four things that could be wrong, and the book can count two

This split, being wrong about a number or wrong about the shape, is separate from the
definitional and conditional models and cuts across that distinction. [ch01](#point-estimates)'s
test assumes the model contains every term it needs, yet a definitional model is right only about
the terms it has: one missing a cost line is wrong with every input right. The book has used four
kinds of error throughout but has not put them in one place.

**A measurement wobbles.** A measured constant has a standard error, and it is as likely to be
high as low ([ch03](#where-the-numbers-come-from)). It shrinks when you repeat the same measurement
over more shards, and halving it costs four times the work. In this book's models this error hardly
moves the answer: [ch19](#which-input-is-the-answer) removed the standard errors of the measured
constants and neither interval moved.

**A number is unknown.** An input nobody measured, given a distribution somebody chose: a price,
a growth rate, a count of label values ([ch13](#monte-carlo)). It shrinks when you go and measure
that input. [ch19](#which-input-is-the-answer) ranks which one to measure first, and every input at
the top of its tables is of this kind, not a measured constant.

Those two are what the interval is made of. Both are quantities the model can carry, and the
whole apparatus of Part IV and [ch19](#which-input-is-the-answer) is about them.

**The world takes a different path.** A launch doubles the busy hour. The service shrinks instead
of growing. These are changes in the world, not choices you make. This one is *not* in the
interval. You handle it by running the model again for that path, with the inputs set to it in a
scenario: a small file beside the model that overrides inputs and says why
([Appendix A](#appendix-a-dsl-reference)). You do not handle it by widening the ranges, which would
blend that path into every future. A fleet bought for the growth case ([ch12](#the-sizing-model))
changes only the number of hosts: the same model and futures, but a different fleet. That is a
choice you make, not a different world.

**The model is the wrong shape.** This is the error this chapter is about. It appears in no
interval and no scenario, because nothing in the file knows the term is missing. The glossary calls
this structural error.

Naming the four says what a wide interval is and is not. A wide interval reports on the first two.
It is silent about the third, because the model was not run for that path. It is silent about the
fourth, which is a modelling decision nobody knew they were taking.

### The book's own example, on a published page

```{include} _generated/the-missing-node-outputs.md
```

```{image} _figures/the-missing-node-graph.svg
:alt: What feeds the ingest total, and what is missing from it
:width: 100%
```

The observability model's ingest figure combines metrics and logs, as shown in the *ingest, metrics
and logs only* row. It is arithmetically correct: every input is declared, sourced and sampled, and
the interval is as honest as the rest of the book.

The model leaves out an entire chain, traces. The *traces ingest* row shows *not yet measured*
because spans per request has not been measured. Spans per request belongs to a single instrumented
application at one version, and nothing in this repository can measure it.

```{include} _generated/the-missing-node-unmeasured.md
```

The box names two unmeasured constants. Only spans per request feeds the traces chain; the other,
collector throughput per core, feeds a different output that this chapter does not use.

This case is visible because the model file has a node for the missing quantity. The toolkit marks
everything downstream as not yet measured rather than filling it in. The row label *metrics and logs
only* indicates the missing chain. This is the easy case, visible on a published page so you can
compare it against the hard case.

The hard case is a chain nobody thought of. It has no node, so there is nothing to mark and no box
to render. The model cannot know it is incomplete, and its output is a number with an interval
around it and no sign that it is a lower bound.

### Why the interval makes it worse

A single number invites doubt; an interval does not, because it looks as if the doubt has already
been accounted for. Before an invoice arrives to show otherwise, the interval alone is what a
reader has.

This page shows a model in that state: the file under problem 20.3 calculates monthly cost from
instances at a rate, storage at a rate, and a support charge on both. Every number was invented
for the exercise, and the file is missing one cost line with no node to mark the gap.

The first row shows the file is a definitional model by [ch01](#point-estimates)'s test: every
relationship holds by definition, yet it is incomplete because a line is missing, as the section
*Four things that could be wrong* explained. The invoice average lies above the whole interval,
and the last row shows almost none of the model's futures reach it.

This is why a model missing a line is more dangerous with an interval than with none: the interval
counted the uncertainty it could see and said nothing about the rest. The table shows what this
error looks like, but it does not show how often it happens, since both the model and invoices
were invented for the exercise. Problem 20.3 asks you to find the missing line.

Every chapter in this book has a *What this cannot tell you* section, and a chapter with a model
must name **what the structure omits**, not only what the inputs are uncertain about. That defence
is weak because it can name only the omissions its author noticed.

### What works

No check in the toolkit can find a missing node. These four techniques require a person, and each
answers a different question.

**Compare against an invoice.** A model of something that already exists can be checked against
what it cost. That figure is a fact the model did not have. This technique answers whether the
total is the right size: it shows how far short the model is. But it does not tell which line is
missing. Changing a price that is already in the model can close the gap shown by the invoice.
Problem 20.3 uses this check. In its model file, widening a price closes the gap, which is why that
problem's other tests refuse it.

**Ask what is not in the graph.** Read the node list as a list of *categories*, and ask what
category is absent. This technique answers what kind of cost is not in the model. The web service
model works out a total with no line for watching its own fleet—no metrics, no logs, no
traces—and no line for a testing environment. The book's second model sizes that kind of
platform, for an estate of its own. Each is obvious once named, and invisible until then.

**Distrust an answer that is too neat.** A total that is too round. A unit cost close to a
supplier's headline price. A utilisation that is what you hoped. This technique answers where to
look first. A neat answer is a reason to look for the missing term, not evidence that one is
missing.

**Get somebody who did not build it to read it.** This technique answers what the author did not
think of. A model's author cannot see its missing chain. The same gap in their thinking produced
both the model and their reading of it. Nothing in the toolkit can do it for you. People who run
the system day to day are one kind of reader who did not build the model.

### The two wrong responses, and one of them is measured

Problem 20.1 is the first trap. An observation falls outside the interval. Is the model refuted?

Almost certainly not, on one observation. A 90% interval is **supposed** to be missed one time
in ten. A rule that rejects on a single miss will therefore reject a correct model sooner or
later, and the more observations you make, the surer that becomes. Deciding what would count as
evidence is harder than it looks. The problem makes you state a rule rather than react.

Problem 20.2 is the second trap, and it is the one that gets shipped. The model disagrees with
reality, so make the model vaguer until it stops disagreeing. Widen the inputs. The observation
lands inside, and everyone relaxes.

Widening scales every draw's distance from the median by a factor, so the interval ends up that
many times wider. That factor—the number in problem 20.2—is what the widening costs. The median
does not move, so the headline number is unchanged and only the doubt has grown, which is why the
repair passes review. A wider interval contains figures the model used to rule out, so fewer
observations could ever show the model wrong.

**A model that cannot be wrong has stopped being able to be useful.** Widening is how a model
becomes unfalsifiable. An unfalsifiable model is an expensive way of writing down what somebody
already believed.

## What this cannot tell you

**Whether the observability model is complete.** It is not. The model has no line for the
network between tiers. It has no term for what discarded data costs. Nothing in it counts what an
investigation loses when the log line or trace it needed was never kept or has expired. It has no
term for the people who operate it. These are the omissions the book noticed. The chapter's
argument is that there are others, and that nothing in the repository can find them.

**How likely a missing node is.** There is no distribution over "things nobody thought of". Any
attempt to quantify structural uncertainty ends up as another model with its own missing pieces.

**Whether the four techniques above are enough.** They are what this book has. Three of them need
something outside the model, and the fourth needs somebody outside the team. That is a fair
summary of the limitation: **a model cannot audit itself**. Every technique that works is one
that brings in information the model did not have.

**When to stop looking.** There is no test that says a model is complete. There is only a model
that has been compared against reality at least once, and a model that never has been. The second
is a model whose structure nobody has checked, however good its interval looks.

## Key takeaways

:::{div}
:class: takeaways

- **There are two ways to be wrong, and sampling sees only one.** Sampling reports the doubt you
  wrote down about the numbers, and it catches a wrong number only when the range you declared
  contains the true value. It cannot see a wrong shape, which produces a converged interval around
  the wrong answer, and the convergence looks like rigour.
- **Four things could be wrong, and the interval covers two.** A measurement wobbles, a number is
  unknown, the world takes a different path, or the model is the wrong shape. The third needs its
  own run of the model (a scenario), and the fourth appears in no interval and no scenario.
- **A definitional model is right only about the terms it has.** The test from
  [ch01](#point-estimates) assumes every term is there. A model missing a cost line is wrong with
  every input right.
- **An interval makes a model with a missing line more dangerous, not less.** It looks as if the
  doubt has been counted. The model file under problem 20.3 puts almost none of its futures at or
  above the invoice average, and nothing in it says it is short.
- **Nothing automatic finds a missing node.** Compare against an invoice, ask what is not in the
  graph, distrust an answer that is too neat, and get somebody who did not build the model to read
  it. Each technique answers a different question.
- **Widening the inputs until the observation fits is how a model becomes unfalsifiable.** The
  median does not move, only the doubt grows, and a model that cannot be wrong has stopped being
  useful.
:::

## Problems

Four, in `tests/the_missing_node/`. The first three have tests. The last does not, and says why.

**20.1 — What would count as evidence?**
Some observations fall outside the interval. Decide what it would take to call the model refuted,
state a rule that weighs how far out they fall against how many you have, and implement it over
the whole set. One miss is not it.

```bash
python3 -m pytest tests/the_missing_node/test_problem_1_refuted.py -m problem
```

**20.2 — The wrong repair, measured.**
Widen the model until it agrees with the observation, then measure the factor by which the model's
spread about its median has to grow to land the observation inside the 90% interval. That factor
is how many times wider the interval becomes. The median does not move, so the headline figure is
unchanged; a model that cannot be wrong has stopped being able to be useful.

```bash
python3 -m pytest tests/the_missing_node/test_problem_2_widening.py -m problem
```

**20.3 — Find the missing node.**
The page shows a copy of a model file that is deliberately incomplete, missing one cost line. The
table under *Why the interval makes it worse* shows its 90% interval beside an invented monthly
figure, the average of twelve invoices, that lies above the whole interval. Repair the model so
the observation lands inside the interval by adding a new quantity and the line that prices
it—the inputs already there stay as they are. Give the new quantity a provenance source that says
what you would measure to confirm its size, because choosing the range until the invoice fits is
fitting the model to the observation (the trap from problem 20.2). The tests check only that it
has one. There is no answer key; the oracle is a figure the model does not contain.

```bash
python3 -m pytest tests/the_missing_node/test_problem_3_missing_node.py -m problem
```

**20.4 — The node you have not written down.** No test: if a check could find what is missing,
the chapter would not be necessary.

Take your own model and look for what is missing. The four techniques in this chapter each answer
a different question, so use the ones that fit what you have: **compare against an invoice** (where
the system already exists), **ask what is not in the graph**, **distrust an answer that is too
neat**, and **get somebody who did not build it to read it**. The people who run the system day to
day are one kind of reader who did not build the model.

A good answer names at least one quantity that was not in the model and says how much it moves
the answer. What would show it wrong is adding the quantity and watching no output move: then it
was missing and harmless, and the one that matters is still missing. If you find nothing, the
honest conclusion is that you have not looked hard enough, not that the model is complete. There
is no test for completeness, which is what this chapter is about.

## Where to go next

[ch21](#a-tco-for-finance) puts a total in front of the person whose decision it is. The sentence
beside the number says what the model does not contain, and [ch21](#a-tco-for-finance)'s *What
this cannot tell you* names this chapter: a limitation that does not stop applying when the
audience changes.

[ch23](#what-the-model-got-wrong) runs a post-mortem on the book's own models. On the observability
model, where the ingest total leaves out traces, the method blames the inputs that are present,
showing this chapter's failure in action rather than escaping it.

[ch14](#correlation-and-convergence) ends on the sentence this chapter expands, if you skipped
it: a model whose answer has stopped moving between runs has settled its arithmetic, and nothing
else.
