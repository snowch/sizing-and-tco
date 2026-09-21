"""Problem 8.2 - a host lost at the busy hour.

Graded against the model's own node for the survivors' utilisation, and against ch06's division
applied to it, both worked out at test time. The sweep holds the utilisation still while the fleet
shrinks, by asking the model for a smaller fleet carrying proportionally less work. Nothing is
stored.
"""

from __future__ import annotations

import math

import pytest

from sizing.dsl import Scenario, load_model
from sizing.evaluate import point
from tests.regime_changes.stubs import after_a_host_loss

#: Fleet sizes the sweep walks down through, at the reference fleet's utilisation.
FLEETS = [89, 34, 13, 5, 3, 2]


@pytest.fixture(scope="module")
def model():
    return load_model("models/web_service/model.yaml")


@pytest.fixture(scope="module")
def values(model):
    """The model at its point: every node, one number each."""
    return point(model)


def at_fleet(model, values: dict[str, float], hosts: int) -> dict[str, float]:
    """The model's point with ``hosts`` in the fleet and the busy hour as busy as the reference's.

    The day-one request rate is scaled with the fleet, so a smaller fleet carries less work and
    its utilisation is the reference fleet's.
    """
    scaled = values["peak_request_rate_t0"] * hosts / values["hosts"]
    sweep = Scenario(
        "host-loss sweep",
        "a smaller fleet, as busy",
        overrides={"hosts": float(hosts), "peak_request_rate_t0": scaled},
    )
    return point(model, sweep)


def residence(values: dict[str, float], utilisation: float) -> float:
    """ch06's division, as the model's ``residence_time`` writes it: service time over what is
    left of the fleet."""
    return values["service_seconds"] / (1 - utilisation)


def survivors_of(values: dict[str, float], hosts: int) -> tuple[float, float]:
    return after_a_host_loss(values["utilisation"], hosts, values["service_seconds"])


@pytest.mark.problem
def test_it_agrees_with_the_model_at_the_point(values):
    utilisation, after = survivors_of(values, int(values["hosts"]))
    assert utilisation == pytest.approx(values["utilisation_after_failure"], rel=1e-9), (
        "the survivors' utilisation is the model's own `utilisation_after_failure` node: the lost "
        "host's share of the work lands on the hosts that are left"
    )
    assert after == pytest.approx(residence(values, values["utilisation_after_failure"]), rel=1e-9)


@pytest.mark.problem
def test_the_residence_time_rises_by_more_than_the_utilisation_did(values):
    """The regime change: the survivors' utilisation is arithmetic, and what it does to the
    residence time is not."""
    utilisation, after = survivors_of(values, int(values["hosts"]))
    rise_in_utilisation = utilisation / values["utilisation"]
    rise_in_residence = after / residence(values, values["utilisation"])
    assert rise_in_residence > rise_in_utilisation, (
        f"the utilisation rose by a factor of {rise_in_utilisation:.4f} and the residence time by "
        f"{rise_in_residence:.4f}. A residence time that rises by the same factor as the load is a "
        "chain of multiplications, and a queue is not one."
    )


@pytest.mark.problem
@pytest.mark.parametrize("hosts", FLEETS)
def test_a_smaller_fleet_at_the_same_utilisation(model, values, hosts):
    """Walk the fleet down. Under one the answer is the definition; at or past one there is
    nothing left to divide by, and the problem accepts a non-finite residence time or a raise."""
    survivors = at_fleet(model, values, hosts)["utilisation_after_failure"]
    if survivors < 1:
        utilisation, after = survivors_of(values, hosts)
        assert utilisation == pytest.approx(survivors, rel=1e-9)
        assert after == pytest.approx(residence(values, survivors), rel=1e-9)
        return
    try:
        _, after = survivors_of(values, hosts)
    except NotImplementedError:
        raise
    except Exception:  # raising is one of the two answers the problem accepts past one
        return
    assert not math.isfinite(after), (
        f"with {hosts} hosts the survivors are at {survivors:.2f} of capacity, past one, and the "
        f"residence time came back as {after}. There is nothing left to divide by: return "
        "something that is not finite, or raise."
    )


def test_the_reference_fleet_is_under_one_after_the_loss(values):
    """Scaffolding: there is something to compute. A fleet the loss puts past one has no residence
    time to compare."""
    assert values["utilisation_after_failure"] < 1, (
        "the reference fleet cannot lose a host and stay under one, so the problem has nothing "
        "finite to grade"
    )


def test_the_chapter_s_claim_holds_of_this_model(values):
    """Scaffolding: the residence time rises by more than the utilisation, and by a margin, from
    the model's own nodes. If the reference fleet were nearly idle the two rises would be close
    and the problem would have nothing to show."""
    extra_utilisation = values["utilisation_after_failure"] / values["utilisation"] - 1
    before = residence(values, values["utilisation"])
    after = residence(values, values["utilisation_after_failure"])
    extra_residence = after / before - 1
    assert extra_residence > 1.5 * extra_utilisation, (
        f"one host lost adds {extra_utilisation:.1%} to the utilisation and {extra_residence:.1%} "
        "to the residence time; the chapter's claim needs the second to be clearly the larger"
    )


def test_the_sweep_holds_the_utilisation_still_and_reaches_past_one(model, values):
    """Scaffolding: the sweep is at one utilisation, and its smallest fleet loses too much."""
    survivors = []
    for hosts in FLEETS:
        at = at_fleet(model, values, hosts)
        assert at["utilisation"] == pytest.approx(values["utilisation"], rel=1e-9), (
            f"scaling the request rate with the fleet should hold the utilisation still at "
            f"{hosts} hosts"
        )
        survivors.append(at["utilisation_after_failure"])
    assert survivors == sorted(survivors), "a smaller fleet loses a larger share when one host goes"
    assert survivors[0] < 1 < survivors[-1], (
        f"the sweep should start under one and end past it, and it runs {survivors[0]:.2f} to "
        f"{survivors[-1]:.2f}"
    )
