"""Problem 20.3 — find the missing node.

The oracle is an observation the model does not contain: what the service cost per month, as the
average of twelve invoices. It is invented for this exercise, and it lives here, in the file that
grades against it. ``bench/run_missing_node.py`` reads it from this file for ch20's table, beside
what the model says, and stamps it with a condition saying it is invented, so the page and this
test cannot disagree and nobody can mistake it for an observation of anything.
"""

from __future__ import annotations

import numpy as np
import pytest

from sizing import mc, units
from sizing.dsl import Derived, Input, load_model, load_scenario
from sizing.evaluate import evaluate

FIXTURE = "tests/the_missing_node/fixtures/model.yaml"
REPAIRED = "tests/the_missing_node/fixtures/repaired.yaml"
#: The file the page shows under the problem, editable, and writes back before grading.
EDITABLE = (REPAIRED,)
SCENARIO = "tests/the_missing_node/fixtures/scenarios/reference.yaml"
OUTPUT = "monthly_cost"

#: What the service cost per month, averaged over twelve invoices. Invented for this exercise.
#: The model as shipped cannot reach it, and widening its inputs is not allowed to be the way you
#: get there. ``bench/run_missing_node.py`` reads this line as source for ch20's table, so it
#: stays a plain number, and changing it means re-running that runner.
OBSERVED_MONTHLY = 38_200.0

#: How far the percentiles of an untouched derived node may wander between the two runs. The
#: repair adds an uncertain input, which changes which random draws the sampler hands to the
#: old ones, so their percentiles move by sampling noise and nothing else. A plug written into an
#: old formula moves them by far more than this.
NOISE = 0.05


@pytest.fixture(scope="module")
def original():
    return load_model(FIXTURE)


@pytest.fixture(scope="module")
def scenario():
    return load_scenario(SCENARIO)


def _interval(model, scenario):
    return mc.interval(evaluate(model, scenario).samples[OUTPUT])


def _is_money(unit: str) -> bool:
    return "[currency]" in units.dimensionality(unit)


@pytest.mark.problem
def test_no_existing_input_was_changed(original):
    """The chapter's second trap, ruled out.

    Not widened, not shifted, not re-centred: an input the model already had keeps its unit, its
    value and its distribution. Making a model vaguer until it stops contradicting the evidence is
    the same error with a wider error bar on it, and moving a distribution sideways is the same
    error again with the invoice copied into an input.
    """
    repaired = load_model(REPAIRED)
    for name, node in original.nodes.items():
        if not isinstance(node, Input):
            continue
        assert name in repaired.nodes, f"{name}: an input the model had is gone"
        after = repaired.nodes[name]
        assert isinstance(after, Input), f"{name}: was an input and is now a {after.kind} node"
        was = (node.unit, node.value, node.distribution)
        now = (after.unit, after.value, after.distribution)
        assert now == was, (
            f"{name}: its unit, value or distribution changed, from {was} to {now}. A model that "
            "disagrees with an invoice is not fixed by adjusting the numbers in it. The inputs "
            "stay as they were; the repair is a line the model did not have."
        )


