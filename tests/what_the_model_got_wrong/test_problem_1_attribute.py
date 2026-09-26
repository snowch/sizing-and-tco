"""Problem 23.1 - attributing a failure to the inputs that were doing something unusual.

Graded twice over. Against a synthetic case whose answer is arithmetic, so the test knows what
the right answer is without anybody storing one; and against the book's own web service model, where
the ranking has to match the attribution the build publishes.
"""

from __future__ import annotations

import numpy as np
import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate, sampled_inputs
from tests.what_the_model_got_wrong.stubs import attribute

WEB_SERVICE = "models/web_service/model.yaml"
REFERENCE = "models/web_service/scenarios/reference.yaml"


def synthetic(n: int = 20_000) -> tuple[dict[str, np.ndarray], np.ndarray, float]:
    """One input that causes the failures, one that is a bystander, and the exact answer.

    ``guilty`` is uniform on [0, 1) and the design fails when it is above 0.8. Its median overall
    is a half; its median among the failures is nine tenths. So the shift is exactly 0.8, and no
    part of that figure came from the code under test.
    """
    generator = np.random.Generator(np.random.PCG64(20260916))
    guilty = generator.random(n)
    bystander = generator.random(n) * 100.0
    return {"guilty": guilty, "bystander": bystander}, guilty > 0.8, 0.8


def low_in_the_failures(n: int = 20_000) -> tuple[dict[str, np.ndarray], np.ndarray, float]:
    """One input that is *low* in the failures, one that is a little high, and the exact answer.

    ``cause`` is one plus a uniform on [0, 1), and the design fails when the uniform is below
    0.2. Its median overall is 1.5; its median among the failures is 1.1. So its shift is exactly
    -4/15. ``follower`` leans a little the other way, so it is high in the failures by less.
    Ordered by sign, ``follower`` comes first; ordered by size, ``cause`` does.
    """
    generator = np.random.Generator(np.random.PCG64(20260917))
    uniform, noise = generator.random(n), generator.random(n)
    draws = {"cause": 1.0 + uniform, "follower": 1.0 + 0.3 * (1.0 - uniform) + 0.7 * noise}
    return draws, uniform < 0.2, 1.1 / 1.5 - 1.0


def service_draws() -> tuple[dict[str, np.ndarray], np.ndarray]:
    model, scenario = load_model(WEB_SERVICE), load_scenario(REFERENCE)
    result = evaluate(model, scenario)
    failed = np.asarray(result.samples["queueing_headroom"], dtype=float) > 1.0
    draws = {
        name: np.asarray(result.samples[name], dtype=float)
        for name in sampled_inputs(model)
        if name in result.samples and name in model.ancestors("queueing_headroom")
    }
    return draws, failed


@pytest.mark.problem
def test_the_guilty_input_is_first_and_the_bystander_is_not():
    draws, failed, _ = synthetic()
    ranked = attribute(draws, failed)
    assert [name for name, _ in ranked][0] == "guilty", (
        "the input that decides the failures has to come first, by a distance"
    )
    assert abs(dict(ranked)["bystander"]) < 0.05, "a bystander's shift is about nothing"


@pytest.mark.problem
def test_the_shift_is_the_arithmetic_answer():
    draws, failed, expected = synthetic()
    assert dict(attribute(draws, failed))["guilty"] == pytest.approx(expected, abs=0.02), (
        "the median of a uniform above its own 80th percentile is 0.9, against 0.5 overall"
    )


@pytest.mark.problem
def test_an_input_that_is_low_in_the_failures_comes_first_when_its_shift_is_largest():
    draws, failed, expected = low_in_the_failures()
    ranked = attribute(draws, failed)
    assert [name for name, _ in ranked][0] == "cause", (
        "one input here sits well below its usual value in the failures, and it belongs first: "
        "order by the size of the shift, not by its sign"
    )
    close = abs(dict(ranked)["cause"] - expected) <= 0.02
    assert close, "the shift of an input that is low in the failures is negative; keep its sign"


@pytest.mark.problem
def test_an_input_that_never_moves_has_no_shift():
    n = 1_000
    draws = {"fixed": np.full(n, 3.0), "moving": np.linspace(0.0, 1.0, n)}
    failed = draws["moving"] > 0.9
    assert dict(attribute(draws, failed))["fixed"] == pytest.approx(0.0)


@pytest.mark.problem
def test_it_agrees_with_the_attribution_the_build_publishes():
    draws, failed = service_draws()
    ranked = attribute(draws, failed)
    published = load_result("postmortem")["summary"]["complete"]["rows"]
    assert [name for name, _ in ranked] == [row["input"] for row in published], (
        "the same draws and the same question should give the same order"
    )
    first = published[0]
    close = abs(dict(ranked)[first["input"]] / first["shift"] - 1.0) <= 1e-6
    assert close, (
        f"the order is right, but the shift of {first['label']!r} does not match the published "
        "one. It is the median in the failures over the median across every future, minus one: "
        "a mean gives a different figure on inputs this skewed"
    )


# -- scaffolding: the problem is answerable, and its cases are not all the same case ------------


def test_the_synthetic_case_has_a_cause_and_a_bystander():
    draws, failed, expected = synthetic()
    assert 0.15 < failed.mean() < 0.25, "the failures have to be a fifth of the samples, roughly"
    guilty = float(np.median(draws["guilty"][failed]) / np.median(draws["guilty"]) - 1.0)
    bystander = float(np.median(draws["bystander"][failed]) / np.median(draws["bystander"]) - 1.0)
    assert guilty == pytest.approx(expected, abs=0.02) and abs(bystander) < 0.05


def test_the_low_case_tells_size_from_sign():
    draws, failed, expected = low_in_the_failures()
    shift = {
        name: float(np.median(drawn[failed]) / np.median(drawn) - 1.0)
        for name, drawn in draws.items()
    }
    assert shift["cause"] == pytest.approx(expected, abs=0.02)
    assert 0.02 < shift["follower"] < abs(shift["cause"]), (
        "the follower has to be high in the failures, and by less than the cause is low, or a "
        "sort by sign would pass"
    )


def test_the_web_service_still_fails_often_enough_to_attribute():
    _, failed = service_draws()
    assert 0.2 < failed.mean() < 0.5, (
        "the chapter is about a design that fails in a good share of its futures. If this has "
        "moved, the chapter's argument has moved with it."
    )
