"""Chapter 9's problems. Edit this file; the tests beside it say whether you are right."""

from __future__ import annotations


def raw_for(usable: float, replication: float, compression: float, overhead: float) -> float:
    """Problem 9.1 - the chain from what you need to what you must buy.

    ``usable`` is the bytes the application wants to store. ``replication`` is how many copies you
    keep. ``compression`` is the ratio the data achieves - a two means it halves. ``overhead`` is
    a multiplier for filesystem, index and journal, so 1.05 means five per cent.

    Return the raw bytes you have to buy.

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
