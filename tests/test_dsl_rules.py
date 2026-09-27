"""The holes the model builder's conformance suite found in the book's own rules, each closed.

The builder (design/model-builder.md) holds its engine to what this toolkit says about a set of
model files. Writing that suite found places where the toolkit said yes to a file the book would
not defend, or fell over instead of saying no. Each test here is one of those files, written small,
and the answer the book now gives. The builder's case name is in each docstring.
"""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import pytest

from sizing.dsl import DSL_VERSION, ModelError, load_model
from sizing.evaluate import check_units, point
from sizing.expr import FormulaError, parse
from sizing.units import UnitError, compatible
from sizing.units import parse as parse_unit

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "verify_models", ROOT / "scripts" / "verify-models.py"
)
verify_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_models)

INPUT = """
  {name}:
    kind: input
    decided: outside
    unit: {unit}
    value: {value}
    note: one number, for the test
    provenance: {{kind: assumption, source: "the test's own"}}"""

SHAPED = """
  {name}:
    kind: input
    decided: outside
    unit: dimensionless
    distribution: {{triangular: {{minimum: 1, likely: 2, maximum: 3}}}}
    provenance: {{kind: assumption, source: "{source}"}}"""


def model_file(tmp_path: Path, body: str, head: str = "dsl: 1\n", outputs: str = "[x]") -> Path:
    text = f"{head}model: case\ntitle: a case\nnodes:{body}\noutputs: {outputs}\n"
    path = tmp_path / "case" / "model.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))
    return path


def problems_of(path: Path) -> list[str]:
    _, problems = verify_models.check_file(path)
    return problems


# -- units -----------------------------------------------------------------------------------


def test_a_byte_is_not_a_pure_number():
    """edge/bytes-are-dimensionless: terabytes were a pure number to Pint."""
    assert not compatible("TB", "dimensionless")
    assert str(parse_unit("TB").dimensionality) == "[information]"
    assert compatible("TB", "GiB")


def test_terabytes_cannot_be_an_exponent_or_a_logarithm(tmp_path):
    """The case that passed: a growth factor raised to terabytes, a logarithm of terabytes."""
    body = (
        INPUT.format(name="held", unit="TB", value=15)
        + INPUT.format(name="growth", unit="dimensionless", value=1.3)
        + """
  x:
    kind: derived
    unit: dimensionless
    formula: log(held) + growth ** held"""
    )
    problems, _ = check_units(load_model(model_file(tmp_path, body)))
    assert problems, "a formula taking terabytes as an exponent or a logarithm typechecked"


@pytest.mark.parametrize("unit", ["degC", "dB", "decibel"])
def test_a_scale_with_an_offset_or_a_logarithm_is_refused(unit):
    """The unit probes degC, dB and decibel: a node converts by one factor, and these do not."""
    with pytest.raises(UnitError, match="not a ratio scale"):
        parse_unit(unit)


def test_a_model_may_price_in_euros(tmp_path):
    """The unit probes EUR and GBP: a reader who prices in another currency could not build."""
    body = INPUT.format(name="x", unit="EUR/host", value=5000)
    path = model_file(tmp_path, body, head="dsl: 1\ncurrency: EUR\n")
    assert not [p for p in problems_of(path) if "currency" in p]


def test_money_in_another_currency_is_refused(tmp_path):
    body = INPUT.format(name="x", unit="EUR/host", value=5000)
    path = model_file(tmp_path, body, head="dsl: 1\ncurrency: USD\n")
    assert any("counts money in" in p for p in problems_of(path))


def test_dollars_do_not_add_to_euros():
    assert not compatible("USD", "EUR")


# -- the loader ------------------------------------------------------------------------------


def test_yes_is_not_a_number(tmp_path):
    """edge/yaml-yes-is-one: `value: yes` loaded as 1.0."""
    path = model_file(tmp_path, INPUT.format(name="x", unit="host", value="yes"))
    with pytest.raises(ModelError, match="not a number"):
        load_model(path)


def test_a_node_written_twice_is_refused(tmp_path):
    """edge/duplicate-node-key: the second declaration won, without a word."""
    body = INPUT.format(name="x", unit="host", value=1) + INPUT.format(
        name="x", unit="host", value=2
    )
    with pytest.raises(ModelError, match="written twice"):
        load_model(model_file(tmp_path, body))