@pytest.mark.problem
def test_the_repair_adds_a_quantity_and_prices_it(original):
    """A cost line is a quantity times what it is billed at, and both halves have to be nodes.

    A new input that is only a sum of money a month is a plug: the invoice, written into the
    model under another name. So at least one added input has to be the thing the missing line
    is billed on, and a new derived node has to turn it into money and feed the total.
    """
    repaired = load_model(REPAIRED)
    added = {name: repaired.nodes[name] for name in set(repaired.nodes) - set(original.nodes)}
    assert added, (
        "the repair has to add something. A model that disagrees with an invoice is not fixed by "
        "adjusting the numbers in it."
    )
    for name, node in sorted(added.items()):
        assert node.unit, f"{name}: every node declares a unit"
        if isinstance(node, Input):
            assert node.provenance and node.provenance.source.strip(), (
                f"{name}: every input says where it came from, including one you have just "
                "invented — especially one you have just invented."
            )
    quantities = sorted(
        name for name, node in added.items() if isinstance(node, Input) and not _is_money(node.unit)
    )
    assert quantities, (
        "every input you added is an amount of money. A missing cost line is billed on "
        "something — bytes moved, requests served, seats, whatever it is — and the model has to "
        "name that quantity as an input of its own, with its unit and its source, before it can "
        "price it. An input that is only dollars a month is a plug."
    )
    money = f"{original.currency}/month"
    lines = sorted(
        name
        for name, node in added.items()
        if isinstance(node, Derived)
        and units.compatible(node.unit, money)
        and set(quantities) & repaired.ancestors(name)
    )
    assert lines, (
        f"none of the nodes you added is a cost in {money} worked out from "
        f"{', '.join(quantities)}. The new line has to be a derived node whose formula prices "
        "the quantity, so that the model says what it is paying for and at what rate."
    )
    reaching = [name for name in lines if name in repaired.ancestors(OUTPUT)]
    assert reaching, (
        f"{', '.join(lines)} does not feed {OUTPUT}. A cost line the total does not add up is "
        "not in the model yet."
    )


@pytest.mark.problem
def test_nothing_old_moved_except_what_the_new_line_feeds(original, scenario):
    """The repair is a new line, not a thumb on an old one.

    A derived node with nothing new upstream of it is the same arithmetic over the same inputs,
    so its percentiles land where they did, give or take sampling noise. If one moved, a formula
    the model already had was changed to carry the gap, which is the plug in a different place.
    """
    repaired = load_model(REPAIRED)
    added = set(repaired.nodes) - set(original.nodes)
    before = evaluate(original, scenario).samples
    after = evaluate(repaired, scenario).samples
    for name, node in original.nodes.items():
        if not isinstance(node, Derived) or added & repaired.ancestors(name):
            continue
        assert name in repaired.nodes and name in after, f"{name}: a node the model had is gone"
        was = np.percentile(before[name], [5, 50, 95])
        now = np.percentile(after[name], [5, 50, 95])
        assert np.allclose(now, was, rtol=NOISE), (
            f"{name}: nothing new feeds it, and its p5, p50 and p95 went from {was.round(0)} to "
            f"{now.round(0)}. An old line was altered to reach the invoice. The repair is a line "
            "the model did not have, and the lines it had stay as they were."
        )


@pytest.mark.problem
def test_the_observation_lands_inside_the_interval(original, scenario):
    repaired = load_model(REPAIRED)
    low, high = _interval(repaired, scenario)
    assert low <= OBSERVED_MONTHLY <= high, (
        f"the repaired model's 90% interval is {low:,.0f} to {high:,.0f} and the invoices "
        f"average {OBSERVED_MONTHLY:,.0f} a month. Still outside, so the structure is still wrong."
    )


def test_the_fixture_really_is_wrong(original, scenario):
    """Scaffolding: the problem exists.

    Unmarked, so CI keeps checking that the fixture still contradicts the observation. If a change
    to the fixture made this pass, the problem has quietly solved itself and needs rewriting.
    """
    low, high = _interval(original, scenario)
    assert high < OBSERVED_MONTHLY, (
        f"the fixture's interval is {low:,.0f} to {high:,.0f}, which already contains the observed "
        f"{OBSERVED_MONTHLY:,.0f}. There is nothing for the reader to find."
    )


def test_the_fixture_has_no_plug_of_its_own(original):
    """Scaffolding: the rule the problem enforces is one the fixture already keeps.

    Every input it has is a quantity or a price, and none is a bare amount of money a month. So a
    repair of the shape the tests ask for is the shape the file already uses, not a rule invented
    for the exercise.
    """
    inputs = [node for node in original.nodes.values() if isinstance(node, Input)]
    assert any(not _is_money(node.unit) for node in inputs)
    assert all(node.unit != f"{original.currency}/month" for node in inputs)
