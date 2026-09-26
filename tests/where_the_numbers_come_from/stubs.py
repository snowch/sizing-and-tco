"""Chapter 3's problems. Edit this file; the tests beside it say whether you are right.

The first asks you to take a measurement and stamp it properly. The second asks what a
measurement is worth, which is a different question and the one people skip.
"""

from __future__ import annotations


def measure_something(shards: int = 8) -> dict:
    """Problem 3.1 - take a constant, and stamp it so somebody else could check it.

    Pick any quantity a codec or an encoder decides. The obvious ones are already taken by
    ``bench/run_corpus.py``; reach for a different one. Three ideas, each a ratio: how much a
    thousand UUIDs shrink when compressed together; what base64 encoding costs, as encoded size
    over raw size; how much smaller a column of timestamps gets when you store the differences
    between them.

    Return four parts as one dictionary:

        {
            "summary": {"value": ..., "sd": ..., "shards": shards},
            "units": {"value": ..., "sd": ..., "shards": ...},
            "produced_by": {"corpus": ..., "codec": ...},
            "per_shard": [...],
        }

    ``per_shard`` is the figure measured on each shard, one number per shard, in shard order.
    ``value`` is the mean of ``per_shard``. ``sd`` is the standard error of that mean: the spread
    between the shards divided by the square root of their number. It is not the spread itself.
    The key is called ``sd`` because the book's own stamps use that name.

    Every figure in ``summary`` needs a unit the toolkit knows, and none may have time in it. It
    knows data units such as ``byte`` and ``bit``; ``dimensionless``, for a ratio or a plain
    count such as the number of shards; and the book's counting units: ``request``, ``span``,
    ``sample``, ``series``, ``line``, ``query``, ``host``, ``node``, ``core``, ``label``,
    ``drive``, ``failure``. They combine, as in ``byte/line``. There is no unit for a UUID.

    The test stamps the answer as a ``corpus`` result, because a codec is deterministic and anyone
    can re-run it. It names this file as the code that produced the figure, so a re-run can be
    told from a retyping. Then it holds the result to every rule in
    ``bench.stamp.provenance_problems``:

    * a ``corpus`` and a ``codec`` in ``produced_by``, because a compression figure without the
      body of data it compressed is an anecdote;
    * a unit for every figure in the summary - and not one with time in it, because how fast the
      codec ran is a property of your computer;
    * a ``value`` and an ``sd``, measured over ``shards`` independently generated pieces of
      corpus. One measurement is a number; the interesting question is how much it would move if
      you did it again.

    Generate the corpus in this file, deterministically, from starting numbers you state, so that
    anyone can generate the same one. A constant measured over data nobody else can obtain is a
    constant nobody else can check.
    """
    raise NotImplementedError("problem 3.1")


def shards_needed(observed_sd: float, at_shards: int, target_sd: float) -> int:
    """Problem 3.2 - how much more measuring would it take?

    You have measured a constant over ``at_shards`` pieces of corpus and got a standard error of
    ``observed_sd``. You want ``target_sd``. Return the number of shards that would get you there,
    rounded up.

    The standard error of a mean falls as one over the square root of the count. Here you use that
    relationship backwards: from the error you want to the count that would buy it.

    This is the arithmetic that stops a measurement campaign before it starts: work out what
    halving your uncertainty costs before agreeing to halve it.

    Return the total number of shards needed, including the ones you already have, not the number
    of extra ones. Refuse a target of zero.
    """
    raise NotImplementedError("problem 3.2")
