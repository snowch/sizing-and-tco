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

    @property
    def sources(self) -> tuple[str, ...]:
        if self.pending is not None:
            return ()
        return tuple(name for name in (self.result, *self.also) if name)


@dataclass(frozen=True)
class Diagram:
    """An SVG drawn by :mod:`bench.diagrams`, deterministically."""

    draw: Callable[..., str]
    alt: str
    result: str
    args: tuple = ()
    pending: str | None = None

    @property
    def sources(self) -> tuple[str, ...]:
        return (self.result,) if self.pending is None else ()

    def render(self) -> str:
        return self.draw(self.result, *self.args)


#: The reference machine runs the `rig` measurements, and nobody has one attached to CI.
RIG = "take it on the reference machine (`make measure-rig`) and commit the result"

FIGURES: dict[str, Table | Diagram] = {
    # -- ch01 What one number hides -----------------------------------------------------------
    # Two rows, not the model's twenty. The page asks "how big" and "how much" and shows that
    # each answer is a range; the rest are a chapter's subject arriving up to nineteen chapters
    # early. Six of them are the model's ceilings, and a ceiling shown without its limit, its
    # verdict or the probability of breaching it is the least readable row in the book — which
    # is why ch13 gives them a table of their own with all three.
    "what-one-number-hides-outputs": Table(
        render=tables.outputs_table,
        result="web_service-reference",
        args=("hosts_recommended", "tco"),
    ),
    "what-one-number-hides-tco-distribution": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("tco",),
        alt="The five-year total cost as a distribution, with the point estimate marked on it",
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
    "monte-carlo-ceilings-resized": Table(
        render=tables.ceilings_table, result="web_service-sized_for_growth"
    ),
    "monte-carlo-provenance": Table(render=tables.provenance_table, result="web_service-reference"),
    "monte-carlo-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service-reference",
        args=("tco",),
        alt="The sub-graph that feeds the five-year total",
    ),
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
    "appendix-e-web-service-model-outputs": Table(
        render=tables.outputs_table, result="web_service-reference"
    ),
    "appendix-e-web-service-model-ceilings": Table(
        render=tables.ceilings_table, result="web_service-reference"
    ),
    "appendix-e-web-service-model-measured": Table(
        render=tables.measured_table, result="web_service-reference"
    ),
    "appendix-e-web-service-model-provenance": Table(
        render=tables.provenance_table, result="web_service-reference"
    ),
    "appendix-e-web-service-model-tornado": Table(
        render=tables.tornado_table, result="web_service-reference", args=("tco",)
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
    "appendix-f-observability-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="observability-reference",
        alt="The observability model as a dependency graph, with the unmeasured chain marked",
    ),
    "appendix-f-observability-model-outputs": Table(
        render=tables.outputs_table, result="observability-reference"
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
    "appendix-f-observability-model-tornado": Table(
        render=tables.tornado_table, result="observability-reference", args=("active_series",)
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
    "where-the-numbers-come-from-provenance": Table(
        render=tables.provenance_table, result="observability-reference"
    ),
    "where-the-numbers-come-from-measured": Table(
        render=tables.measured_table, result="observability-reference"
    ),
    "where-the-numbers-come-from-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    "where-the-numbers-come-from-rig": Table(
        render=tables.constant_table,
        result="collector-throughput-per-core",
        pending=f"Collector throughput per core is a timing: {RIG}.",
    ),
    # -- ch04 Peak, mean and growth ---------------------------------------------------------------
    "peak-mean-and-growth-tornado": Table(
        render=tables.tornado_table, result="web_service-reference", args=("hosts_recommended",)
    ),
    "peak-mean-and-growth-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="web_service-reference",
        args=("hosts_recommended",),
        alt="Which input moves the recommended host count most",
    ),
    "peak-mean-and-growth-demand": Diagram(
        draw=diagrams.distribution,
        result="web_service_uncertainty-reference",
        args=("peak_request_rate",),
        alt="The busy-hour request rate at the horizon, as a distribution",
    ),
    # -- ch05 Little's law ------------------------------------------------------------------------
    "littles-law-outputs": Table(
        render=tables.outputs_table, result="web_service_littles_law-reference"
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
        args=("in_flight_unqueued",),
        alt="The sub-graph that produces the number of requests in flight",
    ),
    # -- ch06 Queueing and the knee ---------------------------------------------------------------
    "queueing-and-the-knee-curve": Diagram(
        draw=diagrams.queueing_curve,
        result="queueing-curve",
        alt="Residence time against utilisation: flat, and then vertical",
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
    "when-adding-servers-stops-helping-scenarios": Table(
        render=tables.scenario_comparison,
        result="web_service-reference",
        args=("web_service-twice_the_hosts",),
        also=("web_service-twice_the_hosts",),
    ),
    # -- ch08 Regime changes ----------------------------------------------------------------------
    "regime-changes-cardinality": Diagram(
        draw=diagrams.distribution,
        result="observability-reference",
        args=("label_cardinality",),
        alt="Label cardinality: a product of uncertain counts",
    ),
    "regime-changes-knee": Diagram(
        draw=diagrams.queueing_curve,
        result="queueing-curve",
        alt="The queueing knee, as a regime change a multiplication cannot express",
    ),
    "regime-changes-ceilings": Table(
        render=tables.ceilings_table, result="observability-reference"
    ),
    "regime-changes-tornado": Table(
        render=tables.tornado_table, result="observability-reference", args=("active_series",)
    ),
    # -- ch09 Capacity ----------------------------------------------------------------------------
    "capacity-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service_capacity-reference",
        args=("hosts_for_storage",),
        alt="The chain from what you need to store to how many hosts you must buy",
    ),
    "capacity-outputs": Table(render=tables.outputs_table, result="web_service_capacity-reference"),
    "capacity-measured": Table(
        render=tables.measured_table, result="web_service_capacity-reference"
    ),
    # -- ch10 Bandwidth and the binding constraint ------------------------------------------------
    "bandwidth-and-the-binding-constraint-table": Table(
        render=tables.binding_table, result="binding-constraint"
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
    # -- ch11 Headroom and failure domains --------------------------------------------------------
    "headroom-and-failure-domains-service": Table(
        render=tables.ceilings_table, result="web_service_headroom-reference"
    ),
    "headroom-and-failure-domains-observability": Table(
        render=tables.ceilings_table, result="observability-reference"
    ),
    # -- ch12 The sizing model --------------------------------------------------------------------
    "the-sizing-model-outputs": Table(
        render=tables.outputs_table, result="web_service_sizing-reference"
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
    "the-sizing-model-hosts": Diagram(
        draw=diagrams.distribution,
        result="web_service_sizing-reference",
        args=("hosts_recommended",),
        alt="The recommended host count, as a distribution",
    ),
    # -- ch15 Capex, opex and where the total stops -----------------------------------------------
    "capex-opex-and-lifecycle-split": Table(
        render=tables.cost_split_table, result="web_service-reference"
    ),
    "capex-opex-and-lifecycle-outputs": Table(
        render=tables.outputs_table, result="web_service-reference"
    ),
    "capex-opex-and-lifecycle-tornado": Table(
        render=tables.tornado_table, result="web_service-reference", args=("annual_opex",)
    ),
    # -- ch16 Power first -------------------------------------------------------------------------
    "power-first-scenarios": Table(
        render=tables.scenario_comparison,
        result="web_service-reference",
        args=("web_service-power_first",),
        also=("web_service-power_first",),
    ),
    "power-first-ceilings": Table(render=tables.ceilings_table, result="web_service-power_first"),
    "power-first-tornado": Table(
        render=tables.tornado_table, result="web_service-reference", args=("annual_energy",)
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
    "unit-economics-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service-reference",
        args=("cost_per_million_requests",),
        alt="Everything that feeds the unit cost, including its denominator",
    ),
    "unit-economics-per-stored": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("cost_per_stored_tb_month",),
        alt="The same total over a different denominator: cost per stored TB per month",
    ),
    # -- ch18 The five-year model -----------------------------------------------------------------
    "the-five-year-model-service": Table(
        render=tables.outputs_table, result="web_service-reference"
    ),
    "the-five-year-model-observability": Table(
        render=tables.outputs_table, result="observability-reference"
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
        render=tables.tornado_table, result="web_service-reference", args=("residence_time",)
    ),
    "which-input-is-the-answer-correlation": Table(
        render=tables.correlation_table, result="correlation-effect"
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
        render=tables.outputs_table, result="observability-reference"
    ),
    "the-missing-node-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    "the-missing-node-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="observability-reference",
        args=("known_ingest",),
        alt="What feeds the ingest total, and what is missing from it",
    ),
    # -- ch21 A TCO for a finance audience --------------------------------------------------------
    "a-tco-for-finance-scenarios": Table(
        render=tables.scenario_comparison,
        result="web_service-reference",
        args=("web_service-sized_for_growth",),
        also=("web_service-sized_for_growth",),
    ),
    "a-tco-for-finance-distribution": Diagram(
        draw=diagrams.distribution,
        result="web_service-reference",
        args=("tco",),
        alt="The five-year total as a distribution, with the point estimate on it",
    ),
    "a-tco-for-finance-ceilings": Table(
        render=tables.ceilings_table, result="web_service-reference"
    ),
    "a-tco-for-finance-provenance": Table(
        render=tables.provenance_table, result="web_service-reference"
    ),
    # -- appendices ------------------------------------------------------------------------------------
    "appendix-a-dsl-reference-kinds": Table(
        render=tables.node_kinds_table, result="observability-reference"
    ),
    "appendix-a-dsl-reference-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="web_service_demand-reference",
        alt="The smallest model in the book, as a graph",
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
    "appendix-d-units-conversions": Table(
        render=tables.conversions_table,
        computed_from="`models/`",
    ),
    "appendix-g-glossary-terms": Table(
        render=tables.glossary_table,
        computed_from="`bench/outline.py` and `bench/tables.py`",
    ),
}


def cited_results() -> set[str]:
    return {result for figure in FIGURES.values() for result in figure.sources}


def pending_results() -> dict[str, str]:
    return {
        figure.result: figure.pending for figure in FIGURES.values() if figure.pending is not None
    }
