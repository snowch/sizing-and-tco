"""Problem 14.2 — correlate two inputs without disturbing their distributions.

The reader's artefact is one entry for the model's ``correlations:`` block, in the file's own
form. Two assertions matter, and the second is the one that separates the right method from the
obvious one: the interval widens, and neither input's own distribution moves.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import yaml

from sizing import mc
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate

A, B, OUTPUT = "host_price", "network_price_per_host", "capex"
FRAGMENT = "tests/correlation_and_convergence/problem_2_correlation.yaml"
#: The file the page shows under the problem, editable, and writes back before grading.
EDITABLE = (FRAGMENT,)
#: The weakest correlation the problem accepts: the section says why a weak one barely shows.
AT_LEAST = 0.5


def declared() -> list[dict]:
    entries = yaml.safe_load(Path(FRAGMENT).read_text())
    assert isinstance(entries, list) and entries, "the fragment is a list of correlation entries"
    return entries


@pytest.fixture(scope="module")
def model():
    # Start from a model with no correlations at all, so the problem is about the one the reader
    # adds rather than about the ones the book already declared.
    return replace(load_model("models/web_service/model.yaml"), correlations=())


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


@pytest.fixture
def correlated(model):
    return replace(model, correlations=tuple(declared()))


def rho_declared() -> float:
    entry = next(e for e in declared() if {e.get("a"), e.get("b")} == {A, B})
    rho = entry.get("rho")
    assert isinstance(rho, int | float), "declare `rho` as a number"
    return float(rho)


@pytest.mark.problem
def test_the_entry_names_the_pair_and_a_strong_enough_rho():
    assert any({e.get("a"), e.get("b")} == {A, B} for e in declared()), (
        f"the entry correlates {A} with {B}"
    )
    assert AT_LEAST <= rho_declared() < 1.0, (
        "a rank correlation of at least a half, and below one: the section says why a weak one "
        "barely shows, and one is not a correlation but a copy"
    )


@pytest.mark.problem
def test_the_interval_widens(model, correlated, scenario):
    before = mc.half_width(evaluate(model, scenario).samples[OUTPUT])
    after = mc.half_width(evaluate(correlated, scenario).samples[OUTPUT])
    assert after > before * 1.02, (
        f"the half-width went from {before:,.0f} to {after:,.0f}. Two prices that move together "
        "cannot cancel each other out, so the interval on their sum has to get wider — if it did "
        "not, the correlation did not reach the sampler."
    )


@pytest.mark.problem
def test_the_marginals_do_not_move(model, correlated, scenario):
    plain = evaluate(model, scenario).samples
    together = evaluate(correlated, scenario).samples
    for name in (A, B):
        for percentile in (5, 25, 50, 75, 95):
            was = float(np.percentile(plain[name], percentile))
            now = float(np.percentile(together[name], percentile))
            assert abs(now - was) < 0.02 * abs(was), (
                f"{name}: its p{percentile} moved from {was:.4g} to {now:.4g}. Correlating should "
                "only change which draws line up with which — if a marginal moved, the values "
                "were adjusted rather than reordered, and you have overwritten the distribution "
                "the model chose."
            )


@pytest.mark.problem
def test_the_correlation_is_the_one_that_was_declared(correlated, scenario):
    samples = evaluate(correlated, scenario).samples
    ranks = [np.argsort(np.argsort(samples[name])) for name in (A, B)]
    measured = float(np.corrcoef(*ranks)[0, 1])
    assert abs(measured - rho_declared()) < 0.05, (
        f"declared a rank correlation of {rho_declared()}, measured {measured:.3f}. A small "
        "consistent shortfall means the attenuation has not been corrected for — see the section "
        "on it."
    )


@pytest.mark.problem
def test_the_correlation_says_why():
    """The chapter calls the reason required: a coefficient with nothing attached is the section's
    own example of a number nobody can argue with."""
    entry = next(e for e in declared() if {e.get("a"), e.get("b")} == {A, B})
    assert str(entry.get("because") or "").strip(), (
        "say why these two move together, in the entry's `because`. The chapter calls the reason "
        "the required column."
    )


def test_the_two_inputs_both_feed_the_output(model):
    """Scaffolding: the problem's premise holds."""
    feeding = model.ancestors(OUTPUT)
    assert A in feeding and B in feeding, (
        f"{A} and {B} must both feed {OUTPUT} or correlating them cannot widen its interval"
    )
