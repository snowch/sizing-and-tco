---
title: "Where the numbers come from"
short_title: "ch03 Where the numbers come from"
---

(where-the-numbers-come-from)=
# ch03 · Where the numbers come from

:::{note}
**Draft.** Content drafted. This chapter is undergoing final review and polish.
:::

## The question

What is the difference between a number you measured, a number you were told, and a number you
decided?

Once they are all cells in the same column, none. That is the problem.

## The material

### Three claims, wearing the same clothes

Every input in this book declares which of three things it is.

**`fact`**: traceable to something: a stamped measurement, an invoice, or a published
specification. A stamped measurement is a result file in `bench/results/`. It records the figure,
the unit, what produced it (the body of data and the software, or the machine), and a fingerprint
of the code that created it. The build refuses a `fact` whose source cites nothing. An assumption
dressed as a `fact` is worse than one labelled as an assumption, because the label hides the doubt
a reviewer would otherwise challenge.

**`vendor_claim`**: stated by the vendor selling it. Often true, and never checked here. It carries
its mark in the tables on this page — the ◐ symbol — and when you click a node in a model, its
Provenance line names it a vendor claim. It is never quietly promoted to a `fact`. Once a quoted
throughput becomes "the throughput" in your head, the model holds a fact it never earned.

**`assumption`**: a decision this model makes. Naming it as one is what lets a reviewer argue with
it. An assumption nobody can find is not a weaker claim than a measurement. It is a stronger one,
because nothing can dislodge it.

### The first number somebody else supplied

Every input in [ch02](#what-a-workload-is)'s file was either outside your control (how many
requests arrive, how much is held, how fast both grow) or decided by you (how long the fleet has to
last). The next input, `ram_per_host`, is how much memory each host carries. You choose which
memory modules to fit, so its file says `decided: you`. What the number means is not yours to
decide: it comes off the vendor's spec sheet, so its provenance is `vendor_claim`. These two lines
answer different questions. `decided:` records who chooses the value; `provenance` records who
stands behind the number and how much they are claiming. The form that takes is:

```{literalinclude} ../models/web_service/stages/06-provenance/model.yaml
:language: yaml
:start-at: ram_per_host:
:end-before: os_reserve:
```

