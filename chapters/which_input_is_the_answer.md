---
title: "Which input to go and measure"
short_title: "ch19 Which input to go and measure"
---

(which-input-is-the-answer)=
# ch19 · Which input to go and measure

## The question

Which input should you go and measure first, and how would the model tell you?

An interval describes a problem. Choosing which input to go and measure is the only actionable
thing you can do with one. Everything here works on a model that has already been sampled, so it
needs [ch13](#monte-carlo) behind it rather than the chapter before.

## The material

### More samples never help

The instinct is to run more samples. [ch14](#correlation-and-convergence) said why that fails: a
wide interval is not sampling noise. The interval is a property of the model's inputs. More draws
locate it more precisely. They do not narrow it.

So there are exactly two things that narrow an interval.

- **Measure something.** Replace a guess with a figure that has a standard error.
- **Decide something.** Replace an uncertainty with a constraint: cap the growth by policy, fix
  how long records are kept, shed load above a stated rate.

Both are work. The question is which one is worth doing. The answer is not obvious, because the
model has dozens of uncertain inputs and only one of them matters.

### Swing one thing at a time

```{image} _figures/which-input-is-the-answer-tco.svg
:alt: Which input moves the five-year total most
:width: 100%
```

Each bar swings one input across the middle eighty per cent of its own distribution, with
everything else held still. Problem 19.1 builds this chart, against the host count rather than
the total.

The swing comes from the input's **declared distribution**, not from its slider range. Otherwise
an input somebody gave a generous slider gets a long bar for free, and the chart measures
somebody's choice of slider rather than the model.

The ordering is the useful part. It answers "what should I go and measure first". That is the
only question a tornado answers well.

### What the widest bars have in common

```{image} _figures/which-input-is-the-answer-observability.svg
:alt: Which input moves the retention store most
:width: 100%
```

```{include} _generated/which-input-is-the-answer-residence.md
```

Two charts and a table, because the third is short enough to read as a table. Look at what is at
the top of each.

**Cardinality**, in the observability model. It is a product of uncertain counts, and the
uncertainty compounds ([ch08](#regime-changes)).

**The busy hour**, in the web service's residence time. The day-one rate and the growth that
multiplies it tie at the top. The cost of a request is a distant third, and nothing else is on
the chart at all. Those are the inputs that meet in a division by what is left of the system
([ch06](#queueing-and-the-knee)), and a bar that long is the knee.

**The head count**, in the web service's five-year total. That breaks the pattern the other two
make, and the break is the most useful thing on this page.

The pattern the first two make is this: **the widest bar is somewhere the model is not linear**.
An exponent, a product of uncertain things, a division by a small remainder. Inputs that are
merely multiplied by constants, or added, hardly move anything, however uncertain they are. So the
five-year total ought to be topped by the growth rate, which is raised to a power. And
[ch04](#peak-mean-and-growth)'s tornado, which swings the same inputs against the *recommended*
host count, is topped by growth with nothing else close.

The first chart is against the five-year total, and growth is not on it at all. It cannot be. The
cost chain starts at *hosts in the fleet*, which is a decision somebody took, and a decision has
no distribution. The exponent left the cost model at the moment the fleet was chosen. What remains
downstream of that choice is a bill of materials, and in a bill of materials the largest line
wins: how many people run the fleet, what a licence costs per core, what those people are paid,
and only then what a host costs.

The rule to take from it: **a tornado is about the output you point it at, and pinning a
decision can remove the dominant input from everything downstream of it.** Neither chart is wrong.
They answer different questions. The cost question has a boring answer because the interesting
one was settled before it was asked.

### The correlation the chart cannot show

```{include} _generated/which-input-is-the-answer-correlation.md
```

Declared correlations widen every interval in the book. A tornado has no way to show that. Each
bar moves one input, and a correlation is a statement about two.

So the two figures answer different questions, and you should not read one against the other. The
tornado says which input is worth measuring. The interval says what the model currently believes.
An input with a short bar that is strongly correlated with a long one is still worth attention,
and neither chart will say so.

### What one-at-a-time misses

Problem 19.2 measures a sharper version of the same limitation.

Swing input A alone. Swing B alone. Swing both. If the model were additive in them, the third
would be the sum of the first two. In a model built out of multiplications it is not, and the
model in this book is built out of multiplications.

So a tornado's bars do not add up to the interval, and they are not a decomposition of it. They
are a ranking, and that is all they are. The chart invites you to treat the bar lengths as shares
of the variance, and that is a mistake. A variance-based decomposition does answer that question.
It is not in this toolkit, and `NEXT_STEPS.md` in the repository lists it as work left to do.

### What the measurement would be worth

A ranking is not a quantity. Somebody has to approve the measurement, and they will ask what it
would buy.

That is computable, and the computation is simple. Take one uncertain input and pin it at its
median, as if somebody had gone and measured it perfectly. Re-sample the whole model. What comes
back is the interval the model would report if that one thing were known.

```{include} _generated/which-input-is-the-answer-worth-service.md
```

The last column is a **ceiling**. No real measurement is perfect. A real one leaves a standard
error behind, that error propagates like any other ([ch03](#where-the-numbers-come-from)), and
the interval closes by less than the column says. That bound is what makes the column useful. A
small number in it says the measurement is not worth commissioning *however well it goes*, and
somebody can take that decision before spending anything.

Read down the column. No single input is worth much of the interval. The four at the top are the
people and the prices the tornado put first. Each is worth a modest share, and everything below
them is rounding. A campaign to pin down the *electricity price*, the line a review of a fleet's
running cost spends longest on, would be a quarter's work for a result nobody could see on a
chart.

Now the same experiment against the host count, which is the question
[ch12](#the-sizing-model) asked. The answer has the opposite shape:

```{include} _generated/which-input-is-the-answer-worth-hosts.md
```

One input is worth most of the interval, and everything below it is rounding. It is the growth
rate, which belongs to no target and cannot be measured at all ([ch04](#peak-mean-and-growth)).
The table will keep pointing at it. The only thing you can do with it is *decide* it, by policy,
and accept the flexibility that costs.

And on the observability model, where the answer has a third shape:

```{include} _generated/which-input-is-the-answer-worth-observability.md
```

Two inputs tie at the top, and **the same number is not the same decision**. One is a count of
label values somebody could go and query this afternoon. The other is a growth rate again, with
the same answer: decide it.

Now the bottom rows of the last two tables.

**The measured constants buy nothing.** The record compression ratio in one table, bytes per
sample and bytes per log line in the other, were measured over a declared corpus, with a standard
error, by the most careful machinery in this book. Remove that standard error entirely and
neither interval moves. Their *values* matter, because they scale the answer. Their
*uncertainty* is not what the answer rests on. Measuring them again, better, would produce a
nicer provenance and the same interval.

**And the rows do not add up.** They come to rather more or rather less than the whole, depending
on the model and the output, and they are not shares of anything. Uncertainty in a chain of
multiplications does not divide between the inputs. Problem 19.2 measures the same fact from the
other direction, where it is harder to argue with.

### After you measure it

The point of a sensitivity analysis is to change something, so it ends in a plan. There are three
things you can do with the input at the top:

- **measure it**: turn an assumption into a measured constant with a standard error, which is
  [ch03](#where-the-numbers-come-from)'s discipline, and problem 3.2's arithmetic says how much
  measuring is enough;
- **decide it**: turn an uncertainty into a policy, which costs flexibility rather than money;
- **design around it**: make the answer less sensitive to it, which is usually the most expensive
  option and the most durable.

Then re-run the model, because the tornado will have a different input at the top. That is what
progress looks like here. Not a narrower interval on the same chart, but a different chart.

:::{note} Key takeaways
- **Only two things narrow an interval: measure something or decide something.** More samples locate
  the interval. They never shrink it.
- **A tornado ranks inputs by how far the answer moves when each one swings alone.** The ordering
  answers *what should I measure first*, and that is the only question it answers well.
- **The widest bar is where the model is not linear.** An exponent, a product of uncertain things, a
  division by a small remainder. Pinning a decision can remove the dominant input from everything
  downstream of it.
- **The bars are a ranking, not a decomposition.** They do not add up to the interval, they cannot
  show a correlation, and an input whose effect appears only in combination gets a short bar and can
  still sink you.
- **What a measurement would be worth is a ceiling you can compute before spending anything.** Pin
  an input at its median, re-sample, and read how much the interval closes. Often the input worth
  most is a growth rate, and the only thing to do with a growth rate is decide it.
:::

## What this cannot tell you

**How much the interval would narrow if you measured it *in practice*.** The table above is the
bound, computed by pretending the measurement is perfect. A real one leaves a standard error
behind, and how large that error would be is not knowable before doing the work. So the honest
figure is the ceiling, and the shortfall against it is somebody's judgement about how good a
measurement they can take.

**Anything about interactions.** One at a time, by construction. Problem 19.2 measures the gap,
and the gap is not small in a multiplicative model. An input whose effect appears only in
combination with another gets a short bar and can still be the thing that sinks you.

**Anything about correlated inputs.** As above: a bar is one input and a correlation is two.

**Whether the input can be measured at all.** Against the host count, and again in the
observability model, the input worth most is a growth rate. That is a claim about the future, and
it belongs to no target ([ch04](#peak-mean-and-growth)). The chart will keep pointing at it, and
the honest response is to decide it rather than measure it.

**Whether the model has the right inputs.** An input that is not there has no bar. A tornado of a
model missing a cost line is a confident ranking of the wrong list.
[ch20 · The missing node](#the-missing-node).

## Problems

Three, in `tests/which_input_is_the_answer/`. The first two have tests. The last does not, and says
why.

**19.1 — Build the chart.**
Build the tornado for the number of hosts the model recommends. The test hands you two things:
each input's band, which is the middle eighty per cent of its declared distribution, and a way
to ask the model for the host count with any inputs held. The band is not the slider range, so
every bar answers the same question. Draw one bar per input, longest first.

```bash
python3 -m pytest tests/which_input_is_the_answer/test_problem_1_tornado.py -m problem
```

**19.2 — What one-at-a-time misses.**
Move two inputs separately, then together, and measure the difference. The test hands you the
two bands and the same way of asking the model as before. It names a pair that meets in a
product and a pair that meets in a sum; predict which will show a gap.

```bash
python3 -m pytest tests/which_input_is_the_answer/test_problem_2_interaction.py -m problem
```

**19.3 — Which input yours rests on.** No test: the ranges are the ones you would defend, and only
you can say what those are.

Before computing anything, ask two colleagues which input they think the answer is most sensitive
to. Write down their answers. Then work it out: swing each input across the range you would
defend, one at a time, and see which moves the result most.

The disagreement is the point. In this book's model the growth rate wins whenever the output is a
size and vanishes whenever it is a bill, and neither is what anybody guesses first. In yours it
may be a price, a ratio or a constant nobody has measured. Being wrong about where the
sensitivity is means measuring the wrong thing next.

A good answer has a ranking, and a note of where it differed from what people expected. If it
matched everybody's intuition exactly, check that your ranges are the ones you would defend rather
than the ones that were easy to write.

## Where to go next

[ch20](#the-missing-node) is the input that has no bar because it is not in the model, and the one
error nothing in this book can rank.
