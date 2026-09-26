"""Problem 19.1 - graded against the tornado the build publishes.

The test builds the two things the reader is handed: each input's band, read from the
distribution the model file declares, and a way to ask the model for the output with some inputs
held. What it grades against is the build's own chart, read from the stamped result.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from bench.stamp import load_result
from sizing import mc
from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.which_input_is_the_answer.stubs import tornado

OUTPUT = "hosts_recommended"
#: The two ends of a band: the middle eighty per cent of what an input could be.
LOW, HIGH = 0.1, 0.9


@pytest.fixture(scope="module")
def model():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def scenario():
    return load_scenario("models/web_service/scenarios/reference.yaml")


@pytest.fixture(scope="module")
def swings(model, scenario):
    """Each input with a band, mapped to its tenth and its ninetieth percentile.

    Nothing the scenario pins, nothing an unmeasured constant blocks, and no measured constant:
    a measured constant's uncertainty is a standard error, and the build swings it by a different
    rule.
    """
    out = {}
    for name, node in model.nodes.items():
        distribution = getattr(node, "distribution", None)
        if not distribution or name in scenario.overrides or name in model.blocked():
            continue
        shape, parameters = mc.one_shape(distribution)
        low, high = mc.SHAPES[shape](np.array([LOW, HIGH]), **parameters)
        out[name] = (float(low), float(high))
    return out


@pytest.fixture(scope="module")
def output_at(model, scenario):
    """The model at a point: the named inputs held, everything else at its point value."""

    def at(held: dict[str, float]) -> float:
        return point(model, replace(scenario, overrides={**scenario.overrides, **held}))[OUTPUT]

    return at


@pytest.fixture(scope="module")
def published(model):
    """The build's bars for the inputs that declare a band. The build also swings a measured
    constant by its standard error, which is a different rule; the problem leaves that out."""
    bars = load_result("web_service-reference")["summary"]["tornado"][OUTPUT]
    return [bar for bar in bars if getattr(model.nodes[bar["node"]], "distribution", None)]


@pytest.mark.problem
def test_it_finds_the_same_inputs(swings, output_at, published):
    mine = dict(tornado(swings, output_at))
    assert set(mine) == {bar["node"] for bar in published}, (
        f"different inputs: yours {sorted(set(mine) - {b['node'] for b in published})}, "
        f"missing {sorted({b['node'] for b in published} - set(mine))}"
    )


@pytest.mark.problem
def test_every_span_matches(swings, output_at, published):
    mine = dict(tornado(swings, output_at))
    for bar in published:
        yours = mine[bar["node"]]
        assert yours == pytest.approx(bar["span"], rel=1e-6), (
            f"{bar['node']}: you make it {yours:,.0f}, "
            f"{'longer' if yours > bar['span'] else 'shorter'} than the book's bar. Hold the input "
            "at each end of its band in turn, with nothing else held, and take the distance "
            "between the two outputs. The point estimate is not one of the ends."
        )


@pytest.mark.problem
def test_it_is_sorted_longest_first(swings, output_at):
    spans = [span for _, span in tornado(swings, output_at)]
    assert spans == sorted(spans, reverse=True), (
        "the bars go longest first: sort by span, largest at the top. The order is what answers "
        "'what should I measure first'."
    )


# -- scaffolding: what the reader is handed is what the build swung ------------------------------


def test_the_bands_are_the_ones_the_build_swung(swings, published):
    """The test's bands are the build's: the same inputs, each between the same two values."""
    assert set(swings) == {bar["node"] for bar in published}
    for bar in published:
        low, high = swings[bar["node"]]
        assert (low, high) == pytest.approx((bar["low_input"], bar["high_input"])), bar["node"]


def test_the_model_answers_at_its_point(output_at, published):
    """With nothing held, the callable returns the point estimate every published bar starts at."""
    assert output_at({}) == pytest.approx(published[0]["base"])


def test_the_published_tornado_has_a_clear_winner(published):
    """Scaffolding: the chart says something.

    If the top two bars were the same length, the chapter's argument about where to spend a
    measurement would need rewriting rather than the test.
    """
    spans = sorted((bar["span"] for bar in published), reverse=True)
    assert spans[0] > 1.5 * spans[1], f"top two are {spans[0]:,.0f} and {spans[1]:,.0f}"
