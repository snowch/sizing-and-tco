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

Every chapter and every appendix is written. What is left, first, is the largest change the book
has had since the scaffold, and then the work a first draft leaves:

- **Retire the old spine.** PLAN.md §4 records the decision and the first two of its three moves
  have landed: every chapter, figure, experiment and test now runs on `models/web_service`. What
  is left is the third: remove `models/storage_cluster` and `models/service_tier`, their stamped
  results, viewers and playgrounds, the `mixed_objects` corpus and its `storage-object-compression`
  constant if nothing still reads it, their pins in `tests/test_models.py`, and every mention that
  survives in the toolkit's docstrings — `sizing/evaluate.py` and `bench/run_corpus.py` still name
  the storage model, and the first of those is in `KIND_SOURCES["model"]`, so that edit re-stamps
  every model result.
- **A rig, or not.** `service_demand`, CPU time per request, is a `rig` measurement and none can
  be taken here. It is held as a labelled claim. Declaring a machine in `rig/machine.yml` and
  writing the runner turns the running example into the book's first end-to-end measured model.

- **The chapters that are waiting on a measurement.** ch20 and ch22 both describe the
  observability model's traces chain around a hole, and so does Appendix F. They read correctly
  today and they will read better when the chain lights up; none needs a rewrite, which was the
  point of building the blocked-state machinery.
- **Cross-references.** Every chapter links forwards and backwards by hand. `tests/test_book.py`
  checks the anchors resolve, not that the links are the right ones.

## The toolkit

- **Sensitivity beyond one-at-a-time, properly.** `bench/run_information.py` bounds what each
  input is worth on its own, which is most of what ch19 needed. A variance-based decomposition
  over the samples already drawn would answer the interaction question the tornado cannot, and is
  still not much code.
- **A second ceiling kind.** Every ceiling here is "a value against a limit". A queueing ceiling
  that took a service time and an arrival rate and derived the knee would let ch05 stop describing
  the shape and start drawing it.

## Known rough edges

- The dependency graph's layout is a barycentre heuristic. It is legible on both models and it
  will not stay legible forever.
- `bench/measure.py`'s corpora are synthetic, deliberately and loudly. The proportions in
  `mixed_objects` and the schemas in `application_records` are the single largest assumption in
  each model's compression constant, and they are an assumption rather than an observation.
- `bench/render.py` handles the node types the book currently uses and raises on anything else.
  That is the intended behaviour, and it means a new directive needs a branch.
- **Nothing checks what a page looks like.** Every check here reads the source or the parsed
  content, and both can be perfectly valid while the rendered page is wrong. Money written as
  `$318,062 to $611,522` shipped for weeks as an equation, because two dollar signs on a line are
  a LaTeX span and nothing in a clean build says so. `tests/test_figures.py` covers the SVGs and
  `ci-check.sh` now refuses an `inlineMath` node, but both of those were written after somebody
  looked at the site on a phone. That is still the only way this class of fault is found.
