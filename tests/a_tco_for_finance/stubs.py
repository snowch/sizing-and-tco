"""Chapter 21's problems. Edit this file; the tests beside it say whether you are right.

Neither is arithmetic. Both are about what to say.
"""

from __future__ import annotations


def decision_table(summaries: dict[str, dict]) -> list[dict]:
    """Problem 21.1 - two designs, priced, with their risk.

    ``summaries`` holds the stamped result of each of the chapter's two designs,
    keyed by scenario name. Both are scenarios of the web service model:
    ``reference`` buys the fleet the model recommends with every input at its
    point estimate, and ``sized_for_growth`` buys the fleet the model recommends
    when the annual growth factor is at its 90th percentile, with every other
    input at its point estimate.

    A summary is the build's record of one run, as data.
    ``summary["nodes"]`` has an entry per node of the model. The figures the
    table needs live at:

    ``nodes["hosts"]["point"]``
      hosts purchased

    ``nodes["tco"]["summary"]["p50"]``
      the five-year total's median

    ``nodes["tco"]["summary"]["p95"]``
      its 95th percentile

    ``nodes["queueing_headroom"]["ceiling"]["p_over_limit"]``
      the share of futures in which the busy hour is over its limit

    Return a list of rows, one for each design. Each row is a dictionary with
    exactly these keys:

    ``"scenario"``
      the scenario's name

    ``"hosts"``
      hosts purchased

    ``"tco_p50"``
      the median five-year total

    ``"tco_p95"``
      its 95th percentile

    ``"p_over_the_knee"``
      the share of futures in which the busy hour is over its limit, between 0 and 1

    Build it from the stamped results rather than by re-running anything, so
    the table the person who signs is shown is the table the build produced.
    Figures copied from the chapter's tables are rounded and will not match.

    The columns are fixed. Each is there because it answers the one question
    the person who signs has: what am I buying, and what am I buying it
    *instead of*? Hosts say what; the two totals say what it costs, in the
    middle and near the top; the last column says what the extra money buys.
    When the test passes, read the table as that person will.
    """
    raise NotImplementedError("problem 21.1")


def one_number() -> tuple[float, str]:
    """Problem 21.2 - they have asked for a single number.

    They will. Refusing is not an option that exists, and answering with a range is a way of
    refusing that annoys people without informing them.

    Return the number you would give for the reference design's five-year total, and a string
    saying what it hides.

    Any defensible choice passes: the median, a high percentile, a round figure above the median.

    The test checks three things. First, the number lies inside the model's 90% interval for the
    total, or close to it. Second, it is rounded: a whole multiple of a round step (1, 2 or 5
    times a power of ten from 100, or 2.5 times one from 1,000), and the step is no finer than a
    hundredth of the width of the 90% interval. Third, the sentence names something specific:
    which percentile or the median; an input the total rests on, such as growth or a price; a
    cost it leaves out; or a limit, such as the busy-hour ceiling. It has at least eight words. A
    sentence that only says it is uncertain names nothing.

    The sentence is the deliverable. The number is what gets written down; the sentence is what
    makes it honest, and you get one.
    """
    raise NotImplementedError("problem 21.2")
