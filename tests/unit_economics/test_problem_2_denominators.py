"""Problem 17.2 - four defensible denominators, four different answers.

Every expected value is computed from the samples at test time. The test hands the stub the two
things the four need beyond the samples, the model's day-one holding and the months in the
horizon, as plain numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import evaluate
from tests.unit_economics.stubs import denominators

KEYS = ("at_horizon", "at_start", "average_linear", "per_sample")
MONTHS_PER_YEAR = 12.0


@pytest.fixture(scope="module")
def evaluated():
    return evaluate(
        load_model("models/web_service/model.yaml"),
        load_scenario("models/web_service/scenarios/reference.yaml"),
    )


@pytest.fixture(scope="module")
def given(evaluated):
    """What the stub is handed: the two bags, day one's holding and the months in the horizon."""
    return (
        evaluated.samples["stored_data"],
        evaluated.samples["tco"],
        evaluated.point["stored_data_t0"],
        evaluated.point["horizon"] * MONTHS_PER_YEAR,
    )


def _mistakes(held, total, at_start, months) -> dict[str, float]:
    """The wrong turns a hint can name, each computed from the same samples as the right one."""

    def median(values) -> float:
        return float(np.median(values))

    return {
        "medians first, at the horizon": median(total) / median(held) / months,
        "divided first, at the horizon": median(total / held / months),
        "divided first, over the straight line": median(total / ((at_start + held) / 2) / months),
        "the mean of the ratios": float(np.mean(total / held / months)),
        "means instead of medians": float(np.mean(total)) / float(np.mean(held)) / months,
    }


def _named(answer: float, expected: float, given, hints: dict[str, str], default: str) -> str:
    """The hint for the mistake the answer matches, or the key's definition if it matches none.

    Only called when the answer is wrong, and never says what the right answer is.
    """
    held, total, at_start, months = given
    if answer == pytest.approx(expected * months, rel=1e-6):
        return "yours is not per month: divide by the months you were handed."
    mistakes = _mistakes(held, total, at_start, months)
    for name, value in mistakes.items():
        if name in hints and answer == pytest.approx(value, rel=1e-6):
            return hints[name]
    return default


@pytest.mark.problem
def test_all_four_are_returned(given):
    answer = denominators(*given)
    assert set(answer) == set(KEYS), f"expected {sorted(KEYS)}, got {sorted(answer)}"
    assert all(np.isfinite(v) and v > 0 for v in answer.values()), (
        "each of the four should be a single positive number, a cost per terabyte per month"
    )


@pytest.mark.problem
def test_the_per_sample_one_is_the_median_of_ratios(given):
    held, total, _, months = given
    answer = denominators(*given)["per_sample"]
    expected = float(np.median(total / held / months))
    assert answer == pytest.approx(expected, rel=1e-6), _named(
        answer,
        expected,
        given,
        {
            "medians first, at the horizon": (
                "you took the medians first and divided one by the other. Divide each total by "
                "what its own sample holds at the horizon first, then take the median."
            ),
            "divided first, over the straight line": (
                "right order, wrong holding: that is the model's own figure, over the straight "
                "line between day one and the horizon. per_sample divides by what each sample "
                "holds at the horizon."
            ),
            "the mean of the ratios": (
                "right order, but you took the mean of the ratios. The key asks for their median."
            ),
        },
        "divide each total by what that same sample holds at the horizon, per month, then take "
        "the median of those ratios.",
    )


@pytest.mark.problem
def test_the_horizon_one_is_the_ratio_of_medians(given):
    held, total, _, months = given
    answer = denominators(*given)["at_horizon"]
    expected = float(np.median(total)) / float(np.median(held)) / months
    assert answer == pytest.approx(expected, rel=1e-6), _named(
        answer,
        expected,
        given,
        {
            "divided first, at the horizon": (
                "you divided sample by sample first, which is per_sample's order. at_horizon "
                "takes the median total and the median holding first."
            ),
            "means instead of medians": "you took means. at_horizon divides the medians.",
        },
        "the median total over the median of what is held at the horizon, divided by the months.",
    )


