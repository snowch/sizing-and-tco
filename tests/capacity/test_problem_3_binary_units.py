"""Problem 9.3 - the same model in the other kind of terabyte.

Graded by what only a consistent change of units gives: the converted model typechecks, every
input still means the same bytes, nothing the model buys has moved, and every node read in
tebibytes reads smaller by exactly the ratio. Derived from the model at test time; nothing here
says what any number is.
"""

from __future__ import annotations

import pytest
from pint.util import to_units_container

from sizing import mc
from sizing.dsl import Input, load_model, load_scenario
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


def terabytes_in(unit: str) -> int:
    """The power a terabyte carries in a unit: one for TB, minus one for USD/TB/month, zero."""
    return int(to_units_container(parse_unit(unit)).get("terabyte", 0))


def tebibytes_in(unit: str) -> int:
    return int(to_units_container(parse_unit(unit)).get("tebibyte", 0))


def in_old_units(value: float, new_unit: str, old_unit: str) -> float:
    return float(UNITS.Quantity(value, new_unit).to(old_unit).magnitude)


@pytest.mark.problem
def test_every_terabyte_became_a_tebibyte_in_the_same_place(base):
    converted = in_binary_units(base)
    carrying = {n for n, node in base.nodes.items() if terabytes_in(node.unit)}
    assert carrying, "the model carries no terabytes; problem 9.3 needs rewriting"
    for name, node in base.nodes.items():
        after = converted.nodes[name]
        assert terabytes_in(after.unit) == 0, f"{name} still carries a terabyte: {after.unit!r}"
        assert tebibytes_in(after.unit) == terabytes_in(node.unit), (
            f"{name}: {node.unit!r} should become the same unit with tebibytes in the terabytes' "
            f"place, not {after.unit!r}"
        )
        if name not in carrying:
            assert after.unit == node.unit, f"{name}: a unit with no terabyte in it changed"


@pytest.mark.problem
def test_every_input_still_means_the_same_bytes(base):
    converted = in_binary_units(base)
    for name, node in base.nodes.items():
        if not isinstance(node, Input):
            continue
        after = converted.nodes[name]
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
                assert in_old_units(now[key], after.unit, node.unit) == pytest.approx(
                    value, rel=1e-9
                ), f"{name}: the band's {key} no longer means the same bytes"


@pytest.mark.problem
def test_no_formula_changed(base):
    converted = in_binary_units(base)
    for name, node in base.nodes.items():
        assert getattr(converted.nodes[name], "formula_text", "") == getattr(
            node, "formula_text", ""
        ), (
            f"{name}: the formula changed. The build converts; doing it by hand is how two copies of a model start to disagree."
        )


@pytest.mark.problem
def test_it_still_typechecks(base):
    problems, _ = check_units(in_binary_units(base))
    assert not problems, "\n".join(problems)


@pytest.mark.problem
def test_nothing_the_model_buys_moved(base, scenario):
    before = point(base, scenario)
    after = point(in_binary_units(base), scenario)
    for name, node in base.nodes.items():
        if terabytes_in(node.unit) or isinstance(node, Input):
            continue
        assert after[name] == pytest.approx(before[name], rel=1e-9), (
            f"{name}: {before[name]:,.4f} became {after[name]:,.4f}, and it has no terabyte in "
            "it. A consistent change of units moves nothing the model buys; something was "
            "converted wrongly, or a unit was missed."
        )


@pytest.mark.problem
def test_every_tebibyte_figure_reads_smaller_by_exactly_the_ratio(base, scenario):
    before = point(base, scenario)
    after = point(in_binary_units(base), scenario)
    for name, node in base.nodes.items():
        if terabytes_in(node.unit) != 1 or isinstance(node, Input):
            continue
        assert after[name] == pytest.approx(before[name] * TIB_PER_TB, rel=1e-9), (
            f"{name}: {before[name]:,.3f} TB should read {before[name] * TIB_PER_TB:,.3f} TiB. "
            "The same bytes counted in bigger units is a smaller number."
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
