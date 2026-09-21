"""Chapter 21's problems. Edit this file; the tests beside it say whether you are right.

Neither is arithmetic. Both are about what to say.
"""

from __future__ import annotations


def decision_table(summaries: dict[str, dict]) -> list[dict]:
    """Problem 21.1 - two designs, priced, with their risk.

    ``summaries`` holds the stamped result of each of the chapter's two designs, keyed by scenario
    name. Both are scenarios of the web service model: ``reference`` buys what the model
    recommends at the point estimate, and ``sized_for_growth`` buys the same fleet sized for the
    growth we might get rather than the growth we expect.

    A summary is the build's record of one run, as data. ``summary["nodes"]`` has an entry per
    node of the model, and the figures the table needs live at:

    ``nodes["hosts"]["point"]``                                 hosts purchased
    ``nodes["tco"]["summary"]["p50"]`` and ``["p95"]``          the five-year total's median and
                                                                its 95th percentile
    ``nodes["queueing_headroom"]["ceiling"]["p_over_limit"]``   how often the queueing ceiling
                                                                is breached

    Return a list of rows, one for each design. Each row is a dictionary with exactly these keys:

    ``"scenario"``     the scenario's name
    ``"hosts"``        hosts purchased
    ``"tco_p50"``      the median five-year total
    ``"tco_p95"``      the 95th percentile of it
    ``"p_over_the_knee"``  how often the queueing ceiling is breached

    Build it from the stamped results rather than by re-running anything, so that the table
    somebody is shown is the table the build produced.

    Then read it as the person on the other side of the table will. They have one question - what
    am I buying and what am I buying it *instead of* - and every column is there to answer it or it
    should not be there. A handful of columns is not a constraint; it is what fits in somebody's
    head while they decide.
    """
    raise NotImplementedError("problem 21.1")


def one_number() -> tuple[float, str]:
    """Problem 21.2 - they have asked for a single number.

    They will. Refusing is not an option that exists, and answering with a range is a way of
    refusing that annoys people without informing them.

    Return the number you would give for the reference design's five-year total, and a string
    saying what it hides.

    Any defensible choice passes: the median, a percentile, a rounded figure. The test
    checks that it came out of the model, that you rounded it to a precision the model can support,
    and that your sentence names a specific thing - the percentile you chose, the structural
    omission, the assumption the whole thing rests on. A sentence that says "it is uncertain" is
    not naming anything.

    The point is that the sentence is the deliverable. The number is what gets written down; the
    sentence is what makes it honest, and you get one.
    """
    raise NotImplementedError("problem 21.2")
