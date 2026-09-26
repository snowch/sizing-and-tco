"""Problem 9.3 - the same model in the other kind of terabyte.

Graded by what only a consistent change of units gives: the converted model typechecks, every
input still means the same bytes, nothing the model buys has moved, and every node read in
tebibytes reads smaller by exactly the ratio. The reader is handed every node's unit and every
input's number or band; the test puts what comes back into the model, formulas untouched. Derived
from the model at test time; nothing here says what any number is.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from pint.util import to_units_container

from sizing import mc
from sizing.dsl import Input, Model, load_model, load_scenario
from sizing.evaluate import check_units, point
from sizing.units import UNITS
from sizing.units import parse as parse_unit
from tests.capacity.stubs import in_binary_units

MODEL = "models/web_service/model.yaml"
SCENARIO = "models/web_service/scenarios/reference.yaml"
TIB_PER_TB = 1e12 / 2**40


@pytest.fixture(scope="module")
def base():
    return load_model(MODEL)


@pytest.fixture(scope="module")
def scenario():
    return load_scenario(SCENARIO)


def declared(model: Model) -> tuple[dict[str, str], dict[str, float | dict]]:
    """What the reader is handed: every node's unit, and every input's number or band."""
    units = {name: node.unit for name, node in model.nodes.items()}
    values: dict[str, float | dict] = {}
    for name, node in model.nodes.items():
        if isinstance(node, Input):
            if node.value is not None:
                values[name] = node.value
            else:
                values[name] = dict(mc.one_shape(node.distribution)[1])
    return units, values


def rebuilt(model: Model, units: dict[str, str], values: dict[str, float | dict]) -> Model:
    """The model with these units and numbers put back into it, and nothing else changed."""
    missing = sorted(set(model.nodes) - set(units))
    assert not missing, f"no unit came back for {missing[:5]}"
    nodes = {}
    for name, node in model.nodes.items():
        changes: dict = {"unit": units[name]}
        if isinstance(node, Input):
            assert name in values, f"no number came back for the input {name}"
            if node.value is not None:
                changes["value"] = float(values[name])
            else:
                shape, _ = mc.one_shape(node.distribution)
                changes["distribution"] = {shape: dict(values[name])}
        nodes[name] = replace(node, **changes)
    return replace(model, nodes=nodes)


def converted(model: Model) -> Model:
    return rebuilt(model, *in_binary_units(*declared(model)))


def terabytes_in(unit: str) -> int:
    """The power a terabyte carries in a unit: one for TB, minus one for USD/TB/month, zero."""
    return int(to_units_container(parse_unit(unit)).get("terabyte", 0))


def tebibytes_in(unit: str) -> int:
    return int(to_units_container(parse_unit(unit)).get("tebibyte", 0))


def in_old_units(value: float, new_unit: str, old_unit: str) -> float:
    return float(UNITS.Quantity(value, new_unit).to(old_unit).magnitude)


@pytest.mark.problem
def test_every_terabyte_became_a_tebibyte_in_the_same_place(base):
    after_all = converted(base)
    carrying = {n for n, node in base.nodes.items() if terabytes_in(node.unit)}
    assert carrying, "the model carries no terabytes; problem 9.3 needs rewriting"
    for name, node in base.nodes.items():
        after = after_all.nodes[name]
        assert terabytes_in(after.unit) == 0, f"{name} still carries a terabyte: {after.unit!r}"
        assert tebibytes_in(after.unit) == terabytes_in(node.unit), (
            f"{name}: {node.unit!r} should become the same unit with tebibytes in the terabytes' "
            f"place, not {after.unit!r}"
        )
        if name not in carrying:
            assert after.unit == node.unit, f"{name}: a unit with no terabyte in it changed"


@pytest.mark.problem
def test_every_input_still_means_the_same_bytes(base):
    after_all = converted(base)
    for name, node in base.nodes.items():
        if not isinstance(node, Input):
            continue
        after = after_all.nodes[name]
        if node.value is not None:
            assert in_old_units(after.value, after.unit, node.unit) == pytest.approx(
                node.value, rel=1e-9
            ), (
                f"{name}: {after.value} {after.unit} is not {node.value} {node.unit}. A new unit "
                "under the same number is a different claim; convert the number with the unit."
            )
        if node.distribution is not None:
            shape, was = mc.one_shape(node.distribution)
            now_shape, now = mc.one_shape(after.distribution)
            assert now_shape == shape, f"{name}: the shape of the band changed"
            for key, value in was.items():
                assert key in now, f"{name}: the band came back without its {key}"
                assert in_old_units(now[key], after.unit, node.unit) == pytest.approx(
                    value, rel=1e-9
                ), f"{name}: the band's {key} no longer means the same bytes"


@pytest.mark.problem
def test_no_formula_changed(base):
    """The reader hands back units and numbers, and the test puts only those into the model. This
    holds the test to that: converting by hand inside a formula is how two copies of a model
    start to disagree, and no route to one is left open."""
    after_all = converted(base)
    for name, node in base.nodes.items():
        assert getattr(after_all.nodes[name], "formula_text", "") == getattr(
            node, "formula_text", ""
        ), f"{name}: the formula changed. The build converts; doing it by hand is the error."


@pytest.mark.problem
def test_it_still_typechecks(base):
    problems, _ = check_units(converted(base))
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_nothing_the_model_buys_moved(base, scenario):
    before = point(base, scenario)
    after = point(converted(base), scenario)
    for name, node in base.nodes.items():
        if terabytes_in(node.unit) or isinstance(node, Input):
            continue
        if after[name] != pytest.approx(before[name], rel=1e-9):
            pytest.fail(
                f"{name} has no terabyte in it and moved by a factor of "
                f"{after[name] / before[name]:.4f}. A consistent change of units moves nothing "
                "the model buys; something was converted wrongly, or a unit was missed.",
                pytrace=False,
            )


@pytest.mark.problem
def test_every_tebibyte_figure_reads_smaller_by_exactly_the_ratio(base, scenario):
    before = point(base, scenario)
    after = point(converted(base), scenario)
    for name, node in base.nodes.items():
        if terabytes_in(node.unit) != 1 or isinstance(node, Input):
            continue
        if after[name] != pytest.approx(before[name] * TIB_PER_TB, rel=1e-9):
            pytest.fail(
                f"{name}: read in tebibytes it should be smaller than in terabytes by exactly the "
                "ratio of the two units, and it is not. The same bytes counted in bigger units "
                "is a smaller number.",
                pytrace=False,
            )


#: A price of the reader's own to convert, because no input in the web service model carries a
#: terabyte below the line: the model's one such unit is on a computed node, which is relabelled.
PRICE_UNIT = "USD/TB/month"
PRICES = {"value": 10.0, "band": {"minimum": 8.0, "likely": 10.0, "maximum": 15.0}}


@pytest.mark.problem
@pytest.mark.parametrize("form", sorted(PRICES))
def test_a_terabyte_below_the_line_converts_the_other_way(form):
    was = PRICES[form]
    units, values = in_binary_units({"price": PRICE_UNIT}, {"price": was})
    unit, now = units["price"], values["price"]
    assert tebibytes_in(unit) == -1 and terabytes_in(unit) == 0, (
        f"price: {PRICE_UNIT!r} should become the same unit with a tebibyte in the terabyte's "
        f"place, not {unit!r}"
    )
    pairs = [(now[key], was[key]) for key in was] if isinstance(was, dict) else [(now, was)]
    for new, old in pairs:
        assert in_old_units(new, unit, PRICE_UNIT) == pytest.approx(old, rel=1e-9), (
            "price: the number no longer means the same money for the same bytes. A price per "
            "terabyte-month has the terabyte below the line, so its number moves the opposite "
            "way from a number of terabytes."
        )


def test_the_two_terabytes_really_do_differ():
    """Scaffolding: the problem is about something."""
    assert abs(TIB_PER_TB - 1.0) > 0.05
    assert UNITS.Quantity(1.0, "TiB").to("TB").magnitude == pytest.approx(1 / TIB_PER_TB)


def test_the_model_carries_terabytes_above_and_below_the_line(base):
    """Scaffolding: the exercise meets a terabyte in a numerator and in a denominator, so a
    relabelling that only handles ``TB`` cannot pass it."""
    powers = {terabytes_in(node.unit) for node in base.nodes.values()}
    assert {1, -1} <= powers, powers


def test_putting_the_declared_units_and_numbers_back_changes_nothing(base, scenario):
    """Scaffolding: the route the grader takes, handing the reader every unit and number and
    putting what comes back into the model, is faithful. Handed back unchanged, the model is the
    model."""
    units, values = declared(base)
    assert set(units) == set(base.nodes)
    assert set(values) == {n for n, node in base.nodes.items() if isinstance(node, Input)}
    assert point(rebuilt(base, units, values), scenario) == point(base, scenario)


def test_the_price_test_is_needed_and_can_fail():
    """Scaffolding: the price test tells the two directions apart, so a conversion that treats a
    terabyte below the line like one above it cannot pass it."""
    below = sorted(
        name
        for name, node in load_model(MODEL).nodes.items()
        if isinstance(node, Input) and terabytes_in(node.unit) < 0
    )
    assert not below, f"{below} carry a terabyte below the line; the 9.3 stub says no input does"
    wrong_way = PRICES["value"] * TIB_PER_TB
    assert in_old_units(wrong_way, "USD/TiB/month", PRICE_UNIT) != pytest.approx(
        PRICES["value"], rel=1e-3
    )
