---
title: "The missing node"
short_title: "ch20 The missing node"
---

(the-missing-node)=
# ch20 · The missing node

## The question

How do you find the error that no amount of sampling can see?

Every chapter since [ch13](#monte-carlo) has deferred this one. It is the limitation of the entire
method. It deserves its own chapter rather than a paragraph at the end of somebody else's.

## The material

### Two ways to be wrong

**Wrong about a number.** An input is off. The model is the right shape and the arithmetic is
right, but one of the quantities is not what you thought. Every chapter so far has been about
this error. [ch13](#monte-carlo) quantifies it, [ch14](#correlation-and-convergence) refines it,
and [ch19](#which-input-is-the-answer) says which one to go and fix.

**Wrong about the shape.** A cost line is missing. A chain is not in the model. A ceiling nobody
declared. Two things multiplied that should have been added.

Sampling handles the first perfectly, and it is blind to the second. Worse than blind:
it produces a beautifully converged interval around the wrong answer, and the convergence looks
like rigour.

### Four things that could be wrong, and the book can count two

That split matters more than any other in the book. Here it is again with all four pieces named,
because the book has been using them for twenty chapters without putting them in one place.

**A measurement wobbles.** A measured constant has a standard error, and it is as likely to be
high as low ([ch03](#where-the-numbers-come-from)). This is the smallest of the four, and the
only one anybody can reduce by working harder.

**A number is unknown.** An input nobody measured, given a distribution somebody chose: a price,
a growth rate, a count of label values ([ch13](#monte-carlo)). This is usually the largest thing
inside the interval, and [ch19](#which-input-is-the-answer) is about which of them to go after.

Those two are what the interval is made of. Both are quantities the model can carry, and the
whole apparatus of Parts IV and VI is about them.

**The world takes a different path.** A launch doubles the busy hour. Growth stops. Somebody
halves how long records are kept. This one is *not* in the interval, and it is why this book has
scenarios at all. A scenario is a second run rather than a wider distribution, because the
alternative is not a value the current model could have produced. A fleet bought for the growth
case is a different model of the world, not an unlucky draw from this one
([ch12](#the-sizing-model), [ch16](#power-first)).

**The model is the wrong shape.** This is the error this chapter is about. It appears in no
interval and no scenario, because nothing in the file knows the term is missing.

Naming the four says what a wide interval is and is not. A wide interval is a report about the
first two. It is silent about the third, which is a modelling decision somebody took. It is
silent about the fourth, which is a modelling decision nobody knew they were taking.

### The book's own example, on a published page

```{include} _generated/the-missing-node-outputs.md
```

```{image} _figures/the-missing-node-graph.svg
:alt: What feeds the ingest total, and what is missing from it
:width: 100%
```

The observability model has an ingest figure that is metrics plus logs. It is arithmetically
correct. Every input feeding it is declared, sourced and sampled, and the interval around it is
as honest as the rest of the book.

It is also missing an entire chain, because nobody has measured spans per request:

```{include} _generated/the-missing-node-unmeasured.md
```

This one is visible, because the model file format happens to have a node for the missing thing,
and the toolkit marks it. That is the *easy* case. It is on a published page so that you have
something to compare the hard case against.

The hard case is a chain nobody thought of at all. It has no node, so there is nothing to mark,
no box to render, and no way for the model to know it is incomplete. The output is a number with
an interval around it, and no indication whatsoever that it is a lower bound.

### Why the interval makes it worse

A single number invites doubt. An interval does not. It looks as if the doubt has already been
accounted for.

So a structurally incomplete model with a tight interval is more dangerous than the same model
with no interval at all. The apparatus that was supposed to communicate uncertainty ends up
communicating false confidence. It quantified the uncertainty it could see, and said nothing
about the rest.

That is why every chapter in this book has a *What this cannot tell you* section. It is also why
the one in a chapter with a model in it must name **what the structure omits**, not only what the
inputs are uncertain about. That is the only defence available, and it is a weak one.

### What works

Nothing automatic. Four things that are not:

**Compare against an invoice.** The strongest test available. A model of something that already
exists can be checked against what it cost, and that number is a fact the model did not have.
Problem 14.3 is that check. It is the only exercise in the book where the oracle is outside
the model.

**Ask what is not in the graph.** Read the node list as a list of *categories*, and ask what
category is absent. The web service model has no line for rack space, cross-connects, backup,
the database's own licence, or the migration that fills the fleet. Each of those is obvious once
named, and invisible until then.

**Distrust an answer that is too neat.** A total that is too round. A unit cost suspiciously
close to a supplier's headline price. A utilisation that is exactly what somebody hoped. Each is
a reason to look for the term that is missing, not a reason to celebrate.

**Get somebody who did not build it to read it.** The single most effective technique, and the
least automatable. A model's author cannot see its missing chain, because the same gap in their
thinking produced both.

### The two wrong responses, and one of them is measured

Problem 20.1 is the first trap. An observation falls outside the interval. Is the model refuted?

Almost certainly not, on one observation. A 90% interval is **supposed** to be missed one time
in ten. A rule that rejects on a single miss will therefore reject a correct model sooner or
later, and the more observations you make, the surer that becomes. Deciding what would count as
evidence is harder than it looks. The problem makes you state a rule rather than react.

Problem 20.2 is the second trap, and it is the one that gets shipped. The model disagrees with
reality, so make the model vaguer until it stops disagreeing. Widen the inputs. The observation
lands inside, and everyone relaxes.

Measure what that costs and the answer is unambiguous. The interval grows until the model can no
longer tell two designs apart, which is the only thing it was for. The median does not move. So
the headline number is unchanged and only the doubt has grown, which is why it passes review.

**A model that cannot be wrong has stopped being able to be useful.** Widening is how a model
becomes unfalsifiable. An unfalsifiable model is an expensive way of writing down what somebody
already believed.

:::{note} Key takeaways
- **There are two ways to be wrong, and sampling sees only one.** Wrong about a number is what the
  interval reports. Wrong about the shape produces a converged interval around the wrong answer, and
  the convergence looks like rigour.
- **Four things could be wrong, and the interval covers two.** A measurement wobbles, a number is
  unknown, the world takes a different path, or the model is the wrong shape. The third is a
  scenario and the fourth is a blind spot, and neither is in the interval.
- **An interval makes a structurally incomplete model more dangerous, not less.** It looks as if the
  doubt has already been accounted for.
- **Nothing automatic finds a missing node.** Compare against an invoice, read the node list as a
  list of categories and ask what is absent, distrust an answer that is too neat, and get somebody
  who did not build the model to read it.
- **Widening the inputs until the observation fits is how a model becomes unfalsifiable.** The
  median does not move, only the doubt grows, and a model that cannot be wrong has stopped being
  useful.
:::

## What this cannot tell you

**Whether this chapter's own model is complete.** It is not. The observability model has no line
for the network between tiers, no term for the cost of a query nobody ran, and no notion of the
people who operate it. Those are the omissions somebody noticed. The chapter's argument is that
there are others, and that nothing in the repository can find them.

**How likely a missing node is.** There is no distribution over "things nobody thought of". Any
attempt to quantify structural uncertainty ends up as another model with its own missing pieces.

**Whether the four techniques above are enough.** They are what this book has. Three of them need
something outside the model, and the fourth needs somebody outside the team. That is a fair
summary of the limitation: **a model cannot audit itself**. Every technique that works is one
that brings in information the model did not have.

**When to stop looking.** There is no test that says a model is complete. There is only a model
that has been compared against reality at least once, and a model that never has been. The second
is a model whose structure nobody has checked, however good its interval looks.

## Problems

Three, in `tests/the_missing_node/`. The first two have tests. The last does not, and says why.

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

**20.3 — The node you have not written down.** No test: if a check could find what is missing,
the chapter would not be necessary.

Take your own model and go looking for what is missing. Use whichever of this chapter's
techniques applies: compare it against a system that already exists, look for a quantity that
appears in an invoice and nowhere in the model, or ask somebody who operates it rather than plans
it.

The last one is usually the fastest. The people who carry a system know about the quantity that
doubles the storage and appears in no design document. They are rarely asked.

A good answer names at least one quantity that was not in the model and says how much it moves
the answer. What would show it wrong is adding the quantity and watching no output move: then it
was missing and harmless, and the one that matters is still missing. If you find nothing, the
honest conclusion is that you have not looked hard enough, not that the model is complete. There
is no test for completeness, which is what this chapter is about.

## Where to go next

[ch21](#a-tco-for-finance) is the last chapter of the argument, and this one is its prerequisite.
An honest presentation of a total includes what the model does not contain, and saying so out
loud is harder than any of the arithmetic that came before it.

[ch14](#correlation-and-convergence) has the exercise where an invoice refutes a model, if you
skipped it.
