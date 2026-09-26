"""Problem 3.1 - take a constant and stamp it.

Graded by the repository's own rules, applied to whatever the reader produced. The reader hands
back a value, its standard error, the figure from each shard, their units and what produced them;
the test stamps those the way the book stamps its own constants, and holds the result to the same
rules. The only thing it compares against is the reader's own shards, because the point is not the
value - it is whether somebody else could check it.
"""

from __future__ import annotations

import math
import statistics

import pytest

from bench.stamp import build_result, load_result, provenance_problems
from sizing.units import UnitError, has_time
from tests.where_the_numbers_come_from.stubs import measure_something

SHARDS = 6
PARTS = ("summary", "units", "produced_by", "per_shard")
#: The code that produced the figure: the reader's, and the stamp hashes it.
STUB = "tests/where_the_numbers_come_from/stubs.py"
#: Where a reader whose `sd` is wrong is sent. The page works one through; the test does not.
WORKED = "*What a measurement is worth*, in the chapter, works one through from its shards."


def stamped(answer: dict) -> dict:
    """The reader's three stamped parts, stamped as the book stamps a corpus constant."""
    return build_result(
        "your-constant",
        target="corpus",
        kind="measurement",
        produced_by=answer["produced_by"],
        summary=answer["summary"],
        units=answer["units"],
        code_sources=[STUB],
        write=False,
    )


def standard_errors(values: list[float]) -> tuple[float, float]:
    """The standard error of the mean of ``values``, with the spread taken both common ways.

    ``bench.measure.with_error`` divides by one less than the count; numpy's default divides by
    the count. Either is the standard error of a mean and a reader who used either has the point,
    so both pass. Derived from the reader's own shards at test time, never stored.
    """
    root = math.sqrt(len(values))
    return statistics.stdev(values) / root, statistics.pstdev(values) / root


@pytest.fixture
def answer():
    out = measure_something(shards=SHARDS)
    missing = [part for part in PARTS if part not in out]
    assert not missing, f"the answer has no {missing}; the stub says which four parts to return"
    return out


@pytest.mark.problem
def test_it_passes_every_provenance_rule(answer):
    # The refusal is kept and reported outside the `except`, so the reader sees the stamp's
    # sentences and not a chained traceback through Pint.
    try:
        payload, refusal = stamped(answer), None
    except ValueError as raised:
        payload, refusal = None, str(raised)
    if refusal is not None:
        hint = (
            "\n\nThe toolkit refuses a unit it does not know. The stub's docstring lists the ones "
            "it knows."
            if "not a unit" in refusal
            else ""
        )
        pytest.fail(f"the stamp refused it:\n{refusal}{hint}", pytrace=False)
    assert not provenance_problems("your-constant.json", payload)


@pytest.mark.problem
def test_it_says_what_it_measured_and_with_what(answer):
    produced = answer["produced_by"]
    for required in ("corpus", "codec"):
        assert produced.get(required, "").strip(), (
            f"{required!r} is empty. A compression figure without the body of data it compressed "
            "is not a measurement, it is an anecdote."
        )


@pytest.mark.problem
def test_it_carries_an_uncertainty_that_came_from_somewhere(answer):
    summary = answer["summary"]
    missing = [key for key in ("value", "sd") if key not in summary]
    if missing:
        pytest.fail(f"the summary has no {missing}; the stub says what it holds", pytrace=False)
    assert summary["sd"] > 0, (
        "a standard error of zero claims the constant was measured exactly. Measure it over "
        "several independently generated shards and report the standard error of their mean."
    )
    assert summary.get("shards", SHARDS) == SHARDS, (
        "summary['shards'] is not the number of shards the test asked for. Pass the argument "
        "through."
    )


