"""Chapter 20's problems. Edit this file; the tests beside it say whether you are right.

Three problems about a model that is wrong in shape. The first two ask the question that comes
before any repair: how would you know? The third is the repair, and the only exercise in the book
whose oracle is outside the model.
"""

from __future__ import annotations

import numpy as np

from sizing.dsl import Model


def is_refuted(samples: np.ndarray, observed: np.ndarray) -> bool:
    """Problem 20.1 - what would count as evidence against the model?

    ``samples`` is a model's output distribution. ``observed`` is every figure you have from the
    real system the model was supposed to describe, one per observation: a single number in an
    array of one, a year of invoices in an array of twelve.

    Return whether the set refutes the model.

    The whole problem is in the word "refuted", and the trap is that a 90% interval is *supposed*
    to be missed one time in ten. One observation outside it is not evidence; it is the expected
    behaviour of an interval that is doing its job. A model rejected on that basis would be
    rejected roughly whenever it was right.

    Two things bear on the verdict, and a rule has to weigh both: how much of the model's belief
    lies beyond each observation, and how many observations you have. A figure the model puts a
    twentieth of its belief beyond is unremarkable once and damning fifty times over; a figure it
    puts none of its belief beyond is damning on its own. So a rule is a threshold on how
    surprising the whole set would be if the model were right. State one that holds together, and
    implement it.

    The tests check the cases at both ends: a single miss just outside the interval is never a
    refutation, and an observation far enough out that no plausible model produces it always is,
    however few of them you have. In between, the tests only check that your rule is monotonic
    in both directions - never less damning with more copies of the same figure, never less
    damning further out - because there is no right answer there and pretending otherwise would
    be the same error the chapter is about.
    """
    raise NotImplementedError("problem 20.1")


def widen_until_it_fits(samples: np.ndarray, observation: float) -> float:
    """Problem 20.2 - the wrong repair, measured.

    A model disagrees with an observation. The easiest response is to make the model vaguer until
    it stops disagreeing.

    Return the factor by which the distribution's spread about its median would have to grow for
    ``observation`` to land inside the 90% interval. Scale the samples about their median; do not
    shift them. Scaling the output's own draws stands in for widening the inputs, which is what
    somebody would do to the file: the same repair, one step downstream. The factor is at least
    one, because an observation already inside needs no widening.

    Then look at what that does to the interval. The model now agrees with the observation and can
    no longer distinguish between designs, which is the only thing it was for. A model that cannot
    be wrong has stopped being able to be useful, and this number is what that costs.
    """
    raise NotImplementedError("problem 20.2")


def repair_the_model(model: Model) -> Model:
    """Problem 20.3 - find the missing node.

    ``tests/the_missing_node/fixtures/model.yaml`` is a small monthly cost model for a hosted
    service. It is arithmetically correct, its inputs carry honest distributions, and it converges
    beautifully. It is also wrong, because a cost line is missing from it, and no amount of
    sampling can see that.

    The evidence is in the test: what the service the model describes cost per month, averaged
    over twelve invoices. The figure is invented for the exercise, and it falls **outside** the
    model's 90% interval - comfortably outside, on the high side.

    Return a repaired model whose interval contains the observation.

    Three rules, all enforced:

    * every input the model already has keeps its value and its distribution. Not widened, not
      shifted. Making a model vaguer until it stops disagreeing with reality is the most common
      wrong answer to this situation, and moving an input until the invoice fits is the same
      answer with the invoice copied into the file;
    * the repair adds a **quantity**: a new input whose unit is the thing the missing line is
      billed on rather than an amount of money, with a provenance source like every other input.
      A node that is only dollars a month is a plug, and a plug is the observation written into
      the model under another name;
    * the repair adds a **cost line**: a new derived node that prices the quantity and feeds the
      total, and nothing the model already computed moves except what that line feeds.

    The missing line is a real one and it is findable. Ask what a hosted service pays for that is
    neither a machine, nor a disk, nor a support contract - and which is billed on a quantity
    nothing in this model currently mentions.
    """
    raise NotImplementedError("problem 20.3")
