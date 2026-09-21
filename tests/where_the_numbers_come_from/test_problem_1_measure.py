"""Problem 3.1 - take a constant and stamp it.

Graded by the repository's own rules, applied to whatever the reader produced. The reader hands
back a value, its spread, their units and what produced them; the test stamps those the way the
book stamps its own constants, and holds the result to the same rules. There is nothing to
compare against, because the point is not the value - it is whether somebody else could check it.
"""

from __future__ import annotations

import pytest

from bench.stamp import build_result, provenance_problems
from sizing.units import has_time
from tests.where_the_numbers_come_from.stubs import measure_something

SHARDS = 6
PARTS = ("summary", "units", "produced_by")
#: The code that produced the figure: the reader's, and the stamp hashes it.
STUB = "tests/where_the_numbers_come_from/stubs.py"


def stamped(answer: dict) -> dict:
    """The reader's three parts, stamped as the book stamps a corpus constant."""
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


@pytest.fixture
def answer():
    out = measure_something(shards=SHARDS)
    missing = [part for part in PARTS if part not in out]
    assert not missing, f"the answer has no {missing}; the stub says which three parts to return"
    return out


@pytest.mark.problem
def test_it_passes_every_provenance_rule(answer):
    try:
        payload = stamped(answer)
    except ValueError as refusal:
        pytest.fail(f"the stamp refused it:\n{refusal}")
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
    assert "value" in summary and "sd" in summary
    assert summary["sd"] > 0, (
        "a standard error of zero claims the constant was measured exactly. Measure it over "
        "several independently generated shards and report the spread of the mean."
    )
    assert summary.get("shards", SHARDS) == SHARDS


@pytest.mark.problem
def test_nothing_in_it_is_about_how_fast_your_computer_is(answer):
    for figure, unit in answer["units"].items():
        assert not has_time(unit), (
            f"{figure} is in {unit!r}. How fast the codec ran is a property of the machine that "
            "ran it, not of the codec - that is a `rig` measurement and this is not a rig."
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
