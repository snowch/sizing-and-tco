---
title: "Part III — Sizing"
short_title: "Part III — Sizing"
---

(part-sizing)=
# Part III — Sizing

> How do you get from a stated workload to a number of machines you would defend?

Everything so far has been preparation. This part does the arithmetic, and then looks at what it
produced.

**[ch09 · Capacity](#capacity)** is the chain from what an application stores to what a purchase
order says. Two of the chain's four terms are decisions: the replication factor and the disk margin,
each a single value with no range. The other two are uncertain and lean the same way, towards
needing more disk: index overhead has a range that reaches further up than down, and the compression
ratio was measured on one continuous stream, so it represents the most a real store could achieve,
not what it will achieve.

**[ch10 · Three chains, and the binding constraint](#bandwidth-and-the-binding-constraint)** adds
two more chains to the storage chain: one from the requests, and one from the working set that must
fit in memory. The three ask for different numbers of hosts, and the fleet has to satisfy the
largest. The chapter then works out what sizing on one chain costs: how often the fleet ends up too
small because another chain asked for more, and by how much.

**[ch11 · Headroom and failure domains](#headroom-and-failure-domains)** is about the margin under
each ceiling, and why a margin is a rule rather than a number. Margins compose by multiplication:
each margin takes a share of what the previous one left for it. A room that adds its margins instead
reserves more of the fleet than the margins themselves ask for, and ends up buying hosts that no
individual margin requested.

**[ch12 · The sizing model](#the-sizing-model)** assembles all of it and produces the number the
book is about. It lets the inputs move and asks how often the fleet goes past each of its ceilings.
The answer is not one number: a relationship between a number of hosts and a risk. The person who
signs for the fleet chooses a point on it. How those shares were computed is Part IV's subject.
