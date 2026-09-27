---
title: "Headroom and failure domains"
short_title: "ch11 Headroom and failure domains"
---

(headroom-and-failure-domains)=
# ch11 · Headroom and failure domains

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
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

They are all percentages, and they are not the same kind of thing.

**A capacity margin protects against a cliff.** Two ceilings protect capacity: *working set
against memory* and *disk fill at horizon*. When the disk fills it shows up as failed writes. When
the working set stops fitting in memory, some reads that were served from memory go to disk and the
service time per request becomes a different number, from a different regime.
[ch08](#regime-changes) is about why nothing in a chain of multiplications can say what that number
is. What the margin buys is the time between noticing and doing something, plus the space a lost
host's copies need to land in.

**A queueing margin protects against a slope.** Nothing fails and nobody is paged. The fleet slides
up [ch06](#queueing-and-the-knee)'s curve and every request pays in latency, for as long as nobody
looks. This margin is larger than the capacity margins in the table, for two reasons. The failure
mode is invisible, and recovering from it means adding machines, which
[ch07](#when-adding-servers-stops-helping) showed works badly.

**A scaling margin protects a budget.** Nothing fails and nothing gets slow. The fleet costs more
than its work is worth. It is the largest percentage in the table, and it is still the loosest
ceiling. Its limit is the whole fleet wasted, so the allowed line still lets a large share of the
fleet go on coordination before the ceiling objects. It is declared anyway, because a cost that has
no bound on it grows.

The right size of each kind of margin is set by a different thing:

- a capacity margin, by how fast you can react and how much room a lost host's copies need;
- a queueing margin, by how much latency every request can afford at the busy hour;
- a scaling margin, by how much waste the budget will carry.

So one percentage applied to all three would fit at most one of them, and the reason it was chosen
would not apply to the other two. The model file gives a reason beside every margin it declares.
Here they are, in its words:

```{include} _generated/headroom-and-failure-domains-margins.md
```

### The one margin you can compute

Most headroom is judgement. One piece of it is arithmetic.

:::{div}
:class: definition

A fleet that has to survive losing hosts needs somewhere for their share of the requests to go. That
capacity is the **failure reserve**. It has to be there beforehand. A fleet that finds it needs a
failure reserve during a loss is already past its queueing margin.
:::

:::{div}
:class: definition

A **failure domain** is the set
of hosts one fault takes out together. One host is the smallest. Hosts that share a rack, a switch
or a power feed make a larger one.
:::

The reserve has to cover the failure domain you plan to survive.
This chapter's arithmetic, and the model's ceiling below, take it to be one host.

Problem 11.1 asks for one number: the share of the fleet's capacity that has to be kept free to
survive losing a given number of hosts. Every fleet keeps one host free for each host it plans to
lose. What changes with fleet size is the share of the fleet that host is. A small fleet keeps a
large share of itself free: one host in five is a fifth of the fleet. A large fleet keeps a small
share free. That is a capacity argument for larger pools, where each loss is a smaller share. It is
not an argument for larger failure domains, which are worse, because more hosts go at once.

**The margin is for a loss, not for a failure.** A host drained for a kernel upgrade removes the
same capacity as one that has died. A rolling upgrade drains hosts on purpose, one after another. So
planned work spends the reserve by design, and a reserve sized only for hardware failure is already
in use while an upgrade runs.

The running example carries this as a ceiling of its own: the queueing margin again, audited with
one host gone, because a host lost at the busy hour is a queueing problem for the survivors:

```{literalinclude} ../models/web_service/stages/14-headroom/model.yaml
:language: yaml
:start-at: hosts_after_failure:
:end-before: outputs:
```

```{iframe} /models/web_service_headroom-reference.html
:width: 100%
The graph as ch11 leaves it, with every margin the model declares. Click any ceiling for its
reason.
```

### Two generations: the host with the most cores, and the last day

The mixed pool from [ch10](#bandwidth-and-the-binding-constraint) is bought for requests routed by
capacity, with some old hosts kept to the horizon. In it, some of this chapter's ceilings mean
something different, and one is new.

Surviving the loss of one host means surviving the loss of the host with the most cores, because
that is the most processing one fault can take away. In a pool of one kind of host every host has
the most cores. In the mixed pool it is a new host. The model's failure ceiling subtracts that
host's cores from the pool's total. The old hosts have more memory, so for memory the biggest loss
is an old host, and the model has no ceiling for that loss.

A shard has to sit whole on one host, and it can land on the smallest. The pool's total disk says
nothing about whether a shard fits on the smallest host, so the smallest host's disk sets a ceiling
of its own, checked against the disk margin.

The old hosts retire on their own schedule, which need not match the purchase. The check has to hold
at the worst point: after they go, while demand is still growing. The model's `old_retired` scenario
is that point: the same new hosts, and no old ones.

The table checks the pool three ways: as bought, with the old hosts kept; on the day they retire;
and against the all-new fleet from [ch10](#bandwidth-and-the-binding-constraint)'s first column, the
purchase the web service model recommends for this workload with no old hosts. Each cell gives the
share of futures past the allowed line (*Over allowed*), then what the plan says at the point
estimate: *ok*, *into the margin* or **over**. The table has the web service's two capacity ceilings
as well: working set against memory, and disk fill at horizon.

```{include} _generated/headroom-and-failure-domains-mixed-pool.md
```

On the day the old hosts retire, three ceilings are **over** at the plan: memory, disk, and losing
the host with the most cores. Memory is the one the old hosts were covering: their extra memory held
the whole working set in [ch10](#bandwidth-and-the-binding-constraint), where memory asked for no
new hosts. The new hosts alone cannot hold the working set or the data.

With the old hosts kept, routing requests equally is **over** at the plan, so the pool bought for
routing by capacity does not survive equal routing. Once the old hosts retire, the two routing rows
agree, because every host in the pool is then the same size.

The shard row does not move, because both generations have the same disk, so the smallest disk is
the same whichever generation remains. The all-new fleet is *ok* at the plan on every ceiling. It is
what buying for the day the old hosts retire would leave on that day.

Buy for the day the old hosts retire, or plan the next purchase for that day. The model shows the
gap; it does not choose between them.

### Margins do not add

A sizing conversation collects margins. Rebuild wants some. Queueing wants some. Growth between
now and the next purchase wants some. Each request arrives separately, each is defensible, and
each is granted.

Margins do not add. Each takes its share of what the previous one left, so applying them in
sequence multiplies them. Take three margins of a quarter each. Added together, they reserve three
quarters of the fleet and leave a quarter working. Applied in sequence, they leave a little over
two fifths working.

So adding over-reserves: a room that adds its margins sizes the fleet as though only a quarter of
it will do the work, and buys hosts that none of the margins it granted asked for. Problem 11.2 is
the composition.

Push the margins up and addition stops describing anything. Three margins of ninety per cent add
to nearly three whole fleets, and no system has negative capacity. Taking nine tenths three times
over leaves a sliver. Multiplying still leaves a fleet with some capacity, where adding said it had less than none.

### What a margin is for, written down

Every ceiling in this book carries a `because`. Not because it is tidy, but because the failure
mode of a margin is specific and predictable: it gets copied.

A margin with a reason attached can be argued with, adjusted when the reason changes, and dropped
when the reason goes away. A margin that is just a number gets carried into the next model, and
the one after that, by people who were not in the room. Ten years later an organisation has a
thirty-per-cent rule that everybody follows and nobody can source.

The toolkit refuses a ceiling without a reason. It cannot check that the reason is true; a reviewer reading it can.

### The output a margin produces

Not a verdict. A probability.

The two ceiling tables at the top of *The material* end with two columns that answer two questions. *Over allowed* shows how often the
design ends up past the allowed line (the limit less the margin), and *Over limit* shows how often
it ends up past the limit itself. A verdict at the plan describes one future, but these columns
describe all the futures the model thinks could happen.

At *utilisation at the busy hour*, the verdict is *ok*, but the *Over limit* column still shows the
design past the limit in a share of the futures. At *utilisation, counting coordination*, the
verdict is already *into the margin* — the plan has spent part of the reserve before anything has
failed. Read its *Over limit* cell. [ch12](#the-sizing-model) prices the difference between a
verdict at the plan and what the columns show.

## What this cannot tell you

**Whether any of these margins is right.** Every margin in this book was declared in its model
file, with a reason, and the reason is an argument rather than a measurement. This chapter argues
that a margin must exist and must be explicable. It does not argue that these particular ones are
correct, and it has no way to.

**How long you have.** A margin buys time between something going wrong and something being done.
How much time depends on how fast your load moves and how quickly you notice, and neither is in
any model here. A generous margin on a system nobody watches is not generous.

**Whether the failure domain is what you think.** The failure arithmetic assumes hosts fail
independently. They do not. They share racks, power, switches, firmware versions, and the
engineer who is applying an update to all of them. A margin sized for one host and spent on a
rack is a margin that was not there.

**Whether two losses can happen at once.** The ceiling *utilisation with one host down* takes
exactly one host away from the fleet. A planned drain during an upgrade and an unplanned loss can
overlap: one host is out for a kernel upgrade when another fails. Then two hosts are gone at the
busy hour. The model has no term for two hosts down at once. A reserve that covers one loss covers
one of them, and the ceiling reports on a fleet that is one host larger than the one serving
requests.

**Whether the mixed pool's checks are all the checks it needs.** It checks losing the host with the
most cores, with requests routed by capacity. It has no check for losing the host with the most
memory, which is an old one, and none for a loss when requests are routed equally. It treats
retirement as every old host leaving on one day, where real hosts leave a few at a time.

## Key takeaways

:::{div}
:class: takeaways

- **Headroom is a rule because the right number differs for every ceiling.** A capacity margin
  protects against a cliff, a queueing margin against a slope, a scaling margin against a budget,
  and one percentage cannot serve all three.
- **The failure reserve is the one margin you can compute, and it is for a loss, not a failure.** A
host drained for an upgrade removes the same capacity as one that has died. Every fleet keeps one
host free for each it plans to lose: a small fleet keeps a large share of itself free and a large
fleet a small share.
- **In a mixed pool, check the biggest loss and the last day.** For processing, the host to keep
free is the one with the most cores. The check has to hold on the day the old hosts retire, when
memory and disk can be the first to break.
- **Margins multiply. They do not add.** Each takes its share of what the one before left, so
  adding reserves more than the margins call for. A fleet sized by adding buys hosts none of the
  margins asked for, and for large margins addition reserves more than the whole fleet.
- **A margin without a reason gets copied.** Every ceiling carries a *because*, so that the margin
  can be argued with, adjusted when the reason changes, and dropped when it goes away.
- **What a margin produces is a probability, not a verdict.** Across the model's futures, *Over
  allowed* is how often the design ends up past the allowed line (the limit less the margin).
  *Over limit* is how often it ends up past the limit itself. The verdict describes the plan at the
  point estimate only.
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
The page shows a fragment of the model file: one ceiling, *connections per host*, with three fields
left empty. Fill in the `unit`, the `headroom` (the margin) and the `because` (the reason), and
change nothing else. The expression and the limit are given. The limit carries its unit by being
multiplied by the constant that holds it, the way the model file does. The unit has to be the one
the expression produces. You can find the units of `concurrency` and `host_count` by clicking each
in the graph above. A margin can be written as a number or as the name of a node that holds one, as
`headroom: queueing_margin` in the listing above does. The toolkit refuses the fragment until all
three are right: a missing or wrong unit is refused by the loader or the units check, and a missing
margin or a missing reason is refused by the model verifier. Each refusal is a rule this chapter
argues for. Once it is accepted, the test evaluates the web service model with the new ceiling and
checks that the ceiling reports a verdict and how often the model's futures take it past its limit:
the same *Verdict* and *Over limit* the tables at the top of this chapter show. The Check says
whether the tests pass; it does not print those values.

```bash
python3 -m pytest tests/headroom_and_failure_domains/test_problem_3_ceiling.py -m problem
```

**11.4 — Your margin, and who chose it.** No test: the answer is a number somebody chose, and the
interesting part is who.

Find the headroom your system is planned to, then find the person or the document that chose it.

Does the margin have a reason attached that is not "it is what we have always used"? Does your
failure domain match the physical layout: are the machines you assume fail independently in the
same rack, the same power feed, the same availability zone?

A good answer has three things: a number, a name or a document, and a reason. If the reason amounts
to a round number, such as twenty or thirty per cent, ask what it would have been had the first
person to say it said a different round number.

What would falsify the answer? Any one of these shows the margin is not the one the system needs:

- the reason names something the system no longer has, such as a hardware generation, a failure
  domain or a traffic pattern that has changed since the number was chosen;
- the reason is for a different kind of margin from the ceiling it sits on, for example a queueing
  reason on a disk ceiling;
- nobody can find who chose it or where it is written, which means there is no reason to check.

Take the number, the name or document, and the reason that holds up under that test back to whoever
sizes the system next.

## Where to go next

[ch12](#the-sizing-model) assembles Part III: every chain, every margin, and a number at the end of
it.

[ch13](#monte-carlo) shows how the *Over allowed* and *Over limit* columns, and the shares in the mixed pool's table, are computed: the
model is worked out many times with its inputs drawn at random, and each column is the share of
those runs past a line.