@pytest.mark.problem
def test_its_sd_is_the_standard_error_of_its_own_shards(answer):
    values = [float(value) for value in answer["per_shard"]]
    if len(values) != SHARDS:
        pytest.fail(
            f"per_shard holds {len(values)} figures, and the test asked for {SHARDS} shards. "
            "Return one figure per shard.",
            pytrace=False,
        )
    summary = answer["summary"]
    if summary["value"] != pytest.approx(statistics.fmean(values), rel=1e-9):
        pytest.fail(
            "value is not the mean of per_shard. A stamp records the mean over the shards, so the "
            "two have to agree.",
            pytrace=False,
        )
    spreads = (statistics.stdev(values), statistics.pstdev(values))
    if any(summary["sd"] == pytest.approx(spread, rel=1e-6) for spread in spreads if spread):
        pytest.fail(
            "sd is the spread between your shards. The stamp wants the standard error of their "
            f"mean, which is a different number. {WORKED}",
            pytrace=False,
        )
    if not any(
        summary["sd"] == pytest.approx(error, rel=1e-6) for error in standard_errors(values)
    ):
        pytest.fail(
            f"sd is not the standard error of the mean of per_shard. {WORKED}", pytrace=False
        )


@pytest.mark.problem
def test_nothing_in_it_is_about_how_fast_your_computer_is(answer):
    for figure, unit in answer["units"].items():
        try:
            timed = has_time(unit)
        except UnitError:
            timed = None
        if timed is None:
            pytest.fail(
                f"{figure} is in {unit!r}, which the toolkit does not know. The stub's docstring "
                "lists the units it does; a ratio or a plain count is 'dimensionless'.",
                pytrace=False,
            )
        if timed:
            pytest.fail(
                f"{figure} is in {unit!r}. How fast the codec ran is a property of the machine "
                "that ran it, not of the codec - that is a `rig` measurement and this is not a "
                "rig.",
                pytrace=False,
            )


@pytest.mark.problem
def test_measuring_it_twice_gives_the_same_answer(answer):
    again = measure_something(shards=SHARDS)
    assert again["summary"]["value"] == pytest.approx(answer["summary"]["value"], rel=1e-12), (
        "two runs disagree, so the corpus is not deterministic. State your seeds and use them: a "
        "constant nobody else can reproduce is a constant nobody else can check."
    )


def test_the_books_own_constants_pass_the_same_rules():
    """Scaffolding: the bar the reader is held to is the bar the book is held to."""
    import json
    from pathlib import Path

    for path in Path("bench/results").glob("*.json"):
        payload = json.loads(path.read_text())
        if payload.get("target") != "corpus":
            continue
        assert not provenance_problems(path.name, payload)


def test_the_books_own_constants_carry_a_standard_error_not_a_spread():
    """Scaffolding: the rule the reader's ``sd`` is held to is the one the book's own stamps keep,
    and at this many shards the two numbers the test tells apart are far apart."""
    summary = load_result("logs-line-bytes")["summary"]
    assert summary["sd"] == pytest.approx(
        summary["shard_spread"] / math.sqrt(summary["shards"]), rel=1e-9
    )
    # The spread is the standard error times the root of the shard count: over twice it here.
    assert math.sqrt(SHARDS) > 2


def test_the_stamp_the_reader_is_held_to_refuses_a_rate():
    """Scaffolding: the stamp the test applies is real and does refuse things. A figure with time
    in its unit is the one thing a corpus result may never carry, and the refusal names it."""
    with pytest.raises(ValueError, match="time"):
        stamped(
            {
                "summary": {"value": 1.0, "sd": 0.5, "shards": SHARDS},
                "units": {"value": "byte/second", "sd": "byte/second", "shards": "dimensionless"},
                "produced_by": {"corpus": "none", "codec": "none"},
            }
        )


def test_the_stamp_says_when_a_unit_is_not_one():
    """Scaffolding: the hint in the first test keys off these words in the stamp's refusal, so a
    rewording there would silently drop the hint."""
    with pytest.raises(ValueError, match="not a unit"):
        stamped(
            {
                "summary": {"value": 1.0, "sd": 0.5, "shards": SHARDS},
                "units": {"value": "byte/uuid", "sd": "byte/uuid", "shards": "dimensionless"},
                "produced_by": {"corpus": "none", "codec": "none"},
            }
        )
