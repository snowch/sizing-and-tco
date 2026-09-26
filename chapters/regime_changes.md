---
title: "Regime changes"
short_title: "ch08 Regime changes"
---

(regime-changes)=
# ch08 · Regime changes

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

When does a chain of multiplications stop describing a system?

Everything in Parts I and III is a product of quantities. This chapter is about the points where a
system stops behaving like a product. It is also about why no amount of care over the inputs will
warn you that you are near one. Those points are why [ch01](#point-estimates) separates a
conditional model from a definitional one.

## The material

### What a chain of multiplications can and cannot say

Every sizing model in this book is, at heart, a product. Bytes per line times lines per second times
seconds of retention. Terabytes times replication divided by compression. Each input is a multiplier
or a divisor; [ch04](#peak-mean-and-growth) shows that growth alone is raised to a power. A change
to one input moves the answer by the same proportion at any size: double a multiplier and the answer
doubles, double a divisor and it halves.

A product covers an enormous amount of the world, which is why the technique works. It cannot
express a **regime change**: a point at which the system stops obeying one rule and starts obeying
another.

Problem 8.1 fits a straight line to a queue, using only the loads a healthy system has run at.
Those points are the dots on the left half of the figure below. They are rows of
[ch06](#queueing-and-the-knee)'s queueing table, and the curve is that chapter's division drawn
smooth. Extrapolate the line to the loads you are planning for, near full utilisation. The fit is
excellent where it was made. At the busy end it is not wrong by a percentage. It is wrong by a
multiple, and the multiple grows with load. The dashed line marks
[ch06](#queueing-and-the-knee)'s allowed line for the queueing margin, the same value as the
*Allowed* column of the *utilisation at the busy hour* row in this page's ceilings table, further
down.

```{image} _figures/regime-changes-knee.svg
:alt: Residence time against utilisation: one division, rising slowly while much of the fleet is idle and steeply as it nears full
:width: 100%
```

The healthy points fit a straight line well and [ch06](#queueing-and-the-knee)'s division equally
well, so the data cannot tell them apart. A straight line fitted there is wrong at the busy end, not
because of how you fit it but because of its shape. The division fitted to the same points follows the curve all the way to the
busy end, because the curve was drawn from it; on a real system, only as far as its assumptions
hold. What tells a line from the division is knowing the mechanism, not collecting more healthy
data. A straight line predicts confidently despite being wrong, because the data it fits to is
clean.

### Three regime changes

**A queue at full utilisation.** Utilisation is how busy the fleet is: the work arriving each
second against the work its cores can do in a second. Below one, [ch06](#queueing-and-the-knee)'s
division holds and the wait grows faster with each step of load. The division has no special
point. At one and past it, work arrives faster than the cores can do it. So
[ch05](#littles-law)'s condition, as much going out as coming in, no longer holds, and the queue
grows for as long as the overload lasts. The division has nothing left to divide by. That is the
regime change. A chain of multiplications has no term for the faster growth near one and nothing
for past one. [ch06](#queueing-and-the-knee)'s ceiling keeps utilisation well below one because
the cost is paid in latency by every request. Where that becomes too much is your tolerance, not a
point on the curve.

**A host lost at the busy hour.** One host goes; its work lands on the survivors and utilisation
rises in one step, with nothing else changed. The survivors' utilisation is one line of arithmetic,
and so is the residence time [ch06](#queueing-and-the-knee) gives them. Problem 8.2 asks you to
predict whether it rises by the same factor as utilisation. For a small enough fleet or busy enough
one, that one step takes survivors past one, the regime change above, reached at once instead of by
growth. There the division has no answer. [ch11](#headroom-and-failure-domains) audits this with a
ceiling of its own, on the survivors' utilisation; it is not in this chapter's model yet.

**A working set that stops fitting.** The working set is the records a busy hour touches: total
records held times the share touched. The fleet has a fixed memory to hold it. While the working set
fits in that memory, every record the busy hour reads can stay in memory. Past that point, some must
go to disk. A model with an average cost per read describes only the mix at the one ratio it was
calibrated for. It describes neither side.

The working set is the regime change this chapter adds to the running example. The model now
includes three things: the share of the records a busy hour touches, the memory the fleet has for
them, and a ceiling on the ratio. The reason for that ceiling says what happens if the working set
exceeds it.

```{literalinclude} ../models/web_service/stages/11-regime/model.yaml
:language: yaml
:start-at: hot_fraction:
:end-before: outputs:
```

The model assumes a request's time is set by its CPU time per request, [ch05](#littles-law)'s
service demand, whatever its share of reads from memory. It has no term for disk waits. This chapter
states that assumption, which did not start here; `cache_fill`'s reason says the same. Past the
ceiling, requests wait for disk reads, and every chain using the service time understates it by an
amount the model cannot compute.

The viewer shows the graph as this chapter leaves it. Open *Inputs* to reach the sliders and,
under them, *Outputs*. Drag *share of records touched in a busy hour*. The last row of *Outputs* is
the ceiling, *working set against memory*. Its badge turns amber past the allowed line and red past
the limit.

```{iframe} /models/web_service_regime-reference.html
:width: 100%
Click the last *Outputs* row to open *Details*, which shows the ceiling's limit, headroom, allowed
value and its reason.
```

### What the three have in common

Each of the three ceilings is a ratio of demand to capacity, with its limit at one: utilisation,
the survivors' utilisation, and the working set against memory. Each is a **threshold with
different physics on either side**. In each case a chain of multiplications computes the ratio
perfectly well: the model is not wrong about the numbers. It is wrong about what those numbers
*mean* past one.

So the model file format has a node kind for this. A `ceiling` does not model the regime
change; nothing in a spreadsheet-shaped model can. It declares where the change is, keeps a margin
away from it, and reports how much of the model's own uncertainty falls on the wrong side:

```{include} _generated/regime-changes-ceilings.md
```

The table shows the running example's ceilings: [ch06](#queueing-and-the-knee)'s *utilisation at the
busy hour*, [ch07](#when-adding-servers-stops-helping)'s two, and this chapter's *working set
against memory*. The host-loss ceiling arrives with [ch11](#headroom-and-failure-domains).

[ch06](#queueing-and-the-knee) defined the last two columns: *Over allowed* is the share of the
model's futures past the margin, and *Over limit* is the share past the limit, where the model has
stopped applying. Look at the *working set against memory* row. Its verdict is *ok*, and its *Over
limit* is the share of futures in which the working set does not fit in memory. Neither column says
how busy the system will be; each says how much of what the model thinks could happen lands past a
line.

### Label cardinality: a product, not a threshold

A label is a tag on a metric such as the endpoint or the status code. Each distinct value multiplies
the number of series that carry it: add many values and the count is multiplied, not incremented.
The observability platform, in [Appendix F](#appendix-f-observability-model) and met in ch02, counts
label cardinality as three numbers multiplied: distinct endpoint values, status values, and
accidental label values from the labels nobody planned. A chain of multiplications expresses this
correctly. There is no point where the rule changes, so label cardinality is not a regime change.

The table below shows each count's band.

```{image} _figures/regime-changes-cardinality.svg
:alt: Label cardinality as a distribution — a product of uncertain counts
:width: 100%
```

```{include} _generated/regime-changes-tornado.md
```

The product's band is wider than any one count's band but narrower than the three widths multiplied,
because the counts are independent in the model and rarely reach their extremes together.
Uncertainty compounds when quantities multiply, which [ch01](#point-estimates)'s problem 1.2
measured. The structure of this count is not in doubt, only its inputs are, so running its inputs
over their ranges shows all of the count's doubt.

### When ranges are enough

A definitional model has no regime changes in it. Watts times hours times price is an accounting identity.
It is true at every scale, and there is no load at which electricity starts behaving differently.
So for a definitional model, running the arithmetic over the inputs' ranges is enough. The structure is not in doubt; only the
numbers are.

A conditional model has thresholds in it, and past a threshold the structure itself changes. Run the
inputs of a model that has stopped applying across their ranges and you measure, precisely, the
doubt in a number that has stopped describing anything.

So a model with a `ceiling` in it is classified as a conditional model, and the toolkit refuses one
that declares a limit with no margin. The distinction is not taxonomy. It separates a model whose
uncertainty you can quantify from a model whose *applicability* you have to bound.

## What this cannot tell you

**Where your thresholds are.** Each ceiling puts its limit at one: the point at which the ratio says
the thing is full. That limit is a definition; the margins below are decisions. Whether your system
changes behaviour before one is something the model does not know: for example, whether reads start
going to disk before the working set outgrows memory. None of the margins was measured, and
measuring where a system changes behaviour means running it into the regime you are trying to avoid.

**How many thresholds you have.** Three regime changes are named above because three were thought
of. A real system has more: a connection limit, a file-descriptor ceiling, a licence tier, a garbage
collector that changes behaviour at some heap size, a network that reorders under load. Each one you
have not declared is a ceiling the model cannot report on, and the model will not tell you it is
missing. [ch20](#the-missing-node) is about that gap.

**What happens past one.** A ceiling says where the model stops applying and nothing about the other
side—that is deliberate. The structure leaves out two things: the time a request waits for a read
from disk, and a queue that grows when work arrives faster than it is done. So the model cannot say
how much worse the far side of any ceiling is. Problem 8.1 measures what it costs to extend a rule
past the data it was fitted on, even below one; past a ceiling there is no data at all.

**Whether the margin is enough.** A headroom is a decision, and this chapter argues only that it
must exist and have a reason. Whether a given one is generous or reckless depends on how fast your
load moves and how long you take to notice, neither of which this book can see.

## Key takeaways

:::{div}
:class: takeaways

- **A chain of multiplications cannot express a regime change.** It computes the crossing quantity
  perfectly and is wrong about what the number means past a point it cannot represent.
- **Three thresholds, each a ratio with its limit at one and different physics on either side.**
  Utilisation ([ch06](#queueing-and-the-knee)). The survivors' utilisation after a host is lost
  ([ch11](#headroom-and-failure-domains)). A working set that stops fitting in memory (this
  chapter).
- **A ceiling does not model the other side. It declares where the change is.** It keeps a margin
  away from it and reports how much of the model's own uncertainty falls beyond it.
- **A model fitted where the system was healthy predicts the wrong thing, confidently.** A straight
  line fitted to the healthy data is wrong by a multiple at the busy end, even though the healthy
  data fits it as well as [ch06](#queueing-and-the-knee)'s division. Knowing the mechanism, not
  collecting more healthy data, tells them apart.
- **A ceiling is one of two things that make a model conditional.** The other is a measured constant
  ([ch01](#point-estimates)). Running the inputs over their ranges quantifies a definitional model's
  doubt, but a conditional model's applicability has to be bounded as well.
- **A wide product of uncertain counts is not a regime change.** Label cardinality multiplies
  distinct counts, and its band is wider than any one of theirs. The rule for the product is the
  same at every size, so running the inputs over their ranges shows all of its doubt.
:::

## Problems

Three, in `tests/regime_changes/`. The first two have tests. The last does not, and says why.

**8.1 — Do what a spreadsheet would do.**
Fit a straight line to the healthy points, nothing above half utilisation, and extrapolate it
towards full utilisation. The test checks four things: the line fits the points it was fitted to,
what you return is a straight line, it falls short at the busy end by a multiple, and the gap widens
with load. A forecast that bends with the curve, such as the queueing model's division, would fail
the straight-line check. But that is the right model, and this problem asks what the wrong one
predicts.

```bash
python3 -m pytest tests/regime_changes/test_problem_1_straight_line.py -m problem
```

**8.2 — A host lost at the busy hour.**
Lose one host from the fleet at the busy hour and work out where the survivors land: their
utilisation, and the residence time [ch06](#queueing-and-the-knee)'s division then gives them.
Predict before you run it whether the residence time rises by the same factor as the utilisation.
The test then shrinks the fleet at the same utilisation until the survivors are past one, where
the division has nothing left to divide by.

```bash
python3 -m pytest tests/regime_changes/test_problem_2_host_loss.py -m problem
```

**8.3 — Every threshold you have.** No test: nothing here knows what your system runs into
first.

Three regime changes are named above because three were thought of. List yours: every limit your
system runs into before it runs out of the thing you normally count. Memory before storage. File
handles. A connection pool. A licence tier. A queue depth somebody set in 2019.

For each, write what happens when it is crossed: not what you would do about it, but what the
system does. The ones where the honest answer is "I do not know" are the expensive ones.

A good answer has more entries than this chapter names and at least one nobody in your team had
written down before. If your list is exactly the regime changes this chapter names and no others,
you have listed the book's system rather than yours.

## Where to go next

Part III begins at [ch09](#capacity), and puts everything in Parts I and II to work: a chain of
multiplications from a stated workload to a number of machines, with ceilings declared where the
chain stops applying.

[ch20](#the-missing-node) is the version of this chapter's limitation that no technique in the
book can address. From inside the model, a threshold nobody declared is indistinguishable from a
threshold that is not there.
