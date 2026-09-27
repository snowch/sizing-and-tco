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

import re
from importlib import resources

import pint
from pint.util import to_units_container

#: The currencies a model may price in, by ISO 4217 code. Each is a dimension of its own, so a
#: model that adds dollars to terabytes is refused, and so is one that adds dollars to euros: there
#: is no exchange rate in the registry, and a model that needs one declares it as a node in its own
#: unit (``USD/EUR``) with a source, like any other conversion. A model's ``currency:`` field names
#: the one it prices in, and ``scripts/verify-models.py`` refuses money in any other.
CURRENCIES: tuple[str, ...] = (
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CHF",
    "CAD",
    "AUD",
    "NZD",
    "CNY",
    "HKD",
    "SGD",
    "INR",
    "KRW",
    "SEK",
    "NOK",
    "DKK",
    "PLN",
    "CZK",
    "BRL",
    "MXN",
    "ZAR",
)

#: Quantities that are counted rather than measured, each its own dimension.
COUNTING_UNITS: tuple[str, ...] = (
    "USD = [currency_usd] = usd = dollar",
    *(f"{code} = [currency_{code.lower()}]" for code in CURRENCIES if code != "USD"),
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


def _definitions() -> list[str]:
    """Pint's own definitions, with one line changed: a bit is a dimension, not a pure number.

    Pint defines ``bit = []``, so a byte, a terabyte and every storage unit are dimensionless, and
    wherever a formula wants a pure number (an exponent, a logarithm) a terabyte passed. A growth
    factor raised to fifteen terabytes typechecked. With a dimension of its own, information is
    refused there by Pint itself, and a byte meets a pure number only through a node that says how.
    Pint's file imports its constants from beside itself, so they are read in here the same way.
    """
    package = resources.files("pint")
    text = (package / "default_en.txt").read_text()
    constants = (package / "constants_en.txt").read_text()
    text = re.sub(r"(?m)^@import constants_en\.txt\s*$", lambda _: constants, text)
    patched = re.sub(r"(?m)^bit = \[\]", "bit = [information]", text)
    if patched == text:
        raise RuntimeError("Pint's definitions no longer say `bit = []`; units.py needs revisiting")
    return patched.splitlines()


def registry() -> pint.UnitRegistry:
    """The book's unit registry.

    Everything a model may declare is a ratio scale. Pint also defines scales with an offset
    (degrees Celsius) and logarithmic ones (decibels); :func:`parse` refuses both, because a node
    converts by one factor and neither converts that way.
    """
    ureg = pint.UnitRegistry(None)
    ureg.load_definitions(_definitions())
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
        parsed = UNITS.Unit(unit)
    except Exception as exc:  # pint raises several unrelated types here
        raise UnitError(f"unknown unit {unit!r}: {exc}") from exc
    for name in to_units_container(parsed):
        converter = UNITS._units[name].converter
        if not converter.is_multiplicative or getattr(converter, "is_logarithmic", False):
            raise UnitError(
                f"unit {unit!r} is not a ratio scale: {name} converts with an offset or a "
                "logarithm, and a node converts by one factor"
            )
    return parsed


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


def described(unit: str) -> str:
    """What kind of quantity a unit makes, in the words ch02 teaches, for an error message.

    Not its dimensions: a message built from them tells a reader who has just learnt that a
    terabyte is a stock that ``TB`` is ``[information]``, which is true and no help.
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
