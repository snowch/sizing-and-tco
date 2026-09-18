"""Problem 3.1 - take a constant and stamp it.

Graded by the repository's own rules, applied to whatever the reader produced. There is nothing to
compare against, because the point is not the value - it is whether somebody else could check it.
"""

from __future__ import annotations

import pytest

from bench.stamp import provenance_problems
from sizing.units import has_time
from tests.where_the_numbers_come_from.stubs import measure_something

SHARDS = 6


@pytest.fixture
def payload():
    return measure_something(shards=SHARDS)


@pytest.mark.problem
def test_it_passes_every_provenance_rule(payload):
    problems = provenance_problems("your-constant.json", payload)
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_it_says_what_it_measured_and_with_what(payload):
    produced = payload["produced_by"]
    for required in ("corpus", "codec"):
        assert produced.get(required, "").strip(), (
            f"{required!r} is empty. A compression figure without the body of data it compressed "
            "is not a measurement, it is an anecdote."
        )


@pytest.mark.problem
def test_it_carries_an_uncertainty_that_came_from_somewhere(payload):
    summary = payload["summary"]
    assert "value" in summary and "sd" in summary
    assert summary["sd"] > 0, (
        "a standard error of zero claims the constant was measured exactly. Measure it over "
        "several independently generated shards and report the spread of the mean."
    )
    assert summary.get("shards", SHARDS) == SHARDS


@pytest.mark.problem
def test_nothing_in_it_is_about_how_fast_your_computer_is(payload):
    for figure, unit in payload["units"].items():
        assert not has_time(unit), (
            f"{figure} is in {unit!r}. How fast the codec ran is a property of the machine that "
            "ran it, not of the codec - that is a `rig` measurement and this is not a rig."
        )


@pytest.mark.problem
def test_measuring_it_twice_gives_the_same_answer(payload):
    again = measure_something(shards=SHARDS)
    assert again["summary"]["value"] == pytest.approx(payload["summary"]["value"], rel=1e-12), (
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
