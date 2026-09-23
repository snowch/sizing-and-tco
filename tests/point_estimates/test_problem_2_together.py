"""Problem 1.2 - compound doubt from the taxi example.

The reader looks at the taxi table in the chapter (run 1: £3,125; run 4: £7,800) and computes
the ratio. This teaches that when every input moves at once, the answer moves further than
any single input can move it alone. That is why a point estimate cannot be defended by pointing
at how carefully each input was chosen.
"""

from __future__ import annotations

import pytest

from tests.point_estimates.stubs import spread_on_paper


@pytest.mark.problem
def test_the_ratio_is_right():
    expected = 7800 / 3125  # run 4 / run 1
    answer = spread_on_paper()
    assert abs(answer - expected) < 1e-6, (
        f"you gave {answer:.3f}. Run 4 costs £7,800 and run 1 costs £3,125. "
        f"The ratio is {expected:.3f}."
    )
