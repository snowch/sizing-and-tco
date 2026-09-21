"""Problem 14.2 — correlate two inputs without disturbing their distributions.

Two assertions, and the second is the one that separates the right method from the obvious one.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.correlation_and_convergence.stubs import correlated_model

A, B, OUTPUT = "host_price", "network_price_per_host", "capex"
RHO = 0.85


@pytest.fixture(scope="module")
def model():
    from dataclasses import replace

    # Start from a model with no correlations at all, so the problem is about the one the reader
    # adds rather than about the ones the book already declared.
    return replace(load_model("models/web_service/model.yaml"), correlations=())


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


@pytest.mark.problem
def test_the_interval_widens(model, scenario):
    before = mc.half_width(evaluate(model, scenario).samples[OUTPUT])
    after = mc.half_width(evaluate(correlated_model(model, A, B, RHO), scenario).samples[OUTPUT])
    assert after > before * 1.02, (
        f"the half-width went from {before:,.0f} to {after:,.0f}. Two prices that move together "
        "cannot cancel each other out, so the interval on their sum has to get wider — if it did "
        "not, the correlation did not reach the sampler."
    )


@pytest.mark.problem
def test_the_marginals_do_not_move(model, scenario):
    plain = evaluate(model, scenario).samples
    correlated = evaluate(correlated_model(model, A, B, RHO), scenario).samples
    for name in (A, B):
        for percentile in (5, 25, 50, 75, 95):
            was = float(np.percentile(plain[name], percentile))
            now = float(np.percentile(correlated[name], percentile))
            assert abs(now - was) < 0.02 * abs(was), (
                f"{name}: its p{percentile} moved from {was:.4g} to {now:.4g}. Correlating should "
                "only change which draws line up with which — if a marginal moved, the values "
                "were adjusted rather than reordered, and you have overwritten the distribution "
                "the model chose."
            )


@pytest.mark.problem
def test_the_correlation_is_the_one_that_was_asked_for(model, scenario):
    samples = evaluate(correlated_model(model, A, B, RHO), scenario).samples
    ranks = [np.argsort(np.argsort(samples[name])) for name in (A, B)]
    measured = float(np.corrcoef(*ranks)[0, 1])
    assert abs(measured - RHO) < 0.05, (
        f"asked for a rank correlation of {RHO}, measured {measured:.3f}. A small consistent "
        "shortfall means the attenuation has not been corrected for — see the section on it."
    )


@pytest.mark.problem
def test_the_correlation_says_why(model):
    """The chapter calls the reason required: a coefficient with nothing attached is the section's
    own example of a number nobody can argue with."""
    added = [
        c
        for c in correlated_model(model, A, B, RHO).correlations
        if {c.get("a"), c.get("b")} == {A, B}
    ]
    assert added, f"no correlation between {A} and {B} was declared"
    assert all(str(c.get("because", "")).strip() for c in added), (
        "say why these two move together, in the correlation's `because`. The chapter calls the "
        "reason the required column."
    )


def test_the_two_inputs_both_feed_the_output(model):
    """Scaffolding: the problem's premise holds."""
    feeding = model.ancestors(OUTPUT)
    assert A in feeding and B in feeding, (
        f"{A} and {B} must both feed {OUTPUT} or correlating them cannot widen its interval"
    )
