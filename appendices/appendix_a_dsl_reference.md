---
title: "The DSL, in full"
short_title: "Appendix A · The DSL"
---

(appendix-a-dsl-reference)=
# Appendix A · The DSL, in full

:::{note} What this holds
:class: dropdown

| | |
|---|---|
| **Purpose** | Every node kind, every field, every distribution, and what the build checks |
| **Source** | `sizing/dsl.py`, `sizing/expr.py`, `sizing/evaluate.py` |
:::

A model is a YAML file. It declares named quantities, each with a unit, and how they depend on
each other. There is no evaluation order in the file, no cells, no hidden state, and no way to
write a number in one place and have it mean something else in another.

The whole language is on this page. It is small on purpose: [ch01](#reading-a-model) argues that a
model somebody has to learn a system to read is a model nobody reads.

## The file

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: model: storage_cluster
:end-before: nodes:
```

Four keys before the nodes begin. `model` is the identifier, and it is the directory name.
`currency` is declared rather than assumed, so that a model mixing two of them fails to typecheck
instead of quietly adding them. `description` is prose, and it is where a model says what it is
*for* — the one thing a reader cannot reconstruct from the graph.

## The four node kinds

```{include} ../chapters/_generated/appendix-a-dsl-reference-kinds.md
```

The last row is the distinction the book is built on, and it is decided by the file rather than
by its author's opinion of it. A model containing a `measured` node or a `ceiling` node **is** a
sizing model: it has an empirical constant that belongs to one stack at one version, or a limit
past which its arithmetic stops describing anything, and in either case sampling the inputs is not
sufficient on its own. A model with neither is a cost model, and there it is.

Here are the kinds, as the loader defines them:

```{literalinclude} ../sizing/dsl.py
:language: python
:start-at: class Node:
:end-before: KINDS: dict[str, type[Node]]
```

### `input` — a number somebody chose

A value, or a distribution, or both. Plus a provenance kind and a non-empty source, which is the
one field the build will not let you skip:

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: annual_growth:
:end-before: horizon:
```

`range` is what the interactive page turns into a slider. It is a plausible span for a reader to
explore, not a claim about the distribution — the distribution is the claim about the
distribution.

### `derived` — arithmetic

A formula over other nodes, and a unit that has to agree with what the formula produces:

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: raw_per_usable:
:end-before: raw_capacity:
```

The formula language is deliberately not Python. It is parsed with Python's own parser and then
walked, and only these functions survive the walk:

```{literalinclude} ../sizing/expr.py
:language: python
:start-at: FUNCTIONS: dict[str, Any] = {
:end-before: class FormulaError
```

Arithmetic is `+ - * / **` and unary minus. There is no name lookup other than other nodes, no
attribute access, no calls to anything not in that dictionary. A model file cannot do anything, so
running a stranger's model is reading their arithmetic rather than executing their code.

### `measured` — a constant somebody measured

Not a value. A reference to a stamped result:

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: object_compression:
:end-before: replication_factor:
```

The number, its standard error and the implementation it belongs to all come from
`bench/results/`, which is what makes a measured constant different from an input that happens to
have been measured once. If the result does not exist, the node has no value and neither does
anything downstream of it — the state propagates by itself and the figures say *not yet measured*
rather than showing an estimate ([ch03](#where-the-numbers-come-from)).

### `ceiling` — where the arithmetic stops working

A quantity, a limit, a margin, and a reason:

```{literalinclude} ../models/service_tier/model.yaml
:language: yaml
:start-at: queueing_headroom:
:end-before: # -- what more machines buy
```

`of`, `limit` and `headroom` are all expressions rather than numbers, and that is deliberate. A
margin a sizing formula uses and a margin a ceiling audits against should be able to be *the same
node*. Writing the same figure in both places is how a design comes to be sized for one headroom
and checked against another, some months after anybody remembers there were two.

`because` is required and `headroom` is required. A ceiling with a limit and no margin is not a
sizing rule, it is a comparison, and the build refuses it
([ch11](#headroom-and-failure-domains)).

## Provenance

```{literalinclude} ../sizing/dsl.py
:language: python
:start-at: #: How much a modeller is claiming when they write a number down.
:end-before: PROVENANCE_MEANING
```

Three kinds, one required source string, and the gap between the first two is the one that costs
money. Every figure in the book colours them differently and none of them is ever silently
promoted.

## Distributions

An input may declare exactly one shape. These are the four, and adding a fifth is a percentile
function and a line:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: SHAPES: dict[str, Callable[..., np.ndarray]] = {
:end-before: def sample(
```

[Appendix C](#appendix-c-distributions) is one page each on what they assume and how they lie.

## Outputs

Which nodes are answers. Everything else in the graph is working:

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: outputs:
:end-before: correlations:
```

The list decides what the tables report and what the tornado is drawn against. It is not a
restriction — every node keeps its value and its distribution, and the interactive page will show
you any of them. It is an editorial judgement about which handful of numbers somebody is going to
be asked about.

## Correlations

A model may declare that two inputs move together, with a reason:

```{literalinclude} ../models/storage_cluster/model.yaml
:language: yaml
:start-at: correlations:
```

The reason is not optional. A coefficient with no reason attached is a number somebody will copy
into the next model without knowing what it was for
([ch14](#correlation-and-convergence)).

## Scenarios

A scenario is a small file beside the model. It overrides inputs, names why, and pins the sample
count and the seed so the run can be reproduced exactly:

```{literalinclude} ../models/storage_cluster/scenarios/sized_for_growth.yaml
:language: yaml
```

Scenarios are how two designs get compared without either of them being edited into the other
([ch21](#a-tco-for-finance)).

## What the build checks

`scripts/verify-models.py` runs on every model on every push, and fails on any of:

- **A unit that does not follow.** Every formula is evaluated in units as well as in numbers. A
  declared unit that disagrees with what the formula produces is an error, and a declared unit
  that agrees dimensionally but differs by a factor — dollars per TB per *year* against per
  *month* — is recorded as a conversion and applied, not waved through
  ([Appendix D](#appendix-d-units)).
- **An input with no provenance, or a `fact` that cites nothing.**
- **An input that is sampled and does not name its shape in that source.** The distribution is a
  claim about what can happen, and it is the claim to argue with first
  ([Appendix C](#appendix-c-distributions)).
- **A ceiling with no headroom, or no reason.**
- **A measured node whose result reports no uncertainty**, which is a claim to have measured
  something exactly.
- **A cycle**, or a node that depends on something that does not exist.
- **A measured constant with no ceiling anywhere in the model.** A model with empirical inputs
  and no declared limit is claiming that nothing in it changes regime. That may be true, and it
  should be stated by declaring the ceiling rather than by leaving it out. The classification
  itself is derived from the file and cannot be asserted by hand.
- **A node that feeds no output**, which is either a leftover or an output somebody forgot to
  declare — and a model that declares no outputs at all, since nothing in it can then be checked.
- **A scenario overriding a node that does not exist, or a derived one.** Overriding a derived
  node would be editing the arithmetic while claiming to change an assumption.

## The graph

```{image} ../chapters/_figures/appendix-a-dsl-reference-graph.svg
:alt: The smallest model in the book as a dependency graph, coloured by node kind
:width: 100%
```

The service tier model, which is the smallest one in the book: nine inputs, three ceilings and
the arithmetic between them. It has no measured constant, which is why the ceilings alone make it
a sizing model — [Appendix F](#appendix-f-observability-model) is the one with all four kinds in
it. Reading right to left from any answer gives exactly the quantities it rests on; reading left
to right shows how few inputs most of the graph is downstream of.

## Running it

```bash
python3 -m bench.run_models                  # evaluate, sample and stamp every model
python3 -m bench.run_models --model NAME     # just one
python3 scripts/verify-models.py             # units, provenance, ceilings, classification
python3 scripts/build-viewers.py             # the interactive pages
```
