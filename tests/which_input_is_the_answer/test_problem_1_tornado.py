"""Problem 19.1 - graded against the tornado the build publishes."""

from __future__ import annotations

import pytest

from bench.stamp import load_result
from sizing.dsl import load_model, load_scenario
from tests.which_input_is_the_answer.stubs import tornado

OUTPUT = "hosts_recommended"


@pytest.fixture(scope="module")
def model():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


@pytest.fixture(scope="module")
def published(model):
    """The build's bars for the inputs that declare a band. The build also swings a measured
    constant by its standard error, which is a different rule; the problem leaves that out."""
    bars = load_result("web_service-reference")["summary"]["tornado"][OUTPUT]
    return [bar for bar in bars if getattr(model.nodes[bar["node"]], "distribution", None)]


@pytest.mark.problem
def test_it_finds_the_same_inputs(model, scenario, published):
    mine = dict(tornado(model, scenario, OUTPUT))
    assert set(mine) == {bar["node"] for bar in published}, (
        f"different inputs: yours {sorted(set(mine) - {b['node'] for b in published})}, "
        f"missing {sorted({b['node'] for b in published} - set(mine))}"
    )


@pytest.mark.problem
def test_every_span_matches(model, scenario, published):
    mine = dict(tornado(model, scenario, OUTPUT))
    for bar in published:
        assert mine[bar["node"]] == pytest.approx(bar["span"], rel=1e-6), (
            f"{bar['node']}: the book makes it {bar['span']:,.0f} and you make "
            f"{mine[bar['node']]:,.0f}. Swing from the distribution's own percentiles, not from "
            "the slider range."
        )


@pytest.mark.problem
def test_it_is_sorted_longest_first(model, scenario):
    spans = [span for _, span in tornado(model, scenario, OUTPUT)]
    assert spans == sorted(spans, reverse=True), (
        "the ordering is the useful part - it answers 'what should I measure first'"
    )


def test_the_published_tornado_has_a_clear_winner(published):
    """Scaffolding: the chart says something.

    If the top two bars were the same length, the chapter's argument about where to spend a
    measurement would need rewriting rather than the test.
    """
    spans = sorted((bar["span"] for bar in published), reverse=True)
    assert spans[0] > 1.5 * spans[1], f"top two are {spans[0]:,.0f} and {spans[1]:,.0f}"
