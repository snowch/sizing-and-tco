"""Every figure the book contains, declared in one place.

One entry per table and per diagram, so that a chapter cannot quietly cite a different run from
the one its prose discusses. ``scripts/render-figures.py`` turns these into files under
``chapters/_generated/`` and ``chapters/_figures/``, which pages pull in with ``{include}`` and
``{image}``; ``scripts/verify-numbers.py`` fails the build when a committed fragment no longer
matches what the results say.

## Figures that are waiting on a measurement

This book inherits ``pending=`` from the template it was built on, and then mostly does not need
it — because a missing measurement here is a *node*, not a figure, and the state propagates down
the graph on its own (``Model.blocked``). A table whose model has an unmeasured constant renders
the affected rows as *not yet measured* without anybody marking anything, and the accompanying
box names the constants and the runner that would take them.

``pending=`` remains for the case the graph cannot see: a figure whose whole result file does not
exist yet, because the experiment it comes from has not been run on the machine it needs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bench import diagrams, tables
from bench.outline import label_of
from bench.stamp import rig_declaration


@dataclass(frozen=True)
class Table:
    """A markdown fragment and every committed result it is rendered from.

    ``result`` is ``None`` for a fragment computed from the model files at build time rather than
    from a run. Before that was possible, such a fragment had to name *some* result to satisfy the
    machinery, and two of them named a compression benchmark they had nothing to do with — so the
    conditions line under a table of unit conversions sent a reader to `logs-line-bytes.json`.
    """

    render: Callable[..., str]
    result: str | None = None
    #: What a fragment with no `result` was assembled from, as a phrase for the conditions line.
    computed_from: str | None = None
    args: tuple = ()
    #: Further stamped results this fragment draws on. A scenario comparison prints two columns
    #: from two runs, and a conditions line naming one of them is a disclosure that is quietly
    #: false — which is what five of them were.
    also: tuple[str, ...] = ()
    #: None means "take the conditions line from `result`"; a name overrides it.
    conditions_from: str | None = None
    #: Why this has not been produced, and what to run. None means it has been.
    pending: str | None = None
    #: What the *Source* line says after the link, in place of "every input on a slider". For
    #: the one page where the link leads somewhere the reader has not been prepared for.
    source_note: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        if self.pending is not None:
            return ()
        return tuple(name for name in (self.result, *self.also) if name)


@dataclass(frozen=True)
class Explorer:
    """An interactive figure, written as HTML with its script inside, and placed on a page by an
    empty ``{div}`` whose classes are ``explorer`` and the figure's name.

    It is generated for the same reason every other figure is: its defaults are a stamped
    result's values, and a copy typed into the page would drift from them. MyST converts raw HTML
    into its own nodes, so the page cannot carry the markup; the renderer reads the generated file
    in place of the empty box (`bench/render.py`).
    """

    render: Callable[..., str]
    result: str
    args: tuple = ()
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,)


@dataclass(frozen=True)
class Diagram:
    """An SVG drawn by :mod:`bench.diagrams`, deterministically.

    ``result`` is ``None`` for a drawing of a rule rather than of a run -- the unit check, say --
    and ``computed_from`` then names what it was drawn from, for the same reason a table has it.
    """

    draw: Callable[..., str]
    alt: str
    result: str | None = None
    computed_from: str | None = None
    args: tuple = ()
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.pending is None and self.result else ()

    def render(self) -> str:
        return self.draw(self.result, *self.args)


#: The reference machine runs the `rig` measurements, and nobody has one attached to CI.
RIG = "take it on the reference machine (`make measure-rig`) and commit the result"
#: Whether a reference machine is declared is a fact about the repository, so it is read from the
#: repository rather than written into a page, where it would go stale the day one is declared.
NO_RIG = (
    ""
    if rig_declaration()
    else (
        " No reference machine is declared yet: `rig/machine.yml` does not exist, so the toolkit"
        " refuses this measurement on every computer."
    )
)

#: Appendix A's graph, described. The chapter's label is derived, as every chNN the renderer
#: prints is: typed into the alt text, it would go stale the first time a chapter moved.
APPENDIX_A_GRAPH_ALT = "The running example as {chapter} leaves it, as a graph"

FIGURES: dict[str, Table | Diagram] = {
    # -- ch01 Point estimates -----------------------------------------------------------------
    # Two rows, not the model's twenty. The page asks "how big" and "how much" and shows that
    # each answer is a range; the rest are a chapter's subject arriving up to nineteen chapters
    # early. Six of them are the model's ceilings, and a ceiling shown without its limit, its
    # verdict or the probability of breaching it is the least readable row in the book — which
    # is why ch13 gives them a table of their own with all three.
    # Both in plain words: ch01 comes before the book names an interval, a sample or a median.
    "point-estimates-outputs": Table(
        render=tables.outputs_in_plain_words,
        result="web_service-reference",
        args=("hosts_recommended", "tco"),
        source_note="the finished model, which ch02 starts building from nothing",
    ),
    # The taxi example, one input moved at a time and then all of them, so that "together is
    # wider than any one alone" is on the page and problem 1.2 can ask how. Computed from the
    # file the problem's test reads, rather than typed into the page and the test separately.
    "point-estimates-commute": Table(
        render=tables.commute_table,
        computed_from="`tests/point_estimates/fixtures/commute.yaml`, the example from problem 1.2",
    ),
    # -- ch13 Monte Carlo -------------------------------------------------------------------------
    "monte-carlo-outputs": Table(render=tables.outputs_table, result="web_service-reference"),
    "monte-carlo-hosts-distribution": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("hosts_recommended",),
        alt="The recommended host count as a distribution",
    ),
    "monte-carlo-tco-distribution": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("tco",),
        alt="The five-year total as a distribution, with the point estimate marked on it",
    ),
    "monte-carlo-ceilings": Table(render=tables.ceilings_table, result="web_service-reference"),
    "monte-carlo-provenance": Table(render=tables.provenance_table, result="web_service-reference"),
    # -- ch14 Correlation and convergence ---------------------------------------------------------
    "correlation-and-convergence-table": Table(
        render=tables.convergence_table, result="convergence-tco"
    ),
    "correlation-and-convergence-curve": Diagram(
        draw=diagrams.convergence,
        result="convergence-tco",
        alt="Run-to-run spread against sample count, with the one-over-root-n law beside it",
    ),
    "correlation-and-convergence-effect": Table(
        render=tables.correlation_table, result="correlation-effect"
    ),
    "correlation-and-convergence-declared": Table(
        render=tables.declared_correlations, result="web_service-reference"
    ),
    # -- appendix E: the web service model --------------------------------------------------
    "appendix-e-web-service-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service-reference",
        alt="The web service model as a dependency graph, coloured by node kind",
    ),
    "appendix-e-web-service-model-formulas": Table(
        render=tables.formulas_table,
        args=("web_service",),
        computed_from="`models/web_service/model.yaml` and its build order",
    ),
    "appendix-e-web-service-model-outputs": Table(
        render=tables.outputs_table,
        result="web_service-reference",
        # Every output but `utilisation`: the ceiling on it prints the same numbers a row later.
        args=(
            "hosts_recommended",
            "hosts",
            "tco",
            "cost_per_million_requests",
            "cost_per_stored_tb_month",
            "capex",
            "annual_opex",
            "annual_energy",
            "queueing_headroom",
            "failure_headroom",
            "cache_fill",
            "disk_fill",
            "scaling_loss",
            "coordination_headroom",
            "residence_time",
            "waiting_time",
            "concurrency",
            "in_flight_unqueued",
            "optimism",
            "headroom_to_peak",
        ),
    ),
    "appendix-e-web-service-model-ceilings": Table(
        render=tables.ceilings_table, result="web_service-reference"
    ),
    "appendix-e-web-service-model-measured": Table(
        render=tables.measured_table,
        result="web_service-reference",
        # The line under the table names the corpus and links the stamp that lists its
        # conditions, rather than the model run, which says nothing about either.
        conditions_from="records-compression",
    ),
    "appendix-e-web-service-model-provenance": Table(
        render=tables.provenance_table, result="web_service-reference"
    ),
    "appendix-e-web-service-model-tornado": Table(
        # Nine rows, as many as the chart above it draws bars.
        render=tables.tornado_table,
        result="web_service-reference",
        args=("tco", 9),
    ),
    "appendix-e-web-service-model-tornado-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="web_service-reference",
        args=("tco",),
        alt="Which input moves the five-year total most",
    ),
    "appendix-e-web-service-model-distribution": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("cost_per_million_requests",),
        alt="Cost per million requests, as a distribution",
    ),
    "appendix-e-web-service-model-scenarios": Table(
        render=tables.scenario_comparison,
        result="web_service-reference",
        args=("web_service-sized_for_growth",),
        also=("web_service-sized_for_growth",),
    ),
    # -- appendix F: the observability model ----------------------------------------------
    "appendix-f-observability-model-formulas": Table(
        render=tables.formulas_table,
        args=("observability",),
        computed_from="`models/observability/model.yaml`",
    ),
    "appendix-f-observability-model-outputs": Table(
        render=tables.outputs_table, result="observability-reference"
    ),
    # The factors beside the product, so the page shows how much wider a product is rather than
    # asserting it.
    "appendix-f-observability-model-spread": Table(
        render=tables.spread_table,
        result="observability-reference",
        args=(
            "label_values_endpoint",
            "label_values_status",
            "label_values_accidental",
            "label_cardinality",
        ),
    ),
    "appendix-f-observability-model-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    "appendix-f-observability-model-ceilings": Table(
        render=tables.ceilings_table, result="observability-reference"
    ),
    "appendix-f-observability-model-measured": Table(
        render=tables.measured_table, result="observability-reference"
    ),
    "appendix-f-observability-model-provenance": Table(
        render=tables.provenance_table, result="observability-reference"
    ),
    # The inputs that move active series, and one row counting those that do not, as the chart
    # beside it draws them.
    "appendix-f-observability-model-tornado": Table(
        render=tables.tornado_of_what_reaches,
        result="observability-reference",
        args=("active_series",),
    ),
    "appendix-f-observability-model-tornado-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="observability-reference",
        args=("active_series",),
        alt="Which input moves the active series count most",
    ),
    "appendix-f-observability-model-cardinality": Diagram(
        draw=diagrams.distribution,
        result="observability-reference",
        args=("label_cardinality",),
        alt="Label cardinality as a distribution: a product of uncertain counts",
    ),
    "appendix-f-observability-model-scenarios": Table(
        render=tables.scenario_comparison,
        result="observability-reference",
        args=("observability-knobs_turned_down",),
        also=("observability-knobs_turned_down",),
    ),
    # -- Appendix H Running the toolkit -------------------------------------------------------------
    "appendix-h-running-the-toolkit-constants": Table(
        render=tables.constants_index,
        computed_from="`bench/results/`, one row per stamped result",
    ),
    "appendix-h-running-the-toolkit-models": Table(
        render=tables.node_kinds_table, result="web_service-reference"
    ),
    # -- ch02 What a workload is ------------------------------------------------------------------
    # The growth explorer: the horizon sets how many times the yearly factor is applied, and the
    # same horizon typed three ways. Its defaults are the stage's own point values.
    "what-a-workload-is-growth": Explorer(
        render=tables.growth_explorer,
        result="web_service_demand_horizon_exponent-reference",
    ),
    "what-a-workload-is-three-ways": Table(
        render=tables.horizon_three_ways,
        result="web_service_demand_horizon_exponent-reference",
    ),
    "what-a-workload-is-stage": Table(
        render=tables.stage_outputs, result="web_service_demand-reference"
    ),
    "what-a-workload-is-stage-shape": Table(
        render=tables.stage_shape, result="web_service_demand-reference"
    ),
    "what-a-workload-is-service": Table(
        render=tables.workload_table, result="web_service_demand-reference"
    ),
    "what-a-workload-is-observability": Table(
        render=tables.workload_table, result="observability-reference"
    ),
    # -- ch03 Where the numbers come from ---------------------------------------------------------
    "where-the-numbers-come-from-stage": Table(
        render=tables.stage_outputs, result="web_service_provenance-reference"
    ),
    "where-the-numbers-come-from-stage-shape": Table(
        render=tables.stage_shape, result="web_service_provenance-reference"
    ),
    "where-the-numbers-come-from-constants": Table(
        render=tables.constants_index,
        computed_from="`bench/results/`, one row per stamped result",
    ),
    "where-the-numbers-come-from-service-provenance": Table(
        render=tables.provenance_table, result="web_service_provenance-reference"
    ),
    # The facts and the vendor's claims, not every input: the page uses the tally and the
    # claims, and the assumptions' sources are written for later chapters. Appendix F has the
    # whole census.
    "where-the-numbers-come-from-provenance": Table(
        render=tables.provenance_table,
        result="observability-reference",
        args=("fact", "vendor_claim"),
    ),
    # The quote and the measurement side by side, which Appendix F says is ch03's point.
    "where-the-numbers-come-from-claim-and-measurement": Table(
        render=tables.claim_beside_measurement,
        result="observability-reference",
        args=(
            "collector_throughput_quoted",
            "collector_throughput_measured",
            "quoted_pipeline_capacity",
            "measured_pipeline_capacity",
        ),
    ),
    # One constant with its shards, so the standard error on this page is worked, not asserted.
    "where-the-numbers-come-from-one-constant": Table(
        render=tables.constant_table, result="logs-line-bytes"
    ),
    "where-the-numbers-come-from-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    "where-the-numbers-come-from-rig": Table(
        render=tables.constant_table,
        result="collector-throughput-per-core",
        pending=f"Collector throughput per core is a timing: {RIG}.{NO_RIG}",
    ),
    # -- ch04 Peak, mean and growth ---------------------------------------------------------------
    # The shapes calculator: compound, linear and levelling from one start, computed with the
    # loader's own formulas. Its factor and horizon are the same stage's point values as ch02's.
    "peak-mean-and-growth-shapes": Explorer(
        render=tables.growth_shapes_explorer,
        result="web_service_demand_horizon_exponent-reference",
    ),
    # This page's own output, from this page's own model: the one embedded lower on the page,
    # so the Source link and the viewer agree. Not the finished model's host count, whose
    # ordering is what problem 19.1 asks the reader to build.
    "peak-mean-and-growth-tornado": Table(
        render=tables.tornado_in_plain_words,
        result="web_service_uncertainty-reference",
        args=("peak_request_rate",),
    ),
    "peak-mean-and-growth-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="web_service_uncertainty-reference",
        args=("peak_request_rate",),
        alt="Which input moves the busy-hour request rate at the horizon most",
    ),
    "peak-mean-and-growth-demand": Diagram(
        draw=diagrams.distribution_in_plain_words,
        result="web_service_uncertainty-reference",
        args=("peak_request_rate",),
        alt="The busy-hour request rate at the horizon, as a band",
    ),
    # -- ch05 Little's law ------------------------------------------------------------------------
    "littles-law-outputs": Table(
        render=tables.outputs_table, result="web_service_littles_law-reference"
    ),
    # How often the bought fleet cannot keep up, as the bound the stamped quantiles make exact:
    # a share the model produced may not be typed into the page, in digits or in words.
    "littles-law-over-capacity": Table(
        render=tables.share_past,
        result="web_service_littles_law-reference",
        args=(
            "utilisation",
            1.0,
            "utilisation above one: the busy hour needs more cores than the fleet has",
        ),
    ),
    "littles-law-in-flight": Diagram(
        draw=diagrams.distribution,
        result="web_service_littles_law-reference",
        args=("in_flight_unqueued",),
        alt="Requests in flight at the busy hour, as a distribution",
    ),
    "littles-law-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service_littles_law-reference",
        args=("in_flight_unqueued", True),
        alt="The sub-graph that produces the number of requests in flight",
    ),
    # -- ch06 Queueing and the knee ---------------------------------------------------------------
    "queueing-and-the-knee-curve": Diagram(
        draw=diagrams.queueing_curve,
        result="queueing-curve",
        alt="Residence time against utilisation: flat, and then vertical",
    ),
    "queueing-and-the-knee-zoom": Diagram(
        draw=diagrams.queueing_zoom,
        result="queueing-curve",
        alt="The queueing curve drawn over two stretches, each filling its own axes: the same "
        "shape twice, with the bend wherever the axis stops",
    ),
    "queueing-and-the-knee-table": Table(render=tables.queueing_table, result="queueing-curve"),
    "queueing-and-the-knee-ceilings": Table(
        render=tables.ceilings_table, result="web_service_queueing-reference"
    ),
    # -- ch07 When adding servers stops helping ---------------------------------------------------
    "when-adding-servers-stops-helping-curve": Diagram(
        draw=diagrams.scaling_curve,
        result="scaling-curve",
        alt="Throughput against host count, against the straight line a budget assumes",
    ),
    "when-adding-servers-stops-helping-table": Table(
        render=tables.scaling_table, result="scaling-curve"
    ),
    # The rows the page argues from, in its order: the two that double by definition, the
    # throughput that does not, the efficiency, the two utilisations, the queueing time computed
    # from the optimistic one, and the peak, which no budget moves.
    "when-adding-servers-stops-helping-scenarios": Table(
        render=tables.scenario_ratios,
        result="web_service-reference",
        args=(
            "web_service-twice_the_hosts",
            "hosts",
            "linear_throughput",
            "achievable_throughput",
            "scaling_efficiency",
            "utilisation",
            "utilisation_including_coordination",
            "waiting_time",
            "peak_hosts",
        ),
        also=("web_service-twice_the_hosts",),
    ),
    # ch06's ceilings table, once per scenario, on the three ceilings this page is about.
    "when-adding-servers-stops-helping-ceilings-reference": Table(
        render=tables.ceilings_table,
        result="web_service-reference",
        args=("queueing_headroom", "coordination_headroom", "scaling_loss"),
    ),
    "when-adding-servers-stops-helping-ceilings-doubled": Table(
        render=tables.ceilings_table,
        result="web_service-twice_the_hosts",
        args=("queueing_headroom", "coordination_headroom", "scaling_loss"),
    ),
    # -- ch08 Regime changes ----------------------------------------------------------------------
    "regime-changes-knee": Diagram(
        draw=diagrams.queueing_curve,
        result="queueing-curve",
        alt="Residence time against utilisation: one division, rising slowly while much of the "
        "fleet is idle and steeply as it nears full",
    ),
    # The running example's ceilings as this chapter leaves it, not the observability model's:
    # the page's viewer shows this model, and the working set row is the ceiling ch08 adds.
    "regime-changes-ceilings": Table(
        render=tables.ceilings_table, result="web_service_regime-reference"
    ),
    # Three uncertain counts and their product, each with its band, so the page can show that
    # the product is wider than any of them rather than say so.
    "regime-changes-label-bands": Table(
        render=tables.bands_in_plain_words,
        result="observability-reference",
        args=(
            "label_values_endpoint",
            "label_values_status",
            "label_values_accidental",
            "label_cardinality",
        ),
    ),
    # -- ch09 Capacity ----------------------------------------------------------------------------
    # The chain alone, packed into the columns it needs, so its labels can be read: drawn with
    # the whole stage faded behind it, the canvas was three times as wide and the text a third
    # the size.
    "capacity-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service_capacity-reference",
        args=("hosts_for_storage", True),
        alt="The chain from the records held to how many hosts their disks need",
    ),
    # Two rows: the chain this chapter follows and what it asks for. Its ceiling is in
    # capacity-disk-fill, in the form ch06 taught, because a fill with no limit beside it cannot
    # be read. Everything else in the stage is an earlier chapter's subject.
    "capacity-outputs": Table(
        render=tables.outputs_table,
        result="web_service_capacity-reference",
        args=("raw_data", "hosts_for_storage"),
    ),
    # The chain's ceiling: one row of ch06's table, with its limit, verdict and breach shares.
    "capacity-disk-fill": Table(
        render=tables.ceilings_table,
        result="web_service_capacity-reference",
        args=("disk_fill",),
    ),
    # Which term's uncertainty moves the disk: the chain's three uncertain inputs. Replication
    # and the disk margin are decisions with one value, so no tornado can show them, which is
    # the page's point. In ch04's plain words for the two ends, because ch13 names a percentile.
    "capacity-tornado": Table(
        render=tables.tornado_in_plain_words,
        result="web_service_capacity-reference",
        args=("raw_data", 3),
    ),
    "capacity-measured": Table(
        render=tables.measured_table, result="web_service_capacity-reference"
    ),
    # -- ch10 Bandwidth and the binding constraint ------------------------------------------------
    "bandwidth-and-the-binding-constraint-table": Table(
        render=tables.binding_table, result="binding-constraint"
    ),
    # What each chain asks for with every input at its point estimate. The three are close, which
    # is why the answer changes hands so easily across the futures, and it is what the slider
    # exercise starts from.
    "bandwidth-and-the-binding-constraint-point": Table(
        render=tables.stage_outputs,
        result="web_service_binding-reference",
        args=("hosts_for_requests", "hosts_for_memory", "hosts_for_storage", "hosts_recommended"),
    ),
    # The shortfall of a fleet sized on the usual winner, as a median and as an average over
    # every future. The median over the short futures alone is problem 10.2's, and is not here.
    "bandwidth-and-the-binding-constraint-shortfall": Table(
        render=tables.binding_shortfall_table, result="binding-constraint"
    ),
    "bandwidth-and-the-binding-constraint-requests": Diagram(
        draw=diagrams.distribution,
        result="web_service_binding-reference",
        args=("hosts_for_requests",),
        alt="The host count the request chain asks for",
    ),
    "bandwidth-and-the-binding-constraint-memory": Diagram(
        draw=diagrams.distribution,
        result="web_service_binding-reference",
        args=("hosts_for_memory",),
        alt="The host count the working set asks for",
    ),
    "bandwidth-and-the-binding-constraint-storage": Diagram(
        draw=diagrams.distribution,
        result="web_service_binding-reference",
        args=("hosts_for_storage",),
        alt="The host count the data on disk asks for",
    ),
    # Two generations in one pool: what the old hosts change, chain by chain, and what routing
    # requests equally costs.
    "bandwidth-and-the-binding-constraint-mixed-pool": Table(
        render=tables.mixed_pool_chains,
        result="mixed-pool",
        also=("mixed_pool-reference", "mixed_pool-replace"),
    ),
    # -- ch11 Headroom and failure domains --------------------------------------------------------
    "headroom-and-failure-domains-service": Table(
        render=tables.ceilings_table, result="web_service_headroom-reference"
    ),
    "headroom-and-failure-domains-observability": Table(
        render=tables.ceilings_table, result="observability-reference"
    ),
    "headroom-and-failure-domains-margins": Table(
        render=tables.margins_table, result="web_service_headroom-reference"
    ),
    # The mixed pool as bought, checked with the old hosts kept and after they retire.
    "headroom-and-failure-domains-mixed-pool": Table(
        render=tables.mixed_pool_ceilings,
        result="mixed-pool",
        also=("mixed_pool-reference", "mixed_pool-old_retired", "mixed_pool-replace"),
    ),
    # -- ch12 The sizing model --------------------------------------------------------------------
    # The answer, the decision, and the three chains the answer was the largest of.
    "the-sizing-model-outputs": Table(
        render=tables.outputs_table,
        result="web_service_sizing-reference",
        args=(
            "hosts_recommended",
            "hosts",
            "hosts_for_requests",
            "hosts_for_memory",
            "hosts_for_storage",
        ),
    ),
    "the-sizing-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service_sizing-reference",
        args=("hosts_recommended",),
        alt="Everything that feeds the recommended host count",
    ),
    "the-sizing-model-ceilings": Table(
        render=tables.ceilings_table, result="web_service_sizing-reference"
    ),
    "the-sizing-model-resized": Table(
        render=tables.ceilings_table, result="web_service-sized_for_growth"
    ),
    # The growth fleet's size, which the resized ceilings below it are for. The same two rows as
    # the first outputs table, so the reader sets recommended against bought twice.
    "the-sizing-model-growth-fleet": Table(
        render=tables.outputs_table,
        result="web_service-sized_for_growth",
        args=("hosts_recommended", "hosts"),
    ),
    # Where the point estimate sits against the middle answer, which the prose reads off it. In
    # plain words, because the page comes before ch13.
    "the-sizing-model-hosts": Diagram(
        draw=diagrams.distribution_against_the_middle,
        result="web_service_sizing-reference",
        args=("hosts_recommended",),
        alt="The recommended host count across the model's futures, with the point estimate and "
        "the middle answer marked",
    ),
    # -- ch15 Capex, opex and where the total stops -----------------------------------------------
    "capex-opex-and-lifecycle-split": Table(
        render=tables.cost_split_table, result="web_service-reference"
    ),
    # The capital, the yearly running cost Problem 15.1 needs, and the total whose interval the
    # split table does not give. Not the model's every output: ch13 and Appendix E carry those.
    "capex-opex-and-lifecycle-outputs": Table(
        render=tables.outputs_table,
        result="web_service-reference",
        args=("capex", "annual_opex", "tco"),
    ),
    "capex-opex-and-lifecycle-tornado": Table(
        render=tables.tornado_table, result="web_service-reference", args=("annual_opex",)
    ),
    # -- ch16 Power first -------------------------------------------------------------------------
    "power-first-wall": Diagram(
        draw=diagrams.power_wall,
        result="power-first-sweep",
        alt="Facility power and five-year cost against host count: the allocation is a wall on "
        "the power axis and there is nothing across the cost axis",
    ),
    "power-first-scenarios": Table(
        # The rows the page argues from, in its order: what demand asks for and what power
        # allows; the money, which falls with the fleet; the energy, in its unit; and the
        # response time, which does not fall. Not the model's every output: the ceilings table
        # below carries the ceilings, and a second copy of them here was read by nobody.
        render=tables.scenario_ratios,
        result="web_service-reference",
        args=(
            "web_service-power_first",
            "hosts_recommended",
            "hosts",
            "capex",
            "annual_opex",
            "tco",
            "cost_per_million_requests",
            "annual_energy",
            "residence_time",
        ),
        also=("web_service-power_first",),
    ),
    "power-first-ceilings": Table(render=tables.ceilings_table, result="web_service-power_first"),
    "power-first-breaches": Table(
        # The three ceilings the power-first fleet is over, and how often the reference fleet
        # already broke them: a breach rate beside the one it came from. In ceilings_table's
        # order (by node name), so the two tables read down the same way.
        render=tables.breach_comparison,
        result="web_service-reference",
        args=("web_service-power_first", "cache_fill", "coordination_headroom", "disk_fill"),
        also=("web_service-power_first",),
    ),
    "power-first-tornado": Table(
        # Two rows because two inputs are all that can move the kilowatt-hours: the formula is
        # hosts x host power x PUE x hours, the host count is a decision with no range, and the
        # hours are a definition. The six zero rows below them were the page's point made by
        # absence, and read as a table nobody chose.
        render=tables.tornado_table,
        result="web_service-reference",
        args=("annual_energy", 2),
    ),
    # -- ch17 Unit economics ----------------------------------------------------------------------
    "unit-economics-distribution": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("cost_per_million_requests",),
        alt="Cost per million requests, as a distribution",
    ),
    "unit-economics-tornado": Table(
        render=tables.tornado_table,
        result="web_service-reference",
        args=("cost_per_million_requests",),
    ),
    # How far the model's straight-line average overstates a compounding holding, across the
    # growth factor's declared band. A view of the model file, like the formula sheet: the model
    # keeps the straight line, and this is what that costs the unit cost.
    "unit-economics-straight-line": Table(
        render=tables.straight_line_overstatement,
        args=("web_service",),
        computed_from=(
            "`models/web_service/model.yaml`: the growth factor's declared p10 and p90, and the "
            "horizon"
        ),
    ),
    "unit-economics-per-stored": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("cost_per_stored_tb_month",),
        alt="The same total over a different denominator: cost per stored TB per month",
    ),
    # -- ch18 The five-year model -----------------------------------------------------------------
    "the-five-year-model-seam": Diagram(
        draw=diagrams.seam,
        result="observability-reference",
        args=("web_service-reference",),
        alt="The web service model's computed cost per stored terabyte-month and the "
        "observability model's assumed storage price, on one logarithmic axis, with the "
        "single number that would cross between them",
    ),
    # The seam's two ends in one table: the price one model computes, the price the other
    # assumes, and what the assumed one buys. Both results, so the Source line names both.
    "the-five-year-model-seam-ends": Table(
        render=tables.seam_table,
        result="observability-reference",
        args=("web_service-reference",),
        also=("web_service-reference",),
    ),
    # What growth, swung on its own, does to each side of the seam: it pushes them apart.
    "the-five-year-model-seam-growth": Table(
        render=tables.seam_growth_table,
        result="observability-reference",
        args=("web_service-reference",),
        also=("web_service-reference",),
    ),
    "the-five-year-model-split": Table(
        render=tables.cost_split_table, result="web_service-reference"
    ),
    # -- ch19 Which input to go and measure -------------------------------------------------------
    "which-input-is-the-answer-tco": Diagram(
        draw=diagrams.tornado_chart,
        result="web_service-reference",
        args=("tco",),
        alt="Which input moves the five-year total most",
    ),
    "which-input-is-the-answer-observability": Diagram(
        draw=diagrams.tornado_chart,
        result="observability-reference",
        args=("known_stored",),
        alt="Which input moves the retention store most",
    ),
    "which-input-is-the-answer-residence": Table(
        render=tables.tornado_of_what_moves,
        result="web_service-reference",
        args=("residence_time", tables.RESIDENCE_HEADING),
    ),
    "which-input-is-the-answer-worth-service": Table(
        render=tables.value_of_information_table,
        result="value-of-information",
        args=("web_service", "tco"),
    ),
    "which-input-is-the-answer-worth-hosts": Table(
        render=tables.value_of_information_table,
        result="value-of-information",
        args=("web_service", "hosts_recommended"),
    ),
    "which-input-is-the-answer-worth-observability": Table(
        render=tables.value_of_information_table,
        result="value-of-information",
        args=("observability", "known_stored"),
    ),
    # -- ch22 What the model got wrong ------------------------------------------------------------
    "what-the-model-got-wrong-attribution": Table(
        render=tables.postmortem_table, result="postmortem", args=("complete",)
    ),
    "what-the-model-got-wrong-incomplete": Table(
        render=tables.postmortem_table, result="postmortem", args=("incomplete",)
    ),
    "what-the-model-got-wrong-ceilings": Table(
        render=tables.ceilings_table, result="web_service-reference"
    ),
    "what-the-model-got-wrong-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    # -- ch20 The missing node --------------------------------------------------------------------
    "the-missing-node-outputs": Table(
        render=tables.outputs_table,
        result="observability-reference",
        args=("metrics_ingest", "logs_ingest", "traces_ingest", "known_ingest"),
    ),
    "the-missing-node-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    # ch20's hard case: the problem 20.3 model file, missing a line and with no node to say so,
    # beside the invented invoice it cannot reach. Stamped by bench/run_missing_node.py.
    "the-missing-node-fixture": Table(
        render=tables.fixture_against_invoice, result="the-missing-node-fixture"
    ),
    # -- ch21 A TCO for a finance audience --------------------------------------------------------
    # Chosen for this page: what each design buys, costs and risks. The full comparison, every
    # output and every ceiling, is Appendix E's.
    "a-tco-for-finance-scenarios": Table(
        render=tables.scenario_decision,
        result="web_service-reference",
        args=("web_service-sized_for_growth",),
        also=("web_service-sized_for_growth",),
    ),
    # The median marked, because the page offers it as the first number to choose.
    "a-tco-for-finance-distribution": Diagram(
        draw=diagrams.distribution_with_median,
        result="web_service-reference",
        args=("tco",),
        alt="The five-year total as a distribution, with the point estimate and the median on it",
    ),
    "a-tco-for-finance-ceilings": Table(
        render=tables.ceilings_table, result="web_service-reference"
    ),
    # The vendor claims, which are what this page's reader asks about; the rest are counted.
    "a-tco-for-finance-provenance": Table(
        render=tables.provenance_table, result="web_service-reference", args=("vendor_claim",)
    ),
    # -- ch22 Comparing two TCOs ------------------------------------------------------------------
    # Every table here was chosen for this page. The two quote results exist and have viewers,
    # but a reader is not shown the twenty-one-row outputs table twice: the comparison result
    # holds the rows the argument needs, and the quotes are linked beside it.
    "comparing-two-tcos-quotes": Table(
        render=tables.comparison_quotes,
        result="comparison",
        also=("web_service-incumbent", "web_service-challenger"),
    ),
    "comparing-two-tcos-lines": Table(render=tables.comparison_lines, result="comparison"),
    "comparing-two-tcos-difference": Diagram(
        draw=diagrams.paired_difference,
        result="comparison",
        alt="The difference between the two five-year totals, future by future, with the tie "
        "marked and the share of futures either side of it",
    ),
    "comparing-two-tcos-totals": Table(render=tables.comparison_totals, result="comparison"),
    "comparing-two-tcos-paired": Table(render=tables.comparison_paired, result="comparison"),
    "comparing-two-tcos-ceilings": Table(
        render=tables.comparison_ceilings,
        result="comparison",
        also=("web_service-incumbent", "web_service-challenger"),
    ),
    "comparing-two-tcos-break-even": Table(
        render=tables.comparison_break_even, result="comparison"
    ),
    # Keep the old generation or replace it: the same subtraction, on the mixed pool model.
    "comparing-two-tcos-keep-or-replace": Table(
        render=tables.mixed_pool_keep_vs_replace,
        result="mixed-pool",
        also=("mixed_pool-reference", "mixed_pool-replace", "mixed_pool-keep_routed_equally"),
    ),
    "comparing-two-tcos-keep-or-replace-lines": Table(
        render=tables.mixed_pool_keep_vs_replace_lines,
        result="mixed-pool",
        also=("mixed_pool-reference", "mixed_pool-replace"),
    ),
    "comparing-two-tcos-tornado": Diagram(
        draw=diagrams.tornado_chart,
        result="comparison",
        args=("difference",),
        alt="Which shared input moves the difference between the two totals, and how many "
        "do not move it at all",
    ),
    # -- ch23 The seller's TCO ---------------------------------------------------------------------
    # The seller's model for a customer it has not met, as a brochure and as it should be built;
    # then the same model on ch22's customer, beside ch22's bottom-up answer.
    "the-sellers-tco-scenarios": Table(
        render=tables.seller_scenarios,
        result="seller",
        also=("sellers_tco-reference", "sellers_tco-brochure"),
    ),
    "the-sellers-tco-by-year": Diagram(
        draw=diagrams.seller_by_year,
        result="seller",
        alt="Each option's spend added up year by year for one customer, starting from the cost "
        "of the move, with the year each proposal pays back marked",
    ),
    "the-sellers-tco-breakdown": Diagram(
        draw=diagrams.seller_breakdown,
        result="seller",
        alt="Each proposal's five-year spend split into the part of today's spend that stays, "
        "the proposed hosts and the move, against the customer's own total",
    ),
    "the-sellers-tco-plane": Diagram(
        draw=diagrams.seller_plane,
        result="seller",
        alt="The transfer factor against the share of the spend that scales, split by the line "
        "where the saving is zero, with the seller's futures as dots and three settings marked",
    ),
    "the-sellers-tco-tornado": Diagram(
        draw=diagrams.tornado_chart,
        result="sellers_tco-reference",
        args=("saving",),
        alt="Which input moves the seller's saving most, for a customer the seller has not met",
    ),
    "the-sellers-tco-ladder": Table(
        render=tables.seller_ladder,
        result="seller",
        also=("sellers_tco-ch22_customer", "comparison", "web_service-incumbent"),
    ),
    "the-sellers-tco-transfer": Diagram(
        draw=diagrams.seller_transfer,
        result="seller",
        alt="The five-year saving for one customer against the share of the benchmark that "
        "carries over, for three guesses at the share of the spend that scales, with the "
        "bottom-up answer marked",
    ),
    # -- appendices ------------------------------------------------------------------------------------
    # The web service model: every model file the page quotes is that one.
    "appendix-a-dsl-reference-kinds": Table(
        render=tables.node_kinds_table, result="web_service-reference"
    ),
    "appendix-a-dsl-reference-shapes": Table(
        render=tables.distribution_keys,
        computed_from="`sizing/mc.py`: each shape in `SHAPES`, and its function's parameters",
    ),
    # Three columns, drawn compact so a phone shows its labels at a size they can be read at.
    "appendix-a-dsl-reference-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service_demand-reference",
        args=(None, False, True),
        alt=APPENDIX_A_GRAPH_ALT.format(chapter=label_of("what_a_workload_is")),
    ),
    "appendix-b-monte-carlo-module-convergence": Table(
        render=tables.convergence_table, result="convergence-tco"
    ),
    "appendix-c-distributions-shapes": Diagram(
        draw=diagrams.distribution_shapes,
        result="web_service-reference",
        alt="The four distributions, drawn from the percentile functions the sampler uses",
    ),
    "appendix-c-distributions-correlation": Table(
        render=tables.correlation_table, result="correlation-effect"
    ),
    "appendix-d-units-algebra": Table(
        render=tables.unit_algebra_table,
        computed_from="`sizing/units.py`, which worked out every row",
    ),
    "appendix-d-units-verdicts": Table(
        render=tables.unit_check_table,
        computed_from="`sizing/evaluate.py`'s unit check, which reached every verdict",
    ),
    "appendix-d-units-conversions": Table(
        render=tables.conversions_table,
        computed_from="`models/`",
    ),
    "appendix-g-glossary-terms": Table(
        render=tables.glossary_table,
        computed_from="`bench/outline.py` and `bench/tables.py`",
    ),
    # The four targets, read from the dict the stamp checks against: a table wraps on a phone,
    # where the dict quoted as code ran off the edge.
    "appendix-g-glossary-targets": Table(
        render=tables.targets_table,
        computed_from="`bench/stamp.py`",
    ),
}


def cited_results() -> set[str]:
    return {result for figure in FIGURES.values() for result in figure.sources}


def pending_results() -> dict[str, str]:
    return {
        figure.result: figure.pending for figure in FIGURES.values() if figure.pending is not None
    }
