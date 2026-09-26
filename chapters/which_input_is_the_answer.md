---
title: "Which input to go and measure"
short_title: "ch19 Which input to go and measure"
---

(which-input-is-the-answer)=
# ch19 · Which input to go and measure

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

Which input should you go and measure first, and how would the model tell you?

An interval describes a problem, but it does not tell you what to do about it. You can measure an
input, decide it, or design around it — and before any of those, you need to know which input the
answer rests on. Everything here works on a model that has already been sampled, so it needs
[ch13](#monte-carlo) behind it rather than the chapter before.

## The material

### More samples never help

The instinct is to run more samples. [ch14](#correlation-and-convergence) said why that fails: a
wide interval is not sampling noise. The interval is a property of the model's inputs. More draws
locate it more precisely. They do not narrow it.

Three things narrow an interval, each aimed at one input.

- **Measure it.** Replace a guess with a figure that has a standard error. That is
  [ch03](#where-the-numbers-come-from)'s discipline; problem 3.2's arithmetic says how much
  measuring is enough. It costs the measurement.
- **Decide it.** Replace an uncertainty with a constraint: cap the growth by policy, or fix how
  long records are kept. It costs flexibility rather than money.
- **Design around it.** Change the system so the answer depends less on the input: shed load above
  a stated rate, so the size of the fleet no longer depends on how high the busy hour goes. It
  costs money and engineering work, and it lasts, whatever value the input turns out to have.

All three are work. The question is which input to spend it on. The answer is not obvious: on some
outputs one input carries most of the interval, and on others no single input carries much of it.
The tables further down show both.

### Swing one thing at a time

```{image} _figures/which-input-is-the-answer-tco.svg
:alt: Which input moves the five-year total most
:width: 100%
```

Each bar swings one input across the middle eighty per cent of its own distribution, with
everything else held still. Problem 19.1 builds this chart, against the host count rather than
the total.

The swing comes from the input's **declared distribution**, not from its slider range. Otherwise
an input the modeller gave a generous slider would get a long bar for free, and the chart would
measure the modeller's choice of slider rather than the model.

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

[ch14](#correlation-and-convergence) sampled both reference models twice: once with their declared
correlations and once without. Declaring that two inputs move together widened every interval it
measured. A tornado cannot show that, because each bar moves one input and a correlation is a
statement about two.

The tornado and the interval answer different questions. The tornado ranks inputs by how far each
moves the answer alone, while the interval, sampled with correlations, says what the model
currently believes. An input with a short bar that is strongly correlated with a long one is still
worth attention, and the tornado will not tell you so.

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

A ranking is not a quantity. Whoever approves a measurement will ask what it would buy. That can be
computed, and simply: take one uncertain input and pin it, as if measured perfectly, then re-sample
the whole model. What comes back is the interval the model would report if that one thing were
known.

A perfect measurement can land anywhere in the input's band, and you do not know where until you
take it. Each input is pinned three times: at the low end, middle, and high end — the same two ends
the tornado swings it between. Each column is the share of today's interval that the pin
removes, and a negative share means the interval came back wider. Here it is against the five-year
total:

```{include} _generated/which-input-is-the-answer-worth-service.md
```

No single input removes much of the five-year total's interval, wherever it lands. The four at the
top are engineers, licence per core, salary, and host price. Everything below removes almost
nothing in any column, the electricity price included.

Licence per core removes the same share wherever it lands: it is only multiplied by the fleet's
fixed count of cores and added to the other lines. Engineers and salary remove more if found low
than high because they multiply each other. An input whose row is small in all three columns is
not worth measuring, and you can tell that before spending anything.

No real measurement is perfect. A real one leaves a standard error behind, that error propagates
like any other ([ch03](#where-the-numbers-come-from)), and the table does not include it.

Now the same experiment against the host count, which is the question [ch12](#the-sizing-model)
asked. The answer has the opposite shape:

```{include} _generated/which-input-is-the-answer-worth-hosts.md
```

One input, annual growth, dominates every column. Where it lands matters most: found low, it would
remove most of the interval; found high, far less.

At its high end, three inputs leave the interval wider: the day-one busy-hour rate, the share of
records touched, and CPU time per request. Each multiplies the demand, so a high value scales up
every other input's contribution.

Growth belongs to no target and cannot be measured at all ([ch04](#peak-mean-and-growth)). The
table will keep pointing at it. The only thing you can do with it is decide it, by policy, and
accept the flexibility that costs.

And on the observability model, where the answer has a third shape:

```{include} _generated/which-input-is-the-answer-worth-observability.md
```

In the retention store, annual growth and extra accidental label values almost tie in the middle
column. The ends separate them: found low, growth removes more; found high, neither removes
anything.

**The same number is not the same decision.** Extra accidental label values are a count you could
query from your own system this afternoon. Growth is a forecast again, with the same answer:
decide it.

**The measured constants buy nothing.** The record compression ratio in the host count's table, and
bytes per sample and bytes per log line in the retention store's, were measured over a declared
corpus, with a standard error, by the most careful machinery in this book. Pin any of them at
either end of its band or at its middle, and the interval does not move.

Their *values* matter, because they scale the answer. Their *uncertainty* is not what the answer
rests on. Measuring them again, better, would produce a nicer provenance and the same interval.

**And the rows do not add up.** The middle column of the five-year total's table comes to well
under the whole interval, and the retention store's to more than the whole. The rows are not shares
of anything. Uncertainty in a chain of multiplications does not divide between the inputs.

### Turning the ranking into a plan

The point of a sensitivity analysis is to change something, so it ends in a plan. Take the input at
the top and measure it, decide it, or design around it. Then re-run the model. The tornado will
have a different input at the top. That is what progress looks like here: not a narrower interval
on the same chart, but a different chart.

## What this cannot tell you

**How much the interval would narrow if you measured it *in practice*.** The tables pin an input
exactly, at three places in its band. A real measurement is not exact: it leaves a standard error
behind, and how large that error would be is not knowable before doing the work. Nor is where it
will land, until you take it. For an input that multiplies others, where it lands decides whether
the interval narrows a lot, a little, or widens. So the tables show what a perfect measurement would
do, but how close you get to it depends on the measurement you can take.

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

## Key takeaways

:::{div}
:class: takeaways

- **Three things narrow an interval: measure an input, decide it, or design around it.** More
  samples locate the interval. They never shrink it.
- **A tornado ranks inputs by how far the answer moves when each one swings alone.** The ordering
  answers *what should I measure first*, and that is the only question it answers well.
- **The widest bar is where the model is not linear.** An exponent, a product of uncertain things, a
  division by a small remainder. Pinning a decision can remove the dominant input from everything
  downstream of it.
- **The bars are a ranking, not a decomposition.** They do not add up to the interval, they cannot
  show a correlation, and an input whose effect appears only in combination gets a short bar and can
  still sink you.
- **What a perfect measurement of an input would buy can be computed before you spend anything.**
  Pin the input at the low end, middle and high end of its band and re-sample to read how much of
  the interval each pin removes. An input that multiplies others, found high, can leave the
  interval wider. Often the input at the top is a growth rate, and the only thing to do with a
  growth rate is decide it.
:::

## Problems

Three, in `tests/which_input_is_the_answer/`. The first two have tests. The last does not, and says
why.

**19.1 — Build the chart.**
Build the tornado for the number of hosts the model recommends. The test hands you two things:
each input's band, which is the middle eighty per cent of its declared distribution, and a way
to ask the model for the host count with any inputs held. The band is not the slider range, so
every bar answers the same question. Return one bar per input, as the input's name and the bar's
length, longest first.

```bash
python3 -m pytest tests/which_input_is_the_answer/test_problem_1_tornado.py -m problem
```

**19.2 — What one-at-a-time misses.**
Move two inputs separately, then together, and measure the difference: how far the joint move is
from the two separate moves added up, as a fraction of those two. The test hands you the two bands
and the same way of asking the model as in problem 19.1. It runs your function on two pairs from
the web service: the annual growth factor and the index overhead, which meet in a product, and the
electricity price and the number of engineers, which meet only in a sum. The second pair checks
that your function finds nothing where there is nothing to find.

```bash
python3 -m pytest tests/which_input_is_the_answer/test_problem_2_interaction.py -m problem
```

**19.3 — Which input yours rests on.** No test: the ranges are the ones you would defend, and only
you can say what those are.

Before computing anything, ask two colleagues which input they think the answer is most sensitive
to. Write down their answers. Then work it out: swing each input across the range you would
defend, one at a time, and see which moves the result most.

The disagreement is the point. In this book's web service model, growth dominates the ranking
whenever the output is a size and disappears whenever it is a bill, where people and licences come
first. In yours the top may be a price, a ratio or a constant nobody has measured. Being wrong about
where the sensitivity is means measuring the wrong thing next.

A good answer has a ranking, and a note of where it differed from what people expected. If it
matched everybody's intuition exactly, check that your ranges are the ones you would defend rather
than the ones that were easy to write.

## Where to go next

[ch20](#the-missing-node) is the input that has no bar because it is not in the model, and the one
error nothing in this book can rank.
