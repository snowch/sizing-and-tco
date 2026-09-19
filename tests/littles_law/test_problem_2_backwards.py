"""Problem 5.2 - the law used the way it is actually used.

The oracle is the same model, run forwards: take its arrival rate and its concurrency, hand them
to the reader's function, and check the residence time that comes back is the one the model
started from. A round trip through the reader's arithmetic.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.littles_law.stubs import residence_from_observation


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


@pytest.mark.problem
def test_the_round_trip_returns_what_it_started_with(evaluated):
    recovered = residence_from_observation(
        evaluated.samples["concurrency"], evaluated.samples["peak_request_rate"]
    )
    assert np.allclose(recovered, evaluated.samples["residence_time"], rtol=1e-9), (
        "inferring residence time from what you can observe has to give back the residence time "
        "the model used to produce that observation, or the inversion is wrong"
    )


@pytest.mark.problem
def test_it_works_on_numbers_somebody_could_actually_have():
    """A connection gauge and a request counter, which is all anybody needs."""
    assert residence_from_observation(90.0, 4500.0) == pytest.approx(0.02)
    assert residence_from_observation(1.0, 1.0) == pytest.approx(1.0)


@pytest.mark.problem
def test_a_system_with_nothing_arriving_is_refused_or_infinite():
    """Zero arrivals says nothing about how long anything stays. Say so, or return infinity."""
    try:
        answer = residence_from_observation(5.0, 0.0)
    except (ZeroDivisionError, ValueError):
        return
    assert not np.isfinite(answer), (
        "with nothing arriving there is no residence time to infer; return an infinity or raise, "
        "but do not return a number somebody could put in a slide"
    )


def test_the_two_observables_are_things_a_system_exposes(evaluated):
    """Scaffolding: the problem's premise holds — both are nodes, and both vary."""
    for name in ("concurrency", "peak_request_rate"):
        assert name in evaluated.samples and evaluated.samples[name].std() > 0
