"""Problem 22.1 - graded against the toolkit's own evaluation of both quotes, on the same draws."""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate

MODEL = "models/web_service/model.yaml"
INCUMBENT = "models/web_service/scenarios/incumbent.yaml"
CHALLENGER = "models/web_service/scenarios/challenger.yaml"
REQUIRED = {"p5", "p50", "p95", "share_challenger_cheaper"}


@pytest.fixture(scope="module")
def totals():
    """Both quotes, evaluated the way the book evaluates them. Derived here, never stored."""
    model = load_model(MODEL)
    incumbent = evaluate(model, load_scenario(INCUMBENT)).samples["tco"]
    challenger = evaluate(model, load_scenario(CHALLENGER)).samples["tco"]
    return incumbent, challenger


@pytest.fixture(scope="module")
def paired(totals):
    incumbent, challenger = totals
    return challenger - incumbent


@pytest.fixture(scope="module")
def answer():
    from tests.comparing_two_tcos.stubs import paired_difference

    return paired_difference()


def width_of(values: np.ndarray) -> float:
    low, high = np.percentile(values, [5, 95])
    return float(high - low)


@pytest.mark.problem
def test_it_has_the_four_figures(answer):
    assert set(answer) == REQUIRED, sorted(set(answer) ^ REQUIRED)


@pytest.mark.problem
def test_the_percentiles_are_of_the_paired_difference(answer, paired):
    p5, p50, p95 = np.percentile(paired, [5, 50, 95])
    for key, expected in (("p5", p5), ("p50", p50), ("p95", p95)):
        assert answer[key] == pytest.approx(expected, rel=1e-3, abs=1.0), (
            f"{key}: got {answer[key]:,.0f}, the paired difference has {expected:,.0f}. "
            "Subtract sample by sample, from two evaluations that share a seed."
        )


@pytest.mark.problem
def test_you_did_not_subtract_two_independent_draws(answer, paired):
    """The wrong answer is wider, and wider by a lot: the two totals share most of their futures."""
    width, right = answer["p95"] - answer["p5"], width_of(paired)
    assert width < right * 1.5, (
        f"your interval is {width:,.0f} wide and the paired one is {right:,.0f}. An interval "
        "that much wider is the difference of two *independent* draws: the electricity price "
        "from one future against the price from another. Both designs live in the same future."
    )


@pytest.mark.problem
def test_the_share_is_a_fraction_of_the_same_futures(answer, paired):
    expected = float((paired < 0).mean())
    assert answer["share_challenger_cheaper"] == pytest.approx(expected, abs=2e-3), (
        f"got {answer['share_challenger_cheaper']:.3f}, expected {expected:.3f}: the share of "
        "futures in which the challenger's total is the lower one"
    )


# -- scaffolding: the problem is answerable, and the paired answer differs from the naive one ----


def test_both_quotes_pin_the_same_inputs():
    """Pairing only works if the same inputs are drawn on both sides, in the same order."""
    a, b = load_scenario(INCUMBENT), load_scenario(CHALLENGER)
    assert set(a.overrides) == set(b.overrides), sorted(set(a.overrides) ^ set(b.overrides))
    assert (a.seed, a.samples) == (b.seed, b.samples)


def test_the_shared_futures_really_are_shared():
    """The same draw of a shared input reaches both designs, which is what makes subtraction fair."""
    model = load_model(MODEL)
    incumbent = evaluate(model, load_scenario(INCUMBENT)).samples
    challenger = evaluate(model, load_scenario(CHALLENGER)).samples
    for name in ("electricity_price", "pue", "fully_loaded_salary", "annual_growth"):
        assert np.array_equal(incumbent[name], challenger[name]), name


def test_pairing_narrows_the_interval_materially(totals, paired):
    """If it did not, the problem would have nothing to teach."""
    incumbent, challenger = totals
    shuffled = np.random.default_rng(1).permutation(challenger)
    assert width_of(paired) < width_of(shuffled - incumbent) * 0.5, (
        width_of(paired),
        width_of(shuffled - incumbent),
    )


def test_the_ordering_is_not_settled(paired):
    """A comparison the model is sure about would be a poorer problem."""
    share = float((paired < 0).mean())
    assert 0.02 < share < 0.98, share


def test_the_incumbent_is_the_point_estimate_held_exactly():
    """Its quote pins every line at the value the reference scenario's point estimate uses."""
    from sizing.evaluate import point_value_of_input

    model = load_model(MODEL)
    reference = load_scenario("models/web_service/scenarios/reference.yaml")
    incumbent = load_scenario(INCUMBENT)
    for name, pinned in incumbent.overrides.items():
        assert pinned == pytest.approx(point_value_of_input(model.nodes[name], reference)), name


def test_the_challenger_is_sized_by_the_same_rule():
    """Its host count is what the model recommends at the point estimate for its own host."""
    from dataclasses import replace

    from sizing.evaluate import point

    model = load_model(MODEL)
    challenger = load_scenario(CHALLENGER)
    unsized = replace(
        challenger, overrides={k: v for k, v in challenger.overrides.items() if k != "hosts"}
    )
    assert challenger.overrides["hosts"] == point(model, unsized)["hosts_recommended"]
