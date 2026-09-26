"""Problem 6.2 - inverting the formula, and discovering there is no knee.

Graded against the forward formula rather than against a stored utilisation: whatever your
inverse returns, putting it back through the model's own curve has to give the tolerance you
asked for.
"""

from __future__ import annotations

import pytest

from tests.queueing_and_the_knee.stubs import knee_at

TOLERANCES = [1.25, 1.5, 2.0, 3.0, 5.0, 10.0]


def inflation_at(utilisation: float) -> float:
    """The forward direction, from the chapter. Used here only to check the inverse."""
    return 1.0 / (1.0 - utilisation)


@pytest.mark.problem
@pytest.mark.parametrize("tolerance", TOLERANCES)
def test_the_inverse_round_trips(tolerance):
    utilisation = knee_at(tolerance)
    assert 0.0 <= utilisation < 1.0, f"a utilisation of {utilisation} is not a utilisation"
    assert inflation_at(utilisation) == pytest.approx(tolerance, rel=1e-9), (
        f"you said requests take {tolerance}x as long at {utilisation:.4f} busy, and at that "
        f"utilisation they take {inflation_at(utilisation):.4f}x as long"
    )


@pytest.mark.problem
def test_tolerating_nothing_means_an_idle_system():
    utilisation = knee_at(1.0)
    assert utilisation == pytest.approx(0.0), (
        f"a tolerance of 1x means a request takes no longer than it would on an idle system, and "
        f"you returned {utilisation}. Check two things: that you return the share of time the "
        "system is busy, not idle, and that the tolerance multiplies the whole time in the "
        "system, waiting included."
    )


@pytest.mark.problem
def test_the_knee_moves_a_long_way_for_a_small_change_in_taste():
    """The point of the problem.

    Somebody willing to accept twice the latency and somebody willing to accept ten times are
    making the same kind of decision and will size the same system very differently. There is no
    knee in the curve; there is only where each of them stopped being willing.
    """
    strict, tolerant = knee_at(2.0), knee_at(10.0)
    for tolerance, utilisation in ((2.0, strict), (10.0, tolerant)):
        assert inflation_at(utilisation) == pytest.approx(tolerance, rel=1e-9), (
            f"knee_at({tolerance}) does not round-trip yet, so the gap between a strict engineer "
            "and a tolerant one means nothing. Get test_the_inverse_round_trips passing first."
        )
    assert tolerant > strict, "a more tolerant engineer accepts a busier system, not a quieter one"
    assert tolerant - strict > 0.35, (
        "between a 2x tolerance and a 10x one lies most of the useful range of a system. That gap "
        "is a decision, and ch11 is where it gets made."
    )


def test_the_forward_formula_is_the_one_the_chapter_publishes():
    """Scaffolding: the oracle agrees with the book's own swept curve."""
    from bench.stamp import load_result

    for row in load_result("queueing-curve")["summary"]["curve"]:
        assert inflation_at(row["utilisation"]) == pytest.approx(row["inflation"], rel=1e-6)
