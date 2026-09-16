# NEXT_STEPS.md

What is left, roughly in the order it is worth doing. Kept short and honest; when an item is done
it comes out rather than being ticked.

## Needs a machine or a system, not a desk

- **`collector-throughput-per-core`** (`rig`). Declare a reference machine in `rig/machine.yml`,
  write the runner, and `make measure-rig`. Until then the observability model's honest ingest
  ceiling cannot be computed, and the page says so.
- **`traces-spans-per-request`** (`estate`). An observation of an instrumented application: how
  many spans one request actually produces, over a stated window, on a named stack at a named
  version. Nothing in this repository can derive it. Stamping it lights up the whole traces chain
  with no other change to the model.

## The book

- Twenty chapters are stubs. Each names its question and the figures it owes; `make chapter`
  regenerates any that go missing. The order that makes the book readable soonest is ch01
  (*Reading a model*), then ch12 (*The sizing model*), then ch03 (*Where the numbers come from*) —
  those three are what ch13 and ch14 currently assume without being able to point at.
- Appendices A to D and G are stubs. B is nearly free: it is `sizing/mc.py` quoted in order.

## The toolkit

- **Part pages.** The template this book inherits from puts a short introduction in front of each
  part, and a test insists on it. Not carried over yet.
- **`sync-labels.py`.** Chapter numbers in prose are currently checked by `tests/test_book.py`
  rather than rewritten. With twenty stubs and few cross-references that is enough; it will not
  stay enough.
- **A second ceiling kind.** Every ceiling here is "a value against a limit". A queueing ceiling
  that took a service time and an arrival rate and derived the knee would let ch06 stop describing
  the shape and start drawing it.
- **Sensitivity beyond one-at-a-time.** The tornado swings each input alone, which ch19 will have
  to admit misses interaction effects. A variance-based decomposition over the samples already
  drawn is not much code.

## Known rough edges

- The dependency graph's layout is a barycentre heuristic. It is legible on both models and it
  will not stay legible forever.
- `bench/measure.py`'s corpora are synthetic, deliberately and loudly. The proportions in
  `mixed_objects` are the single largest assumption in the storage model's compression constant,
  and they are an assumption rather than an observation.
- The PDF renderer handles the node types the book currently uses and raises on anything else.
  That is the intended behaviour, and it means a new directive needs a branch.
