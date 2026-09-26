"""Problem 21.2 - the single number, and the sentence that goes with it.

Nothing here grades the choice. It grades whether the number came from the model, whether it is
rounded to a precision the model can support, and whether the sentence names something.
"""

from __future__ import annotations

import re

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


#: Words that name something: which figure was chosen, an input the total rests on, a cost line
#: or a limit. Matched as the start of a word, so "percentiles", "omitted" and "hosts" count.
NAMES = (
    "percentile",
    "median",
    "p5",
    "p10",
    "p50",
    "p90",
    "p95",
    "growth",
    "compression",
    "pric",
    "missing",
    "omit",
    "omission",
    "exclud",
    "assum",
    "tax",
    "refresh",
    "structur",
    "measured",
    "capacity",
    "risk",
    "host",
    "licen",
    "people",
    "salar",
    "staff",
    "energy",
    "electricity",
    "discount",
    "migration",
    "vendor",
    "ceiling",
    "knee",
    "queue",
)
#: And the phrases the chapter itself uses for an omission.
LEFT_OUT = re.compile(r"\b(leaves? out|left out|does not include|not included|does not count)\b")
VAGUE = {"uncertain", "uncertainty", "approximate", "estimate", "roughly", "about"}


def words_of(sentence: str) -> list[str]:
    """The words of a sentence, lower case, with the punctuation around them gone."""
    return re.findall(r"[a-z0-9]+", sentence.lower())


def names_something(sentence: str) -> bool:
    words = words_of(sentence)
    return any(word.startswith(NAMES) for word in words) or bool(LEFT_OUT.search(" ".join(words)))


@pytest.mark.problem
def test_the_sentence_names_something(answer):
    _, sentence = answer
    words = words_of(sentence)
    assert len(words) >= 8, "one sentence, but a whole one: it has fewer than eight words."
    if VAGUE & set(words) and not names_something(sentence):
        pytest.fail(
            "saying it is uncertain is not naming anything. Say which figure you chose, or what "
            f"the total leaves out or rests on. Yours: {sentence!r}"
        )
    assert names_something(sentence), (
        "the sentence has to name a specific thing: which percentile, which omission, which "
        f"assumption. Yours: {sentence!r}"
    )


def test_naming_is_read_from_words_not_from_punctuation():
    """Scaffolding: a sentence that names the median before a comma, or the knee before a full
    stop, names it; a sentence that only says it is uncertain names nothing."""
    assert names_something("It is the median, so half the futures cost more than this figure.")
    assert names_something("Growth at its high end puts the busy hour over the knee.")
    assert names_something("It leaves out what running short would cost; the model has no term.")
    assert not names_something("There is some uncertainty in this figure, as there always is.")


def test_the_model_produces_a_wide_enough_answer_for_this_to_matter(summary):
    """Scaffolding: if the interval were narrow, one number would be a fine answer."""
    assert summary["p95"] / summary["p5"] > 1.3, summary
