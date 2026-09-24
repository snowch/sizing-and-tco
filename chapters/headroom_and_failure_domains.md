---
title: "Headroom and failure domains"
short_title: "ch11 Headroom and failure domains"
---

(headroom-and-failure-domains)=
# ch11 · Headroom and failure domains

:::{note}
**Draft.** This chapter is written and complete. It is undergoing final review and polish.
:::

## The question

Why is headroom a rule rather than a number?

Because the number is different for every ceiling, for reasons that have nothing to do with each
other. And because the moment it becomes a single number, it becomes a number somebody rounds.

## The material

### Three margins, three different things being protected

Here is every ceiling in the book's two models, with its declared margin. First the running
example's, as this chapter leaves it, then the observability platform's:

```{include} _generated/headroom-and-failure-domains-service.md
```

```{include} _generated/headroom-and-failure-domains-observability.md
```

They are all percentages, and they are not the same kind of thing at all.

**A capacity margin protects against a cliff.** The disk fills, or the working set stops fitting
in memory, and you find out immediately: one as failed writes, the other as a service time that
has doubled. What the margin buys is the time between noticing and doing something, plus the
space a failed host's copies need to land in.

**A queueing margin protects against a slope.** Nothing fails. There is no page. The system slides
down [ch06](#queueing-and-the-knee)'s curve, paying in latency on every request, for as long as
nobody looks. This margin is larger, for two reasons. The failure mode is invisible, and
recovering from it means adding machines, which [ch07](#when-adding-servers-stops-helping) showed
works badly.

**A scaling margin protects a budget.** Nothing fails and nothing gets slow. The fleet costs more
than its work is worth. It is the loosest margin in the book, and it is still worth
declaring, because a cost that nobody has bounded is a cost that grows.

A single "keep thirty per cent free" rule applied to all three would be too tight for one, too
loose for another, and unexplainable for the third. The model file gives a reason beside every
margin it declares. Here they are, in its words:

```{include} _generated/headroom-and-failure-domains-margins.md
```

### The one margin you can compute

Most headroom is judgement. One piece of it is arithmetic.

A fleet that has to survive losing hosts needs somewhere for those hosts' work to go. That
capacity has to be there *beforehand*. A fleet that discovers it needs a failure reserve during a
failure is already over the knee.

Problem 11.1 is that fraction. It has a consequence people rarely state as a capacity argument. A
small fleet pays an enormous margin, because one host in five is a fifth of the fleet. A large
fleet pays almost nothing per host. That is a real and quantitative argument for larger failure
domains, and it is not the argument people usually give for them.

The second half of that problem is worth more than the arithmetic. **The margin is for a loss, not
for a failure.** A host drained for a kernel upgrade costs exactly the same capacity as one that
has died, and planned work is far more common than failure. Most fleets spend their failure
reserve on a Tuesday afternoon. A reserve sized for annual hardware failure is not there when
somebody starts a rolling upgrade.

The running example carries this as a ceiling of its own: the queueing margin again, audited with
one host gone, because a host lost at the busy hour is a queueing problem for the survivors:

```{literalinclude} ../models/web_service/stages/10-headroom/model.yaml
:language: yaml
:start-at: hosts_after_failure:
:end-before: outputs:
```

```{iframe} /models/web_service_headroom-reference.html
:width: 100%
The graph as ch11 leaves it, with every margin the model declares. Click any ceiling for its
reason.
```

```{iframe} /playground/headroom-and-failure-domains/
:width: 100%
The same file, running. Set the queueing margin to zero and two ceilings move at once, because
they share it.
```

### Margins do not add

A sizing conversation collects margins. Rebuild wants some. Queueing wants some. Growth between
now and the next purchase wants some. Each request arrives separately, each is defensible, and
each is granted.

They do not add. Each one takes its share of what the previous one left, so applying them in
sequence is multiplication. Three margins of a quarter each sound like three quarters of the
fleet left working, and they are not: three quarters of three quarters of three quarters is a
little over two fifths. Problem 11.2 is that composition.

Nobody in the room multiplied them. That is how a fleet ends up twice the size anybody intended,
with every individual decision in the chain defensible.

Push the margins up and addition stops describing anything. Three margins of ninety per cent add
to nearly three whole fleets, and no system has negative capacity. Taking nine tenths three times
over leaves a sliver. That is severe, and at least it is a quantity that exists.

### What a margin is for, written down

Every ceiling in this book carries a `because`. Not because it is tidy, but because the failure
mode of a margin is specific and predictable: it gets copied.

A margin with a reason attached can be argued with, adjusted when the reason changes, and dropped
when the reason goes away. A margin that is just a number gets carried into the next model, and
the one after that, by people who were not in the room. Ten years later an organisation has a
thirty-per-cent rule that everybody follows and nobody can source.

The toolkit refuses a ceiling without one. That is the only enforcement available, and it is
better than none.

### The output a margin produces

Not a verdict. A probability.

Read the last two columns of the tables above. They answer one question: across everything this
model thinks could happen, how often does the design end up past this limit? A point estimate
comfortably inside the margin tells you about one future only. [ch13](#monte-carlo) is where the
other futures come from. [ch12](#the-sizing-model) is what the difference between the two
readings costs.

## What this cannot tell you

**Whether any of these margins is right.** Every one was declared by somebody, with a reason, and
the reason is an argument rather than a measurement. This chapter argues that a margin must exist
and must be explicable. It does not argue that these particular ones are correct, and it has no
way to.

**How long you have.** A margin buys time between something going wrong and something being done.
How much time depends on how fast your load moves and how quickly anybody notices, and neither is
in any model here. A generous margin on a system nobody watches is not generous.

**Whether the failure domain is what you think.** The failure arithmetic assumes hosts fail
independently. They do not. They share racks, power, switches, firmware versions, and the
engineer who is applying an update to all of them. A margin sized for one host and spent on a
rack is a margin that was not there.

**What happens when two margins are needed at once.** The composition arithmetic above assumes the
margins are for independent things. A host lost during a growth spike during a busy hour is one
event, not three, and the model has no term for it.

## Key takeaways

:::{div}
:class: takeaways

- **Headroom is a rule because the right number differs for every ceiling.** A capacity margin
  protects against a cliff, a queueing margin against a slope, a scaling margin against a budget,
  and one percentage cannot serve all three.
- **The failure reserve is the one margin you can compute, and it is for a loss, not a failure.** A
  host drained for an upgrade costs the same capacity as one that died. A small fleet pays an
  enormous share for the reserve and a large fleet almost nothing.
- **Margins multiply. They do not add.** Each takes its share of what the last one left, so three
  modest margins can leave well under half the fleet doing the work it was bought for.
- **A margin without a reason gets copied.** Every ceiling carries a *because*, so that the margin
  can be argued with, adjusted when the reason changes, and dropped when it goes away.
- **What a margin produces is a probability, not a verdict.** Across every future the model thinks
  plausible, how often the design ends up past this limit.
:::

## Problems

Four, in `tests/headroom_and_failure_domains/`. The first three have tests. The last does not, and
says why.

**11.1 — What a host loss costs.**
The one piece of headroom that is arithmetic rather than judgement. Then notice what it says about
small fleets, and what it says about planned work.

```bash
python3 -m pytest tests/headroom_and_failure_domains/test_problem_1_rebuild.py -m problem
```

**11.2 — Two margins are not one margin twice.**
Compose several independent margins. Do not add them; the clue that you cannot is what addition
does to three large ones. Then look at what three separately reasonable requests leave you.

```bash
python3 -m pytest tests/headroom_and_failure_domains/test_problem_2_compose.py -m problem
```

**11.3 — Add a ceiling.**
The page shows a fragment of the model file: a ceiling on connections per host with its unit,
its margin and its reason left empty. Fill them in, and get a verdict and a breach probability
out of it. The toolkit refuses it three different ways before it accepts it, and each refusal
is a rule this chapter argues for.

```bash
python3 -m pytest tests/headroom_and_failure_domains/test_problem_3_ceiling.py -m problem
```

**11.4 — Your margin, and who chose it.** No test: the answer is a number somebody chose, and the
interesting part is who.

Find the headroom your system is planned to, then find the person or the document that chose it.
This is usually the shortest problem in the book and the most uncomfortable.

Two follow-ups. Does the margin have a reason attached that is not "it is what we have always
used"? And does your failure domain match the physical layout? Are the machines you assume fail
independently in the same rack, the same power feed, the same availability zone?

A good answer has a number, a name or a document, and a reason. If the reason is round, twenty
per cent or thirty per cent, ask what it would have been if the first person to say it had said a
different round number. That is usually the whole derivation.

## Where to go next

[ch12](#the-sizing-model) is Part III assembled: every chain, every margin, and a number at the
end of it.

[ch13](#monte-carlo) is what the last two columns of every table in this chapter actually came
from.
