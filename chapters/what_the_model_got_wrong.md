---
title: "What the model got wrong"
short_title: "ch22 What the model got wrong"
---

(what-the-model-got-wrong)=
# ch22 · What the model got wrong

## The question

The design failed. Can the model say why, and what can it never say?

Every chapter so far has ended before anything happened. This one is three years later. It is
the only chapter in the book where the model is the defendant.

:::{important} Nothing here is an observation
No system was watched and no invoice was read. What follows is the model's *own* futures,
filtered to the ones in which the design failed. That is what makes it reproducible, and it is
also exactly what bounds what it can say. A real post-mortem compares a prediction against
something that happened. That is the `estate` target ([ch03](#where-the-numbers-come-from)), and
it belongs to whoever runs the system.
:::

## The material

### The model said this would happen

Start with the uncomfortable half. The fleet [ch12](#the-sizing-model) bought was the one the
point estimates recommended, and the same model reported this about it:

```{include} _generated/what-the-model-got-wrong-ceilings.md
```

The last column said it would be over the knee at the busy hour in a substantial share of the
futures the model thought plausible, and that the working set would outgrow memory in more of
them still. Nobody was misled. Nothing was hidden. The figures were on a page.

That is the first finding of most post-mortems worth doing: **the failure was forecast, in
writing, by the people it later surprised.** What went wrong was not the model. A percentage in a
table is not an event, and a number nobody has to sign for is a number nobody reads out loud.
That is the whole of [ch21](#a-tco-for-finance), arriving too late to help.

### Where the failures actually were

Now the part the model can do well. The sampled futures already contain the failures. They are
the draws where the queueing ceiling, utilisation at the busy hour, came out over its limit. So
the question *what went wrong* is a filter. Take those draws, and look at what each input had
been doing in them.

```{include} _generated/what-the-model-got-wrong-attribution.md
```

Read the *Shift* column. All three inputs sit higher in the failures than they do generally, and
none of them by much. The busy hour on day one is the furthest from its usual self, growth next,
the cost of a request last. Nothing is exactly where it always is, because the three meet in one
multiplication, and any of them can carry the product over the knee.

Now read it against [ch04](#peak-mean-and-growth)'s tornado and
[ch19](#which-input-is-the-answer)'s value-of-information table. Both put growth first and
nothing close. The column here ranks by how far each input moved, not by what the move did, and
the two orderings differ for a structural reason. Growth moved less than the busy hour did and
did more, because the horizon raises it to a power. So these are three different questions:
*what moves the answer*, *what is worth measuring*, and *what broke it*. The third has to be read
with the model's shape beside it. Otherwise it ranks the inputs by how they were written down
rather than by what they do.

### There was no smoking gun

Now the last column, which is the finding.

An input is *extreme* here when it came out beyond its own ninetieth percentile: the kind of
value somebody would describe afterwards as unusual. Something was extreme in most of the futures
where this fleet went over the knee, and the base rate says that is real. The failures contain an
unusual input far more often than futures at large do.

That is not the finding, though. Turn the number round. In a large minority of the failures,
**nothing was extreme**. The busy hour was a little above its usual. Growth was a little above
average. A request took a little longer. That was enough.

This is the sentence a post-mortem culture is worst at accepting, because it is nobody's fault
and it makes a poor slide:

> Some of the failures have a story. A large share of them do not: nothing remarkable happened,
> something unremarkable did, and there was no margin for unremarkable.

That is an argument about [ch11](#headroom-and-failure-domains), not about the world. It is the
kind of conclusion that only exists if somebody looked. The story that gets told instead is
always about the one dramatic thing, because a dramatic thing can be pointed at.

One caution about that column, because it is the sort of statistic that goes wrong quietly. The
share of failures containing something extreme only means anything against the share of *all*
futures containing something extreme, which the table also gives. A model with enough uncertain
inputs has one of them beyond its own p90 more often than not, whether or not anything failed. A
post-mortem that reports "something was unusual" without its base rate has discovered how many
inputs the model has.

### The same method, on a model with a hole in it

Here is what this technique does when the cause is not in the file. The observability model's
ingest total excludes traces entirely, because nobody has measured spans per request
([ch20](#the-missing-node)):

```{include} _generated/what-the-model-got-wrong-unmeasured.md
```

Run the identical attribution against its ingest ceiling, and it is happy to help:

```{include} _generated/what-the-model-got-wrong-incomplete.md
```

The top three are confident, specific and ranked. Not one of them mentions the chain that is
missing, because the chain is not in the samples and never was. If traces were what actually
filled that pipeline, this table is a list of innocent parties in descending order of how guilty
they look.

**A post-mortem inside a model is a post-mortem of that model.** It can tell you which of the
things you thought of was responsible. It cannot tell you that you thought of the wrong things,
and it will not decline to answer.

### The loop this closes

The book has been going round the same circle since [ch03](#where-the-numbers-come-from). This
is the first chapter where it closes:

> **model → measure → predict → build → observe → compare → update**

Parts I to V do the first four. [ch19](#which-input-is-the-answer) is about doing the second one
better, and about knowing whether it is worth it. This chapter is *compare*. The step after it,
*update*, is the only one that makes the next model better than this one.

*Compare* needs a prediction recorded before the fact, with its interval, its inputs, its date
and a hash of the code that produced it. That requirement is unglamorous, and it is why this
repository is shaped the way it is. A forecast reconstructed from memory afterwards is not
evidence, because memory adjusts, and the adjustment always runs in the direction that makes the
present bearable. Every stamped result in this book exists so that somebody who was not there can
make the comparison without taking anybody's word for it.

## What this cannot tell you

**Whether the cause was in the model at all.** The whole chapter conditions on the model's own
samples, so every answer it can give is drawn from the list of things somebody already declared.
[ch20](#the-missing-node) is the failure mode, and this chapter demonstrates it rather than
escaping it.

**A cause from a correlate.** Two inputs that move together are equally implicated by this
method, and the model's declared correlations guarantee there are such pairs
([ch14](#correlation-and-convergence)). Attribution finds what is *associated* with failure. What
caused it is a claim about mechanism, and the mechanism is the part of the model nobody sampled.

**Anything about a failure with no ceiling.** The filter is a ceiling being breached. A design
that failed in a way nobody declared a limit for produces no failing samples to condition on, and
this chapter reports serenely that nothing went wrong.

**What to do about it.** The busy hour being the cause does not say whether to buy more hosts,
shed load, or move the margin. Attribution is a diagnosis. This book has been careful throughout
not to pretend a diagnosis is a remedy.

**Whether any of this happened.** It did not. These are computed futures. The only honest way to
run this chapter against reality is to have written the prediction down first and to go and
observe the system afterwards, and a book can do neither for you.

## Problems

Three, in `tests/what_the_model_got_wrong/`. The first two have tests, one for each half of the
chapter, and the second is worth predicting before you run it. The last does not, and says why.

**22.1 — Attribute the failure.**
Given the draws and which of them failed, rank the inputs by how far each one had to be from its
ordinary self. Use a median, and order by the size of the shift rather than its sign. An input
that is unusually *low* in the failures is just as much of a cause.

```bash
python3 -m pytest tests/what_the_model_got_wrong/test_problem_1_attribute.py
```

**22.2 — How often is there a culprit?**
Work out the share of failures in which nothing was beyond its own ninetieth percentile. Write
your prediction in a comment first. Then do it again with eight inputs that have nothing to do
with the failure, and watch the same statistic find a villain anyway.

```bash
python3 -m pytest tests/what_the_model_got_wrong/test_problem_2_extreme.py
```

**22.3 — A post-mortem on one of yours.** No test: it is your history, and nobody else has it.

Find an estimate you or your team made that turned out badly: a fleet that hit its knee early, a
budget that overran, a tier that needed replacing sooner than planned. Reconstruct what was
assumed at the time, not what is known now.

Then apply this chapter's question. Was the cause an input that moved, or a structure that was
wrong? An input that moved is a wider distribution next time. A structure that was wrong is a
quantity nobody had written down, and no amount of sampling would have found it.

A good answer identifies which of the two it was and says what would have caught it. If the
honest answer is that nothing available at the time would have caught it, write that down. It is
the most useful entry in the list, and the one most often rewritten into a lesson nobody learned.

## Where to go next

[ch20](#the-missing-node) is the limitation this chapter keeps running into. It is worth
re-reading now rather than before: the argument lands differently once you have watched an
attribution name three innocent inputs without hesitating.

[ch03](#where-the-numbers-come-from) is the target a real post-mortem belongs to, and the rules
that make somebody's observation of their own system worth anything to anybody else.

[Appendix E](#appendix-e-web-service-model) is the model this chapter convicted, in full.

And the question the book opened with, which is worth answering out loud now that there are
twenty-two chapters behind it. **How big** it answered in Part III, with a chain of
multiplications and a number you could put on a purchase order. **How much** it answered in Part
V, over a horizon, split between the invoice that gets a meeting and the one that does not. **How
wrong could I be** it answered in the only way anything can: by sampling what was written down,
and then, in [ch20](#the-missing-node) and in the second half of this chapter, by showing you the
part of the answer that sampling cannot reach. A model can tell you how wrong its inputs might
be. Nothing in it can tell you that the model is the wrong shape, and a method that claimed
otherwise would be the most dangerous thing in this book.
