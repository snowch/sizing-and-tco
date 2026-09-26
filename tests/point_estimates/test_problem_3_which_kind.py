"""Problem 1.3 - definitional or conditional, read from the descriptions in the chapter.

Three model descriptions (A, B, C) appear in the chapter. Each is also written as a model file
under ``fixtures/``, and the oracle is the toolkit: it reads the kind of each file the way the
chapter says it does, from whether a measured constant or a ceiling is in it. So the answer is
derived at test time and stored nowhere.
"""

from __future__ import annotations

import pytest

from tests.point_estimates.oracle import DESCRIBED, kinds
from tests.point_estimates.stubs import stages_and_kinds

WORDS = ("definitional", "conditional")


@pytest.mark.problem
def test_the_classifications_are_right():
    answer = list(stages_and_kinds())
    ok = len(answer) == len(DESCRIBED)
    assert ok, f"you gave {len(answer)} answers; give one for each of models A, B and C, in order"
    ok = all(isinstance(kind, str) and kind.strip().lower() in WORDS for kind in answer)
    assert ok, "each answer is one of two words, 'definitional' or 'conditional'"
    ok = all(kind in WORDS for kind in answer)
    assert ok, "write each word in lower case, with no spaces around it"
    expected = kinds()
    too_many = any(
        a == "conditional" and e == "definitional" for a, e in zip(answer, expected, strict=True)
    )
    too_few = any(
        a == "definitional" and e == "conditional" for a, e in zip(answer, expected, strict=True)
    )
    hints = []
    if too_many:
        hints.append(
            "You have called a model conditional that has no measured constant and no ceiling in "
            "it. A number is a measured constant because of where it came from, not because of "
            "what it measures: read what each description says about where its numbers came from."
        )
    if too_few:
        hints.append(
            "You have called a model definitional that holds only on a condition. Look for a "
            "number measured on one version of one piece of software, or a limit past which the "
            "arithmetic stops being true."
        )
    ok = not (too_many or too_few)
    assert ok, " ".join(hints)


def test_the_three_descriptions_are_not_all_one_kind():
    """Scaffolding: one word for all three would pass if they were, which is no problem at all."""
    assert set(kinds()) == set(WORDS)


def test_each_file_differs_from_model_a_only_by_what_the_page_says():
    """Scaffolding: B is A with its processor time measured, and C is A with ceilings added. If a
    file drifted from its description, the reader would be graded on a model the page does not
    show."""
    from sizing.dsl import load_model

    a, b, c = (load_model(path) for path in DESCRIBED)
    assert not a.of_kind("measured") and not a.of_kind("ceiling")
    assert [n.name for n in b.of_kind("measured")] == ["processor_time"]
    assert not b.of_kind("ceiling")
    assert set(b.nodes) == set(a.nodes)
    assert not c.of_kind("measured") and len(c.of_kind("ceiling")) == 2
    assert set(a.nodes) <= set(c.nodes)
