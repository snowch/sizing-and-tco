# Model builder: design

A tool that lets a reader build a model of their own system, guided by the book's questions, and
write the same YAML the book's models use. This is the design; nothing here is built yet.

The clickable mock-up is [`model-builder-mockup.html`](model-builder-mockup.html) beside this
file: open it in a browser. It is the reference for the flow described below. Its engine is a JavaScript copy of the
toolkit's rules and its measured results are invented; both are listed under
[What the mock-up fakes](#what-the-mock-up-fakes).

## Why

The book teaches bottom-up, because each idea needs the one before it: you cannot grow a figure
until you know what a rate is. Building a model works the other way. A reader with a question of
their own does not know where to start, and a blank YAML file does not tell them.

The builder turns the book's distinctions into questions asked at the moment they matter. Every
distinction is already a field in the DSL and a rule in `scripts/verify-models.py`, so the
builder's questions exist already, as validation:

| Question the builder asks | Where the book teaches it | What the DSL enforces |
|---|---|---|
| Is it a rate, a level, a length of time or a ratio? | ch02 | `unit`, checked dimensionally |
| Who decides it? | ch02 | `decided: outside \| you \| definition` |
| Where did it come from? | ch03 | `provenance` kind and source; a `fact` cites something |
| Is it measured on one implementation, with an error? | ch09 | `measured` node pointing at a stamped result |
| Is there a limit, and what margin? | ch06, ch11 | `ceiling` with `headroom` and `because` |
| How sure are you? | ch04, ch13 | a `distribution` named in the source |

## Principles

1. **The output is the book's YAML.** The builder is a front end to the DSL, not a new format. A
   reader can graduate to editing the file, and the viewer, the checks and the problem tests all
   read what they built.
2. **The book's rules, proven equal.** The builder's rules engine is JavaScript, for speed, and
   is held to the book's by a conformance suite the book publishes: it may not release while any
   case differs. See [Repository](#repository).
3. **No default values.** Invariant 3 applies to the builder as it does to the book. An input with
   no number is *not yet measured* and so is everything downstream. The builder may preset the
   *kind* of a node (from a pattern or the path); it never presets a number.
4. **Ask, do not answer.** Each screen is one question, with the chapter that teaches it. A reader
   who cannot answer "who decides this?" learns more from being stuck on it than from a default.
5. **The build's refusals are the wizard's gates.** The wizard does not move on from an answer the
   build would refuse: a shaped input whose source does not name the shape, a ceiling with no
   margin, a fact that cites nothing.

## The flow: answer first

Top-down, from the answer back to the inputs. This is the order that builds a sound model, and
it differs from the book's teaching order on purpose.

1. **The answer.** What are you being asked for: hosts, storage, cost, or another quantity. Its
   name, label and unit. It becomes the model's first output.
2. **The decision it feeds.** Who acts on the number and what they do with it. It sets how
   precise the answer needs to be, and it is what the finished model is checked against (ch01,
   ch21).
3. **The horizon.** When the answer is for. It is a decision (`decided: you`), it fixes what the
   answer means, and every growth figure hangs off it. A model for today skips it explicitly.
4. **Work back.** Every node not yet defined is shown as *to define*. For each, one question:
   - **Given**: a number stated, estimated or decided. The input questions follow: unit, who
     decides, source, how sure. The branch ends here.
   - **Measured**: points at a stamped result in `bench/results/`. Makes the model conditional.
   - **Worked out**: a formula. Any name in it that does not exist yet becomes a new node to
     define. The next-step bar always points at the next one, breadth first from the outputs.
5. **Refine**, once nothing is left to define. Optional and skippable, in the order that pays:
   - where each number came from (ch03), grouped by claim
   - where it stops working: a ceiling and its margin (ch05 – ch08, ch11)
   - ranges for the inputs outside your control (ch04, ch13)
   - which input to measure first (ch19)
   - a second case, as a scenario (ch21, ch22)

### Nodes to define, and unit inference

A formula can name nodes that do not exist yet. Each becomes a *to define* node, and where the
formula fixes its unit, the builder infers it:

- added to, subtracted from, or compared in `min`/`max` with something of known unit: the same
  unit;
- used as an exponent, or inside `log`/`exp`: a pure number;
- the base of a power that is not a whole number: a pure number (growth, not terabytes);
- when exactly one unknown is left in a product or quotient, solved against the unit the node
  declares.

A node whose unit the formula does not fix asks for one when it is defined. A worked-out node
waiting on nodes to define shows *waits on N to define*, never *not yet measured*: that phrase is
reserved for a missing measurement.

### Patterns

When a worked-out node needs a formula, the builder offers patterns from the book's own models,
filtered to those that produce the node's unit. Names are the book's; any that do not exist yet
become nodes to define. From `models/web_service/model.yaml`:

| Pattern | Formula | Where |
|---|---|---|
| Needed ÷ one host's share below a margin, rounded up | `ceil(busy_cores / (cores_per_host * (1 - queueing_margin)))` | ch09, ch11 |
| The resource that binds | `max(hosts_for_requests, hosts_for_memory, hosts_for_storage)` | ch10 |
| Today's figure grown to the horizon | `x_t0 * annual_growth ** horizon_periods` | ch02, ch04 |
| A length of time as a number of years | `horizon / one_year` | ch02 |
| Work arriving × what each piece costs | `peak_request_rate * service_demand` | ch05, ch09 |
| Held × copies ÷ compression | `stored_data * replication_factor / record_compression` | ch09 |
| Up front plus running, over the horizon | `hosts * host_price + hosts * running_cost_per_host_year * horizon` | ch15, ch18 |

Formulas are limited to the DSL's functions (`sizing/expr.py`): `min`, `max`, `ceil`, `floor`,
`sqrt`, `log`, `exp`.

### The hosts question

When the answer is a count of machines, the builder asks one more question before offering a
pattern: **one kind of host, several roles, or several generations in one role?**

- **One kind doing several jobs** (the web service model): per-host specification inputs as
  decisions, one chain per resource, and the fleet is the `max` of the chains (ch10). The sum is
  wrong: the same hosts are doing three things.
- **Several roles** (the observability model: collectors, store nodes, query nodes): one pool per
  role, each sized by its own `max`, and the fleet is the *sum* of the pools, because they are
  different machines.
- **Several generations in one role**: see [Mixed generations](#mixed-generations). Needs the
  book to cover it first.

A different configuration of the same role is not modelled side by side. It is a scenario that
overrides the per-host inputs, compared in full (ch22, `scenarios/challenger.yaml`).

## Mixed generations

The book does not yet cover a single pool of mixed hardware: last year's hosts and this year's,
doing the same job. It is on the list to add to the book (ch10, ch11, ch18, ch22), and the
builder should follow the book rather than lead it. The outline:

- the question becomes how many *new* hosts to buy, given the ones already owned:
  `ceil((max(need, existing) - existing) / per_new_host)` per chain, with the need already
  divided by one minus the margin, then `max`. Not `max(0, need - existing)`: the book's operand
  rule refuses a pure zero meeting a unit, which the builder found (`edge/max-with-zero`). Written
  this way in `models/mixed_pool/model.yaml`;
- **the balancing policy decides whether capacity adds.** Weighted by capacity, it sums.
  Round-robin sends every host the same share, so the weakest reaches the knee first and the
  pool behaves like `all_hosts * min(old, new)`. Both are expressible; a ceiling checks the
  policy actually run. Needs a primary source in `references.bib` before it is written;
- each chain sums each generation's share of that resource, and the binding chain can differ
  from either generation's alone;
- an indivisible item (a shard) must fit on the smallest host: a per-host ceiling;
- old hosts retire inside the horizon, so the check is at the worst point, not only the end;
- N+1 headroom covers the largest host, not the average (ch11);
- the old hosts' purchase is sunk and stays out of the TCO; their running costs do not (ch15,
  ch18). Keep versus replace is two scenarios compared (ch22).

## What the builder shows

- **The answer, worked back**: the model as a tree from each output, with *to define* marked,
  and anything feeding no output listed apart (the build fails it).
- **Next step**: one action, with its reason and chapter. A failing build check comes first once
  nothing is left to define.
- **The graph**: the viewer's colours; a dashed outline for a node to define or not yet measured;
  a bar for an input you decide.
- **Answers**: each output at the book's values, and a range once inputs have shapes.
- **Measure first**: each shaped input moved from the low end of its range to the high end, one at
  a time, ranked by how far the first output moves (ch19). Notes that one at a time cannot show two
  inputs that matter only together (ch19, ch20).
- **Build checks**: the rules of `verify-models.py`, live.
- **The file**: the YAML, with a copy button, and each scenario as its own file.
- **The classification**: definitional or conditional, worked out from the node kinds (ch01), never
  set by hand.

## Repository

A separate repository. The builder is a product with its own release cycle, its own tests
(interaction flows, not prose invariants) and its own audience; the book's CI stays about the
book.

### JavaScript, held to the book by a conformance suite

The builder is JavaScript throughout, rules engine included. Its value is feedback on every
keystroke: a formula's unit as it is typed, the tree redrawn as a node is defined. Running the
book's Python in the browser (Pyodide) costs about ten megabytes and seconds before the first
response, which is the wrong trade for a guided tool.

The risk of a second implementation is drift: a builder whose rules differ from the book's writes
files the book refuses. The book already manages this once. `sizing/viewer/evaluate.js` is a
JavaScript evaluator, and `tests/test_viewer.py` holds it to values Python computed, for every
node of every model. The builder does the same at a larger scale:

1. **The book publishes a conformance suite.** A set of model files, each with what the book's
   toolkit says about it: loads or is refused and why, which `verify-models.py` rule fails, every
   node's unit and value at the point estimate, and the classification. Generated by the book's
   CI from the Python toolkit, so it cannot disagree with it, and released with each format
   version. It includes both reference models and a case for every refusal the build knows.
2. **The builder may not release while any case differs.** Its CI runs its engine over the
   suite. A rule the book adds arrives as failing cases, not as a surprise to a reader.
3. **Sampling is checked by distribution, not by draw.** Ranges from the builder's sampler must
   land within a stated tolerance of the book's for the same file and seed. A JavaScript
   Iman–Conover implementation is this repository's own code, citing the method, as the book's is.

Pyodide stays available as an option, not the engine: a "check with the book's own toolkit" action
for an authoritative verdict on a finished file, as the viewer's resample already does.

The alternative, considered and not recommended: Pyodide as the engine, with the book's `sizing`
wheel pinned (`sizing.playground.toolkit.wheels` already builds it). One source of truth with no
suite to maintain, at the cost of the download and the latency above.

### A format version

The model file gains a top-level `dsl: <version>` line, which the loader checks. A model then says
which rules it was written against, the conformance suite is released per version, and the builder
refuses a file newer or older than the suite it passed. This is a change to `sizing/dsl.py`, so
every stamped result is regenerated with it.

### The builder's own tests

Besides the suite: every model it writes, for a set of scripted flows, loads with the book's
toolkit and passes `verify-models.py`. The book's two reference models, loaded into the builder
and written back out, are unchanged.

## What the mock-up fakes

The real builder must not ship any of these:

- **The measured results are invented.** Its compression ratio, bytes per line and their errors
  are placeholders for the demonstration. The real list is read from `bench/results/`, with the
  implementation each was measured on.
- **The rules are an unchecked JavaScript copy.** Units, formulas, functions and the build checks
  are reimplemented and close to the toolkit, but nothing holds them to it. The real builder's
  engine passes the conformance suite.
- **Inputs that move together are recorded but ignored** when the range is drawn. The real one
  samples with the toolkit's Iman–Conover method, as the book does (ch14).
- **Ranges use a small sample and its own random generator.** The real one uses the toolkit's
  sampler and a pinned seed, so its ranges match the book's for the same file.

## Open questions

- Where does a reader's model live: in the browser only, or saved to a file they choose? The
  static-site constraint argues for browser storage plus copy and open.
- Does the builder host the book's viewer for the finished model, or link to a build of it?
- How much of the refine step should run before the tree is complete? Measuring first on a half
  model is misleading, which is why the mock-up waits.
- Problem 2.5 and the other problems about the reader's own system have no oracle. Should the
  book link to the builder from them?
