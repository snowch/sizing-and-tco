"""Problem 10.3 - graded against the mixed pool model, which reaches the answer through its own nodes."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sizing.dsl import load_model, load_scenario
from sizing.evaluate import point
from tests.bandwidth_and_the_binding_constraint.stubs import new_hosts_for_requests

MODEL = "models/mixed_pool/model.yaml"
SCENARIO = "models/mixed_pool/scenarios/reference.yaml"

#: How many old hosts stay: none, some, the book's own, and more than the load needs.
OLD_HOSTS = (0, 10, 30, 200)

#: Old hosts with more cores than the new ones: too few to carry the load, and enough. A rule
#: that only fits the book's pool, where the old hosts are the smaller, fails one of these.
LARGER_OLD = ((20, 32), (30, 32))

#: Every case, as (old hosts, cores per old host); None keeps the model's own cores.
CASES = tuple((n, None) for n in OLD_HOSTS) + LARGER_OLD

#: The model's node for each routing.
NODES = {"capacity": "new_for_requests", "equal": "new_for_requests_equal"}


@pytest.fixture(scope="module")
def model():
    return load_model(MODEL)


def model_says(model, old_hosts: int, cores_per_old_host: float | None = None) -> dict[str, float]:
    base = load_scenario(SCENARIO)
    overrides = {**base.overrides, "old_hosts": old_hosts}
    if cores_per_old_host is not None:
        overrides["cores_per_old_host"] = cores_per_old_host
    return point(model, replace(base, overrides=overrides))


def yours(values: dict[str, float], old_hosts: int, routing: str) -> float:
    return new_hosts_for_requests(
        values["busy_cores"],
        old_hosts,
        values["cores_per_old_host"],
        values["cores_per_new_host"],
        values["queueing_margin"],
        routing,
    )


@pytest.mark.problem
@pytest.mark.parametrize(("old_hosts", "old_cores"), CASES)
def test_routed_by_capacity(model, old_hosts, old_cores):
    values = model_says(model, old_hosts, old_cores)
    answer = yours(values, old_hosts, "capacity")
    # Compared outside the assert, so that a failure shows the reader's figure and not the model's.
    right = answer == pytest.approx(values[NODES["capacity"]])
    assert right, (
        f"with {old_hosts} old hosts of {values['cores_per_old_host']:.0f} cores routed by "
        f"capacity, you buy {answer} new hosts, and the model buys a different number. Routed by "
        "capacity, the old hosts' cores and the new hosts' cores add up: take what the old hosts give from what the requests need below the margin, "
        "and divide what is left by one new host's cores. Round up, and never below none."
    )


@pytest.mark.problem
@pytest.mark.parametrize(("old_hosts", "old_cores"), CASES)
def test_routed_equally(model, old_hosts, old_cores):
    values = model_says(model, old_hosts, old_cores)
    answer = yours(values, old_hosts, "equal")
    right = answer == pytest.approx(values[NODES["equal"]])
    assert right, (
        f"with {old_hosts} old hosts of {values['cores_per_old_host']:.0f} cores routed equally, "
        f"you buy {answer} new hosts, and the model buys a different number. Routed equally, "
        "every host carries the same share, so the pool is held to the cores of the smallest host "
        "in it. Ask first whether the old hosts carry the load alone; if they do, there is no new "
        "host, and none to be the smallest. If they do not, the smallest host is the smaller of "
        "the two generations: work out how many hosts of that size the requests need below the "
        "margin, then subtract the old hosts you already have. Round up."
    )


def test_the_two_routings_disagree_at_the_book_s_own_pool(model):
    """Scaffolding: the problem has two answers, not one written twice.

    If the two routings bought the same number of new hosts, the second test would pass for any
    answer to the first and the chapter's point would be gone.
    """
    values = model_says(model, 30)
    assert values[NODES["equal"]] > values[NODES["capacity"]] > 0


def test_enough_old_hosts_carry_the_load_alone(model):
    """Scaffolding: the largest case in OLD_HOSTS really is more than the load needs.

    It is the case that catches a negative answer, so it has to be one.
    """
    values = model_says(model, max(OLD_HOSTS))
    assert values[NODES["capacity"]] == 0 and values[NODES["equal"]] == 0


def test_larger_old_hosts_part_the_two_readings_of_equal_routing(model):
    """Scaffolding: the larger-old-host cases catch a rule that only fits the book's pool.

    Too few larger old hosts need new ones, and enough need none, under equal routing; the
    book's own pool never shows either, because its old hosts are the smaller.
    """
    short, enough = (model_says(model, n, cores) for n, cores in LARGER_OLD)
    assert short[NODES["equal"]] > 0 and enough[NODES["equal"]] == 0
