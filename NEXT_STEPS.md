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

Every chapter and every appendix is written. What is left is the work a first draft leaves:

- **The two chapters that are waiting on measurements.** ch19 and ch21 both describe the
  observability model's traces chain around a hole. They read correctly today and they will
  read better when the chain lights up; neither needs a rewrite, which was the point of building
  the blocked-state machinery.
- **Cross-references.** Every chapter links forwards and backwards by hand. `tests/test_book.py`
  checks the anchors resolve, not that the links are the right ones.

## The toolkit

- **Sensitivity beyond one-at-a-time, properly.** `bench/run_information.py` bounds what each
  input is worth on its own, which is most of what ch18 needed. A variance-based decomposition
  over the samples already drawn would answer the interaction question the tornado cannot, and is
  still not much code.
- **`sync-labels.py`.** Chapter numbers in prose are currently checked by `tests/test_book.py`
  rather than rewritten. Inserting a chapter now means editing every `chNN` that a page says out
  loud, and the check will find them, which is not the same as fixing them.
- **A second ceiling kind.** Every ceiling here is "a value against a limit". A queueing ceiling
  that took a service time and an arrival rate and derived the knee would let ch05 stop describing
  the shape and start drawing it.

## Known rough edges

- The dependency graph's layout is a barycentre heuristic. It is legible on both models and it
  will not stay legible forever.
- `bench/measure.py`'s corpora are synthetic, deliberately and loudly. The proportions in
  `mixed_objects` are the single largest assumption in the storage model's compression constant,
  and they are an assumption rather than an observation.
- The PDF renderer handles the node types the book currently uses and raises on anything else.
  That is the intended behaviour, and it means a new directive needs a branch.
- **Nothing checks what a page looks like.** Every check here reads the source or the parsed
  content, and both can be perfectly valid while the rendered page is wrong. Money written as
  `$318,062 to $611,522` shipped for weeks as an equation, because two dollar signs on a line are
  a LaTeX span and nothing in a clean build says so. `tests/test_figures.py` covers the SVGs and
  `ci-check.sh` now refuses an `inlineMath` node, but both of those were written after somebody
  looked at the site on a phone. That is still the only way this class of fault is found.
