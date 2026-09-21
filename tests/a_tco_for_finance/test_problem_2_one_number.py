"""Problem 21.2 - the single number, and the sentence that goes with it.

Nothing here grades the choice. It grades whether the number came from the model, whether it is
rounded to a precision the model can support, and whether the sentence names something.
"""

from __future__ import annotations

import pytest

from bench.stamp import load_result


@pytest.fixture(scope="module")
def answer():
    from tests.a_tco_for_finance.stubs import one_number

    return one_number()


@pytest.fixture(scope="module")
def summary():
    return load_result("web_service-reference")["summary"]["nodes"]["tco"]["summary"]


@pytest.mark.problem
def test_it_is_a_number_and_a_sentence(answer):
    value, sentence = answer
    assert isinstance(value, int | float) and value > 0
    assert isinstance(sentence, str)


@pytest.mark.problem
def test_the_number_came_out_of_the_model(answer, summary):
    value, _ = answer
    assert summary["p5"] * 0.9 <= value <= summary["p95"] * 1.1, (
        f"{value:,.0f} is outside the range the model produces ({summary['p5']:,.0f} to "
        f"{summary['p95']:,.0f}). Whatever you pick has to be a figure the model computed."
    )


@pytest.mark.problem
def test_it_is_rounded_to_a_precision_the_model_supports(answer, summary):
    """A five-year total written to the dollar claims a precision no input in the model has."""
    value, _ = answer
    spread = summary["p95"] - summary["p5"]
    step = spread / 100
    # Rounded to a precision the model can support: a whole multiple of a round step no finer
    # than a hundredth of the interval, the steps being the ones a person rounds to.
    steps = [m * 10**k for k in range(2, 8) for m in (1, 2, 5, 25)]
    rounded = any(s >= step and abs(value / s - round(value / s)) < 1e-9 for s in steps)
    assert rounded, (
        f"{value:,.2f} is quoted more precisely than an interval {spread:,.0f} wide can support. "
        f"Round it to a step no finer than {step:,.0f}, and to one you would defend."
    )


@pytest.mark.problem
def test_the_sentence_names_something(answer):
    value, sentence = answer
    words = sentence.lower().split()
    assert len(words) >= 8, "one sentence, but a sentence"
    vague = {"uncertain", "uncertainty", "approximate", "estimate", "roughly", "about"}
    named = {
        "percentile",
        "median",
        "p50",
        "p95",
        "growth",
        "compression",
        "price",
        "missing",
        "excludes",
        "assumes",
        "tax",
        "refresh",
        "structure",
        "measured",
        "capacity",
        "risk",
        "hosts",
        "licence",
        "licences",
        "people",
        "salary",
        "knee",
        "queue",
    }
    assert named & set(words), (
        f"the sentence has to name a specific thing - which percentile, which omission, which "
        f"assumption. Yours: {sentence!r}"
    )
    assert not (vague & set(words)) or (named & set(words)), (
        "saying it is uncertain is not naming anything"
    )


def test_the_model_produces_a_wide_enough_answer_for_this_to_matter(summary):
    """Scaffolding: if the interval were narrow, one number would be a fine answer."""
    assert summary["p95"] / summary["p5"] > 1.3, summary
