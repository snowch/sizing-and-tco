"""Problem 5.2 - inverting the formula, and discovering there is no knee.

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
    assert knee_at(1.0) == pytest.approx(0.0)


@pytest.mark.problem
def test_the_knee_moves_a_long_way_for_a_small_change_in_taste():
    """The point of the problem.

    Somebody willing to accept twice the latency and somebody willing to accept ten times are
    making the same kind of decision and will size the same system very differently. There is no
    knee in the curve; there is only where each of them stopped being willing.
    """
    tolerant = knee_at(10.0)
    strict = knee_at(1.5)
    assert tolerant > strict
    assert tolerant - strict > 0.5, (
        f"between a 1.5x tolerance ({strict:.2f}) and a 10x one ({tolerant:.2f}) lies most of the "
        "useful range of a system. That gap is a decision, and it is the whole of ch10."
    )


def test_the_forward_formula_is_the_one_the_chapter_publishes():
    """Scaffolding: the oracle agrees with the book's own swept curve."""
    from bench.stamp import load_result

    for row in load_result("queueing-curve")["summary"]["curve"]:
        assert inflation_at(row["utilisation"]) == pytest.approx(row["inflation"], rel=1e-6)
