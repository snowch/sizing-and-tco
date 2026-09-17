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
    # -- the preface ---------------------------------------------------------------------
    "preface-storage-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "preface-tco-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The five-year total cost as a distribution, with the point estimate marked on it",
    ),
    # -- ch13 Monte Carlo ----------------------------------------------------------------
    "monte-carlo-outputs": Table(render=tables.outputs_table, result="storage_cluster-reference"),
    "monte-carlo-nodes-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("nodes_recommended",),
        alt="The recommended node count as a distribution",
    ),
    "monte-carlo-tco-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The five-year total as a distribution, with the point estimate marked on it",
    ),
    "monte-carlo-ceilings": Table(render=tables.ceilings_table, result="storage_cluster-reference"),
    "monte-carlo-ceilings-resized": Table(
        render=tables.ceilings_table, result="storage_cluster-sized_for_growth"
    ),
    "monte-carlo-provenance": Table(
        render=tables.provenance_table, result="storage_cluster-reference"
    ),
    "monte-carlo-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The sub-graph that feeds the five-year total",
    ),
    # -- ch14 Correlation and convergence ------------------------------------------------
    "correlation-and-convergence-table": Table(
        render=tables.convergence_table, result="convergence-storage-tco"
    ),
    "correlation-and-convergence-curve": Diagram(
        draw=diagrams.convergence,
        result="convergence-storage-tco",
        alt="Run-to-run spread against sample count, with the one-over-root-n law beside it",
    ),
    "correlation-and-convergence-effect": Table(
        render=tables.correlation_table, result="correlation-effect"
    ),
    "correlation-and-convergence-declared": Table(
        render=tables.declared_correlations, result="observability-reference"
    ),
    # -- appendix E: the storage model ---------------------------------------------------
    "appendix-e-storage-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        alt="The storage cluster model as a dependency graph, coloured by node kind",
    ),
    "appendix-e-storage-model-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-ceilings": Table(
        render=tables.ceilings_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-measured": Table(
        render=tables.measured_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-provenance": Table(
        render=tables.provenance_table, result="storage_cluster-reference"
    ),
    "appendix-e-storage-model-tornado": Table(
        render=tables.tornado_table, result="storage_cluster-reference", args=("tco",)
    ),
    "appendix-e-storage-model-tornado-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="storage_cluster-reference",
        args=("tco",),
        alt="Which input moves the five-year total most",
    ),
    "appendix-e-storage-model-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("cost_per_usable_tb_month",),
        alt="Cost per usable TB per month, as a distribution",
    ),
    "appendix-e-storage-model-scenarios": Table(
        render=tables.scenario_comparison,
        result="storage_cluster-reference",
        args=("storage_cluster-sized_for_growth",),
        also=("storage_cluster-sized_for_growth",),
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
    # -- ch00 Prerequisites and setup ------------------------------------------------------
    "prerequisites-and-setup-constants": Table(
        render=tables.constants_index,
        computed_from="`bench/results/`, one row per stamped result",
    ),
    "prerequisites-and-setup-models": Table(
        render=tables.node_kinds_table, result="storage_cluster-reference"
    ),
    # -- ch01 Reading a model ---------------------------------------------------------------
    "reading-a-model-kinds": Table(
        render=tables.node_kinds_table, result="storage_cluster-reference"
    ),
    "reading-a-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        alt="A model as a graph, coloured by node kind and by provenance",
    ),
    "reading-a-model-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "reading-a-model-conversions": Table(
        render=tables.conversions_table,
        computed_from="`models/`",
    ),
    # -- ch02 What a workload is -------------------------------------------------------------
    "what-a-workload-is-storage": Table(
        render=tables.workload_table, result="storage_cluster-reference"
    ),
    "what-a-workload-is-observability": Table(
        render=tables.workload_table, result="observability-reference"
    ),
    "what-a-workload-is-service": Table(
        render=tables.workload_table, result="service_tier-reference"
    ),
    # -- ch03 Where the numbers come from ------------------------------------------------------
    "where-the-numbers-come-from-constants": Table(
        render=tables.constants_index,
        computed_from="`bench/results/`, one row per stamped result",
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
    # -- ch04 Peak, mean and growth ------------------------------------------------------------
    "peak-mean-and-growth-tornado": Table(
        render=tables.tornado_table, result="storage_cluster-reference", args=("nodes_recommended",)
    ),
    "peak-mean-and-growth-chart": Diagram(
        draw=diagrams.tornado_chart,
        result="storage_cluster-reference",
        args=("nodes_recommended",),
        alt="Which input moves the recommended node count most",
    ),
    "peak-mean-and-growth-capacity": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("usable_capacity",),
        alt="Usable capacity at the horizon, as a distribution",
    ),
    # -- ch05 Little's law ----------------------------------------------------------------------
    "littles-law-outputs": Table(render=tables.outputs_table, result="service_tier-reference"),
    "littles-law-concurrency": Diagram(
        draw=diagrams.distribution,
        result="service_tier-reference",
        args=("concurrency",),
        alt="Requests in the system, as a distribution",
    ),
    "littles-law-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="service_tier-reference",
        args=("concurrency",),
        alt="The sub-graph that produces the number of requests in the system",
    ),
    # -- ch06 Queueing and the knee --------------------------------------------------------------
    "queueing-and-the-knee-curve": Diagram(
        draw=diagrams.queueing_curve,
        result="queueing-curve",
        alt="Residence time against utilisation: flat, and then vertical",
    ),
    "queueing-and-the-knee-table": Table(render=tables.queueing_table, result="queueing-curve"),
    "queueing-and-the-knee-ceilings": Table(
        render=tables.ceilings_table, result="service_tier-reference"
    ),
    # -- ch07 When adding servers stops helping -----------------------------------------------------
    "when-adding-servers-stops-helping-curve": Diagram(
        draw=diagrams.scaling_curve,
        result="scaling-curve",
        alt="Throughput against node count, against the straight line a budget assumes",
    ),
    "when-adding-servers-stops-helping-table": Table(
        render=tables.scaling_table, result="scaling-curve"
    ),
    "when-adding-servers-stops-helping-scenarios": Table(
        render=tables.scenario_comparison,
        result="service_tier-reference",
        args=("service_tier-twice_the_nodes",),
        also=("service_tier-twice_the_nodes",),
    ),
    # -- ch08 Regime changes ---------------------------------------------------------------------
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
    # -- ch09 Capacity -----------------------------------------------------------------------------
    "capacity-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        args=("nodes_for_capacity",),
        alt="The chain from what you need to store to how many machines you must buy",
    ),
    "capacity-outputs": Table(render=tables.outputs_table, result="storage_cluster-reference"),
    "capacity-measured": Table(render=tables.measured_table, result="storage_cluster-reference"),
    # -- ch10 Bandwidth and the binding constraint ------------------------------------------------
    "bandwidth-and-the-binding-constraint-table": Table(
        render=tables.binding_table, result="binding-constraint"
    ),
    "bandwidth-and-the-binding-constraint-capacity": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("nodes_for_capacity",),
        alt="The node count the capacity chain asks for",
    ),
    "bandwidth-and-the-binding-constraint-throughput": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("nodes_for_throughput",),
        alt="The node count the bandwidth chain asks for",
    ),
    # -- ch11 Headroom, failure domains and reservations --------------------------------------------
    "headroom-and-failure-domains-storage": Table(
        render=tables.ceilings_table, result="storage_cluster-reference"
    ),
    "headroom-and-failure-domains-observability": Table(
        render=tables.ceilings_table, result="observability-reference"
    ),
    "headroom-and-failure-domains-service": Table(
        render=tables.ceilings_table, result="service_tier-reference"
    ),
    # -- ch12 The sizing model -------------------------------------------------------------------
    "the-sizing-model-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "the-sizing-model-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        args=("nodes_recommended",),
        alt="Everything that feeds the recommended node count",
    ),
    "the-sizing-model-ceilings": Table(
        render=tables.ceilings_table, result="storage_cluster-reference"
    ),
    "the-sizing-model-resized": Table(
        render=tables.ceilings_table, result="storage_cluster-sized_for_growth"
    ),
    "the-sizing-model-nodes": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("nodes_recommended",),
        alt="The recommended node count, as a distribution",
    ),
    # -- ch15 Capex, opex and the lifecycle ----------------------------------------------------------
    "capex-opex-and-lifecycle-split": Table(
        render=tables.cost_split_table, result="storage_cluster-reference"
    ),
    "capex-opex-and-lifecycle-outputs": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "capex-opex-and-lifecycle-tornado": Table(
        render=tables.tornado_table, result="storage_cluster-reference", args=("annual_opex",)
    ),
    # -- ch16 Power first -------------------------------------------------------------------------
    "power-first-scenarios": Table(
        render=tables.scenario_comparison,
        result="storage_cluster-reference",
        args=("storage_cluster-power_first",),
        also=("storage_cluster-power_first",),
    ),
    "power-first-ceilings": Table(
        render=tables.ceilings_table, result="storage_cluster-power_first"
    ),
    "power-first-tornado": Table(
        render=tables.tornado_table, result="storage_cluster-reference", args=("annual_energy",)
    ),
    # -- ch17 Unit economics -----------------------------------------------------------------------
    "unit-economics-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("cost_per_usable_tb_month",),
        alt="Cost per usable TB per month, as a distribution",
    ),
    "unit-economics-tornado": Table(
        render=tables.tornado_table,
        result="storage_cluster-reference",
        args=("cost_per_usable_tb_month",),
    ),
    "unit-economics-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="storage_cluster-reference",
        args=("cost_per_usable_tb_month",),
        alt="Everything that feeds the unit cost, including its denominator",
    ),
    # -- ch18 The five-year model -------------------------------------------------------------------
    "the-five-year-model-storage": Table(
        render=tables.outputs_table, result="storage_cluster-reference"
    ),
    "the-five-year-model-observability": Table(
        render=tables.outputs_table, result="observability-reference"
    ),
    "the-five-year-model-split": Table(
        render=tables.cost_split_table, result="storage_cluster-reference"
    ),
    # -- ch19 Which input is the answer? --------------------------------------------------------------
    "which-input-is-the-answer-storage": Diagram(
        draw=diagrams.tornado_chart,
        result="storage_cluster-reference",
        args=("tco",),
        alt="Which input moves the five-year total most",
    ),
    "which-input-is-the-answer-observability": Diagram(
        draw=diagrams.tornado_chart,
        result="observability-reference",
        args=("known_stored",),
        alt="Which input moves the retention store most",
    ),
    "which-input-is-the-answer-service": Table(
        render=tables.tornado_table, result="service_tier-reference", args=("residence_time",)
    ),
    "which-input-is-the-answer-correlation": Table(
        render=tables.correlation_table, result="correlation-effect"
    ),
    "which-input-is-the-answer-worth-storage": Table(
        render=tables.value_of_information_table,
        result="value-of-information",
        args=("storage_cluster", "tco"),
    ),
    "which-input-is-the-answer-worth-observability": Table(
        render=tables.value_of_information_table,
        result="value-of-information",
        args=("observability", "known_stored"),
    ),
    # -- ch22 What the model got wrong -------------------------------------------------------------
    "what-the-model-got-wrong-attribution": Table(
        render=tables.postmortem_table, result="postmortem", args=("complete",)
    ),
    "what-the-model-got-wrong-incomplete": Table(
        render=tables.postmortem_table, result="postmortem", args=("incomplete",)
    ),
    "what-the-model-got-wrong-ceilings": Table(
        render=tables.ceilings_table, result="storage_cluster-reference"
    ),
    "what-the-model-got-wrong-unmeasured": Table(
        render=tables.not_yet_measured, result="observability-reference"
    ),
    # -- ch20 The missing node ---------------------------------------------------------------------
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
    # -- ch21 A TCO for a finance audience ------------------------------------------------------------
    "a-tco-for-finance-scenarios": Table(
        render=tables.scenario_comparison,
        result="storage_cluster-reference",
        args=("storage_cluster-sized_for_growth",),
        also=("storage_cluster-sized_for_growth",),
    ),
    "a-tco-for-finance-distribution": Diagram(
        draw=diagrams.distribution,
        result="storage_cluster-reference",
        args=("tco",),
        alt="The five-year total as a distribution, with the point estimate on it",
    ),
    "a-tco-for-finance-ceilings": Table(
        render=tables.ceilings_table, result="storage_cluster-reference"
    ),
    "a-tco-for-finance-provenance": Table(
        render=tables.provenance_table, result="storage_cluster-reference"
    ),
    # -- appendices ------------------------------------------------------------------------------------
    "appendix-a-dsl-reference-kinds": Table(
        render=tables.node_kinds_table, result="observability-reference"
    ),
    "appendix-a-dsl-reference-graph": Diagram(
        draw=diagrams.dependency_graph,
        result="service_tier-reference",
        alt="The smallest model in the book, as a graph",
    ),
    "appendix-b-monte-carlo-module-convergence": Table(
        render=tables.convergence_table, result="convergence-storage-tco"
    ),
    "appendix-c-distributions-shapes": Diagram(
        draw=diagrams.distribution_shapes,
        result="storage_cluster-reference",
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
