"""Measurement and provenance for *Sizing and TCO*.

Two targets, and the split runs through the whole book:

* **corpus** — a deterministic measurement over a declared body of data with a named codec.
  Reproducible on any machine, re-derived by CI on every push, and never allowed to carry a rate
  or a duration.
* **rig** — a throughput or latency figure, taken natively on the declared reference machine and
  refused anywhere else.

:mod:`bench.stamp` holds the rules. :mod:`bench.figures` declares every figure the book contains.
"""
