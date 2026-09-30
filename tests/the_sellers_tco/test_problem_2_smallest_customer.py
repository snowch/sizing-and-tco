"""Problem 23.2 - graded by putting the answer back into the model, or by the model's own margin.

Three cases, each a share of the spend that scales and a transfer factor. In two, every host the
customer runs saves money each year after the move, so some customer size pays for the move, and
the answer is graded by reading the saving there. In the third, every host loses money each year,
no size pays, and the right answer is ``None``. Nothing is stored: which case is which is read
off the model's margin at test time.
"""

from __future__ import annotations

from dataclasses import replace
from functools import partial

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point

MODEL = "models/sellers_tco/model.yaml"
CUSTOMER = "models/sellers_tco/scenarios/ch22_customer.yaml"

#: (share of the spend that scales, transfer factor). The chapter prints none of these.
CASES = ((0.9, 0.9), (0.7, 1.0), (0.5, 0.8))
#: How far from zero the saving at the answer may be, in dollars.
TOLERANCE = 1.0


def values(case: tuple[float, float], hosts: float | None = None) -> dict:
    share, transfer = case
    customer = load_scenario(CUSTOMER)
    overrides = {**customer.overrides, "scaling_share": share, "transfer_factor": transfer}
    if hosts is not None:
        overrides["usage_hosts"] = hosts
    return point(load_model(MODEL), replace(customer, overrides=overrides))


def saving_for(case: tuple[float, float], hosts: float) -> float:
    """The seller's five-year saving for a customer running ``hosts`` hosts."""
    return values(case, hosts)["saving"]


def pays(case: tuple[float, float]) -> bool:
    """Whether each host saves anything a year: the model's own margin, read at test time."""
    return values(case)["margin_per_host_year"] > 0


@pytest.fixture(scope="module", params=CASES, ids=lambda c: f"share {c[0]}, transfer {c[1]}")
def case(request) -> tuple[float, float]:
    return request.param


@pytest.fixture(scope="module")
def answer(case):
    from tests.the_sellers_tco.stubs import smallest_customer

    return smallest_customer(partial(saving_for, case))


@pytest.mark.problem
def test_none_exactly_when_no_customer_pays(answer, case):
    share, transfer = case
    if pays(case):
        assert answer is not None, (
            f"with {share:.0%} of the spend scaling and {transfer:.0%} of the benchmark carrying "
            "over, each host saves money every year after the move, so a large enough customer "
            "pays for it. Return the size at which it does."
        )
    else:
        assert answer is None, (
            f"with {share:.0%} of the spend scaling and {transfer:.0%} of the benchmark carrying "
            f"over, you returned {answer!r}. Each host loses money every year here, so the larger "
            "the customer, the larger the loss, and no size pays for the move. A negative number "
            "of hosts is not a customer: return None."
        )


@pytest.mark.problem
def test_the_saving_is_zero_there(answer, case):
    if not pays(case) or answer is None:
        return
    assert isinstance(answer, int | float), "return a number of hosts, or None"
    gap = saving_for(case, answer)
    assert abs(gap) < TOLERANCE, (
        f"a customer running {answer:,.2f} hosts still {'saves' if gap > 0 else 'loses'} "
        f"{abs(gap):,.0f} dollars over the horizon. The test wants the saving within a dollar of "
        "zero. It is a straight line in the number of hosts: two evaluations fix it."
    )


# -- scaffolding: the problem is answerable, and each kind of case is there -----------------------


def test_both_kinds_of_case_are_graded():
    assert any(pays(c) for c in CASES) and not all(pays(c) for c in CASES)


def test_the_saving_is_a_straight_line_in_hosts(case):
    a, b, c = (saving_for(case, h) for h in (10.0, 50.0, 90.0))
    assert abs((c - b) - (b - a)) < 1e-6 * max(1.0, abs(a), abs(c)), (a, b, c)


def test_the_model_s_own_break_even_is_a_zero(case):
    """Where some size pays, the model's formula gives it, and the saving there is zero."""
    if not pays(case):
        return
    even = values(case)["break_even_usage"]
    assert even > 0 and abs(saving_for(case, even)) < TOLERANCE, even


def test_where_none_pays_the_formula_goes_negative(case):
    """The trap: the formula still returns a number when nothing pays, and it is negative."""
    if pays(case):
        return
    assert values(case)["break_even_usage"] < 0


def test_the_answers_differ_between_paying_cases():
    evens = [values(c)["break_even_usage"] for c in CASES if pays(c)]
    assert len(evens) >= 2 and abs(evens[0] - evens[1]) > 1, evens
