"""Problem 22.1 - graded against the toolkit's own evaluation of both quotes, on the same draws.

The test evaluates both quotes here and hands the reader the two arrays of five-year totals. What
it grades against is its own subtraction of the same two arrays, derived at test time and never
stored. It grades twice: on every future, which is what the chapter's table prints, and on the
first few thousand of the same futures, which the chapter does not print, so a figure copied off
the page does not pass.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate

MODEL = "models/web_service/model.yaml"
INCUMBENT = "models/web_service/scenarios/incumbent.yaml"
CHALLENGER = "models/web_service/scenarios/challenger.yaml"
REQUIRED = {"p5", "p50", "p95", "share_challenger_cheaper"}
#: The second set of futures the answer is graded on: the first this many of the same draws.
SUBSET = 10_000
#: How close a percentile must be, relative and in dollars, and how close the share must be.
REL, ABS, SHARE = 1e-3, 1.0, 2e-3
LEVELS = {"p5": 5, "p50": 50, "p95": 95}


@pytest.fixture(scope="module")
def totals():
    """Both quotes, evaluated the way the book evaluates them. Derived here, never stored."""
    model = load_model(MODEL)
    incumbent = evaluate(model, load_scenario(INCUMBENT)).samples["tco"]
    challenger = evaluate(model, load_scenario(CHALLENGER)).samples["tco"]
    return incumbent, challenger


@pytest.fixture(scope="module", params=("every future", "a subset of the futures"))
def case(request, totals):
    incumbent, challenger = totals
    if request.param != "every future":
        incumbent, challenger = incumbent[:SUBSET], challenger[:SUBSET]
    return incumbent, challenger


@pytest.fixture(scope="module")
def paired(case):
    incumbent, challenger = case
    return challenger - incumbent


@pytest.fixture(scope="module")
def answer(case):
    from tests.comparing_two_tcos.stubs import paired_difference

    # Copies, so an answer that subtracts in place cannot change what it is graded against.
    incumbent, challenger = case
    return paired_difference(incumbent.copy(), challenger.copy())


def width_of(values: np.ndarray) -> float:
    low, high = np.percentile(values, [5, 95])
    return float(high - low)


def close(value: float, target: float) -> bool:
    return float(value) == pytest.approx(float(target), rel=REL, abs=ABS)


def what_went_wrong(key: str, value: float, case, paired: np.ndarray) -> str:
    """Name the mistake an answer looks like, without saying what the right answer is."""
    incumbent, challenger = case
    level = LEVELS[key]
    if close(value, -np.percentile(paired, 100 - level)):
        return (
            "the sign is the wrong way round. The difference is the challenger's total minus "
            "the incumbent's, so a future in which the challenger is cheaper comes out negative."
        )
    if close(value, np.percentile(challenger, level) - np.percentile(incumbent, level)):
        return (
            "that is one total's percentile minus the other's, each taken on its own. It is not "
            "a percentile of the difference, and here it comes out narrower. Subtract the arrays "
            "entry by entry first, then take the percentiles of the result."
        )
    if key != "p50" and close(
        value, np.percentile(challenger, level) - np.percentile(incumbent, 100 - level)
    ):
        return (
            "that is the end of one interval minus the opposite end of the other, as if the two "
            "totals could each be anywhere in their own intervals. Subtract the arrays entry by "
            "entry first, then take the percentiles of the result."
        )
    return (
        "it is not a percentile of the difference taken future by future. Subtract the arrays "
        "entry by entry, the i-th total from the i-th total, then take the percentiles."
    )


@pytest.mark.problem
def test_it_has_the_four_figures(answer):
    assert set(answer) == REQUIRED, sorted(set(answer) ^ REQUIRED)


@pytest.mark.problem
def test_the_percentiles_are_of_the_paired_difference(answer, case, paired):
    for key, level in LEVELS.items():
        expected = np.percentile(paired, level)
        assert close(answer[key], expected), (
            f"{key}: you returned {float(answer[key]):,.0f}, and "
            + what_went_wrong(key, answer[key], case, paired)
        )


@pytest.mark.problem
def test_you_did_not_subtract_two_independent_draws(answer, paired):
    """The wrong answer is wider, and wider by a lot: the two totals share most of their futures."""
    width = answer["p95"] - answer["p5"]
    assert width < width_of(paired) * 1.5, (
        f"your interval is {width:,.0f} wide, more than half as wide again as the difference "
        "taken future by future. An interval that wide is the difference of two *independent* "
        "draws, the electricity price from one future against the price from another, or of "
        "the two intervals' opposite ends. Both designs live in the same future."
    )


@pytest.mark.problem
def test_the_share_is_a_fraction_of_the_same_futures(answer, paired):
    expected = float((paired < 0).mean())
    share = float(answer["share_challenger_cheaper"])
    if share == pytest.approx(expected * 100, abs=SHARE * 100):
        hint = "the share is a fraction between 0 and 1, not a percentage."
    elif share == pytest.approx(1 - expected, abs=SHARE):
        hint = (
            "that is the share of futures in which the incumbent is cheaper. The challenger is "
            "cheaper where challenger minus incumbent is below zero."
        )
    else:
        hint = (
            "count the futures in which the challenger's total is below the incumbent's, the "
            "same future on both sides, and divide by the number of futures."
        )
    assert share == pytest.approx(expected, abs=SHARE), f"you returned {share:.3f}: {hint}"


# -- scaffolding: the problem is answerable, and the paired answer differs from the naive one ----


def test_both_quotes_pin_the_same_inputs():
    """Pairing only works if the same inputs are drawn on both sides, in the same order."""
    a, b = load_scenario(INCUMBENT), load_scenario(CHALLENGER)
    assert set(a.overrides) == set(b.overrides), sorted(set(a.overrides) ^ set(b.overrides))
    assert (a.seed, a.samples) == (b.seed, b.samples)


def test_the_shared_futures_really_are_shared():
    """The same draw of a shared input reaches both designs, which makes the subtraction fair."""
    model = load_model(MODEL)
    incumbent = evaluate(model, load_scenario(INCUMBENT)).samples
    challenger = evaluate(model, load_scenario(CHALLENGER)).samples
    for name in ("electricity_price", "pue", "fully_loaded_salary", "annual_growth"):
        assert np.array_equal(incumbent[name], challenger[name]), name


def test_the_two_arrays_are_one_future_per_entry(totals):
    """The reader is handed one total per sampled future on each side, the same count on both."""
    incumbent, challenger = totals
    assert incumbent.shape == challenger.shape and incumbent.ndim == 1, (
        incumbent.shape,
        challenger.shape,
    )
    assert np.all(incumbent > 0) and np.all(challenger > 0)
    assert incumbent.size > SUBSET


def test_the_figures_on_the_page_do_not_pass_on_the_subset(totals):
    """The chapter prints the answer over every future. Over the subset, every graded figure
    lands outside the tolerance of that answer, so copying the table cannot pass both."""
    incumbent, challenger = totals
    every, some = challenger - incumbent, (challenger - incumbent)[:SUBSET]
    for level in LEVELS.values():
        assert not close(np.percentile(some, level), np.percentile(every, level)), level
    assert abs(float((some < 0).mean()) - float((every < 0).mean())) > SHARE


def test_the_diagnoses_do_not_fire_on_a_right_answer(case, paired):
    """Each mistake the test names is a different number from the right answer, so a reader who
    is nearly right is never told they made one of them."""
    incumbent, challenger = case
    for key, level in LEVELS.items():
        right = np.percentile(paired, level)
        assert not close(right, -np.percentile(paired, 100 - level)), key
        assert not close(right, np.percentile(challenger, level) - np.percentile(incumbent, level))
        if key != "p50":
            assert not close(
                right, np.percentile(challenger, level) - np.percentile(incumbent, 100 - level)
            ), key
    share = float((paired < 0).mean())
    assert share != pytest.approx(1 - share, abs=SHARE)


def test_pairing_narrows_the_interval_materially(totals):
    """If it did not, the problem would have nothing to teach."""
    incumbent, challenger = totals
    paired = challenger - incumbent
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