The source has two clauses. The second, *the sheet says gigabytes and means gibibytes*, names the
gap between what a spec sheet writes and what it counts. [Appendix D](#appendix-d-units) covers
that decimal-against-binary gap. There is a second gap: the operating system keeps some memory for
itself before the service sees any. The next input, `os_reserve`, carries it, and Appendix D does
not cover this one. Writing both down is the discipline: the claim is recorded as a claim, and what
is doubtful about it is recorded beside it.

`os_reserve` is an `assumption`: one number for the share of memory the kernel, the agents and the
page cache floor keep. It has not been measured on these hosts. With `os_reserve`, the model
reaches its first node about hardware rather than data: `ram_for_service`, the memory the service
can use per host, which is `ram_per_host` times one minus `os_reserve`. The input is:

```{literalinclude} ../models/web_service/stages/06-provenance/model.yaml
:language: yaml
:start-at: os_reserve:
:end-before: ram_for_service:
```

```{include} _generated/where-the-numbers-come-from-stage.md
```

```{include} _generated/where-the-numbers-come-from-stage-shape.md
```

The graph below has three more nodes than [ch02](#what-a-workload-is)'s. The output table's final
row is in decimal terabytes per host; *ram per host* itself is in gibibytes per host—the build
converts between units. Since a gibibyte is larger than a gigabyte, the row is larger than what you
would get by taking the reserve from the vendor's sheet figure and reading it as decimal gigabytes;
that difference is the first gap, now visible.

```{iframe} /models/web_service_provenance-reference.html
:width: 100%
The graph as ch03 leaves it. Click *ram per host* to see whose claim it is.
```

Still a definitional model, and a vendor's claim does not change that. A claim is about a number: how
much you should trust it. The distinction this book is built on is about the *shape* of the
arithmetic: whether the chain of multiplications stops applying somewhere. So a model can be
built entirely out of figures a salesperson supplied and still be a definitional model, and a model built
entirely out of your own measurements can be a conditional one. What flips it is a limit the system
runs into, and [ch06](#queueing-and-the-knee) adds the first.

### Three claims, counted

Here is the census of the running example as this chapter leaves it. It is short, and one row of
it is the claim above:

```{include} _generated/where-the-numbers-come-from-service-provenance.md
```

The book's second model is the observability platform, and its inputs include all three kinds of
claim. Both its vendor claims are figures quoted for a component: the collector's throughput per
core and the query tier's scan rate. The census table below shows facts and vendor claims; one row
counts assumptions, and the tally sums all three kinds. The complete census, every input with its
source, is in [Appendix F](#appendix-f-observability-model).

```{include} _generated/where-the-numbers-come-from-provenance.md
```

The tally at the bottom of each table shows what kind of claim each model rests on. Both models on
this page rest primarily on assumptions. A labelled assumption is acceptable—a reviewer can find
it and argue with it. An unlabelled assumption is not acceptable, because nothing marks it as a
decision anyone could challenge.

### A measured constant is not a fact about the world

% word-ok: a telemetry sample is one reading, not a draw from a spread
A compression ratio is not a property of compression. It is a property of some data and some
software at some version, and it moves when either changes. The software is the **codec**—the
program that compresses or encodes the data. The data is a **corpus**—a declared body of data the
codec runs over. Every corpus in this repository is generated by code in `bench/measure.py`, the
same way every time, from starting numbers the result records. Numbers like bytes per sample, spans
per request, and throughput per core behave the same way—this book calls them **measured
constants** and gives them their own node kind, `measured`. Every one names the implementation it
belongs to:

```{include} _generated/where-the-numbers-come-from-constants.md
```

% word-ok: a telemetry sample is one reading, not a draw from a spread
The *Measured against* column names the implementation. One of these constants, bytes per sample,
was produced by an encoder in this repository, not by any product. That encoder writes whole bytes,
whereas a production format that packs bits uses fewer bytes per sample. The figure is correct, and
it describes that encoder. If you copied it into a model of a real system, your model would be
wrong by an amount this page does not measure.

The method transfers. The number does not.

### Four targets, and who can check each

Every stamped result declares a **target**: what it was taken against. The target decides who can
check the result.

| Target | What it is | Who can check it |
|---|---|---|
| `corpus` | a codec or an encoder over a declared body of data | you, with the repository |
| `model` | a model file evaluated in this repository | you, with the repository |
| `rig` | a throughput or a latency, on the reference machine | whoever has that machine |
| `estate` | an observation of a running system | **nobody** |

A corpus result may carry no rate and no duration. CI re-derives every one on every push. A model
result is evidence about what the book's own models say, and about nothing else. The toolkit
refuses a rig measurement on any machine but the reference one: a throughput measured on whatever
machine was free is indistinguishable from a real one once it is a number in a table. The *Target*
column of the constants table above shows each measured constant's target.

### The target that cannot be checked, only disclosed

An observation of a running system cannot be repeated by you or anyone else, because there is no
corpus to re-run and no machine to re-run it on—the system has moved on. The observability model
includes one such quantity: *spans per request*, how many spans one request emits in one
instrumented application at one version. The build cannot derive it, the reference machine cannot
measure it, and it belongs to the `estate` target.

`estate` is held to the strictest disclosure rules in the book: the system, the window, and when
you observed it. That disclosure is the only verification an `estate` figure receives.

When a page uses an `estate` figure, it says so where it uses it, not in a footnote, so you can
tell which numbers rest on someone's word. Some quantities can only be known by watching a real
system. The book discloses them; it does not claim they can be checked.

### When nobody has measured it

```{include} _generated/where-the-numbers-come-from-measured.md
```

Two rows of the constants table above say *not yet measured*. The first is collector throughput
per core, a timing and thus a `rig` measurement—it needs the reference machine. The second is spans
per request from the earlier section, an `estate` observation of an instrumented application you
run.

```{include} _generated/where-the-numbers-come-from-unmeasured.md
```

A measured node with no value leaves nothing downstream with a value either; the toolkit works this
out from the graph with nothing marked by hand. The box names each missing constant, the result
file it needs, and counts the nodes downstream that cannot be computed.

The observability model declares collector throughput twice, on purpose: once as the vendor's
quoted figure, and once as a measured constant. The table below shows the two side by side, each
with the pipeline capacity it produces: collector cores times throughput per core.

The quoted row has a value, and so does its capacity. The measured row has neither. The only
pipeline capacity the model can compute today rests on the vendor's claim, and the table shows that
instead of filling the gap. No placeholder, no estimate, no number borrowed from a different stack
and quietly rounded. This gap stays visible on purpose: after one copy-paste, a placeholder cannot
be distinguished from a measurement.

### The rig, and why the book will not let you fake it

```{include} _generated/where-the-numbers-come-from-rig.md
```

The toolkit refuses to produce a `rig` measurement except on a machine that matches a declared
reference machine. The reference machine is declared in a file that names its processor model and
core count, and the toolkit compares your running processor against that
declaration. If no declaration exists, the toolkit refuses on every machine.

An environment variable would have been easier—you could set one and run anywhere. But setting a
variable by accident would let you stamp a laptop timing as a reference measurement. The
declaration must be a file that names the silicon, so a `rig` result cannot be produced by
accident.

### What a measurement is worth

One measurement is a number. It says nothing about how far it would move if you took it again. So
every constant in this book is measured over several shards: independently generated pieces of its
corpus, each from its own starting number, which the result records. The result reports the mean
of the shards' figures, with the standard error of that mean beside it.

The table walks one constant through: bytes per compressed log line. It shows the mean over the
shards, the standard error of that mean, the spread between shards, and the lowest and highest
shard. The spread between shards is how far a typical shard's figure sits from the mean. The
standard error is that spread divided by the square root of the number of shards. You can check it
against the table. The standard error is smaller than the spread because it is about the mean, and
a mean of several shards moves less than any one shard does.

That standard error becomes the measured node's uncertainty, and [ch13](#monte-carlo) carries it
through the model like any other. The build refuses a measured constant whose standard error is
zero: zero claims it was measured exactly.

A standard error also tells you what more measuring would buy. It falls as one over the square
root of the count, so halving it takes four times as many shards. Problem 3.2 is that arithmetic.
Do it before agreeing to a measurement campaign, not during one.

## What this cannot tell you

**Whether a corpus resembles your data.** Every constant above was measured over a corpus this
repository generates. For the record compression ratio, the corpus is a mix of three kinds of
record: user profiles, orders and events. Those proportions and schemas were chosen, not observed,
so they are an assumption. Nothing in this repository measures how the compression ratio changes
when the mixture changes. The standard error you see covers only shard-to-shard variation with the
mixture held constant. To measure what the mixture does, you would need to run the records
generator over some of your own records, or with a different mixture, and compare the ratios.

**Whether a `vendor_claim` is true.** Nothing here checks one. They are marked so you can see how
much of your model rests on them. The table under *When nobody has measured it* sets the quoted
collector throughput beside the measured one, which has no value yet. Where only the claim exists,
that is what you have.

**Whether an `estate` observation happened.** It is someone's word, with a disclosure attached:
what system, over what window, when. The disclosure lets you trace the figure to whoever took it.
It does not make the figure checkable, or true.

**Whether an assumption is reasonable.** The provenance census counts them. It does not read them.
A model can be all assumptions, all sourced, all defensible-sounding, and completely wrong.

## Key takeaways

:::{div}
:class: takeaways

- **Every input says how much its author was claiming.** A fact is traceable to something, a
  vendor's claim was stated by the vendor and is never quietly promoted, and an assumption is a
  decision a reviewer can argue with.
- **A measured constant belongs to some data and some software at some version.** The method
  transfers. The number does not.
- **Four targets, and nobody can check the fourth.** You can re-derive a `corpus` or a `model`
  result with the repository. A `rig` timing can be taken only on the reference machine a file
  declares, and the toolkit refuses it anywhere else. An `estate` observation of a running system
  is someone's word, with a disclosure attached: what system, over what window, when.
- **A constant nobody has measured has no value, and nor does anything downstream of it.** No
  placeholder, no estimate, no number borrowed from a different stack.
- **One measurement says nothing about its own wobble.** A constant is measured over several shards,
  and the result reports their mean with a standard error—the spread divided by the square root of
  the shard count. Halving that error takes four times as many shards.
:::

## Problems

Three, in `tests/where_the_numbers_come_from/`. The first two have tests. The third does not, and
says why.

**3.1 — Take a constant, and stamp it so somebody else could check it.**
Pick a quantity a codec decides and measure it over a corpus you generate deterministically, in
several shards. Hand back what a stamp records: the mean over the shards as the value, the standard
error of that mean, the figure from each shard, a unit for each figure with no time in it, and the
corpus and codec that produced them. *What a measurement is worth*, above, works a standard error
through from its shards. The test stamps the answer, holds it to every rule in
`bench.stamp.provenance_problems`, and checks that your standard error matches the shards you
provide.

```bash
python3 -m pytest tests/where_the_numbers_come_from/test_problem_1_measure.py -m problem
```

**3.2 — What would it cost to be more sure?**
Given a standard error at some number of shards, work out how many shards would be needed to reach
a target standard error. Halving your uncertainty costs four times the measuring. Work it out
before the measurement campaign starts, while the answer can still affect the decision.

```bash
python3 -m pytest tests/where_the_numbers_come_from/test_problem_2_shards.py -m problem
```

**3.3 — Label your own numbers.** No test: these are your numbers, and nothing here can check
them.

Take the quantities you wrote down for [ch02](#what-a-workload-is)'s problem 2.5 and put one of
three words against each: `fact`, `vendor_claim`, `assumption`. Then, for every `fact`, write the
source you would hand to someone who asked: a document, an invoice, a measurement with a date on
it. Write the thing you would send, not where you think it came from.

Any figure you read off a system you run—from a dashboard, a log line count, a monitoring tool—is
what this chapter calls an `estate` observation. Its source is the system, the window it covers,
and when you read it. Without those three, it is not yet a `fact`.

The useful work is reclassification. Count how many started as facts and ended as vendor claims
once you looked for the source. Count how many ended as assumptions because the source was a
conversation. The census tables on this page show how many inputs in the book's own models are
assumptions. That is why the labels are mandatory rather than encouraged.

A good answer has a source line for every `fact` that you could paste into an email, a system, a
window and a date for every `estate` figure, and at least one line that changed category while you
were writing it. If nothing changed category, you have labelled what you believe rather than what
you can show.

## Where to go next

[ch04](#peak-mean-and-growth) is about growth: the input that moves the web service's busy-hour
demand at the horizon more than any other input. Growth cannot be measured at all: a growth rate is
a claim about the future, and no amount of provenance discipline turns one into a measurement.

[ch13](#monte-carlo) is what to do with a standard error once you have one.
