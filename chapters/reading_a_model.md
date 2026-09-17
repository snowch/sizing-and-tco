---
title: "Reading a model"
short_title: "ch01 Reading a model"
---

(reading-a-model)=
# ch01 · Reading a model

:::{note} Prerequisites, and what this chapter is built from
:class: dropdown

| | |
|---|---|
| **Prerequisites** | [ch00](#prerequisites-and-setup) |
| **What it produces** | Every node kind, against the storage model, and the conversions the build applies |
| **Built from** | `models/storage_cluster/model.yaml`, `storage_cluster-reference` |
:::

## The question

What is a model file, and why is it not a spreadsheet?

You could build everything in this book in a spreadsheet. People do, and the results run
organisations. "Spreadsheets are bad" is not an argument and is not true, so the case for a text
file has to be narrow and exact.

## The material

### What a spreadsheet cannot hold

A cell holds a value. It does not hold the fact that the value was measured last March against
version 2.4 of something, or that it is a vendor's claim nobody has checked, or that it was agreed
in a meeting by people who have since left. Those facts live in the head of whoever built the
sheet, and they leave when that person does.

Nor does a cell have a unit. `=B4*C7` is as valid as any other product, and multiplying series by
requests gives a number that looks exactly like a number of bytes.

So a model here is a graph of **named quantities** in a text file that diffs and reviews like
code. Each node declares a unit, so the build can refuse the product that should never have been
taken. Each node also declares a kind, which says what sort of quantity it is:

```{include} _generated/reading-a-model-kinds.md
```

### `input` — a number, and who is claiming it

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: drive_price:
:end-before: drive_capex:
```

A value or a distribution, a unit, and a provenance — what kind of claim this is, and where it
came from. The kind and the source are both required, and the build fails without either. There
are three kinds: `fact`, `vendor_claim`, `assumption`. Confusing the first with the second is
what costs money, and [ch03](#where-the-numbers-come-from) is about telling them apart.

The `range` is what a slider on the interactive page moves between. It is also a claim: it says
what you would consider a defensible setting, which is a different and narrower thing than what
the distribution says is possible.

### `derived` — arithmetic, whose units are checked

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: raw_per_usable:
:end-before: raw_capacity:
```

A formula over other nodes. The build **checks** the declared unit against what the formula
produces rather than taking it on trust.

Checking dimensions alone is not enough, and one real error in this repository proved it. Cost
per terabyte per year and cost per terabyte per month have identical dimensions and differ by a
factor of twelve. A check that compared only dimensionality would have waved the storage model's
unit cost through, twelve times too large, looking entirely plausible. So the build converts as
well as checks:

```{include} _generated/reading-a-model-conversions.md
```

Every row there is a place where somebody wrote a formula in the units their invoices came in,
declared the answer in the unit they wanted to read, and the build did the arithmetic that
everybody gets wrong by hand. [Appendix D](#appendix-d-units) has the rest of the traps.

### `measured` — a constant that belongs to something

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: object_compression:
:end-before: replication_factor:
```

Four fields. The last one names a stamped file, and that file carries the value, the standard
error, the corpus, the codec and the implementation. A compression ratio is not a fact about the
world; it is a fact about some data and some software at some version, and a model that treated it
as a constant would be hiding the most interesting thing about itself.

When the file does not exist, the node has no value — and neither does anything downstream of it.
Nothing is estimated in its place and nothing has to be marked by hand; the state propagates down
the graph on its own. [Appendix F](#appendix-f-observability-model) shows one of those on a
published page.

### `ceiling` — a limit, with a margin and a reason

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: fill_level:
:end-before: read_utilisation:
```

The kind that has no equivalent in a spreadsheet at all.

A ceiling watches an expression, compares it against a limit, and subtracts a declared margin.
The margin is required: a limit with no headroom is not a sizing rule, it is a number with an
inequality next to it. The reason is required too, because a margin nobody can argue with gets
copied into the next model by somebody who does not know what it was for.

The headroom here is not a number but the *name of another node*, the same one the sizing formula
uses. That is deliberate. Writing the same fraction in both places is how a model comes to be
sized for one margin and audited against another, six months after anybody remembers there were
two.

What a ceiling produces is not a verdict but a probability: across everything the model thinks
could happen, how often is this limit breached? [ch13](#monte-carlo) is where that number comes
from and [ch11](#headroom-and-failure-domains) is what to do about it.

### The whole thing, as a picture

```{image} _figures/reading-a-model-graph.svg
:alt: The storage model as a dependency graph, coloured by node kind and provenance
:width: 100%
```

Colour is kind. An input's border says what it is claiming: solid for a fact, dashed for a
vendor's claim, dotted for an assumption. Arrows run from cause to effect, and every node sits
immediately to the right of the last thing it depends on.

Two things read straight off it. The graph is **wide at the left and narrow at the right** —
dozens of quantities collapsing into a handful of answers, which is what makes a single wrong
input so hard to spot downstream. And there is a lot of dotted border, so a lot of this model is
assumption — the honest state of any model built before anybody has measured anything.

### How the build tells a sizing model from a cost model

The last row of the node census said *sizing model*, and the build worked that out rather than
being told. A model with a `measured` node or a `ceiling` in it **is** a sizing model; one with
neither **is** a cost model. `scripts/verify-models.py` holds the two to different rules, and a
sizing model that declares a limit with no margin does not build.

That is [the front matter](#preface)'s central claim, arranged so that the repository enforces it.
A thesis the build does not check is a paragraph.

## What the model says

```{include} _generated/reading-a-model-outputs.md
```

## What this cannot tell you

**Whether the model is a good description of anything.** Everything above is about form. A model
can declare every unit correctly, cite every input, and still describe a system that does not
exist — and the build will pass it, because the build has never seen your datacentre.

**What the right shape for a distribution is.** The DSL offers four shapes, refuses a node that
declares two of them, and has no opinion about which one belongs on a given input. That is an
editorial decision with your name on it ([ch13](#monte-carlo)).

**Whether a formula is the right formula.** Dimensional analysis catches a product that should
never have been taken. It does not catch a sum that should have been a product, or a term that is
missing entirely — both of which typecheck perfectly. That error is the subject of
[ch20](#the-missing-node), and nothing in this chapter can see it.

**What a `range` means.** It bounds a slider and nothing else. An input can be inside its declared
range and wildly outside anything defensible, and the model will keep computing.

## Problems

Three, in `tests/reading_a_model/`. Each is one node kind and what declaring it commits you to.

**1.1 — Add a ceiling.**
Add one to the storage model, with a margin and a reason, and get a verdict and a breach
probability out of it. The build will refuse it three different ways before it accepts it, and
each refusal is a rule this book spends a chapter on.

```bash
python3 -m pytest tests/reading_a_model/test_problem_1_ceiling.py
```

**1.2 — The other kind of terabyte.**
Re-declare every capacity node in binary units and change nothing else. The outputs must come out
smaller by exactly the right ratio, and the model must still typecheck. If you find yourself
editing a value to compensate, stop.

```bash
python3 -m pytest tests/reading_a_model/test_problem_2_binary_units.py
```

**1.3 — Turn a sizing model into a cost model.**
Remove what makes the storage model a sizing model, keep it working, and then write one sentence
saying what the result can no longer tell anybody. If you cannot name it, you removed something
that was doing no work — and the original model should not have had it.

```bash
python3 -m pytest tests/reading_a_model/test_problem_3_classification.py
```

## Where to go next

[Appendix A](#appendix-a-dsl-reference) is the reference: every field of every node kind, and
every rule the build applies.

[ch02](#what-a-workload-is) is the other half of a model — not the machinery, but the question of
which quantities are worth putting in one.
