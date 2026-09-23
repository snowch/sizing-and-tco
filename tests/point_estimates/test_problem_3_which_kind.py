"""Problem 1.3 - definitional or conditional, read from the problem text in the chapter.

Three model descriptions (A, B, C) appear in the chapter. The reader reads each one and decides
whether it is a definitional or a conditional model by looking for measured constants and
ceilings.
"""

from __future__ import annotations

import pytest

from tests.point_estimates.stubs import stages_and_kinds

#: A has neither; B has a constant measured on one version; C has ceilings.
EXPECTED = ["definitional", "conditional", "conditional"]


@pytest.mark.problem
def test_the_classifications_are_right():
    kinds = stages_and_kinds()
    assert len(kinds) == 3, f"you gave {len(kinds)} classifications, need 3 (models A, B, C)"
    assert kinds == EXPECTED, (
        f"you classified: {kinds}. Look for measured constants and ceilings: either one makes "
        "a model conditional."
    )


def test_the_three_models_are_ordered():
    """Scaffolding: verify the expected output makes sense."""
    assert set(EXPECTED) == {"definitional", "conditional"}
    assert EXPECTED[0] != EXPECTED[1], "model B adds a measured constant to model A"
