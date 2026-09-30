"""Problem 23.1 - graded by putting the answer back into the model and reading the saving.

The chapter prints the break-even transfer for the seller's own guess at the share of the spend
that scales. The answer is graded at three other shares. For each, the test builds the saving as a
function of the transfer factor, hands it to the reader, and reads the saving at the answer. No
expected value is stored: a tie is a tie wherever it falls.
"""

from __future__ import annotations

from dataclasses import replace
from functools import partial

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point

MODEL = "models/sellers_tco/model.yaml"
CUSTOMER = "models/sellers_tco/scenarios/ch22_customer.yaml"

#: The shares of the spend that scale the answer is graded at. None is a share the chapter prints.
SHARES = (0.62, 0.7, 0.85)
#: How far from zero the saving at the answer may be, in dollars.
TOLERANCE = 1.0


def saving_at(share: float, transfer: float) -> float:
    """The seller's five-year saving on ch22's customer, at the point estimate."""
    customer = load_scenario(CUSTOMER)
    overrides = {**customer.overrides, "scaling_share": share, "transfer_factor": transfer}
    return point(load_model(MODEL), replace(customer, overrides=overrides))["saving"]


@pytest.fixture(scope="module", params=SHARES)
def share(request) -> float:
    return request.param


@pytest.fixture(scope="module")
def answer(share):
    from tests.the_sellers_tco.stubs import break_even_transfer

    return break_even_transfer(partial(saving_at, share))


@pytest.mark.problem
def test_it_is_a_share_of_the_benchmark(answer, share):
    assert isinstance(answer, int | float), (
        f"return one number, the transfer factor; you returned {type(answer).__name__}"
    )
    assert 0 < answer < 2, (
        f"with {share:.0%} of the spend scaling you returned {answer}. A transfer factor is a "
        "share of the benchmark's advantage, so near one, not a percentage and not a saving."
    )


@pytest.mark.problem
def test_the_saving_is_zero_there(answer, share):
    assert isinstance(answer, int | float), "return one number, the transfer factor"
    gap = saving_at(share, answer)
    assert abs(gap) < TOLERANCE, (
        f"with {share:.0%} of the spend scaling and a transfer factor of {answer:.6f}, the "
        f"customer still {'saves' if gap > 0 else 'loses'} {abs(gap):,.0f} dollars over the "
        "horizon. The test wants the saving to within a dollar of zero."
    )


# -- scaffolding: the problem is answerable, and not by copying one number ------------------------


def test_the_saving_rises_with_the_transfer_factor(share):
    """So there is one zero, and bisection finds it."""
    values = [saving_at(share, t / 10) for t in range(2, 13)]
    assert all(b > a for a, b in zip(values, values[1:], strict=False)), values


def test_there_is_a_zero_inside_the_range_the_model_admits(share):
    low, high = load_model(MODEL).nodes["transfer_factor"].slider
    assert saving_at(share, low) < 0 < saving_at(share, high), share


def test_the_model_s_own_break_even_is_a_zero(share):
    """The model's own formula for the break-even gives no saving when put back."""
    customer = load_scenario(CUSTOMER)
    overrides = {**customer.overrides, "scaling_share": share}
    even = point(load_model(MODEL), replace(customer, overrides=overrides))["break_even_transfer"]
    assert abs(saving_at(share, even)) < TOLERANCE, (share, even)


def zero_of(share: float) -> float:
    """Bisection, as the stub suggests: the test's own check that a searcher can find it."""
    low, high = 0.2, 1.2
    for _ in range(60):
        middle = (low + high) / 2
        low, high = (middle, high) if saving_at(share, middle) < 0 else (low, middle)
    return (low + high) / 2


def test_the_answers_differ_by_share():
    """One number copied from anywhere cannot pass all three: each share's zero is a loss or a
    saving of more than the tolerance at the others."""
    zeros = [zero_of(share) for share in SHARES]
    for i, share in enumerate(SHARES):
        for j, other in enumerate(zeros):
            if i != j:
                assert abs(saving_at(share, other)) > 100 * TOLERANCE, (share, other)


def test_the_graded_shares_are_not_the_page_s():
    """The chapter prints the break-even at the seller's guess and at the bottom-up's share."""
    from bench.stamp import load_result

    printed = [c["scaling_share"] for c in load_result("seller")["summary"]["curves"]]
    for share in SHARES:
        assert all(abs(share - p) > 0.02 for p in printed), (share, printed)
