"""Chapter 9's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations

from sizing.dsl import Model


def raw_for(stored: float, replication: float, compression: float, overhead: float) -> float:
    """Problem 9.1 - the chain from what you must keep to what you must buy.

    ``stored`` is the bytes of records the service has to keep. ``replication`` is how many
    copies the store keeps of each. ``compression`` is the ratio the records achieve on disk - a
    two means they halve. ``overhead`` is a multiplier for the indexes and the write-ahead log
    kept beside them, so 1.3 means thirty per cent.

    Return the raw bytes of disk you have to buy.

    Two of those four multiply and one divides, and getting the division the wrong way up gives an
    answer that is wrong by the square of the compression ratio while still looking entirely
    plausible. Work out which is which by asking what each one does to the amount you buy.

    The order matters less than people think and the direction matters more. Check yours against
    a case you can do in your head before running the test.
    """
    raise NotImplementedError("problem 9.1")


def erasure_crossover(data_shards: int, parity_shards: int) -> float:
    """Problem 9.2 - when is erasure coding cheaper than copies?

    Replication keeps whole copies: three copies costs three times the space and survives two
    losses. Erasure coding splits an object into ``data_shards`` pieces and computes
    ``parity_shards`` more, and survives the loss of any ``parity_shards`` of them - for a space
    cost of ``(data + parity) / data``.

    Return the **replication factor** that would give the same durability as this erasure code, so
    that the two can be compared on space at equal safety.

    It is one line and the point is what it exposes. Erasure coding is not cheaper because it is
    cleverer; it is cheaper because it amortises the same protection over more pieces. The saving
    grows with ``data_shards``, and so does the number of machines a single read has to touch -
    which is a bandwidth and latency cost this model has no term for, and ch10 is why that
    matters.
    """
    raise NotImplementedError("problem 9.2")


def in_binary_units(model: Model) -> Model:
    """Problem 9.3 - the same model, read in the other kind of terabyte.

    A vendor's TB is a trillion bytes. A filesystem's TiB is 2^40 of them, about ten per cent
    more. Both are spelled "terabyte" in conversation and the difference has bought a lot of
    people a smaller cluster than they thought.

    Return a copy of ``model`` in which every unit that carries a terabyte, in a numerator or a
    denominator, ``TB``, ``TB/host``, ``USD/TB/month`` and the rest, carries a tebibyte in its
    place. For a computed node that is a relabelling and nothing else: its number is worked out
    from the inputs and the build converts it. For an input it is more than that. An input's
    number is a claim about bytes, and the same number under a new unit is a different claim, so
    convert the number too: a value, or each end of a band, so that it means the same bytes it
    meant before. A price per terabyte-month becomes a slightly higher price per tebibyte-month.
    Change no formula.

    The test then asserts what only a consistent conversion gives: the model still typechecks,
    nothing the model buys has moved, the same hosts and the same money to the last digit, and
    every node read in tebibytes reads smaller by exactly the ratio. If a host count moved, you
    converted a number wrongly or missed a unit, and which one is the exercise.
    """
    raise NotImplementedError("problem 9.3")


def make_it_a_cost_model(model: Model) -> Model:
    """Problem 9.4 - turn a sizing model back into a cost model, honestly.

    ``scripts/verify-models.py`` classifies a model by what is in it: a ``measured`` node or a
    ``ceiling`` makes it a sizing model, and a model with neither is a cost model whose inputs
    can simply be sampled. The web service model crossed that line in ch06, when its first
    ceiling arrived; this chapter adds the measured constant that would have crossed it anyway.

    Return a copy of ``model`` that classifies as a **cost** model, while still evaluating and
    still producing at least one of the outputs it produced before.

    You may delete nodes, and you will have to delete outputs: the ceilings are outputs, and the
    measured constant feeds the recommended host count. Keep at least one of the original outputs
    working. And the point of the exercise is in the third test: having removed them, finish the
    last line of this docstring with one sentence saying what the resulting model can no longer
    tell anybody. If you cannot name it, you have removed something that was not doing any work,
    and the original model should not have had it.

    What it can no longer say:
    """
    raise NotImplementedError("problem 9.4")