@pytest.mark.problem
def test_the_start_one_divides_by_day_one(given):
    _, total, at_start, months = given
    expected = float(np.median(total)) / at_start / months
    assert denominators(*given)["at_start"] == pytest.approx(expected, rel=1e-6), (
        "the day-one figure is the stored_at_start you were handed, and the months are the "
        "horizon's"
    )


@pytest.mark.problem
def test_the_linear_one_divides_by_the_mean_of_the_two(given):
    held, total, at_start, months = given
    answer = denominators(*given)["average_linear"]
    expected = float(np.median(total)) / ((at_start + float(np.median(held))) / 2.0) / months
    assert answer == pytest.approx(expected, rel=1e-6), _named(
        answer,
        expected,
        given,
        {
            "divided first, over the straight line": (
                "you divided sample by sample first: that is the model's own figure. "
                "average_linear takes the median total over the straight-line holding of the "
                "medians."
            ),
        },
        "the median total over the mean of day one's holding and the median holding at the "
        "horizon: a straight line between the two ends, per month.",
    )


@pytest.mark.problem
def test_they_are_not_close_together(given):
    """The point of the problem."""
    answer = denominators(*given)
    values = list(answer.values())
    assert max(values) / min(values) > 1.5, (
        f"four defensible denominators giving {min(values):.2f} to {max(values):.2f} is the "
        "finding, and most of it is day one against the rest: a fleet bought for growth looks "
        "dear per terabyte on the day it is installed. If yours are all within a few per cent, "
        "check that at_start is using the day-one figure and not the horizon one."
    )


@pytest.mark.problem
def test_day_one_gives_the_most_expensive_answer(given):
    """A fleet bought for growth looks dreadful per terabyte on the day it is installed."""
    answer = denominators(*given)
    assert answer["at_start"] == max(answer.values()), (
        "at_start should be the largest of the four: day one holds the least, so the same total "
        "is spread over the fewest terabytes"
    )


def test_the_two_holdings_differ(given):
    """Scaffolding: the problem is about something."""
    held, _, at_start, _ = given
    ratio = float(np.median(held)) / at_start
    assert ratio > 1.5, f"what is held only grows by {ratio:.2f}x over the horizon"


def test_each_hint_names_one_mistake(given):
    """Scaffolding: no two of the answers a hint tells apart agree to the tests' tolerance."""
    held, total, at_start, months = given
    # The first two mistakes are at_horizon's and per_sample's right answers, so with
    # average_linear's this covers every value a hint is chosen between.
    candidates = {
        "average_linear": float(np.median(total))
        / ((at_start + float(np.median(held))) / 2.0)
        / months,
        **_mistakes(held, total, at_start, months),
    }
    values = sorted(candidates.values())
    closest = min(b / a - 1 for a, b in zip(values, values[1:], strict=False))
    assert closest > 1e-4, "two of the answers the hints tell apart are too close to tell apart"


def test_the_straight_line_overstates_what_is_held(given):
    """Scaffolding for the docstring and the page: the chord lies above a compounding curve.

    Held on day one at a and at the horizon at b, a steadily compounding holding averages
    (b - a) / ln(b / a) over the horizon. The straight line averages (a + b) / 2, never less.
    """
    held, _, at_start, _ = given
    moved = ~np.isclose(held, at_start)
    a, b = at_start, held[moved]
    assert np.all((a + b) / 2 >= (b - a) / np.log(b / a))


def test_the_models_own_figure_divides_first_over_the_straight_line(evaluated, given):
    """Scaffolding for the page: its per-stored figure is none of the four keys."""
    held, total, at_start, months = given
    ours = total / ((at_start + held) / 2) / months
    assert np.allclose(evaluated.samples["cost_per_stored_tb_month"], ours, rtol=1e-9)
