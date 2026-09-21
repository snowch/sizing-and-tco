"""Chapter 3's problems. Edit this file; the tests beside it say whether you are right.

The first asks you to take a measurement and stamp it properly. The second asks what a
measurement is worth, which is a different question and the one people skip.
"""

from __future__ import annotations


def measure_something(shards: int = 8) -> dict:
    """Problem 3.1 - take a constant, and stamp it so somebody else could check it.

    Pick any quantity a codec or an encoder decides. The obvious ones are already taken by
    ``bench/run_corpus.py``; reach for a different one. How many bytes a UUID costs after
    compression when there are a thousand of them together. What a base64 encoding costs. How much
    smaller a column of timestamps gets when you store the differences.

    Return a **stamped result payload** - the dictionary ``bench.stamp.build_result`` produces -
    without writing it to disk. Use ``build_result(..., write=False)``, and name this file in
    its ``code_sources``: the stamp hashes the code that produced the figure, so a re-run can be
    told from a retyping.

    It must satisfy every rule in ``bench.stamp.provenance_problems``:

    * target ``corpus``, because a codec is deterministic and anybody can check it;
    * a ``corpus`` and a ``codec`` in ``produced_by``, because a compression figure without the
      body of data it compressed is an anecdote;
    * a unit for every figure in the summary - and not one with time in it, because how fast the
      codec ran is a property of your computer;
    * a ``value`` and an ``sd``, measured over ``shards`` independently generated pieces of
      corpus. One measurement is a number; the interesting question is how much it would move if
      you did it again.

    Generate the corpus in this file, deterministically, from starting numbers you state, so that
    anybody can generate the same one. A constant measured
    over data nobody else can obtain is a constant nobody else can check.
    """
    raise NotImplementedError("problem 3.1")


def shards_needed(observed_sd: float, at_shards: int, target_sd: float) -> int:
    """Problem 3.2 - how much more measuring would it take?

    You have measured a constant over ``at_shards`` pieces of corpus and got a standard error of
    ``observed_sd``. You want ``target_sd``. Return the number of shards that would get you there,
    rounded up.

    The standard error of a mean falls as one over the square root of the count, so this is the
    arithmetic ch14 uses to ask how many draws are enough, used in the direction people find less
    intuitive. It is also the arithmetic that stops a measurement campaign before it starts: work
    out what halving your uncertainty costs *before* agreeing to halve it.

    Return the total number of shards needed, not the number of extra ones.
    """
    raise NotImplementedError("problem 3.2")
