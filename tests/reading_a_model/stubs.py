"""Chapter 1's problems. Edit this file; the tests beside it say whether you are right.

All three are about the four node kinds and what declaring one commits you to.
"""

from __future__ import annotations

from sizing.dsl import Model


def add_a_ceiling(model: Model, name: str, of: str, limit: float, headroom: float) -> Model:
    """Problem 1.1 - add a ceiling to a model that has none.

    Return a copy of ``model`` with one more node: a ``ceiling`` called ``name``, watching the
    expression ``of``, against ``limit``, with ``headroom`` of margin, and with a reason.

    Three things the build will insist on, and each one is the subject of a chapter:

    * the ceiling's unit must be the unit its expression produces, or the dimensional pass
      refuses it (ch01);
    * the headroom must be declared - a limit with no margin is not a sizing rule (ch11);
    * the reason must not be empty, because a margin nobody can argue with gets copied into the
      next model by somebody who does not know what it was for (ch11).

    Add it to the model's outputs too, or ``verify-models.py`` will point out that it feeds
    nothing.
    """
    raise NotImplementedError("problem 1.1")


def in_binary_units(model: Model) -> Model:
    """Problem 1.2 - the same model, read in the other kind of terabyte.

    A vendor's TB is a trillion bytes. A filesystem's TiB is 2^40 of them, about ten per cent
    more. Both are spelled "terabyte" in conversation and the difference has bought a lot of
    people a smaller cluster than they thought.

    Return a copy of ``model`` in which every node currently declared in ``TB`` is declared in
    ``TiB`` instead - and **change nothing else**. No formula, no input value, no distribution.

    The test then asserts two things that only both hold if the unit system is doing its job:
    every affected output is numerically *smaller* by the expected ratio, because the same
    quantity of bytes counted in larger units is a smaller number - and the model still
    typechecks, because the dimensions did not change, only the units.

    If you find yourself editing a value to compensate, stop. The build does that conversion, and
    doing it by hand is how the two copies of a model start to disagree.
    """
    raise NotImplementedError("problem 1.2")


def make_it_a_cost_model(model: Model) -> Model:
    """Problem 1.3 - turn a sizing model into a cost model, honestly.

    ``scripts/verify-models.py`` classifies a model by what is in it: a ``measured`` node or a
    ``ceiling`` makes it a sizing model, and a model with neither is a cost model whose inputs
    can simply be sampled. That is the distinction the front matter is built on.

    Return a copy of ``model`` that classifies as a **cost** model, while still evaluating and
    still producing at least one of the outputs it produced before.

    You may delete nodes. You may not delete the outputs. And the point of the exercise is in the
    third test: having removed them, write one sentence in this docstring saying what the
    resulting model can no longer tell anybody. If you cannot name it, you have removed something
    that was not doing any work, and the original model should not have had it.
    """
    raise NotImplementedError("problem 1.3")
