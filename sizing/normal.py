"""The inverse normal CDF, vectorised.

This is the one function in the Monte Carlo core that cannot be derived on the back of an
envelope, and it is in its own file so that :mod:`sizing.mc` stays readable. Everything else in
the sampler is three lines of algebra; this is a rational approximation, and pretending otherwise
by burying it among the others would misrepresent what the reader is looking at.

Why it is here at all. :mod:`sizing.mc` samples every distribution by inverse transform — draw a
percentile uniformly, ask the distribution what value sits at it — so the normal and the
lognormal both need :math:`\\Phi^{-1}`, and so does the rank-correlation step. The standard
library has an exact-enough scalar version in ``statistics.NormalDist().inv_cdf``, but it is
scalar: at the sample counts ch13 uses to demonstrate convergence it costs seconds per run, which
is enough to make the experiment tedious and therefore not run.

So the approximation is used for speed and the standard library is used as the oracle:
``tests/test_mc.py`` checks the two agree to nine figures across the whole range, including the
tails. A fast implementation nobody checks is how a book ends up publishing an interval that is
quietly wrong in the 99th percentile.

The coefficients are Acklam's @acklam2003inverse. They are constants of a published algorithm
rather than anybody's prose, and the arrangement below is this repository's own.
"""

from __future__ import annotations

import numpy as np

#: Where the central rational approximation stops being the accurate one. Below this and above
#: its mirror, the approximation works on ``sqrt(-2 ln p)`` instead — which is the tail's natural
#: variable, and the reason the accuracy holds out to one part in a billion rather than degrading
#: where the interesting percentiles are.
_TAIL = 0.02425

_CENTRAL_NUM = (
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
)
_CENTRAL_DEN = (
    -5.447609879822406e01,
    1.615858368580409e02,
    -1.556989798598866e02,
    6.680131188771972e01,
    -1.328068155288572e01,
)
_TAIL_NUM = (
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
)
_TAIL_DEN = (
    7.784695709041462e-03,
    3.224671290700398e-01,
    2.445134137142996e00,
    3.754408661907416e00,
)


def _poly(coefficients: tuple[float, ...], x: np.ndarray) -> np.ndarray:
    """Horner's rule. ``_poly((a, b, c), x)`` is ``a*x**2 + b*x + c``."""
    out = np.zeros_like(x)
    for coefficient in coefficients:
        out = out * x + coefficient
    return out


def normal_ppf(u: np.ndarray | float) -> np.ndarray:
    """The value below which a fraction ``u`` of a standard normal distribution lies.

    ``normal_ppf(0.5)`` is 0, ``normal_ppf(0.9)`` is about 1.28, and ``normal_ppf(0.975)`` is the
    1.96 that turns up in every textbook margin of error.

    Raises on 0 and 1 rather than returning an infinity. Both are real bugs when they happen — a
    uniform draw is never exactly 0 or 1 under numpy's generator, so an endpoint here means a
    percentile was computed rather than drawn, and silently returning an infinity would put it in
    a sum and turn a whole model's output into ``nan`` several steps later.
    """
    u = np.asarray(u, dtype=float)
    if np.any((u <= 0.0) | (u >= 1.0)):
        raise ValueError("normal_ppf needs percentiles strictly between 0 and 1")

    out = np.empty_like(u)

    lower = u < _TAIL
    upper = u > 1.0 - _TAIL
    central = ~(lower | upper)

    # The middle 95%, as a rational function of the distance from the median.
    q = u[central] - 0.5
    r = q * q
    out[central] = _poly(_CENTRAL_NUM, r) * q / (_poly(_CENTRAL_DEN, r) * r + 1.0)

    # Both tails, in the variable that makes them well behaved. The upper tail is the lower one
    # reflected, which is worth doing explicitly: it is the only reason the function is accurate
    # at 0.999 as well as at 0.001, and a reader checking the code should be able to see that.
    for mask, tail_u, sign in ((lower, u[lower], 1.0), (upper, 1.0 - u[upper], -1.0)):
        q = np.sqrt(-2.0 * np.log(tail_u))
        out[mask] = sign * _poly(_TAIL_NUM, q) / (_poly(_TAIL_DEN, q) * q + 1.0)

    return out
