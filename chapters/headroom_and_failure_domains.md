---
title: "Headroom and failure domains"
short_title: "ch11 Headroom and failure domains"
---

(headroom-and-failure-domains)=
# ch11 · Headroom and failure domains

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch06](#queueing-and-the-knee), [ch09](#capacity) |
| **What it produces** | Every declared margin in the book, and the reason for each |
| **Built from** | `storage_cluster-reference`, `observability-reference`, `service_tier-reference` |
:::

## The question

Why is headroom a rule rather than a number?

Because the number is different for every ceiling, for reasons that have nothing to do with each
other — and because the moment it becomes a single number, it becomes a number somebody rounds.

## The material

### Three margins, three different things being protected

Here is every ceiling in the book's three models, with its declared margin:

```{include} _generated/headroom-and-failure-domains-storage.md
```

```{include} _generated/headroom-and-failure-domains-service.md
```

```{include} _generated/headroom-and-failure-domains-observability.md
```

They are all percentages and they are not the same kind of thing at all.

**A capacity margin protects against a cliff.** The disk fills, writes fail, and you find out
immediately. What the margin buys is the time between noticing and doing something, plus the space
a failed machine's data needs to land in.

**A queueing margin protects against a slope.** Nothing fails. There is no page. The system slides
down [ch06](#queueing-and-the-knee)'s curve, paying in latency on every request, for as long as
nobody looks. This margin is larger, because the failure mode is invisible and because recovering
from it means adding machines — which [ch07](#when-adding-servers-stops-helping) showed works
badly.

**A scaling margin protects a budget.** Nothing fails and nothing gets slow; the tier simply costs
more than its work is worth. It is the loosest margin in the book and it is still worth declaring,
because a cost that nobody has bounded is a cost that grows.

A single "keep thirty per cent free" rule applied to all three would be too tight for one, too
loose for another, and unexplainable for the third.

### The one margin you can actually compute

Most headroom is judgement. One piece of it is arithmetic.

A cluster that has to survive losing machines needs somewhere for those machines' data to go. That
space has to be there *beforehand* — a cluster discovering it needs a rebuild reserve during a
rebuild has already failed.

Problem 11.1 is that fraction. It has a consequence people rarely state as a capacity argument: a
small cluster pays an enormous margin, because one machine in five is a fifth of the estate, while
a large cluster pays almost nothing per machine. That is a real and quantitative argument for
larger failure domains, and it is not the argument people usually give for them.

The second half of that problem is worth more than the arithmetic. **The margin is for a loss, not
for a failure.** A machine drained for an upgrade costs exactly the same capacity as one that has
died, and planned work is far more common than failure. Most clusters spend their rebuild reserve
on a Tuesday afternoon. A reserve sized for annual hardware failure is not there when somebody
starts a rolling upgrade.

### Margins do not add

A sizing conversation collects margins. Rebuild wants some. Queueing wants some. Growth between
now and the next purchase wants some. Each request arrives separately, each is defensible, and
each is granted.

They do not add. Each one takes its share of what the previous one left, so applying them in
sequence is multiplication — and three separately modest margins leave you with well under half of
the cluster doing the work it was bought for. Problem 11.2 is that composition.

Nobody in the room multiplied them. That is how a cluster ends up twice the size anybody intended,
with every individual decision in the chain defensible.

Push the margins up and addition stops describing anything. Three margins of ninety per cent add
to nearly three whole clusters, and no system has negative capacity. Taking nine tenths three
times over leaves a sliver — severe, and at least a quantity that exists.

### What a margin is for, written down

Every ceiling in this book carries a `because`. Not because it is tidy, but because the failure
mode of a margin is specific and predictable: it gets copied.

A margin with a reason attached can be argued with, adjusted when the reason changes, and dropped
when the reason goes away. A margin that is just a number gets carried into the next model, and
the one after that, by people who were not in the room. Ten years later an organisation has a
thirty-per-cent rule that everybody follows and nobody can source.

`scripts/verify-models.py` refuses a ceiling without one, which is the only enforcement available
and is better than none.

### The output a margin actually produces

Not a verdict. A probability.

Read the last two columns of the tables above. They answer one question: across everything this
model thinks could happen, how often does the design end up past this limit? A point estimate
comfortably inside the margin tells you about one future only. [ch13](#monte-carlo) is where the
other futures come from, and [ch12](#the-sizing-model) is what the difference between the two
readings costs.

## What this cannot tell you

**Whether any of these margins is right.** Every one was declared by somebody, with a reason, and
the reason is an argument rather than a measurement. This chapter argues that a margin must exist
and must be explicable. It does not argue that these particular ones are correct, and it has no
way to.

**How long you have.** A margin buys time between something going wrong and something being done.
How much time depends on how fast your load moves and how quickly anybody notices, and neither is
in any model here. A generous margin on a system nobody watches is not generous.

**Whether the failure domain is what you think.** The rebuild arithmetic assumes machines fail
independently. They do not: they share racks, power, switches, firmware versions and the engineer
who is applying an update to all of them. A margin sized for one machine and spent on a rack is a
margin that was not there.

**What happens when two margins are needed at once.** The composition arithmetic above assumes the
margins are for independent things. A rebuild during a growth spike during a busy hour is one
event, not three, and the model has no term for it.

## Problems

Two, in `tests/headroom_and_failure_domains/`.

**11.1 — What a node loss costs.**
The one piece of headroom that is arithmetic rather than judgement. Then notice what it says about
small clusters, and what it says about planned work.

```bash
python3 -m pytest tests/headroom_and_failure_domains/test_problem_1_rebuild.py
```

**11.2 — Two margins are not one margin twice.**
Compose several independent margins. Do not add them — the clue that you cannot is what addition
does to three large ones. Then look at what three separately reasonable requests leave you.

```bash
python3 -m pytest tests/headroom_and_failure_domains/test_problem_2_compose.py
```

## Where to go next

[ch12](#the-sizing-model) is Part III assembled: every chain, every margin, and a number at the
end of it.

[ch13](#monte-carlo) is what the last two columns of every table in this chapter actually came
from.
