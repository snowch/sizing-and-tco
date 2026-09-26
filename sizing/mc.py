"""Monte Carlo, from first principles.

This module is small on purpose. It is quoted into ch13 and ch14 and it is meant to be read, not
imported and trusted, so there is no simulation framework underneath it and no statistics package
beside it — numpy for arrays, :mod:`sizing.normal` for one rational approximation, and nothing
else. A reader who finishes ch14 should be able to delete this file and write it again.

## One idea

Every distribution here is sampled the same way, and it is the only sampling idea in the book:

    draw a percentile uniformly at random, and ask the distribution what value sits at it.

That is *inverse transform sampling*. It is why each distribution below needs exactly one
function — its percentile function, ``ppf`` — and why adding a distribution to this book is
three lines rather than a new dependency. Problem 13.1 asks the reader to add one.

## What is deliberately absent

No variance reduction, no quasi-random sequences, no importance sampling. Every one of them
narrows an interval for the same number of draws, and every one of them also makes the interval
harder to explain to the person who has to sign for the money. This book's bottleneck is never
compute; it is whether the reader believes the answer.

No fitted distributions either. Nothing here reads data and tells you which shape it is. Choosing
a shape is an editorial act with provenance attached (ch03), and a function that guesses it for
you produces a model whose central assumption nobody ever wrote down.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from sizing.normal import normal_ppf

#: The percentile the ``p10``/``p90`` form of a lognormal is pinned at, as a z-score. Named
#: because it appears in the parameter solution below and a bare 1.2816 there would be a mystery.
Z90 = float(normal_ppf(0.9))

#: How many draws a model is sampled with unless a scenario says otherwise.
#:
#: Not a magic number: ch14 derives it. At this count the 90% interval of the reference storage
#: model is stable to within the precision the book reports it to, which is the only definition of
#: "enough samples" that means anything. A model whose answer is still moving at 100,000 draws is
#: telling you something about itself, and :func:`samples_needed` says how many it wants.
DEFAULT_SAMPLES = 100_000


def rng(seed: int) -> np.random.Generator:
    """The generator, seeded.

    One per run, created here so that every result in the book can record the seed that produced
    it and be reproduced exactly. An unseeded Monte Carlo is a measurement nobody can repeat,
    which is the same thing this repository refuses everywhere else.

    PCG64 rather than the legacy Mersenne Twister: numpy's modern generator is what
    ``default_rng`` gives you, and pinning it by name means a numpy upgrade cannot silently
    change which stream a stamped seed refers to.
    """
    return np.random.Generator(np.random.PCG64(seed))


# -- percentile functions ----------------------------------------------------------------
#
# Each takes a vector of percentiles in (0, 1) and returns the values at them. That is the whole
# interface. Everything else in this module is arrangement.


def uniform_ppf(u: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
    """Every value between two bounds, equally likely.

    Honest when the bounds are genuinely all you know — a contract that caps a price, a retention
    window somebody will choose from a range. Dishonest as a default, because it says the bounds
    are as likely as the middle, and almost nothing real is like that.
    """
    return minimum + u * (maximum - minimum)


def triangular_ppf(u: np.ndarray, minimum: float, likely: float, maximum: float) -> np.ndarray:
    """An expert's guess: the least it could be, the most, and the one they would bet on.

    The shape most sizing inputs arrive in, because it is the shape of the answer to "what is it,
    roughly?". Its flaw is worth stating every time it is used: it asserts that nothing outside
    the bounds can happen, and the bounds came from somebody's memory.

    The two branches meet at the mode. Below it the area grows as the square of the distance from
    the minimum, which inverts to a square root — the whole derivation, and problem 13.1 asks for
    it again for a distribution that is not here.
    """
    if not minimum <= likely <= maximum:
        raise ValueError(
            f"triangular needs min <= likely <= max, got {minimum}, {likely}, {maximum}"
        )
    if maximum == minimum:
        return np.full_like(u, minimum)
    width = maximum - minimum
    at_mode = (likely - minimum) / width
    below = minimum + np.sqrt(u * width * (likely - minimum))
    above = maximum - np.sqrt((1.0 - u) * width * (maximum - likely))
    return np.where(u < at_mode, below, above)


def lognormal_ppf(u: np.ndarray, p10: float, p90: float) -> np.ndarray:
    """Multiplicative uncertainty: the shape of prices, growth rates and anything compounding.

    Parameterised by two percentiles rather than by the mean and standard deviation of the
    logarithm, because nobody has an intuition for the second and everybody has one for the first.
    "I would be surprised if it were under 11 or over 19" is a sentence a person can say about a
    price, and it is exactly ``p10=11, p90=19``.

    Two properties earn it its place. It cannot go negative, and neither can a price. And a
    product of several of them is another one, which is what a chain of multiplications in a
    sizing model *is* — so the uncertainty that arrives at the end of the chain has this shape
    whether or not anybody chose it.
    """
    if not 0 < p10 < p90:
        raise ValueError(f"lognormal needs 0 < p10 < p90, got p10={p10}, p90={p90}")
    # Solve for the two parameters of the underlying normal from the two stated percentiles.
    log_median = (np.log(p10) + np.log(p90)) / 2.0
    log_spread = (np.log(p90) - np.log(p10)) / (2.0 * Z90)
    return np.exp(log_median + log_spread * normal_ppf(u))


def normal_ppf_scaled(u: np.ndarray, mean: float, sd: float) -> np.ndarray:
    """Symmetric error around a central value.

    In this book it means one thing: the measurement uncertainty of a ``measured`` node (ch03).
    A constant was measured, the measurement has a standard error, and that error is as likely to
    be high as low. It is the wrong default for a price — see :func:`lognormal_ppf` — and the
    wrong shape for anything that cannot go negative, which it happily will.
    """
    if sd < 0:
        raise ValueError(f"normal needs sd >= 0, got {sd}")
    return mean + sd * normal_ppf(u)


#: The distributions a model file may declare, by the key it declares them under. Adding one is a
#: percentile function and a line here; there is no registration machinery and no plugin system,
#: because four shapes cover every input in both reference models and a fifth should have to
#: argue for itself.
SHAPES: dict[str, Callable[..., np.ndarray]] = {
    "uniform": uniform_ppf,
    "triangular": triangular_ppf,
    "lognormal": lognormal_ppf,
    "normal": normal_ppf_scaled,
}


def sample(spec: dict, n: int, generator: np.random.Generator) -> np.ndarray:
    """Draw ``n`` values from a declared distribution.

    Two lines, and they are the two lines of the whole chapter: draw percentiles, look up values.
    """
    shape, parameters = one_shape(spec)
    return SHAPES[shape](generator.random(n), **parameters)


def one_shape(spec: dict) -> tuple[str, dict]:
    """Pull the single distribution out of a declaration, refusing ambiguity.

    A node that declares two shapes is not a node with a shape to be guessed at; it is a model
    file somebody edited without deleting the old line, and picking either one for them hides it.
    """
    declared = [key for key in spec if key in SHAPES]
    if len(declared) != 1:
        known = ", ".join(sorted(SHAPES))
        raise ValueError(
            f"a distribution declares exactly one shape, got {sorted(spec)!r}. Known shapes: {known}"
        )
    shape = declared[0]
    return shape, dict(spec[shape])


# -- inputs that move together -----------------------------------------------------------


def correlation_matrix(names: list[str], pairs: list[dict]) -> np.ndarray:
    """A full correlation matrix from the pairs a model bothered to declare.

    Everything not named is left at zero, which is an assumption and not a fact — ch14 is mostly
    about how much that assumption costs. Stating it here rather than hiding it in a default is
    the point of building the matrix explicitly.
    """
    index = {name: i for i, name in enumerate(names)}
    matrix = np.eye(len(names))
    for pair in pairs:
        a, b, rho = pair["a"], pair["b"], float(pair["rho"])
        if a not in index or b not in index:
            missing = a if a not in index else b
            raise ValueError(f"correlation names {missing!r}, which is not a sampled input")
        if not -1.0 <= rho <= 1.0:
            raise ValueError(f"correlation between {a} and {b} is {rho}, outside [-1, 1]")
        matrix[index[a], index[b]] = matrix[index[b], index[a]] = rho
    return matrix


def rank_to_score_correlation(rank_rho: np.ndarray) -> np.ndarray:
    """Work out the score correlation to ask for, so the ranks come out as declared.

    :func:`correlate` correlates normal scores and then reorders each input to follow them. The
    rank correlation that comes out is lower than the score correlation that went in, by a fixed
    formula, a result due to Karl Pearson (1907):

        rank correlation  =  (6 / pi) * arcsin(score correlation / 2)

    The gap is small and consistent: ask the scores for 0.8 and the ranks come out at about
    0.786. That is why it survives review, since nobody expects the number they typed to come
    back different. So this inverts the formula: a model file's ``rho`` means the rank
    correlation the modeller wants.
    """
    return 2.0 * np.sin(np.pi * rank_rho / 6.0)


def correlate(
    columns: np.ndarray, target: np.ndarray, generator: np.random.Generator
) -> np.ndarray:
    """Give each input the rank correlation a model declares, without changing its distribution.

    Iman and Conover's method (1982): each column is reordered to match the target correlations.
    Every value that was in a column is still in it, so each input keeps exactly the distribution
    the modeller chose. Only which draws line up with which changes.

    Correlating the values themselves instead would change each input's distribution, and then
    the model would answer a question nobody asked. Problem 14.2 checks both: each input's
    distribution does not move, and the rank correlation comes out as declared.

    ``columns`` is (samples, inputs); ``target`` is the square matrix from
    :func:`correlation_matrix`, holding rank correlations.
    """
    n, k = columns.shape
    if target.shape != (k, k):
        raise ValueError(f"correlation matrix is {target.shape}, expected {(k, k)}")
    if k == 0 or np.allclose(target, np.eye(k)):
        return columns

    # A reference set with the right shape and no correlation: the normal scores, independently
    # shuffled per column, from the run's own generator so the whole thing reproduces from one
    # stamped seed. Working in scores rather than in the data is what makes the method
    # indifferent to what the marginals actually are.
    scores = normal_ppf(np.arange(1, n + 1) / (n + 1))
    reference = np.column_stack([generator.permutation(scores) for _ in range(k)])

    wanted_scores = rank_to_score_correlation(target)
    np.fill_diagonal(wanted_scores, 1.0)
    try:
        wanted = np.linalg.cholesky(wanted_scores)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "the declared correlations are not mutually consistent — no set of inputs can have "
            "all of them at once. Check for a triangle of strong correlations that disagree."
        ) from exc
    have = np.linalg.cholesky(np.corrcoef(reference, rowvar=False))
    shaped = reference @ np.linalg.solve(have, wanted).T

    # Reorder each column to follow the shaped scores' ranking. `argsort` twice gives the rank of
    # every element; sorting the column and indexing by rank puts the largest value where the
    # largest score is, and so on down.
    out = np.empty_like(columns)
    for j in range(k):
        ranks = np.argsort(np.argsort(shaped[:, j]))
        out[:, j] = np.sort(columns[:, j])[ranks]
    return out


# -- reading the answer ------------------------------------------------------------------

#: The percentiles every sampled node reports. Deliberately few. A table with a dozen of them
#: invites the reader to find the one that supports the decision they had already made.
PERCENTILES = (5, 25, 50, 75, 95)


def summarise(x: np.ndarray) -> dict:
    """Summarise a node's draws as percentiles, minimum, maximum, mean and standard deviation.

    The percentiles are interpolated between draws rather than read directly from them. This is
    the right choice because the draws come from a continuous distribution the model made up: no
    single draw is real, so there is no reason to prefer one.
    """
    x = np.asarray(x, dtype=float)
    values = np.percentile(x, PERCENTILES)
    return {
        "min": float(np.min(x)),
        **{f"p{p}": float(v) for p, v in zip(PERCENTILES, values, strict=True)},
        "max": float(np.max(x)),
        "mean": float(np.mean(x)),
        "sd": float(np.std(x, ddof=1)) if x.size > 1 else 0.0,
    }


def interval(x: np.ndarray, lo: float = 5, hi: float = 95) -> tuple[float, float]:
    """The range the model puts ``hi - lo`` per cent of its belief in.

    Not a confidence interval and not a guarantee. It is a statement about this model's inputs,
    and it is exactly as good as they are — which is what ch14's closing section is about.
    """
    low, high = np.percentile(np.asarray(x, dtype=float), [lo, hi])
    return float(low), float(high)


def half_width(x: np.ndarray, lo: float = 5, hi: float = 95) -> float:
    """Half the distance between the 5th and 95th percentile of the draws, by default.

    The width belongs to the distribution. More draws locate it; they do not shrink it.
    """
    low, high = interval(x, lo, hi)
    return (high - low) / 2.0


def samples_needed(observed_spread: float, at_n: int, target_spread: float) -> int:
    """How many draws until the answer moves between runs by no more than ``target_spread``.

    ``observed_spread`` is how much a figure varied between runs of ``at_n`` draws with different
    seeds. The run-to-run spread falls as one over the square root of the number of draws, so
    halving it takes four times as many draws. ch14 shows the law in a table.

    This is about sampling noise only: how much the answer wobbles because it was made from a
    finite number of draws. It says nothing about whether the model is right, and the interval
    does not narrow with more draws.
    """
    if target_spread <= 0:
        raise ValueError("the target spread must be positive")
    ratio = observed_spread / target_spread
    return int(np.ceil(at_n * ratio * ratio))


#: Above this ratio between the 95th percentile and the 5th, equal-width bins stop describing the
#: quantity: most of the draws fall in the first bin and the rest of the picture is empty. A queue
#: near saturation does this. Deliberately measured across the interval rather than across the
#: extremes, because one stray draw from a long tail should not change how everything is binned.
LOG_BINNING_SPAN = 100.0


def histogram(x: np.ndarray, bins: int = 64) -> dict:
    """Compress a node's draws into counts and bin edges, small enough for the browser.

    By default that is 64 counts and 65 edges instead of 100,000 draws, for every node in the
    graph. This is what lets you click any node and see a narrow input become a wide output
    further down the chain.

    Bins are equal in width, or equal in ratio if the draws span more than
    :data:`LOG_BINNING_SPAN`; the result's ``spacing`` says which. Anything that draws the
    histogram must check ``spacing``: the same counts mean different things on the two axes.
    """
    x = np.asarray(x, dtype=float)
    low, high = float(x.min()), float(x.max())
    p5, p95 = (float(v) for v in np.percentile(x, [5, 95]))
    if low > 0 and p5 > 0 and p95 / p5 >= LOG_BINNING_SPAN:
        counts, edges = np.histogram(x, bins=np.geomspace(low, high, bins + 1))
        return {"counts": counts.tolist(), "edges": edges.tolist(), "spacing": "log"}
    counts, edges = np.histogram(x, bins=bins)
    return {"counts": counts.tolist(), "edges": edges.tolist(), "spacing": "linear"}
