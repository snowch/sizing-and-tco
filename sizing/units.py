"""Units, and the reason this book has a build step at all.

A sizing model is a chain of multiplications, and the commonest way for one to be wrong is not
arithmetic — it is multiplying two quantities that should never have met. Series by requests.
Bytes by seconds. A per-node figure by a per-core one. Spreadsheets cannot see any of this: a
cell holds a number, the number has no dimension, and ``=B4*C7`` is as valid as any other
product. Every node here declares a unit instead, and :func:`sizing.evaluate.check_units` refuses
a model whose formula does not typecheck.

## Counting units are units

The registry defines everything in :data:`COUNTING_UNITS` as a *dimension of its own*, not as a
synonym for "dimensionless". That is the whole value of this module. Without it,
spans-per-request and bytes-per-span are both plain numbers and multiplying the wrong pair gives a
plausible answer; with it, ``request/second × span/request × byte/span`` is ``byte/second`` and
nothing else is.

Converting between two counting units requires a node that names the conversion, in its own unit
(``span/request``, ``sample/series``). That node carries a provenance like any other input, so the
unit system makes the conversion declared and sourced. It is sometimes a measured constant, like
``spans_per_request`` in the observability model, and sometimes not: ``one_sample_per_series`` is
a definition, ``lines_per_request`` an assumption, ``cores_per_host`` a vendor claim. Only a
measured one makes the model conditional (ch01).

## Why Pint is not in the evaluator

Pint is used **here, at build time, and nowhere else**. :func:`sizing.evaluate.check_units` walks
a model's formulas with unit-bearing quantities and reports every formula whose unit does not
follow, and the conversion factor for each one that does; after that the units are stripped and
:mod:`sizing.evaluate` works in plain ``float64``.

Two reasons. A unit-bearing array across every node and every draw of a model is slow, and its
behaviour is fiddly in ways unrelated to the subject. :mod:`sizing.mc` is read end to end in
Appendix B. A units library inside it would add code unrelated to what the module is for. Units
are a gate, not a tax.
"""

from __future__ import annotations

import pint
from pint.util import to_units_container

#: Quantities that are counted rather than measured, each its own dimension.
#:
#: ``currency`` is here for the same reason: a model that adds dollars to terabytes is broken,
#: and nothing else in the registry would notice. The registry defines one currency, ``USD``. A
#: unit in any other currency is unknown, so a model that uses one does not load. A model's
#: ``currency:`` field is a label; no check reads it.
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
    return parse(left).dimensionality == parse(right).dimensionality and _bits(left) == _bits(right)


def _bits(unit: str) -> float:
    """How many times bits or bytes appear in a unit, net of any that cancel.

    Pint gives bits no dimension, so on dimensions alone a plain number and a terabyte are the
    same kind of thing, and converting one to the other quietly multiplies by 1.25e-13. A node
    declared in ``TB`` whose formula produced a pure number, or a ceiling in ``TB`` with a bare
    limit, typechecked and then compared against a number thirteen orders of magnitude too
    small. Counting the bits in each unit is what tells an amount of data from a ratio.
    """
    root = UNITS.Quantity(1.0, parse(unit)).to_root_units().units
    return float(dict(to_units_container(root)).get("bit", 0))


def dimensionality(unit: str) -> str:
    """A unit's dimensions, as a string, for an error message or a stamped result."""
    return str(parse(unit).dimensionality)


def described(unit: str) -> str:
    """What kind of quantity a unit makes, in the words ch02 teaches, for an error message.

    Not its dimensions: bytes carry none in this registry, so a message built from dimensions
    told a reader who had just learnt that a terabyte is a stock that ``TB`` was dimensionless.
    """
    parsed = parse(unit)
    time = parsed.dimensionality.get("[time]", 0)
    if time < 0:
        return "a rate"
    if time > 0:
        return "a duration"
    powers = list(to_units_container(parsed).values())
    if not powers:
        return "a pure number"
    return "an amount" if all(power > 0 for power in powers) else "a ratio"


def has_time(unit: str) -> bool:
    """Whether a unit is about how long something takes or how fast it goes.

    Used by :mod:`bench.stamp` to enforce the rule that a ``corpus`` measurement may not carry a
    duration or a rate. A codec's compression ratio is a property of the codec and the data; how
    fast it ran is a property of the machine that ran it, and the two must not arrive in the same
    file wearing the same stamp.
    """
    return "[time]" in parse(unit).dimensionality