def test_a_file_for_other_rules_is_refused(tmp_path):
    """The format version: a file says which rules it is written against."""
    path = model_file(tmp_path, INPUT.format(name="x", unit="host", value=1), head="dsl: 99\n")
    with pytest.raises(ModelError, match=f"reads dsl {DSL_VERSION}"):
        load_model(path)


def test_a_file_that_does_not_say_is_reported(tmp_path):
    path = model_file(tmp_path, INPUT.format(name="x", unit="host", value=1), head="")
    assert any("which rules it is written against" in p for p in problems_of(path))


def test_an_empty_source_is_missing_not_the_word_none(tmp_path):
    """edge/types-in-the-yaml: `source:` with nothing after it passed as the text "None"."""
    body = """
  x:
    kind: input
    decided: outside
    unit: host
    value: 1
    note: one number
    provenance:
      kind: assumption
      source:"""
    assert any("empty provenance source" in p for p in problems_of(model_file(tmp_path, body)))


# -- formulas --------------------------------------------------------------------------------


@pytest.mark.parametrize("formula", ["min(a)", "max()"])
def test_min_and_max_take_two_or_more(formula):
    """The formula probes min(a) and max(): they parsed and failed at evaluation."""
    with pytest.raises(FormulaError, match="fewer than two"):
        parse(formula)


def test_a_literal_zero_meets_any_unit(tmp_path):
    """edge/max-with-zero: what is left over, or nothing, in the chain's own unit."""
    body = (
        INPUT.format(name="need", unit="TB", value=10)
        + INPUT.format(name="held", unit="TB", value=4)
        + """
  x:
    kind: derived
    unit: TB
    formula: max(0, need - held)"""
    )
    model = load_model(model_file(tmp_path, body))
    problems, _ = check_units(model)
    assert not problems
    assert point(model)["x"] == pytest.approx(6)


# -- the verifier ----------------------------------------------------------------------------


def test_a_correlation_names_two_inputs_that_vary(tmp_path):
    """edge/correlation-unchecked: a pair naming a missing or derived node was dropped silently."""
    body = SHAPED.format(name="x", source="triangular: the test's own")
    text = model_file(tmp_path, body).read_text()
    text += "correlations:\n  - {a: x, b: nowhere, rho: 0.4, because: the test}\n"
    path = tmp_path / "case" / "model.yaml"
    path.write_text(text)
    assert any("neither an input with a shape" in p for p in problems_of(path))


def test_a_correlation_is_between_minus_one_and_one(tmp_path):
    body = SHAPED.format(name="x", source="triangular: the test's own") + SHAPED.format(
        name="y", source="triangular: the test's own"
    )
    path = model_file(tmp_path, body, outputs="[x, y]")
    path.write_text(path.read_text() + "correlations:\n  - {a: x, b: y, rho: 2, because: t}\n")
    assert any("between -1 and 1" in p for p in problems_of(path))


def test_the_source_names_the_input_s_own_shape(tmp_path):
    """edge/shape-named-loosely: any shape's name passed, and "lognormal" contains "normal"."""
    body = SHAPED.format(name="x", source="a normal busy hour, and a lognormal price")
    assert any("sampled as a triangular" in p for p in problems_of(model_file(tmp_path, body)))


def test_two_shapes_are_reported_not_a_traceback(tmp_path):
    """invalid/distribution-two-shapes: the verifier fell over building its message."""
    body = """
  x:
    kind: input
    decided: outside
    unit: dimensionless
    distribution: {uniform: {minimum: 1, maximum: 2}, normal: {mean: 1, sd: 1}}
    provenance: {kind: assumption, source: "the test's own"}"""
    problems = problems_of(model_file(tmp_path, body))
    assert any("exactly one shape" in p for p in problems)


def test_a_scenario_with_no_name_is_reported_not_a_traceback(tmp_path):
    """invalid/scenario-missing-name: scenarios_for raised outside the verifier's try."""
    path = model_file(tmp_path, INPUT.format(name="x", unit="host", value=1))
    (path.parent / "scenarios").mkdir()
    (path.parent / "scenarios" / "broken.yaml").write_text("title: no name\noverrides: {}\n")
    model = load_model(path)
    problems: list[str] = []
    verify_models.check_scenarios(model, problems)
    assert any("does not load" in p for p in problems)
