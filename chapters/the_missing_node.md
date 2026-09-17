---
title: "The missing node"
short_title: "ch20 The missing node"
---

(the-missing-node)=
# ch20 · The missing node

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch14](#correlation-and-convergence) |
| **What it produces** | The observability model's incomplete ingest total, and what it costs to believe it |
| **Built from** | `observability-reference` |
:::

## The question

How do you find the error that no amount of sampling can see?

Every chapter since [ch13](#monte-carlo) has deferred this one. It is the limitation of the entire
method and it deserves its own chapter rather than a paragraph at the end of somebody else's.

## The material

### Two ways to be wrong

**Wrong about a number.** An input is off. The model is the right shape, the arithmetic is right,
one of the quantities is not what you thought. Every chapter so far has been about this error:
[ch13](#monte-carlo) quantifies it, [ch14](#correlation-and-convergence) refines it,
[ch19](#which-input-is-the-answer) says which one to go and fix.

**Wrong about the shape.** A cost line is missing. A chain is not in the model. A ceiling nobody
declared. Two things multiplied that should have been added.

Sampling handles the first perfectly and is completely blind to the second. Worse than blind:
it produces a beautifully converged interval around the wrong answer, and the convergence looks
like rigour.

### Four things that could be wrong, and the book can count two

The split above is the one that matters, and it is worth drawing once more with the pieces named,
because the book has been using all four of these for twenty chapters without ever putting them in
one place.

**A measurement wobbles.** A measured constant has a standard error, and it is as likely to be
high as low ([ch03](#where-the-numbers-come-from)). This is the smallest of the four and the only
one anybody can reduce by working harder.

**A number is unknown.** An input nobody measured, given a distribution somebody chose: a price, a
growth rate, a count of label values ([ch13](#monte-carlo)). Usually the largest thing inside the
interval, and [ch19](#which-input-is-the-answer) is which of them to go after.

Those two are what the interval is made of. Both are quantities the model can carry, and the whole
apparatus of Parts IV and VI is about them.

**The world takes a different path.** Retention policy changes. Growth stops. Somebody turns the
sampling rate down. This one is *not* in the interval, and it is why this book has scenarios at
all — a scenario is a second run rather than a wider distribution, because the alternative is not
a value the current model could have produced. A cluster bought for the growth case is a different
model of the world, not an unlucky draw from this one
([ch12](#the-sizing-model), [ch16](#power-first)).

**The model is the wrong shape.** This chapter. Not in the interval, not in a scenario, not
anywhere — because nothing in the file knows the term is missing.

The useful thing about naming them is what it says about a wide interval. A wide interval is a
report about the first two. It is silent about the third, which is a modelling decision somebody
took, and it is silent about the fourth, which is a modelling decision nobody knew they were
taking.

### The book's own example, on a published page

```{include} _generated/the-missing-node-outputs.md
```

```{image} _figures/the-missing-node-graph.svg
:alt: What feeds the ingest total, and what is missing from it
:width: 100%
```

The observability model has an ingest figure that is metrics plus logs. It is arithmetically
correct. Every input feeding it is declared, sourced and sampled, and the interval around it is as
honest as the rest of the book.

It is also missing an entire chain, because nobody has measured spans per request:

```{include} _generated/the-missing-node-unmeasured.md
```

This one is visible, because the DSL happens to have a node for the missing thing and the build
marks it. That is the *easy* case, and it is on a published page precisely so the hard case has
something to be compared against.

The hard case is a chain nobody thought of at all. It has no node, so there is nothing to mark, no
box to render, and no way for the model to know it is incomplete. The output is a number with an
interval around it and no indication whatsoever that it is a lower bound.

### Why the interval makes it worse

A single number invites doubt. An interval does not — it looks like the doubt has already been
accounted for.

So a structurally incomplete model with a tight interval is more dangerous than the same model
with no interval at all. The apparatus that was supposed to communicate uncertainty ends up
communicating false confidence, because it quantified the uncertainty it could see and said
nothing about the rest.

That is why every chapter in this book has a *What this cannot tell you* section, and why the one
in a chapter with a model in it must name **what the structure omits** rather than only what the
inputs are uncertain about. It is the only defence available and it is a weak one.

### What actually works

Nothing automatic. Four things that are not automatic:

**Compare against an invoice.** The strongest test available. A model of something that already
exists can be checked against what it actually cost, and that number is a fact the model did not
have. ch14's problem 3 is exactly this, and it is the only exercise in the book where the oracle
is outside the model.

**Ask what is not in the graph.** Read the node list as a list of *categories* and ask what
category is absent. The storage model has no line for rack space, cross-connects, backup, or the
migration that fills the cluster. Each of those is obvious once named and invisible until.

**Check the dimensions of the answer.** A total that is too round, a unit cost that is
suspiciously close to a supplier's headline price, a utilisation that is exactly what somebody
hoped — each is a reason to look for the term that is missing rather than to celebrate.

**Get somebody who did not build it to read it.** The single most effective and least automatable
technique. A model's author cannot see its missing chain, because the same gap in their thinking
produced both.

### The two wrong responses, and one of them is measured

Problem 20.1 is the first trap. An observation falls outside the interval. Is the model refuted?

Almost certainly not, on one observation — a 90% interval is **supposed** to be missed one time in
ten, and a rule that rejects a model on a single miss rejects a correct model roughly whenever it
is correct. Deciding what would count as evidence is harder than it looks and the problem makes
you state a rule rather than react.

Problem 20.2 is the second trap, and it is the one that gets shipped. The model disagrees with
reality, so make the model vaguer until it stops disagreeing. Widen the inputs. The observation
lands inside, everyone relaxes.

Measure what that costs and it is unambiguous: the interval grows until the model can no longer
tell two designs apart, which is the only thing it was for. The median does not move — so the
headline number is unchanged and only the doubt has grown, which is why it passes review.

**A model that cannot be wrong has stopped being able to be useful.** Widening is how a model
becomes unfalsifiable, and an unfalsifiable model is a very expensive way of writing down what
somebody already believed.

## What this cannot tell you

**Whether this chapter's own model is complete.** It is not. The observability model has no line
for the network between tiers, no term for the cost of a query nobody ran, no notion of the people
who operate it. Those are the ones that have been noticed. The chapter's argument is that there
are others and that nothing in the repository can find them.

**How likely a missing node is.** There is no distribution over "things nobody thought of". Any
attempt to quantify structural uncertainty ends up being another model with its own missing
pieces.

**Whether the four techniques above are enough.** They are what this book has. Three of them need
something outside the model and the fourth needs somebody outside the team, which is a fair summary
of the limitation: **a model cannot audit itself**, and every technique that works is one that
brings in information the model did not have.

**When to stop looking.** There is no test that says a model is complete. What there is, is a
model that has been compared against reality at least once — and a model that never has is a model
whose structure nobody has checked, however good its interval looks.

## Problems

Two, in `tests/the_missing_node/`.

**20.1 — What would count as evidence?**
An observation falls outside the interval. Decide what it would take to call the model refuted,
state a rule that holds together, and implement it. One miss is not it.

```bash
python3 -m pytest tests/the_missing_node/test_problem_1_refuted.py
```

**20.2 — The wrong repair, measured.**
Widen the model until it agrees with the observation, then measure what the interval has become.
A model that cannot be wrong has stopped being able to be useful, and this is what that costs.

```bash
python3 -m pytest tests/the_missing_node/test_problem_2_widening.py
```

## Where to go next

[ch21](#a-tco-for-finance) is the last chapter of the argument, and this one is its
prerequisite: the honest
presentation of a total includes what the model does not contain, and saying so out loud is harder
than any of the arithmetic that came before it.

[ch14](#correlation-and-convergence) has the exercise where an invoice refutes a model, if you
skipped it.
