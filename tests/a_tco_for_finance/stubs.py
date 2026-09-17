"""Chapter 20's problems. Edit this file; the tests beside it say whether you are right.

Neither is arithmetic. Both are about what to say.
"""

from __future__ import annotations


def decision_table() -> list[dict]:
    """Problem 20.1 - two designs, priced, with their risk.

    Return a list of rows, one per scenario of the storage model that represents a purchasable
    design. Each row is a dictionary with exactly these keys:

    ``"scenario"``     the scenario's name
    ``"nodes"``        machines purchased
    ``"tco_p50"``      the median five-year total
    ``"tco_p95"``      the 95th percentile of it
    ``"p_out_of_space"``  how often the capacity ceiling is breached

    Build it from the stamped model results rather than by re-running anything, so that the table
    somebody is shown is the table the build produced.

    Then read it as the person on the other side of the table will. They have one question - what
    am I buying and what am I buying it *instead of* - and every column is there to answer it or it
    should not be there. Four columns is not a constraint; it is the number that fits in somebody's
    head while they decide.
    """
    raise NotImplementedError("problem 20.1")


def one_number() -> tuple[float, str]:
    """Problem 20.2 - they have asked for a single number.

    They will. Refusing is not an option that exists, and answering with a range is a way of
    refusing that annoys people without informing them.

    Return the number you would give for the reference design's five-year total, and a string
    saying what it hides.

    Any defensible choice passes: the median, the mean, a percentile, a rounded figure. The test
    checks that it came out of the model, that you rounded it to a precision the model can support,
    and that your sentence names a specific thing - the percentile you chose, the structural
    omission, the assumption the whole thing rests on. A sentence that says "it is uncertain" is
    not naming anything.

    The point is that the sentence is the deliverable. The number is what gets written down; the
    sentence is what makes it honest, and you get one.
    """
    raise NotImplementedError("problem 20.2")
