"""The evaluator refuses operands that meet in different units of one dimension.

It converts a formula's result once, into the node's declared unit. That is right for products
and quotients and wrong for a sum, a difference, a min or a max of quantities declared in
different units, and for a ceil or floor over a number not yet in the node's unit: each
typechecks, because the dimensions agree, and each computes a wrong number in silence. Problem 9.3
runs into it, and so would any reader adding ``USD/year`` to ``USD/month``.
"""

from __future__ import annotations

import textwrap

import pytest

from sizing.dsl import load_model
from sizing.evaluate import check_units

HEADER = """
model: mixed
title: mixed units, for the test
currency: USD
nodes:
  a:
    kind: input
    unit: TB
    value: 10
    provenance: {kind: assumption, source: test}
  b:
    kind: input
    unit: TiB
    value: 10
    provenance: {kind: assumption, source: test}
  per_host:
    kind: input
    unit: TB/host
    value: 2
    provenance: {kind: assumption, source: test}
"""


def model_with(tmp_path, nodes: str, outputs: list[str]):
    text = (
        HEADER
        + textwrap.indent(textwrap.dedent(nodes), "  ")
        + "outputs:\n"
        + "".join(f"  - {o}\n" for o in outputs)
    )
    path = tmp_path / "model.yaml"
    path.write_text(text)
    return load_model(path)


def test_a_sum_of_two_units_of_one_dimension_is_refused(tmp_path):
    model = model_with(
        tmp_path,
        """
        both:
          kind: derived
          unit: TB
          formula: a + b
        """,
        ["both"],
    )
    problems, _ = check_units(model)
    assert len(problems) == 1
    assert "'both'" in problems[0] and "terabyte" in problems[0] and "tebibyte" in problems[0]
    assert "one unit" in problems[0]


@pytest.mark.parametrize("formula", ["a - b", "max(a, b)", "min(a, b)"])
def test_a_difference_or_a_comparison_is_refused_the_same_way(tmp_path, formula):
    model = model_with(
        tmp_path,
        f"""
        mixed:
          kind: derived
          unit: TB
          formula: {formula}
        """,
        ["mixed"],
    )
    problems, _ = check_units(model)
    assert len(problems) == 1 and "'mixed'" in problems[0], problems


def test_rounding_a_number_not_yet_in_the_nodes_unit_is_refused(tmp_path):
    model = model_with(
        tmp_path,
        """
        hosts:
          kind: derived
          unit: host
          formula: ceil(b / per_host)
        """,
        ["hosts"],
    )
    problems, _ = check_units(model)
    assert len(problems) == 1 and "rounded the wrong number" in problems[0], problems


def test_matching_units_and_products_are_untouched(tmp_path):
    model = model_with(
        tmp_path,
        """
        c:
          kind: input
          unit: TB
          value: 3
          provenance: {kind: assumption, source: test}
        total:
          kind: derived
          unit: TiB
          formula: a + c
        scaled:
          kind: derived
          unit: TiB
          formula: b * 2
        hosts:
          kind: derived
          unit: host
          formula: ceil(a / per_host)
        """,
        ["total", "scaled", "hosts"],
    )
    problems, factors = check_units(model)
    assert not problems, problems
    assert factors["total"] == pytest.approx(1e12 / 2**40)


def test_the_books_own_models_pass_the_rule():
    for path in ("models/web_service/model.yaml", "models/observability/model.yaml"):
        problems, _ = check_units(load_model(path))
        assert not problems, problems


def test_a_pure_number_is_not_an_amount_of_data(tmp_path):
    """Bits carry no dimension in Pint, so a plain number converted to ``TB`` was scaled by
    1.25e-13 in silence, and a ceiling with a bare limit compared against almost nothing."""
    model = model_with(
        tmp_path,
        """
        ratio:
          kind: input
          unit: dimensionless
          value: 3
          provenance: {kind: assumption, source: test}
        held:
          kind: derived
          unit: TB
          formula: ratio * 2
        full:
          kind: ceiling
          unit: TB
          of: a
          limit: 10
          headroom: 0.1
          because: test
        """,
        ["held", "full"],
    )
    problems, _ = check_units(model)
    assert len(problems) == 2, problems
    assert any("'held'" in p and "a pure number" in p for p in problems), problems
    assert any("'full' limit" in p for p in problems), problems
