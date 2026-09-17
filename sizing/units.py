"""Units, and the reason this book has a build step at all.

A sizing model is a chain of multiplications, and the commonest way for one to be wrong is not
arithmetic — it is multiplying two quantities that should never have met. Series by requests.
Bytes by seconds. A per-node figure by a per-core one. Spreadsheets cannot see any of this: a
cell holds a number, the number has no dimension, and ``=B4*C7`` is as valid as any other
product. Every node here declares a unit instead, and :func:`check_formula` refuses a model whose
formula does not typecheck.

## Counting units are units

The registry defines ``request``, ``span``, ``sample``, ``series``, ``line``, ``query``, ``host``,
``node``, ``core``, ``label`` and ``drive`` as *dimensions of their own*, not as synonyms for
"dimensionless". That is the whole value of this module. Without it, spans-per-request and
bytes-per-span are both plain numbers and multiplying the wrong pair gives a plausible answer;
with it, ``request/second × span/request × byte/span`` is ``byte/second`` and nothing else is.

It costs something, and the cost is the point: converting between two counting units requires a
node that names the conversion. That node is exactly the *measured constant* of ch02 — an
empirical, stack-specific number with provenance — so the unit system pushes you towards
declaring the thing the book says you must declare.

## Why Pint is not in the evaluator

Pint is used **here, at build time, and nowhere else**. :func:`check_formula` walks a model's
formulas with unit-bearing quantities and raises on a dimensional error; after that the units are
stripped and :mod:`sizing.evaluate` works in plain ``float64``.

Two reasons. A unit-bearing array across a hundred nodes and a hundred thousand samples is slow
and its semantics are fiddly in ways that have nothing to do with the subject. And
:mod:`sizing.mc` is a chapter of this book that the reader is asked to read: a units library in
the middle of it would be answering a question nobody asked. Units are a gate, not a tax.
"""

from __future__ import annotations

import pint

#: Quantities that are counted rather than measured, each its own dimension.
#:
#: ``currency`` is here for the same reason: a model that adds dollars to terabytes is broken,
#: and nothing else in the registry would notice. The book prices in USD (``myst.yml`` and each
#: model's ``currency:`` field), and a model may declare another — the dimension is what matters,
#: and a model that mixes two currencies without a declared rate fails to typecheck.
COUNTING_UNITS: tuple[str, ...] = (
    "USD = [currency] = usd = dollar",
    "request = [request] = req",
    "span = [span]",
    "sample = [sample]",
    "series = [series]",
    "line = [line]",
    "query = [query]",
    "host = [host]",
    "node = [node]",
    "core = [core]",
    "label = [label]",
    "drive = [drive]",
    "failure = [failure]",
)


def registry() -> pint.UnitRegistry:
    """The book's unit registry.

    ``autoconvert_offset_to_baseunit`` is off and no temperature units are defined: this book has
    no use for a scale with an offset, and a model that tried to multiply by one would be wrong in
    a way that is tedious to explain. Everything here is a ratio scale.
    """
    ureg = pint.UnitRegistry()
    for definition in COUNTING_UNITS:
        ureg.define(definition)
    return ureg


#: One registry for the process. Pint quantities from two registries do not interoperate, and the
#: resulting error message is about registries rather than about the model, which is the least
#: useful place for a units error to surface.
UNITS = registry()


class UnitError(ValueError):
    """A model that does not typecheck.

    Carries the node, what the formula produces and what the node declared, because those three
    together are the whole of the fix and hunting for any of them is wasted time.
    """


def parse(unit: str):
    """A declared unit string as a Pint unit, with a readable failure.

    ``dimensionless`` is spelled out rather than left blank. A blank unit in a model file is
    ambiguous between "this is a pure ratio" and "nobody has thought about it yet", and the
    second is the one worth catching.
    """
    try:
        return UNITS.Unit(unit)
    except Exception as exc:  # pint raises several unrelated types here
        raise UnitError(f"unknown unit {unit!r}: {exc}") from exc


def quantity(value: float, unit: str):
    """A magnitude with a unit attached."""
    return UNITS.Quantity(value, parse(unit))


def compatible(left: str, right: str) -> bool:
    """Whether two declared units describe the same kind of thing.

    Compatible, not equal: ``TB`` and ``GB`` are the same dimension and a model may declare either.
    ``TB`` and ``TiB`` are also compatible, which is why appendix D exists — Pint will convert
    between them silently and correctly, and the reader still has to know which one the vendor
    meant.
    """
    return parse(left).dimensionality == parse(right).dimensionality


def dimensionality(unit: str) -> str:
    """A unit's dimensions, as a string, for an error message or a stamped result."""
    return str(parse(unit).dimensionality)


def has_time(unit: str) -> bool:
    """Whether a unit is about how long something takes or how fast it goes.

    Used by :mod:`bench.stamp` to enforce the rule that a ``corpus`` measurement may not carry a
    duration or a rate. A codec's compression ratio is a property of the codec and the data; how
    fast it ran is a property of the machine that ran it, and the two must not arrive in the same
    file wearing the same stamp.
    """
    return "[time]" in parse(unit).dimensionality
