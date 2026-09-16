"""The Monte Carlo core, checked against things that are true independently of it.

Every assertion here has an oracle that does not come from this module: the standard library's
own normal quantile function, the closed-form mean of a triangular distribution, the percentiles a
lognormal was asked for by construction, the square-root law. A test suite for a sampler that used
the sampler to work out what to expect would pass forever and mean nothing.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pytest

from sizing import mc
from sizing.normal import normal_ppf

SAMPLES = 200_000


# -- the one piece of numerics ---------------------------------------------------------------


@pytest.mark.parametrize(
    "u", [1e-9, 1e-6, 0.001, 0.02424, 0.02426, 0.1, 0.5, 0.9, 0.97574, 0.999, 1 - 1e-9]
)
def test_the_inverse_normal_cdf_agrees_with_the_standard_library(u):
    """The approximation is used for speed; the standard library is the oracle.

    Including points either side of the tail boundary, which is where an approximation stitched
    together from two rational functions is most likely to be discontinuous.
    """
    assert float(normal_ppf(np.array([u]))[0]) == pytest.approx(NormalDist().inv_cdf(u), abs=1e-8)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
def test_it_refuses_percentiles_outside_the_open_interval(bad):
    with pytest.raises(ValueError):
        normal_ppf(np.array([bad]))


# -- each distribution reproduces what its parameters claim -----------------------------------


@pytest.mark.parametrize(
    ("minimum", "likely", "maximum"), [(1, 2, 6), (0, 0, 10), (0, 10, 10), (-5, 1, 3)]
)
def test_the_triangular_has_the_mean_its_parameters_imply(minimum, likely, maximum):
    """Closed form: (min + mode + max) / 3. Nothing in `mc` is consulted to produce it."""
    drawn = mc.sample(
        {"triangular": {"minimum": minimum, "likely": likely, "maximum": maximum}},
        SAMPLES,
        mc.rng(3),
    )
    assert drawn.mean() == pytest.approx(
        (minimum + likely + maximum) / 3, abs=0.02 * (maximum - minimum + 1)
    )
    assert drawn.min() >= minimum and drawn.max() <= maximum


@pytest.mark.parametrize(("p10", "p90"), [(11.0, 19.0), (1.0, 100.0), (0.085, 0.21)])
def test_the_lognormal_hits_the_percentiles_it_was_given(p10, p90):
    drawn = mc.sample({"lognormal": {"p10": p10, "p90": p90}}, SAMPLES, mc.rng(5))
    low, high = np.percentile(drawn, [10, 90])
    assert low == pytest.approx(p10, rel=0.02)
    assert high == pytest.approx(p90, rel=0.02)
    assert drawn.min() > 0, "a lognormal cannot be negative, which is why prices use one"


def test_the_uniform_is_uniform():
    drawn = mc.sample({"uniform": {"minimum": 4.0, "maximum": 9.0}}, SAMPLES, mc.rng(7))
    for percentile in (10, 25, 50, 75, 90):
        assert np.percentile(drawn, percentile) == pytest.approx(
            4.0 + (percentile / 100) * 5.0, abs=0.05
        )


def test_a_distribution_declaring_two_shapes_is_refused():
    with pytest.raises(ValueError, match="exactly one shape"):
        mc.sample(
            {"uniform": {"minimum": 0, "maximum": 1}, "normal": {"mean": 0, "sd": 1}}, 10, mc.rng(1)
        )


def test_the_same_seed_gives_the_same_numbers():
    """An unseeded simulation is a measurement nobody can repeat."""
    spec = {"lognormal": {"p10": 2.0, "p90": 8.0}}
    assert np.array_equal(mc.sample(spec, 1000, mc.rng(42)), mc.sample(spec, 1000, mc.rng(42)))
    assert not np.array_equal(mc.sample(spec, 1000, mc.rng(42)), mc.sample(spec, 1000, mc.rng(43)))


# -- correlation ------------------------------------------------------------------------------


def _spearman(x, y):
    return float(np.corrcoef(np.argsort(np.argsort(x)), np.argsort(np.argsort(y)))[0, 1])


@pytest.mark.parametrize("rho", [-0.6, 0.0, 0.3, 0.8])
def test_correlate_produces_the_rank_correlation_it_was_asked_for(rho):
    """Including the attenuation correction, which is the easy thing to get quietly wrong."""
    generator = mc.rng(11)
    columns = np.column_stack(
        [
            mc.sample({"lognormal": {"p10": 1.0, "p90": 3.0}}, 100_000, generator),
            mc.sample(
                {"triangular": {"minimum": 2, "likely": 5, "maximum": 20}}, 100_000, generator
            ),
        ]
    )
    target = mc.correlation_matrix(["a", "b"], [{"a": "a", "b": "b", "rho": rho}])
    out = mc.correlate(columns, target, mc.rng(13))
    assert _spearman(out[:, 0], out[:, 1]) == pytest.approx(rho, abs=0.02)


def test_correlate_leaves_every_marginal_exactly_alone():
    """The property that makes the method the right one: it reorders, it never adjusts."""
    generator = mc.rng(17)
    columns = np.column_stack(
        [
            mc.sample({"lognormal": {"p10": 1.0, "p90": 3.0}}, 20_000, generator),
            mc.sample({"normal": {"mean": 10.0, "sd": 2.0}}, 20_000, generator),
        ]
    )
    out = mc.correlate(
        columns, mc.correlation_matrix(["a", "b"], [{"a": "a", "b": "b", "rho": 0.7}]), mc.rng(19)
    )
    for column in (0, 1):
        assert np.array_equal(np.sort(columns[:, column]), np.sort(out[:, column]))


def test_a_correlation_between_inputs_that_push_the_same_way_widens_the_interval():
    generator = mc.rng(23)
    columns = np.column_stack(
        [mc.sample({"lognormal": {"p10": 1.0, "p90": 4.0}}, 60_000, generator) for _ in range(2)]
    )
    plain = mc.half_width(columns.sum(axis=1))
    linked = mc.half_width(
        mc.correlate(
            columns,
            mc.correlation_matrix(["a", "b"], [{"a": "a", "b": "b", "rho": 0.8}]),
            mc.rng(29),
        ).sum(axis=1)
    )
    assert linked > plain * 1.1, (
        "two inputs that move together cannot cancel each other out, so their sum has to get "
        "less certain, not more"
    )


def test_inconsistent_correlations_are_refused_with_a_useful_message():
    target = mc.correlation_matrix(
        ["a", "b", "c"],
        [
            {"a": "a", "b": "b", "rho": 0.95},
            {"a": "b", "b": "c", "rho": 0.95},
            {"a": "a", "b": "c", "rho": -0.95},
        ],
    )
    with pytest.raises(ValueError, match="not mutually consistent"):
        mc.correlate(np.random.default_rng(0).random((2000, 3)), target, mc.rng(31))


def test_a_correlation_naming_an_unknown_input_is_refused():
    with pytest.raises(ValueError, match="not a sampled input"):
        mc.correlation_matrix(["a"], [{"a": "a", "b": "nonexistent", "rho": 0.5}])


# -- reading the answer -------------------------------------------------------------------------


def test_summarise_reports_percentiles_in_order():
    drawn = mc.sample({"lognormal": {"p10": 1.0, "p90": 10.0}}, 50_000, mc.rng(37))
    summary = mc.summarise(drawn)
    ordered = [summary[key] for key in ("min", "p5", "p25", "p50", "p75", "p95", "max")]
    assert ordered == sorted(ordered)
    assert summary["sd"] > 0


def test_samples_needed_follows_the_square_root_law():
    """Four times the samples to halve the wobble. Ten thousand times to divide it by a hundred."""
    assert mc.samples_needed(1.0, 10_000, 0.5) == 40_000
    assert mc.samples_needed(1.0, 1_000, 0.01) == 10_000_000
    assert mc.samples_needed(2.0, 100, 2.0) == 100


def test_the_interval_settles_while_the_run_to_run_spread_falls():
    """ch14's central claim, as a test rather than a paragraph.

    Forty replicates rather than a dozen, and the reason is the chapter's own argument turned on
    itself: the spread between runs is being *estimated*, and an estimate of a spread from twelve
    samples carries about twenty per cent noise of its own — enough to make a ratio of two of them
    land anywhere between three and five. Measuring how uncertain something is, is itself an
    uncertain measurement.
    """
    spec = {"lognormal": {"p10": 1.0, "p90": 6.0}}
    replicates = 40
    widths, mean_spreads, p95_spreads = [], [], []
    for count in (1_000, 10_000, 100_000):
        runs = [mc.sample(spec, count, mc.rng(7000 + count * 13 + r)) for r in range(replicates)]
        widths.append(float(np.mean([mc.half_width(x) for x in runs])))
        mean_spreads.append(float(np.std([float(x.mean()) for x in runs], ddof=1)))
        p95_spreads.append(float(np.std([float(np.percentile(x, 95)) for x in runs], ddof=1)))

    assert widths[-1] == pytest.approx(widths[0], rel=0.08), (
        "the interval is a property of the distribution, so more samples locate it rather than "
        "shrinking it. If this fails, the experiment is measuring something else."
    )

    # The mean is the clean case: its standard error is exactly the population spread over the
    # square root of n, for any distribution with a finite variance.
    ratio = (mean_spreads[0] / mean_spreads[-1]) ** 0.5
    assert ratio == pytest.approx(math.sqrt(10.0), rel=0.2), (
        f"across two decades the spread of the mean fell by {ratio:.2f}x per decade; the law says "
        f"{math.sqrt(10.0):.2f}x"
    )

    # A tail percentile obeys the same law eventually, and more slowly — which is worth asserting
    # separately and loosely rather than pretending the two cases are identical.
    assert all(p95_spreads[i] > p95_spreads[i + 1] * 2.0 for i in range(len(p95_spreads) - 1)), (
        f"the spread of a tail percentile should fall substantially per decade: {p95_spreads}"
    )


def test_a_histogram_is_small_enough_to_ship_and_covers_everything():
    drawn = mc.sample({"triangular": {"minimum": 0, "likely": 3, "maximum": 9}}, 40_000, mc.rng(41))
    histogram = mc.histogram(drawn, bins=64)
    assert len(histogram["counts"]) == 64 and len(histogram["edges"]) == 65
    assert sum(histogram["counts"]) == 40_000, "every draw lands in a bin or the picture lies"
