"""Chapter 9's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def raw_for(stored: float, replication: float, compression: float, overhead: float) -> float:
    """Problem 9.1 - the chain from what you must keep to what you must buy.

    ``stored`` is the bytes of records the service has to keep. ``replication`` is how many
    copies the store keeps of each. ``compression`` is the ratio the records achieve on disk - a
    two means they halve. ``overhead`` is a multiplier for the indexes and the write-ahead log
    kept beside them, so 1.3 means thirty per cent.

    Return the raw bytes of disk you have to buy.

    Two of those four multiply and one divides, and getting the division the wrong way up gives an
    answer that is wrong by the square of the compression ratio while still looking
    plausible. Work out which is which by asking what each one does to the amount you buy.

    The order in which you combine them does not matter. Which way up the division goes does.
    Check yours against a case you can do in your head before running the test: one term at a
    time, with the other three at one.
    """
    raise NotImplementedError("problem 9.1")


def replication_as_safe_as(data_shards: int, parity_shards: int) -> float:
    """Problem 9.2 - what replication factor is as safe as this erasure code?

    Replication keeps whole copies: three copies costs three times the space and survives two
    losses. Erasure coding splits an object into ``data_shards`` pieces and computes
    ``parity_shards`` more, and survives the loss of any ``parity_shards`` of them - for a space
    cost of ``(data + parity) / data``.

    Return the **replication factor** that would give the same durability as this erasure code, so
    that the two can be compared on space at equal safety.

    The answer is one line and the point is what it exposes. Erasure coding is not cheaper because
    it is cleverer; it is cheaper because it spreads the same protection over more pieces. The
    saving grows with ``data_shards``, and so does the number of machines a single read has to
    touch. That is a cost in network traffic and in waiting, and no model in this book has a term
    for it.
    """
    raise NotImplementedError("problem 9.2")


def in_binary_units(
    units: dict[str, str], values: dict[str, float | dict]
) -> tuple[dict[str, str], dict[str, float | dict]]:
    """Problem 9.3 - the same model, read in the other kind of terabyte.

    A vendor's TB is a trillion bytes. A filesystem's TiB is 2^40 of them, about ten per cent
    more. Both are called "terabyte" in conversation. A drive counted in the wrong one holds less
    than the plan thinks.

    ``units`` maps every node in the finished web service model to the unit it declares.
    ``values`` maps every input to its number, or to its band as a dictionary: ``p10`` and
    ``p90``, or ``minimum``, ``likely`` and ``maximum``. Return the two, converted. Every unit that
    carries a terabyte, above or below the line, ``TB``, ``TB/host``, ``USD/TB/month`` and the
    rest, carries a tebibyte in its place. For a computed node that is a relabelling: the build
    works its number out from the inputs. For an input, the number is a claim about bytes, so
    convert it too, a value or every number in a band, so that it means the same bytes it meant
    before. A price per terabyte-month becomes a higher price per tebibyte-month. In this model
    only a computed node has a terabyte below the line, so the test also hands your function a
    price of its own in ``USD/TB/month``, once as a value and once as a band, and checks it still
    means the same money for the same bytes. Leave every other unit and number as it was. The
    test puts what you return back into the model; no formula changes.

    The test then checks what only a consistent conversion gives: the model still typechecks,
    nothing it buys has moved (the same hosts and the same money), and every node read in
    tebibytes reads smaller by exactly the ratio. If a host count moved, you converted a number
    wrongly or missed a unit, and which one is the exercise.
    """
    raise NotImplementedError("problem 9.3")


def what_to_remove(kinds: dict[str, str], reads: dict[str, set[str]]) -> list[str]:
    """Problem 9.4 - turn a conditional model back into a definitional one, honestly.

    ``scripts/verify-models.py`` classifies a model by what is in it: a ``measured`` node or a
    ``ceiling`` makes it a conditional model, and a model with neither is a definitional model
    whose inputs can be drawn at random. The web service model crossed that line in ch06, when its
    first ceiling arrived; this chapter adds the measured constant that would have crossed it
    anyway.

    ``kinds`` maps every node in the finished web service model to its kind: ``input``,
    ``derived``, ``measured`` or ``ceiling``. ``reads`` maps every node to the names of the nodes
    its formula reads. Return the names to delete so that what is left classifies as a
    **definitional** model and still evaluates: every measured constant, every ceiling, and every
    node downstream of them, because a node that reads a deleted node cannot be worked out.

    The test deletes them, outputs included. At least one of the original outputs has to survive.
    Having removed them, finish the last line of this docstring with one sentence saying what the
    resulting model can no longer tell anybody. If you cannot name it, you removed something that
    was doing no work, and the original model should not have had it.

    What it can no longer say:
    """
    raise NotImplementedError("problem 9.4")
