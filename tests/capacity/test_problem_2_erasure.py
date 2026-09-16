"""Problem 9.2 - comparing two protection schemes at equal safety.

The oracle is the definition of the schemes, computed at test time. Nothing is stored.
"""

from __future__ import annotations

import pytest

from tests.capacity.stubs import erasure_crossover

#: (data, parity) -> the replication factor that survives the same number of losses.
CASES = [(4, 2), (6, 3), (8, 2), (10, 4), (2, 1)]


def equally_safe_replication(parity: int) -> float:
    """Surviving `parity` losses needs `parity + 1` copies. That is the whole comparison."""
    return float(parity + 1)


def erasure_space(data: int, parity: int) -> float:
    return (data + parity) / data


@pytest.mark.problem
@pytest.mark.parametrize(("data", "parity"), CASES)
def test_it_matches_the_replication_that_survives_the_same_losses(data, parity):
    assert erasure_crossover(data, parity) == pytest.approx(equally_safe_replication(parity)), (
        f"an erasure code with {parity} parity shards survives {parity} losses, and so does "
        f"{parity + 1}-way replication. Those are the two things to compare on space."
    )


@pytest.mark.problem
@pytest.mark.parametrize(("data", "parity"), CASES)
def test_erasure_coding_always_wins_on_space_at_equal_safety(data, parity):
    replication = erasure_crossover(data, parity)
    assert erasure_space(data, parity) < replication, (
        f"{data}+{parity} costs {erasure_space(data, parity):.2f}x the space and the equally safe "
        f"replication costs {replication:.0f}x. It should never be the other way round."
    )


@pytest.mark.problem
def test_the_saving_grows_with_the_stripe():
    """Which is the point, and is also where the cost that is not space comes from."""
    narrow = erasure_space(4, 2) / erasure_crossover(4, 2)
    wide = erasure_space(16, 2) / erasure_crossover(16, 2)
    assert wide < narrow, (
        "spreading the same protection over more pieces costs less space per byte - and touches "
        "more machines on every read, which is ch10's problem rather than this one's"
    )


def test_replication_and_erasure_are_not_the_same_at_one_parity():
    """Scaffolding: the comparison is not trivial."""
    assert erasure_space(4, 1) < equally_safe_replication(1)
