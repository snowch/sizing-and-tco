"""Problem 9.2 - comparing two protection schemes at equal safety.

The oracle is the definition of the schemes, computed at test time. Nothing is stored.
"""

from __future__ import annotations

import pytest

from tests.capacity.stubs import replication_as_safe_as

#: (data, parity) -> the replication factor that survives the same number of losses.
CASES = [(4, 2), (6, 3), (8, 2), (10, 4), (2, 1)]


def equally_safe_replication(parity: int) -> float:
    """Surviving `parity` losses needs `parity + 1` copies. That is the whole comparison."""
    return float(parity + 1)


def erasure_space(data: int, parity: int) -> float:
    return (data + parity) / data


def losses(count: int) -> str:
    return f"{count} lost shard" if count == 1 else f"{count} lost shards"


def diagnosis(data: int, parity: int, returned: float) -> str:
    """What a wrong answer most likely returned instead, without saying what is right."""
    if returned == pytest.approx(erasure_space(data, parity)):
        return (
            f"that is what the {data}+{parity} code costs in space. The question is how many "
            "whole copies are as safe as it is."
        )
    if returned == pytest.approx(parity):
        return (
            f"that is how many losses the {data}+{parity} code survives. The question is how "
            "many whole copies it takes to survive as many."
        )
    return (
        f"a {data}+{parity} code survives {losses(parity)}. Return how many whole copies it "
        "takes to survive as many losses."
    )


@pytest.mark.problem
@pytest.mark.parametrize(("data", "parity"), CASES)
def test_it_matches_the_replication_that_survives_the_same_losses(data, parity):
    returned = replication_as_safe_as(data, parity)
    if returned != pytest.approx(equally_safe_replication(parity)):
        pytest.fail(diagnosis(data, parity, returned), pytrace=False)


@pytest.mark.problem
@pytest.mark.parametrize(("data", "parity"), CASES)
def test_erasure_coding_always_wins_on_space_at_equal_safety(data, parity):
    replication = replication_as_safe_as(data, parity)
    assert erasure_space(data, parity) < replication, (
        f"{data}+{parity} costs {erasure_space(data, parity):.2f}x the space and your "
        f"replication factor costs {replication:g}x. At equal safety the code always costs less."
    )


@pytest.mark.problem
def test_the_saving_grows_with_the_stripe():
    """Which is the point, and is also where the cost that is not space comes from."""
    assert replication_as_safe_as(4, 2) == pytest.approx(replication_as_safe_as(16, 2)), (
        "the replication that matches an erasure code's safety depends on its parity alone. The "
        "stripe width changes what the code costs, not what it survives."
    )
    narrow = erasure_space(4, 2) / replication_as_safe_as(4, 2)
    wide = erasure_space(16, 2) / replication_as_safe_as(16, 2)
    assert wide < narrow, (
        "spreading the same protection over more pieces costs less space per byte, and touches "
        "more machines on every read: a cost no model in this book has a term for"
    )


def test_replication_and_erasure_are_not_the_same_at_one_parity():
    """Scaffolding: the comparison is not trivial."""
    assert erasure_space(4, 1) < equally_safe_replication(1)


def test_the_likely_mistakes_get_their_own_messages():
    """Scaffolding: returning the space cost and returning the parity are told apart from each
    other and from the general message, in every case the test uses."""
    for data, parity in CASES:
        space = diagnosis(data, parity, erasure_space(data, parity))
        count = diagnosis(data, parity, float(parity))
        other = diagnosis(data, parity, -1.0)
        assert len({space, count, other}) == 3, (data, parity)
