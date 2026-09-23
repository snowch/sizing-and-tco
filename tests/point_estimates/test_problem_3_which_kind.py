"""Problem 1.3 - cost model or sizing model, read from the problem text in the chapter.

Three model descriptions (A, B, C) appear in the chapter. The reader reads each one and decides
whether it is a cost or sizing model by looking for measured constants and ceilings.
"""

from __future__ import annotations

import pytest

from tests.point_estimates.stubs import stages_and_kinds

#: Expected classifications for the three models: A (cost), B (cost), C (sizing).
EXPECTED = ["cost", "cost", "sizing"]


@pytest.mark.problem
def test_the_classifications_are_right():
    kinds = stages_and_kinds()
    assert len(kinds) == 3, f"you gave {len(kinds)} classifications, need 3 (models A, B, C)"
    assert kinds == EXPECTED, (
        f"you classified: {kinds}. The three models are: {EXPECTED}. "
        f"Look for measured constants and ceilings."
    )


def test_the_three_models_are_ordered():
    """Scaffolding: verify the expected output makes sense."""
    assert EXPECTED == ["cost", "cost", "sizing"]
    assert EXPECTED[2] != EXPECTED[1], "model C should be different from B"
