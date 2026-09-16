"""The rules a stamped result is held to, checked where the rules can be checked.

One of these exists because of a CI failure rather than a design review: an identical tree went
green on one runner and red on another, because two summaries were compared for exact equality
and numpy takes different instruction paths on different processors. A check that fails for a
reason unrelated to what it is checking is worse than no check, because people learn to re-run it.
"""

from __future__ import annotations

import pytest

from bench.stamp import (
    RERUN_TOLERANCE,
    TARGET_MEANING,
    TARGETS,
    numeric_differences,
    provenance_problems,
)


def test_every_target_says_what_it_means():
    assert set(TARGETS) == set(TARGET_MEANING), "a target with no stated meaning is a label"


def test_tiny_float_noise_is_not_a_difference():
    """What broke CI: the last bits of a percentile differ between processors."""
    committed = {"curve": [{"value": 1.2599999999999998}], "n": 100}
    fresh = {"curve": [{"value": 1.2600000000000002}], "n": 100}
    assert numeric_differences(committed, fresh) == []


def test_a_real_change_is_a_difference():
    assert numeric_differences({"a": 1.0}, {"a": 1.01})
    assert numeric_differences({"a": 1.0}, {"a": 1.0 + 2 * RERUN_TOLERANCE})


@pytest.mark.parametrize(
    ("committed", "fresh", "expected"),
    [
        ({"a": 1}, {}, "removed"),
        ({}, {"a": 1}, "added"),
        ({"a": [1, 2]}, {"a": [1, 2, 3]}, "entries became"),
        ({"a": "zstd"}, {"a": "gzip"}, "->"),
        ({"a": True}, {"a": False}, "->"),
    ],
)
def test_structural_changes_are_never_forgiven(committed, fresh, expected):
    """A renamed key or a changed codec is never floating-point noise."""
    found = numeric_differences(committed, fresh)
    assert found and expected in found[0]


def test_a_true_and_a_one_are_not_the_same_thing():
    """`True == 1` in Python, and a flag that became a count is a real change."""
    assert numeric_differences({"over": True}, {"over": 1.0})


def test_a_corpus_result_may_not_carry_a_duration():
    problems = provenance_problems(
        "x.json",
        {
            "target": "corpus",
            "kind": "measurement",
            "produced_by": {"corpus": "c", "codec": "d"},
            "summary": {"rate": 5.0},
            "units": {"rate": "byte/second"},
        },
    )
    assert any("has time in it" in line for line in problems)


def test_a_model_result_must_declare_the_model_target():
    problems = provenance_problems(
        "x.json",
        {
            "target": "corpus",
            "kind": "model",
            "produced_by": {"model": "m", "scenario": "s", "seed": 1, "samples": 10},
            "summary": {"nodes": {}},
            "units": {},
        },
    )
    assert any("must declare target 'model'" in line for line in problems)


def test_an_estate_observation_must_disclose_what_it_watched():
    problems = provenance_problems(
        "x.json",
        {
            "target": "estate",
            "kind": "measurement",
            "produced_by": {"stack": "something"},
            "summary": {"value": 3.0},
            "units": {"value": "span/request"},
        },
    )
    for required in ("system", "window", "observed_at"):
        assert any(required in line for line in problems)
