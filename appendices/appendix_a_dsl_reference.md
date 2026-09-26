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
| **Source** | `sizing/dsl.py`, `sizing/expr.py`, `sizing/evaluate.py`, `sizing/mc.py`, `scripts/verify-models.py` |
:::

A model is a YAML file. It declares named quantities, each with a unit, and how they depend on
each other. There is no evaluation order in the file, no cells, no hidden state, and no way to
write a number in one place and have it mean something else in another.

Every key in a model file or scenario file is on this page, along with what happens when you leave
it out; so is every rule the build applies. The unit names are in [Appendix D](#appendix-d-units).
The language is small on purpose: a model somebody has to learn a system to read is a model nobody
reads.

## The file

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: model: web_service
:end-before: nodes:
```

The quoted lines are the top of the running example's file. A model file has seven top-level keys.

| Key | What it holds | If you leave it out |
|---|---|---|
| `model` | the model's identifier; its results are named `<model>-<scenario>` | the file does not load |
| `title` | the name a reader sees | the model's identifier |
| `description` | prose saying what the model is *for*, the one thing the graph cannot show | nothing is shown |
| `currency` | a label for the money | `USD` |
| `nodes` | every quantity in the model, by name | the file does not load |
| `outputs` | which nodes are answers | the file loads but the build refuses it |
| `correlations` | pairs of inputs that move together | every uncertain input is independent |

`currency` is only a label. No check reads it; the loader writes `USD` when you leave it out. `USD`
is the only currency unit the toolkit defines, so a model whose units are in any other currency does
not load.

By convention, the identifier is also the name of its folder under `models/`. Nothing checks that
the two match. The nodes follow these keys, under `nodes:`.

## The four node kinds

```{include} ../chapters/_generated/appendix-a-dsl-reference-kinds.md
```

The table counts each kind of node in the running example's finished model, which
[Appendix E](#appendix-e-web-service-model) shows in full. Its last row classifies that model. The
file decides whether a model is conditional or definitional, not its author's opinion. A model
containing a `measured` node or a `ceiling` node **is** a conditional model: it has an empirical
constant at one stack and version, or a limit past which its arithmetic stops describing anything.
In either case sampling the inputs is not sufficient on its own; a model with neither is
definitional.

Every node is a mapping under its name, and holds these keys.

| Key | Kinds | If you leave it out |
|---|---|---|
| `kind` | every node | the file does not load |
| `unit` | every node | the file does not load |
| `label` | every node | the name is shown with underscores as spaces |
| `note` | every node | nothing; shown in node details if present |
| `decided` | `input` | the build refuses it |
| `provenance` (`kind`, `source`) | `input` | the build refuses it |
| `value` | `input` | the median of the distribution |
| `distribution` | `input` | one number, not randomised |
| `range` | `input` | no slider |
| `formula` | `derived` | the file does not load |
| `result` | `measured` | the file does not load |
| `of` | `ceiling` | the file does not load |
| `limit` | `ceiling` | the file does not load |
| `headroom` | `ceiling` | the build refuses it |
| `because` | `ceiling` | the build refuses it |

`kind` is one of `input`, `derived`, `measured`, or `ceiling`; `unit` must be known to the build or
the file does not load (use `dimensionless` for a pure number). [Appendix D](#appendix-d-units)
lists the unit names. An input needs a `value`, `distribution`, or both; with neither the file loads
but the build fails when evaluating scenarios.

The loader reads these keys and no others; any other key in a node is ignored without warning. A
misspelt key is lost silently: `lable:` leaves the node with no label, `slider:` written for
`range:` leaves the input with no slider. Both files load and pass the build.

### `input` — a number the model is given

An input carries a `value`, a `distribution`, or both. If you give both, the `value` is the single
number the tables and interactive page use to start, and the distribution is what the sampler draws
from. With only a distribution, the single number is its median.

A scenario can override the value or the distribution; an override wins. Every input must also have
a `decided` line, saying who settles the number:

- `outside`: outside your control, whether or not it has been given a shape yet; the busy hour, the
  records held, a price
- `you`: a choice you make and can change; the fleet, the horizon, a headroom margin
- `definition`: an identity nobody chooses and the world does not vary; a year in seconds, one host,
  one request

The build refuses an input without a `decided` line or with any other value. An input decided by
`you` is marked with a bar on its left edge in the graph and interactive page; that is the legend's
"you decide". The quoted input, annual growth, is `outside`: it has a distribution, and nobody in
the model chose it. An input also has a provenance kind and a source the build will not let you
leave empty:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: annual_growth:
:end-before: horizon:
```

`range` is what the interactive page turns into a slider. It is a plausible span for a reader to
explore, not a claim about the distribution — the distribution is the claim about the
distribution.

### `derived` — arithmetic

A formula over other nodes, and a unit that has to agree with what the formula produces:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: peak_request_rate:
:end-before: stored_data:
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

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: record_compression:
:end-before: replication_factor:
```

The number, its standard error and the implementation it belongs to all come from
`bench/results/`. That is what separates a measured constant from an input that happens to have
been measured once. If the result does not exist, the node has no value and neither does anything
downstream of it — the state propagates by itself and the figures say *not yet measured* rather
than showing an estimate ([ch03](#where-the-numbers-come-from)).

### `ceiling` — where the arithmetic stops working

A quantity, a limit, a margin, and a reason:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: queueing_headroom:
:end-before: # -- what more hosts buy
```

`of` is the quantity the ceiling watches, and its value is what `of` works out to (checked like a
formula). `limit` is where arithmetic stops; it must match the ceiling's `unit`. `headroom` is the
margin below the limit as a fraction of it; it must be a plain number. In the quoted ceiling, `of`
is fleet utilisation at busy hour, `limit` is full utilisation, and `headroom` is `queueing_margin`.
Every ceiling in the book uses this pattern with plain-number limits, so it suits only
`dimensionless` units. The build refuses a plain-number limit in any other unit, `TB` included; any
other unit takes its limit from a node.

The ceiling allows the limit less the headroom's share of it:

```{literalinclude} ../sizing/evaluate.py
:language: python
:start-at: allowed = limit * (1.0 - headroom)
:end-before: entry = {
```

The headroom is a share, not an amount subtracted; the larger it is, the smaller the allowed portion
of the limit.

Each ceiling gets one of three verdicts:

- `ok`: at or below the allowed level
- `inside headroom`: above the allowed level but not above the limit
- `over`: above the limit

When the inputs are drawn at random, the report shows the share of futures above the allowed level
and above the limit. [ch11](#headroom-and-failure-domains) argues that a design inside its headroom
has not failed; it has spent the reserve it kept for one.

`of`, `limit`, and `headroom` are all expressions rather than numbers, so a sizing formula's margin
and a ceiling's margin can be *the same node*. Writing the same figure in both places is how a
design gets sized for one headroom and checked against another, some months after anybody remembers
there were two. `because` and `headroom` are both required. A ceiling with a limit and no margin is
not a sizing rule but a comparison, and the build refuses it; an empty `because` counts as none.

## Provenance

```{literalinclude} ../sizing/dsl.py
:language: python
:start-at: #: How much a modeller is claiming when they write a number down.
:end-before: PROVENANCE_MEANING
```

Every input has a `provenance` mapping with two keys: `kind`, one of the three shown above, and
`source`, text saying where the number came from. The build refuses an input with an invalid kind or
an empty source. For a sampled input, the source must also name the distribution shape:
`triangular`, `lognormal`, `uniform`, or `normal`.

A `fact` has to cite something. The build counts a source as citing when it contains one of these
strings:

```{literalinclude} ../scripts/verify-models.py
:language: python
:start-at: #: A `fact` has to point at something.
:end-before: def _shown
```

The check only looks for the string, so a source can pass and still point at nothing; a reviewer
reading the source does the rest of the check. A `fact` whose source is "the vendor's datasheet" is
refused because it names a document but contains none of these strings. As a `vendor_claim`, the
same source passes, provided the input is not sampled or the source also names its shape.

## Distributions

An input's `distribution` names exactly one shape, and under it the keys that shape takes. The
quoted input uses this pattern: a `lognormal` with its two keys. The table lists the four shapes and
their keys, read from the sampler's own code so it cannot drift from what a file may write:

```{literalinclude} ../sizing/mc.py
:language: python
:start-at: SHAPES: dict[str, Callable[..., np.ndarray]] = {
:end-before: def sample(
```

A distribution naming no shape, two shapes, or keys its shape does not take cannot be worked out;
the build fails when evaluating scenarios. The same applies to out-of-order values, such as a
`likely` outside `minimum` and `maximum`, or a `p10` above the `p90`. Adding a fifth shape requires
a percentile function and a line in `SHAPES` in `sizing/mc.py`.

[Appendix C](#appendix-c-distributions) is one page each on what they assume and how they lie.

## Outputs

Which nodes are answers. Everything else in the graph is working:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: outputs:
:end-before: correlations:
```

The list decides what the tables report and what the tornado is drawn against. It is not a
restriction — every node keeps its value and its distribution, and the interactive page will show
you any of them. It is an editorial judgement about which handful of numbers somebody is going to
be asked about.

## Correlations

A model may declare that two quantities move together. Each entry has four keys: `a` and `b`, the
two nodes; `rho`, how strongly they move together; and `because`, the reason:

```{literalinclude} ../models/web_service/model.yaml
:language: yaml
:start-at: correlations:
```

% number-ok: the range a rank correlation is defined on
`rho` is a rank correlation, between −1 and 1; [ch14](#correlation-and-convergence) explains why
ranks rather than values. A value outside that range on a used pair stops the model from being
worked out, as do pairs that cannot all hold at once. `a` and `b` must name nodes that are drawn at
random: inputs with a distribution, or measured constants with a standard error.

A pair naming anything else is dropped without a message: a misspelt name, an input with no
distribution, or an input a scenario has pinned. The model still builds and runs as though the pair
were not there; the misspelling is the case to watch for. The build refuses a correlation whose
`because` is missing or empty; it is part of the rule that every input says where it came from. A
coefficient with no reason attached is a number somebody will copy into the next model without
knowing what it was for.

## Scenarios

A scenario is a small file in the `scenarios/` folder beside the model file. The build evaluates
every file in that folder. A scenario sets some of the model's numbers, says why, and fixes how many
futures are drawn and the seed so the run can be repeated exactly. The one quoted here buys the
fleet the high-growth case needs:

```{literalinclude} ../models/web_service/scenarios/sized_for_growth.yaml
:language: yaml
```

| Key | What it holds | If you leave it out |
|---|---|---|
| `scenario` | the scenario's name | the file does not load |
| `title` | the name a reader sees | the scenario's name |
| `because` | why this scenario exists | nothing |
| `overrides` | nodes and their values in each node's unit | the model runs on its original values |
| `samples` | how many futures to draw | the loader uses a default, which the result records |
| `seed` | where the random draws start | the loader uses a default, which the result records |

An override may name an input or a measured constant. An overridden input is not drawn at random in
that scenario; it is pinned to the one number, and any correlation naming it is dropped. The build
refuses an override naming a non-existent node or a derived node, which would amount to editing the
arithmetic while claiming to change an assumption. An override on a ceiling is accepted but changes
nothing; a ceiling's value is always what its `of` works out to. To move a ceiling, override the
inputs that its `of`, `limit`, or `headroom` read.

[ch21](#a-tco-for-finance) reads this scenario beside the reference one to show what the extra hosts
buy; [ch22](#comparing-two-tcos) compares two designs each described by a scenario file without
editing either into the other.

## What the build checks

A model meets two checks. The loader reads the file into a graph and stops at the first thing it
cannot read. Then `scripts/verify-models.py` runs on every model on every push, reporting every
problem it finds at once rather than stopping at the first (CI runs it: `scripts/ci-check.sh`).

### When the file loads

The loader refuses these:

- **A missing key the file needs**: `model` or `nodes` at the top; `kind` or `unit` on any node;
  `formula` on a derived node, `result` on a measured one, `of` or `limit` on a ceiling.
- **A `kind` that is not one of the four, or a unit that is blank or that the build does not know.**
- **A formula that is not arithmetic.** Anything but numbers, other nodes, `+ - * / **`, unary minus
  and the functions quoted under `derived` is refused, so a model file cannot run code.
- **A name that is not a node**: a formula that refers to one, or an output that lists one.
- **A cycle.**

### When the verifier runs

The build refuses these:

- **A unit that does not follow.** Every formula is evaluated in units as well as in numbers. A
  declared unit that disagrees with what the formula produces is an error. One that agrees
  dimensionally but differs by a factor, dollars per TB per *year* against per *month*, is converted
  and applied, not waved through ([Appendix D](#appendix-d-units)). A plain number is not an amount
  of data, so a `TB` node or limit whose formula gives one is refused.
- **Quantities in different units meeting in a sum, a difference, a `min` or a `max`.** The
  conversion is applied once, to the whole formula's result, so it cannot fix two operands that were
  never in one unit. `a + b` with `a` in `TB` and `b` in `TiB` is refused. Declare them in one unit,
  or convert one in a node of its own.
- **A `ceil` or `floor` over a number not yet in the node's unit.** It would round the wrong number,
  since the conversion comes after.
- **A ceiling whose `limit` is a different kind of quantity from its `unit`, or whose `headroom` is
  not a plain number.**
- **An input with no `decided` line**, or one that is not `you`, `outside` or `definition`.
- **An input with no provenance, a kind that is not one of the three, an empty source, a correlation
  with no `because`, or a `fact` that cites nothing.** *Provenance*, above, says what counts as
  citing.
- **An input that is sampled and does not name its shape in its source.** The distribution is a
  claim about what can happen, and it is the claim to argue with first
  ([Appendix C](#appendix-c-distributions)).
- **A measured node that names no result; whose result has no value, or reports no uncertainty; or
  whose result is in a different unit from the node.** Reporting no uncertainty is a claim to have
  measured something exactly. A result that does not exist yet is not refused: the node is *not yet
  measured*, and so is everything downstream of it.
- **A ceiling with no headroom, or no reason.** An empty reason counts as none.
- **A node that feeds no output**, which is either a leftover or an output nobody declared. Also a
  model that declares no outputs at all, since nothing in it can then be checked.
- **A measured constant with no ceiling anywhere in the model.** A model with empirical inputs and
  no declared limit is claiming that nothing in it changes regime. That may be true; say it by
  declaring the ceiling, not by leaving one out.
- **A scenario that overrides a node the model does not have, or a derived node.** *Scenarios*,
  above, gives the reason.
- **A scenario that cannot be worked out.** The verifier evaluates the model under every scenario,
  and this is where problems surface: an input with neither a value nor a distribution, a
  distribution naming no shape or two, parameters out of order, and correlations that cannot hold.
- **A stamped model result older than the model.** Every result under `bench/results/` from a model
  run carries a fingerprint of the code and the model file that produced it. Edit either, and the
  build refuses the old result until you re-run `python3 -m bench.run_models`.

### What nothing checks

The build accepts all of these without a word:

- **A key the loader does not know.** It is ignored. *The four node kinds*, above, explains where
  this matters.
- **`currency`.** Only a label. *The file*, above, says more.
- **Whether a correlation's two names are drawn at random.** A pair naming anything else is dropped.
  *Correlations*, above, has the details.
- **A scenario's `because`, and an override on a ceiling**, which changes nothing. *Scenarios*,
  above, explains both.
- **That `model` matches the model's folder name.**

## The graph

```{image} ../chapters/_figures/appendix-a-dsl-reference-graph.svg
:alt: The running example as a graph, with boxes coloured by node kind and arrows showing dependencies
:width: 100%
```

The graph shows the running example as [ch02](#what-a-workload-is) leaves it: inputs and derived
nodes, and nothing else. It has no ceiling and no measured constant, so it is a definitional model;
[ch06](#queueing-and-the-knee) is where it stops being one. Reading right to left from any answer
gives exactly the quantities it rests on, and reading left to right shows how few inputs most of the
graph is downstream of. Both of the book's finished models have all four kinds in them:
[Appendix E](#appendix-e-web-service-model), the running example, and
[Appendix F](#appendix-f-observability-model), the second model.

## Running it

```bash
python3 -m bench.run_models                  # evaluate, sample and stamp every model
python3 -m bench.run_models --model NAME     # just one
python3 scripts/verify-models.py             # units, provenance, ceilings, classification
python3 scripts/build-viewers.py             # the interactive pages
```
