"""Chapter 8's problems. Edit this file; the tests beside it say whether you are right.

Both are about the same claim: some things a chain of multiplications cannot express, and no
amount of care about the inputs to that chain will warn you.
"""

from __future__ import annotations

import numpy as np


def straight_line_forecast(known: list[tuple[float, float]], at: np.ndarray) -> np.ndarray:
    """Problem 8.1 - do what a spreadsheet would do, and watch it fail.

    ``known`` is a list of ``(utilisation, residence_time)`` pairs from a system that has never
    been busy: all at low load, which is the data a healthy system has.

    ``at`` is the utilisations you want a forecast for.

    Fit a straight line through the known points and return what it predicts at each of ``at``.

    A straight line is the shape a chain of multiplications gives an input it multiplies by. In such
    a chain every input is a multiplier or a divisor, and growth is raised to a power: the rule for
    how an input moves the answer is the same at every size.

    The test compares your forecast against the curve the book swept out of the queueing model. At
    the loads you fitted on, the line is excellent. Further out it is not wrong by a percentage; it
    is wrong by a multiple, and the multiple grows.

    The test also checks that what you return is a straight line. Fitting the queueing model's
    division to the same points would follow the curve: that is the right model and the book's
    lesson from ch06. This problem asks what the wrong one predicts.
    """
    raise NotImplementedError("problem 8.1")


def after_a_host_loss(utilisation: float, hosts: int, service_time: float) -> tuple[float, float]:
    """Problem 8.2 - a host lost at the busy hour.

    ``utilisation`` is how busy the fleet is at the busy hour, ``hosts`` is how many hosts it has,
    and ``service_time`` is ch05's service time in seconds: how long one request takes alone. All
    three are plain numbers; the test reads them off the web service model.

    One host is lost. Its share of the requests lands on the survivors. Return two numbers: the
    survivors' utilisation, and the residence time ch06's division then gives them, the service
    time divided by what is left of the system. At or past a utilisation of one there is nothing
    left to divide by, so return something that is not finite, or raise.

    Predict before you run it. The utilisation rises by a factor you can write down without a
    calculator. Does the residence time rise by the same factor? Write your answer down, then run
    the test. It checks the reference fleet, and then shrinks the fleet at the same utilisation
    until the survivors are past one.
    """
    raise NotImplementedError("problem 8.2")
